# Socket.IO Integration for SubForge Dashboard Backend

This document describes the Socket.IO integration added to the SubForge Dashboard Backend for real-time communication capabilities.

## Overview

The Socket.IO integration provides enhanced real-time communication features for the dashboard, including:

- Real-time bidirectional communication
- Room-based messaging for different dashboard sections
- Auto-reconnection support
- Event-based architecture
- Redis scaling support (when Redis is available)
- Production-ready error handling and logging

## Files Added/Modified

### New Files

1. **`app/websocket/socketio_manager.py`** - Complete Socket.IO manager implementation
2. **`run_socketio.py`** - Entry point for running with Socket.IO support

### Modified Files

1. **`requirements.txt`** - Added Socket.IO dependencies
2. **`app/main.py`** - Integrated Socket.IO server with FastAPI
3. **`app/core/config.py`** - Fixed pydantic-settings import

## Dependencies Added

```text
python-socketio[asyncio]==5.10.0
python-socketio>=5.10.0
```

## Socket.IO Manager Features

### Events Supported

The Socket.IO manager supports the following events from the frontend:

- `agent_status_update` - Agent status changes
- `task_update` - Task progress updates  
- `system_metrics_update` - System performance metrics
- `workflow_event` - Workflow state changes
- `join_room` / `leave_room` - Room management
- `ping` / `pong` - Connection health checks

### Room-Based Messaging

The system supports the following rooms for organized messaging:

- `agents` - Agent status and management
- `tasks` - Task board updates
- `metrics` - System metrics and monitoring
- `workflows` - Workflow orchestration
- `system` - System-wide notifications
- `dashboard` - Main dashboard room (auto-joined)
- `admin` - Admin-only notifications

### CORS Configuration

Socket.IO server is configured with CORS support for:

- `http://localhost:3001` (Primary frontend dev server)
- `http://127.0.0.1:3001`
- `http://localhost:3000` (Alternative frontend port)
- `http://127.0.0.1:3000`

## Usage

### Starting the Server

#### Option 1: Using the Socket.IO Runner (Recommended)

```bash
python run_socketio.py
```

#### Option 2: Standard FastAPI with Socket.IO Integration

```bash
python -m app.main
```

#### Option 3: With Uvicorn

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Connection

Frontend clients can connect to the Socket.IO server at:

```
http://localhost:8000/socket.io/
```

### Example Client Code (JavaScript)

```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:8000', {
  cors: {
    origin: "http://localhost:3001",
    methods: ["GET", "POST"]
  }
});

// Join a specific room
socket.emit('join_room', { room: 'agents' });

// Listen for agent updates
socket.on('agent_status_update', (data) => {
  console.log('Agent update:', data);
});

// Send agent status update
socket.emit('agent_status_update', {
  agent_id: 'agent-123',
  status: 'active',
  metadata: { cpu: 75, memory: 60 }
});
```

## API Endpoints

### Debug Endpoints (Development Mode)

- `GET /debug/socketio` - Socket.IO connection status
- `POST /debug/socketio/broadcast` - Broadcast test messages

### Health Check

The main health check endpoint (`/health`) now includes Socket.IO status:

```json
{
  "status": "healthy",
  "checks": {
    "socketio_manager": {
      "active_connections": 5,
      "rooms": 6
    }
  }
}
```

## Message Format

All Socket.IO messages follow this structure:

```python
@dataclass
class SocketIOMessage:
    event: str              # Event type
    data: Dict[str, Any]    # Message payload
    room: Optional[str]     # Target room (optional)
    timestamp: Optional[str] # ISO timestamp
```

## Convenience Functions

The module provides helper functions for common operations:

```python
from app.websocket.socketio_manager import (
    emit_agent_status,
    emit_task_update,
    emit_system_metrics,
    emit_workflow_event
)

# Emit agent status update
await emit_agent_status(
    agent_id="agent-123",
    status="active",
    data={"cpu": 75, "memory": 60}
)

# Emit task update
await emit_task_update(
    task_id="task-456", 
    status="completed",
    data={"result": "success"}
)
```

## Error Handling

The Socket.IO manager includes comprehensive error handling:

- Connection failures are logged but don't crash the server
- Invalid message formats return error events to clients
- Disconnected clients are automatically cleaned up
- Redis failures gracefully degrade to in-memory operation

## Scaling and Redis Integration

When Redis is available, the Socket.IO manager:

- Stores client session information in Redis
- Enables horizontal scaling across multiple server instances
- Provides persistence for connection metadata
- Supports distributed room management

## Production Considerations

1. **CORS Origins**: Update `cors_allowed_origins` for production domains
2. **Redis**: Configure Redis for scaling and persistence
3. **Monitoring**: Socket.IO metrics are included in health checks
4. **Logging**: Comprehensive logging for debugging and monitoring
5. **Security**: Consider authentication/authorization for sensitive rooms

## Testing

The integration has been tested with:

- Socket.IO server creation and configuration
- FastAPI integration via ASGIApp
- Event handler registration
- CORS configuration
- Basic message broadcasting

## Next Steps

1. Install remaining dependencies for full functionality:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Redis for production scaling

3. Implement frontend Socket.IO client integration

4. Add authentication/authorization as needed

5. Monitor performance and connection metrics

---

*Socket.IO integration implemented for SubForge Dashboard Backend*  
*Compatible with FastAPI and existing WebSocket infrastructure*