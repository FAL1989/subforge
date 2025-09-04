"""
SubForge Dashboard - Socket.IO Manager
Enhanced real-time communication with Socket.IO support
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from socketio import AsyncServer
from socketio.exceptions import DisconnectedError

from ..core.config import settings
from ..services.redis_service import redis_service
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SocketIOEvent(str, Enum):
    """Socket.IO event types"""

    # Connection events
    CONNECT = "connect"
    DISCONNECT = "disconnect"

    # Agent events
    AGENT_STATUS_UPDATE = "agent_status_update"
    AGENT_CONNECTED = "agent_connected"
    AGENT_DISCONNECTED = "agent_disconnected"

    # Task events
    TASK_UPDATE = "task_update"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # System events
    SYSTEM_METRICS_UPDATE = "system_metrics_update"
    SYSTEM_STATUS_CHANGE = "system_status_change"

    # Workflow events
    WORKFLOW_EVENT = "workflow_event"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"

    # Room events
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_UPDATE = "room_update"

    # System events
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class SocketIORoom(str, Enum):
    """Socket.IO room names for different dashboard sections"""

    AGENTS = "agents"
    TASKS = "tasks"
    METRICS = "metrics"
    WORKFLOWS = "workflows"
    SYSTEM = "system"
    DASHBOARD = "dashboard"  # Main dashboard room
    ADMIN = "admin"  # Admin-only room


@dataclass
class SocketIOMessage:
    """Socket.IO message structure"""

    event: str
    data: Dict[str, Any]
    room: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class ClientInfo:
    """Client connection information"""

    session_id: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    connected_at: Optional[str] = None
    rooms: Set[str] = None

    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.utcnow().isoformat()
        if self.rooms is None:
            self.rooms = set()


class SocketIOManager:
    """
    Enhanced Socket.IO manager for real-time communication

    Provides:
    - Room-based messaging
    - Event broadcasting
    - Connection management
    - Error handling and logging
    - Redis integration for scaling
    """

    def __init__(self):
        """Initialize Socket.IO manager"""
        self.sio: Optional[AsyncServer] = None
        self.clients: Dict[str, ClientInfo] = {}
        self.room_members: Dict[str, Set[str]] = {}
        self._initialize_rooms()

    def _initialize_rooms(self):
        """Initialize room member tracking"""
        for room in SocketIORoom:
            self.room_members[room.value] = set()

    def create_server(self) -> AsyncServer:
        """Create and configure Socket.IO server"""
        if self.sio is not None:
            return self.sio

        # Configure CORS settings
        cors_allowed_origins = [
            "http://localhost:3001",  # Frontend development server
            "http://127.0.0.1:3001",
            "http://localhost:3000",  # Alternative port
            "http://127.0.0.1:3000",
        ]

        if not settings.DEBUG:
            # Add production origins
            cors_allowed_origins.extend(settings.ALLOWED_ORIGINS)

        # Create Socket.IO server with async support
        self.sio = AsyncServer(
            cors_allowed_origins=cors_allowed_origins,
            cors_credentials=True,
            async_mode="asgi",
            logger=settings.DEBUG,
            engineio_logger=settings.DEBUG,
            ping_timeout=60,
            ping_interval=25,
        )

        # Register event handlers
        self._register_event_handlers()

        logger.info(
            "Socket.IO server created with CORS origins: %s", cors_allowed_origins
        )
        return self.sio

    def _register_event_handlers(self):
        """Register Socket.IO event handlers"""
        if not self.sio:
            raise RuntimeError("Socket.IO server not initialized")

        @self.sio.event
        async def connect(
            sid: str, environ: Dict[str, Any], auth: Optional[Dict[str, Any]] = None
        ):
            """Handle client connection"""
            try:
                # Extract client information
                user_agent = environ.get("HTTP_USER_AGENT", "unknown")
                ip_address = environ.get("REMOTE_ADDR", "unknown")

                client_info = ClientInfo(
                    session_id=sid, user_agent=user_agent, ip_address=ip_address
                )

                # Store client info
                self.clients[sid] = client_info

                # Auto-join dashboard room
                await self.sio.enter_room(sid, SocketIORoom.DASHBOARD.value)
                client_info.rooms.add(SocketIORoom.DASHBOARD.value)
                self.room_members[SocketIORoom.DASHBOARD.value].add(sid)

                # Notify connection
                await self.sio.emit(
                    SocketIOEvent.CONNECT,
                    {
                        "status": "connected",
                        "session_id": sid,
                        "timestamp": datetime.utcnow().isoformat(),
                        "available_rooms": [room.value for room in SocketIORoom],
                    },
                    room=sid,
                )

                # Store connection in Redis for scaling
                if redis_service.is_available():
                    await redis_service.set_json(
                        f"socketio:client:{sid}",
                        asdict(client_info),
                        expire=3600,  # 1 hour TTL
                    )

                logger.info(f"Socket.IO client connected: {sid} from {ip_address}")

            except Exception as e:
                logger.error(f"Error handling Socket.IO connection: {e}", exc_info=True)

        @self.sio.event
        async def disconnect(sid: str):
            """Handle client disconnection"""
            try:
                client_info = self.clients.get(sid)
                if client_info:
                    # Remove from all rooms
                    for room in list(client_info.rooms):
                        await self.leave_room(sid, room)

                    # Remove client info
                    del self.clients[sid]

                    # Remove from Redis
                    if redis_service.is_available():
                        await redis_service.delete(f"socketio:client:{sid}")

                    logger.info(f"Socket.IO client disconnected: {sid}")

            except Exception as e:
                logger.error(
                    f"Error handling Socket.IO disconnection: {e}", exc_info=True
                )

        @self.sio.event
        async def join_room(sid: str, data: Dict[str, Any]):
            """Handle room join requests"""
            try:
                room_name = data.get("room")
                if not room_name or room_name not in [
                    room.value for room in SocketIORoom
                ]:
                    await self.sio.emit(
                        SocketIOEvent.ERROR, {"error": "Invalid room name"}, room=sid
                    )
                    return

                await self._join_room(sid, room_name)

                await self.sio.emit(
                    "room_joined",
                    {"room": room_name, "timestamp": datetime.utcnow().isoformat()},
                    room=sid,
                )

            except Exception as e:
                logger.error(f"Error joining room: {e}", exc_info=True)
                await self.sio.emit(
                    SocketIOEvent.ERROR, {"error": "Failed to join room"}, room=sid
                )

        @self.sio.event
        async def leave_room(sid: str, data: Dict[str, Any]):
            """Handle room leave requests"""
            try:
                room_name = data.get("room")
                if not room_name:
                    return

                await self.leave_room(sid, room_name)

                await self.sio.emit(
                    "room_left",
                    {"room": room_name, "timestamp": datetime.utcnow().isoformat()},
                    room=sid,
                )

            except Exception as e:
                logger.error(f"Error leaving room: {e}", exc_info=True)

        @self.sio.event
        async def agent_status_update(sid: str, data: Dict[str, Any]):
            """Handle agent status updates from frontend"""
            try:
                # Validate data
                required_fields = ["agent_id", "status"]
                if not all(field in data for field in required_fields):
                    await self.sio.emit(
                        SocketIOEvent.ERROR,
                        {"error": "Missing required fields for agent status update"},
                        room=sid,
                    )
                    return

                # Broadcast to agents room
                message = SocketIOMessage(
                    event=SocketIOEvent.AGENT_STATUS_UPDATE,
                    data=data,
                    room=SocketIORoom.AGENTS.value,
                )

                await self.broadcast_to_room(SocketIORoom.AGENTS.value, message)

                # Store in Redis for persistence
                if redis_service.is_available():
                    await redis_service.set_json(
                        f"agent:status:{data['agent_id']}",
                        data,
                        expire=300,  # 5 minutes
                    )

                logger.debug(
                    f"Agent status update: {data['agent_id']} -> {data['status']}"
                )

            except Exception as e:
                logger.error(f"Error handling agent status update: {e}", exc_info=True)

        @self.sio.event
        async def task_update(sid: str, data: Dict[str, Any]):
            """Handle task updates from frontend"""
            try:
                # Validate data
                required_fields = ["task_id", "status"]
                if not all(field in data for field in required_fields):
                    await self.sio.emit(
                        SocketIOEvent.ERROR,
                        {"error": "Missing required fields for task update"},
                        room=sid,
                    )
                    return

                # Broadcast to tasks room
                message = SocketIOMessage(
                    event=SocketIOEvent.TASK_UPDATE,
                    data=data,
                    room=SocketIORoom.TASKS.value,
                )

                await self.broadcast_to_room(SocketIORoom.TASKS.value, message)

                # Store in Redis
                if redis_service.is_available():
                    await redis_service.set_json(
                        f"task:status:{data['task_id']}", data, expire=3600  # 1 hour
                    )

                logger.debug(f"Task update: {data['task_id']} -> {data['status']}")

            except Exception as e:
                logger.error(f"Error handling task update: {e}", exc_info=True)

        @self.sio.event
        async def system_metrics_update(sid: str, data: Dict[str, Any]):
            """Handle system metrics updates from frontend"""
            try:
                # Broadcast to metrics room
                message = SocketIOMessage(
                    event=SocketIOEvent.SYSTEM_METRICS_UPDATE,
                    data=data,
                    room=SocketIORoom.METRICS.value,
                )

                await self.broadcast_to_room(SocketIORoom.METRICS.value, message)

                logger.debug("System metrics update broadcasted")

            except Exception as e:
                logger.error(
                    f"Error handling system metrics update: {e}", exc_info=True
                )

        @self.sio.event
        async def workflow_event(sid: str, data: Dict[str, Any]):
            """Handle workflow events from frontend"""
            try:
                # Validate data
                if "workflow_id" not in data:
                    await self.sio.emit(
                        SocketIOEvent.ERROR,
                        {"error": "Missing workflow_id for workflow event"},
                        room=sid,
                    )
                    return

                # Broadcast to workflows room
                message = SocketIOMessage(
                    event=SocketIOEvent.WORKFLOW_EVENT,
                    data=data,
                    room=SocketIORoom.WORKFLOWS.value,
                )

                await self.broadcast_to_room(SocketIORoom.WORKFLOWS.value, message)

                logger.debug(f"Workflow event: {data['workflow_id']}")

            except Exception as e:
                logger.error(f"Error handling workflow event: {e}", exc_info=True)

        @self.sio.event
        async def ping(sid: str, data: Optional[Dict[str, Any]] = None):
            """Handle ping requests"""
            try:
                await self.sio.emit(
                    SocketIOEvent.PONG,
                    {"timestamp": datetime.utcnow().isoformat(), "data": data},
                    room=sid,
                )
            except Exception as e:
                logger.error(f"Error handling ping: {e}")

    async def _join_room(self, sid: str, room_name: str):
        """Internal method to join a room"""
        await self.sio.enter_room(sid, room_name)

        # Update client info
        if sid in self.clients:
            self.clients[sid].rooms.add(room_name)

        # Update room members
        if room_name not in self.room_members:
            self.room_members[room_name] = set()
        self.room_members[room_name].add(sid)

        logger.debug(f"Client {sid} joined room {room_name}")

    async def leave_room(self, sid: str, room_name: str):
        """Remove client from a room"""
        try:
            await self.sio.leave_room(sid, room_name)

            # Update client info
            if sid in self.clients:
                self.clients[sid].rooms.discard(room_name)

            # Update room members
            if room_name in self.room_members:
                self.room_members[room_name].discard(sid)

            logger.debug(f"Client {sid} left room {room_name}")

        except Exception as e:
            logger.error(f"Error leaving room: {e}")

    async def broadcast_to_room(self, room: str, message: SocketIOMessage):
        """Broadcast message to all clients in a room"""
        try:
            if not self.sio:
                logger.warning("Socket.IO server not initialized")
                return

            await self.sio.emit(message.event, message.data, room=room)

            logger.debug(f"Broadcasted {message.event} to room {room}")

        except Exception as e:
            logger.error(f"Error broadcasting to room {room}: {e}")

    async def send_to_client(self, sid: str, message: SocketIOMessage):
        """Send message to specific client"""
        try:
            if not self.sio:
                logger.warning("Socket.IO server not initialized")
                return

            await self.sio.emit(message.event, message.data, room=sid)

            logger.debug(f"Sent {message.event} to client {sid}")

        except DisconnectedError:
            logger.warning(f"Client {sid} disconnected while sending message")
        except Exception as e:
            logger.error(f"Error sending message to client {sid}: {e}")

    async def broadcast_to_all(self, message: SocketIOMessage):
        """Broadcast message to all connected clients"""
        try:
            if not self.sio:
                logger.warning("Socket.IO server not initialized")
                return

            await self.sio.emit(message.event, message.data)

            logger.debug(f"Broadcasted {message.event} to all clients")

        except Exception as e:
            logger.error(f"Error broadcasting to all clients: {e}")

    def get_connection_count(self) -> int:
        """Get total number of connected clients"""
        return len(self.clients)

    def get_room_members(self, room: str) -> List[str]:
        """Get list of clients in a room"""
        return list(self.room_members.get(room, set()))

    def get_client_rooms(self, sid: str) -> List[str]:
        """Get list of rooms a client has joined"""
        client = self.clients.get(sid)
        return list(client.rooms) if client else []

    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information for debugging"""
        return {
            "total_connections": len(self.clients),
            "clients": {
                sid: {
                    "user_agent": client.user_agent,
                    "ip_address": client.ip_address,
                    "connected_at": client.connected_at,
                    "rooms": list(client.rooms),
                }
                for sid, client in self.clients.items()
            },
            "room_counts": {
                room: len(members) for room, members in self.room_members.items()
            },
        }

    async def cleanup_disconnected_clients(self):
        """Cleanup disconnected clients (called periodically)"""
        try:
            if not self.sio:
                return

            # Get list of currently connected sessions from Socket.IO
            # Note: This is a simplified cleanup - Socket.IO handles most cleanup automatically
            disconnected_clients = []

            for sid in list(self.clients.keys()):
                try:
                    # Try to get session info - if it fails, client is disconnected
                    session = self.sio.get_session(sid)
                    if not session:
                        disconnected_clients.append(sid)
                except:
                    disconnected_clients.append(sid)

            # Clean up disconnected clients
            for sid in disconnected_clients:
                if sid in self.clients:
                    client_info = self.clients[sid]
                    # Remove from all rooms
                    for room in list(client_info.rooms):
                        await self.leave_room(sid, room)
                    # Remove client
                    del self.clients[sid]

                    # Remove from Redis
                    if redis_service.is_available():
                        await redis_service.delete(f"socketio:client:{sid}")

            if disconnected_clients:
                logger.info(
                    f"Cleaned up {len(disconnected_clients)} disconnected Socket.IO clients"
                )

        except Exception as e:
            logger.error(f"Error during Socket.IO client cleanup: {e}")


