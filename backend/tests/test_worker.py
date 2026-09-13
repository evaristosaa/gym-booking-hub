from datetime import datetime, timezone

from app.worker import next_target_date


def test_friday_targets_the_following_monday() -> None:
    friday = datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc)
    assert next_target_date(friday, 1).isoformat() == "2026-09-21"


def test_friday_targets_the_following_wednesday() -> None:
    friday = datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc)
    assert next_target_date(friday, 3).isoformat() == "2026-09-23"
