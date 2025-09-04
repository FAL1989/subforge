#!/usr/bin/env python3
"""
SubForge Dashboard Backend with Socket.IO support
Entry point for running the application with Socket.IO integration
"""

import socketio
import uvicorn
from app.main import app, settings
from app.websocket.socketio_manager import socketio_manager


def create_socketio_app():
    """Create the Socket.IO enabled application"""
    # Create Socket.IO server
    sio = socketio_manager.create_server()

    # Create Socket.IO ASGI app with FastAPI
    socketio_app = socketio.ASGIApp(sio, app)

    return socketio_app


if __name__ == "__main__":
    # Create the Socket.IO enabled application
    application = create_socketio_app()

    # Run with uvicorn
    uvicorn.run(
        application,
        host=settings.HOST,
        port=settings.PORT,
        reload=False,  # Socket.IO doesn't work well with reload
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )