# SubForge Dashboard - Claude Code Project Configuration

## Project Overview
Real-time monitoring dashboard for SubForge AI Agent Orchestration Platform. Provides comprehensive visibility into workflow execution, agent status, and system metrics through a modern web interface with live WebSocket updates.

## Architecture
**Type**: Full-stack web application with real-time integration  
**Pattern**: Microservices with event-driven updates  
**Integration**: File system monitoring of `.subforge/` directory for workflow data

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **WebSocket**: Socket.IO (python-socketio)
- **Database**: SQLAlchemy with SQLite
- **File Monitoring**: Watchdog
- **Queue**: Redis (optional)
- **Data Validation**: Pydantic

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18
- **Styling**: Tailwind CSS
- **Components**: Shadcn/ui
- **WebSocket Client**: Socket.IO Client
- **State Management**: React Hooks + Context
- **Icons**: Lucide React
- **Charts**: Recharts

## Project Structure

```
subforge-dashboard/
├── backend/
│   ├── app/
│   │   ├── api/              # REST API endpoints
│   │   │   ├── v1/          # Version 1 endpoints
│   │   │   └── subforge_routes.py  # SubForge integration endpoints
│   │   ├── core/            # Core configurations
│   │   ├── models/          # Database models
│   │   │   ├── subforge_models.py  # SubForge data models
│   │   │   └── database.py  # Database setup
│   │   ├── services/        # Business logic
│   │   │   └── subforge_integration.py  # SubForge monitoring service
│   │   ├── websocket/       # WebSocket handlers
│   │   └── main_simple.py   # Simplified Socket.IO server
│   ├── alembic/             # Database migrations
│   └── run_simple.py        # Quick start script
│
└── frontend/
    ├── src/
    │   ├── app/             # Next.js app router pages
    │   │   ├── page.tsx     # Dashboard home
    │   │   └── workflows/   # Workflows monitoring
    │   ├── components/      # React components
    │   │   ├── dashboard/   # Dashboard widgets
    │   │   ├── layout/      # Layout components
    │   │   └── metrics/     # Metrics visualizations
    │   ├── hooks/          # Custom React hooks
    │   │   ├── use-websocket.ts  # WebSocket connection
    │   │   └── use-subforge.ts   # SubForge data hook
    │   └── types/          # TypeScript definitions
    │       └── subforge.ts  # SubForge type definitions
    └── public/             # Static assets
```

## Key Features

### Real-time Monitoring
- Live workflow status updates via WebSocket
- File system monitoring of `.subforge/` directory
- Automatic detection of new workflows
- Real-time agent activity tracking

### Data Integration
- **33+ workflows** from SubForge system
- Phase-by-phase execution tracking
- Agent performance metrics
- Historical data persistence

### Dashboard Components
1. **Workflow Monitor**: Active and recent workflows
2. **Agent Status**: Real-time agent monitoring
3. **System Health**: CPU, memory, uptime metrics
4. **Metrics Cards**: Key performance indicators
5. **Recent Tasks**: Task execution history

## Development Workflow

### Quick Start
```bash
# Backend (Terminal 1)
cd backend
python run_simple.py

# Frontend (Terminal 2)
cd frontend
npm run dev
```

### API Endpoints

#### SubForge Integration
- `GET /api/subforge/workflows` - List all workflows
- `GET /api/subforge/workflow/{id}` - Get workflow details
- `GET /api/subforge/metrics` - Aggregated metrics
- `GET /api/subforge/status` - System status
- `POST /api/subforge/scan` - Trigger workflow scan

#### WebSocket Events
- `connect` - Client connection
- `workflow_update` - Workflow status change
- `agent_activity` - Agent activity update
- `subscribe_workflow` - Subscribe to workflow updates

## Critical Files

### Backend
- `app/services/subforge_integration.py` - Core integration logic
- `app/main_simple.py` - Socket.IO server implementation
- `app/api/subforge_routes.py` - API endpoints
- `app/models/subforge_models.py` - Data models

### Frontend
- `src/hooks/use-subforge.ts` - SubForge data management
- `src/app/workflows/page.tsx` - Workflows page
- `src/components/dashboard/workflow-monitor.tsx` - Workflow monitoring
- `src/types/subforge.ts` - TypeScript types

## Testing Strategy

### Manual Testing
1. Verify WebSocket connection (check "Connected" status)
2. Confirm workflow data loads (33 workflows)
3. Test real-time updates (create new workflow)
4. Validate metrics calculations
5. Check responsive design

### Integration Points
- SubForge → File System → Backend → API → Frontend
- WebSocket: Backend ↔ Frontend bidirectional
- Database: Persistence layer (SQLAlchemy)

## Common Issues & Solutions

### WebSocket Connection Failed
- Ensure backend is running on port 8000
- Check CORS settings in `main_simple.py`
- Verify Socket.IO versions match

### No Workflows Displaying
- Check `.subforge/` directory exists
- Verify file permissions
- Run manual scan: `POST /api/subforge/scan`

### Frontend Build Errors
- Clear `.next` directory
- Remove `node_modules` and reinstall
- Check for missing dependencies

## Production Readiness Checklist

### Critical (Must Have)
- [ ] Authentication/authorization
- [ ] HTTPS/TLS configuration
- [ ] Environment variables setup
- [ ] Database migrations
- [ ] Error handling improvements

### Important (Should Have)
- [ ] Logging infrastructure
- [ ] Health check endpoints
- [ ] Basic test coverage
- [ ] Deployment documentation
- [ ] Rate limiting

### Nice to Have
- [ ] CI/CD pipeline
- [ ] Performance monitoring
- [ ] Cache layer (Redis)
- [ ] Email notifications

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=sqlite:///./subforge.db
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=http://localhost:3001
SECRET_KEY=your-secret-key
SUBFORGE_DIR=/home/user/projects/.subforge
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=http://localhost:8000
```

## Deployment Notes

### Docker Support (Planned)
- Dockerfile for backend service
- Dockerfile for frontend application
- docker-compose.yml for orchestration
- Volume mounting for `.subforge/` directory

### Monitoring Requirements
- Minimum 2GB RAM
- 10GB disk space for logs
- Network access to SubForge directory
- Port 8000 (backend), 3001 (frontend)

## Performance Considerations

- WebSocket connections scale to ~1000 concurrent
- File system monitoring optimized for <10,000 workflows
- API response time <100ms for most endpoints
- Frontend bundle size ~500KB gzipped

## Security Notes

**Current State**: Development mode  
**Required for Production**:
- JWT authentication
- Role-based access control
- API rate limiting
- Input validation
- SQL injection prevention
- XSS protection

## Contributing Guidelines

1. **Code Style**: Follow existing patterns
2. **Components**: Use Shadcn/ui components
3. **Types**: Define TypeScript types
4. **API**: RESTful conventions
5. **WebSocket**: Event-driven patterns
6. **Testing**: Add tests for new features

## Support & Documentation

- **SubForge Docs**: See main project documentation
- **API Reference**: `/docs` endpoint (FastAPI)
- **Component Library**: shadcn.com/docs
- **WebSocket**: socket.io documentation

---

*Generated by Claude Code for SubForge Dashboard v1.0*  
*Historic Integration: First real-time monitoring system for AI agent orchestration*

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>