"""
Test Models for Performance Suite
Created: 2025-09-05 17:35 UTC-3 São Paulo

Simple mock models to support performance testing.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class AgentConfig:
    """Mock agent configuration for testing."""
    name: str
    domain: str
    expertise: List[str] = None
    tools: List[str] = None
    knowledge_base: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.expertise is None:
            self.expertise = []
        if self.tools is None:
            self.tools = []
        if self.knowledge_base is None:
            self.knowledge_base = {}


@dataclass
class ProjectContext:
    """Mock project context for testing."""
    name: str
    description: str = ""
    tech_stack: List[str] = None
    architecture: str = "monolithic"
    complexity: str = "simple"
    
    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = []