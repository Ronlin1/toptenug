from __future__ import annotations
from collections.abc import Callable
from datetime import UTC,datetime,timedelta
from uuid import NAMESPACE_URL,UUID,uuid5
import httpx
from app.domain.schemas import EntityRef,ObservationInput
from .base import RetryableSourceError,SourceError

class GitHubAdapter:
    def __init__(self,*,token:str|None,client:httpx.AsyncClient|None=None,now:Callable[[],datetime]|None=None,api_base_url:str='https://api.github.com')->None:
        self._token=token; self._client=client; self._owns_client=client is None; self._now=now or (lambda:datetime.now(UTC)); self._api_base_url=api_base_url.rstrip('/')
    def _headers(self)->dict[str,str]:
        h={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'TopTenUG/0.1'}
        if self._token:h['Authorization']=f'Bearer {self._token}'
        return h
    async def _request(self,client:httpx.AsyncClient,method:str,url:str,**kwargs:object)->httpx.Response:
        r=await client.request(method,url,headers=self._headers(),**kwargs)
        if r.status_code in {403,429}:
            ra=r.headers.get('retry-after'); reset=r.headers.get('x-ratelimit-reset'); reset_at=datetime.fromtimestamp(int(reset),tz=UTC) if reset and reset.isdigit() else None
            raise RetryableSourceError(f'GitHub rate limit returned {r.status_code}',retry_after_seconds=int(ra) if ra and ra.isdigit() else None,reset_at=reset_at)
        if r.status_code>=400 and r.status_code!=404:raise SourceError(f'GitHub returned {r.status_code} for {url}')
        return r
    @staticmethod
    def _evidence_id(url:str,observed_at:datetime)->UUID:return uuid5(NAMESPACE_URL,f'{url}|{observed_at.isoformat()}')
    @staticmethod
    def _dt(v:str)->datetime:return datetime.fromisoformat(v.replace('Z','+00:00'))
    async def collect(self,entity:EntityRef)->list[ObservationInput]:
        client=self._client or httpx.AsyncClient(base_url=self._api_base_url,timeout=20); observed=self._now().astimezone(UTC); user=entity.external_id
        try:
            profile_r=await self._request(client,'GET',f'/users/{user}')
            if profile_r.status_code==404:return []
            profile=profile_r.json(); repos_r=await self._request(client,'GET',f'/users/{user}/repos',params={'per_page':100,'type':'owner','sort':'updated'}); repos=repos_r.json() if repos_r.status_code==200 else []; owned=[r for r in repos if not r.get('fork',False)]; stars=sum(int(r.get('stargazers_count',0)) for r in owned); cutoff=observed-timedelta(days=180); active=sum(1 for r in owned if r.get('pushed_at') and self._dt(str(r['pushed_at'])).astimezone(UTC)>=cutoff)
            graph_r=await self._request(client,'POST','/graphql',json={'query':'query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions} totalPullRequestContributions totalPullRequestReviewContributions}}}','variables':{'login':user,'from':(observed-timedelta(days=90)).isoformat(),'to':observed.isoformat()}}); coll=graph_r.json().get('data',{}).get('user',{}).get('contributionsCollection',{}) if graph_r.status_code==200 else {}; contributions=int(coll.get('contributionCalendar',{}).get('totalContributions',0)); collaboration=int(coll.get('totalPullRequestContributions',0))+int(coll.get('totalPullRequestReviewContributions',0)); profile_url=str(profile.get('html_url') or f'https://github.com/{user}'); repos_url=f'https://api.github.com/users/{user}/repos'; activity_url=f'https://github.com/{user}?tab=overview'
            metrics=[('github.followers',int(profile.get('followers',0)),profile_url),('github.owned_repo_stars',stars,repos_url),('github.active_owned_repos_180d',active,repos_url),('github.contributions_90d',contributions,activity_url),('github.prs_and_reviews_90d',collaboration,activity_url)]
            return [ObservationInput(metric_key=k,raw_value=v,observed_at=observed,source_url=url,evidence_id=self._evidence_id(url,observed),source_record_id=f'{user}:{k}:{observed.date().isoformat()}') for k,v,url in metrics]
        finally:
            if self._owns_client:await client.aclose()
