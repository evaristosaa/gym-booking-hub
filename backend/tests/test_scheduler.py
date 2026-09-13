from datetime import datetime, timezone

from app.scheduler import is_due_friday_launch


def test_due_for_friday_1530_madrid() -> None:
    # 13:30 UTC is 15:30 CEST on Friday 18 September 2026.
    now = datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc)
    assert is_due_friday_launch(now, 15, 30)


def test_not_due_outside_requested_minute() -> None:
    now = datetime(2026, 9, 18, 13, 31, tzinfo=timezone.utc)
    assert not is_due_friday_launch(now, 15, 30)
