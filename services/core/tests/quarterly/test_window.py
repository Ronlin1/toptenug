from datetime import UTC, datetime

import pytest

from app.quarterly.window import (
    PublishWindowNotOpenError,
    assert_publish_window_open,
    quarter_window,
)


def test_2026_q3_ends_at_kampala_midnight_in_utc() -> None:
    window = quarter_window("2026-Q3")

    assert window.quarter == "2026-Q3"
    assert window.timezone == "Africa/Kampala"
    assert window.ends_at_exclusive.isoformat() == "2026-09-30T21:00:00+00:00"


def test_q3_contains_last_second_before_cutoff_but_not_cutoff() -> None:
    window = quarter_window("2026-Q3")

    assert window.contains(datetime(2026, 9, 30, 20, 59, 59, tzinfo=UTC))
    assert not window.contains(datetime(2026, 9, 30, 21, 0, 0, tzinfo=UTC))


def test_publish_window_rejects_pre_cutoff_clock() -> None:
    with pytest.raises(PublishWindowNotOpenError):
        assert_publish_window_open(
            "2026-Q3",
            datetime(2026, 9, 30, 20, 59, 59, tzinfo=UTC),
        )


def test_publish_window_opens_at_exact_cutoff() -> None:
    assert_publish_window_open(
        "2026-Q3",
        datetime(2026, 9, 30, 21, 0, 0, tzinfo=UTC),
    )
