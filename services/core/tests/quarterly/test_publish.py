from pathlib import Path
from uuid import UUID

import pytest

from app.domain.enums import RankingRunStatus
from app.quarterly.publish import (
    CategorySnapshotInput,
    InMemoryRankingStore,
    Quarter,
    QuarterPublisher,
    QuarterValidationError,
)
from app.ranking.engine import CandidateMetrics
from app.ranking.loader import load_algorithm_spec

CATEGORY = UUID(int=10)
SPEC = load_algorithm_spec(Path("algorithms/devrankug/v1.0.0.yaml"))


def _candidate(entity_id: int = 1, stars: int = 100) -> CandidateMetrics:
    return CandidateMetrics(
        entity_id=UUID(int=entity_id),
        metrics={
            "github.owned_repo_stars": stars,
            "github.contributions_90d": 80,
            "github.active_owned_repos_180d": 5,
            "github.followers": 100,
            "github.prs_and_reviews_90d": 40,
        },
        eligible=True,
    )


def test_failed_validation_keeps_previous_snapshot_official():
    store = InMemoryRankingStore()
    publisher = QuarterPublisher(store)
    store.configure_category(CATEGORY, CategorySnapshotInput(spec=SPEC, candidates=[_candidate()]))
    previous_run = publisher.publish(Quarter(2026, 2), CATEGORY, "1.0.0")

    store.configure_category(
        CATEGORY,
        CategorySnapshotInput(
            spec=SPEC,
            candidates=[_candidate(stars=1000)],
            metric_pairs=[("github.owned_repo_stars", 10.0, 1000.0)],
        ),
    )
    with pytest.raises(QuarterValidationError):
        publisher.publish(Quarter(2026, 3), CATEGORY, "1.0.0")

    assert publisher.current_official(CATEGORY).id == previous_run.id
    assert any(run.status == RankingRunStatus.FAILED for run in store.runs.values())


def test_successful_publish_is_immutable_snapshot():
    store = InMemoryRankingStore()
    publisher = QuarterPublisher(store)
    candidates = [_candidate(entity_id=1)]
    store.configure_category(CATEGORY, CategorySnapshotInput(spec=SPEC, candidates=candidates))
    run = publisher.publish(Quarter(2026, 3), CATEGORY, "1.0.0")
    published_results = store.results[run.id]

    candidates[0] = _candidate(entity_id=2, stars=9999)

    assert published_results[0].entity_id == UUID(int=1)
    assert store.results[run.id][0].entity_id == UUID(int=1)
    assert run.status == RankingRunStatus.PUBLISHED
