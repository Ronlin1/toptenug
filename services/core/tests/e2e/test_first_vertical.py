from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi.testclient import TestClient

from app.api.store import EntityPublicRecord, public_store
from app.domain.enums import EntityType, RankingType, UgandaRelation
from app.domain.schemas import CandidateProposal, ObservationInput
from app.ingestion.derive import derive_candidate_metrics
from app.ingestion.eligibility import EligibilityEvidence, EligibilityService
from app.ingestion.pipeline import InMemoryIngestionRepository, IngestionPipeline
from app.main import app
from app.quarterly.publish import CategorySnapshotInput, InMemoryRankingStore, Quarter, QuarterPublisher
from app.ranking.loader import load_algorithm_spec

CATEGORY = UUID(int=900)
SPEC = load_algorithm_spec(Path("algorithms/devrankug/v1.0.0.yaml"))
NOW = datetime(2026, 9, 30, tzinfo=UTC)


def proposal(name: str, github: str, url: str) -> CandidateProposal:
    return CandidateProposal(
        display_name=name,
        entity_type=EntityType.PERSON,
        candidate_profiles={"github": f"https://github.com/{github}"},
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


def _observations(github: str) -> list[ObservationInput]:
    source_url = f"https://github.com/{github}"
    rows = []
    for metric, value in METRICS[github].items():
        evidence_id = uuid5(NAMESPACE_URL, f"{github}:{metric}:evidence")
        rows.append(
            ObservationInput(
                metric_key=metric,
                raw_value=value,
                observed_at=NOW,
                source_url=source_url,
                evidence_id=evidence_id,
                source_record_id=f"{github}:{metric}:2026-Q3",
            )
        )
    return rows


def _run(order: list[CandidateProposal]):
    repo = InMemoryIngestionRepository()
    pipeline = IngestionPipeline(repo)
    ranked_candidates = []
    name_by_id: dict[UUID, str] = {}

    for candidate in order:
        github_url = candidate.candidate_profiles["github"]
        github = github_url.rsplit("/", 1)[-1]
        outcome = pipeline.ingest(candidate, _observations(github))
        entity = repo.entities[outcome.entity_id]
        name_by_id[entity.id] = entity.name
        eligibility = EligibilityService().evaluate([
            EligibilityEvidence(
                evidence_id=repo.evidence[0].id,
                relation=UgandaRelation.NATIONAL,
                confidence=0.95,
            )
        ])
        assert eligibility.eligible is True
        ranked_candidates.append(
            derive_candidate_metrics(repo, entity.id, eligible=eligibility.eligible)
        )

    store = InMemoryRankingStore()
    store.configure_category(CATEGORY, CategorySnapshotInput(spec=SPEC, candidates=ranked_candidates))
    run = QuarterPublisher(store).publish(Quarter(2026, 3), CATEGORY, "1.0.0")
    ordered = sorted(store.results[run.id], key=lambda row: row.rank)
    return repo, store, run, name_by_id, ordered


def test_full_fixture_flow_is_deterministic_and_ignores_discovery_order():
    first = _run(CANDIDATES)
    second = _run(list(reversed(CANDIDATES)))

    first_names = [first[3][row.entity_id] for row in first[4]]
    second_names = [second[3][row.entity_id] for row in second[4]]
    first_scores = [row.score for row in first[4]]
    second_scores = [row.score for row in second[4]]

    assert second_names == first_names
    assert second_scores == first_scores
    assert second[2].algorithm_version == "1.0.0"

    repo, store, run, _, results = second
    public_store.reset()
    public_store.ranking_store = store
    public_store.register_category(
        slug="github-developers",
        name="Top Ugandan GitHub Developers",
        category_id=CATEGORY,
        ranking_type=RankingType.INDEX,
        methodology_slug="devrankug-v1",
    )
    for entity in repo.entities.values():
        public_store.register_entity(
            EntityPublicRecord(
                id=entity.id,
                slug=entity.slug,
                name=entity.name,
                evidence_urls=[e.source_url for e in repo.evidence if e.entity_id == entity.id],
            )
        )

    client = TestClient(app)
    leaderboard = client.get("/v1/rankings/github-developers?limit=10")
    assert leaderboard.status_code == 200
    payload = leaderboard.json()
    assert payload["algorithm_version"] == "1.0.0"
    assert len(payload["results"]) == len(results)
    assert all(row["provenance"]["source_count"] >= 1 for row in payload["results"])

    top = payload["results"][0]
    profile = client.get(f"/v1/entities/{top['entity_slug']}")
    history = client.get(f"/v1/entities/{top['entity_slug']}/history")
    share = client.get(f"/v1/rankings/results/{top['ranking_result_id']}/share")
    assert profile.status_code == history.status_code == share.status_code == 200
    assert share.json()["rank"] == top["rank"]
    public_store.reset()
