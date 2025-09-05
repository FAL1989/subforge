#!/usr/bin/env python3
"""
Type definitions for Context Engineering module
Provides strong typing for all context-related data structures
"""

from typing import TypedDict, List, Optional, Literal, NotRequired
from datetime import datetime


class TechStack(TypedDict):
    """Technology stack configuration"""
    languages: List[str]
    frameworks: List[str]
    databases: List[str]
    tools: List[str]


class ProjectContext(TypedDict):
    """Complete project context information"""
    name: str
    path: str
    architecture_pattern: str
    complexity_level: Literal["simple", "medium", "complex", "enterprise"]
    languages: List[str]
    frameworks: List[str]
    databases: List[str]
    tools: List[str]
    team_size_estimate: int
    has_tests: bool
    has_ci_cd: bool
    has_docker: bool
    file_count: int
    lines_of_code: int


class TechnicalContext(TypedDict):
    """Phase-specific technical context"""
    phase: str
    primary_language: str
    deployment_target: Literal["cloud", "traditional"]
    testing_strategy: Literal["comprehensive", "basic"]
    ci_cd_integration: bool
    # Phase-specific optional fields
    analysis_depth: NotRequired[Literal["deep", "standard"]]
    discovery_areas: NotRequired[List[str]]
    template_criteria: NotRequired[List[str]]
    customization_level: NotRequired[Literal["high", "medium", "low"]]
    generation_targets: NotRequired[List[str]]
    customization_required: NotRequired[bool]
    integration_complexity: NotRequired[str]


class Example(TypedDict):
    """Code example with metadata"""
    title: str
    purpose: str
    language: str
    code: str
    notes: str
    framework: NotRequired[Optional[str]]
    tags: NotRequired[List[str]]


class Pattern(TypedDict):
    """Design pattern specification"""
    name: str
    purpose: str
    implementation: str
    benefits: List[str]
    examples: List[str]
    applicability: NotRequired[str]
    description: NotRequired[str]


class ValidationGate(TypedDict):
    """Validation gate configuration"""
    name: str
    test: str
    command: str
    expected: str
    on_failure: str
    type: NotRequired[Literal["syntax", "semantic", "security", "performance"]]
    severity: NotRequired[Literal["critical", "high", "medium", "low"]]


class PreviousOutput(TypedDict):
    """Structure for phase outputs passed between stages"""
    phase: str
    timestamp: str
    success: bool
    data: dict
    errors: NotRequired[List[str]]


class ContextPackageDict(TypedDict):
    """Serializable context package data"""
    project_context: ProjectContext
    technical_context: TechnicalContext
    examples: List[Example]
    patterns: List[Pattern]
    validation_gates: List[ValidationGate]
    references: List[str]
    success_criteria: List[str]
    generated_at: str