"""
Enhanced WebSocket API v2 for real-time features
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ...services.api_enhancement import (
    api_enhancement_service,
    get_current_user,
    require_auth,
)
from ...websocket.enhanced_manager import (
    MessageType,
    WebSocketMessage,
    enhanced_websocket_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class WebSocketConnectionInfo(BaseModel):
    connection_id: str
    user_id: Optional[str] = None
    state: str
    connected_at: datetime
    last_activity: datetime
    rooms: List[str] = []
    message_count: int = 0
    client_info: Dict[str, Any] = {}


class RoomInfo(BaseModel):
    name: str
    members_count: int
    members: List[str] = []
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class BroadcastRequest(BaseModel):
    message_type: MessageType
    room: Optional[str] = None
    data: Dict[str, Any] = {}
    exclude_user_id: Optional[str] = None


class RoomJoinRequest(BaseModel):
    room_name: str
    user_id: Optional[str] = None


class EventHistoryRequest(BaseModel):
    room: Optional[str] = None
    event_types: Optional[List[MessageType]] = None
    limit: int = 50
    since: Optional[datetime] = None


# API Endpoints


@router.get(
    "/connections",
    response_model=List[WebSocketConnectionInfo],
    summary="Get all active WebSocket connections",
)
@api_enhancement_service.cache_response(ttl=10)
@api_enhancement_service.rate_limit(requests_per_minute=60)
@require_auth
async def get_websocket_connections(current_user: dict = Depends(get_current_user)):
    """Get information about all active WebSocket connections"""
    try:
        connections_info = enhanced_websocket_manager.get_connection_info()

        return [
            WebSocketConnectionInfo(
                connection_id=conn["connection_id"],
                user_id=conn["client_info"].get("user_id"),
                state=conn.get("state", "unknown"),
                connected_at=datetime.fromisoformat(conn["connected_at"]),
                last_activity=datetime.fromisoformat(conn["last_activity"]),
                message_count=conn["message_count"],
                client_info=conn["client_info"],
            )
            for conn in connections_info
        ]

    except Exception as e:
        logger.error(f"Error getting WebSocket connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection information",
        )


@router.get(
    "/connections/{connection_id}",
    response_model=WebSocketConnectionInfo,
    summary="Get specific WebSocket connection info",
)
@api_enhancement_service.cache_response(ttl=5)
@api_enhancement_service.rate_limit(requests_per_minute=120)
async def get_websocket_connection(connection_id: str):
    """Get information about a specific WebSocket connection"""
    try:
        connections_info = enhanced_websocket_manager.get_connection_info()

        for conn in connections_info:
            if conn["connection_id"] == connection_id:
                return WebSocketConnectionInfo(
                    connection_id=conn["connection_id"],
                    user_id=conn["client_info"].get("user_id"),
                    state=conn.get("state", "unknown"),
                    connected_at=datetime.fromisoformat(conn["connected_at"]),
                    last_activity=datetime.fromisoformat(conn["last_activity"]),
                    message_count=conn["message_count"],
                    client_info=conn["client_info"],
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting WebSocket connection {connection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection information",
        )


@router.get(
    "/rooms", response_model=List[RoomInfo], summary="Get all active WebSocket rooms"
)
@api_enhancement_service.cache_response(ttl=30)
@api_enhancement_service.rate_limit(requests_per_minute=60)
async def get_websocket_rooms():
    """Get information about all active WebSocket rooms"""
    try:
        rooms_data = []

        for room_name, connection_ids in enhanced_websocket_manager.rooms.items():
            # Get user IDs for room members
            members = []
            for conn_id in connection_ids:
                if conn_id in enhanced_websocket_manager.connection_info:
                    user_id = enhanced_websocket_manager.connection_info[
                        conn_id
                    ].user_id
                    if user_id:
                        members.append(user_id)
                    else:
                        members.append(conn_id)  # Use connection ID if no user ID

            room_info = RoomInfo(
                name=room_name, members_count=len(connection_ids), members=members
            )
            rooms_data.append(room_info)

        return rooms_data

    except Exception as e:
        logger.error(f"Error getting WebSocket rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve room information",
        )


@router.get(
    "/rooms/{room_name}",
    response_model=RoomInfo,
    summary="Get specific WebSocket room info",
)
@api_enhancement_service.cache_response(ttl=10)
@api_enhancement_service.rate_limit(requests_per_minute=120)
async def get_websocket_room(room_name: str):
    """Get information about a specific WebSocket room"""
    try:
        if room_name not in enhanced_websocket_manager.rooms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Room {room_name} not found",
            )

        connection_ids = enhanced_websocket_manager.rooms[room_name]

        # Get user IDs for room members
        members = []
        for conn_id in connection_ids:
            if conn_id in enhanced_websocket_manager.connection_info:
                user_id = enhanced_websocket_manager.connection_info[conn_id].user_id
                if user_id:
                    members.append(user_id)
                else:
                    members.append(conn_id)

        return RoomInfo(
            name=room_name, members_count=len(connection_ids), members=members
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting WebSocket room {room_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve room information",
        )


@router.post("/broadcast", summary="Broadcast message to WebSocket connections")
@api_enhancement_service.rate_limit(requests_per_minute=30, per_user=True)
@require_auth
async def broadcast_message(
    request: BroadcastRequest, current_user: dict = Depends(get_current_user)
):
    """Broadcast a message to WebSocket connections"""
    try:
        message = WebSocketMessage(
            type=request.message_type,
            room=request.room,
            data={
                **request.data,
                "sent_by": current_user.get("id"),
                "sent_at": datetime.utcnow().isoformat(),
            },
        )

        if request.room:
            # Broadcast to specific room
            sent_count = await enhanced_websocket_manager.broadcast_to_room(
                request.room, message
            )
        else:
            # Broadcast to all connections
            exclude_connection = None
            if request.exclude_user_id:
                exclude_connection = enhanced_websocket_manager.user_connections.get(
                    request.exclude_user_id
                )

            sent_count = await enhanced_websocket_manager.broadcast_to_all(
                message, exclude_connection=exclude_connection
            )

        # Add to event history
        await enhanced_websocket_manager.add_to_event_history(
            request.message_type, message.data, request.room, current_user.get("id")
        )

        return {
            "message": "Broadcast sent successfully",
            "recipients_count": sent_count,
            "message_id": message.message_id,
            "timestamp": message.timestamp,
        }

    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast message",
        )


@router.post("/rooms/{room_name}/join", summary="Join a WebSocket room")
@api_enhancement_service.rate_limit(requests_per_minute=60, per_user=True)
async def join_room(
    room_name: str,
    request: RoomJoinRequest,
    current_user: dict = Depends(get_current_user),
):
    """Join a WebSocket room (for managing room membership via API)"""
    try:
        # Find connection by user ID
        user_id = request.user_id or current_user.get("id")
        connection_id = enhanced_websocket_manager.user_connections.get(user_id)

        if not connection_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active connection found for user {user_id}",
            )

        # Join room
        success = await enhanced_websocket_manager.join_room(connection_id, room_name)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to join room"
            )

        return {
            "message": f"Successfully joined room {room_name}",
            "room_name": room_name,
            "user_id": user_id,
            "connection_id": connection_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining room {room_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join room",
        )


@router.post("/rooms/{room_name}/leave", summary="Leave a WebSocket room")
@api_enhancement_service.rate_limit(requests_per_minute=60, per_user=True)
async def leave_room(
    room_name: str,
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Leave a WebSocket room"""
    try:
        # Find connection by user ID
        target_user_id = user_id or current_user.get("id")
        connection_id = enhanced_websocket_manager.user_connections.get(target_user_id)

        if not connection_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active connection found for user {target_user_id}",
            )

        # Leave room
        success = await enhanced_websocket_manager.leave_room(connection_id, room_name)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to leave room"
            )

        return {
            "message": f"Successfully left room {room_name}",
            "room_name": room_name,
            "user_id": target_user_id,
            "connection_id": connection_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving room {room_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave room",
        )


@router.get("/event-history", summary="Get WebSocket event history")
@api_enhancement_service.cache_response(ttl=60)
@api_enhancement_service.rate_limit(requests_per_minute=30)
async def get_event_history(
    room: Optional[str] = Query(None, description="Filter by room"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    limit: int = Query(50, ge=1, le=500, description="Number of events to return"),
    since: Optional[str] = Query(
        None, description="ISO datetime to filter events since"
    ),
):
    """Get WebSocket event history with filtering"""
    try:
        # Parse event types
        parsed_event_types = None
        if event_types:
            try:
                parsed_event_types = [
                    MessageType(event_type.strip())
                    for event_type in event_types.split(",")
                ]
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event type: {e}",
                )

        # Parse since datetime
        since_datetime = None
        if since:
            try:
                since_datetime = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid datetime format. Use ISO format",
                )

        # Get event history
        events = await enhanced_websocket_manager.get_event_history(
            room=room, event_types=parsed_event_types, limit=limit
        )

        # Filter by since if provided
        if since_datetime:
            events = [event for event in events if event.timestamp > since_datetime]

        return {
            "events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "room": event.room,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat(),
                    "user_id": event.user_id,
                }
                for event in events
            ],
            "total_count": len(events),
            "filters": {
                "room": room,
                "event_types": event_types,
                "since": since,
                "limit": limit,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event history",
        )


