"""Friday booking worker. It runs only at configured launch minutes in Madrid."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from firebase_admin import firestore

from .security import CredentialCipher
from .store import wodbuster_connection
from .wodbuster import InvalidCredentials, WodBusterClient, WodBusterError


MADRID = ZoneInfo("Europe/Madrid")


def next_target_date(now: datetime, weekday_sunday_zero: int):
    local = now.astimezone(MADRID).date()
    target_weekday = (weekday_sunday_zero - 1) % 7
    return local + timedelta(days=(target_weekday - local.weekday()) % 7)


def run_due_schedules(encryption_key: str) -> list[dict[str, str]]:
    now = datetime.now(MADRID)
    if now.weekday() != 4:  # Friday
        return []
    week_key = now.strftime("%G-W%V")
    due: list[dict[str, str]] = []
    for snapshot in firestore.client().collection_group("schedules").where("active", "==", True).stream():
        schedule = snapshot.to_dict()
        if schedule.get("launch_time") != now.strftime("%H:%M") or schedule.get("last_run_week") == week_key:
            continue
        uid = snapshot.reference.parent.parent.id
        connection = wodbuster_connection(uid)
        if not connection or not connection.get("verified_at"):
            continue
        cipher = CredentialCipher(encryption_key)
        client = WodBusterClient(cipher.decrypt(str(connection["username_ciphertext"])), cipher.decrypt(str(connection["password_ciphertext"])))
        target = next_target_date(now, int(schedule["weekday"]))
        try:
            box_url = cipher.decrypt(str(connection["box_url_ciphertext"]))
            result = client.book(box_url, target, str(schedule["class_time"]))
            message = result
        except (InvalidCredentials, WodBusterError) as exc:
            message = str(exc)
        snapshot.reference.update({"last_run_week": week_key, "last_result": message, "last_run_at": now})
        due.append({"schedule_id": snapshot.id, "result": message})
    return due
