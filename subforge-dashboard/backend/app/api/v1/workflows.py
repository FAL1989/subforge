"""
API endpoints for workflow management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from typing import List, Optional
from uuid import UUID

from ...database.session import get_db
from ...models.workflow import Workflow
from ...models.task import Task
from ...models.agent import Agent
from ...schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowStatusUpdate,
    WorkflowProgressUpdate,
    WorkflowAgentAssignment,
    WorkflowTemplate,
    WorkflowExecution
)
from ...websocket.manager import websocket_manager

router = APIRouter()


@router.get("/", response_model=List[WorkflowResponse])
async def get_workflows(
    status: Optional[str] = Query(None, regex="^(active|inactive|paused|completed|failed|cancelled)$"),
    workflow_type: Optional[str] = None,
    project_id: Optional[str] = None,
    is_template: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all workflows with optional filtering
    """
    query = select(Workflow)
    
    # Apply filters
    conditions = []
    if status:
        conditions.append(Workflow.status == status)
    if workflow_type:
        conditions.append(Workflow.workflow_type == workflow_type)
    if project_id:
        conditions.append(Workflow.project_id == project_id)
    if is_template is not None:
        conditions.append(Workflow.is_template == is_template)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Workflow.created_at.desc())
    
    result = await db.execute(query)
    workflows = result.scalars().all()
    
    return [WorkflowResponse.from_orm(workflow) for workflow in workflows]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific workflow by ID
    """
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    return WorkflowResponse.from_orm(workflow)


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow_data: WorkflowCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new workflow
    """
    # Validate assigned agents exist
    for agent_data in workflow_data.assigned_agents:
        if "id" in agent_data:
            agent_result = await db.execute(
                select(Agent).where(Agent.id == agent_data["id"])
            )
            if not agent_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Agent {agent_data['id']} not found"
                )
    
    # Create new workflow
    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        status=workflow_data.status,
        workflow_type=workflow_data.workflow_type,
        project_id=workflow_data.project_id,
        project_name=workflow_data.project_name,
        configuration=workflow_data.configuration,
        parameters=workflow_data.parameters,
        tags=workflow_data.tags,
        metadata=workflow_data.metadata,
        estimated_duration_hours=workflow_data.estimated_duration_hours,
        assigned_agents=workflow_data.assigned_agents,
        is_template=workflow_data.is_template,
        requires_approval=workflow_data.requires_approval,
        scheduled_at=workflow_data.scheduled_at
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "workflow_created",
            "data": workflow.to_dict()
        }
    )
    
    return WorkflowResponse.from_orm(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow_update: WorkflowUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing workflow
    """
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Update fields
    update_data = workflow_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    await db.commit()
    await db.refresh(workflow)
    
    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "workflow_updated",
            "data": workflow.to_dict()
        }
    )
    
    return WorkflowResponse.from_orm(workflow)


@router.patch("/{workflow_id}/status", response_model=WorkflowResponse)
async def update_workflow_status(
    workflow_id: UUID,
    status_update: WorkflowStatusUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Update workflow status
    """
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    old_status = workflow.status
    workflow.status = status_update.status
    
    # Handle status transitions
    if status_update.status == "running" and old_status in ["active", "paused"]:
        workflow.start_workflow()
    elif status_update.status == "paused":
        workflow.pause_workflow()
    elif status_update.status == "active" and old_status == "paused":
        workflow.resume_workflow()
    elif status_update.status == "completed":
        workflow.complete_workflow()
    
    if status_update.progress_percentage is not None:
        workflow.progress_percentage = status_update.progress_percentage
    
    await db.commit()
    await db.refresh(workflow)
    
    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "workflow_status_updated",
            "data": {
                "workflow_id": str(workflow.id),
                "old_status": old_status,
                "new_status": workflow.status,
                "progress": workflow.progress_percentage
            }
        }
    )
    
    return WorkflowResponse.from_orm(workflow)


@router.patch("/{workflow_id}/progress", response_model=WorkflowResponse)
async def update_workflow_progress(
    workflow_id: UUID,
    progress_update: WorkflowProgressUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Update workflow progress
    """
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    workflow.progress_percentage = progress_update.progress_percentage
    
    if progress_update.total_tasks is not None:
        workflow.total_tasks = progress_update.total_tasks
    if progress_update.completed_tasks is not None:
        workflow.completed_tasks = progress_update.completed_tasks
    if progress_update.failed_tasks is not None:
        workflow.failed_tasks = progress_update.failed_tasks
    
    # Recalculate derived metrics
    workflow.update_progress()
    
    # Auto-complete workflow if progress is 100%
    if progress_update.progress_percentage >= 100.0 and workflow.status != "completed":
        workflow.complete_workflow()
    
    await db.commit()
    await db.refresh(workflow)
    
    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "workflow_progress_updated",
            "data": {
                "workflow_id": str(workflow.id),
                "progress": workflow.progress_percentage,
                "tasks": {
                    "total": workflow.total_tasks,
                    "completed": workflow.completed_tasks,
                    "failed": workflow.failed_tasks
                }
            }
        }
    )
    
    return WorkflowResponse.from_orm(workflow)


@router.post("/{workflow_id}/agents", response_model=WorkflowResponse)
async def assign_agent_to_workflow(
    workflow_id: UUID,
    agent_assignment: WorkflowAgentAssignment,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Assign an agent to a workflow
    """
    # Get workflow
    workflow_result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = workflow_result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Get agent
    agent_result = await db.execute(
        select(Agent).where(Agent.id == agent_assignment.agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent not found"
        )
    
    # Add agent to workflow
    workflow.add_agent(
        agent_assignment.agent_id,
        agent_assignment.agent_name or agent.name
    )
    
    await db.commit()
    await db.refresh(workflow)
    
    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "workflow_agent_assigned",
            "data": {
                "workflow_id": str(workflow.id),
                "agent_id": agent_assignment.agent_id,
                "agent_name": agent.name
            }
        }
    )
    
    return WorkflowResponse.from_orm(workflow)


@router.delete("/{workflow_id}/agents/{agent_id}", response_model=WorkflowResponse)
async def remove_agent_from_workflow(
    workflow_id: UUID,
    agent_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an agent from a workflow
    """
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    workflow.remove_agent(agent_id)
    
    await db.commit()
    await db.refresh(workflow)
    
    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "workflow_agent_removed",
            "data": {
                "workflow_id": str(workflow.id),
                "agent_id": agent_id
            }
        }
    )
    
    return WorkflowResponse.from_orm(workflow)


@router.get("/{workflow_id}/tasks", response_model=List[dict])
async def get_workflow_tasks(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get all tasks associated with a workflow
    """
    result = await db.execute(
        select(Task).where(Task.workflow_id == workflow_id)
    )
    tasks = result.scalars().all()
    
    return [task.to_dict() for task in tasks]


@router.post("/templates", response_model=WorkflowResponse)
async def create_workflow_template(
    template_data: WorkflowTemplate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a workflow template
    """
    workflow = Workflow(
        name=template_data.name,
        description=template_data.description,
        workflow_type=template_data.workflow_type,
        configuration=template_data.configuration,
        parameters=template_data.parameters,
        assigned_agents=template_data.default_agents,
        estimated_duration_hours=template_data.estimated_duration_hours,
        tags=template_data.tags,
        is_template=True,
        status="inactive"
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse.from_orm(workflow)


@router.post("/{workflow_id}/execute", response_model=WorkflowResponse)
async def execute_workflow(
    workflow_id: UUID,
    execution_data: WorkflowExecution,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a workflow (start or schedule execution)
    """
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Update parameters if provided
    if execution_data.parameters:
        workflow.parameters.update(execution_data.parameters)
    
    # Update assigned agents if provided
    if execution_data.assigned_agents:
        workflow.assigned_agents = execution_data.assigned_agents
    
    # Set schedule or start immediately
    if execution_data.scheduled_at:
        workflow.scheduled_at = execution_data.scheduled_at
        workflow.status = "scheduled"
    else:
        workflow.start_workflow()
    
    await db.commit()
    await db.refresh(workflow)
    
    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "workflow_executed",
            "data": {
                "workflow_id": str(workflow.id),
                "status": workflow.status,
                "scheduled_at": workflow.scheduled_at.isoformat() if workflow.scheduled_at else None
            }
        }
    )
    
    return WorkflowResponse.from_orm(workflow)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a workflow
    """
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    await db.execute(delete(Workflow).where(Workflow.id == workflow_id))
    await db.commit()
    
    # Notify via WebSocket
    background_tasks.add_task(
        websocket_manager.broadcast_json,
        {
            "type": "workflow_deleted",
            "data": {"workflow_id": str(workflow_id)}
        }
    )
    
    return {"message": "Workflow deleted successfully"}


@router.get("/stats/summary")
async def get_workflow_stats(db: AsyncSession = Depends(get_db)):
    """
    Get workflow statistics summary
    """
    result = await db.execute(select(Workflow))
    workflows = result.scalars().all()
    
    stats = {
        "total_workflows": len(workflows),
        "active_workflows": len([w for w in workflows if w.status == "active"]),
        "paused_workflows": len([w for w in workflows if w.status == "paused"]),
        "completed_workflows": len([w for w in workflows if w.status == "completed"]),
        "failed_workflows": len([w for w in workflows if w.status == "failed"]),
        "template_workflows": len([w for w in workflows if w.is_template]),
        "avg_progress": sum(w.progress_percentage for w in workflows) / len(workflows) if workflows else 0,
        "avg_success_rate": sum(w.success_rate for w in workflows) / len(workflows) if workflows else 0
    }
    
    return stats