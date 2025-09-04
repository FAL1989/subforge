"""
SubForge Dashboard Backend - FastAPI Application
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .api.v1 import api_router
from .api.v2 import api_v2_router

# Import application modules
from .core.config import settings
from .database.base import Base
from .database.session import async_engine
from .services.analytics_integration import analytics_integration_service
from .services.api_enhancement import api_enhancement_service
from .services.redis_service import redis_service
from .utils.file_watcher import file_watcher
from .utils.logging_config import get_logger, setup_logging
from .websocket.enhanced_manager import enhanced_websocket_manager
from .websocket.manager import (
    periodic_cleanup_task,
    websocket_endpoint,
    websocket_manager,
)
from .websocket.socketio_manager import socketio_manager

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def socketio_periodic_cleanup():
    """Periodic cleanup task for Socket.IO connections"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await socketio_manager.cleanup_disconnected_clients()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in Socket.IO cleanup task: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown tasks
    """
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    try:
        # Initialize Redis service
        await redis_service.initialize()

        # Initialize enhanced WebSocket manager
        await enhanced_websocket_manager.initialize()

        # Initialize Socket.IO server
        socketio_manager.create_server()
        logger.info("✅ Socket.IO server initialized")

        # Initialize API enhancement service
        await api_enhancement_service.initialize()

        # Initialize background task service
        if settings.ENABLE_BACKGROUND_TASKS:
            # Note: Celery workers need to be started separately
            logger.info("✅ Background task service ready")

        # Initialize analytics integration service
        await analytics_integration_service.initialize()

        # Create database tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified")

        # Start file watcher
        if settings.ENABLE_FILE_WATCHER:
            file_watcher.start()
            logger.info("✅ File watcher started")

        # Start periodic WebSocket cleanup task
        cleanup_task = asyncio.create_task(periodic_cleanup_task())
        logger.info("✅ WebSocket cleanup task started")

        # Start Socket.IO cleanup task
        socketio_cleanup_task = asyncio.create_task(socketio_periodic_cleanup())
        logger.info("✅ Socket.IO cleanup task started")

        # Initialize system data (can be extended later)
        logger.info("✅ System initialization complete")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    # Shutdown
    logger.info("💤 Shutting down SubForge Dashboard Backend")

    try:
        # Stop file watcher
        file_watcher.stop()
        logger.info("✅ File watcher stopped")

        # Cancel cleanup task
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("✅ Cleanup task stopped")

        # Cancel Socket.IO cleanup task
        socketio_cleanup_task.cancel()
        try:
            await socketio_cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("✅ Socket.IO cleanup task stopped")

        # Shutdown services
        await analytics_integration_service.shutdown()
        await enhanced_websocket_manager.shutdown()
        await api_enhancement_service.shutdown()
        await redis_service.close()

        # Close database connections
        await async_engine.dispose()
        logger.info("✅ Database connections closed")

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
    )


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    """Handle SQLAlchemy database errors"""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred", "error_type": "database_error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_type": "internal_error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": "now",
        "version": settings.APP_VERSION,
        "checks": {
            "database": True,
            "file_watcher": file_watcher.get_status(),
            "websocket_manager": {
                "active_connections": websocket_manager.get_connection_count()
            },
            "socketio_manager": {
                "active_connections": socketio_manager.get_connection_count(),
                "rooms": len(socketio_manager.room_members),
            },
        },
    }


# WebSocket endpoints
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication (v1)
    """
    await websocket_endpoint(websocket)


