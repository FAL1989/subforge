"""
Background task processing service with Celery integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from celery import Celery
from pydantic import BaseModel

from ..core.config import settings
from .redis_service import redis_service

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class BackgroundTask(BaseModel):
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = {}


class TaskResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 100.0
    metadata: Dict[str, Any] = {}


# Create Celery app
celery_app = Celery(
    "subforge-dashboard",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.services.background_tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_routes={
        "app.services.background_tasks.*": {"queue": "default"},
        "app.services.background_tasks.high_priority_*": {"queue": "high_priority"},
        "app.services.background_tasks.low_priority_*": {"queue": "low_priority"},
    },
    task_default_queue="default",
    task_create_missing_queues=True,
    result_expires=3600,  # 1 hour
)


class BackgroundTaskService:
    """Service for managing background tasks"""

    def __init__(self):
        self.task_registry: Dict[str, BackgroundTask] = {}
        self.task_callbacks: Dict[str, List[Callable]] = {}

    async def submit_task(
        self,
        task_name: str,
        task_args: tuple = (),
        task_kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        eta: Optional[datetime] = None,
        countdown: Optional[int] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Submit a background task"""
        task_id = str(uuid4())
        task_kwargs = task_kwargs or {}
        metadata = metadata or {}

        # Create task record
        task = BackgroundTask(
            id=task_id,
            name=task_name,
            priority=priority,
            max_retries=max_retries,
            created_at=datetime.utcnow(),
            metadata=metadata,
        )

        # Store task info
        self.task_registry[task_id] = task
        await redis_service.hset("background_tasks", task_id, task.dict())

        try:
            # Submit to Celery with custom task ID
            celery_result = celery_app.send_task(
                task_name,
                args=task_args,
                kwargs=task_kwargs,
                task_id=task_id,
                priority=priority.value,
                eta=eta,
                countdown=countdown,
                retry=max_retries > 0,
                retry_policy={
                    "max_retries": max_retries,
                    "interval_start": 0,
                    "interval_step": 0.2,
                    "interval_max": 0.2,
                },
            )

            logger.info(f"Background task submitted: {task_name} ({task_id})")
            return task_id

        except Exception as e:
            # Update task status on failure
            task.status = TaskStatus.FAILURE
            task.error = str(e)
            await self._update_task(task)
            logger.error(f"Failed to submit background task {task_name}: {e}")
            raise

    async def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task information"""
        # Try memory first
        if task_id in self.task_registry:
            return self.task_registry[task_id]

        # Try Redis
        task_data = await redis_service.hget("background_tasks", task_id)
        if task_data:
            task = BackgroundTask(**task_data)
            self.task_registry[task_id] = task
            return task

        # Try Celery result backend
        try:
            celery_result = celery_app.AsyncResult(task_id)
            if celery_result.state:
                # Convert Celery state to our format
                status_map = {
                    "PENDING": TaskStatus.PENDING,
                    "STARTED": TaskStatus.STARTED,
                    "SUCCESS": TaskStatus.SUCCESS,
                    "FAILURE": TaskStatus.FAILURE,
                    "RETRY": TaskStatus.RETRY,
                    "REVOKED": TaskStatus.REVOKED,
                }

                task = BackgroundTask(
                    id=task_id,
                    name="unknown",
                    status=status_map.get(celery_result.state, TaskStatus.PENDING),
                    created_at=datetime.utcnow(),
                )

                if celery_result.info:
                    if isinstance(celery_result.info, dict):
                        task.progress = celery_result.info.get("progress", 0.0)
                        task.metadata = celery_result.info.get("metadata", {})
                        if celery_result.state == "SUCCESS":
                            task.result = celery_result.info
                        elif celery_result.state == "FAILURE":
                            task.error = str(celery_result.info)

                return task

        except Exception as e:
            logger.warning(f"Error getting task from Celery: {e}")

        return None

    async def get_all_tasks(
        self, status: Optional[TaskStatus] = None, limit: int = 100
    ) -> List[BackgroundTask]:
        """Get all tasks with optional filtering"""
        tasks = []

        # Get from Redis
        task_data = await redis_service.hgetall("background_tasks")
        for task_id, data in task_data.items():
            try:
                task = BackgroundTask(**data)
                if not status or task.status == status:
                    tasks.append(task)
                    self.task_registry[task_id] = task
            except Exception as e:
                logger.warning(f"Error deserializing task {task_id}: {e}")

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        try:
            celery_app.control.revoke(task_id, terminate=True)

            # Update task status
            task = await self.get_task(task_id)
            if task:
                task.status = TaskStatus.REVOKED
                task.completed_at = datetime.utcnow()
                await self._update_task(task)

            logger.info(f"Task cancelled: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False

    async def retry_task(self, task_id: str) -> bool:
        """Retry a failed task"""
        try:
            task = await self.get_task(task_id)
            if not task:
                return False

            if task.retry_count >= task.max_retries:
                logger.warning(f"Task {task_id} has exceeded max retries")
                return False

            # Increment retry count
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            task.error = None
            await self._update_task(task)

            # Retry in Celery
            celery_app.control.retry(task_id)

            logger.info(f"Task retried: {task_id} (attempt {task.retry_count})")
            return True

        except Exception as e:
            logger.error(f"Error retrying task {task_id}: {e}")
            return False

    async def update_task_progress(
        self,
        task_id: str,
        progress: float,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Update task progress"""
        task = await self.get_task(task_id)
        if not task:
            return

        task.progress = max(0.0, min(100.0, progress))
        if metadata:
            task.metadata.update(metadata)

        await self._update_task(task)

        # Notify subscribers
        await self._notify_task_update(task_id, task)

    async def complete_task(self, task_id: str, result: TaskResult):
        """Mark task as completed"""
        task = await self.get_task(task_id)
        if not task:
            return

        task.status = TaskStatus.SUCCESS if result.success else TaskStatus.FAILURE
        task.progress = result.progress
        task.result = result.data
        task.error = result.error
        task.completed_at = datetime.utcnow()

        if result.metadata:
            task.metadata.update(result.metadata)

        await self._update_task(task)
        await self._notify_task_update(task_id, task)

    async def cleanup_old_tasks(self, older_than_days: int = 7):
        """Clean up old completed tasks"""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        tasks_to_remove = []

        all_tasks = await self.get_all_tasks()
        for task in all_tasks:
            if (
                task.status
                in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]
                and task.completed_at
                and task.completed_at < cutoff_date
            ):
                tasks_to_remove.append(task.id)

        # Remove from Redis
        if tasks_to_remove:
            await redis_service.hdel("background_tasks", *tasks_to_remove)

            # Remove from memory
            for task_id in tasks_to_remove:
                self.task_registry.pop(task_id, None)

            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

    async def get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics"""
        all_tasks = await self.get_all_tasks()

        stats = {
            "total": len(all_tasks),
            "by_status": {},
            "by_priority": {},
            "average_duration": 0.0,
            "success_rate": 0.0,
        }

        durations = []
        success_count = 0

        for task in all_tasks:
            # Count by status
            status_key = task.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1

            # Count by priority
            priority_key = task.priority.name.lower()
            stats["by_priority"][priority_key] = (
                stats["by_priority"].get(priority_key, 0) + 1
            )

            # Calculate duration for completed tasks
            if task.completed_at:
                start_time = task.started_at or task.created_at
                duration = (task.completed_at - start_time).total_seconds()
                durations.append(duration)

                if task.status == TaskStatus.SUCCESS:
                    success_count += 1

        # Calculate averages
        if durations:
            stats["average_duration"] = sum(durations) / len(durations)

        if all_tasks:
            stats["success_rate"] = (success_count / len(all_tasks)) * 100

        return stats

    async def subscribe_to_task_updates(self, task_id: str, callback: Callable):
        """Subscribe to task updates"""
        if task_id not in self.task_callbacks:
            self.task_callbacks[task_id] = []
        self.task_callbacks[task_id].append(callback)

    async def unsubscribe_from_task_updates(self, task_id: str, callback: Callable):
        """Unsubscribe from task updates"""
        if task_id in self.task_callbacks:
            self.task_callbacks[task_id] = [
                cb for cb in self.task_callbacks[task_id] if cb != callback
            ]
            if not self.task_callbacks[task_id]:
                del self.task_callbacks[task_id]

    async def _update_task(self, task: BackgroundTask):
        """Update task in storage"""
        self.task_registry[task.id] = task
        await redis_service.hset("background_tasks", task.id, task.dict())

    async def _notify_task_update(self, task_id: str, task: BackgroundTask):
        """Notify subscribers about task updates"""
        if task_id in self.task_callbacks:
            for callback in self.task_callbacks[task_id]:
                try:
                    await callback(task)
                except Exception as e:
                    logger.error(f"Error in task update callback: {e}")


# Global background task service
background_task_service = BackgroundTaskService()


# Celery task decorators and utilities
def subforge_task(name: str = None, priority: TaskPriority = TaskPriority.NORMAL):
    """Decorator for creating SubForge background tasks"""

    def decorator(func):
        task_name = name or f"app.services.background_tasks.{func.__name__}"

        @celery_app.task(bind=True, name=task_name, priority=priority.value)
        def wrapper(self, *args, **kwargs):
            task_id = self.request.id

            # Update task status to started
            task = asyncio.run(background_task_service.get_task(task_id))
            if task:
                task.status = TaskStatus.STARTED
                task.started_at = datetime.utcnow()
                asyncio.run(background_task_service._update_task(task))

            try:
                # Execute the actual function
                result = func(self, *args, **kwargs)

                # Handle different result types
                if isinstance(result, TaskResult):
                    asyncio.run(background_task_service.complete_task(task_id, result))
                    return result.dict()
                else:
                    # Assume success if no TaskResult returned
                    task_result = TaskResult(success=True, data=result)
                    asyncio.run(
                        background_task_service.complete_task(task_id, task_result)
                    )
                    return task_result.dict()

            except Exception as exc:
                # Handle task failure
                error_result = TaskResult(success=False, error=str(exc), progress=0.0)
                asyncio.run(
                    background_task_service.complete_task(task_id, error_result)
                )
                raise

        return wrapper

    return decorator


# Example background tasks
@subforge_task("process_agent_configuration")
def process_agent_configuration(self, agent_id: str, config_data: dict):
    """Process agent configuration updates"""
    try:
        # Simulate processing
        import time

        total_steps = 5

        for step in range(total_steps):
            time.sleep(1)  # Simulate work
            progress = ((step + 1) / total_steps) * 100

            # Update progress
            asyncio.run(
                background_task_service.update_task_progress(
                    self.request.id,
                    progress,
                    f"Processing step {step + 1}/{total_steps}",
                )
            )

        return TaskResult(
            success=True,
            data={"agent_id": agent_id, "processed": True},
            metadata={"processing_time": total_steps},
        )

    except Exception as e:
        return TaskResult(success=False, error=str(e))


@subforge_task("analyze_system_metrics")
def analyze_system_metrics(self, time_range: str = "24h"):
    """Analyze system metrics and generate insights"""
    try:
        # Simulate metric analysis
        import time

        time.sleep(3)

        # Generate mock insights
        insights = {
            "total_requests": 1250,
            "average_response_time": 125.5,
            "error_rate": 2.1,
            "peak_usage_hour": "14:00",
            "recommendations": [
                "Consider scaling up during peak hours",
                "Monitor error rate trends",
            ],
        }

        return TaskResult(
            success=True, data=insights, metadata={"analysis_time_range": time_range}
        )

    except Exception as e:
        return TaskResult(success=False, error=str(e))


@subforge_task("backup_agent_data", priority=TaskPriority.LOW)
def backup_agent_data(self, backup_type: str = "incremental"):
    """Backup agent configuration and data"""
    try:
        import time

        time.sleep(5)  # Simulate backup process

        return TaskResult(
            success=True,
            data={"backup_type": backup_type, "backup_size": "15.2 MB"},
            metadata={"backup_location": "/backups/agents/"},
        )

    except Exception as e:
        return TaskResult(success=False, error=str(e))