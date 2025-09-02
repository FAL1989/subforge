"""
Task model for SubForge dashboard
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Float, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from ..database.base import Base


class Task(Base):
    """
    Task model representing work items in the SubForge system
    """
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Status and priority
    status = Column(String(50), nullable=False, default="pending", index=True)
    priority = Column(String(20), nullable=False, default="medium", index=True)
    
    # Assignment
    assigned_agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_agent_name = Column(String(255), nullable=True)
    
    # Workflow association
    workflow_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Task details
    task_type = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=False, default=list)
    task_metadata = Column(JSON, nullable=False, default=dict)
    
    # Time tracking
    estimated_duration_minutes = Column(Integer, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dependencies
    dependencies = Column(JSON, nullable=False, default=list)
    dependents = Column(JSON, nullable=False, default=list)
    
    # Progress tracking
    progress_percentage = Column(Float, nullable=False, default=0.0)
    subtasks_completed = Column(Integer, nullable=False, default=0)
    subtasks_total = Column(Integer, nullable=False, default=0)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    complexity_score = Column(Integer, nullable=True)
    effort_points = Column(Integer, nullable=True)
    
    # Status flags
    is_blocked = Column(Boolean, nullable=False, default=False)
    is_urgent = Column(Boolean, nullable=False, default=False)
    requires_review = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', priority='{self.priority}')>"
    
    def to_dict(self) -> dict:
        """Convert task to dictionary"""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assigned_agent": {
                "id": str(self.assigned_agent_id) if self.assigned_agent_id else None,
                "name": self.assigned_agent_name
            },
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "task_type": self.task_type,
            "tags": self.tags,
            "metadata": self.task_metadata,
            "time_tracking": {
                "estimated_duration_minutes": self.estimated_duration_minutes,
                "actual_duration_minutes": self.actual_duration_minutes,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None
            },
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "progress": {
                "percentage": self.progress_percentage,
                "subtasks_completed": self.subtasks_completed,
                "subtasks_total": self.subtasks_total
            },
            "quality_metrics": {
                "quality_score": self.quality_score,
                "complexity_score": self.complexity_score,
                "effort_points": self.effort_points
            },
            "flags": {
                "is_blocked": self.is_blocked,
                "is_urgent": self.is_urgent,
                "requires_review": self.requires_review
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None
        }
    
    def start_task(self):
        """Mark task as started"""
        self.status = "in_progress"
        self.started_at = datetime.utcnow()
        
    def complete_task(self, quality_score: float = None):
        """Mark task as completed"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.actual_duration_minutes = int(duration.total_seconds() / 60)
        
        if quality_score is not None:
            self.quality_score = quality_score
    
    def update_progress(self, percentage: float):
        """Update task progress percentage"""
        self.progress_percentage = min(100.0, max(0.0, percentage))
        self.updated_at = datetime.utcnow()
    
    def add_dependency(self, task_id: str):
        """Add a task dependency"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
    
    def remove_dependency(self, task_id: str):
        """Remove a task dependency"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
    
    def is_ready_to_start(self, completed_tasks: list = None) -> bool:
        """Check if task is ready to start (all dependencies completed)"""
        if not self.dependencies:
            return True
        
        if completed_tasks is None:
            return False
        
        return all(dep_id in completed_tasks for dep_id in self.dependencies)