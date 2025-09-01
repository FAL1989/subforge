"""
Pydantic schemas for Workflow model
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class WorkflowBase(BaseModel):
    """Base workflow schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_type: Optional[str] = Field(None, max_length=100)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowCreate(WorkflowBase):
    """Schema for creating a new workflow"""
    status: str = Field(default="active", regex="^(active|inactive|paused|completed|failed|cancelled)$")
    project_id: Optional[str] = Field(None, max_length=255)
    project_name: Optional[str] = Field(None, max_length=255)
    estimated_duration_hours: Optional[float] = Field(None, gt=0)
    assigned_agents: List[Dict[str, str]] = Field(default_factory=list)
    is_template: bool = Field(default=False)
    requires_approval: bool = Field(default=False)
    scheduled_at: Optional[datetime] = None
    
    @validator("tags")
    def validate_tags(cls, v):
        """Validate that tags is a list of strings"""
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
        return v
    
    @validator("assigned_agents")
    def validate_assigned_agents(cls, v):
        """Validate assigned agents format"""
        if not isinstance(v, list):
            raise ValueError("Assigned agents must be a list")
        for agent in v:
            if not isinstance(agent, dict):
                raise ValueError("Each assigned agent must be a dictionary")
            if "id" not in agent:
                raise ValueError("Each assigned agent must have an 'id' field")
        return v


class WorkflowUpdate(BaseModel):
    """Schema for updating an existing workflow"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, regex="^(active|inactive|paused|completed|failed|cancelled)$")
    workflow_type: Optional[str] = Field(None, max_length=100)
    project_id: Optional[str] = Field(None, max_length=255)
    project_name: Optional[str] = Field(None, max_length=255)
    configuration: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    estimated_duration_hours: Optional[float] = Field(None, gt=0)
    actual_duration_hours: Optional[float] = Field(None, gt=0)
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    total_tasks: Optional[int] = Field(None, ge=0)
    completed_tasks: Optional[int] = Field(None, ge=0)
    failed_tasks: Optional[int] = Field(None, ge=0)
    success_rate: Optional[float] = Field(None, ge=0.0, le=100.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    efficiency_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    assigned_agents: Optional[List[Dict[str, str]]] = None
    agent_utilization: Optional[Dict[str, Any]] = None
    is_paused: Optional[bool] = None
    is_template: Optional[bool] = None
    requires_approval: Optional[bool] = None
    scheduled_at: Optional[datetime] = None
    
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
    
    @validator("completed_tasks")
    def validate_completed_tasks(cls, v, values):
        """Validate completed tasks doesn't exceed total"""
        if v is not None and "total_tasks" in values and values["total_tasks"] is not None:
            if v > values["total_tasks"]:
                raise ValueError("Completed tasks cannot exceed total tasks")
        return v


class WorkflowProject(BaseModel):
    """Schema for workflow project information"""
    id: Optional[str] = None
    name: Optional[str] = None


class WorkflowProgress(BaseModel):
    """Schema for workflow progress information"""
    percentage: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0


class WorkflowTimeTracking(BaseModel):
    """Schema for workflow time tracking"""
    estimated_duration_hours: Optional[float] = None
    actual_duration_hours: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowQualityMetrics(BaseModel):
    """Schema for workflow quality metrics"""
    success_rate: float = 0.0
    quality_score: Optional[float] = None
    efficiency_score: Optional[float] = None


class WorkflowAgents(BaseModel):
    """Schema for workflow agent information"""
    assigned: List[Dict[str, str]] = Field(default_factory=list)
    utilization: Dict[str, Any] = Field(default_factory=dict)


class WorkflowFlags(BaseModel):
    """Schema for workflow status flags"""
    is_paused: bool = False
    is_template: bool = False
    requires_approval: bool = False


class WorkflowResponse(WorkflowBase):
    """Schema for workflow response"""
    id: UUID
    status: str
    project: WorkflowProject
    progress: WorkflowProgress
    time_tracking: WorkflowTimeTracking
    quality_metrics: WorkflowQualityMetrics
    agents: WorkflowAgents
    flags: WorkflowFlags
    created_at: datetime
    updated_at: datetime
    scheduled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }


class WorkflowStatusUpdate(BaseModel):
    """Schema for updating workflow status"""
    status: str = Field(..., regex="^(active|inactive|paused|completed|failed|cancelled)$")
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)


class WorkflowProgressUpdate(BaseModel):
    """Schema for updating workflow progress"""
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    total_tasks: Optional[int] = Field(None, ge=0)
    completed_tasks: Optional[int] = Field(None, ge=0)
    failed_tasks: Optional[int] = Field(None, ge=0)
    
    @validator("completed_tasks")
    def validate_completed_tasks(cls, v, values):
        """Validate completed tasks doesn't exceed total"""
        if v is not None and "total_tasks" in values and values["total_tasks"] is not None:
            if v > values["total_tasks"]:
                raise ValueError("Completed tasks cannot exceed total tasks")
        return v


class WorkflowAgentAssignment(BaseModel):
    """Schema for workflow agent assignment"""
    agent_id: str = Field(..., min_length=1)
    agent_name: Optional[str] = None


class WorkflowTemplate(BaseModel):
    """Schema for workflow template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_type: str = Field(..., max_length=100)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    default_agents: List[Dict[str, str]] = Field(default_factory=list)
    estimated_duration_hours: Optional[float] = Field(None, gt=0)
    tags: List[str] = Field(default_factory=list)


class WorkflowExecution(BaseModel):
    """Schema for workflow execution request"""
    workflow_id: UUID
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    assigned_agents: Optional[List[Dict[str, str]]] = None