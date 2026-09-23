from uuid import UUID

import pytest

from app.domain.enums import RankingRunStatus
from app.quarterly.publish import Quarter, QuarterPublisher, QuarterValidationError
from app.quarterly.validate import ValidationCandidate

CATEGORY = UUID(int=10)


def test_failed_validation_keeps_previous_snapshot_official():
    publisher = QuarterPublisher()
    publisher.set_candidates([
        ValidationCandidate(entity_id=UUID(int=1), score=70, rank=1, factor_coverage=1.0, provenance_count=2)
    ])
    previous_run = publisher.publish(Quarter(2026, 2), CATEGORY, "1.0.0")
    publisher.set_candidates([
        ValidationCandidate(
            entity_id=UUID(int=1), score=99, rank=1, factor_coverage=1.0,
            provenance_count=2, current_metric=1000, previous_metric=10,
        )
    ])
    with pytest.raises(QuarterValidationError):
        publisher.publish(Quarter(2026, 3), CATEGORY, "1.0.0")
    assert publisher.current_official(CATEGORY).id == previous_run.id
    assert publisher.failed_runs[-1].status == RankingRunStatus.FAILED


def test_successful_publish_is_immutable_snapshot():
    publisher = QuarterPublisher()
    candidates = [ValidationCandidate(entity_id=UUID(int=1), score=80, rank=1, factor_coverage=1.0, provenance_count=2)]
    publisher.set_candidates(candidates)
    run = publisher.publish(Quarter(2026, 3), CATEGORY, "1.0.0")
    candidates[0] = ValidationCandidate(entity_id=UUID(int=2), score=100, rank=1, factor_coverage=1.0, provenance_count=2)
    assert run.results[0].entity_id == UUID(int=1)
    assert run.status == RankingRunStatus.PUBLISHED
