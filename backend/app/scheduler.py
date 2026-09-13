"""Schedule evaluation in Madrid time; Cloud Scheduler can invoke this every minute."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")


def is_due_friday_launch(now: datetime, hour: int, minute: int) -> bool:
    """Return true only for the requested Friday minute in Europe/Madrid."""
    local = now.astimezone(MADRID)
    return local.weekday() == 4 and local.hour == hour and local.minute == minute
