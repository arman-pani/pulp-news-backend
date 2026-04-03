from __future__ import annotations

import json
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import get_settings


settings = get_settings()


def _build_credentials() -> credentials.Base:
    if settings.firebase_credentials_json:
        return credentials.Certificate(json.loads(settings.firebase_credentials_json))
    raise ValueError("Firebase credentials are not configured. Set FIREBASE_CREDENTIALS_JSON.")


@lru_cache
def get_firebase_app() -> firebase_admin.App:
    if firebase_admin._apps:
        return firebase_admin.get_app()

    credential = _build_credentials()
    return firebase_admin.initialize_app(credential=credential)


def get_messaging() -> messaging:
    get_firebase_app()
    return messaging
