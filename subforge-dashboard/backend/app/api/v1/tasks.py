"""
API endpoints for task management
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.session import get_db
from ...models.agent import Agent
from ...models.task import Task
from ...schemas.task import (
    TaskAssignment,
    TaskBulkUpdate,
    TaskCreate,
    TaskDependency,
    TaskProgressUpdate,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from ...websocket.manager import websocket_manager

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = Query(
        None, regex="^(pending|in_progress|completed|failed|blocked|cancelled)$"
    ),
    priority: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    assigned_agent_id: Optional[UUID] = None,
    workflow_id: Optional[UUID] = None,
    task_type: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    is_urgent: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all tasks with optional filtering
    """
    query = select(Task)

    # Apply filters
    conditions = []
    if status:
        conditions.append(Task.status == status)
    if priority:
        conditions.append(Task.priority == priority)
    if assigned_agent_id:
        conditions.append(Task.assigned_agent_id == assigned_agent_id)
    if workflow_id:
        conditions.append(Task.workflow_id == workflow_id)
    if task_type:
        conditions.append(Task.task_type == task_type)
    if is_blocked is not None:
        conditions.append(Task.is_blocked == is_blocked)
    if is_urgent is not None:
        conditions.append(Task.is_urgent == is_urgent)

    if conditions:
        query = query.where(and_(*conditions))

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [TaskResponse.from_orm(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific task by ID
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return TaskResponse.from_orm(task)


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new task
    """
    # Validate assigned agent exists if provided
    if task_data.assigned_agent_id:
        agent_result = await db.execute(
            select(Agent).where(Agent.id == task_data.assigned_agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned agent not found",
            )
        task_data.assigned_agent_name = agent.name

    # Create new task
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        assigned_agent_id=task_data.assigned_agent_id,
        assigned_agent_name=task_data.assigned_agent_name,
        workflow_id=task_data.workflow_id,
        task_type=task_data.task_type,
        tags=task_data.tags,
        metadata=task_data.metadata,
        estimated_duration_minutes=task_data.estimated_duration_minutes,
        dependencies=task_data.dependencies,
        complexity_score=task_data.complexity_score,
        effort_points=task_data.effort_points,
        due_date=task_data.due_date,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {"type": "task_created", "data": task.to_dict()},
    )

    return TaskResponse.from_orm(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing task
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Validate assigned agent if being updated
    if task_update.assigned_agent_id:
        agent_result = await db.execute(
            select(Agent).where(Agent.id == task_update.assigned_agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned agent not found",
            )
        task_update.assigned_agent_name = agent.name

    # Update fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {"type": "task_updated", "data": task.to_dict()},
    )

    return TaskResponse.from_orm(task)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: UUID,
    status_update: TaskStatusUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Update task status
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    old_status = task.status
    task.status = status_update.status

    # Handle status transitions
    if status_update.status == "in_progress" and old_status == "pending":
        task.start_task()
    elif status_update.status == "completed":
        task.complete_task(status_update.quality_score)

    if status_update.progress_percentage is not None:
        task.update_progress(status_update.progress_percentage)

    await db.commit()
    await db.refresh(task)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "task_status_updated",
            "data": {
                "task_id": str(task.id),
                "old_status": old_status,
                "new_status": task.status,
                "progress": task.progress_percentage,
            },
        },
    )

    return TaskResponse.from_orm(task)


@router.patch("/{task_id}/progress", response_model=TaskResponse)
async def update_task_progress(
    task_id: UUID,
    progress_update: TaskProgressUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Update task progress
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    task.update_progress(progress_update.progress_percentage)

    if progress_update.subtasks_completed is not None:
        task.subtasks_completed = progress_update.subtasks_completed
    if progress_update.subtasks_total is not None:
        task.subtasks_total = progress_update.subtasks_total

    # Auto-complete task if progress is 100%
    if progress_update.progress_percentage >= 100.0 and task.status != "completed":
        task.complete_task()

    await db.commit()
    await db.refresh(task)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "task_progress_updated",
            "data": {
                "task_id": str(task.id),
                "progress": task.progress_percentage,
                "subtasks": {
                    "completed": task.subtasks_completed,
                    "total": task.subtasks_total,
                },
            },
        },
    )

    return TaskResponse.from_orm(task)


@router.patch("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: UUID,
    assignment: TaskAssignment,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Assign task to an agent
    """
    # Get task
    task_result = await db.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Get agent
    agent_result = await db.execute(
        select(Agent).where(Agent.id == assignment.assigned_agent_id)
    )
    agent = agent_result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Agent not found"
        )

    # Update assignment
    task.assigned_agent_id = assignment.assigned_agent_id
    task.assigned_agent_name = assignment.assigned_agent_name or agent.name
    task.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "task_assigned",
            "data": {
                "task_id": str(task.id),
                "agent_id": str(agent.id),
                "agent_name": agent.name,
            },
        },
    )

    return TaskResponse.from_orm(task)


