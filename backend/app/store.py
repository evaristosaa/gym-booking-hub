"""Server-only Firestore persistence for encrypted provider connections."""

from __future__ import annotations

from firebase_admin import firestore


def wodbuster_document(uid: str):
    return firestore.client().collection("users").document(uid).collection("private").document("wodbuster")


def wodbuster_connection(uid: str) -> dict[str, object] | None:
    snapshot = wodbuster_document(uid).get()
    return snapshot.to_dict() if snapshot.exists else None
