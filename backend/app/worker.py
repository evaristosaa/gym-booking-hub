"""Background workers for Friday plans and one-off availability watches."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from firebase_admin import firestore

from .security import CredentialCipher
from .store import wodbuster_connection
from .wodbuster import InvalidCredentials, WodBusterClient, WodBusterError
from .notifications import notify_booking


MADRID = ZoneInfo("Europe/Madrid")


def next_target_date(now: datetime, weekday_sunday_zero: int):
    local = now.astimezone(MADRID).date()
    target_weekday = (weekday_sunday_zero - 1) % 7
    return local + timedelta(days=(target_weekday - local.weekday()) % 7)


def _client_for(uid: str, encryption_key: str) -> tuple[WodBusterClient, str] | None:
    connection = wodbuster_connection(uid)
    if not connection or not connection.get("verified_at") or not connection.get("box_url_ciphertext"):
        return None
    cipher = CredentialCipher(encryption_key)
    return (
        WodBusterClient(
            cipher.decrypt(str(connection["username_ciphertext"])),
            cipher.decrypt(str(connection["password_ciphertext"])),
        ),
        cipher.decrypt(str(connection["box_url_ciphertext"])),
    )


def run_due_schedules(encryption_key: str, now: datetime | None = None) -> list[dict[str, str]]:
    now = now or datetime.now(MADRID)
    if now.weekday() != 4:  # Friday
        return []
    week_key = now.strftime("%G-W%V")
    due: list[dict[str, str]] = []
    for snapshot in firestore.client().collection_group("schedules").where("active", "==", True).stream():
        schedule = snapshot.to_dict()
        if schedule.get("launch_time") != now.strftime("%H:%M") or schedule.get("last_run_week") == week_key:
            continue
        uid = snapshot.reference.parent.parent.id
        client_data = _client_for(uid, encryption_key)
        if not client_data:
            continue
        client, box_url = client_data
        target = next_target_date(now, int(schedule["weekday"]))
        try:
            message = client.book(box_url, target, str(schedule["class_time"]))
        except (InvalidCredentials, WodBusterError) as exc:
            message = str(exc)
        snapshot.reference.update({"last_run_week": week_key, "last_result": message, "last_run_at": now})
        due.append({"schedule_id": snapshot.id, "result": message})
    return due


def run_availability_watches(
    encryption_key: str,
    vapid_private_key: str | None,
    vapid_subject: str,
    now: datetime | None = None,
) -> list[dict[str, str]]:
    """Try every active one-off watch once; full classes remain active for the next tick."""
    now = now or datetime.now(MADRID)
    due: list[dict[str, str]] = []
    for snapshot in firestore.client().collection_group("availability_watches").where("active", "==", True).stream():
        watch = snapshot.to_dict()
        try:
            target = datetime.fromisoformat(f"{watch['class_date']}T{watch['class_time']}").replace(tzinfo=MADRID)
        except (KeyError, TypeError, ValueError):
            snapshot.reference.update({"active": False, "last_result": "Configuración inválida"})
            continue
        if target <= now:
            snapshot.reference.update({"active": False, "last_result": "La clase ya ha empezado"})
            continue
        uid = snapshot.reference.parent.parent.id
        client_data = _client_for(uid, encryption_key)
        if not client_data:
            snapshot.reference.update({"last_result": "WodBuster necesita validarse de nuevo", "last_checked_at": now})
            continue
        client, box_url = client_data
        try:
            result = client.book(box_url, target.date(), str(watch["class_time"]))
        except (InvalidCredentials, WodBusterError) as exc:
            result = str(exc)
        update: dict[str, object] = {"last_result": result, "last_checked_at": now}
        if result in {"booked", "already_booked"}:
            update.update({"active": False, "completed_at": now, "status": "confirmed"})
            when = target.strftime("%A %d/%m · %H:%M")
            notify_booking(uid, "Reserva confirmada", f"WodBuster: {when}", vapid_private_key, vapid_subject)
        snapshot.reference.update(update)
        due.append({"watch_id": snapshot.id, "result": result})
    return due
