"""
Workflow model for SubForge dashboard
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from ..database.base import Base


class Workflow(Base):
    """
    Workflow model representing orchestrated task sequences
    """
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Status and type
    status = Column(String(50), nullable=False, default="active", index=True)
    workflow_type = Column(String(100), nullable=True, index=True)
    
    # Project association
    project_id = Column(String(255), nullable=True, index=True)
    project_name = Column(String(255), nullable=True)
    
    # Workflow configuration
    configuration = Column(JSON, nullable=False, default=dict)
    parameters = Column(JSON, nullable=False, default=dict)
    
    # Progress tracking
    progress_percentage = Column(Float, nullable=False, default=0.0)
    total_tasks = Column(Integer, nullable=False, default=0)
    completed_tasks = Column(Integer, nullable=False, default=0)
    failed_tasks = Column(Integer, nullable=False, default=0)
    
    # Time tracking
    estimated_duration_hours = Column(Float, nullable=True)
    actual_duration_hours = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Quality metrics
    success_rate = Column(Float, nullable=False, default=0.0)
    quality_score = Column(Float, nullable=True)
    efficiency_score = Column(Float, nullable=True)
    
    # Agent assignments
    assigned_agents = Column(JSON, nullable=False, default=list)
    agent_utilization = Column(JSON, nullable=False, default=dict)
    
    # Workflow metadata
    tags = Column(JSON, nullable=False, default=list)
    workflow_metadata = Column(JSON, nullable=False, default=dict)
    
    # Status flags
    is_paused = Column(Boolean, nullable=False, default=False)
    is_template = Column(Boolean, nullable=False, default=False)
    requires_approval = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert workflow to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "workflow_type": self.workflow_type,
            "project": {
                "id": self.project_id,
                "name": self.project_name
            },
            "configuration": self.configuration,
            "parameters": self.parameters,
            "progress": {
                "percentage": self.progress_percentage,
                "total_tasks": self.total_tasks,
                "completed_tasks": self.completed_tasks,
                "failed_tasks": self.failed_tasks
            },
            "time_tracking": {
                "estimated_duration_hours": self.estimated_duration_hours,
                "actual_duration_hours": self.actual_duration_hours,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None
            },
            "quality_metrics": {
                "success_rate": self.success_rate,
                "quality_score": self.quality_score,
                "efficiency_score": self.efficiency_score
            },
            "agents": {
                "assigned": self.assigned_agents,
                "utilization": self.agent_utilization
            },
            "tags": self.tags,
            "metadata": self.workflow_metadata,
            "flags": {
                "is_paused": self.is_paused,
                "is_template": self.is_template,
                "requires_approval": self.requires_approval
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None
        }
    
    def start_workflow(self):
        """Start the workflow execution"""
        self.status = "running"
        self.started_at = datetime.utcnow()
        self.is_paused = False
    
    def complete_workflow(self):
        """Mark workflow as completed"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.actual_duration_hours = duration.total_seconds() / 3600
        
        # Calculate final success rate
        if self.total_tasks > 0:
            self.success_rate = (self.completed_tasks / self.total_tasks) * 100
    
    def pause_workflow(self):
        """Pause workflow execution"""
        self.is_paused = True
        if self.status == "running":
            self.status = "paused"
    
    def resume_workflow(self):
        """Resume paused workflow"""
        self.is_paused = False
        if self.status == "paused":
            self.status = "running"
    
    def update_progress(self):
        """Recalculate workflow progress based on task completion"""
        if self.total_tasks > 0:
            self.progress_percentage = (self.completed_tasks / self.total_tasks) * 100
            self.success_rate = (self.completed_tasks / (self.completed_tasks + self.failed_tasks)) * 100 if (self.completed_tasks + self.failed_tasks) > 0 else 0
        else:
            self.progress_percentage = 0.0
            self.success_rate = 0.0
    
    def add_agent(self, agent_id: str, agent_name: str = None):
        """Add an agent to the workflow"""
        agent_data = {"id": agent_id, "name": agent_name}
        if agent_data not in self.assigned_agents:
            self.assigned_agents.append(agent_data)
    
    def remove_agent(self, agent_id: str):
        """Remove an agent from the workflow"""
        self.assigned_agents = [a for a in self.assigned_agents if a.get("id") != agent_id]
    
    def update_agent_utilization(self, agent_id: str, utilization_data: dict):
        """Update agent utilization metrics"""
        self.agent_utilization[agent_id] = utilization_data