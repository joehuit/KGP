"""Idempotency service for duplicate request detection and safe response replays."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import threading
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import ConflictError
from app.models.idempotency import IdempotencyKey


def compute_request_hash(
    path: str,
    customer_identifier: str,
    payload: Any,
) -> str:
    """Compute deterministic SHA-256 hash of the request path, customer, and payload."""
    serialized = json.dumps(payload, sort_keys=True, default=str) if payload is not None else ""
    raw = f"{path}|{customer_identifier}|{serialized}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class IdempotencyService:
    """Handles idempotency checking, conflict detection, and response caching."""

    _locks: Dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    @classmethod
    def get_lock_for_key(cls, key: str) -> threading.Lock:
        """Retrieve or create an in-process synchronization lock for an active idempotency key."""
        with cls._global_lock:
            if key not in cls._locks:
                cls._locks[key] = threading.Lock()
            return cls._locks[key]

    @classmethod
    def release_lock_if_empty(cls, key: str) -> None:
        """Cleanup lock mapping when no longer contested."""
        with cls._global_lock:
            cls._locks.pop(key, None)

    @staticmethod
    def get_existing_response(
        db: Session,
        key: str,
        request_hash: str,
    ) -> Optional[Tuple[int, Dict[str, Any]]]:
        """Check if an idempotency key has already been executed.
        Returns:
            Tuple of (status_code, response_data) if key exists and hash matches.
        Raises:
            ConflictError if key exists but the payload hash differs.
        """
        existing = db.scalar(select(IdempotencyKey).where(IdempotencyKey.key == key))
        if not existing:
            return None

        # Detect conflicting payload reuse
        if existing.request_hash != request_hash:
            raise ConflictError(
                "Idempotency key conflict: A request with this Idempotency-Key has already been "
                "processed with different parameters or payload."
            )

        try:
            cached_data = json.loads(existing.response_body)
        except Exception:
            cached_data = {"data": existing.response_body}

        return existing.response_code, cached_data

    @staticmethod
    def save_response(
        db: Session,
        key: str,
        request_hash: str,
        response_code: int,
        response_data: Any,
        retention_hours: int = 24,
    ) -> IdempotencyKey:
        """Persist execution result for future idempotent replays."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=retention_hours)

        if isinstance(response_data, str):
            body_str = response_data
        else:
            body_str = json.dumps(response_data, default=str)

        record = IdempotencyKey(
            key=key,
            request_hash=request_hash,
            response_code=response_code,
            response_body=body_str,
            expires_at=expires_at,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
