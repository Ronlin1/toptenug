from app.quarterly.validate import QuarterValidator, ValidationInput


def test_extreme_jump_is_flagged_before_publish():
    report = QuarterValidator().validate(
        ValidationInput(
            provenance_complete=True,
            stale_critical_sources=False,
            algorithm_version="1.0.0",
            expected_algorithm_version="1.0.0",
            ranks=[1],
            factor_coverages=[1.0],
            metric_pairs=[("github.followers", 10.0, 1000.0)],
            minimum_factor_coverage=0.6,
        )
    )
    assert report.blocking_anomalies


def test_low_factor_coverage_blocks_publication():
    report = QuarterValidator().validate(
        ValidationInput(
            provenance_complete=True,
            stale_critical_sources=False,
            algorithm_version="1.0.0",
            expected_algorithm_version="1.0.0",
            ranks=[1],
            factor_coverages=[0.4],
            minimum_factor_coverage=0.6,
        )
    )
    assert report.ok is False
    assert "factor_coverage_below_minimum" in report.errors
