"""
Enhanced WebSocket manager with room-based messaging, authentication, and advanced features
"""

import json
import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Union
from collections import defaultdict
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
import aioredis
from pydantic import BaseModel

from ..core.config import settings

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    CONNECTING = "connecting"
    AUTHENTICATED = "authenticated"
    AUTHORIZED = "authorized"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(str, Enum):
    # Authentication
    AUTH_REQUEST = "auth_request"
    AUTH_SUCCESS = "auth_success"
    AUTH_ERROR = "auth_error"
    
    # Room management
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_MESSAGE = "room_message"
    
    # System events
    SYSTEM_NOTIFICATION = "system_notification"
    AGENT_UPDATE = "agent_update"
    TASK_UPDATE = "task_update"
    METRICS_UPDATE = "metrics_update"
    FILE_CHANGE = "file_change"
    
    # Analytics events
    ANALYTICS_UPDATE = "analytics_update"
    ANALYTICS_ALERT = "analytics_alert"
    ANALYTICS_REPORT = "analytics_report"
    
    # Connection management
    PING = "ping"
    PONG = "pong"
    HEARTBEAT = "heartbeat"
    CONNECTION_STATE = "connection_state"
    
    # Event history
    EVENT_HISTORY = "event_history"
    REPLAY_EVENTS = "replay_events"


class WebSocketMessage(BaseModel):
    type: MessageType
    room: Optional[str] = None
    data: Dict[str, Any] = {}
    timestamp: Optional[str] = None
    message_id: Optional[str] = None
    correlation_id: Optional[str] = None


class ConnectionInfo(BaseModel):
    connection_id: str
    user_id: Optional[str] = None
    client_info: Dict[str, Any] = {}
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: datetime
    last_activity: datetime
    rooms: Set[str] = set()
    message_count: int = 0
    permissions: Set[str] = set()


class EventHistoryEntry(BaseModel):
    event_id: str
    event_type: MessageType
    room: Optional[str] = None
    data: Dict[str, Any] = {}
    timestamp: datetime
    user_id: Optional[str] = None


