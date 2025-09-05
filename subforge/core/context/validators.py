#!/usr/bin/env python3
"""
Validation utilities for Context Engineering module
Provides input validation and type checking
"""

import logging
from pathlib import Path
from typing import Optional, List

from ..project_analyzer import ProjectProfile
from .exceptions import InvalidProfileError, ValidationError
from .types import ProjectContext, TechnicalContext, Example, Pattern, ValidationGate

logger = logging.getLogger(__name__)


def validate_project_profile(profile: ProjectProfile) -> None:
    """
    Validate project profile completeness and correctness
    
    Args:
        profile: Project profile to validate
        
    Raises:
        InvalidProfileError: If profile is invalid or incomplete
    """
    logger.debug(f"Validating project profile: {profile.name}")
    
    # Required fields validation
    if not profile.name:
        raise InvalidProfileError("Project name is required")
    
    if not profile.path or not Path(profile.path).exists():
        raise InvalidProfileError(f"Project path '{profile.path}' does not exist")
    
    if not profile.technology_stack:
        raise InvalidProfileError("Technology stack is required")
    
    if not profile.technology_stack.languages:
        raise InvalidProfileError("At least one programming language must be specified")
    
    # Complexity validation
    valid_complexities = ["simple", "medium", "complex", "enterprise"]
    if profile.complexity.value not in valid_complexities:
        raise InvalidProfileError(
            f"Invalid complexity level: {profile.complexity.value}. "
            f"Must be one of: {', '.join(valid_complexities)}"
        )
    
    # Architecture pattern validation
    valid_architectures = [
        "monolithic", "modular", "microservices", "serverless", 
        "event_driven", "layered", "mvc", "jamstack", "unknown"
    ]
    if profile.architecture_pattern.value not in valid_architectures:
        logger.warning(
            f"Unknown architecture pattern: {profile.architecture_pattern.value}"
        )
    
    # Team size validation
    if profile.team_size_estimate < 1:
        raise InvalidProfileError(
            f"Invalid team size estimate: {profile.team_size_estimate}"
        )
    
    # File and code metrics validation
    if profile.file_count < 0:
        raise InvalidProfileError(f"Invalid file count: {profile.file_count}")
    
    if profile.lines_of_code < 0:
        raise InvalidProfileError(f"Invalid lines of code: {profile.lines_of_code}")
    
    logger.info(f"Project profile validation successful: {profile.name}")


def validate_project_context(context: ProjectContext) -> None:
    """
    Validate project context data structure
    
    Args:
        context: Project context to validate
        
    Raises:
        ValidationError: If context is invalid
    """
    logger.debug("Validating project context")
    
    required_fields = [
        "name", "path", "architecture_pattern", "complexity_level",
        "languages", "frameworks", "team_size_estimate"
    ]
    
    for field in required_fields:
        if field not in context or context[field] is None:
            raise ValidationError(f"Required field missing in project context: {field}")
    
    # Validate path exists
    if not Path(context["path"]).exists():
        raise ValidationError(f"Project path does not exist: {context['path']}")
    
    # Validate complexity level
    valid_complexities = ["simple", "medium", "complex", "enterprise"]
    if context["complexity_level"] not in valid_complexities:
        raise ValidationError(
            f"Invalid complexity level: {context['complexity_level']}"
        )
    
    # Validate lists are not empty for critical fields
    if not context["languages"]:
        raise ValidationError("At least one language must be specified")
    
    logger.debug("Project context validation successful")


def validate_technical_context(context: TechnicalContext) -> None:
    """
    Validate technical context data structure
    
    Args:
        context: Technical context to validate
        
    Raises:
        ValidationError: If context is invalid
    """
    logger.debug(f"Validating technical context for phase: {context.get('phase')}")
    
    required_fields = [
        "phase", "primary_language", "deployment_target", 
        "testing_strategy", "ci_cd_integration"
    ]
    
    for field in required_fields:
        if field not in context:
            raise ValidationError(f"Required field missing in technical context: {field}")
    
    # Validate deployment target
    if context["deployment_target"] not in ["cloud", "traditional"]:
        raise ValidationError(
            f"Invalid deployment target: {context['deployment_target']}"
        )
    
    # Validate testing strategy
    if context["testing_strategy"] not in ["comprehensive", "basic"]:
        raise ValidationError(
            f"Invalid testing strategy: {context['testing_strategy']}"
        )
    
    logger.debug(f"Technical context validation successful for phase: {context['phase']}")


def validate_example(example: Example) -> None:
    """
    Validate example data structure
    
    Args:
        example: Example to validate
        
    Raises:
        ValidationError: If example is invalid
    """
    required_fields = ["title", "purpose", "language", "code", "notes"]
    
    for field in required_fields:
        if field not in example or not example[field]:
            raise ValidationError(f"Required field missing in example: {field}")
    
    # Validate language is not empty
    if not example["language"].strip():
        raise ValidationError("Example language cannot be empty")
    
    # Validate code is not empty
    if not example["code"].strip():
        raise ValidationError("Example code cannot be empty")


def validate_pattern(pattern: Pattern) -> None:
    """
    Validate pattern data structure
    
    Args:
        pattern: Pattern to validate
        
    Raises:
        ValidationError: If pattern is invalid
    """
    required_fields = ["name", "purpose", "implementation", "benefits", "examples"]
    
    for field in required_fields:
        if field not in pattern or not pattern[field]:
            raise ValidationError(f"Required field missing in pattern: {field}")
    
    # Validate lists are not empty
    if not pattern["benefits"]:
        raise ValidationError("Pattern must have at least one benefit")
    
    if not pattern["examples"]:
        raise ValidationError("Pattern must have at least one example")


def validate_validation_gate(gate: ValidationGate) -> None:
    """
    Validate validation gate data structure
    
    Args:
        gate: Validation gate to validate
        
    Raises:
        ValidationError: If validation gate is invalid
    """
    required_fields = ["name", "test", "command", "expected", "on_failure"]
    
    for field in required_fields:
        if field not in gate or not gate[field]:
            raise ValidationError(f"Required field missing in validation gate: {field}")
    
    # If type is specified, validate it
    if "type" in gate:
        valid_types = ["syntax", "semantic", "security", "performance"]
        if gate["type"] not in valid_types:
            raise ValidationError(f"Invalid validation gate type: {gate['type']}")
    
    # If severity is specified, validate it
    if "severity" in gate:
        valid_severities = ["critical", "high", "medium", "low"]
        if gate["severity"] not in valid_severities:
            raise ValidationError(f"Invalid validation gate severity: {gate['severity']}")


def validate_context_package_data(
    project_context: ProjectContext,
    technical_context: TechnicalContext,
    examples: List[Example],
    patterns: List[Pattern],
    validation_gates: List[ValidationGate]
) -> None:
    """
    Validate all components of a context package
    
    Args:
        project_context: Project context to validate
        technical_context: Technical context to validate
        examples: List of examples to validate
        patterns: List of patterns to validate
        validation_gates: List of validation gates to validate
        
    Raises:
        ValidationError: If any component is invalid
    """
    logger.info("Validating complete context package")
    
    # Validate individual components
    validate_project_context(project_context)
    validate_technical_context(technical_context)
    
    # Validate lists
    for example in examples:
        validate_example(example)
    
    for pattern in patterns:
        validate_pattern(pattern)
    
    for gate in validation_gates:
        validate_validation_gate(gate)
    
    logger.info("Context package validation successful")