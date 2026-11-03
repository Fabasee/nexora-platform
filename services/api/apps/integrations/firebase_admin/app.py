"""Lazy Firebase Admin app factory.

This module deliberately performs no credential loading or network work at import time.
Keep Firebase SDK usage inside this infrastructure boundary.
"""
from __future__ import annotations

import os
from pathlib import Path
from threading import Lock

import firebase_admin
from firebase_admin import credentials


class FirebaseConfigurationError(RuntimeError):
    """Raised when Firebase Admin is requested without explicit configuration."""


class FirebaseAdminAppFactory:
    _lock = Lock()

    @classmethod
    def get_app(cls, name: str = "[DEFAULT]"):
        try:
            return firebase_admin.get_app(name)
        except ValueError:
            pass

        with cls._lock:
            try:
                return firebase_admin.get_app(name)
            except ValueError:
                return cls._initialize(name)

    @classmethod
    def _initialize(cls, name: str):
        project_id = os.environ.get("FIREBASE_PROJECT_ID")
        credentials_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")

        if not project_id:
            raise FirebaseConfigurationError(
                "FIREBASE_PROJECT_ID is required before Firebase Admin is used."
            )
        if not credentials_path:
            raise FirebaseConfigurationError(
                "FIREBASE_CREDENTIALS_PATH must point to a secret managed outside source control."
            )

        path = Path(credentials_path).expanduser()
        if not path.is_file():
            raise FirebaseConfigurationError("Configured Firebase credentials file does not exist.")

        credential = credentials.Certificate(str(path))
        return firebase_admin.initialize_app(
            credential,
            options={"projectId": project_id},
            name=name,
        )
