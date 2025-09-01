"""
Simplified FastAPI app with Socket.IO support for testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins=["http://localhost:3001"],
    async_mode='asgi',
    logger=True,
    engineio_logger=True
)

# Create FastAPI app
app = FastAPI(
    title="SubForge Dashboard Backend",
    description="Simplified backend with Socket.IO support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create ASGI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to SubForge Dashboard'}, to=sid)
    # No return value needed for async handlers

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def agent_status_update(sid, data):
    logger.info(f"Agent status update from {sid}: {data}")
    # Broadcast to all clients
    await sio.emit('agent_status_update', data)

@sio.event
async def task_update(sid, data):
    logger.info(f"Task update from {sid}: {data}")
    await sio.emit('task_update', data)

@sio.event
async def system_metrics_update(sid, data):
    logger.info(f"System metrics update from {sid}: {data}")
    await sio.emit('system_metrics_update', data)

@sio.event
async def workflow_event(sid, data):
    logger.info(f"Workflow event from {sid}: {data}")
    await sio.emit('workflow_event', data)

@sio.event
async def join_room(sid, room):
    sio.enter_room(sid, room)
    logger.info(f"Client {sid} joined room: {room}")
    await sio.emit('room_joined', {'room': room}, to=sid)

@sio.event
async def leave_room(sid, room):
    sio.leave_room(sid, room)
    logger.info(f"Client {sid} left room: {room}")
    await sio.emit('room_left', {'room': room}, to=sid)

# Regular HTTP endpoints
@app.get("/")
async def root():
    return {
        "message": "SubForge Dashboard Backend (Simplified)",
        "status": "running",
        "socket_io": "enabled",
        "cors": "configured for http://localhost:3001"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "socket_io": "active"
    }

@app.get("/api/dashboard/overview")
async def dashboard_overview():
    """Return dashboard overview data"""
    return {
        "agents": {
            "total": 6,
            "active": 4,
            "idle": 1,
            "error": 1
        },
        "tasks": {
            "completed": 145,
            "pending": 8,
            "failed": 2,
            "total": 155
        },
        "system": {
            "uptime": 86400,
            "cpu": 45,
            "memory": 68,
            "connections": 12
        }
    }

# Export the socket app for uvicorn
app = socket_app