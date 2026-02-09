"""Simple TTL cache for articles."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with expiration."""

    value: T
    expires_at: float


@dataclass
class TTLCache(Generic[T]):
    """Simple in-memory TTL cache."""

    ttl_seconds: int = 1800  # 30 minutes default
    _cache: Dict[str, CacheEntry[T]] = field(default_factory=dict)

    def get(self, key: str) -> Optional[T]:
        """Get value from cache if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None

        if time.time() > entry.expires_at:
            # Entry expired, remove it
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + ttl,
        )

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns number of removed entries."""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() if now > entry.expires_at
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def __contains__(self, key: str) -> bool:
        """Check if key exists and not expired."""
        return self.get(key) is not None

    def __len__(self) -> int:
        """Return number of entries (including possibly expired)."""
        return len(self._cache)


# Global cache instances
articles_cache: TTLCache[Any] = TTLCache(ttl_seconds=1800)  # 30 minutes
digest_cache: TTLCache[Any] = TTLCache(ttl_seconds=300)  # 5 minutes
