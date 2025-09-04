"""
Pydantic schemas for SystemMetrics model
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SystemOverview(BaseModel):
    """Schema for system overview metrics"""

    total_agents: int = 0
    active_agents: int = 0
    idle_agents: int = 0
    offline_agents: int = 0


class TaskOverview(BaseModel):
    """Schema for task overview metrics"""

    total_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0


class WorkflowOverview(BaseModel):
    """Schema for workflow overview metrics"""

    total_workflows: int = 0
    active_workflows: int = 0
    completed_workflows: int = 0
    paused_workflows: int = 0


class PerformanceMetrics(BaseModel):
    """Schema for system performance metrics"""

    system_load_percentage: float = 0.0
    memory_usage_percentage: float = 0.0
    cpu_usage_percentage: float = 0.0
    disk_usage_percentage: float = 0.0


class ResponseTimeMetrics(BaseModel):
    """Schema for response time metrics"""

    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0


class SuccessRates(BaseModel):
    """Schema for success rate metrics"""

    overall_success_rate: float = 0.0
    task_success_rate: float = 0.0
    workflow_success_rate: float = 0.0
    agent_success_rate: float = 0.0


class NetworkMetrics(BaseModel):
    """Schema for network metrics"""

    websocket_connections: int = 0
    api_requests_per_minute: float = 0.0
    error_rate_percentage: float = 0.0


class SystemHealth(BaseModel):
    """Schema for system health metrics"""

    uptime_percentage: float = 100.0
    last_restart: Optional[datetime] = None
    is_healthy: bool = True
    health_checks: Dict[str, Any] = Field(default_factory=dict)


class DetailedMetrics(BaseModel):
    """Schema for detailed metrics"""

    agent_metrics: Dict[str, Any] = Field(default_factory=dict)
    task_metrics: Dict[str, Any] = Field(default_factory=dict)
    workflow_metrics: Dict[str, Any] = Field(default_factory=dict)


class TimeSeries(BaseModel):
    """Schema for time series metrics"""

    hourly_stats: Dict[str, Any] = Field(default_factory=dict)
    daily_stats: Dict[str, Any] = Field(default_factory=dict)
    weekly_stats: Dict[str, Any] = Field(default_factory=dict)


class SystemMetricsResponse(BaseModel):
    """Schema for system metrics response"""

    id: UUID
    system_overview: SystemOverview
    task_overview: TaskOverview
    workflow_overview: WorkflowOverview
    performance_metrics: PerformanceMetrics
    response_time_metrics: ResponseTimeMetrics
    success_rates: SuccessRates
    network_metrics: NetworkMetrics
    system_health: SystemHealth
    detailed_metrics: DetailedMetrics
    time_series: TimeSeries
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        }


class SystemMetricsCreate(BaseModel):
    """Schema for creating system metrics"""

    system_load_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_usage_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    cpu_usage_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    disk_usage_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    websocket_connections: Optional[int] = Field(None, ge=0)
    api_requests_per_minute: Optional[float] = Field(None, ge=0.0)
    error_rate_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    detailed_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SystemStatusSummary(BaseModel):
    """Schema for system status summary"""

    status: str = "running"
    agents: SystemOverview
    tasks: TaskOverview
    workflows: WorkflowOverview
    uptime: str
    connected_clients: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class SystemHealthCheck(BaseModel):
    """Schema for system health check"""

    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, bool] = Field(default_factory=dict)
    uptime_seconds: Optional[float] = None
    version: str = "1.0.0"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class MetricsTimeRange(BaseModel):
    """Schema for metrics time range queries"""

    start_date: datetime
    end_date: datetime
    granularity: str = Field(default="hour", regex="^(minute|hour|day|week)$")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}