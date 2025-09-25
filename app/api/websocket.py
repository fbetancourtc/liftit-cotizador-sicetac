"""
WebSocket endpoints for real-time price updates.
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from app.services.realtime import connection_manager, price_monitor
from app.core.auth import get_current_user_ws

logger = logging.getLogger("websocket")

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time price updates.

    Client can send messages:
    - {"action": "subscribe", "route_id": "origin:destination:config"}
    - {"action": "unsubscribe", "route_id": "origin:destination:config"}
    - {"action": "ping"} - Keep alive

    Server sends:
    - {"type": "price_update", "route_id": "...", "price": ..., "timestamp": ...}
    - {"type": "subscription_confirmed", "route_id": "..."}
    - {"type": "error", "message": "..."}
    """
    user_id = "anonymous"

    try:
        # Authenticate user if token provided
        if token:
            try:
                user = await get_current_user_ws(token)
                user_id = user.get("email", "authenticated")
            except:
                # Allow anonymous connections for public price viewing
                pass

        await connection_manager.connect(websocket, user_id)

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Liftit real-time pricing",
            "user_id": user_id
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                route_id = data.get("route_id")
                if route_id:
                    await connection_manager.subscribe_to_route(websocket, route_id)
                    logger.info(f"User {user_id} subscribed to {route_id}")

            elif action == "unsubscribe":
                route_id = data.get("route_id")
                if route_id:
                    await connection_manager.unsubscribe_from_route(websocket, route_id)
                    logger.info(f"User {user_id} unsubscribed from {route_id}")

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

            elif action == "refresh":
                route_id = data.get("route_id")
                if route_id and price_monitor:
                    await price_monitor.trigger_manual_update(route_id)

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected")

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        connection_manager.disconnect(websocket, user_id)


@router.websocket("/ws/admin")
async def admin_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    Admin WebSocket endpoint for monitoring all price updates.
    Requires authentication.
    """
    try:
        # Authenticate admin user
        user = await get_current_user_ws(token)
        user_email = user.get("email", "")

        # Check if user is admin (from liftit.co domain)
        if not user_email.endswith("@liftit.co"):
            await websocket.close(code=1008, reason="Unauthorized")
            return

        await connection_manager.connect(websocket, f"admin_{user_email}")

        # Auto-subscribe admin to all routes for monitoring
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to admin monitoring",
            "user": user_email,
            "mode": "monitor_all"
        })

        while True:
            data = await websocket.receive_json()

            # Admin commands
            if data.get("action") == "get_stats":
                # Send current connection stats
                stats = {
                    "type": "stats",
                    "total_connections": len(connection_manager.active_connections),
                    "total_subscriptions": sum(
                        len(subs) for subs in connection_manager.user_subscriptions.values()
                    )
                }
                await websocket.send_json(stats)

            elif data.get("action") == "broadcast":
                # Allow admin to broadcast messages
                message = data.get("message")
                if message:
                    for connections in connection_manager.active_connections.values():
                        for conn in connections:
                            try:
                                await conn.send_json({
                                    "type": "broadcast",
                                    "message": message,
                                    "from": "admin"
                                })
                            except:
                                pass

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, f"admin_{user_email}")
        logger.info(f"Admin {user_email} disconnected")

    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")