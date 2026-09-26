from uuid import UUID

from app.quarterly.validate import QuarterValidator, ValidationCandidate


def test_extreme_jump_is_flagged_before_publish():
    report = QuarterValidator().validate([
        ValidationCandidate(
            entity_id=UUID(int=1), score=90.0, rank=1, factor_coverage=1.0,
            provenance_count=5, current_metric=1000.0, previous_metric=10.0,
        )
    ])
    assert report.blocking_anomalies


def test_low_factor_coverage_blocks_publication():
    report = QuarterValidator().validate([
        ValidationCandidate(entity_id=UUID(int=1), score=80, rank=1, factor_coverage=0.4, provenance_count=2)
    ])
    assert report.ok is False
