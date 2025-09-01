# SubForge Dashboard Backend Setup Guide

## 🎯 Overview

You now have a complete, production-ready FastAPI backend for the SubForge Dashboard! This backend provides:

- ✅ **Complete REST API** with async/await patterns
- ✅ **Real-time WebSocket** communication
- ✅ **SQLAlchemy models** with proper relationships
- ✅ **Pydantic schemas** for validation
- ✅ **CORS configuration** for frontend integration  
- ✅ **File watcher** for SubForge directory monitoring
- ✅ **Database migrations** with Alembic
- ✅ **Comprehensive logging** and error handling
- ✅ **Production configuration** support

## 🏗️ Architecture Created

### Directory Structure
```
backend/
├── app/
│   ├── api/v1/              # API endpoints
│   │   ├── agents.py        # Agent management endpoints
│   │   ├── tasks.py         # Task management endpoints  
│   │   ├── workflows.py     # Workflow management endpoints
│   │   └── system.py        # System monitoring endpoints
│   ├── core/
│   │   └── config.py        # Configuration management
│   ├── database/
│   │   ├── base.py          # SQLAlchemy base
│   │   └── session.py       # Database sessions
│   ├── models/              # SQLAlchemy models
│   │   ├── agent.py         # Agent model
│   │   ├── task.py          # Task model  
│   │   ├── workflow.py      # Workflow model
│   │   └── system_metrics.py # System metrics model
│   ├── schemas/             # Pydantic schemas
│   │   ├── agent.py         # Agent validation schemas
│   │   ├── task.py          # Task validation schemas
│   │   ├── workflow.py      # Workflow validation schemas
│   │   └── system_metrics.py # Metrics schemas
│   ├── utils/
│   │   ├── file_watcher.py  # SubForge file monitoring
│   │   └── logging_config.py # Logging setup
│   ├── websocket/
│   │   └── manager.py       # WebSocket connection management
│   └── main.py              # FastAPI application
├── alembic/                 # Database migration scripts
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── run.py                   # Development server runner
└── verify_setup.py          # Setup verification script
```

### API Endpoints Created

#### Agents (`/api/v1/agents`)
- `GET /` - List agents with filtering
- `POST /` - Create agent
- `GET /{id}` - Get agent details
- `PUT /{id}` - Update agent
- `PATCH /{id}/status` - Update status
- `PATCH /{id}/metrics` - Update metrics  
- `POST /{id}/heartbeat` - Agent heartbeat
- `DELETE /{id}` - Delete agent

#### Tasks (`/api/v1/tasks`)
- `GET /` - List tasks with filtering
- `POST /` - Create task
- `GET /{id}` - Get task details
- `PUT /{id}` - Update task
- `PATCH /{id}/status` - Update status
- `PATCH /{id}/progress` - Update progress
- `PATCH /{id}/assign` - Assign to agent
- `POST /{id}/dependencies` - Add dependency
- `PATCH /bulk` - Bulk update tasks

#### Workflows (`/api/v1/workflows`)  
- `GET /` - List workflows
- `POST /` - Create workflow
- `GET /{id}` - Get workflow details
- `PUT /{id}` - Update workflow
- `PATCH /{id}/status` - Update status
- `POST /{id}/agents` - Assign agent
- `POST /{id}/execute` - Execute workflow
- `POST /templates` - Create template

#### System (`/api/v1/system`)
- `GET /health` - Health check
- `GET /status` - System status
- `GET /metrics/current` - Current metrics
- `GET /metrics/history` - Historical metrics
- `GET /metrics/agents` - Agent metrics
- `GET /metrics/tasks` - Task metrics  
- `GET /metrics/workflows` - Workflow metrics

### Database Models

#### Agent Model
```python
class Agent:
    id: UUID
    name: str
    agent_type: str
    status: str  # active, idle, busy, offline, error
    current_task_id: UUID
    model: str  # claude-3-sonnet, etc.
    tools: List[str]
    capabilities: List[str]
    performance_metrics: dict
    created_at: datetime
    updated_at: datetime
```

