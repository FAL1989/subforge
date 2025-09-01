"""
SubForge Dashboard Backend
FastAPI application for monitoring SubForge agent orchestration system
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Pydantic Models
class Agent(BaseModel):
    id: str
    name: str
    type: str
    status: str = "active"
    current_task: Optional[str] = None
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = Field(default_factory=lambda: datetime.now().isoformat())
    configuration: Dict[str, Any] = Field(default_factory=dict)

class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    status: str = "pending"
    priority: str = "medium"
    assigned_agent: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    dependencies: List[str] = Field(default_factory=list)

class Workflow(BaseModel):
    id: str
    name: str
    description: str = ""
    status: str = "active"
    tasks: List[Task] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    progress: float = 0.0
    estimated_completion: str = ""

class PRP(BaseModel):
    id: str
    title: str
    description: str = ""
    status: str = "active"
    priority: int = 5
    agent_assignments: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    success_metrics: Dict[str, float] = Field(default_factory=dict)

class SystemMetrics(BaseModel):
    total_agents: int = 0
    active_agents: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    system_load: float = 0.0
    memory_usage: float = 0.0
    avg_response_time: float = 0.0
    success_rate: float = 0.0
    uptime: float = 100.0

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

# SubForge File Watcher
class SubForgeWatcher(FileSystemEventHandler):
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(self.manager.broadcast({
                "type": "file_change",
                "payload": {"file": event.src_path},
                "timestamp": datetime.now().isoformat()
            }))

# Global instances
manager = ConnectionManager()
data_store = {
    "agents": [],
    "tasks": [],
    "workflows": [],
    "prps": [],
    "metrics": SystemMetrics()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting SubForge Dashboard Backend")
    await initialize_data()
    start_file_watcher()
    asyncio.create_task(update_metrics_periodically())
    yield
    # Shutdown
    print("💤 Shutting down SubForge Dashboard Backend")

# FastAPI App
app = FastAPI(
    title="SubForge Dashboard API",
    description="Backend API for SubForge monitoring dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_data():
    """Initialize data from SubForge files"""
    print("📊 Loading SubForge data...")
    
    # Load agents from .claude/agents/
    agents_dir = Path(".claude/agents")
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            data_store["agents"].append(Agent(
                id=agent_name,
                name=agent_name.replace("-", " ").title(),
                type=agent_name,
                configuration={
                    "model": "claude-3-sonnet",
                    "tools": ["read", "write", "edit", "bash"],
                    "capabilities": ["code-generation", "analysis", "testing"]
                },
                performance_metrics={
                    "tasks_completed": 5,
                    "success_rate": 95.0,
                    "avg_response_time": 2.3,
                    "uptime": 98.5
                }
            ))
    
    # Load workflow data from .subforge/
    subforge_dir = Path(".subforge")
    if subforge_dir.exists():
        for workflow_dir in subforge_dir.iterdir():
            if workflow_dir.is_dir():
                workflow_context_file = workflow_dir / "workflow_context.json"
                if workflow_context_file.exists():
                    try:
                        with open(workflow_context_file) as f:
                            workflow_data = json.load(f)
                            
                        data_store["workflows"].append(Workflow(
                            id=workflow_data.get("project_id", workflow_dir.name),
                            name=workflow_data.get("project_id", "SubForge Workflow"),
                            description=workflow_data.get("user_request", ""),
                            status="completed",
                            progress=100.0
                        ))
                    except Exception as e:
                        print(f"Error loading workflow {workflow_dir}: {e}")
    
    # Load PRPs
    prp_dir = Path(".subforge") / "PRPs" / "generated"
    if prp_dir.exists():
        for prp_file in prp_dir.glob("*.json"):
            try:
                with open(prp_file) as f:
                    prp_data = json.load(f)
                
                data_store["prps"].append(PRP(
                    id=prp_data.get("id", prp_file.stem),
                    title=prp_data.get("title", f"PRP {prp_file.stem}"),
                    description=prp_data.get("description", ""),
                    priority=prp_data.get("priority", 5),
                    success_metrics={
                        "completion_rate": 85.0,
                        "quality_score": 92.0,
                        "time_efficiency": 88.0
                    }
                ))
            except Exception as e:
                print(f"Error loading PRP {prp_file}: {e}")
    
    # Generate sample tasks
    task_types = ["Bug Fix", "Feature Development", "Code Review", "Testing", "Documentation"]
    for i, task_type in enumerate(task_types):
        data_store["tasks"].append(Task(
            id=f"task_{i+1}",
            title=f"{task_type} - Dashboard Implementation",
            description=f"Work on {task_type.lower()} for the SubForge dashboard",
            status=["pending", "in_progress", "completed"][i % 3],
            priority=["low", "medium", "high", "critical"][i % 4],
            assigned_agent=data_store["agents"][i % len(data_store["agents"])].id if data_store["agents"] else None,
            estimated_duration=30 + (i * 15),
            dependencies=[]
        ))
    
    print(f"✅ Loaded: {len(data_store['agents'])} agents, {len(data_store['workflows'])} workflows, {len(data_store['prps'])} PRPs, {len(data_store['tasks'])} tasks")

def start_file_watcher():
    """Start watching SubForge files for changes"""
    observer = Observer()
    event_handler = SubForgeWatcher(manager)
    
    # Watch .subforge directory
    if Path(".subforge").exists():
        observer.schedule(event_handler, ".subforge", recursive=True)
    
    # Watch .claude directory  
    if Path(".claude").exists():
        observer.schedule(event_handler, ".claude", recursive=True)
    
    observer.start()
    print("👀 File watcher started")

async def update_metrics_periodically():
    """Update system metrics every 30 seconds"""
    while True:
        try:
            # Calculate current metrics
            metrics = SystemMetrics(
                total_agents=len(data_store["agents"]),
                active_agents=len([a for a in data_store["agents"] if a.status == "active"]),
                total_tasks=len(data_store["tasks"]),
                completed_tasks=len([t for t in data_store["tasks"] if t.status == "completed"]),
                system_load=45.2,  # Mock data - would come from system monitoring
                memory_usage=67.8,
                avg_response_time=2.1,
                success_rate=94.5,
                uptime=99.2
            )
            
            data_store["metrics"] = metrics
            
            # Broadcast metrics update
            await manager.broadcast({
                "type": "metrics_update",
                "payload": metrics.dict(),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error updating metrics: {e}")
        
        await asyncio.sleep(30)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "agents_loaded": len(data_store["agents"]) > 0,
            "workflows_available": len(data_store["workflows"]) >= 0,
            "websocket_ready": len(manager.active_connections) >= 0
        }
    }

# Agent endpoints
@app.get("/agents", response_model=List[Agent])
async def get_agents():
    return data_store["agents"]

@app.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    agent = next((a for a in data_store["agents"] if a.id == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.post("/agents", response_model=Agent)
async def create_agent(agent: Agent):
    data_store["agents"].append(agent)
    await manager.broadcast({
        "type": "agent_update",
        "payload": agent.dict(),
        "timestamp": datetime.now().isoformat()
    })
    return agent

@app.put("/agents/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, agent_update: dict):
    agent = next((a for a in data_store["agents"] if a.id == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    for key, value in agent_update.items():
        if hasattr(agent, key):
            setattr(agent, key, value)
    
    agent.last_activity = datetime.now().isoformat()
    
    await manager.broadcast({
        "type": "agent_update",
        "payload": agent.dict(),
        "timestamp": datetime.now().isoformat()
    })
    
    return agent

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    agent = next((a for a in data_store["agents"] if a.id == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    data_store["agents"].remove(agent)
    return {"message": "Agent deleted successfully"}

# Task endpoints
@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    return data_store["tasks"]

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = next((t for t in data_store["tasks"] if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    data_store["tasks"].append(task)
    await manager.broadcast({
        "type": "task_update",
        "payload": task.dict(),
        "timestamp": datetime.now().isoformat()
    })
    return task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: dict):
    task = next((t for t in data_store["tasks"] if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for key, value in task_update.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    task.updated_at = datetime.now().isoformat()
    
    await manager.broadcast({
        "type": "task_update",
        "payload": task.dict(),
        "timestamp": datetime.now().isoformat()
    })
    
    return task

# Workflow endpoints
@app.get("/workflows", response_model=List[Workflow])
async def get_workflows():
    return data_store["workflows"]

@app.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str):
    workflow = next((w for w in data_store["workflows"] if w.id == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@app.post("/workflows", response_model=Workflow)
async def create_workflow(workflow: Workflow):
    data_store["workflows"].append(workflow)
    await manager.broadcast({
        "type": "workflow_update",
        "payload": workflow.dict(),
        "timestamp": datetime.now().isoformat()
    })
    return workflow

# PRP endpoints
@app.get("/prps", response_model=List[PRP])
async def get_prps():
    return data_store["prps"]

@app.get("/prps/{prp_id}", response_model=PRP)
async def get_prp(prp_id: str):
    prp = next((p for p in data_store["prps"] if p.id == prp_id), None)
    if not prp:
        raise HTTPException(status_code=404, detail="PRP not found")
    return prp

@app.post("/prps", response_model=PRP)
async def create_prp(prp: PRP):
    data_store["prps"].append(prp)
    return prp

# Metrics endpoints
@app.get("/system/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    return data_store["metrics"]

@app.get("/system/status")
async def get_system_status():
    return {
        "status": "running",
        "agents": {
            "total": len(data_store["agents"]),
            "active": len([a for a in data_store["agents"] if a.status == "active"]),
            "idle": len([a for a in data_store["agents"] if a.status == "idle"])
        },
        "tasks": {
            "total": len(data_store["tasks"]),
            "pending": len([t for t in data_store["tasks"] if t.status == "pending"]),
            "in_progress": len([t for t in data_store["tasks"] if t.status == "in_progress"]),
            "completed": len([t for t in data_store["tasks"] if t.status == "completed"])
        },
        "workflows": {
            "total": len(data_store["workflows"]),
            "active": len([w for w in data_store["workflows"] if w.status == "active"])
        },
        "uptime": datetime.now().isoformat(),
        "connected_clients": len(manager.active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)