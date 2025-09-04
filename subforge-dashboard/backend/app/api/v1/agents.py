"""
API endpoints for agent management
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.session import get_db
from ...models.agent import Agent
from ...schemas.agent import (
    AgentCreate,
    AgentHeartbeat,
    AgentMetricsUpdate,
    AgentResponse,
    AgentStatusUpdate,
    AgentUpdate,
)
from ...websocket.manager import websocket_manager

router = APIRouter()


@router.get("/", response_model=List[AgentResponse])
async def get_agents(
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all agents with optional filtering
    """
    query = select(Agent)

    # Apply filters
    if status:
        query = query.where(Agent.status == status)
    if agent_type:
        query = query.where(Agent.agent_type == agent_type)
    if is_active is not None:
        query = query.where(Agent.is_active == is_active)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    agents = result.scalars().all()

    return [AgentResponse.from_orm(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific agent by ID
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    return AgentResponse.from_orm(agent)


@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new agent
    """
    # Check if agent with same name and type already exists
    existing_agent = await db.execute(
        select(Agent).where(
            Agent.name == agent_data.name, Agent.agent_type == agent_data.agent_type
        )
    )
    if existing_agent.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent with this name and type already exists",
        )

    # Create new agent
    agent = Agent(
        name=agent_data.name,
        agent_type=agent_data.agent_type,
        status=agent_data.status,
        description=agent_data.description,
        model=agent_data.model,
        tools=agent_data.tools,
        capabilities=agent_data.capabilities,
        configuration=agent_data.configuration,
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {"type": "agent_created", "data": agent.to_dict()},
    )

    return AgentResponse.from_orm(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_update: AgentUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing agent
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    # Update fields
    update_data = agent_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    agent.update_activity()

    await db.commit()
    await db.refresh(agent)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {"type": "agent_updated", "data": agent.to_dict()},
    )

    return AgentResponse.from_orm(agent)


@router.patch("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: UUID,
    status_update: AgentStatusUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Update agent status
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    agent.status = status_update.status
    if status_update.current_task_id:
        agent.current_task_id = status_update.current_task_id
    if status_update.current_task_title:
        agent.current_task_title = status_update.current_task_title

    agent.update_activity()

    await db.commit()
    await db.refresh(agent)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "agent_status_updated",
            "data": {
                "agent_id": str(agent.id),
                "status": agent.status,
                "current_task": {
                    "id": str(agent.current_task_id) if agent.current_task_id else None,
                    "title": agent.current_task_title,
                },
            },
        },
    )

    return AgentResponse.from_orm(agent)


@router.patch("/{agent_id}/metrics", response_model=AgentResponse)
async def update_agent_metrics(
    agent_id: UUID,
    metrics_update: AgentMetricsUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Update agent performance metrics
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    # Update metrics
    if metrics_update.tasks_completed is not None:
        agent.tasks_completed = metrics_update.tasks_completed
    if metrics_update.tasks_failed is not None:
        agent.tasks_failed = metrics_update.tasks_failed
    if metrics_update.avg_response_time is not None:
        agent.avg_response_time = metrics_update.avg_response_time
    if metrics_update.uptime_percentage is not None:
        agent.uptime_percentage = metrics_update.uptime_percentage

    # Recalculate success rate
    agent.calculate_success_rate()
    agent.update_activity()

    await db.commit()
    await db.refresh(agent)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "agent_metrics_updated",
            "data": {
                "agent_id": str(agent.id),
                "metrics": {
                    "tasks_completed": agent.tasks_completed,
                    "tasks_failed": agent.tasks_failed,
                    "success_rate": agent.success_rate,
                    "avg_response_time": agent.avg_response_time,
                    "uptime_percentage": agent.uptime_percentage,
                },
            },
        },
    )

    return AgentResponse.from_orm(agent)


@router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: UUID,
    heartbeat: AgentHeartbeat,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Process agent heartbeat
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    # Update heartbeat and status
    agent.update_heartbeat()
    agent.status = heartbeat.status
    agent.is_active = heartbeat.status != "offline"

    if heartbeat.current_task_id:
        agent.current_task_id = heartbeat.current_task_id

    # Update metrics if provided
    if heartbeat.metrics:
        for key, value in heartbeat.metrics.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

    await db.commit()

    return {"status": "heartbeat_received", "timestamp": heartbeat.timestamp}


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an agent
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    await db.execute(delete(Agent).where(Agent.id == agent_id))
    await db.commit()

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {"type": "agent_deleted", "data": {"agent_id": str(agent_id)}},
    )

    return {"message": "Agent deleted successfully"}


@router.get("/stats/summary")
async def get_agent_stats(db: AsyncSession = Depends(get_db)):
    """
    Get agent statistics summary
    """
    result = await db.execute(select(Agent))
    agents = result.scalars().all()

    stats = {
        "total_agents": len(agents),
        "active_agents": len([a for a in agents if a.status == "active"]),
        "idle_agents": len([a for a in agents if a.status == "idle"]),
        "busy_agents": len([a for a in agents if a.status == "busy"]),
        "offline_agents": len([a for a in agents if a.status == "offline"]),
        "avg_success_rate": (
            sum(a.success_rate for a in agents) / len(agents) if agents else 0
        ),
        "avg_response_time": (
            sum(a.avg_response_time for a in agents) / len(agents) if agents else 0
        ),
        "avg_uptime": (
            sum(a.uptime_percentage for a in agents) / len(agents) if agents else 100
        ),
    }

    return stats