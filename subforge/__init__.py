"""
SubForge - Forge your perfect Claude Code development team
"""

__version__ = "1.1.2"
__author__ = "SubForge Contributors"
__description__ = "AI-powered subagent factory for Claude Code developers"
__license__ = "MIT"

# Core imports for easier access
from .core.knowledge_extractor import ProjectKnowledgeExtractor
from .core.context_builder import ContextBuilder
from .core.gap_analyzer import GapAnalyzer

__all__ = [
    "ProjectKnowledgeExtractor",
    "ContextBuilder",
    "GapAnalyzer",
    "__version__",
    "__author__",
    "__description__",
    "__license__",
]