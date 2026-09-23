from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest

from app.sources.base import EntityRef, RetryableSourceError
from app.sources.github import GitHubAdapter

NOW = datetime(2026, 9, 23, tzinfo=UTC)


def _transport(rate_limited: bool = False):
    def handler(request: httpx.Request) -> httpx.Response:
        if rate_limited:
            return httpx.Response(429, headers={"retry-after": "60"}, request=request)
        if request.url.path.endswith("/users/octocat"):
            return httpx.Response(200, json={"login": "octocat", "followers": 42, "html_url": "https://github.com/octocat"}, request=request)
        if request.url.path.endswith("/users/octocat/repos"):
            return httpx.Response(200, json=[
                {"fork": False, "stargazers_count": 10, "pushed_at": "2026-09-01T00:00:00Z"},
                {"fork": False, "stargazers_count": 5, "pushed_at": "2025-01-01T00:00:00Z"},
                {"fork": True, "stargazers_count": 999, "pushed_at": "2026-09-10T00:00:00Z"},
            ], request=request)
        if request.url.path.endswith("/graphql"):
            return httpx.Response(200, json={"data": {"user": {"contributionsCollection": {
                "totalCommitContributions": 17,
                "totalPullRequestContributions": 4,
                "totalPullRequestReviewContributions": 6,
            }}}}, request=request)
        return httpx.Response(404, request=request)
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_github_adapter_collects_hard_metrics_and_filters_forks():
    async with httpx.AsyncClient(transport=_transport(), base_url="https://api.github.com") as client:
        rows = await GitHubAdapter(client=client, token="test", clock=lambda: NOW).collect(EntityRef(id=UUID(int=1), external_id="octocat"))
    assert {row.metric_key: row.raw_value for row in rows} == {
        "github.followers": 42,
        "github.owned_repo_stars": 15,
        "github.active_owned_repos_180d": 1,
        "github.contributions_90d": 21,
        "github.prs_and_reviews_90d": 10,
    }


@pytest.mark.asyncio
async def test_github_adapter_never_returns_unprovenanced_observation():
    async with httpx.AsyncClient(transport=_transport(), base_url="https://api.github.com") as client:
        rows = await GitHubAdapter(client=client, token="test", clock=lambda: NOW).collect(EntityRef(id=UUID(int=1), external_id="octocat"))
    assert rows
    assert all(row.source_url and row.evidence_id for row in rows)
    assert all("rank" not in type(row).model_fields and "score" not in type(row).model_fields for row in rows)


@pytest.mark.asyncio
async def test_rate_limit_becomes_retryable_source_error():
    async with httpx.AsyncClient(transport=_transport(rate_limited=True), base_url="https://api.github.com") as client:
        adapter = GitHubAdapter(client=client, token="test", clock=lambda: NOW)
        with pytest.raises(RetryableSourceError) as exc:
            await adapter.collect(EntityRef(id=UUID(int=1), external_id="octocat"))
    assert exc.value.retry_after_seconds == 60
