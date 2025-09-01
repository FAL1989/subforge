"""
Background Tasks API v2 for task management and monitoring
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel

from ...services.api_enhancement import (
    api_enhancement_service, 
    get_current_user, 
    require_auth
)
from ...services.background_tasks import (
    background_task_service,
    BackgroundTask,
    TaskStatus,
    TaskPriority,
    TaskResult
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class TaskCreateRequest(BaseModel):
    task_name: str
    task_args: tuple = ()
    task_kwargs: dict = {}
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    eta: Optional[datetime] = None
    countdown: Optional[int] = None
    metadata: Dict[str, Any] = {}


class TaskResponse(BaseModel):
    id: str
    name: str
    status: TaskStatus
    priority: TaskPriority
    progress: float
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int
    max_retries: int
    metadata: Dict[str, Any] = {}


class TaskStatistics(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    average_duration: float
    success_rate: float


class BulkTaskOperation(BaseModel):
    task_ids: List[str]
    operation: str  # "cancel", "retry"


# API Endpoints

@router.get(
    "/",
    response_model=List[TaskResponse],
    summary="List background tasks with filtering and pagination"
)
@api_enhancement_service.cache_response(ttl=10)
@api_enhancement_service.rate_limit(requests_per_minute=100)
async def list_background_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of tasks to return"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    task_name: Optional[str] = Query(None, description="Filter by task name"),
    created_after: Optional[str] = Query(None, description="Filter tasks created after datetime"),
    created_before: Optional[str] = Query(None, description="Filter tasks created before datetime"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """List background tasks with advanced filtering and pagination"""
    try:
        # Get all tasks
        all_tasks = await background_task_service.get_all_tasks(status=status)
        
        # Apply additional filters
        filtered_tasks = []
        for task in all_tasks:
            # Filter by priority
            if priority and task.priority != priority:
                continue
            
            # Filter by task name
            if task_name and task_name.lower() not in task.name.lower():
                continue
            
            # Filter by created dates
            if created_after:
                try:
                    after_dt = datetime.fromisoformat(created_after.replace("Z", "+00:00"))
                    if task.created_at < after_dt:
                        continue
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid created_after datetime format"
                    )
            
            if created_before:
                try:
                    before_dt = datetime.fromisoformat(created_before.replace("Z", "+00:00"))
                    if task.created_at > before_dt:
                        continue
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid created_before datetime format"
                    )
            
            filtered_tasks.append(task)
        
        # Sort tasks
        reverse_sort = sort_order == "desc"
        if sort_by == "name":
            filtered_tasks.sort(key=lambda t: t.name.lower(), reverse=reverse_sort)
        elif sort_by == "status":
            filtered_tasks.sort(key=lambda t: t.status.value, reverse=reverse_sort)
        elif sort_by == "priority":
            filtered_tasks.sort(key=lambda t: t.priority.value, reverse=reverse_sort)
        elif sort_by == "progress":
            filtered_tasks.sort(key=lambda t: t.progress, reverse=reverse_sort)
        else:  # default to created_at
            filtered_tasks.sort(key=lambda t: t.created_at, reverse=reverse_sort)
        
        # Apply pagination
        total_count = len(filtered_tasks)
        paginated_tasks = filtered_tasks[skip:skip + limit]
        
        # Convert to response format
        response_tasks = []
        for task in paginated_tasks:
            response_tasks.append(TaskResponse(
                id=task.id,
                name=task.name,
                status=task.status,
                priority=task.priority,
                progress=task.progress,
                result=task.result,
                error=task.error,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                retry_count=task.retry_count,
                max_retries=task.max_retries,
                metadata=task.metadata
            ))
        
        return response_tasks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing background tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve background tasks"
        )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get background task details"
)
@api_enhancement_service.cache_response(ttl=5)
@api_enhancement_service.rate_limit(requests_per_minute=200)
async def get_background_task(task_id: str):
    """Get detailed information about a specific background task"""
    try:
        task = await background_task_service.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            status=task.status,
            priority=task.priority,
            progress=task.progress,
            result=task.result,
            error=task.error,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            metadata=task.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting background task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve background task"
        )


@router.post(
    "/",
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new background task"
)
@api_enhancement_service.rate_limit(requests_per_minute=50, per_user=True)
@require_auth
async def create_background_task(
    request: TaskCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new background task"""
    try:
        # Add user information to metadata
        metadata = request.metadata.copy()
        metadata.update({
            "created_by": current_user.get("id"),
            "created_by_username": current_user.get("username")
        })
        
        # Submit task
        task_id = await background_task_service.submit_task(
            task_name=request.task_name,
            task_args=request.task_args,
            task_kwargs=request.task_kwargs,
            priority=request.priority,
            max_retries=request.max_retries,
            eta=request.eta,
            countdown=request.countdown,
            metadata=metadata
        )
        
        return {
            "task_id": task_id,
            "message": "Background task created successfully",
            "status": "submitted"
        }
        
    except Exception as e:
        logger.error(f"Error creating background task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create background task"
        )


