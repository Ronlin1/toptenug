from fastapi.testclient import TestClient

from app.api.store import public_store
from app.cli import run_first_vertical_fixture
from app.domain.enums import EntityType
from app.intelligence.base import CandidateProposal
from app.main import app


def proposal(name: str, github: str, url: str) -> CandidateProposal:
    return CandidateProposal(
        display_name=name,
        entity_type=EntityType.PERSON,
        candidate_profiles={"github": github},
        uganda_relation_claims=["Ugandan technology builder"],
        source_urls=[url],
        confidence=0.95,
    )


CANDIDATES = [
    proposal("Alice Builder", "aliceug", "https://example.com/alice"),
    proposal("Bob Builder", "bobug", "https://example.com/bob"),
]

METRICS = {
    "aliceug": {
        "github.owned_repo_stars": 350,
        "github.contributions_90d": 85,
        "github.active_owned_repos_180d": 6,
        "github.followers": 140,
        "github.prs_and_reviews_90d": 55,
    },
    "bobug": {
        "github.owned_repo_stars": 80,
        "github.contributions_90d": 120,
        "github.active_owned_repos_180d": 4,
        "github.followers": 70,
        "github.prs_and_reviews_90d": 35,
    },
}


def test_full_fixture_flow_is_deterministic_and_ignores_discovery_order():
    public_store.clear()
    first = run_first_vertical_fixture(CANDIDATES, METRICS, quarter="2026-Q3")
    first_order = [row.entity_id for row in first.results]
    first_scores = [row.score for row in first.results]

    public_store.clear()
    second = run_first_vertical_fixture(list(reversed(CANDIDATES)), METRICS, quarter="2026-Q3")
    assert [row.entity_id for row in second.results] == first_order
    assert [row.score for row in second.results] == first_scores
    assert second.algorithm_version == "1.0.0"
    assert all(row.evidence_urls for row in second.results)

    client = TestClient(app)
    leaderboard = client.get("/v1/rankings/github-developers?limit=10")
    assert leaderboard.status_code == 200
    payload = leaderboard.json()
    assert payload["algorithm_version"] == "1.0.0"
    assert len(payload["results"]) <= 10
    assert all(row["provenance_count"] >= 1 for row in payload["results"])

    top = payload["results"][0]
    profile = client.get(f"/v1/entities/{top['slug']}")
    history = client.get(f"/v1/entities/{top['slug']}/history")
    share = client.get(f"/v1/rankings/results/{top['result_id']}/share")
    assert profile.status_code == history.status_code == share.status_code == 200
    assert share.json()["rank"] == top["rank"]
