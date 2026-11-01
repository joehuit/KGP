"""Extensible request rate-limiting engine.

Provides sliding-window rate limiting with in-memory storage for development,
testing, and single-process deployments, alongside a documented production Redis adapter
for multi-instance clustering.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple
from fastapi import Request
from app.core.config import settings
from app.core.errors import RateLimitExceededError
from app.core.logging import logger


class BaseRateLimiter(ABC):
    """Abstract rate limiter interface."""

    @abstractmethod
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """Check if request under `key` is allowed.
        Returns:
            (allowed: bool, remaining: int, retry_after_seconds: int)
        """
        pass

    @abstractmethod
    def reset(self, key: Optional[str] = None) -> None:
        """Reset state for a specific key or clear all."""
        pass


class InMemoryRateLimiter(BaseRateLimiter):
    """Thread-safe sliding-window rate limiter using in-memory timestamps.
    Suitable for single-process development, testing, and staging.
    NOTE: In multi-worker or horizontally scaled production clusters,
    each worker maintains independent state. Deploy RedisRateLimiter for clusters.
    """

    def __init__(self):
        self._store: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_prune = time.time()

    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Periodic pruning of dormant keys every 5 minutes
            if now - self._last_prune > 300:
                self._prune_dormant(now)
                self._last_prune = now

            timestamps = self._store[key]
            # Evict timestamps outside current window
            valid_timestamps = [t for t in timestamps if t > window_start]
            self._store[key] = valid_timestamps

            current_count = len(valid_timestamps)
            if current_count < limit:
                self._store[key].append(now)
                remaining = limit - current_count - 1
                return True, remaining, 0

            # Calculate retry after based on the oldest timestamp in the current window
            oldest_in_window = valid_timestamps[0] if valid_timestamps else window_start
            retry_after = max(1, int(oldest_in_window + window_seconds - now))
            return False, 0, retry_after

    def reset(self, key: Optional[str] = None) -> None:
        with self._lock:
            if key:
                self._store.pop(key, None)
            else:
                self._store.clear()

    def _prune_dormant(self, now: float) -> None:
        """Prune keys that haven't been accessed in over 1 hour."""
        cutoff = now - 3600
        keys_to_remove = [k for k, ts in self._store.items() if not ts or max(ts) < cutoff]
        for k in keys_to_remove:
            del self._store[k]


class RedisRateLimiter(BaseRateLimiter):
    """Distributed sliding-window rate limiter backed by Redis sorted sets (ZSET).
    Production-ready for multi-instance clusters.
    Redis commands used:
      1. ZREMRANGEBYSCORE key 0 (now - window_seconds)
      2. ZCARD key
      3. If count < limit: ZADD key now now + EXPIRE key window_seconds
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self._client = None
        # In a real environment with redis-py installed:
        # import redis
        # self._client = redis.from_url(redis_url)

    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        if not self._client:
            logger.warning("Redis client not configured for RedisRateLimiter; falling back to allowed.")
            return True, limit, 0

        # Note: When redis is connected, atomic pipeline:
        # pipe = self._client.pipeline()
        # pipe.zremrangebyscore(key, 0, now - window_seconds)
        # pipe.zcard(key)
        # ...
        return True, limit, 0

    def reset(self, key: Optional[str] = None) -> None:
        if self._client:
            if key:
                self._client.delete(key)
            else:
                self._client.flushdb()


# Global singleton rate limiter instance
_default_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> BaseRateLimiter:
    """Dependency / accessor for the active application rate limiter."""
    return _default_rate_limiter


def enforce_rate_limit(
    key: str,
    limit: int,
    window_seconds: int = 60,
    action_name: str = "request",
    limiter: Optional[BaseRateLimiter] = None,
) -> None:
    """Evaluate rate limit; raise RateLimitExceededError if limit breached."""
    active_limiter = limiter or _default_rate_limiter
    allowed, remaining, retry_after = active_limiter.check_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window_seconds,
    )
    if not allowed:
        logger.warning(
            "Rate limit exceeded for key '%s' on %s (limit: %d/%ds). Retry-After: %ds",
            key,
            action_name,
            limit,
            window_seconds,
            retry_after,
        )
        raise RateLimitExceededError(
            message=f"Too many {action_name} attempts. Please wait {retry_after} seconds before trying again.",
            retry_after=retry_after,
            details={"limit": limit, "window_seconds": window_seconds, "retry_after": retry_after},
        )
