"""
Pydantic schemas for Task model
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class TaskBase(BaseModel):
    """Base task schema with common fields"""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")
    task_type: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskCreate(TaskBase):
    """Schema for creating a new task"""

    status: str = Field(
        default="pending",
        regex="^(pending|in_progress|completed|failed|blocked|cancelled)$",
    )
    assigned_agent_id: Optional[UUID] = None
    assigned_agent_name: Optional[str] = Field(None, max_length=255)
    workflow_id: Optional[UUID] = None
    estimated_duration_minutes: Optional[int] = Field(None, gt=0)
    dependencies: List[str] = Field(default_factory=list)
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    effort_points: Optional[int] = Field(None, gt=0)
    due_date: Optional[datetime] = None

    @validator("tags")
    def validate_tags(cls, v):
        """Validate that tags is a list of strings"""
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
        return v

    @validator("dependencies")
    def validate_dependencies(cls, v):
        """Validate that dependencies is a list of strings"""
        if not isinstance(v, list):
            raise ValueError("Dependencies must be a list")
        for dep in v:
            if not isinstance(dep, str):
                raise ValueError("All dependencies must be strings")
        return v


class TaskUpdate(BaseModel):
    """Schema for updating an existing task"""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = Field(
        None, regex="^(pending|in_progress|completed|failed|blocked|cancelled)$"
    )
    priority: Optional[str] = Field(None, regex="^(low|medium|high|critical)$")
    assigned_agent_id: Optional[UUID] = None
    assigned_agent_name: Optional[str] = Field(None, max_length=255)
    workflow_id: Optional[UUID] = None
    task_type: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    estimated_duration_minutes: Optional[int] = Field(None, gt=0)
    actual_duration_minutes: Optional[int] = Field(None, gt=0)
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    effort_points: Optional[int] = Field(None, gt=0)
    is_blocked: Optional[bool] = None
    is_urgent: Optional[bool] = None
    requires_review: Optional[bool] = None
    due_date: Optional[datetime] = None

    @validator("tags")
    def validate_tags(cls, v):
        """Validate that tags is a list of strings"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Tags must be a list")
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError("All tags must be strings")
        return v


class TaskAssignedAgent(BaseModel):
    """Schema for task's assigned agent information"""

    id: Optional[UUID] = None
    name: Optional[str] = None


class TaskTimeTracking(BaseModel):
    """Schema for task time tracking"""

    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskProgress(BaseModel):
    """Schema for task progress information"""

    percentage: float = 0.0
    subtasks_completed: int = 0
    subtasks_total: int = 0


class TaskQualityMetrics(BaseModel):
    """Schema for task quality metrics"""

    quality_score: Optional[float] = None
    complexity_score: Optional[int] = None
    effort_points: Optional[int] = None


class TaskFlags(BaseModel):
    """Schema for task status flags"""

    is_blocked: bool = False
    is_urgent: bool = False
    requires_review: bool = False


class TaskResponse(TaskBase):
    """Schema for task response"""

    id: UUID
    status: str
    assigned_agent: TaskAssignedAgent
    workflow_id: Optional[UUID] = None
    time_tracking: TaskTimeTracking
    dependencies: List[str]
    dependents: List[str]
    progress: TaskProgress
    quality_metrics: TaskQualityMetrics
    flags: TaskFlags
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        }


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status"""

    status: str = Field(
        ..., regex="^(pending|in_progress|completed|failed|blocked|cancelled)$"
    )
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)


class TaskProgressUpdate(BaseModel):
    """Schema for updating task progress"""

    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    subtasks_completed: Optional[int] = Field(None, ge=0)
    subtasks_total: Optional[int] = Field(None, ge=0)

    @validator("subtasks_completed")
    def validate_subtasks_completed(cls, v, values):
        """Validate subtasks completed doesn't exceed total"""
        if (
            v is not None
            and "subtasks_total" in values
            and values["subtasks_total"] is not None
        ):
            if v > values["subtasks_total"]:
                raise ValueError("Subtasks completed cannot exceed total")
        return v


class TaskAssignment(BaseModel):
    """Schema for task assignment"""

    assigned_agent_id: UUID
    assigned_agent_name: Optional[str] = None


class TaskDependency(BaseModel):
    """Schema for task dependency operations"""

    dependency_id: str = Field(..., min_length=1)


class TaskBulkUpdate(BaseModel):
    """Schema for bulk task updates"""

    task_ids: List[UUID] = Field(..., min_items=1)
    updates: TaskUpdate

    @validator("task_ids")
    def validate_task_ids(cls, v):
        """Validate that task_ids is not empty"""
        if not v:
            raise ValueError("At least one task ID must be provided")
        return v