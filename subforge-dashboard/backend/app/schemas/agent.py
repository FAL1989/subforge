"""
Pydantic schemas for Agent model
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class AgentBase(BaseModel):
    """Base agent schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    model: str = Field(default="claude-3-sonnet", max_length=100)
    tools: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class AgentCreate(AgentBase):
    """Schema for creating a new agent"""
    status: str = Field(default="idle", regex="^(active|idle|busy|offline|error)$")
    
    @validator("tools")
    def validate_tools(cls, v):
        """Validate that tools is a list of strings"""
        if not isinstance(v, list):
            raise ValueError("Tools must be a list")
        for tool in v:
            if not isinstance(tool, str):
                raise ValueError("All tools must be strings")
        return v
    
    @validator("capabilities")
    def validate_capabilities(cls, v):
        """Validate that capabilities is a list of strings"""
        if not isinstance(v, list):
            raise ValueError("Capabilities must be a list")
        for capability in v:
            if not isinstance(capability, str):
                raise ValueError("All capabilities must be strings")
        return v


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    agent_type: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, regex="^(active|idle|busy|offline|error)$")
    description: Optional[str] = None
    model: Optional[str] = Field(None, max_length=100)
    tools: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    current_task_id: Optional[UUID] = None
    current_task_title: Optional[str] = Field(None, max_length=500)
    
    @validator("tools")
    def validate_tools(cls, v):
        """Validate that tools is a list of strings"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Tools must be a list")
            for tool in v:
                if not isinstance(tool, str):
                    raise ValueError("All tools must be strings")
        return v
    
    @validator("capabilities")
    def validate_capabilities(cls, v):
        """Validate that capabilities is a list of strings"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Capabilities must be a list")
            for capability in v:
                if not isinstance(capability, str):
                    raise ValueError("All capabilities must be strings")
        return v


class AgentTaskInfo(BaseModel):
    """Schema for agent's current task information"""
    id: Optional[UUID] = None
    title: Optional[str] = None


class AgentConfiguration(BaseModel):
    """Schema for agent configuration"""
    model: str
    tools: List[str]
    capabilities: List[str]


class AgentPerformanceMetrics(BaseModel):
    """Schema for agent performance metrics"""
    tasks_completed: float = 0.0
    tasks_failed: float = 0.0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    uptime_percentage: float = 100.0


class AgentResponse(AgentBase):
    """Schema for agent response"""
    id: UUID
    status: str
    current_task: AgentTaskInfo
    performance_metrics: AgentPerformanceMetrics
    last_activity: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }


class AgentStatusUpdate(BaseModel):
    """Schema for updating agent status"""
    status: str = Field(..., regex="^(active|idle|busy|offline|error)$")
    current_task_id: Optional[UUID] = None
    current_task_title: Optional[str] = Field(None, max_length=500)


class AgentMetricsUpdate(BaseModel):
    """Schema for updating agent metrics"""
    tasks_completed: Optional[float] = None
    tasks_failed: Optional[float] = None
    avg_response_time: Optional[float] = None
    uptime_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    @validator("uptime_percentage")
    def validate_uptime(cls, v):
        """Validate uptime percentage is between 0 and 100"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Uptime percentage must be between 0 and 100")
        return v


class AgentHeartbeat(BaseModel):
    """Schema for agent heartbeat updates"""
    agent_id: UUID
    status: str = Field(..., regex="^(active|idle|busy|offline|error)$")
    current_task_id: Optional[UUID] = None
    metrics: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)