@router.post(
    "/connections/{connection_id}/replay-events",
    summary="Replay events to a specific connection",
)
@api_enhancement_service.rate_limit(requests_per_minute=10, per_user=True)
@require_auth
async def replay_events_to_connection(
    connection_id: str,
    request: EventHistoryRequest,
    current_user: dict = Depends(get_current_user),
):
    """Replay historical events to a specific connection"""
    try:
        # Check if connection exists
        if connection_id not in enhanced_websocket_manager.active_connections:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection {connection_id} not found or inactive",
            )

        # Replay events
        await enhanced_websocket_manager.replay_events_to_connection(
            connection_id, room=request.room, since=request.since, limit=request.limit
        )

        return {
            "message": "Events replayed successfully",
            "connection_id": connection_id,
            "filters": {
                "room": request.room,
                "since": request.since.isoformat() if request.since else None,
                "limit": request.limit,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replaying events to connection {connection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to replay events",
        )


@router.get("/statistics", summary="Get WebSocket system statistics")
@api_enhancement_service.cache_response(ttl=30)
@api_enhancement_service.rate_limit(requests_per_minute=60)
async def get_websocket_statistics():
    """Get WebSocket system statistics"""
    try:
        stats = enhanced_websocket_manager.get_connection_stats()

        # Add additional statistics
        stats.update(
            {
                "uptime": "system_uptime_placeholder",  # Would be calculated from startup time
                "message_throughput": {
                    "last_minute": 0,  # Would be calculated from metrics
                    "last_hour": 0,
                    "last_day": 0,
                },
                "error_rate": 0.0,  # Would be calculated from error logs
                "peak_connections": 0,  # Would be tracked over time
            }
        )

        return stats

    except Exception as e:
        logger.error(f"Error getting WebSocket statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve WebSocket statistics",
        )


@router.delete(
    "/connections/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disconnect a specific WebSocket connection",
)
@api_enhancement_service.rate_limit(requests_per_minute=20, per_user=True)
@require_auth
async def disconnect_websocket_connection(
    connection_id: str, current_user: dict = Depends(get_current_user)
):
    """Forcefully disconnect a WebSocket connection"""
    try:
        # Check if connection exists
        if connection_id not in enhanced_websocket_manager.active_connections:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection {connection_id} not found or already disconnected",
            )

        # Disconnect
        await enhanced_websocket_manager.disconnect(connection_id)

        logger.info(
            f"Connection {connection_id} forcefully disconnected by {current_user.get('id')}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting connection {connection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect connection",
        )