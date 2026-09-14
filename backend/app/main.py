"""HTTPS API boundary for Gym Booking Hub.

This initial slice deliberately exposes no credential endpoint until Firebase token
verification and Firestore rules are deployed. A missing encryption key therefore
cannot accidentally downgrade secrets to plain text.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .settings import get_settings
from .auth import verified_firebase_user
from .security import CredentialCipher, EncryptionUnavailable
from .store import (
    availability_watches_collection,
    push_subscriptions_collection,
    schedules_collection,
    wodbuster_connection as load_wodbuster_connection,
    wodbuster_document,
)
from .wodbuster import InvalidCredentials, WodBusterClient, WodBusterError
from .worker import run_availability_watches, run_due_schedules


settings = get_settings()
app = FastAPI(title="Gym Booking Hub API", version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gym-booking-hub-api"}


@app.get("/v1/session", include_in_schema=False)
def session(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, str]:
    """Minimal authenticated endpoint; never returns credentials or claims wholesale."""
    subject = user.get("uid") or user.get("sub")
    if not isinstance(subject, str):
        raise ValueError("Firebase token is missing a subject")
    return {"uid": subject}


class WodBusterConnectionInput(BaseModel):
    username: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1, max_length=512)


class ScheduleInput(BaseModel):
    weekday: int = Field(ge=0, le=6, description="Sunday=0, Monday=1")
    class_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    launch_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class AvailabilityWatchInput(BaseModel):
    class_date: date
    class_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class PushSubscriptionInput(BaseModel):
    endpoint: str = Field(min_length=1, max_length=4096)
    keys: dict[str, str]


def user_id(user: dict[str, object]) -> str:
    subject = user.get("uid") or user.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firebase token is missing a subject")
    return subject


@app.get("/v1/connections/wodbuster", include_in_schema=False)
def wodbuster_connection(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    data = wodbuster_connection_data(user_id(user))
    return {
        "configured": bool(data),
        "verified": bool(data and data.get("verified_at")),
        "usernameHint": data.get("username_hint") if data else None,
    }


@app.put("/v1/connections/wodbuster", include_in_schema=False)
def save_wodbuster_connection(
    connection: WodBusterConnectionInput,
    user: dict[str, object] = Depends(verified_firebase_user),
) -> dict[str, object]:
    try:
        cipher = CredentialCipher(settings.encryption_key)
    except EncryptionUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Credential vault unavailable") from exc
    username = connection.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username is required")
    wodbuster_document(user_id(user)).set({
        "username_ciphertext": cipher.encrypt(username),
        "password_ciphertext": cipher.encrypt(connection.password),
        "username_hint": f"•••{username[-2:]}",
        "updated_at": datetime.now(timezone.utc),
        "verified_at": None,
    })
    return {"configured": True, "verified": False, "usernameHint": f"•••{username[-2:]}"}


def wodbuster_connection_data(uid: str) -> dict[str, object] | None:
    return load_wodbuster_connection(uid)


def wodbuster_client(uid: str) -> tuple[WodBusterClient, dict[str, object]]:
    data = wodbuster_connection_data(uid)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WodBuster is not configured")
    try:
        cipher = CredentialCipher(settings.encryption_key)
        username = cipher.decrypt(str(data["username_ciphertext"]))
        password = cipher.decrypt(str(data["password_ciphertext"]))
    except (EncryptionUnavailable, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Credential vault unavailable") from exc
    return WodBusterClient(username, password), data


@app.post("/v1/connections/wodbuster/test", include_in_schema=False)
def test_wodbuster_connection(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    uid = user_id(user)
    client, data = wodbuster_client(uid)
    try:
        box_url = client.box_url()
    except InvalidCredentials as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Usuario o contraseña de WodBuster incorrectos") from exc
    except WodBusterError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="WodBuster no respondió correctamente") from exc
    wodbuster_document(uid).set({"verified_at": datetime.now(timezone.utc), "box_url_ciphertext": CredentialCipher(settings.encryption_key).encrypt(box_url)}, merge=True)
    return {"verified": True, "usernameHint": data.get("username_hint")}


@app.get("/v1/reservations", include_in_schema=False)
def future_reservations(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    uid = user_id(user)
    client, data = wodbuster_client(uid)
    try:
        cipher = CredentialCipher(settings.encryption_key)
        box_url = cipher.decrypt(str(data["box_url_ciphertext"])) if data.get("box_url_ciphertext") else client.box_url()
        reservations = client.future_confirmed_reservations(box_url)
    except InvalidCredentials as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La sesión WodBuster ya no es válida") from exc
    except WodBusterError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudieron leer las reservas de WodBuster") from exc
    return {"reservations": reservations}


@app.get("/v1/schedules", include_in_schema=False)
def schedules(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    docs = schedules_collection(user_id(user)).where("active", "==", True).stream()
    items = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return {"schedules": sorted(items, key=lambda item: (item["weekday"], item["class_time"]))}


@app.post("/v1/schedules", include_in_schema=False)
def create_schedule(schedule: ScheduleInput, user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    collection = schedules_collection(user_id(user))
    duplicate = next((doc for doc in collection.where("active", "==", True).stream() if doc.to_dict().get("weekday") == schedule.weekday and doc.to_dict().get("class_time") == schedule.class_time), None)
    if duplicate:
        return {"id": duplicate.id, **duplicate.to_dict()}
    document = collection.document()
    payload = {
        "weekday": schedule.weekday,
        "class_time": schedule.class_time,
        "launch_time": schedule.launch_time,
        "active": True,
        "created_at": datetime.now(timezone.utc),
        "last_run_week": None,
    }
    document.set(payload)
    return {"id": document.id, **payload}


@app.delete("/v1/schedules/{schedule_id}", include_in_schema=False)
def disable_schedule(schedule_id: str, user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, bool]:
    document = schedules_collection(user_id(user)).document(schedule_id)
    if not document.get().exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    document.update({"active": False, "updated_at": datetime.now(timezone.utc)})
    return {"disabled": True}


@app.get("/v1/availability-watches", include_in_schema=False)
def availability_watches(user: dict[str, object] = Depends(verified_firebase_user)) -> dict[str, object]:
    docs = availability_watches_collection(user_id(user)).where("active", "==", True).stream()
    items = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return {"watches": sorted(items, key=lambda item: (item["class_date"], item["class_time"]))}


@app.post("/v1/availability-watches", include_in_schema=False)
def create_availability_watch(
    watch: AvailabilityWatchInput,
    user: dict[str, object] = Depends(verified_firebase_user),
) -> dict[str, object]:
    if watch.class_date < datetime.now().date():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La clase ya ha pasado")
    collection = availability_watches_collection(user_id(user))
    active_watches = list(collection.where("active", "==", True).stream())
    if len(active_watches) >= 3:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Máximo de tres vigilancias activas por cuenta",
        )
    duplicate = next(
        (
            doc
            for doc in active_watches
            if doc.to_dict().get("class_date") == watch.class_date.isoformat()
            and doc.to_dict().get("class_time") == watch.class_time
        ),
        None,
    )
    if duplicate:
        return {"id": duplicate.id, **duplicate.to_dict()}
    document = collection.document()
    payload = {
        "class_date": watch.class_date.isoformat(),
        "class_time": watch.class_time,
        "active": True,
        "created_at": datetime.now(timezone.utc),
        "last_result": "Vigilando plazas libres cada 10 minutos",
        "last_checked_at": None,
    }
    document.set(payload)
    return {"id": document.id, **payload}


@app.delete("/v1/availability-watches/{watch_id}", include_in_schema=False)
def disable_availability_watch(
    watch_id: str, user: dict[str, object] = Depends(verified_firebase_user)
) -> dict[str, bool]:
    document = availability_watches_collection(user_id(user)).document(watch_id)
    if not document.get().exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    document.update({"active": False, "updated_at": datetime.now(timezone.utc), "last_result": "Cancelada"})
    return {"disabled": True}


@app.put("/v1/push-subscriptions", include_in_schema=False)
def save_push_subscription(
    subscription: PushSubscriptionInput, user: dict[str, object] = Depends(verified_firebase_user)
) -> dict[str, bool]:
    if not subscription.keys.get("p256dh") or not subscription.keys.get("auth"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Suscripción push incompleta")
    push_subscriptions_collection(user_id(user)).document(subscription.endpoint.rsplit("/", 1)[-1]).set(
        subscription.model_dump()
    )
    return {"subscribed": True}


@app.post("/internal/run-friday-bookings", include_in_schema=False)
def run_friday_bookings(x_worker_token: str | None = Header(default=None)) -> dict[str, object]:
    if not settings.worker_token or x_worker_token != settings.worker_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Worker authentication failed")
    if not settings.encryption_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Credential vault unavailable")
    return {"runs": run_due_schedules(settings.encryption_key)}


@app.post("/internal/run-availability-watches", include_in_schema=False)
def run_between_week_bookings(x_worker_token: str | None = Header(default=None)) -> dict[str, object]:
    if not settings.worker_token or x_worker_token != settings.worker_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Worker authentication failed")
    if not settings.encryption_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Credential vault unavailable")
    return {
        "runs": run_availability_watches(
            settings.encryption_key, settings.vapid_private_key, settings.vapid_subject
        )
    }
