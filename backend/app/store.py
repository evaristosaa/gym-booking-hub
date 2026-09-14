"""Server-only Firestore persistence for encrypted provider connections."""

from __future__ import annotations

from firebase_admin import firestore


def wodbuster_document(uid: str):
    return firestore.client().collection("users").document(uid).collection("private").document("wodbuster")


def wodbuster_connection(uid: str) -> dict[str, object] | None:
    snapshot = wodbuster_document(uid).get()
    return snapshot.to_dict() if snapshot.exists else None


def schedules_collection(uid: str):
    return firestore.client().collection("users").document(uid).collection("schedules")


def availability_watches_collection(uid: str):
    """One-off watches that keep looking for a cancelled place in a class."""
    return firestore.client().collection("users").document(uid).collection("availability_watches")


def push_subscriptions_collection(uid: str):
    return firestore.client().collection("users").document(uid).collection("push_subscriptions")