@router.post(
    "/{task_id}/cancel",
    summary="Cancel a background task"
)
@api_enhancement_service.rate_limit(requests_per_minute=30, per_user=True)
@require_auth
async def cancel_background_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a running or pending background task"""
    try:
        success = await background_task_service.cancel_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel task. Task may not exist or cannot be cancelled."
            )
        
        return {
            "message": f"Task {task_id} cancelled successfully",
            "cancelled_by": current_user.get("id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling background task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel background task"
        )


@router.post(
    "/{task_id}/retry",
    summary="Retry a failed background task"
)
@api_enhancement_service.rate_limit(requests_per_minute=30, per_user=True)
@require_auth
async def retry_background_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retry a failed background task"""
    try:
        success = await background_task_service.retry_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retry task. Task may not exist, not be in a retryable state, or exceed max retries."
            )
        
        return {
            "message": f"Task {task_id} retry initiated successfully",
            "retried_by": current_user.get("id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying background task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry background task"
        )


@router.post(
    "/bulk-operation",
    summary="Perform bulk operations on multiple tasks"
)
@api_enhancement_service.rate_limit(requests_per_minute=10, per_user=True)
@require_auth
async def bulk_task_operation(
    request: BulkTaskOperation,
    current_user: dict = Depends(get_current_user)
):
    """Perform bulk operations on multiple background tasks"""
    try:
        results = []
        
        for task_id in request.task_ids:
            try:
                if request.operation == "cancel":
                    success = await background_task_service.cancel_task(task_id)
                    action = "cancelled"
                elif request.operation == "retry":
                    success = await background_task_service.retry_task(task_id)
                    action = "retried"
                else:
                    results.append({
                        "task_id": task_id,
                        "success": False,
                        "error": f"Unknown operation: {request.operation}"
                    })
                    continue
                
                results.append({
                    "task_id": task_id,
                    "success": success,
                    "action": action if success else "failed"
                })
                
            except Exception as e:
                logger.error(f"Error in bulk operation for task {task_id}: {e}")
                results.append({
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "operation": request.operation,
            "total_tasks": len(request.task_ids),
            "successful": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results,
            "performed_by": current_user.get("id")
        }
        
    except Exception as e:
        logger.error(f"Error in bulk task operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk operation"
        )


@router.get(
    "/statistics",
    response_model=TaskStatistics,
    summary="Get background tasks statistics"
)
@api_enhancement_service.cache_response(ttl=60)
@api_enhancement_service.rate_limit(requests_per_minute=60)
async def get_task_statistics():
    """Get comprehensive statistics about background tasks"""
    try:
        stats = await background_task_service.get_task_statistics()
        
        return TaskStatistics(
            total=stats["total"],
            by_status=stats["by_status"],
            by_priority=stats["by_priority"],
            average_duration=stats["average_duration"],
            success_rate=stats["success_rate"]
        )
        
    except Exception as e:
        logger.error(f"Error getting task statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task statistics"
        )


@router.get(
    "/queue-status",
    summary="Get task queue status information"
)
@api_enhancement_service.cache_response(ttl=30)
@api_enhancement_service.rate_limit(requests_per_minute=60)
async def get_queue_status():
    """Get information about task queues and workers"""
    try:
        # Get task counts by status
        all_tasks = await background_task_service.get_all_tasks()
        
        queue_status = {
            "queues": {
                "default": {
                    "pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
                    "active": len([t for t in all_tasks if t.status == TaskStatus.STARTED]),
                    "failed": len([t for t in all_tasks if t.status == TaskStatus.FAILURE])
                }
            },
            "workers": {
                "active": 1,  # Mock data - would come from Celery inspect
                "available": 1,
                "busy": 0
            },
            "processing_rate": {
                "tasks_per_minute": 0,  # Would be calculated from metrics
                "average_task_duration": 0.0
            },
            "health": {
                "status": "healthy",
                "last_heartbeat": datetime.utcnow().isoformat()
            }
        }
        
        return queue_status
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue status"
        )


@router.post(
    "/cleanup",
    summary="Clean up old completed tasks"
)
@api_enhancement_service.rate_limit(requests_per_minute=5, per_user=True)
@require_auth
async def cleanup_old_tasks(
    older_than_days: int = Query(7, ge=1, le=365, description="Delete tasks older than N days"),
    current_user: dict = Depends(get_current_user)
):
    """Clean up old completed background tasks"""
    try:
        await background_task_service.cleanup_old_tasks(older_than_days)
        
        return {
            "message": f"Cleanup completed for tasks older than {older_than_days} days",
            "cleaned_by": current_user.get("id")
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up old tasks"
        )


# Predefined task endpoints for common operations
@router.post(
    "/predefined/analyze-metrics",
    summary="Start system metrics analysis task"
)
@api_enhancement_service.rate_limit(requests_per_minute=10, per_user=True)
@require_auth
async def start_analyze_metrics_task(
    time_range: str = Query("24h", regex="^(1h|24h|7d)$"),
    current_user: dict = Depends(get_current_user)
):
    """Start a predefined task to analyze system metrics"""
    try:
        task_id = await background_task_service.submit_task(
            "analyze_system_metrics",
            task_args=(time_range,),
            priority=TaskPriority.NORMAL,
            metadata={
                "created_by": current_user.get("id"),
                "task_type": "predefined",
                "analysis_range": time_range
            }
        )
        
        return {
            "task_id": task_id,
            "message": f"System metrics analysis task started for {time_range}",
            "estimated_duration": "3-5 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error starting metrics analysis task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start metrics analysis task"
        )


@router.post(
    "/predefined/backup-data",
    summary="Start data backup task"
)
@api_enhancement_service.rate_limit(requests_per_minute=5, per_user=True)
@require_auth
async def start_backup_task(
    backup_type: str = Query("incremental", regex="^(full|incremental)$"),
    current_user: dict = Depends(get_current_user)
):
    """Start a predefined task to backup agent data"""
    try:
        task_id = await background_task_service.submit_task(
            "backup_agent_data",
            task_args=(backup_type,),
            priority=TaskPriority.LOW,
            metadata={
                "created_by": current_user.get("id"),
                "task_type": "predefined",
                "backup_type": backup_type
            }
        )
        
        return {
            "task_id": task_id,
            "message": f"Data backup task started ({backup_type})",
            "estimated_duration": "5-10 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error starting backup task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start backup task"
        )