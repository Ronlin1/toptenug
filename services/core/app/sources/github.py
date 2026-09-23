from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

import httpx

from app.domain.schemas import ObservationInput
from app.sources.base import EntityRef, RetryableSourceError, SourceNotFoundError


class GitHubAdapter:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        token: str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client
        self.token = token
        self.clock = clock or (lambda: datetime.now(UTC))

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        response = await self.client.request(method, url, headers=self._headers, **kwargs)
        if response.status_code in {403, 429}:
            retry = response.headers.get("retry-after")
            raise RetryableSourceError(
                f"GitHub rate limited request to {url}",
                retry_after_seconds=int(retry) if retry and retry.isdigit() else None,
                reset_at=response.headers.get("x-ratelimit-reset"),
            )
        if response.status_code == 404:
            raise SourceNotFoundError(f"GitHub resource not found: {url}")
        response.raise_for_status()
        return response

    async def collect(self, entity: EntityRef) -> list[ObservationInput]:
        login = entity.external_id
        now = self.clock().astimezone(UTC)
        profile = (await self._request("GET", f"/users/{login}")).json()
        repos = (await self._request("GET", f"/users/{login}/repos", params={"per_page": 100, "sort": "pushed"})).json()
        graph = (await self._request(
            "POST",
            "/graphql",
            json={
                "query": "query($login:String!){user(login:$login){contributionsCollection{totalCommitContributions totalPullRequestContributions totalPullRequestReviewContributions}}}",
                "variables": {"login": login},
            },
        )).json()

        collection = (((graph.get("data") or {}).get("user") or {}).get("contributionsCollection") or {})
        commits = int(collection.get("totalCommitContributions") or 0)
        prs = int(collection.get("totalPullRequestContributions") or 0)
        reviews = int(collection.get("totalPullRequestReviewContributions") or 0)
        owned = [repo for repo in repos if not repo.get("fork")]
        cutoff = now - timedelta(days=180)

        def is_active(repo: dict) -> bool:
            pushed = repo.get("pushed_at")
            if not pushed:
                return False
            return datetime.fromisoformat(pushed.replace("Z", "+00:00")) >= cutoff

        metrics: dict[str, int] = {
            "github.followers": int(profile.get("followers") or 0),
            "github.owned_repo_stars": sum(int(repo.get("stargazers_count") or 0) for repo in owned),
            "github.active_owned_repos_180d": sum(1 for repo in owned if is_active(repo)),
            "github.contributions_90d": commits + prs,
            "github.prs_and_reviews_90d": prs + reviews,
        }
        profile_url = str(profile.get("html_url") or f"https://github.com/{login}")
        evidence_id = uuid5(NAMESPACE_URL, f"{profile_url}|{now.isoformat()}")
        return [
            ObservationInput(
                metric_key=metric_key,
                raw_value=value,
                observed_at=now,
                source_url=profile_url,
                evidence_id=evidence_id,
                source_record_id=f"{login}:{metric_key}",
                metadata={"provider": "github", "login": login},
            )
            for metric_key, value in metrics.items()
        ]
