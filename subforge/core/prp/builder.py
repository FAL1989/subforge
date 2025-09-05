#!/usr/bin/env python3
"""
PRP Builder Pattern Implementation
Provides fluent interface for constructing PRPs
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..context_engineer import ContextPackage
from .base import PRP, PRPType


class PRPBuilder:
    """
    Builder for constructing PRP instances with a fluent interface
    
    This class provides a step-by-step approach to building PRPs,
    ensuring all required fields are set before creation.
    """
    
    def __init__(self):
        """Initialize the builder with default values"""
        self._reset()
    
    def _reset(self):
        """Reset builder to initial state"""
        self._id: Optional[str] = None
        self._type: Optional[PRPType] = None
        self._title: Optional[str] = None
        self._context_package: Optional[ContextPackage] = None
        self._execution_prompt: Optional[str] = None
        self._validation_checklist: List[str] = []
        self._success_metrics: List[str] = []
        self._output_specification: Dict[str, Any] = {}
        self._created_at: Optional[datetime] = None
    
    def with_id(self, prp_id: str) -> 'PRPBuilder':
        """
        Set the PRP ID
        
        Args:
            prp_id: Unique identifier for the PRP
            
        Returns:
            Self for method chaining
        """
        self._id = prp_id
        return self
    
    def with_type(self, prp_type: PRPType) -> 'PRPBuilder':
        """
        Set the PRP type
        
        Args:
            prp_type: Type of PRP
            
        Returns:
            Self for method chaining
        """
        self._type = prp_type
        return self
    
    def with_title(self, title: str) -> 'PRPBuilder':
        """
        Set the PRP title
        
        Args:
            title: Title for the PRP
            
        Returns:
            Self for method chaining
        """
        self._title = title
        return self
    
    def with_context_package(self, context_package: ContextPackage) -> 'PRPBuilder':
        """
        Set the context package
        
        Args:
            context_package: Context package with examples and patterns
            
        Returns:
            Self for method chaining
        """
        self._context_package = context_package
        return self
    
    def with_execution_prompt(self, prompt: str) -> 'PRPBuilder':
        """
        Set the execution prompt
        
        Args:
            prompt: Execution prompt text
            
        Returns:
            Self for method chaining
        """
        self._execution_prompt = prompt
        return self
    
    def add_validation_item(self, item: str) -> 'PRPBuilder':
        """
        Add a validation checklist item
        
        Args:
            item: Validation checklist item
            
        Returns:
            Self for method chaining
        """
        self._validation_checklist.append(item)
        return self
    
    def with_validation_checklist(self, checklist: List[str]) -> 'PRPBuilder':
        """
        Set the entire validation checklist
        
        Args:
            checklist: List of validation items
            
        Returns:
            Self for method chaining
        """
        self._validation_checklist = checklist
        return self
    
    def add_success_metric(self, metric: str) -> 'PRPBuilder':
        """
        Add a success metric
        
        Args:
            metric: Success metric
            
        Returns:
            Self for method chaining
        """
        self._success_metrics.append(metric)
        return self
    
    def with_success_metrics(self, metrics: List[str]) -> 'PRPBuilder':
        """
        Set the entire success metrics list
        
        Args:
            metrics: List of success metrics
            
        Returns:
            Self for method chaining
        """
        self._success_metrics = metrics
        return self
    
    def add_output_spec(self, key: str, value: Any) -> 'PRPBuilder':
        """
        Add an output specification entry
        
        Args:
            key: Specification key
            value: Specification value
            
        Returns:
            Self for method chaining
        """
        self._output_specification[key] = value
        return self
    
    def with_output_specification(self, spec: Dict[str, Any]) -> 'PRPBuilder':
        """
        Set the entire output specification
        
        Args:
            spec: Output specification dictionary
            
        Returns:
            Self for method chaining
        """
        self._output_specification = spec
        return self
    
    def with_created_at(self, created_at: datetime) -> 'PRPBuilder':
        """
        Set the creation timestamp
        
        Args:
            created_at: Creation timestamp
            
        Returns:
            Self for method chaining
        """
        self._created_at = created_at
        return self
    
    def build(self) -> PRP:
        """
        Build the PRP instance
        
        Returns:
            Constructed PRP instance
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        missing = []
        if not self._id:
            missing.append("id")
        if not self._type:
            missing.append("type")
        if not self._title:
            missing.append("title")
        if not self._context_package:
            missing.append("context_package")
        if not self._execution_prompt:
            missing.append("execution_prompt")
        
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Set defaults for optional fields
        if not self._created_at:
            self._created_at = datetime.now()
        
        # Create PRP
        prp = PRP(
            id=self._id,
            type=self._type,
            title=self._title,
            context_package=self._context_package,
            execution_prompt=self._execution_prompt,
            validation_checklist=self._validation_checklist,
            success_metrics=self._success_metrics,
            output_specification=self._output_specification,
            created_at=self._created_at,
        )
        
        # Reset builder for reuse
        self._reset()
        
        return prp


