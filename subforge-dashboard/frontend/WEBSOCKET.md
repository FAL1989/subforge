# WebSocket Configuration

## Overview
The frontend uses Socket.IO for real-time communication with the backend. The WebSocket provider handles connection management, event handling, and error recovery.

## Configuration

### Environment Variables
Set in `.env.local` or `.env.production`:

```bash
# WebSocket Configuration
NEXT_PUBLIC_WEBSOCKET_URL=http://localhost:8000

# API Configuration  
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### WebSocket Provider
Located in `src/components/providers/websocket-provider.tsx`, the WebSocket provider:

- **Auto-connects** on component mount
- **Handles reconnection** with exponential backoff (5 attempts, 1-5s delay)
- **Manages connection state** with status tracking
- **Provides error handling** with user-friendly messages
- **Supports multiple transports** (WebSocket + polling fallback)

## Events

### Backend → Frontend (Listening)
- `agent_status_update` - Agent status changes
- `task_update` - Task progress updates  
- `system_metrics_update` - System performance metrics
- `workflow_event` - Workflow state changes
- `connect/disconnect` - Connection events
- `pong` - Response to ping requests

### Frontend → Backend (Sending)
- `ping` - Connection health check
- `join_room` - Subscribe to specific data streams
- `leave_room` - Unsubscribe from data streams

## Usage

### Basic Hook Usage
```typescript
import { useWebSocket } from '@/components/providers/websocket-provider'

function MyComponent() {
  const { 
    isConnected, 
    connectionStatus, 
    data, 
    error, 
    sendMessage, 
    reconnect 
  } = useWebSocket()

  // Send a message
  const handleSendMessage = () => {
    sendMessage('ping', { test: true })
  }

  // Handle incoming data
  useEffect(() => {
    if (data?.type === 'agent_status_update') {
      console.log('Agent status:', data.payload)
    }
  }, [data])

  return (
    <div>
      <div>Status: {connectionStatus}</div>
      {error && <div>Error: {error}</div>}
      <button onClick={reconnect}>Reconnect</button>
    </div>
  )
}
```

### Connection Status Component
A reusable connection status indicator is available:

```typescript
import { ConnectionStatus } from '@/components/ui/connection-status'

<ConnectionStatus showText={true} />
```

## Development Tools

### WebSocket Debug Component
For development debugging, add the debug component:

```typescript
import { WebSocketDebug } from '@/components/dev/websocket-debug'

// Add anywhere in your component tree
<WebSocketDebug />
```

This provides:
- Real-time connection status
- Event monitoring
- Connection testing
- Manual reconnection controls

### Connection Testing
Use the test utility for automated testing:

```typescript
import { testWebSocketConnection } from '@/utils/websocket-test'

const result = await testWebSocketConnection('http://localhost:8000')
console.log('Connection test:', result)
```

## Production Configuration

### CORS Settings
The backend is configured to accept connections from:
- `http://localhost:3001` (development)
- `http://localhost:3000` (alternative development)
- Production origins (from `ALLOWED_ORIGINS` setting)

### Connection Parameters
- **Ping Timeout**: 60 seconds
- **Ping Interval**: 25 seconds  
- **Reconnection Attempts**: 5
- **Reconnection Delay**: 1-5 seconds (exponential backoff)

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if backend server is running on correct port
   - Verify `NEXT_PUBLIC_WEBSOCKET_URL` environment variable
   - Check firewall/network settings

2. **CORS Errors**
   - Ensure frontend URL is in backend's allowed origins
   - Check protocol (http vs https) consistency

3. **Frequent Disconnections**  
   - Check network stability
   - Monitor browser console for errors
   - Verify backend Socket.IO configuration

4. **Events Not Received**
   - Confirm event names match backend exactly
   - Check if client joined correct rooms
   - Monitor WebSocket network tab in dev tools

### Debug Tools
- Browser Dev Tools → Network → WS (WebSocket connections)
- Use `WebSocketDebug` component in development
- Backend logs at debug level for Socket.IO events
- Redis monitoring for connection persistence (if enabled)

## Backend Integration
This frontend WebSocket client is designed to work with the FastAPI + Socket.IO backend located in `../backend/app/websocket/socketio_manager.py`.

The backend provides:
- Room-based messaging (agents, tasks, metrics, workflows)
- Connection persistence via Redis
- Comprehensive event handling
- Auto-cleanup of disconnected clients