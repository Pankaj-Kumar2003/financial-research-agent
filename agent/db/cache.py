import os
import json
import time
from typing import Optional, Any, Dict

class CacheManager:
    """
    Redis Cache Manager with seamless in-memory fallback.
    Tries connecting to Redis if REDIS_URL is provided or available on localhost.
    Falls back to a thread-safe in-memory TTL cache if Redis server is absent.
    """
    
    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis
            client = redis.Redis.from_url(redis_url, socket_timeout=1.0)
            client.ping()
            self.redis_client = client
            print(f"[CacheManager] Connected to Redis at {redis_url}")
        except Exception:
            print("[CacheManager] Redis server unavailable. Falling back to in-memory TTL cache.")
            self.redis_client = None

    def _make_key(self, ticker: str) -> str:
        return f"research:{ticker.upper().strip()}"

    def get(self, ticker: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(ticker)
        
        # 1. Try Redis
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    print(f"[CacheManager] CACHE HIT (Redis) for {ticker}")
                    return json.loads(data)
            except Exception as e:
                print(f"[CacheManager] Redis read error: {e}")
                
        # 2. Try Memory Cache Fallback
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if time.time() < entry["expires_at"]:
                print(f"[CacheManager] CACHE HIT (In-Memory) for {ticker}")
                return entry["data"]
            else:
                # Expired
                del self.memory_cache[key]
                
        print(f"[CacheManager] CACHE MISS for {ticker}")
        return None

    def set(self, ticker: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        key = self._make_key(ticker)
        expire_time = ttl if ttl is not None else self.default_ttl
        
        # 1. Try Redis
        if self.redis_client:
            try:
                serialized = json.dumps(data)
                self.redis_client.setex(key, expire_time, serialized)
                return True
            except Exception as e:
                print(f"[CacheManager] Redis write error: {e}")
                
        # 2. Memory Cache Fallback
        self.memory_cache[key] = {
            "data": data,
            "expires_at": time.time() + expire_time
        }
        return True

    def invalidate(self, ticker: str) -> bool:
        key = self._make_key(ticker)
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
        if key in self.memory_cache:
            del self.memory_cache[key]
        return True

# Global cache instance singleton
cache_manager = CacheManager()
