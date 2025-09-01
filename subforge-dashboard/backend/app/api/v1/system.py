"""
API endpoints for system monitoring and metrics
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from ...database.session import get_db
from ...models.system_metrics import SystemMetrics
from ...models.agent import Agent
from ...models.task import Task
from ...models.workflow import Workflow
from ...schemas.system_metrics import (
    SystemMetricsResponse,
    SystemMetricsCreate,
    SystemStatusSummary,
    SystemHealthCheck,
    MetricsTimeRange
)
from ...websocket.manager import websocket_manager
from ...core.config import settings

router = APIRouter()


@router.get("/health", response_model=SystemHealthCheck)
async def health_check():
    """
    System health check endpoint
    """
    return SystemHealthCheck(
        status="healthy",
        checks={
            "database": True,
            "websocket": True,
            "file_watcher": settings.ENABLE_FILE_WATCHER
        },
        version=settings.APP_VERSION
    )


@router.get("/status", response_model=SystemStatusSummary)
async def get_system_status(db: AsyncSession = Depends(get_db)):
    """
    Get comprehensive system status
    """
    # Get agents summary
    agents_result = await db.execute(select(Agent))
    agents = agents_result.scalars().all()
    
    agents_summary = {
        "total_agents": len(agents),
        "active_agents": len([a for a in agents if a.status == "active"]),
        "idle_agents": len([a for a in agents if a.status == "idle"]),
        "offline_agents": len([a for a in agents if a.status == "offline"])
    }
    
    # Get tasks summary
    tasks_result = await db.execute(select(Task))
    tasks = tasks_result.scalars().all()
    
    tasks_summary = {
        "total_tasks": len(tasks),
        "pending_tasks": len([t for t in tasks if t.status == "pending"]),
        "in_progress_tasks": len([t for t in tasks if t.status == "in_progress"]),
        "completed_tasks": len([t for t in tasks if t.status == "completed"]),
        "failed_tasks": len([t for t in tasks if t.status == "failed"])
    }
    
    # Get workflows summary
    workflows_result = await db.execute(select(Workflow))
    workflows = workflows_result.scalars().all()
    
    workflows_summary = {
        "total_workflows": len(workflows),
        "active_workflows": len([w for w in workflows if w.status == "active"]),
        "completed_workflows": len([w for w in workflows if w.status == "completed"]),
        "paused_workflows": len([w for w in workflows if w.status == "paused"])
    }
    
    return SystemStatusSummary(
        agents=agents_summary,
        tasks=tasks_summary,
        workflows=workflows_summary,
        connected_clients=websocket_manager.get_connection_count()
    )


@router.get("/metrics/current", response_model=SystemMetricsResponse)
async def get_current_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get current system metrics
    """
    # Get latest metrics record
    result = await db.execute(
        select(SystemMetrics).order_by(desc(SystemMetrics.recorded_at)).limit(1)
    )
    metrics = result.scalar_one_or_none()
    
    if not metrics:
        # Create initial metrics if none exist
        agents_result = await db.execute(select(Agent))
        agents = agents_result.scalars().all()
        
        tasks_result = await db.execute(select(Task))
        tasks = tasks_result.scalars().all()
        
        workflows_result = await db.execute(select(Workflow))
        workflows = workflows_result.scalars().all()
        
        metrics = SystemMetrics.create_snapshot(agents, tasks, workflows)
        db.add(metrics)
        await db.commit()
        await db.refresh(metrics)
    
    return SystemMetricsResponse.from_orm(metrics)


@router.get("/metrics/history", response_model=List[SystemMetricsResponse])
async def get_metrics_history(
    time_range: MetricsTimeRange = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical metrics data
    """
    query = select(SystemMetrics).order_by(desc(SystemMetrics.recorded_at))
    
    # Apply time range filter if provided
    if time_range:
        query = query.where(
            SystemMetrics.recorded_at >= time_range.start_date,
            SystemMetrics.recorded_at <= time_range.end_date
        )
    
    # Apply limit
    query = query.limit(limit)
    
    result = await db.execute(query)
    metrics_list = result.scalars().all()
    
    return [SystemMetricsResponse.from_orm(metrics) for metrics in metrics_list]


@router.post("/metrics", response_model=SystemMetricsResponse)
async def create_metrics_snapshot(
    metrics_data: SystemMetricsCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new metrics snapshot
    """
    # Get current system data
    agents_result = await db.execute(select(Agent))
    agents = agents_result.scalars().all()
    
    tasks_result = await db.execute(select(Task))
    tasks = tasks_result.scalars().all()
    
    workflows_result = await db.execute(select(Workflow))
    workflows = workflows_result.scalars().all()
    
    # Create metrics snapshot
    metrics = SystemMetrics.create_snapshot(agents, tasks, workflows)
    
    # Override with provided data
    if metrics_data.system_load_percentage is not None:
        metrics.system_load_percentage = metrics_data.system_load_percentage
    if metrics_data.memory_usage_percentage is not None:
        metrics.memory_usage_percentage = metrics_data.memory_usage_percentage
    if metrics_data.cpu_usage_percentage is not None:
        metrics.cpu_usage_percentage = metrics_data.cpu_usage_percentage
    if metrics_data.disk_usage_percentage is not None:
        metrics.disk_usage_percentage = metrics_data.disk_usage_percentage
    if metrics_data.websocket_connections is not None:
        metrics.websocket_connections = metrics_data.websocket_connections
    if metrics_data.api_requests_per_minute is not None:
        metrics.api_requests_per_minute = metrics_data.api_requests_per_minute
    if metrics_data.error_rate_percentage is not None:
        metrics.error_rate_percentage = metrics_data.error_rate_percentage
    if metrics_data.detailed_metrics:
        metrics.detailed_metrics.update(metrics_data.detailed_metrics)
    
    # Calculate derived metrics
    metrics.calculate_derived_metrics()
    
    db.add(metrics)
    await db.commit()
    await db.refresh(metrics)
    
    # Broadcast metrics update
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "system_metrics_updated",
            "data": metrics.to_dict()
        }
    )
    
    return SystemMetricsResponse.from_orm(metrics)


