"""
Agent model for SubForge dashboard
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ..database.base import Base


class Agent(Base):
    """
    Agent model representing SubForge agents
    """

    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="idle", index=True)
    description = Column(Text, nullable=True)

    # Current activity
    current_task_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    current_task_title = Column(String(500), nullable=True)

    # Configuration
    model = Column(String(100), nullable=False, default="claude-3-sonnet")
    tools = Column(JSON, nullable=False, default=list)
    capabilities = Column(JSON, nullable=False, default=list)
    configuration = Column(JSON, nullable=False, default=dict)

    # Performance metrics
    tasks_completed = Column(Float, nullable=False, default=0)
    tasks_failed = Column(Float, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)
    avg_response_time = Column(Float, nullable=False, default=0.0)
    uptime_percentage = Column(Float, nullable=False, default=100.0)

    # Activity tracking
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.agent_type}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert agent to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.agent_type,
            "status": self.status,
            "description": self.description,
            "current_task": {
                "id": str(self.current_task_id) if self.current_task_id else None,
                "title": self.current_task_title,
            },
            "configuration": {
                "model": self.model,
                "tools": self.tools,
                "capabilities": self.capabilities,
                **self.configuration,
            },
            "performance_metrics": {
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "success_rate": self.success_rate,
                "avg_response_time": self.avg_response_time,
                "uptime_percentage": self.uptime_percentage,
            },
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "last_heartbeat": (
                self.last_heartbeat.isoformat() if self.last_heartbeat else None
            ),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()

    def calculate_success_rate(self):
        """Calculate and update success rate"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 0:
            self.success_rate = (self.tasks_completed / total_tasks) * 100
        else:
            self.success_rate = 0.0