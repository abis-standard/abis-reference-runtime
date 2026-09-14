"""Lightweight in-memory rate limiting for external test gateway."""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class RateLimitState:
    requests_per_minute: int
    max_concurrent: int
    _minute_buckets: dict[str, deque[float]] = field(default_factory=dict)
    _active: dict[str, int] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def allow(self, client_key: str) -> tuple[bool, str | None]:
        now = time.monotonic()
        with self._lock:
            active = self._active.get(client_key, 0)
            if active >= self.max_concurrent:
                return False, "concurrent_limit"
            bucket = self._minute_buckets.setdefault(client_key, deque())
            while bucket and now - bucket[0] > 60.0:
                bucket.popleft()
            if len(bucket) >= self.requests_per_minute:
                return False, "requests_per_minute"
            bucket.append(now)
            self._active[client_key] = active + 1
            return True, None

    def release(self, client_key: str) -> None:
        with self._lock:
            active = self._active.get(client_key, 0)
            if active <= 1:
                self._active.pop(client_key, None)
            else:
                self._active[client_key] = active - 1