@router.post("/{task_id}/dependencies", response_model=TaskResponse)
async def add_task_dependency(
    task_id: UUID, dependency: TaskDependency, db: AsyncSession = Depends(get_db)
):
    """
    Add a dependency to a task
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Verify dependency task exists
    dep_result = await db.execute(
        select(Task).where(Task.id == dependency.dependency_id)
    )
    if not dep_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Dependency task not found"
        )

    task.add_dependency(dependency.dependency_id)
    await db.commit()
    await db.refresh(task)

    return TaskResponse.from_orm(task)


@router.delete("/{task_id}/dependencies/{dependency_id}", response_model=TaskResponse)
async def remove_task_dependency(
    task_id: UUID, dependency_id: str, db: AsyncSession = Depends(get_db)
):
    """
    Remove a dependency from a task
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    task.remove_dependency(dependency_id)
    await db.commit()
    await db.refresh(task)

    return TaskResponse.from_orm(task)


@router.patch("/bulk", response_model=List[TaskResponse])
async def bulk_update_tasks(
    bulk_update: TaskBulkUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk update multiple tasks
    """
    # Get all tasks to update
    result = await db.execute(select(Task).where(Task.id.in_(bulk_update.task_ids)))
    tasks = result.scalars().all()

    if len(tasks) != len(bulk_update.task_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Some tasks not found"
        )

    # Apply updates to all tasks
    update_data = bulk_update.updates.dict(exclude_unset=True)
    updated_tasks = []

    for task in tasks:
        for field, value in update_data.items():
            setattr(task, field, value)
        task.updated_at = datetime.utcnow()
        updated_tasks.append(task)

    await db.commit()

    # Refresh all tasks
    for task in updated_tasks:
        await db.refresh(task)

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "tasks_bulk_updated",
            "data": {
                "task_ids": [str(task.id) for task in updated_tasks],
                "updates": update_data,
            },
        },
    )

    return [TaskResponse.from_orm(task) for task in updated_tasks]


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """
    Delete a task
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    await db.execute(delete(Task).where(Task.id == task_id))
    await db.commit()

    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {"type": "task_deleted", "data": {"task_id": str(task_id)}},
    )

    return {"message": "Task deleted successfully"}


@router.get("/stats/summary")
async def get_task_stats(db: AsyncSession = Depends(get_db)):
    """
    Get task statistics summary
    """
    result = await db.execute(select(Task))
    tasks = result.scalars().all()

    stats = {
        "total_tasks": len(tasks),
        "pending_tasks": len([t for t in tasks if t.status == "pending"]),
        "in_progress_tasks": len([t for t in tasks if t.status == "in_progress"]),
        "completed_tasks": len([t for t in tasks if t.status == "completed"]),
        "failed_tasks": len([t for t in tasks if t.status == "failed"]),
        "blocked_tasks": len([t for t in tasks if t.is_blocked]),
        "urgent_tasks": len([t for t in tasks if t.is_urgent]),
        "avg_progress": (
            sum(t.progress_percentage for t in tasks) / len(tasks) if tasks else 0
        ),
        "completion_rate": (
            len([t for t in tasks if t.status == "completed"]) / len(tasks) * 100
            if tasks
            else 0
        ),
    }

    return stats