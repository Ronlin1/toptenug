from __future__ import annotations

import math
import statistics
from collections.abc import Sequence


def _min_max(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [0.5 for _ in values]
    return [(value - low) / (high - low) for value in values]


def normalize(kind: str, values: Sequence[float]) -> list[float]:
    numeric = [float(value) for value in values]
    if not numeric:
        return []
    if kind == "log1p":
        transformed = [math.log1p(max(0.0, value)) for value in numeric]
        high = max(transformed)
        return [0.0 if high == 0 else value / high for value in transformed]
    if kind == "percentile":
        ordered = sorted(numeric)
        if len(ordered) == 1:
            return [1.0]
        return [sum(item <= value for item in ordered) / len(ordered) for value in numeric]
    if kind == "robust_z":
        median = statistics.median(numeric)
        deviations = [abs(value - median) for value in numeric]
        mad = statistics.median(deviations)
        if mad == 0:
            return [0.5 for _ in numeric]
        result: list[float] = []
        for value in numeric:
            z = 0.6745 * (value - median) / mad
            z = max(-20.0, min(20.0, z))
            result.append(1.0 / (1.0 + math.exp(-z)))
        return result
    if kind == "min_max":
        return _min_max(numeric)
    if kind == "capped_min_max":
        ordered = sorted(numeric)
        index = max(0, math.ceil(len(ordered) * 0.95) - 1)
        cap = ordered[index]
        return _min_max([min(value, cap) for value in numeric])
    raise ValueError(f"Unsupported normalization: {kind}")