class FluentPRPBuilder(PRPBuilder):
    """
    Enhanced builder with more fluent methods and validation
    """
    
    def for_project(self, project_name: str) -> 'FluentPRPBuilder':
        """
        Configure builder for a specific project
        
        Args:
            project_name: Name of the project
            
        Returns:
            Self for method chaining
        """
        # Update title if not set
        if not self._title:
            self._title = f"PRP for {project_name}"
        
        # Generate ID if not set
        if not self._id:
            timestamp = int(datetime.now().timestamp())
            self._id = f"{project_name.lower().replace(' ', '_')}_{timestamp}"
        
        return self
    
    def for_analysis(self) -> 'FluentPRPBuilder':
        """
        Configure builder for analysis PRP
        
        Returns:
            Self for method chaining
        """
        self._type = PRPType.FACTORY_ANALYSIS
        if self._title and "for" in self._title:
            self._title = f"Factory Analysis {self._title.split('for', 1)[1]}"
        return self
    
    def for_generation(self, subagent_type: str) -> 'FluentPRPBuilder':
        """
        Configure builder for generation PRP
        
        Args:
            subagent_type: Type of subagent being generated
            
        Returns:
            Self for method chaining
        """
        self._type = PRPType.FACTORY_GENERATION
        if self._title and "for" in self._title:
            project_part = self._title.split('for', 1)[1]
            self._title = f"{subagent_type.replace('-', ' ').title()} Generation for{project_part}"
        return self
    
    def for_validation(self, scope: str) -> 'FluentPRPBuilder':
        """
        Configure builder for validation PRP
        
        Args:
            scope: Validation scope
            
        Returns:
            Self for method chaining
        """
        self._type = PRPType.VALIDATION_COMPREHENSIVE
        if self._title and "for" in self._title:
            project_part = self._title.split('for', 1)[1]
            self._title = f"Comprehensive Validation ({scope}) for{project_part}"
        return self
    
    def with_standard_analysis_checklist(self) -> 'FluentPRPBuilder':
        """
        Add standard analysis validation checklist
        
        Returns:
            Self for method chaining
        """
        self._validation_checklist = [
            "Project structure is completely mapped and documented",
            "All technologies are identified with specific versions",
            "Architecture pattern is validated with concrete evidence",
            "Team size and workflow recommendations are specific",
            "Integration requirements are clearly documented",
            "Quality standards are defined and measurable",
            "Analysis provides clear guidance for template selection",
            "All findings are backed by project evidence",
        ]
        return self
    
    def with_standard_generation_checklist(self) -> 'FluentPRPBuilder':
        """
        Add standard generation validation checklist
        
        Returns:
            Self for method chaining
        """
        self._validation_checklist = [
            "Output files are generated in correct locations",
            "All generated content is syntactically valid",
            "Configuration integrates with existing project structure",
            "Documentation is comprehensive and accurate",
            "Generated artifacts follow project conventions",
            "No conflicts with existing configurations",
        ]
        return self
    
    def with_standard_validation_checklist(self) -> 'FluentPRPBuilder':
        """
        Add standard validation checklist
        
        Returns:
            Self for method chaining
        """
        self._validation_checklist = [
            "All artifacts exist and are accessible",
            "No syntax errors in any generated files",
            "All configurations are valid and complete",
            "Documentation is comprehensive and accurate",
            "Integration tests pass successfully",
            "Quality metrics meet defined thresholds",
        ]
        return self


def create_prp_builder() -> PRPBuilder:
    """
    Factory function to create a basic PRP builder
    
    Returns:
        PRPBuilder instance
    """
    return PRPBuilder()


def create_fluent_builder() -> FluentPRPBuilder:
    """
    Factory function to create a fluent PRP builder
    
    Returns:
        FluentPRPBuilder instance
    """
    return FluentPRPBuilder()