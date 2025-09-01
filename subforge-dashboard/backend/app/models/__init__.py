"""
SQLAlchemy models for the SubForge Dashboard
"""

from .agent import Agent
from .task import Task
from .workflow import Workflow
from .system_metrics import SystemMetrics

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    "Agent",
    "Task", 
    "Workflow",
    "SystemMetrics"
]