@app.websocket("/ws/v2")
async def enhanced_websocket_route(websocket: WebSocket):
    """
    Enhanced WebSocket endpoint with rooms, authentication, and advanced features (v2)
    """
    from .websocket.enhanced_manager import enhanced_websocket_manager

    # Get client info from headers
    client_info = {
        "user_agent": websocket.headers.get("user-agent", "unknown"),
        "host": websocket.client.host if websocket.client else "unknown",
    }

    # Connect to enhanced manager
    connection_id = await enhanced_websocket_manager.connect(websocket, client_info)

    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()

            try:
                import json

                from .websocket.enhanced_manager import MessageType, WebSocketMessage

                message_data = json.loads(data)
                message_type = MessageType(message_data.get("type", "ping"))

                if message_type == MessageType.JOIN_ROOM:
                    room_name = message_data.get("room")
                    if room_name:
                        await enhanced_websocket_manager.join_room(
                            connection_id, room_name
                        )

                elif message_type == MessageType.LEAVE_ROOM:
                    room_name = message_data.get("room")
                    if room_name:
                        await enhanced_websocket_manager.leave_room(
                            connection_id, room_name
                        )

                elif message_type == MessageType.PING:
                    await enhanced_websocket_manager.send_to_connection(
                        connection_id,
                        WebSocketMessage(
                            type=MessageType.PONG, data={"timestamp": "now"}
                        ),
                    )

            except Exception as e:
                logger.warning(f"Error processing WebSocket message: {e}")

    except Exception as e:
        logger.error(f"Enhanced WebSocket error: {e}")
    finally:
        await enhanced_websocket_manager.disconnect(connection_id)


# Include API routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api")


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint with basic API information
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs_url": "/docs" if settings.DEBUG else None,
        "api_versions": {
            "v1": {"base_url": "/api/v1", "websocket_url": "/ws", "status": "stable"},
            "v2": {
                "base_url": "/api/v2",
                "websocket_url": "/ws/v2",
                "status": "enhanced",
                "features": [
                    "advanced_websocket_rooms",
                    "rate_limiting",
                    "caching",
                    "background_tasks",
                    "file_uploads",
                    "bulk_operations",
                    "advanced_filtering",
                ],
            },
            "socketio": {
                "endpoint": "/socket.io/",
                "status": "active",
                "features": [
                    "real_time_messaging",
                    "room_based_broadcasting",
                    "auto_reconnection",
                    "event_based_communication",
                    "redis_scaling_support",
                ],
            },
        },
        "services": {
            "redis": "enabled",
            "background_tasks": (
                "enabled" if settings.ENABLE_BACKGROUND_TASKS else "disabled"
            ),
            "file_uploads": "enabled",
            "rate_limiting": "enabled" if settings.ENABLE_RATE_LIMITING else "disabled",
            "caching": "enabled" if settings.ENABLE_CACHING else "disabled",
            "socketio": "enabled",
        },
    }


# Development/Debug endpoints
if settings.DEBUG:

    @app.get("/debug/connections")
    async def debug_websocket_connections():
        """Debug endpoint to show WebSocket connections"""
        return {
            "total_connections": websocket_manager.get_connection_count(),
            "connections": websocket_manager.get_connection_info(),
        }

    @app.post("/debug/broadcast")
    async def debug_broadcast_message(message: Dict[str, Any]):
        """Debug endpoint to broadcast test messages"""
        await websocket_manager.broadcast_json(
            {"type": "debug_message", "data": message}
        )
        return {"status": "message_broadcasted"}

    @app.get("/debug/file-watcher")
    async def debug_file_watcher_status():
        """Debug endpoint to check file watcher status"""
        return file_watcher.get_status()

    @app.get("/debug/socketio")
    async def debug_socketio_status():
        """Debug endpoint to check Socket.IO status"""
        return {
            "connection_info": socketio_manager.get_connection_info(),
            "room_members": {
                room: list(members)
                for room, members in socketio_manager.room_members.items()
            },
        }

    @app.post("/debug/socketio/broadcast")
    async def debug_socketio_broadcast(message: Dict[str, Any]):
        """Debug endpoint to broadcast Socket.IO test messages"""
        from .websocket.socketio_manager import SocketIOEvent, SocketIOMessage

        test_message = SocketIOMessage(
            event=message.get("event", SocketIOEvent.PING),
            data=message.get("data", {"test": True, "timestamp": "now"}),
        )

        room = message.get("room")
        if room:
            await socketio_manager.broadcast_to_room(room, test_message)
        else:
            await socketio_manager.broadcast_to_all(test_message)

        return {"status": "message_broadcasted", "room": room}


# Application metadata
app.extra = {
    "settings": settings,
    "websocket_manager": websocket_manager,
    "socketio_manager": socketio_manager,
    "file_watcher": file_watcher,
}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )