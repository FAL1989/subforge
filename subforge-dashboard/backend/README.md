# SubForge Dashboard Backend

FastAPI backend for the SubForge monitoring dashboard with real-time WebSocket updates, comprehensive agent tracking, task management, and advanced analytics.

## Features

- **FastAPI Framework**: Modern, async Python API framework
- **Real-time Updates**: WebSocket support for live dashboard updates
- **SQLAlchemy ORM**: Async database operations with PostgreSQL/SQLite support
- **Pydantic Validation**: Request/response validation and serialization
- **File Watching**: Monitors SubForge directory changes
- **Comprehensive Logging**: Structured logging with JSON support
- **Database Migrations**: Alembic integration for schema management
- **Production Ready**: CORS, error handling, security features

## Architecture

```
backend/
├── app/
│   ├── api/v1/          # API endpoints (agents, tasks, workflows, system)
│   ├── core/            # Configuration and settings
│   ├── database/        # Database configuration and sessions
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas for validation
│   ├── utils/           # Utility modules (logging, file watcher)
│   ├── websocket/       # WebSocket connection management
│   └── main.py         # FastAPI application entry point
├── alembic/            # Database migration scripts
├── requirements.txt    # Python dependencies
└── run.py             # Development server runner
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Setup

Copy the example environment file and customize:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup

For SQLite (default):
```bash
# Database will be created automatically
```

For PostgreSQL:
```bash
# Create database first, then update DATABASE_URL in .env
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/subforge_dashboard
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start Development Server

```bash
python run.py --reload
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /` - API information
- `WebSocket /ws` - Real-time updates

### Agent Management
- `GET /api/v1/agents` - List agents with filtering
- `POST /api/v1/agents` - Create new agent
- `GET /api/v1/agents/{id}` - Get agent details
- `PUT /api/v1/agents/{id}` - Update agent
- `PATCH /api/v1/agents/{id}/status` - Update agent status
- `PATCH /api/v1/agents/{id}/metrics` - Update agent metrics
- `POST /api/v1/agents/{id}/heartbeat` - Agent heartbeat
- `DELETE /api/v1/agents/{id}` - Delete agent

### Task Management
- `GET /api/v1/tasks` - List tasks with filtering
- `POST /api/v1/tasks` - Create new task
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task
- `PATCH /api/v1/tasks/{id}/status` - Update task status
- `PATCH /api/v1/tasks/{id}/progress` - Update task progress
- `PATCH /api/v1/tasks/{id}/assign` - Assign task to agent
- `POST /api/v1/tasks/{id}/dependencies` - Add task dependency
- `DELETE /api/v1/tasks/{id}/dependencies/{dep_id}` - Remove dependency

### Workflow Management
- `GET /api/v1/workflows` - List workflows
- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows/{id}` - Get workflow details
- `PUT /api/v1/workflows/{id}` - Update workflow
- `PATCH /api/v1/workflows/{id}/status` - Update workflow status
- `POST /api/v1/workflows/{id}/agents` - Assign agent to workflow
- `POST /api/v1/workflows/{id}/execute` - Execute workflow

### System Monitoring
- `GET /api/v1/system/status` - System status summary
- `GET /api/v1/system/metrics/current` - Current metrics
- `GET /api/v1/system/metrics/history` - Historical metrics
- `POST /api/v1/system/metrics` - Create metrics snapshot
- `GET /api/v1/system/metrics/agents` - Agent metrics
- `GET /api/v1/system/metrics/tasks` - Task metrics
- `GET /api/v1/system/metrics/workflows` - Workflow metrics

## WebSocket Events

The WebSocket connection provides real-time updates for:

- `agent_created` - New agent registered
- `agent_updated` - Agent information updated
- `agent_status_updated` - Agent status changed
- `task_created` - New task created
- `task_updated` - Task updated
- `task_status_updated` - Task status changed
- `workflow_created` - New workflow created
- `workflow_updated` - Workflow updated
- `system_metrics_updated` - System metrics updated
- `file_system_event` - SubForge file changes

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Runtime environment |
| `DEBUG` | `true` | Enable debug features |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | SQLite | Database connection URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENABLE_FILE_WATCHER` | `true` | Enable file monitoring |

### Database Configuration

#### SQLite (Development)
```env
DATABASE_URL=sqlite:///./subforge_dashboard.db
```

#### PostgreSQL (Production)
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/subforge_dashboard
```

### Logging Configuration

The backend supports both standard and JSON logging formats:

```env
LOG_LEVEL=INFO
LOG_FORMAT=standard  # or 'json'
```

Logs are written to:
- Console output
- `logs/subforge_dashboard.log` (all logs)
- `logs/subforge_dashboard_errors.log` (errors only)

## Database Models

### Agent
- **id**: UUID primary key
- **name**: Agent name
- **agent_type**: Agent type/role  
- **status**: Current status (active, idle, busy, offline)
- **configuration**: Agent configuration (model, tools, capabilities)
- **performance_metrics**: Success rate, response time, uptime
- **current_task**: Currently assigned task

### Task
- **id**: UUID primary key
- **title**: Task title
- **description**: Task description
- **status**: Task status (pending, in_progress, completed, failed)
- **priority**: Priority level (low, medium, high, critical)
- **assigned_agent_id**: Assigned agent reference
- **workflow_id**: Parent workflow reference
- **progress_percentage**: Completion progress
- **dependencies**: Task dependencies
- **time_tracking**: Duration estimates and actuals

### Workflow
- **id**: UUID primary key
- **name**: Workflow name
- **description**: Workflow description
- **status**: Workflow status
- **progress_percentage**: Overall progress
- **assigned_agents**: List of assigned agents
- **configuration**: Workflow configuration
- **quality_metrics**: Success rate, efficiency scores

### SystemMetrics
- **id**: UUID primary key
- **recorded_at**: Timestamp
- **agent_stats**: Agent counts by status
- **task_stats**: Task counts by status
- **performance_metrics**: System performance data
- **success_rates**: Overall success rates

## Development

### Running Tests

```bash
pytest tests/
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

### Code Formatting

```bash
black app/
ruff check app/
```

### Debug Mode

When `DEBUG=true`, additional endpoints are available:
- `/debug/connections` - WebSocket connection info
- `/debug/broadcast` - Send test WebSocket messages
- `/debug/file-watcher` - File watcher status

## Production Deployment

### Docker Deployment
```bash
# Build image
docker build -t subforge-dashboard-backend .

# Run container
docker run -p 8000:8000 subforge-dashboard-backend
```

### Environment Setup
1. Set `ENVIRONMENT=production`
2. Configure production database
3. Set secure `SECRET_KEY`
4. Configure proper CORS origins
5. Set up proper logging
6. Configure Redis for caching

### Performance Considerations
- Use PostgreSQL for production
- Set up Redis for caching and sessions
- Configure proper connection pooling
- Enable proper logging and monitoring
- Set up health checks and metrics collection

## Integration with Frontend

The backend provides a complete REST API and WebSocket interface for the Next.js frontend:

1. **REST API**: Full CRUD operations for all entities
2. **WebSocket**: Real-time updates and notifications
3. **CORS**: Configured for frontend integration
4. **Error Handling**: Structured error responses
5. **Validation**: Request/response validation with Pydantic

## Monitoring and Observability

- **Health Checks**: `/health` endpoint for service monitoring
- **Metrics**: Comprehensive system metrics collection
- **Logging**: Structured logging with correlation IDs
- **WebSocket Monitoring**: Connection tracking and cleanup
- **File Monitoring**: SubForge directory change detection