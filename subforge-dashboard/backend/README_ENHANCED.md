# SubForge Dashboard Backend - Enhanced Version

A production-ready FastAPI backend with advanced WebSocket features, background task processing, real-time updates, caching, rate limiting, and comprehensive API functionality.

## 🚀 Features

### Core Enhancements
- **Advanced WebSocket Manager**: Room-based messaging, authentication, connection state management
- **Background Task Processing**: Celery integration for async operations
- **Redis Integration**: Caching, pub/sub, session management
- **Rate Limiting**: Per-user and per-IP rate limiting with Redis backend
- **Response Caching**: Intelligent API response caching with TTL
- **File Upload System**: Secure file uploads with validation and metadata
- **API Versioning**: Both v1 (stable) and v2 (enhanced) APIs

### WebSocket Features (v2)
- **Room Management**: Join/leave rooms for targeted messaging
- **Authentication**: WebSocket connection authentication and authorization
- **Message Queuing**: Persistent message queuing for offline users
- **Connection State**: Advanced connection lifecycle management
- **Event History**: Full event history with replay functionality
- **Real-time Broadcasting**: Efficient message broadcasting to rooms or all clients

### API Features (v2)
- **Advanced Filtering**: Complex query filtering with multiple parameters
- **Bulk Operations**: Batch operations on multiple resources
- **Pagination**: Efficient pagination with metadata headers
- **File Uploads**: Multi-file uploads with validation and processing
- **Background Tasks**: Async task submission and monitoring
- **Metrics & Analytics**: Comprehensive API usage analytics

### Background Tasks
- **Agent Configuration Processing**: Async agent setup and validation
- **System Metrics Analysis**: Automated system performance analysis
- **Data Backup Operations**: Scheduled data backup and archival
- **File Processing**: Async file validation and transformation

## 📋 Prerequisites

- Python 3.8+
- Redis Server
- PostgreSQL (optional, defaults to SQLite)

## 🛠️ Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Redis:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   
   # Windows - Download from https://redis.io/download
   ```

3. **Set up environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🚦 Quick Start

### Option 1: Enhanced Startup Script (Recommended)
```bash
python start_enhanced.py
```

This script will:
- Start Redis server (if not running)
- Start Celery worker for background tasks
- Start FastAPI server with all enhancements
- Provide service URLs and monitoring info

### Option 2: Manual Startup

1. **Start Redis:**
   ```bash
   redis-server
   ```

2. **Start Celery Worker:**
   ```bash
   celery -A app.services.background_tasks.celery_app worker --loglevel=info
   ```

3. **Start FastAPI Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 📊 Service URLs

Once started, the following services will be available:

- **API Documentation**: http://localhost:8000/docs
- **API v1 (Stable)**: http://localhost:8000/api/v1/
- **API v2 (Enhanced)**: http://localhost:8000/api/v2/
- **WebSocket v1**: ws://localhost:8000/ws
- **WebSocket v2 (Enhanced)**: ws://localhost:8000/ws/v2
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

Key configuration options in `app/core/config.py`:

```python
# Redis
REDIS_URL = "redis://localhost:6379/0"
REDIS_EXPIRE = 300

# Rate Limiting
ENABLE_RATE_LIMITING = True

# Caching
ENABLE_CACHING = True
CACHE_TTL_DEFAULT = 300

# Background Tasks
ENABLE_BACKGROUND_TASKS = True
CELERY_BROKER_URL = "redis://localhost:6379/2"
CELERY_RESULT_BACKEND = "redis://localhost:6379/3"

# File Upload
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_UPLOAD = 10
UPLOAD_DIR = "uploads"
```

## 📡 WebSocket Usage

### Enhanced WebSocket (v2) Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/v2');

// Join a room
ws.send(JSON.stringify({
    type: 'join_room',
    room: 'agent_monitoring'
}));

// Send a message to a room
ws.send(JSON.stringify({
    type: 'room_message',
    room: 'agent_monitoring',
    data: {
        message: 'Hello room members!'
    }
}));

// Listen for messages
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};
```

### Available WebSocket Message Types

- `join_room` / `leave_room`: Room management
- `ping` / `pong`: Connection health checks
- `auth_request`: Authentication
- `room_message`: Send message to room
- `system_notification`: System-wide notifications
- `agent_update`: Agent status updates
- `task_update`: Task progress updates
- `metrics_update`: System metrics updates

## 🔌 API Usage Examples

### Enhanced Agents API (v2)

```bash
# List agents with filtering
curl "http://localhost:8000/api/v2/agents?status=active&limit=10&sort_by=name"

# Create agent
curl -X POST "http://localhost:8000/api/v2/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Processor",
    "type": "data-scientist",
    "configuration": {
      "model": "claude-3-sonnet",
      "tools": ["read", "write", "analyze"],
      "max_tokens": 4096
    },
    "tags": ["data", "analysis"]
  }'

# Bulk operations
curl -X POST "http://localhost:8000/api/v2/agents/bulk-operation" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_ids": ["agent1", "agent2"],
    "operation": "start"
  }'

# Upload agent configuration
curl -X POST "http://localhost:8000/api/v2/agents/agent123/configuration/upload" \
  -F "file=@config.json"
```

### Background Tasks API

```bash
# Submit a background task
curl -X POST "http://localhost:8000/api/v2/background-tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "analyze_system_metrics",
    "task_args": ["24h"],
    "priority": "normal",
    "metadata": {"analysis_type": "performance"}
  }'

# Get task status
curl "http://localhost:8000/api/v2/background-tasks/task_id_here"

# Get task statistics
curl "http://localhost:8000/api/v2/background-tasks/statistics"
```

