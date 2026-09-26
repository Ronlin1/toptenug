from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from app.domain.schemas import EntityRef, ObservationInput

from .base import RetryableSourceError, SourceError


class GitHubAdapter:
    def __init__(
        self,
        *,
        token: str | None,
        client: httpx.AsyncClient | None = None,
        now: Callable[[], datetime] | None = None,
        clock: Callable[[], datetime] | None = None,
        api_base_url: str = "https://api.github.com",
    ) -> None:
        self._token = token
        self._client = client
        self._owns_client = client is None
        self._now = now or clock or (lambda: datetime.now(UTC))
        self._api_base_url = api_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "TopTenUG/0.1",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        *,
        params: dict[str, str | int] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        response = await client.request(
            method,
            url,
            headers=self._headers(),
            params=params,
            json=json_body,
        )
        if response.status_code in {403, 429}:
            retry_after = response.headers.get("retry-after")
            reset = response.headers.get("x-ratelimit-reset")
            reset_at = (
                datetime.fromtimestamp(int(reset), tz=UTC)
                if reset and reset.isdigit()
                else None
            )
            raise RetryableSourceError(
                f"GitHub rate limit returned {response.status_code}",
                retry_after_seconds=(
                    int(retry_after)
                    if retry_after and retry_after.isdigit()
                    else None
                ),
                reset_at=reset_at,
            )
        if response.status_code >= 400 and response.status_code != 404:
            raise SourceError(f"GitHub returned {response.status_code} for {url}")
        return response

    @staticmethod
    def _evidence_id(url: str, observed_at: datetime) -> UUID:
        return uuid5(NAMESPACE_URL, f"{url}|{observed_at.isoformat()}")

    @staticmethod
    def _dt(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _github_time(value: datetime) -> str:
        return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    async def collect(self, entity: EntityRef) -> list[ObservationInput]:
        client = self._client or httpx.AsyncClient(
            base_url=self._api_base_url,
            timeout=20,
        )
        observed = self._now().astimezone(UTC)
        user = entity.external_id
        try:
            profile_response = await self._request(client, "GET", f"/users/{user}")
            if profile_response.status_code == 404:
                return []

            profile = profile_response.json()
            repos_response = await self._request(
                client,
                "GET",
                f"/users/{user}/repos",
                params={"per_page": 100, "type": "owner", "sort": "updated"},
            )
            repos = repos_response.json() if repos_response.status_code == 200 else []
            owned = [repo for repo in repos if not repo.get("fork", False)]
            stars = sum(int(repo.get("stargazers_count", 0)) for repo in owned)
            cutoff = observed - timedelta(days=180)
            active = sum(
                1
                for repo in owned
                if repo.get("pushed_at")
                and self._dt(str(repo["pushed_at"])).astimezone(UTC) >= cutoff
            )

            from_at = observed - timedelta(days=90)
            graphql_response = await self._request(
                client,
                "POST",
                "/graphql",
                json_body={
                    "query": (
                        "query($login:String!,$from:DateTime!,$to:DateTime!){"
                        "user(login:$login){contributionsCollection(from:$from,to:$to){"
                        "totalCommitContributions "
                        "totalPullRequestContributions "
                        "totalPullRequestReviewContributions}}}"
                    ),
                    "variables": {
                        "login": user,
                        "from": self._github_time(from_at),
                        "to": self._github_time(observed),
                    },
                },
            )
            collection = (
                graphql_response.json()
                .get("data", {})
                .get("user", {})
                .get("contributionsCollection", {})
                if graphql_response.status_code == 200
                else {}
            )
            pull_requests = int(collection.get("totalPullRequestContributions", 0))
            contributions = int(collection.get("totalCommitContributions", 0)) + pull_requests
            collaboration = pull_requests + int(
                collection.get("totalPullRequestReviewContributions", 0)
            )

            profile_url = str(profile.get("html_url") or f"https://github.com/{user}")
            repos_url = f"https://api.github.com/users/{user}/repos"
            activity_url = f"https://github.com/{user}?tab=overview"
            metrics = [
                ("github.followers", int(profile.get("followers", 0)), profile_url),
                ("github.owned_repo_stars", stars, repos_url),
                ("github.active_owned_repos_180d", active, repos_url),
                ("github.contributions_90d", contributions, activity_url),
                ("github.prs_and_reviews_90d", collaboration, activity_url),
            ]
            return [
                ObservationInput(
                    metric_key=key,
                    raw_value=value,
                    observed_at=observed,
                    source_url=url,
                    evidence_id=self._evidence_id(url, observed),
                    source_record_id=f"{user}:{key}:{observed.date().isoformat()}",
                )
                for key, value, url in metrics
            ]
        finally:
            if self._owns_client:
                await client.aclose()
