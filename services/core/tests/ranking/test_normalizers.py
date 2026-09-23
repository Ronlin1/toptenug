import pytest

from app.ranking.normalizers import normalize


@pytest.mark.parametrize("kind", ["log1p", "percentile", "robust_z", "min_max", "capped_min_max"])
def test_normalizers_are_deterministic_and_bounded(kind):
    values = [0.0, 1.0, 10.0, 100.0]
    first = normalize(kind, values)
    second = normalize(kind, values)
    assert first == second
    assert all(0.0 <= value <= 1.0 for value in first)
