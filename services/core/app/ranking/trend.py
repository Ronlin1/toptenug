from __future__ import annotations


def trend_change(current: float | None, baseline: float | None) -> float | None:
    if current is None or baseline is None:
        return None
    if baseline == 0:
        return None if current == 0 else 1.0
    return (current - baseline) / abs(baseline)
