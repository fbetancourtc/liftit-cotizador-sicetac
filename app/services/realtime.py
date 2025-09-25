"""
Real-time price update service using WebSockets and Redis caching.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger("realtime")


class PriceUpdate(BaseModel):
    """Real-time price update model."""

    route_id: str
    origin: str
    destination: str
    configuration: str
    price: float
    previous_price: Optional[float] = None
    change_percentage: Optional[float] = None
    timestamp: datetime
    source: str = "sicetac"


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.user_subscriptions[websocket] = set()
        logger.info(f"User {user_id} connected via WebSocket")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if websocket in self.user_subscriptions:
            del self.user_subscriptions[websocket]
        logger.info(f"User {user_id} disconnected from WebSocket")

    async def subscribe_to_route(self, websocket: WebSocket, route_id: str):
        """Subscribe a connection to price updates for a specific route."""
        if websocket in self.user_subscriptions:
            self.user_subscriptions[websocket].add(route_id)
            await websocket.send_json({
                "type": "subscription_confirmed",
                "route_id": route_id,
                "timestamp": datetime.utcnow().isoformat()
            })

    async def unsubscribe_from_route(self, websocket: WebSocket, route_id: str):
        """Unsubscribe a connection from a specific route."""
        if websocket in self.user_subscriptions:
            self.user_subscriptions[websocket].discard(route_id)
            await websocket.send_json({
                "type": "unsubscription_confirmed",
                "route_id": route_id,
                "timestamp": datetime.utcnow().isoformat()
            })

    async def broadcast_price_update(self, update: PriceUpdate):
        """Broadcast a price update to all subscribed connections."""
        route_id = update.route_id
        update_data = update.dict()
        update_data["timestamp"] = update.timestamp.isoformat()
        update_data["type"] = "price_update"

        # Send to all connections subscribed to this route
        for websocket, subscriptions in self.user_subscriptions.items():
            if route_id in subscriptions:
                try:
                    await websocket.send_json(update_data)
                except Exception as e:
                    logger.error(f"Error sending update to websocket: {e}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a personal message to a specific connection."""
        await websocket.send_json({
            "type": "message",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })


class PriceCache:
    """Redis-based price caching service."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 300  # 5 minutes

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()

    def _generate_key(self, origin: str, destination: str, config: str, period: str) -> str:
        """Generate a cache key for a route."""
        return f"price:{origin}:{destination}:{config}:{period}"

    async def get_price(
        self,
        origin: str,
        destination: str,
        config: str,
        period: str
    ) -> Optional[Dict]:
        """Get cached price for a route."""
        if not self.redis_client:
            return None

        key = self._generate_key(origin, destination, config, period)
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    async def set_price(
        self,
        origin: str,
        destination: str,
        config: str,
        period: str,
        price_data: Dict,
        ttl: Optional[int] = None
    ):
        """Cache price data for a route."""
        if not self.redis_client:
            return

        key = self._generate_key(origin, destination, config, period)
        ttl = ttl or self.default_ttl

        try:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(price_data)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def invalidate_route(self, origin: str, destination: str):
        """Invalidate all cached prices for a route."""
        if not self.redis_client:
            return

        pattern = f"price:{origin}:{destination}:*"
        try:
            async for key in self.redis_client.scan_iter(pattern):
                await self.redis_client.delete(key)
            logger.info(f"Invalidated cache for route {origin}-{destination}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    async def get_stats(self) -> Dict:
        """Get cache statistics."""
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = await self.redis_client.info("stats")
            return {
                "status": "connected",
                "total_connections": info.get("total_connections_received", 0),
                "commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}


class PriceMonitor:
    """Monitor and track price changes."""

    def __init__(self, cache: PriceCache, manager: ConnectionManager):
        self.cache = cache
        self.manager = manager
        self.monitoring = False
        self.poll_interval = 60  # 1 minute

    async def start_monitoring(self):
        """Start monitoring price changes."""
        self.monitoring = True
        logger.info("Price monitoring started")

        while self.monitoring:
            try:
                # In production, this would poll Sicetac API for price updates
                # For now, we'll simulate price changes
                await self._check_price_updates()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)

    async def stop_monitoring(self):
        """Stop monitoring price changes."""
        self.monitoring = False
        logger.info("Price monitoring stopped")

    async def _check_price_updates(self):
        """Check for price updates from Sicetac API."""
        # This would be implemented to:
        # 1. Query Sicetac API for latest prices
        # 2. Compare with cached prices
        # 3. Broadcast updates if prices changed
        # 4. Update cache with new prices
        pass

    async def trigger_manual_update(self, route_id: str):
        """Manually trigger a price update for a specific route."""
        # Parse route_id to get origin, destination, config
        parts = route_id.split(":")
        if len(parts) >= 3:
            origin, destination, config = parts[:3]

            # Fetch fresh price from Sicetac
            # For now, simulate an update
            update = PriceUpdate(
                route_id=route_id,
                origin=origin,
                destination=destination,
                configuration=config,
                price=150000.0,
                previous_price=145000.0,
                change_percentage=3.4,
                timestamp=datetime.utcnow()
            )

            await self.manager.broadcast_price_update(update)


# Global instances
connection_manager = ConnectionManager()
price_cache = PriceCache()
price_monitor = None


async def initialize_realtime_services():
    """Initialize real-time services on startup."""
    global price_monitor

    await price_cache.connect()
    price_monitor = PriceMonitor(price_cache, connection_manager)

    # Start background monitoring
    asyncio.create_task(price_monitor.start_monitoring())

    logger.info("Real-time services initialized")


async def shutdown_realtime_services():
    """Shutdown real-time services."""
    global price_monitor

    if price_monitor:
        await price_monitor.stop_monitoring()

    await price_cache.disconnect()

    logger.info("Real-time services shutdown")