### File Upload API

```bash
# Upload configuration files
curl -X POST "http://localhost:8000/api/v2/files/upload/agent_configs" \
  -F "files=@agent1.json" \
  -F "files=@agent2.yaml" \
  -F "tags=production,v2" \
  -F "metadata={\"project\": \"dashboard_upgrade\"}"

# List uploaded files
curl "http://localhost:8000/api/v2/files?file_type=agent_configs&limit=20"

# Download file
curl "http://localhost:8000/api/v2/files/file_id_here/download" -o downloaded_file.json

# Validate configuration file
curl "http://localhost:8000/api/v2/files/file_id_here/validate?validation_type=agent_config"
```

### WebSocket Management API

```bash
# Get active connections
curl "http://localhost:8000/api/v2/websocket/connections"

# Get rooms
curl "http://localhost:8000/api/v2/websocket/rooms"

# Broadcast message
curl -X POST "http://localhost:8000/api/v2/websocket/broadcast" \
  -H "Content-Type: application/json" \
  -d '{
    "message_type": "system_notification",
    "room": "admin_room",
    "data": {
      "notification": "System maintenance in 10 minutes"
    }
  }'

# Get event history
curl "http://localhost:8000/api/v2/websocket/event-history?room=agent_monitoring&limit=50"
```

## 🏗️ Architecture

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │◄──►│   Redis Cache   │◄──►│ Celery Workers  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Pub/Sub       │    │  Background     │
│   Manager       │    │   Messaging     │    │  Tasks Queue    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

1. **Enhanced WebSocket Manager**: Handles connections, rooms, and real-time messaging
2. **Redis Service**: Provides caching, pub/sub, and session management
3. **API Enhancement Service**: Adds rate limiting, caching, and metrics
4. **Background Task Service**: Manages async operations with Celery
5. **File Upload Service**: Handles secure file uploads and validation

### Data Flow

1. **API Requests**: Rate limited → Cached responses → Database/Redis
2. **WebSocket Messages**: Connection management → Room routing → Event history
3. **Background Tasks**: Queue → Celery workers → Result storage → WebSocket broadcast
4. **File Uploads**: Validation → Storage → Background processing → Metadata indexing

## 📈 Monitoring & Analytics

### Built-in Metrics

- **API Usage**: Request counts, response times, error rates
- **WebSocket**: Connection counts, message throughput, room statistics
- **Background Tasks**: Queue lengths, processing times, success rates
- **System**: Memory usage, disk usage, Redis performance

### Endpoints for Monitoring

- `/api/v2/system/metrics`: System performance metrics
- `/api/v2/system/health`: Health check with component status
- `/api/v2/system/analytics`: Advanced system analytics
- `/api/v2/background-tasks/statistics`: Task processing statistics
- `/api/v2/websocket/statistics`: WebSocket system statistics
- `/api/v2/files/statistics`: File upload statistics

## 🔒 Security Features

- **Rate Limiting**: Prevents API abuse with per-user/IP limits
- **Input Validation**: Comprehensive request validation with Pydantic
- **File Upload Security**: Type validation, size limits, malware scanning hooks
- **WebSocket Authentication**: Connection-level authentication support
- **CORS Configuration**: Configurable cross-origin policies
- **Request Logging**: Comprehensive request/response logging

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## 📝 Environment Variables

Create a `.env` file with your configuration:

```env
# Application
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost/subforge_dashboard
# Or use SQLite (default)
# DATABASE_URL=sqlite:///./subforge_dashboard.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# External Services
ENABLE_BACKGROUND_TASKS=true
ENABLE_RATE_LIMITING=true
ENABLE_CACHING=true

# File Upload
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=uploads
```

## 🚀 Production Deployment

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: subforge_dashboard
      POSTGRES_USER: subforge
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
  
  celery:
    build: .
    command: celery -A app.services.background_tasks.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres
    volumes:
      - ./uploads:/app/uploads
  
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=postgresql://subforge:secure_password@postgres/subforge_dashboard
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
```

### Performance Tuning

- **Database Connection Pooling**: Configured in `database/session.py`
- **Redis Connection Pooling**: Max connections set to 20
- **Celery Concurrency**: Adjust based on CPU cores
- **Rate Limiting**: Tune limits based on expected load
- **Caching TTL**: Adjust based on data freshness requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📚 Additional Documentation

- [API v2 Reference](./docs/api-v2-reference.md)
- [WebSocket Protocol](./docs/websocket-protocol.md)
- [Background Tasks Guide](./docs/background-tasks.md)
- [Deployment Guide](./docs/deployment.md)
- [Performance Tuning](./docs/performance.md)

## 🆘 Troubleshooting

### Common Issues

1. **Redis Connection Failed**: Ensure Redis server is running
2. **Celery Worker Not Starting**: Check Redis connection and Python path
3. **File Upload Errors**: Verify upload directory permissions
4. **WebSocket Connection Issues**: Check CORS configuration
5. **Rate Limiting Too Aggressive**: Adjust limits in config

### Debugging

Enable debug mode:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python start_enhanced.py
```

Check logs:
- FastAPI logs: Console output
- Celery logs: Celery worker output
- Redis logs: Redis server logs

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review the logs for error details
- Open an issue in the repository
- Check the FastAPI and Celery documentation

---

**SubForge Dashboard Enhanced Backend** - Production-ready API with advanced real-time features, background processing, and comprehensive monitoring.