#!/usr/bin/env python3
"""
Refactored PRP Generator using Strategy Pattern
Orchestrates PRP generation through specialized strategies
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from ..context_engineer import ContextPackage
from ..project_analyzer import ProjectProfile
from ..prp_template_loader import PRPTemplateLoader, create_template_loader
from .base import PRP, PRPType
from .registry import PRPStrategyRegistry, create_strategy_registry


class PRPGenerator:
    """
    Refactored PRP Generator that uses Strategy Pattern for generation
    
    This class serves as the main orchestrator, delegating actual PRP
    generation to specialized strategies based on the type of PRP needed.
    """
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize the PRP Generator
        
        Args:
            workspace_dir: Path to workspace directory
        """
        self.workspace_dir = workspace_dir
        self.prps_dir = workspace_dir / "PRPs"
        self.templates_dir = self.prps_dir / "templates"
        self.generated_dir = self.prps_dir / "generated"
        
        # Ensure directories exist
        for directory in [self.prps_dir, self.templates_dir, self.generated_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize template loader
        try:
            self.template_loader = create_template_loader()
        except (ValueError, FileNotFoundError) as e:
            print(f"Warning: Template loader initialization failed: {e}")
            print("Strategies will use embedded templates for backward compatibility")
            self.template_loader = None
        
        # Initialize strategy registry
        self.strategy_registry = create_strategy_registry(workspace_dir, self.template_loader)
    
    async def generate_prp(
        self,
        prp_type: PRPType,
        context: Dict[str, Any]
    ) -> PRP:
        """
        Generate a PRP using the appropriate strategy
        
        Args:
            prp_type: Type of PRP to generate
            context: Context dictionary with necessary information
            
        Returns:
            Generated PRP
            
        Raises:
            ValueError: If no strategy available for the PRP type
        """
        # Get appropriate strategy
        strategy = self.strategy_registry.get_strategy(prp_type)
        
        # Validate context
        if not strategy.validate_context(context):
            required = strategy.get_required_context_keys()
            raise ValueError(f"Invalid context. Required keys: {required}")
        
        # Generate PRP using strategy
        prp = await strategy.generate(context)
        
        # Validate generated PRP
        if not strategy.validate(prp):
            raise ValueError(f"Generated PRP failed validation for type {prp_type.value}")
        
        return prp
    
    def generate_factory_analysis_prp(
        self,
        project_profile: ProjectProfile,
        context_package: ContextPackage,
        user_request: str,
    ) -> PRP:
        """
        Generate PRP for factory analysis phase (backward compatibility)
        
        Args:
            project_profile: Project profile information
            context_package: Context package with examples and patterns
            user_request: Original user request
            
        Returns:
            Generated factory analysis PRP
        """
        context = {
            "project_profile": project_profile,
            "context_package": context_package,
            "user_request": user_request,
        }
        
        # Run async method synchronously for backward compatibility
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from async context, create task
            task = asyncio.create_task(
                self.generate_prp(PRPType.FACTORY_ANALYSIS, context)
            )
            return asyncio.run_coroutine_threadsafe(task, loop).result()
        else:
            # If called from sync context, run directly
            return asyncio.run(
                self.generate_prp(PRPType.FACTORY_ANALYSIS, context)
            )
    
    def generate_factory_generation_prp(
        self,
        project_profile: ProjectProfile,
        context_package: ContextPackage,
        analysis_outputs: Dict[str, Any],
        subagent_type: str,
    ) -> PRP:
        """
        Generate PRP for factory generation phase (backward compatibility)
        
        Args:
            project_profile: Project profile information
            context_package: Context package with examples and patterns
            analysis_outputs: Results from analysis phase
            subagent_type: Type of subagent to generate
            
        Returns:
            Generated factory generation PRP
        """
        context = {
            "project_profile": project_profile,
            "context_package": context_package,
            "analysis_outputs": analysis_outputs,
            "subagent_type": subagent_type,
        }
        
        # Run async method synchronously for backward compatibility
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from async context, create task
            task = asyncio.create_task(
                self.generate_prp(PRPType.FACTORY_GENERATION, context)
            )
            return asyncio.run_coroutine_threadsafe(task, loop).result()
        else:
            # If called from sync context, run directly
            return asyncio.run(
                self.generate_prp(PRPType.FACTORY_GENERATION, context)
            )
    
    async def generate_validation_prp(
        self,
        project_profile: ProjectProfile,
        context_package: ContextPackage,
        validation_scope: str,
        artifacts_to_validate: list[str],
    ) -> PRP:
        """
        Generate PRP for validation phase
        
        Args:
            project_profile: Project profile information
            context_package: Context package with examples and patterns
            validation_scope: Scope of validation (e.g., "full_project", "agents")
            artifacts_to_validate: List of artifacts to validate
            
        Returns:
            Generated validation PRP
        """
        context = {
            "project_profile": project_profile,
            "context_package": context_package,
            "validation_scope": validation_scope,
            "artifacts_to_validate": artifacts_to_validate,
        }
        
        return await self.generate_prp(PRPType.VALIDATION_COMPREHENSIVE, context)
    
    async def generate_workflow_optimization_prp(
        self,
        project_profile: ProjectProfile,
        context_package: ContextPackage,
        optimization_targets: Dict[str, Any],
    ) -> PRP:
        """
        Generate PRP for workflow optimization
        
        Args:
            project_profile: Project profile information
            context_package: Context package with examples and patterns
            optimization_targets: Specific areas to optimize
            
        Returns:
            Generated workflow optimization PRP
        """
        # For now, use generation strategy with workflow-specific context
        context = {
            "project_profile": project_profile,
            "context_package": context_package,
            "analysis_outputs": optimization_targets,
            "subagent_type": "workflow-optimizer",
        }
        
        return await self.generate_prp(PRPType.FACTORY_GENERATION, context)
    
    async def generate_agent_specialization_prp(
        self,
        project_profile: ProjectProfile,
        context_package: ContextPackage,
        agent_type: str,
        specialization_requirements: Dict[str, Any],
    ) -> PRP:
        """
        Generate PRP for agent specialization
        
        Args:
            project_profile: Project profile information
            context_package: Context package with examples and patterns
            agent_type: Type of agent to specialize
            specialization_requirements: Specific requirements for specialization
            
        Returns:
            Generated agent specialization PRP
        """
        # For now, use generation strategy with agent-specific context
        context = {
            "project_profile": project_profile,
            "context_package": context_package,
            "analysis_outputs": specialization_requirements,
            "subagent_type": f"{agent_type}-specialist",
        }
        
        return await self.generate_prp(PRPType.FACTORY_GENERATION, context)
    
    def list_available_strategies(self) -> list[str]:
        """
        List all available PRP generation strategies
        
        Returns:
            List of available strategy types
        """
        return [prp_type.value for prp_type in self.strategy_registry.list_registered_types()]
    
    def register_custom_strategy(self, prp_type: PRPType, strategy):
        """
        Register a custom strategy for a PRP type
        
        Args:
            prp_type: Type of PRP the strategy generates
            strategy: Strategy instance to register
        """
        self.strategy_registry.register(prp_type, strategy)


def create_prp_generator(workspace_dir: Path) -> PRPGenerator:
    """
    Factory function to create PRPGenerator instance
    
    Args:
        workspace_dir: Path to workspace directory
        
    Returns:
        Configured PRPGenerator instance
    """
    return PRPGenerator(workspace_dir)