#### Task Model  
```python
class Task:
    id: UUID
    title: str
    description: str
    status: str  # pending, in_progress, completed, failed
    priority: str  # low, medium, high, critical
    assigned_agent_id: UUID
    workflow_id: UUID
    progress_percentage: float
    dependencies: List[str]
    time_tracking: dict
    created_at: datetime
    updated_at: datetime
```

#### Workflow Model
```python
class Workflow:
    id: UUID  
    name: str
    description: str
    status: str  # active, paused, completed, failed
    progress_percentage: float
    assigned_agents: List[dict]
    configuration: dict
    quality_metrics: dict
    created_at: datetime
    updated_at: datetime
```

### WebSocket Events

Real-time events broadcasted:
- `agent_created`, `agent_updated`, `agent_status_updated`
- `task_created`, `task_updated`, `task_status_updated`  
- `workflow_created`, `workflow_updated`, `workflow_executed`
- `system_metrics_updated`
- `file_system_event` (SubForge file changes)

## 🚀 Next Steps

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Setup Database
```bash
# For SQLite (default) - auto-created
# For PostgreSQL - create database first

# Run migrations
alembic upgrade head
```

### 4. Start Development Server
```bash
# Option 1: Using run script
python run.py --reload

# Option 2: Using uvicorn directly  
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Setup
```bash
python verify_setup.py
```

### 6. Test API
- Visit: http://localhost:8000/docs (Swagger UI)
- Visit: http://localhost:8000/health (Health check)
- WebSocket: ws://localhost:8000/ws

## 🔧 Configuration Options

### Key Environment Variables
```env
# Application
ENVIRONMENT=development  # development, production, testing
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database  
DATABASE_URL=sqlite:///./subforge_dashboard.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# File Monitoring
ENABLE_FILE_WATCHER=true
WATCHER_DEBOUNCE_SECONDS=1.0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=standard  # or 'json'
```

## 🔌 Frontend Integration

The backend is ready for integration with the Next.js frontend:

1. **CORS Configured**: Allows frontend requests
2. **WebSocket Ready**: Real-time updates via `/ws`
3. **Error Handling**: Structured error responses
4. **Validation**: Pydantic request/response validation
5. **Documentation**: Auto-generated OpenAPI/Swagger docs

### Frontend API Client Example
```typescript
// API client configuration
const API_BASE = 'http://localhost:8000/api/v1';
const WS_URL = 'ws://localhost:8000/ws';

// WebSocket connection
const ws = new WebSocket(WS_URL);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

## 📊 Monitoring & Operations

### Health Checks
- `GET /health` - Application health
- `GET /api/v1/system/status` - Detailed system status

### Logging
- Console output with structured formatting
- File logging to `logs/` directory
- JSON logging support for production
- Correlation IDs for request tracking

### Performance Features
- Async/await throughout
- Database connection pooling
- WebSocket connection management
- File watching with debouncing
- Structured error handling

## 🧪 Testing

### Run Tests
```bash
pytest tests/
```

### Manual Testing
1. Start server: `python run.py --reload`
2. Open Swagger UI: http://localhost:8000/docs
3. Test WebSocket: Use browser console or WebSocket client
4. Check logs: `tail -f logs/subforge_dashboard.log`

## 🚀 Production Deployment

### Requirements
- Python 3.8+
- PostgreSQL (recommended)
- Redis (optional, for caching)

### Production Configuration
```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=your-secure-secret-key
ALLOWED_ORIGINS=["https://yourdomain.com"]
```

### Docker Support
A Dockerfile can be added for containerized deployment.

## ✅ What You Have

You now have a **complete, production-ready FastAPI backend** with:

- ✅ **Full REST API** for agents, tasks, workflows
- ✅ **Real-time WebSocket** updates  
- ✅ **Database models** with relationships
- ✅ **Data validation** with Pydantic
- ✅ **File monitoring** for SubForge integration
- ✅ **Comprehensive logging** and error handling
- ✅ **Database migrations** with Alembic
- ✅ **Development tools** and verification
- ✅ **CORS configuration** for frontend
- ✅ **Health checks** and monitoring
- ✅ **Production configuration** support

The backend is **ready to run** and **ready for frontend integration**! 🎉