@router.get("/metrics/agents")
async def get_agent_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated agent metrics
    """
    result = await db.execute(select(Agent))
    agents = result.scalars().all()
    
    if not agents:
        return {
            "total_agents": 0,
            "metrics": {}
        }
    
    metrics = {
        "total_agents": len(agents),
        "by_status": {},
        "by_type": {},
        "performance": {
            "avg_success_rate": sum(a.success_rate for a in agents) / len(agents),
            "avg_response_time": sum(a.avg_response_time for a in agents) / len(agents),
            "avg_uptime": sum(a.uptime_percentage for a in agents) / len(agents),
            "total_tasks_completed": sum(a.tasks_completed for a in agents),
            "total_tasks_failed": sum(a.tasks_failed for a in agents)
        }
    }
    
    # Group by status
    for agent in agents:
        status = agent.status
        if status not in metrics["by_status"]:
            metrics["by_status"][status] = 0
        metrics["by_status"][status] += 1
    
    # Group by type
    for agent in agents:
        agent_type = agent.agent_type
        if agent_type not in metrics["by_type"]:
            metrics["by_type"][agent_type] = 0
        metrics["by_type"][agent_type] += 1
    
    return metrics


@router.get("/metrics/tasks")
async def get_task_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated task metrics
    """
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "total_tasks": 0,
            "metrics": {}
        }
    
    completed_tasks = [t for t in tasks if t.status == "completed"]
    
    metrics = {
        "total_tasks": len(tasks),
        "by_status": {},
        "by_priority": {},
        "by_type": {},
        "performance": {
            "completion_rate": len(completed_tasks) / len(tasks) * 100,
            "avg_progress": sum(t.progress_percentage for t in tasks) / len(tasks),
            "avg_duration": sum(t.actual_duration_minutes or 0 for t in completed_tasks) / len(completed_tasks) if completed_tasks else 0,
            "blocked_count": len([t for t in tasks if t.is_blocked]),
            "urgent_count": len([t for t in tasks if t.is_urgent])
        }
    }
    
    # Group by status
    for task in tasks:
        status = task.status
        if status not in metrics["by_status"]:
            metrics["by_status"][status] = 0
        metrics["by_status"][status] += 1
    
    # Group by priority
    for task in tasks:
        priority = task.priority
        if priority not in metrics["by_priority"]:
            metrics["by_priority"][priority] = 0
        metrics["by_priority"][priority] += 1
    
    # Group by type
    for task in tasks:
        task_type = task.task_type or "unspecified"
        if task_type not in metrics["by_type"]:
            metrics["by_type"][task_type] = 0
        metrics["by_type"][task_type] += 1
    
    return metrics


@router.get("/metrics/workflows")
async def get_workflow_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated workflow metrics
    """
    result = await db.execute(select(Workflow))
    workflows = result.scalars().all()
    
    if not workflows:
        return {
            "total_workflows": 0,
            "metrics": {}
        }
    
    completed_workflows = [w for w in workflows if w.status == "completed"]
    
    metrics = {
        "total_workflows": len(workflows),
        "by_status": {},
        "by_type": {},
        "performance": {
            "completion_rate": len(completed_workflows) / len(workflows) * 100,
            "avg_progress": sum(w.progress_percentage for w in workflows) / len(workflows),
            "avg_success_rate": sum(w.success_rate for w in workflows) / len(workflows),
            "avg_duration": sum(w.actual_duration_hours or 0 for w in completed_workflows) / len(completed_workflows) if completed_workflows else 0,
            "template_count": len([w for w in workflows if w.is_template])
        }
    }
    
    # Group by status
    for workflow in workflows:
        status = workflow.status
        if status not in metrics["by_status"]:
            metrics["by_status"][status] = 0
        metrics["by_status"][status] += 1
    
    # Group by type
    for workflow in workflows:
        workflow_type = workflow.workflow_type or "unspecified"
        if workflow_type not in metrics["by_type"]:
            metrics["by_type"][workflow_type] = 0
        metrics["by_type"][workflow_type] += 1
    
    return metrics


@router.post("/maintenance/cleanup")
async def cleanup_old_metrics(
    days_to_keep: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Clean up old metrics records
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    # Delete old metrics records
    result = await db.execute(
        select(func.count()).select_from(SystemMetrics).where(
            SystemMetrics.recorded_at < cutoff_date
        )
    )
    count_before = result.scalar()
    
    await db.execute(
        SystemMetrics.__table__.delete().where(
            SystemMetrics.recorded_at < cutoff_date
        )
    )
    await db.commit()
    
    result = await db.execute(select(func.count()).select_from(SystemMetrics))
    count_after = result.scalar()
    
    deleted_count = count_before - count_after
    
    return {
        "message": f"Cleanup completed",
        "deleted_records": deleted_count,
        "remaining_records": count_after,
        "cutoff_date": cutoff_date.isoformat()
    }