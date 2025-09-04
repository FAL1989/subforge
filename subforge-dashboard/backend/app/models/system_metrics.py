"""
System metrics model for SubForge dashboard
"""

import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ..database.base import Base


class SystemMetrics(Base):
    """
    System metrics model for tracking SubForge system performance
    """

    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Basic system stats
    total_agents = Column(Integer, nullable=False, default=0)
    active_agents = Column(Integer, nullable=False, default=0)
    idle_agents = Column(Integer, nullable=False, default=0)
    offline_agents = Column(Integer, nullable=False, default=0)

    # Task statistics
    total_tasks = Column(Integer, nullable=False, default=0)
    pending_tasks = Column(Integer, nullable=False, default=0)
    in_progress_tasks = Column(Integer, nullable=False, default=0)
    completed_tasks = Column(Integer, nullable=False, default=0)
    failed_tasks = Column(Integer, nullable=False, default=0)

    # Workflow statistics
    total_workflows = Column(Integer, nullable=False, default=0)
    active_workflows = Column(Integer, nullable=False, default=0)
    completed_workflows = Column(Integer, nullable=False, default=0)
    paused_workflows = Column(Integer, nullable=False, default=0)

    # Performance metrics
    system_load_percentage = Column(Float, nullable=False, default=0.0)
    memory_usage_percentage = Column(Float, nullable=False, default=0.0)
    cpu_usage_percentage = Column(Float, nullable=False, default=0.0)
    disk_usage_percentage = Column(Float, nullable=False, default=0.0)

    # Response time metrics
    avg_response_time_ms = Column(Float, nullable=False, default=0.0)
    min_response_time_ms = Column(Float, nullable=False, default=0.0)
    max_response_time_ms = Column(Float, nullable=False, default=0.0)
    p95_response_time_ms = Column(Float, nullable=False, default=0.0)

    # Success rates
    overall_success_rate = Column(Float, nullable=False, default=0.0)
    task_success_rate = Column(Float, nullable=False, default=0.0)
    workflow_success_rate = Column(Float, nullable=False, default=0.0)
    agent_success_rate = Column(Float, nullable=False, default=0.0)

    # Network and connectivity
    websocket_connections = Column(Integer, nullable=False, default=0)
    api_requests_per_minute = Column(Float, nullable=False, default=0.0)
    error_rate_percentage = Column(Float, nullable=False, default=0.0)

    # System health
    uptime_percentage = Column(Float, nullable=False, default=100.0)
    last_restart = Column(DateTime(timezone=True), nullable=True)
    is_healthy = Column(Boolean, nullable=False, default=True)

    # Detailed metrics (JSON fields)
    agent_metrics = Column(JSON, nullable=False, default=dict)
    task_metrics = Column(JSON, nullable=False, default=dict)
    workflow_metrics = Column(JSON, nullable=False, default=dict)
    system_health_checks = Column(JSON, nullable=False, default=dict)

    # Time-based metrics
    hourly_stats = Column(JSON, nullable=False, default=dict)
    daily_stats = Column(JSON, nullable=False, default=dict)
    weekly_stats = Column(JSON, nullable=False, default=dict)

    # Timestamps
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<SystemMetrics(id={self.id}, recorded_at={self.recorded_at}, uptime={self.uptime_percentage}%)>"

    def to_dict(self) -> dict:
        """Convert system metrics to dictionary"""
        return {
            "id": str(self.id),
            "system_overview": {
                "total_agents": self.total_agents,
                "active_agents": self.active_agents,
                "idle_agents": self.idle_agents,
                "offline_agents": self.offline_agents,
            },
            "task_overview": {
                "total_tasks": self.total_tasks,
                "pending_tasks": self.pending_tasks,
                "in_progress_tasks": self.in_progress_tasks,
                "completed_tasks": self.completed_tasks,
                "failed_tasks": self.failed_tasks,
            },
            "workflow_overview": {
                "total_workflows": self.total_workflows,
                "active_workflows": self.active_workflows,
                "completed_workflows": self.completed_workflows,
                "paused_workflows": self.paused_workflows,
            },
            "performance_metrics": {
                "system_load_percentage": self.system_load_percentage,
                "memory_usage_percentage": self.memory_usage_percentage,
                "cpu_usage_percentage": self.cpu_usage_percentage,
                "disk_usage_percentage": self.disk_usage_percentage,
            },
            "response_time_metrics": {
                "avg_response_time_ms": self.avg_response_time_ms,
                "min_response_time_ms": self.min_response_time_ms,
                "max_response_time_ms": self.max_response_time_ms,
                "p95_response_time_ms": self.p95_response_time_ms,
            },
            "success_rates": {
                "overall_success_rate": self.overall_success_rate,
                "task_success_rate": self.task_success_rate,
                "workflow_success_rate": self.workflow_success_rate,
                "agent_success_rate": self.agent_success_rate,
            },
            "network_metrics": {
                "websocket_connections": self.websocket_connections,
                "api_requests_per_minute": self.api_requests_per_minute,
                "error_rate_percentage": self.error_rate_percentage,
            },
            "system_health": {
                "uptime_percentage": self.uptime_percentage,
                "last_restart": (
                    self.last_restart.isoformat() if self.last_restart else None
                ),
                "is_healthy": self.is_healthy,
                "health_checks": self.system_health_checks,
            },
            "detailed_metrics": {
                "agent_metrics": self.agent_metrics,
                "task_metrics": self.task_metrics,
                "workflow_metrics": self.workflow_metrics,
            },
            "time_series": {
                "hourly_stats": self.hourly_stats,
                "daily_stats": self.daily_stats,
                "weekly_stats": self.weekly_stats,
            },
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def calculate_derived_metrics(self):
        """Calculate derived metrics from base metrics"""
        # Calculate success rates
        total_tasks = self.completed_tasks + self.failed_tasks
        if total_tasks > 0:
            self.task_success_rate = (self.completed_tasks / total_tasks) * 100
        else:
            self.task_success_rate = 0.0

        total_workflows = self.completed_workflows + self.paused_workflows
        if total_workflows > 0:
            self.workflow_success_rate = (
                self.completed_workflows / total_workflows
            ) * 100
        else:
            self.workflow_success_rate = 0.0

        # Calculate overall success rate (weighted average)
        if self.total_agents > 0:
            self.overall_success_rate = (
                self.task_success_rate * 0.6
                + self.workflow_success_rate * 0.3
                + self.agent_success_rate * 0.1
            )
        else:
            self.overall_success_rate = 0.0

        # Determine system health
        self.is_healthy = (
            self.uptime_percentage > 95.0
            and self.error_rate_percentage < 5.0
            and self.system_load_percentage < 90.0
            and self.memory_usage_percentage < 85.0
        )

    @classmethod
    def create_snapshot(cls, agents_data=None, tasks_data=None, workflows_data=None):
        """Create a metrics snapshot from current system state"""
        metrics = cls()

        if agents_data:
            metrics.total_agents = len(agents_data)
            metrics.active_agents = len(
                [a for a in agents_data if a.status == "active"]
            )
            metrics.idle_agents = len([a for a in agents_data if a.status == "idle"])
            metrics.offline_agents = len(
                [a for a in agents_data if a.status == "offline"]
            )

        if tasks_data:
            metrics.total_tasks = len(tasks_data)
            metrics.pending_tasks = len(
                [t for t in tasks_data if t.status == "pending"]
            )
            metrics.in_progress_tasks = len(
                [t for t in tasks_data if t.status == "in_progress"]
            )
            metrics.completed_tasks = len(
                [t for t in tasks_data if t.status == "completed"]
            )
            metrics.failed_tasks = len([t for t in tasks_data if t.status == "failed"])

        if workflows_data:
            metrics.total_workflows = len(workflows_data)
            metrics.active_workflows = len(
                [w for w in workflows_data if w.status == "active"]
            )
            metrics.completed_workflows = len(
                [w for w in workflows_data if w.status == "completed"]
            )
            metrics.paused_workflows = len(
                [w for w in workflows_data if w.status == "paused"]
            )

        metrics.calculate_derived_metrics()
        return metrics