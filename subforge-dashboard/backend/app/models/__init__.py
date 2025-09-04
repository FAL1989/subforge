"""
SQLAlchemy models for the SubForge Dashboard
"""

from .agent import Agent
from .database import (
    AgentPerformanceMetrics,
    HandoffHistory,
    PhaseHistory,
    WorkflowHistory,
)
from .system_metrics import SystemMetrics
from .task import Task
from .workflow import Workflow

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    "Agent",
    "Task",
    "Workflow",
    "SystemMetrics",
    "WorkflowHistory",
    "PhaseHistory",
    "HandoffHistory",
    "AgentPerformanceMetrics",
]