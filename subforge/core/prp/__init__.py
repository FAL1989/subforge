#!/usr/bin/env python3
"""
PRP (Product Requirements Prompt) Package
Refactored implementation using Strategy Pattern
"""

from .base import IPRPStrategy, PRP, PRPType, BaseStrategy
from .factory_strategy import FactoryAnalysisStrategy
from .generation_strategy import GenerationStrategy
from .generator import PRPGenerator, create_prp_generator
from .registry import PRPStrategyRegistry, create_strategy_registry
from .utils import (
    format_analysis_insights,
    format_checklist,
    format_metrics,
    format_output_spec,
    format_project_context,
    get_architecture_workflow_requirements,
    get_subagent_output_specification,
    get_subagent_success_metrics,
    get_subagent_validation_checklist,
)
from .validation_strategy import ValidationStrategy
from .builder import PRPBuilder, FluentPRPBuilder, create_prp_builder, create_fluent_builder

__all__ = [
    # Core classes
    "PRP",
    "PRPType",
    "PRPGenerator",
    
    # Strategies
    "IPRPStrategy",
    "BaseStrategy",
    "FactoryAnalysisStrategy",
    "GenerationStrategy",
    "ValidationStrategy",
    
    # Registry
    "PRPStrategyRegistry",
    
    # Builder
    "PRPBuilder",
    "FluentPRPBuilder",
    
    # Factory functions
    "create_prp_generator",
    "create_strategy_registry",
    "create_prp_builder",
    "create_fluent_builder",
    
    # Utility functions
    "format_analysis_insights",
    "format_checklist",
    "format_metrics",
    "format_output_spec",
    "format_project_context",
    "get_architecture_workflow_requirements",
    "get_subagent_output_specification",
    "get_subagent_success_metrics",
    "get_subagent_validation_checklist",
]

# Version info
__version__ = "2.0.0"
__author__ = "SubForge Team"