from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo


class PublishWindowNotOpenError(ValueError):
    """Raised when an official quarterly publish is attempted before cutoff."""


@dataclass(frozen=True)
class QuarterWindow:
    quarter: str
    timezone: str
    starts_at: datetime
    ends_at_exclusive: datetime

    def contains(self, value: datetime) -> bool:
        if value.tzinfo is None:
            raise ValueError("quarter-window comparisons require timezone-aware datetimes")
        value_utc = value.astimezone(UTC)
        return self.starts_at <= value_utc < self.ends_at_exclusive


def _quarter_parts(quarter: str) -> tuple[int, int]:
    if (
        len(quarter) != 7
        or quarter[4:6] != "-Q"
        or not quarter[:4].isdigit()
        or quarter[6] not in "1234"
    ):
        raise ValueError("quarter must use YYYY-QN where N is 1..4")
    return int(quarter[:4]), int(quarter[6])


def quarter_window(quarter: str, timezone: str = "Africa/Kampala") -> QuarterWindow:
    year, quarter_number = _quarter_parts(quarter)
    zone = ZoneInfo(timezone)
    start_month = (quarter_number - 1) * 3 + 1
    start_local = datetime(year, start_month, 1, tzinfo=zone)
    if quarter_number == 4:
        end_local = datetime(year + 1, 1, 1, tzinfo=zone)
    else:
        end_local = datetime(year, start_month + 3, 1, tzinfo=zone)
    return QuarterWindow(
        quarter=quarter,
        timezone=timezone,
        starts_at=start_local.astimezone(UTC),
        ends_at_exclusive=end_local.astimezone(UTC),
    )


def assert_publish_window_open(quarter: str, now: datetime) -> None:
    if now.tzinfo is None:
        raise ValueError("publish clock must be timezone-aware")
    window = quarter_window(quarter)
    if now.astimezone(UTC) < window.ends_at_exclusive:
        raise PublishWindowNotOpenError(
            f"Official {quarter} publication is blocked until "
            f"{window.ends_at_exclusive.isoformat()} ({window.timezone} quarter close)."
        )
