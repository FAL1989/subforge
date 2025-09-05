#!/usr/bin/env python3
"""
Context Engineer - Modular context engineering system
Uses specialized modules for different responsibilities
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import asyncio

from .project_analyzer import ProjectProfile
from .context.types import PreviousOutput
from .context.exceptions import (
    InvalidProfileError,
    ValidationError,
    ContextGenerationError,
)
from .context.validators import validate_project_profile
from .context.builder import ContextBuilder, ContextPackage
from .context.repository import ExampleRepository
from .context.patterns import PatternExtractor, ContextLevel
from .context.enricher import ContextEnricher
from .context.cache import CachedContextManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextEngineer:
    """
    Modular Context Engineering system with clean separation of concerns
    
    This class orchestrates between specialized modules:
    - ContextBuilder: Builds context packages
    - ExampleRepository: Manages code examples
    - PatternExtractor: Extracts relevant patterns
    - ContextEnricher: Enriches with guidelines
    - CachedContextManager: Handles caching
    """

    def __init__(
        self,
        workspace_dir: Path,
        use_cache: bool = True,
        cache_ttl_hours: int = 24
    ):
        """
        Initialize the Context Engineer with modular components
        
        Args:
            workspace_dir: Base directory for context operations
            use_cache: Whether to use caching
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.workspace_dir = workspace_dir
        self.context_library = workspace_dir / "context_library"
        self.use_cache = use_cache
        
        # Initialize modular components
        self._initialize_components(cache_ttl_hours)
        
        # Ensure directories exist
        self.context_library.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"ContextEngineer initialized with workspace: {workspace_dir}, "
            f"cache: {use_cache}"
        )

    def _initialize_components(self, cache_ttl_hours: int):
        """Initialize all modular components"""
        # Core components
        self.builder = ContextBuilder()
        self.repository = ExampleRepository(self.workspace_dir)
        self.pattern_extractor = PatternExtractor()
        self.enricher = ContextEnricher()
        
        # Cache manager (optional)
        if self.use_cache:
            cache_dir = self.workspace_dir / ".context_cache"
            self.cache_manager = CachedContextManager(
                cache_dir=cache_dir,
                ttl_hours=cache_ttl_hours
            )
        else:
            self.cache_manager = None

    def engineer_context_for_phase(
        self,
        phase_name: str,
        project_profile: ProjectProfile,
        previous_outputs: Optional[Dict[str, PreviousOutput]] = None,
        context_level: ContextLevel = ContextLevel.STANDARD,
    ) -> ContextPackage:
        """
        Engineer comprehensive context for a specific factory phase
        
        This method orchestrates between all modular components to build
        a complete context package.
        
        Args:
            phase_name: Name of the factory phase
            project_profile: Project profile from analyzer
            previous_outputs: Outputs from previous phases
            context_level: Depth of context to generate
            
        Returns:
            Complete context package for the phase
            
        Raises:
            InvalidProfileError: If project profile is invalid
            ContextGenerationError: If context generation fails
        """
        logger.info(
            f"Engineering {context_level.value} context for {phase_name} phase"
        )

        try:
            # Validate project profile
            validate_project_profile(project_profile)

            # Check cache if enabled
            if self.cache_manager:
                cached_context = self.cache_manager.get_cached_context(
                    project_profile, phase_name
                )
                if cached_context:
                    logger.info("Using cached context package")
                    return cached_context

            # Build context using modular components
            context_package = self._build_context_package(
                phase_name,
                project_profile,
                context_level,
                previous_outputs
            )

            # Save context package
            self._save_context_package(phase_name, context_package)

            # Cache if enabled
            if self.cache_manager:
                self.cache_manager.cache_context(
                    project_profile, phase_name, context_package
                )

            # Log statistics
            logger.info(
                f"Context package created: "
                f"{len(context_package.examples)} examples, "
                f"{len(context_package.patterns)} patterns, "
                f"{len(context_package.validation_gates)} validation gates"
            )

            return context_package

        except InvalidProfileError as e:
            logger.error(f"Invalid project profile: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Context validation failed: {e}")
            raise ContextGenerationError(f"Failed to generate context: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during context generation: {e}")
            raise ContextGenerationError(f"Context generation failed: {e}")

    def _build_context_package(
        self,
        phase_name: str,
        project_profile: ProjectProfile,
        context_level: ContextLevel,
        previous_outputs: Optional[Dict[str, PreviousOutput]]
    ) -> ContextPackage:
        """Build context package using modular components"""
        
        # Use async to gather examples efficiently
        examples = asyncio.run(
            self.repository.find_relevant(project_profile, phase_name)
        )
        
        # Extract patterns based on context level
        patterns = self.pattern_extractor.extract_from_profile(
            project_profile, phase_name, context_level
        )
        
        # Add architecture-specific patterns
        arch_patterns = self.pattern_extractor.extract_from_architecture(
            project_profile.architecture_pattern.value, phase_name
        )
        patterns.extend(arch_patterns)
        
        # Add framework-specific patterns
        fw_patterns = self.pattern_extractor.extract_from_frameworks(
            list(project_profile.technology_stack.frameworks), phase_name
        )
        patterns.extend(fw_patterns)
        
        # Build base contexts
        self.builder.with_project_context(project_profile)
        self.builder.with_technical_context(project_profile, phase_name)
        
        # Get enriched technical context
        technical_context = self.builder._technical_context
        technical_context = self.enricher.enrich_with_guidelines(
            technical_context, project_profile.architecture_pattern.value
        )
        technical_context = self.enricher.enrich_with_constraints(
            technical_context, project_profile
        )
        technical_context = self.enricher.enrich_with_best_practices(
            technical_context
        )
        
        # Update builder with enriched context
        self.builder._technical_context = technical_context
        
        # Add all components to builder
        self.builder.with_examples(examples)
        self.builder.with_patterns(patterns)
        
        # Get validation gates and criteria from enricher
        validation_gates = self.enricher.create_validation_gates(
            phase_name, project_profile
        )
        self.builder.with_validation_gates(validation_gates)
        
        references = self.enricher.enrich_with_references(
            project_profile, phase_name
        )
        self.builder.with_references(references)
        
        success_criteria = self.enricher.define_success_criteria(
            phase_name, project_profile
        )
        self.builder.with_success_criteria(success_criteria)
        
        # Build final package
        return self.builder.build()

    def _save_context_package(self, phase_name: str, context_package: ContextPackage):
        """Save context package for reference and debugging"""
        try:
            # Save as markdown
            context_file = self.context_library / f"{phase_name}_context.md"
            with open(context_file, "w", encoding="utf-8") as f:
                f.write(context_package.to_markdown())

            # Save as JSON for programmatic access
            json_file = self.context_library / f"{phase_name}_context.json"
            json_data = self._prepare_for_json(context_package.to_dict())
            
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)

            logger.info(f"Context package saved to {context_file}")

        except Exception as e:
            logger.error(f"Failed to save context package: {e}")
            # Don't fail the whole process if saving fails

    def _prepare_for_json(self, obj):
        """Convert complex objects for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._prepare_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return obj

    def invalidate_cache(
        self,
        profile: Optional[ProjectProfile] = None,
        phase: Optional[str] = None
    ):
        """
        Invalidate cached contexts
        
        Args:
            profile: Project profile (None = all)
            phase: Phase name (None = all phases for profile)
        """
        if self.cache_manager:
            self.cache_manager.invalidate_cache(profile, phase)
            logger.info("Cache invalidated")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache_manager:
            return self.cache_manager.get_cache_stats()
        return {"cache_enabled": False}

    def clear_repository_cache(self):
        """Clear the example repository cache"""
        self.repository.clear_cache()
        logger.info("Repository cache cleared")

    def set_context_level(self, level: ContextLevel):
        """Set the default context level for all operations"""
        self.default_context_level = level
        logger.info(f"Default context level set to: {level.value}")


def create_context_engineer(
    workspace_dir: Path,
    use_cache: bool = True,
    cache_ttl_hours: int = 24
) -> ContextEngineer:
    """
    Factory function to create ContextEngineer instance
    
    Args:
        workspace_dir: Base directory for context operations
        use_cache: Whether to enable caching
        cache_ttl_hours: Cache time-to-live in hours
        
    Returns:
        Configured ContextEngineer instance
    """
    return ContextEngineer(
        workspace_dir=workspace_dir,
        use_cache=use_cache,
        cache_ttl_hours=cache_ttl_hours
    )