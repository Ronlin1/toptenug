from __future__ import annotations


def weighted_index_score(weighted_values: list[tuple[float, float]]) -> float:
    """Return a 0-100 score, renormalizing across available factors."""
    total_weight = sum(weight for weight, _ in weighted_values)
    if total_weight == 0:
        return 0.0
    return 100.0 * sum(weight * value for weight, value in weighted_values) / total_weight
