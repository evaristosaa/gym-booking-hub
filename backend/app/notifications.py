"""Best-effort Web Push delivery. Failed subscriptions never affect bookings."""

from __future__ import annotations

import json

from firebase_admin import firestore
from pywebpush import WebPushException, webpush

from .store import push_subscriptions_collection


def notify_booking(uid: str, title: str, body: str, vapid_private_key: str | None, vapid_subject: str) -> None:
    if not vapid_private_key:
        return
    payload = json.dumps({"title": title, "body": body, "url": "./"})
    for snapshot in push_subscriptions_collection(uid).stream():
        subscription = snapshot.to_dict()
        try:
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": vapid_subject},
            )
        except WebPushException as exc:
            # A 404/410 subscription has expired and is safe to discard.
            if getattr(exc.response, "status_code", None) in {404, 410}:
                snapshot.reference.delete()
        except (TypeError, ValueError):
            snapshot.reference.delete()
