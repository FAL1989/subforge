"""
WebSocket connection manager for real-time updates
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasting
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(
        self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None
    ):
        """
        Accept and register a new WebSocket connection
        """
        try:
            await websocket.accept()
            self.active_connections.append(websocket)

            # Store connection metadata
            metadata = {
                "connected_at": datetime.utcnow(),
                "client_info": client_info or {},
                "message_count": 0,
                "last_activity": datetime.utcnow(),
            }
            self.connection_metadata[websocket] = metadata

            logger.info(
                f"WebSocket connected. Total connections: {len(self.active_connections)}"
            )

            # Send welcome message
            await self.send_personal_message(
                websocket,
                {
                    "type": "connection_established",
                    "data": {
                        "message": "Connected to SubForge Dashboard",
                        "timestamp": datetime.utcnow().isoformat(),
                        "connection_id": id(websocket),
                    },
                },
            )

        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if websocket in self.connection_metadata:
            metadata = self.connection_metadata.pop(websocket)
            duration = datetime.utcnow() - metadata["connected_at"]
            logger.info(
                f"WebSocket disconnected. Duration: {duration.total_seconds():.1f}s, "
                f"Messages sent: {metadata['message_count']}"
            )

        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def send_personal_message(
        self, websocket: WebSocket, message: Dict[str, Any]
    ):
        """
        Send a message to a specific WebSocket connection
        """
        try:
            message_with_timestamp = {
                **message,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await websocket.send_json(message_with_timestamp)

            # Update metadata
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["message_count"] += 1
                self.connection_metadata[websocket]["last_activity"] = datetime.utcnow()

        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            # Connection might be broken, remove it
            self.disconnect(websocket)

    async def broadcast_json(self, message: Dict[str, Any]):
        """
        Broadcast a JSON message to all connected clients
        """
        if not self.active_connections:
            return

        message_with_timestamp = {
            **message,
            "timestamp": datetime.utcnow().isoformat(),
            "broadcast_id": id(message),
        }

        # Create list copy to avoid modification during iteration
        connections_copy = self.active_connections.copy()
        disconnected_connections = []

        for connection in connections_copy:
            try:
                await connection.send_json(message_with_timestamp)

                # Update metadata
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["message_count"] += 1
                    self.connection_metadata[connection][
                        "last_activity"
                    ] = datetime.utcnow()

            except Exception as e:
                logger.warning(f"Failed to broadcast to connection: {e}")
                disconnected_connections.append(connection)

        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)

        if disconnected_connections:
            logger.info(
                f"Cleaned up {len(disconnected_connections)} disconnected WebSocket connections"
            )

    async def broadcast_text(self, message: str):
        """
        Broadcast a text message to all connected clients
        """
        if not self.active_connections:
            return

        connections_copy = self.active_connections.copy()
        disconnected_connections = []

        for connection in connections_copy:
            try:
                await connection.send_text(message)

                # Update metadata
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["message_count"] += 1
                    self.connection_metadata[connection][
                        "last_activity"
                    ] = datetime.utcnow()

            except Exception as e:
                logger.warning(f"Failed to broadcast text to connection: {e}")
                disconnected_connections.append(connection)

        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)

    def get_connection_count(self) -> int:
        """
        Get the number of active connections
        """
        return len(self.active_connections)

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all active connections
        """
        info = []
        current_time = datetime.utcnow()

        for connection in self.active_connections:
            metadata = self.connection_metadata.get(connection, {})
            connection_info = {
                "connection_id": id(connection),
                "connected_at": metadata.get("connected_at", current_time).isoformat(),
                "duration_seconds": (
                    current_time - metadata.get("connected_at", current_time)
                ).total_seconds(),
                "message_count": metadata.get("message_count", 0),
                "last_activity": metadata.get(
                    "last_activity", current_time
                ).isoformat(),
                "client_info": metadata.get("client_info", {}),
            }
            info.append(connection_info)

        return info

    async def ping_all_connections(self):
        """
        Send ping to all connections to check if they're still alive
        """
        if not self.active_connections:
            return

        ping_message = {
            "type": "ping",
            "data": {"timestamp": datetime.utcnow().isoformat()},
        }

        await self.broadcast_json(ping_message)

    async def cleanup_stale_connections(self, max_inactive_minutes: int = 30):
        """
        Clean up connections that haven't been active recently
        """
        current_time = datetime.utcnow()
        stale_connections = []

        for connection, metadata in self.connection_metadata.items():
            last_activity = metadata.get("last_activity", current_time)
            inactive_duration = current_time - last_activity

            if inactive_duration.total_seconds() > (max_inactive_minutes * 60):
                stale_connections.append(connection)

        for connection in stale_connections:
            logger.info(
                f"Cleaning up stale WebSocket connection (inactive for {max_inactive_minutes}+ minutes)"
            )
            try:
                await connection.close()
            except:
                pass
            self.disconnect(connection)

        return len(stale_connections)

    async def send_system_notification(
        self, notification_type: str, data: Dict[str, Any]
    ):
        """
        Send a system notification to all connected clients
        """
        notification = {
            "type": "system_notification",
            "notification_type": notification_type,
            "data": data,
        }

        await self.broadcast_json(notification)


# Global WebSocket manager instance
websocket_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint handler
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    client_info = {
        "host": client_host,
        "user_agent": websocket.headers.get("user-agent", "unknown"),
    }

    await websocket_manager.connect(websocket, client_info)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")

                # Handle different message types
                if message_type == "ping":
                    await websocket_manager.send_personal_message(
                        websocket,
                        {
                            "type": "pong",
                            "data": {"timestamp": datetime.utcnow().isoformat()},
                        },
                    )

                elif message_type == "subscribe":
                    # Handle subscription requests (if needed in future)
                    await websocket_manager.send_personal_message(
                        websocket,
                        {
                            "type": "subscription_acknowledged",
                            "data": message.get("data", {}),
                        },
                    )

                else:
                    logger.info(f"Received unhandled message type: {message_type}")

            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from WebSocket: {data}")

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


async def periodic_cleanup_task():
    """
    Periodic task to clean up stale connections and send pings
    """
    while True:
        try:
            # Clean up stale connections every 30 minutes
            await websocket_manager.cleanup_stale_connections()

            # Send ping every 5 minutes to keep connections alive
            await asyncio.sleep(300)  # 5 minutes
            await websocket_manager.ping_all_connections()

        except Exception as e:
            logger.error(f"Error in periodic cleanup task: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying