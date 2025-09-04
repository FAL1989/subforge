"""
Pydantic models for SubForge integration
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class WorkflowStatus(str, Enum):
    """Workflow status enumeration"""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class PhaseStatus(str, Enum):
    """Phase status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EventType(str, Enum):
    """File system event types"""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class PhaseResult(BaseModel):
    """Model for SubForge phase result"""

    phase: str
    status: PhaseStatus
    duration: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    outputs: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class ProjectProfile(BaseModel):
    """Model for SubForge project profile"""

    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    architecture: Optional[str] = None
    complexity_score: Optional[float] = None
    team_size_estimate: Optional[int] = None
    file_count: Optional[int] = None
    lines_of_code: Optional[int] = None
    patterns: List[str] = Field(default_factory=list)
    dependencies: Dict[str, Any] = Field(default_factory=dict)


class AgentTemplate(BaseModel):
    """Model for agent template configuration"""

    name: str
    role: str
    specialization: str
    domain: str
    description: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    model: str = "claude-3-sonnet-20240229"
    priority: int = 1
    execution_instructions: Optional[str] = None
    context_requirements: List[str] = Field(default_factory=list)


class Task(BaseModel):
    """Model for SubForge task"""

    id: str
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: int = 1
    phase: Optional[str] = None
    assigned_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class AgentActivity(BaseModel):
    """Model for agent activity tracking"""

    agent_id: str
    agent_name: str
    activity_type: str
    description: Optional[str] = None
    timestamp: datetime
    duration: Optional[float] = None
    status: str = "active"
    task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class WorkflowContext(BaseModel):
    """Model for SubForge workflow context"""

    project_id: str
    user_request: str
    project_path: str
    communication_dir: str
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Phase results
    phase_results: Dict[str, PhaseResult] = Field(default_factory=dict)

    # Project analysis
    project_profile: Optional[ProjectProfile] = None

    # Agent configuration
    recommended_agents: List[AgentTemplate] = Field(default_factory=list)
    deployed_agents: List[AgentTemplate] = Field(default_factory=list)

    # Task management
    tasks: List[Task] = Field(default_factory=list)

    # Activity tracking
    agent_activities: List[AgentActivity] = Field(default_factory=list)

    # Metrics
    total_phases: int = 0
    completed_phases: int = 0
    failed_phases: int = 0
    progress_percentage: float = 0.0

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    @validator("phase_results", pre=True)
    def parse_phase_results(cls, v):
        """Parse phase results from dict to PhaseResult objects"""
        if isinstance(v, dict):
            parsed = {}
            for phase_name, result_data in v.items():
                if isinstance(result_data, dict):
                    # Ensure all required fields are present
                    result_data.setdefault("phase", phase_name)
                    result_data.setdefault("status", "pending")
                    parsed[phase_name] = PhaseResult(**result_data)
                else:
                    parsed[phase_name] = result_data
            return parsed
        return v

    def get_current_phase(self) -> Optional[str]:
        """Get the current active phase"""
        for phase_name, result in self.phase_results.items():
            if result.status == PhaseStatus.IN_PROGRESS:
                return phase_name
        return None

    def get_completed_phases(self) -> List[str]:
        """Get list of completed phases"""
        return [
            phase_name
            for phase_name, result in self.phase_results.items()
            if result.status == PhaseStatus.COMPLETED
        ]

    def get_failed_phases(self) -> List[str]:
        """Get list of failed phases"""
        return [
            phase_name
            for phase_name, result in self.phase_results.items()
            if result.status == PhaseStatus.FAILED
        ]

    def calculate_progress(self) -> float:
        """Calculate workflow progress percentage"""
        if not self.phase_results:
            return 0.0

        completed = len(self.get_completed_phases())
        total = len(self.phase_results)
        return (completed / total) * 100.0 if total > 0 else 0.0

    def update_metrics(self):
        """Update workflow metrics"""
        self.total_phases = len(self.phase_results)
        self.completed_phases = len(self.get_completed_phases())
        self.failed_phases = len(self.get_failed_phases())
        self.progress_percentage = self.calculate_progress()


class FileSystemEvent(BaseModel):
    """Model for file system events"""

    event_type: EventType
    file_path: str
    timestamp: datetime
    workflow_id: Optional[str] = None
    is_workflow_file: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class SubForgeIntegrationConfig(BaseModel):
    """Configuration for SubForge integration"""

    subforge_dir: str = ".subforge"
    watch_patterns: List[str] = Field(
        default_factory=lambda: ["*.json", "*.md", "*.py"]
    )
    scan_interval: int = 30  # seconds
    max_workflows: int = 100
    cleanup_after_days: int = 30
    enable_real_time_monitoring: bool = True
    websocket_broadcast: bool = True


class WorkflowSummary(BaseModel):
    """Summary model for workflow list responses"""

    project_id: str
    user_request: str
    status: WorkflowStatus
    progress_percentage: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    current_phase: Optional[str] = None
    total_phases: int = 0
    completed_phases: int = 0
    failed_phases: int = 0
    agent_count: int = 0

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class WorkflowMetrics(BaseModel):
    """Metrics model for workflow analytics"""

    total_workflows: int = 0
    active_workflows: int = 0
    completed_workflows: int = 0
    failed_workflows: int = 0
    average_completion_time: Optional[float] = None
    success_rate: float = 0.0
    most_common_phases: List[Dict[str, Any]] = Field(default_factory=list)
    agent_utilization: Dict[str, float] = Field(default_factory=dict)
    recent_activities: List[AgentActivity] = Field(default_factory=list)