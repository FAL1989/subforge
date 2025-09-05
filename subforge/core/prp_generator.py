#!/usr/bin/env python3
"""
PRP Generator - Product Requirements Prompt System (Compatibility Layer)

This file maintains backward compatibility while delegating to the refactored
Strategy Pattern implementation in the prp/ module.
"""

from pathlib import Path
from typing import Any, Dict

# Import from refactored module
from .prp import (
    PRP,
    PRPType,
    PRPGenerator as NewPRPGenerator,
    create_prp_generator as new_create_prp_generator,
)
from .context_engineer import ContextPackage
from .project_analyzer import ProjectProfile

# Re-export for backward compatibility
__all__ = [
    "PRP",
    "PRPType",
    "PRPGenerator",
    "create_prp_generator",
]


class PRPGenerator(NewPRPGenerator):
    """
    Backward-compatible PRP Generator wrapper
    
    This class maintains the old interface while using the new
    refactored implementation under the hood.
    """
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize PRP Generator with backward compatibility
        
        Args:
            workspace_dir: Path to workspace directory
        """
        super().__init__(workspace_dir)
        
        # Maintain any old attributes for compatibility
        self._create_prp_templates()
    
    def _create_prp_templates(self):
        """Stub for backward compatibility"""
        pass
    
    # The following methods are already implemented in the new generator
    # with the same signatures, so they will work automatically:
    # - generate_factory_analysis_prp
    # - generate_factory_generation_prp
    
    # Add any other backward compatibility methods if needed
    def _get_subagent_execution_prompt(
        self,
        subagent_type: str,
        project_profile: ProjectProfile,
        context_package: ContextPackage,
        analysis_outputs: Dict[str, Any],
    ) -> str:
        """
        Backward compatibility method
        
        This method was used internally but might be called by existing code
        """
        # Delegate to the new implementation
        from .prp.generation_strategy import GenerationStrategy
        
        strategy = GenerationStrategy(self.workspace_dir, self.template_loader)
        
        # Use async method synchronously
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            prompt = loop.run_until_complete(
                strategy._get_subagent_execution_prompt(
                    subagent_type, project_profile, context_package, analysis_outputs
                )
            )
            return prompt
        finally:
            loop.close()
    
    def _get_subagent_validation_checklist(self, subagent_type: str) -> list[str]:
        """Backward compatibility wrapper"""
        from .prp.utils import get_subagent_validation_checklist
        return get_subagent_validation_checklist(subagent_type)
    
    def _get_subagent_success_metrics(self, subagent_type: str) -> list[str]:
        """Backward compatibility wrapper"""
        from .prp.utils import get_subagent_success_metrics
        return get_subagent_success_metrics(subagent_type)
    
    def _get_subagent_output_specification(self, subagent_type: str) -> Dict[str, Any]:
        """Backward compatibility wrapper"""
        from .prp.utils import get_subagent_output_specification
        return get_subagent_output_specification(subagent_type)
    
    def _format_analysis_insights(self, analysis_outputs: Dict[str, Any]) -> str:
        """Backward compatibility wrapper"""
        from .prp.utils import format_analysis_insights
        return format_analysis_insights(analysis_outputs)
    
    def _format_project_context(self, project_profile: ProjectProfile) -> str:
        """Backward compatibility wrapper"""
        from .prp.utils import format_project_context
        return format_project_context(project_profile)
    
    def _get_architecture_workflow_requirements(self, architecture) -> str:
        """Backward compatibility wrapper"""
        from .prp.utils import get_architecture_workflow_requirements
        return get_architecture_workflow_requirements(architecture)
    
    def _save_prp(self, prp: PRP):
        """Backward compatibility wrapper"""
        # Use the base strategy's save method
        from .prp.base import BaseStrategy
        base = BaseStrategy(self.workspace_dir)
        base.save_prp(prp)


def create_prp_generator(workspace_dir: Path) -> PRPGenerator:
    """
    Factory function to create PRPGenerator instance (backward compatible)
    
    Args:
        workspace_dir: Path to workspace directory
        
    Returns:
        Configured PRPGenerator instance with backward compatibility
    """
    return PRPGenerator(workspace_dir)