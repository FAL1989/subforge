"""
Simplified FastAPI app with Socket.IO support for testing
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import socketio
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

# Import SubForge integration
try:
    from .api.subforge_routes import router as subforge_router
    from .services.subforge_integration import subforge_integration
except ImportError:
    # Fallback for direct execution
    from api.subforge_routes import router as subforge_router
    from services.subforge_integration import subforge_integration

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

# Include SubForge router
app.include_router(subforge_router)

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

@app.get("/api/metrics")
async def get_metrics(time_range: str = Query(default="7d", alias="range", description="Time range: 24h, 7d, 30d, 90d")):
    """Return metrics data with time range support"""
    # Generate mock data based on time range
    days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}.get(time_range, 7)
    base_date = datetime.now() - timedelta(days=days)
    
    # Generate task completion data
    task_completion = []
    for i in range(days):
        date = base_date + timedelta(days=i)
        completed = 15 + (i * 2) + (i % 3)
        failed = max(1, i % 4)
        task_completion.append({
            "date": date.strftime("%Y-%m-%d"),
            "completed": completed,
            "failed": failed,
            "total": completed + failed
        })
    
    # Generate system health data (last 24 data points)
    system_health = []
    for i in range(24):
        timestamp = datetime.now() - timedelta(hours=23-i)
        system_health.append({
            "timestamp": timestamp.isoformat() + "Z",
            "cpu": 35 + (i * 2) + (i % 10),
            "memory": 45 + (i * 1.5) + (i % 8),
            "activeConnections": 8 + (i % 12)
        })
    
    # Generate productivity data
    productivity = []
    for i in range(days):
        date = base_date + timedelta(days=i)
        productivity.append({
            "date": date.strftime("%Y-%m-%d"),
            "tasksPerHour": 1.8 + (i * 0.2),
            "agentsActive": min(6, 4 + (i % 3)),
            "efficiency": 78 + (i * 2) + (i % 5)
        })
    
    return {
        "taskCompletion": task_completion,
        "agentPerformance": [
            {"agentName": "Frontend Developer", "successRate": 96, "avgResponseTime": 1.2, "tasksCompleted": 23},
            {"agentName": "Backend Developer", "successRate": 94, "avgResponseTime": 2.1, "tasksCompleted": 18},
            {"agentName": "Code Reviewer", "successRate": 99, "avgResponseTime": 1.8, "tasksCompleted": 31},
            {"agentName": "Data Scientist", "successRate": 98, "avgResponseTime": 3.5, "tasksCompleted": 12},
            {"agentName": "DevOps Engineer", "successRate": 92, "avgResponseTime": 4.2, "tasksCompleted": 8},
            {"agentName": "Test Engineer", "successRate": 88, "avgResponseTime": 2.5, "tasksCompleted": 7},
        ],
        "systemHealth": system_health[-24:],  # Last 24 hours
        "productivity": productivity
    }

@app.get("/api/agents")
async def get_agents():
    """Return simple agent list for dashboard"""
    return {
        "agents": [
            {
                "id": "1",
                "name": "Frontend Developer",
                "type": "Development",
                "status": "active",
                "lastActive": "2 minutes ago",
                "tasksCompleted": 23,
                "currentTask": "Building React components"
            },
            {
                "id": "2",
                "name": "Backend Developer",
                "type": "Development",
                "status": "busy",
                "lastActive": "1 minute ago",
                "tasksCompleted": 18,
                "currentTask": "API endpoint optimization"
            },
            {
                "id": "3",
                "name": "Data Scientist",
                "type": "Analytics",
                "status": "idle",
                "lastActive": "15 minutes ago",
                "tasksCompleted": 12
            },
            {
                "id": "4",
                "name": "DevOps Engineer",
                "type": "Infrastructure",
                "status": "active",
                "lastActive": "5 minutes ago",
                "tasksCompleted": 8,
                "currentTask": "Docker container updates"
            },
            {
                "id": "5",
                "name": "Code Reviewer",
                "type": "Quality",
                "status": "busy",
                "lastActive": "3 minutes ago",
                "tasksCompleted": 31,
                "currentTask": "Security audit review"
            },
            {
                "id": "6",
                "name": "Test Engineer",
                "type": "Quality",
                "status": "error",
                "lastActive": "1 hour ago",
                "tasksCompleted": 7
            }
        ]
    }

@app.get("/api/agents/detailed")
async def get_agents_detailed():
    """Return detailed agent information for agents page"""
    return {
        "agents": [
            {
                "id": "1",
                "name": "Frontend Developer",
                "type": "Development",
                "status": "active",
                "model": "Claude Sonnet",
                "capabilities": ["React", "TypeScript", "Tailwind CSS", "Next.js"],
                "tasksCompleted": 23,
                "currentTask": "Building React components",
                "lastActive": "2 minutes ago",
                "createdAt": "2024-01-01T00:00:00Z",
                "performance": {
                    "successRate": 96,
                    "avgResponseTime": 1.2,
                    "totalTasks": 25
                }
            },
            {
                "id": "2",
                "name": "Backend Developer",
                "type": "Development",
                "status": "busy",
                "model": "Claude Sonnet",
                "capabilities": ["FastAPI", "Python", "PostgreSQL", "Redis"],
                "tasksCompleted": 18,
                "currentTask": "API endpoint optimization",
                "lastActive": "1 minute ago",
                "createdAt": "2024-01-01T00:00:00Z",
                "performance": {
                    "successRate": 94,
                    "avgResponseTime": 2.1,
                    "totalTasks": 20
                }
            },
            {
                "id": "3",
                "name": "Data Scientist",
                "type": "Analytics",
                "status": "idle",
                "model": "Claude Opus",
                "capabilities": ["Python", "Pandas", "Machine Learning", "Statistics"],
                "tasksCompleted": 12,
                "lastActive": "15 minutes ago",
                "createdAt": "2024-01-01T00:00:00Z",
                "performance": {
                    "successRate": 98,
                    "avgResponseTime": 3.5,
                    "totalTasks": 13
                }
            },
            {
                "id": "4",
                "name": "DevOps Engineer",
                "type": "Infrastructure",
                "status": "active",
                "model": "Claude Sonnet",
                "capabilities": ["Docker", "Kubernetes", "AWS", "CI/CD"],
                "tasksCompleted": 8,
                "currentTask": "Docker container updates",
                "lastActive": "5 minutes ago",
                "createdAt": "2024-01-01T00:00:00Z",
                "performance": {
                    "successRate": 92,
                    "avgResponseTime": 4.2,
                    "totalTasks": 10
                }
            },
            {
                "id": "5",
                "name": "Code Reviewer",
                "type": "Quality",
                "status": "busy",
                "model": "Claude Sonnet",
                "capabilities": ["Code Review", "Security", "Best Practices", "Documentation"],
                "tasksCompleted": 31,
                "currentTask": "Security audit review",
                "lastActive": "3 minutes ago",
                "createdAt": "2024-01-01T00:00:00Z",
                "performance": {
                    "successRate": 99,
                    "avgResponseTime": 1.8,
                    "totalTasks": 32
                }
            },
            {
                "id": "6",
                "name": "Test Engineer",
                "type": "Quality",
                "status": "error",
                "model": "Claude Haiku",
                "capabilities": ["Unit Testing", "Integration Testing", "Test Automation"],
                "tasksCompleted": 7,
                "lastActive": "1 hour ago",
                "createdAt": "2024-01-01T00:00:00Z",
                "performance": {
                    "successRate": 88,
                    "avgResponseTime": 2.5,
                    "totalTasks": 9
                }
            }
        ]
    }

@app.get("/api/tasks/recent")
async def get_recent_tasks():
    """Return recent tasks for dashboard"""
    return {
        "tasks": [
            {
                "id": "1",
                "title": "Implement user authentication system",
                "agent": "Backend Developer",
                "status": "completed",
                "priority": "high",
                "timestamp": "2 minutes ago",
                "duration": 1800
            },
            {
                "id": "2",
                "title": "Design responsive navigation component",
                "agent": "Frontend Developer",
                "status": "in_progress",
                "priority": "medium",
                "timestamp": "5 minutes ago"
            },
            {
                "id": "3",
                "title": "Optimize database queries",
                "agent": "Backend Developer",
                "status": "completed",
                "priority": "medium",
                "timestamp": "12 minutes ago",
                "duration": 3600
            },
            {
                "id": "4",
                "title": "Set up CI/CD pipeline",
                "agent": "DevOps Engineer",
                "status": "failed",
                "priority": "high",
                "timestamp": "15 minutes ago"
            },
            {
                "id": "5",
                "title": "Write unit tests for API endpoints",
                "agent": "Test Engineer",
                "status": "pending",
                "priority": "low",
                "timestamp": "18 minutes ago"
            },
            {
                "id": "6",
                "title": "Code review for payment integration",
                "agent": "Code Reviewer",
                "status": "completed",
                "priority": "high",
                "timestamp": "25 minutes ago",
                "duration": 2400
            },
            {
                "id": "7",
                "title": "Analyze user engagement metrics",
                "agent": "Data Scientist",
                "status": "in_progress",
                "priority": "medium",
                "timestamp": "32 minutes ago"
            },
            {
                "id": "8",
                "title": "Update deployment documentation",
                "agent": "DevOps Engineer",
                "status": "completed",
                "priority": "low",
                "timestamp": "45 minutes ago",
                "duration": 1200
            }
        ]
    }

@app.get("/api/tasks")
async def get_all_tasks():
    """Return all tasks for task management page"""
    return {
        "tasks": [
            {
                "id": "1",
                "title": "Implement user authentication system",
                "description": "Build a comprehensive authentication system with JWT tokens, password reset, and multi-factor authentication support.",
                "status": "done",
                "priority": "high",
                "agent": "backend-developer",
                "assignee": "Backend Developer",
                "tags": ["authentication", "security", "backend"],
                "createdAt": "2024-01-15T09:00:00Z",
                "updatedAt": "2024-01-16T14:30:00Z",
                "dueDate": "2024-01-18T17:00:00Z",
                "estimatedTime": 8,
                "actualTime": 6.5,
                "dependencies": []
            },
            {
                "id": "2",
                "title": "Design responsive navigation component",
                "description": "Create a mobile-first navigation component with smooth animations and accessibility features.",
                "status": "in_progress",
                "priority": "medium",
                "agent": "frontend-developer",
                "assignee": "Frontend Developer",
                "tags": ["ui", "navigation", "responsive"],
                "createdAt": "2024-01-16T08:15:00Z",
                "updatedAt": "2024-01-16T16:20:00Z",
                "dueDate": "2024-01-17T12:00:00Z",
                "estimatedTime": 4,
                "dependencies": []
            },
            {
                "id": "3",
                "title": "Optimize database queries",
                "description": "Analyze and optimize slow database queries, add proper indexing, and implement query caching.",
                "status": "done",
                "priority": "medium",
                "agent": "backend-developer",
                "assignee": "Backend Developer",
                "tags": ["database", "performance", "optimization"],
                "createdAt": "2024-01-14T11:30:00Z",
                "updatedAt": "2024-01-16T15:45:00Z",
                "estimatedTime": 6,
                "actualTime": 7.2,
                "dependencies": []
            },
            {
                "id": "4",
                "title": "Set up CI/CD pipeline",
                "description": "Configure automated testing, building, and deployment pipeline using GitHub Actions.",
                "status": "review",
                "priority": "high",
                "agent": "devops-engineer",
                "assignee": "DevOps Engineer",
                "tags": ["devops", "automation", "deployment"],
                "createdAt": "2024-01-13T14:00:00Z",
                "updatedAt": "2024-01-16T13:20:00Z",
                "dueDate": "2024-01-19T09:00:00Z",
                "estimatedTime": 12,
                "dependencies": ["1"]
            },
            {
                "id": "5",
                "title": "Write unit tests for API endpoints",
                "description": "Create comprehensive unit tests for all authentication and user management API endpoints.",
                "status": "todo",
                "priority": "low",
                "agent": "test-engineer",
                "assignee": "Test Engineer",
                "tags": ["testing", "api", "quality"],
                "createdAt": "2024-01-16T10:45:00Z",
                "updatedAt": "2024-01-16T10:45:00Z",
                "dueDate": "2024-01-20T17:00:00Z",
                "estimatedTime": 5,
                "dependencies": ["1"]
            },
            {
                "id": "6",
                "title": "Code review for payment integration",
                "description": "Review payment processing code for security vulnerabilities and best practices compliance.",
                "status": "done",
                "priority": "high",
                "agent": "code-reviewer",
                "assignee": "Code Reviewer",
                "tags": ["security", "payment", "review"],
                "createdAt": "2024-01-15T16:20:00Z",
                "updatedAt": "2024-01-16T11:40:00Z",
                "estimatedTime": 3,
                "actualTime": 2.8,
                "dependencies": []
            },
            {
                "id": "7",
                "title": "Analyze user engagement metrics",
                "description": "Perform statistical analysis on user engagement data and create predictive models.",
                "status": "in_progress",
                "priority": "medium",
                "agent": "data-scientist",
                "assignee": "Data Scientist",
                "tags": ["analytics", "machine-learning", "insights"],
                "createdAt": "2024-01-16T07:30:00Z",
                "updatedAt": "2024-01-16T14:15:00Z",
                "dueDate": "2024-01-22T17:00:00Z",
                "estimatedTime": 16,
                "dependencies": []
            },
            {
                "id": "8",
                "title": "Update deployment documentation",
                "description": "Update all deployment guides and create troubleshooting documentation.",
                "status": "done",
                "priority": "low",
                "agent": "devops-engineer",
                "assignee": "DevOps Engineer",
                "tags": ["documentation", "deployment"],
                "createdAt": "2024-01-15T13:15:00Z",
                "updatedAt": "2024-01-16T12:20:00Z",
                "estimatedTime": 2,
                "actualTime": 1.5,
                "dependencies": []
            },
            {
                "id": "9",
                "title": "Implement real-time notifications",
                "description": "Build WebSocket-based notification system for real-time updates across the dashboard.",
                "status": "todo",
                "priority": "medium",
                "agent": "frontend-developer",
                "assignee": "Frontend Developer",
                "tags": ["websocket", "real-time", "notifications"],
                "createdAt": "2024-01-16T15:30:00Z",
                "updatedAt": "2024-01-16T15:30:00Z",
                "dueDate": "2024-01-25T17:00:00Z",
                "estimatedTime": 10,
                "dependencies": ["2"]
            },
            {
                "id": "10",
                "title": "Performance monitoring setup",
                "description": "Set up application performance monitoring with alerting and dashboards.",
                "status": "todo",
                "priority": "high",
                "agent": "devops-engineer",
                "assignee": "DevOps Engineer",
                "tags": ["monitoring", "performance", "alerting"],
                "createdAt": "2024-01-16T16:00:00Z",
                "updatedAt": "2024-01-16T16:00:00Z",
                "dueDate": "2024-01-21T17:00:00Z",
                "estimatedTime": 8,
                "dependencies": ["4"]
            }
        ]
    }

# Application startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting SubForge Dashboard Backend...")
    try:
        # Initialize SubForge integration
        await subforge_integration.start_monitoring()
        logger.info("SubForge integration started successfully")
    except Exception as e:
        logger.error(f"Failed to start SubForge integration: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down SubForge Dashboard Backend...")
    try:
        # Stop SubForge integration
        await subforge_integration.stop_monitoring()
        logger.info("SubForge integration stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping SubForge integration: {e}")

# SubForge-related Socket.IO events
@sio.event
async def subforge_workflow_subscribe(sid, data):
    """Subscribe to specific workflow updates"""
    workflow_id = data.get('workflow_id')
    if workflow_id:
        sio.enter_room(sid, f"workflow_{workflow_id}")
        logger.info(f"Client {sid} subscribed to workflow: {workflow_id}")
        await sio.emit('subforge_workflow_subscribed', {'workflow_id': workflow_id}, to=sid)

@sio.event
async def subforge_workflow_unsubscribe(sid, data):
    """Unsubscribe from workflow updates"""
    workflow_id = data.get('workflow_id')
    if workflow_id:
        sio.leave_room(sid, f"workflow_{workflow_id}")
        logger.info(f"Client {sid} unsubscribed from workflow: {workflow_id}")
        await sio.emit('subforge_workflow_unsubscribed', {'workflow_id': workflow_id}, to=sid)

@sio.event
async def subforge_scan_request(sid, data):
    """Request SubForge workflows scan"""
    logger.info(f"Scan request from {sid}: {data}")
    try:
        # Trigger scan
        discovered = await subforge_integration.scan_workflows()
        await sio.emit('subforge_scan_complete', {
            'discovered_count': len(discovered),
            'workflows': discovered
        }, to=sid)
    except Exception as e:
        logger.error(f"Error in scan request: {e}")
        await sio.emit('subforge_scan_error', {'error': str(e)}, to=sid)

# Export the socket app for uvicorn
app = socket_app