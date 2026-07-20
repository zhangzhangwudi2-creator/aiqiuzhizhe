"""Small in-memory quota helpers for a single-instance demo deployment."""

import hashlib
import time
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from typing import Any


def build_cache_key(operation: str, resume_text: str, jd_text: str) -> str:
    payload = f"v1\0{operation}\0{resume_text}\0{jd_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, max_entries: int = 100, ttl_seconds: int = 21_600):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str):
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at <= time.monotonic():
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return entry.value

    def set(self, key: str, value: Any) -> None:
        self._entries[key] = CacheEntry(value=value, expires_at=time.monotonic() + self.ttl_seconds)
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 3_600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, identity: str) -> tuple[bool, int]:
        now = time.monotonic()
        events = self._requests[identity]
        cutoff = now - self.window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= self.max_requests:
            retry_after = max(1, int(events[0] + self.window_seconds - now) + 1)
            return False, retry_after
        events.append(now)
        return True, 0

    def clear(self) -> None:
        self._requests.clear()