class EnhancedConnectionManager:
    """Enhanced WebSocket connection manager with rooms, authentication, and event history"""
    
    def __init__(self):
        # Core connection management
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        
        # Room management
        self.rooms: Dict[str, Set[str]] = defaultdict(set)  # room_name -> connection_ids
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        
        # Message queue and persistence
        self.message_queue: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self.event_history: List[EventHistoryEntry] = []
        self.max_history_size = 1000
        
        # Redis client for pub/sub and caching
        self.redis_client: Optional[aioredis.Redis] = None
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the connection manager"""
        try:
            # Initialize Redis connection
            self.redis_client = await aioredis.from_url(settings.REDIS_URL)
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_sender())
            
            logger.info("✅ Enhanced WebSocket manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize WebSocket manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the connection manager"""
        try:
            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            
            # Close all connections
            for connection_id in list(self.active_connections.keys()):
                await self.disconnect(connection_id)
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("✅ Enhanced WebSocket manager shut down")
            
        except Exception as e:
            logger.error(f"❌ Error during WebSocket manager shutdown: {e}")
    
    async def connect(
        self,
        websocket: WebSocket,
        client_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Connect and register a new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        
        try:
            await websocket.accept()
            
            # Store connection
            self.active_connections[connection_id] = websocket
            
            # Create connection info
            info = ConnectionInfo(
                connection_id=connection_id,
                client_info=client_info or {},
                connected_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            self.connection_info[connection_id] = info
            
            logger.info(f"WebSocket connected: {connection_id} (Total: {len(self.active_connections)})")
            
            # Send connection established message
            await self.send_to_connection(connection_id, WebSocketMessage(
                type=MessageType.CONNECTION_STATE,
                data={
                    "connection_id": connection_id,
                    "state": ConnectionState.AUTHENTICATED.value,
                    "message": "Connection established"
                }
            ))
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            raise
    
    async def disconnect(self, connection_id: str):
        """Disconnect and clean up a WebSocket connection"""
        if connection_id not in self.active_connections:
            return
        
        try:
            # Get connection info
            info = self.connection_info.get(connection_id)
            if info:
                # Leave all rooms
                for room_name in list(info.rooms):
                    await self.leave_room(connection_id, room_name)
                
                # Remove user mapping if exists
                if info.user_id and info.user_id in self.user_connections:
                    del self.user_connections[info.user_id]
                
                # Calculate session duration
                duration = datetime.utcnow() - info.connected_at
                logger.info(
                    f"WebSocket disconnected: {connection_id} "
                    f"(Duration: {duration.total_seconds():.1f}s, Messages: {info.message_count})"
                )
            
            # Clean up
            websocket = self.active_connections.pop(connection_id, None)
            if websocket:
                try:
                    await websocket.close()
                except:
                    pass
            
            self.connection_info.pop(connection_id, None)
            self.message_queue.pop(connection_id, None)
            
            logger.info(f"Connection cleaned up: {connection_id} (Total: {len(self.active_connections)})")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {connection_id}: {e}")
    
    async def authenticate_connection(
        self,
        connection_id: str,
        user_id: str,
        permissions: Set[str] = None
    ) -> bool:
        """Authenticate a WebSocket connection"""
        if connection_id not in self.connection_info:
            return False
        
        try:
            info = self.connection_info[connection_id]
            info.user_id = user_id
            info.permissions = permissions or set()
            info.state = ConnectionState.AUTHENTICATED
            info.last_activity = datetime.utcnow()
            
            # Map user to connection
            self.user_connections[user_id] = connection_id
            
            # Send authentication success
            await self.send_to_connection(connection_id, WebSocketMessage(
                type=MessageType.AUTH_SUCCESS,
                data={
                    "user_id": user_id,
                    "permissions": list(permissions) if permissions else [],
                    "state": ConnectionState.AUTHENTICATED.value
                }
            ))
            
            logger.info(f"Connection authenticated: {connection_id} -> {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating connection {connection_id}: {e}")
            return False
    
    async def join_room(self, connection_id: str, room_name: str) -> bool:
        """Add a connection to a room"""
        if connection_id not in self.connection_info:
            return False
        
        try:
            # Add to room
            self.rooms[room_name].add(connection_id)
            self.connection_info[connection_id].rooms.add(room_name)
            
            # Notify connection
            await self.send_to_connection(connection_id, WebSocketMessage(
                type=MessageType.JOIN_ROOM,
                room=room_name,
                data={
                    "room": room_name,
                    "members_count": len(self.rooms[room_name]),
                    "status": "joined"
                }
            ))
            
            # Notify other room members
            await self.broadcast_to_room(room_name, WebSocketMessage(
                type=MessageType.ROOM_MESSAGE,
                room=room_name,
                data={
                    "event": "user_joined",
                    "connection_id": connection_id,
                    "user_id": self.connection_info[connection_id].user_id,
                    "members_count": len(self.rooms[room_name])
                }
            ), exclude_connection=connection_id)
            
            logger.info(f"Connection {connection_id} joined room: {room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining room {room_name} for connection {connection_id}: {e}")
            return False
    
    async def leave_room(self, connection_id: str, room_name: str) -> bool:
        """Remove a connection from a room"""
        if connection_id not in self.connection_info:
            return False
        
        try:
            # Remove from room
            self.rooms[room_name].discard(connection_id)
            self.connection_info[connection_id].rooms.discard(room_name)
            
            # Clean up empty rooms
            if not self.rooms[room_name]:
                del self.rooms[room_name]
            
            # Notify connection
            await self.send_to_connection(connection_id, WebSocketMessage(
                type=MessageType.LEAVE_ROOM,
                room=room_name,
                data={
                    "room": room_name,
                    "status": "left"
                }
            ))
            
            # Notify remaining room members if room still exists
            if room_name in self.rooms:
                await self.broadcast_to_room(room_name, WebSocketMessage(
                    type=MessageType.ROOM_MESSAGE,
                    room=room_name,
                    data={
                        "event": "user_left",
                        "connection_id": connection_id,
                        "user_id": self.connection_info[connection_id].user_id,
                        "members_count": len(self.rooms[room_name])
                    }
                ))
            
            logger.info(f"Connection {connection_id} left room: {room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error leaving room {room_name} for connection {connection_id}: {e}")
            return False
    
    async def send_to_connection(
        self,
        connection_id: str,
        message: WebSocketMessage
    ) -> bool:
        """Send a message to a specific connection"""
        websocket = self.active_connections.get(connection_id)
        if not websocket:
            return False
        
        try:
            # Add message metadata
            if not message.timestamp:
                message.timestamp = datetime.utcnow().isoformat()
            if not message.message_id:
                message.message_id = str(uuid.uuid4())
            
            # Send message
            await websocket.send_json(message.dict())
            
            # Update connection stats
            if connection_id in self.connection_info:
                info = self.connection_info[connection_id]
                info.message_count += 1
                info.last_activity = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def send_to_user(
        self,
        user_id: str,
        message: WebSocketMessage
    ) -> bool:
        """Send a message to a specific user"""
        connection_id = self.user_connections.get(user_id)
        if not connection_id:
            # Store message for later delivery
            self.message_queue[user_id].append(message)
            return False
        
        return await self.send_to_connection(connection_id, message)
    
    async def broadcast_to_room(
        self,
        room_name: str,
        message: WebSocketMessage,
        exclude_connection: Optional[str] = None
    ) -> int:
        """Broadcast a message to all connections in a room"""
        if room_name not in self.rooms:
            return 0
        
        message.room = room_name
        sent_count = 0
        connections_to_remove = []
        
        for connection_id in list(self.rooms[room_name]):
            if connection_id == exclude_connection:
                continue
            
            success = await self.send_to_connection(connection_id, message)
            if success:
                sent_count += 1
            else:
                connections_to_remove.append(connection_id)
        
        # Clean up failed connections
        for connection_id in connections_to_remove:
            await self.disconnect(connection_id)
        
        return sent_count
    
    async def broadcast_to_all(
        self,
        message: WebSocketMessage,
        exclude_connection: Optional[str] = None
    ) -> int:
        """Broadcast a message to all active connections"""
        sent_count = 0
        connections_to_remove = []
        
        for connection_id in list(self.active_connections.keys()):
            if connection_id == exclude_connection:
                continue
            
            success = await self.send_to_connection(connection_id, message)
            if success:
                sent_count += 1
            else:
                connections_to_remove.append(connection_id)
        
        # Clean up failed connections
        for connection_id in connections_to_remove:
            await self.disconnect(connection_id)
        
        return sent_count
    
    async def add_to_event_history(
        self,
        event_type: MessageType,
        data: Dict[str, Any],
        room: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Add an event to the history"""
        entry = EventHistoryEntry(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            room=room,
            data=data,
            timestamp=datetime.utcnow(),
            user_id=user_id
        )
        
        self.event_history.append(entry)
        
        # Trim history if too large
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # Store in Redis for persistence
        if self.redis_client:
            try:
                await self.redis_client.lpush(
                    "websocket:event_history",
                    entry.json()
                )
                await self.redis_client.ltrim("websocket:event_history", 0, self.max_history_size - 1)
            except Exception as e:
                logger.warning(f"Failed to store event in Redis: {e}")
    
    async def get_event_history(
        self,
        room: Optional[str] = None,
        event_types: Optional[List[MessageType]] = None,
        limit: int = 50
    ) -> List[EventHistoryEntry]:
        """Get event history with optional filtering"""
        filtered_events = self.event_history
        
        if room:
            filtered_events = [e for e in filtered_events if e.room == room]
        
        if event_types:
            filtered_events = [e for e in filtered_events if e.event_type in event_types]
        
        return filtered_events[-limit:]
    
    async def replay_events_to_connection(
        self,
        connection_id: str,
        room: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 50
    ):
        """Replay historical events to a connection"""
        try:
            events = await self.get_event_history(room=room, limit=limit)
            
            if since:
                events = [e for e in events if e.timestamp > since]
            
            for event in events:
                await self.send_to_connection(connection_id, WebSocketMessage(
                    type=MessageType.EVENT_HISTORY,
                    room=event.room,
                    data={
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "original_data": event.data,
                        "timestamp": event.timestamp.isoformat(),
                        "is_replay": True
                    }
                ))
            
            logger.info(f"Replayed {len(events)} events to connection {connection_id}")
            
        except Exception as e:
            logger.error(f"Error replaying events to {connection_id}: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = len(self.active_connections)
        authenticated_connections = len([
            info for info in self.connection_info.values()
            if info.state == ConnectionState.AUTHENTICATED
        ])
        
        room_stats = {
            room_name: len(connections)
            for room_name, connections in self.rooms.items()
        }
        
        return {
            "total_connections": total_connections,
            "authenticated_connections": authenticated_connections,
            "rooms": room_stats,
            "total_rooms": len(self.rooms),
            "event_history_size": len(self.event_history),
            "message_queue_size": sum(len(queue) for queue in self.message_queue.values())
        }
    
    async def _periodic_cleanup(self):
        """Periodic cleanup task"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.utcnow()
                stale_connections = []
                
                # Find stale connections (no activity for 30 minutes)
                for connection_id, info in self.connection_info.items():
                    inactive_duration = current_time - info.last_activity
                    if inactive_duration > timedelta(minutes=30):
                        stale_connections.append(connection_id)
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    logger.info(f"Cleaning up stale connection: {connection_id}")
                    await self.disconnect(connection_id)
                
                # Clean up empty rooms
                empty_rooms = [name for name, connections in self.rooms.items() if not connections]
                for room_name in empty_rooms:
                    del self.rooms[room_name]
                
                if stale_connections or empty_rooms:
                    logger.info(f"Cleanup completed: {len(stale_connections)} stale connections, {len(empty_rooms)} empty rooms")
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _heartbeat_sender(self):
        """Send heartbeat messages to maintain connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Send heartbeat every minute
                
                if self.active_connections:
                    await self.broadcast_to_all(WebSocketMessage(
                        type=MessageType.HEARTBEAT,
                        data={"timestamp": datetime.utcnow().isoformat()}
                    ))
                
            except Exception as e:
                logger.error(f"Error in heartbeat sender: {e}")


# Global enhanced WebSocket manager instance
enhanced_websocket_manager = EnhancedConnectionManager()