# Global Socket.IO manager instance
socketio_manager = SocketIOManager()


# Convenience functions for easy access
async def emit_agent_status(
    agent_id: str, status: str, data: Optional[Dict[str, Any]] = None
):
    """Convenience function to emit agent status updates"""
    message_data = {
        "agent_id": agent_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if data:
        message_data.update(data)

    message = SocketIOMessage(
        event=SocketIOEvent.AGENT_STATUS_UPDATE,
        data=message_data,
        room=SocketIORoom.AGENTS.value,
    )
    await socketio_manager.broadcast_to_room(SocketIORoom.AGENTS.value, message)


async def emit_task_update(
    task_id: str, status: str, data: Optional[Dict[str, Any]] = None
):
    """Convenience function to emit task updates"""
    message_data = {
        "task_id": task_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if data:
        message_data.update(data)

    message = SocketIOMessage(
        event=SocketIOEvent.TASK_UPDATE,
        data=message_data,
        room=SocketIORoom.TASKS.value,
    )
    await socketio_manager.broadcast_to_room(SocketIORoom.TASKS.value, message)


async def emit_system_metrics(metrics: Dict[str, Any]):
    """Convenience function to emit system metrics"""
    message = SocketIOMessage(
        event=SocketIOEvent.SYSTEM_METRICS_UPDATE,
        data=metrics,
        room=SocketIORoom.METRICS.value,
    )
    await socketio_manager.broadcast_to_room(SocketIORoom.METRICS.value, message)


async def emit_workflow_event(
    workflow_id: str, event_type: str, data: Optional[Dict[str, Any]] = None
):
    """Convenience function to emit workflow events"""
    message_data = {
        "workflow_id": workflow_id,
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if data:
        message_data.update(data)

    message = SocketIOMessage(
        event=SocketIOEvent.WORKFLOW_EVENT,
        data=message_data,
        room=SocketIORoom.WORKFLOWS.value,
    )
    await socketio_manager.broadcast_to_room(SocketIORoom.WORKFLOWS.value, message)