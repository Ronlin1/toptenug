from dataclasses import dataclass,field
from uuid import UUID
from app.domain.enums import RankingRunStatus,RankingType
from app.quarterly.publish import InMemoryRankingStore,PublishedResult,PublishedRun
@dataclass(frozen=True)
class CategoryPublicRecord: slug:str; name:str; category_id:UUID; ranking_type:RankingType; methodology_slug:str
@dataclass(frozen=True)
class EntityPublicRecord: id:UUID; slug:str; name:str; avatar_url:str|None=None; evidence_urls:list[str]=field(default_factory=list); summary:str|None=None
class PublicStore:
    def __init__(self)->None:self.reset()
    def reset(self)->None:self.ranking_store=InMemoryRankingStore(); self.category_by_slug={}; self.category_by_id={}; self.entity_by_slug={}; self.entity_by_id={}
    def register_category(self,*,slug:str,name:str,category_id:UUID,ranking_type:RankingType,methodology_slug:str)->None:
        r=CategoryPublicRecord(slug,name,category_id,ranking_type,methodology_slug); self.category_by_slug[slug]=r; self.category_by_id[category_id]=r
    def register_entity(self,e:EntityPublicRecord)->None:self.entity_by_slug[e.slug]=e; self.entity_by_id[e.id]=e
    def find_published_run(self,cid:UUID,quarter:str|None=None)->PublishedRun|None:
        if quarter is None:
            rid=self.ranking_store.official_by_category.get(cid); return self.ranking_store.runs.get(rid) if rid else None
        m=[r for r in self.ranking_store.runs.values() if r.category_id==cid and str(r.quarter)==quarter and r.status==RankingRunStatus.PUBLISHED]; return max(m,key=lambda r:r.published_at or r.started_at) if m else None
    def previous_result(self,run:PublishedRun,eid:UUID)->PublishedResult|None:
        prior=sorted([r for r in self.ranking_store.runs.values() if r.category_id==run.category_id and r.status==RankingRunStatus.PUBLISHED and r.quarter<run.quarter],key=lambda x:x.quarter,reverse=True)
        for p in prior:
            for result in self.ranking_store.results.get(p.id,()):
                if result.entity_id==eid:return result
        return None
    def published_quarters(self)->list[str]:return sorted({str(r.quarter) for r in self.ranking_store.runs.values() if r.status==RankingRunStatus.PUBLISHED},reverse=True)
public_store=PublicStore()
