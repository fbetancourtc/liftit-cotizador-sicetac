"""
Production caching service with Redis and in-memory fallback.
"""

import json
import hashlib
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
import asyncio

logger = logging.getLogger("cache")


class CacheService:
    """
    Multi-tier caching service with Redis and in-memory fallback.
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "memory_hits": 0,
            "redis_hits": 0
        }

    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate a consistent cache key from parameters."""
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
        return f"{prefix}:{param_hash}"

    async def get(
        self,
        key: str,
        default: Any = None
    ) -> Optional[Any]:
        """
        Get value from cache (Redis first, then memory).
        """
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    value = await self.redis_client.get(key)
                    if value:
                        self.cache_stats["hits"] += 1
                        self.cache_stats["redis_hits"] += 1
                        return json.loads(value) if isinstance(value, str) else value
                except Exception as e:
                    logger.warning(f"Redis get error: {e}")
                    self.cache_stats["errors"] += 1

            # Fall back to memory cache
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if entry["expires_at"] > datetime.utcnow():
                    self.cache_stats["hits"] += 1
                    self.cache_stats["memory_hits"] += 1
                    return entry["value"]
                else:
                    # Expired, remove it
                    del self.memory_cache[key]

            self.cache_stats["misses"] += 1
            return default

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["errors"] += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300  # 5 minutes default
    ) -> bool:
        """
        Set value in cache (both Redis and memory).
        """
        try:
            # Serialize value
            serialized = json.dumps(value) if not isinstance(value, str) else value

            # Store in Redis
            if self.redis_client:
                try:
                    await self.redis_client.setex(key, ttl, serialized)
                except Exception as e:
                    logger.warning(f"Redis set error: {e}")
                    self.cache_stats["errors"] += 1

            # Store in memory cache with expiration
            self.memory_cache[key] = {
                "value": value,
                "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
            }

            # Limit memory cache size
            if len(self.memory_cache) > 1000:
                self._cleanup_memory_cache()

            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            # Delete from Redis
            if self.redis_client:
                try:
                    await self.redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Redis delete error: {e}")

            # Delete from memory
            if key in self.memory_cache:
                del self.memory_cache[key]

            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        count = 0

        # Clear from Redis
        if self.redis_client:
            try:
                async for key in self.redis_client.scan_iter(pattern):
                    await self.redis_client.delete(key)
                    count += 1
            except Exception as e:
                logger.warning(f"Redis clear pattern error: {e}")

        # Clear from memory
        keys_to_delete = [
            k for k in self.memory_cache.keys()
            if pattern.replace("*", "") in k
        ]
        for key in keys_to_delete:
            del self.memory_cache[key]
            count += 1

        return count

    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry["expires_at"] <= now
        ]
        for key in expired_keys:
            del self.memory_cache[key]

        # If still too large, remove oldest entries
        if len(self.memory_cache) > 800:
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1]["expires_at"]
            )
            for key, _ in sorted_entries[:200]:
                del self.memory_cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0 else 0
        )

        return {
            **self.cache_stats,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache),
            "redis_available": bool(self.redis_client)
        }


def cache_result(
    prefix: str = "api",
    ttl: int = 300,
    key_params: Optional[list] = None
):
    """
    Decorator for caching function results.

    Usage:
        @cache_result(prefix="quote", ttl=600, key_params=["origin", "destination"])
        async def get_quote(origin, destination, config):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache service from app state or create default
            from app.core.config import get_settings
            cache_service = getattr(
                get_settings(),
                "cache_service",
                CacheService()
            )

            # Generate cache key
            if key_params:
                cache_params = {
                    param: kwargs.get(param)
                    for param in key_params
                    if param in kwargs
                }
            else:
                cache_params = kwargs

            cache_key = cache_service._generate_cache_key(
                f"{prefix}:{func.__name__}",
                cache_params
            )

            # Try to get from cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_service.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


class QuoteCache:
    """
    Specialized cache for quote data with smart invalidation.
    """

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.quote_ttl = 300  # 5 minutes for quotes
        self.route_ttl = 3600  # 1 hour for route data

    async def get_quote(
        self,
        origin: str,
        destination: str,
        config: str,
        period: str
    ) -> Optional[Dict]:
        """Get cached quote."""
        key = f"quote:{origin}:{destination}:{config}:{period}"
        return await self.cache.get(key)

    async def set_quote(
        self,
        origin: str,
        destination: str,
        config: str,
        period: str,
        quote_data: Dict
    ):
        """Cache quote data."""
        key = f"quote:{origin}:{destination}:{config}:{period}"
        await self.cache.set(key, quote_data, self.quote_ttl)

        # Also cache route info
        route_key = f"route:{origin}:{destination}"
        await self.cache.set(
            route_key,
            {"distance": quote_data.get("distance"), "active": True},
            self.route_ttl
        )

    async def invalidate_route(self, origin: str, destination: str):
        """Invalidate all quotes for a route."""
        pattern = f"quote:{origin}:{destination}:*"
        count = await self.cache.clear_pattern(pattern)
        logger.info(f"Invalidated {count} quotes for {origin}-{destination}")

    async def warm_cache(self, popular_routes: list):
        """Pre-warm cache with popular routes."""
        from app.services.sicetac import SicetacClient
        from app.core.config import get_settings

        client = SicetacClient(get_settings())
        warmed = 0

        for route in popular_routes:
            try:
                # Fetch and cache quote
                quote_data = await client.fetch_quotes(route)
                await self.set_quote(
                    route["origin"],
                    route["destination"],
                    route["configuration"],
                    route["period"],
                    quote_data
                )
                warmed += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for route: {e}")

        logger.info(f"Warmed cache with {warmed} routes")


# Global cache instance
cache_service: Optional[CacheService] = None


async def initialize_cache():
    """Initialize cache service."""
    global cache_service

    try:
        # Try to connect to Redis
        import redis.asyncio as redis
        redis_client = await redis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Connected to Redis cache")
    except:
        logger.warning("Redis not available, using memory cache only")
        redis_client = None

    cache_service = CacheService(redis_client)
    return cache_service