#!/usr/bin/env python3
"""
Pattern Extractor - Extracts and manages implementation patterns
"""

import logging
from typing import List, Optional
from enum import Enum

from .types import Pattern
from ..project_analyzer import ProjectProfile

logger = logging.getLogger(__name__)


class ContextLevel(Enum):
    """Different levels of context engineering depth"""
    MINIMAL = "minimal"  # Basic project info
    STANDARD = "standard"  # Comprehensive analysis
    DEEP = "deep"  # Full context with examples and patterns
    EXPERT = "expert"  # Advanced patterns with validation


class PatternExtractor:
    """Extracts relevant patterns based on project characteristics"""

    def __init__(self):
        self._pattern_registry = self._initialize_pattern_registry()

    def extract_from_profile(
        self,
        profile: ProjectProfile,
        phase: str,
        context_level: ContextLevel = ContextLevel.STANDARD
    ) -> List[Pattern]:
        """Extract patterns based on project profile and context level"""
        patterns: List[Pattern] = []

        # Base patterns for all levels
        patterns.extend(self._get_base_patterns(profile, phase))

        # Add advanced patterns for deeper context levels
        if context_level in [ContextLevel.DEEP, ContextLevel.EXPERT]:
            patterns.extend(self._get_advanced_patterns(profile, phase))

        # Add expert patterns for highest level
        if context_level == ContextLevel.EXPERT:
            patterns.extend(self._get_expert_patterns(profile, phase))

        return patterns

    def extract_from_architecture(
        self, architecture: str, phase: str
    ) -> List[Pattern]:
        """Extract architecture-specific patterns"""
        patterns: List[Pattern] = []

        if architecture == "microservices":
            patterns.append(self._create_microservices_pattern(phase))
        elif architecture == "serverless":
            patterns.append(self._create_serverless_pattern(phase))
        elif architecture == "monolithic":
            patterns.append(self._create_monolithic_pattern(phase))
        elif architecture == "event-driven":
            patterns.append(self._create_event_driven_pattern(phase))

        return patterns

    def extract_from_frameworks(
        self, frameworks: List[str], phase: str
    ) -> List[Pattern]:
        """Extract framework-specific patterns"""
        patterns: List[Pattern] = []

        for framework in frameworks:
            framework_lower = framework.lower()
            
            if framework_lower in ["react", "vue", "angular"]:
                patterns.append(self._create_spa_pattern(framework, phase))
            elif framework_lower in ["django", "fastapi", "flask"]:
                patterns.append(self._create_api_pattern(framework, phase))
            elif framework_lower in ["nextjs", "nuxt", "sveltekit"]:
                patterns.append(self._create_fullstack_pattern(framework, phase))

        return patterns

    def _initialize_pattern_registry(self) -> dict:
        """Initialize registry of common patterns"""
        return {
            "separation_of_concerns": Pattern(
                name="Separation of Concerns",
                purpose="Maintain clear boundaries between different aspects of the system",
                implementation="Use distinct modules for business logic, data access, and presentation",
                benefits=["Maintainability", "Testability", "Reusability"],
                examples=["MVC pattern", "Clean Architecture", "Hexagonal Architecture"],
            ),
            "dependency_injection": Pattern(
                name="Dependency Injection",
                purpose="Reduce coupling and improve testability",
                implementation="Pass dependencies as parameters rather than creating them internally",
                benefits=["Testability", "Flexibility", "Decoupling"],
                examples=["Constructor injection", "Interface injection", "Service locator"],
            ),
            "repository_pattern": Pattern(
                name="Repository Pattern",
                purpose="Abstract data access logic",
                implementation="Create repository interfaces that hide data access implementation",
                benefits=["Testability", "Flexibility", "Consistency"],
                examples=["UserRepository", "OrderRepository", "Generic Repository<T>"],
            ),
        }

    def _get_base_patterns(
        self, profile: ProjectProfile, phase: str
    ) -> List[Pattern]:
        """Get base patterns applicable to most projects"""
        patterns: List[Pattern] = []

        if phase == "generation":
            patterns.append(
                Pattern(
                    name="Agent Specialization Pattern",
                    purpose="Create highly specialized agents for optimal performance",
                    implementation="Focus each agent on a specific domain with minimal overlap",
                    benefits=[
                        "Clearer responsibilities",
                        "Better context",
                        "Reduced conflicts",
                    ],
                    examples=[
                        "api-developer for REST APIs",
                        "database-specialist for data models",
                        "frontend-developer for UI components",
                    ],
                )
            )

            if profile.team_size_estimate > 3:
                patterns.append(
                    Pattern(
                        name="Team Coordination Pattern",
                        purpose="Coordinate multiple agents effectively",
                        implementation="Use orchestrator for complex multi-agent workflows",
                        benefits=[
                            "Parallel execution",
                            "Clear handoffs",
                            "Progress tracking",
                        ],
                        examples=[
                            "Feature development workflow",
                            "Bug fix coordination",
                            "Release preparation",
                        ],
                    )
                )

        return patterns

    def _get_advanced_patterns(
        self, profile: ProjectProfile, phase: str
    ) -> List[Pattern]:
        """Get advanced implementation patterns"""
        patterns: List[Pattern] = []

        if phase == "generation" and profile.has_tests:
            patterns.append(
                Pattern(
                    name="Test-Driven Development Pattern",
                    purpose="Ensure code quality through comprehensive testing",
                    implementation="Write tests before implementation, maintain high coverage",
                    benefits=[
                        "Bug prevention",
                        "Design improvement",
                        "Documentation",
                        "Refactoring safety",
                    ],
                    examples=[
                        "Unit tests for business logic",
                        "Integration tests for APIs",
                        "E2E tests for critical paths",
                    ],
                )
            )

        if profile.has_ci_cd:
            patterns.append(
                Pattern(
                    name="Continuous Integration Pattern",
                    purpose="Maintain code quality through automated validation",
                    implementation="Run tests and checks on every commit",
                    benefits=[
                        "Early bug detection",
                        "Code quality maintenance",
                        "Team productivity",
                    ],
                    examples=[
                        "GitHub Actions workflows",
                        "GitLab CI pipelines",
                        "Jenkins jobs",
                    ],
                )
            )

        return patterns

    def _get_expert_patterns(
        self, profile: ProjectProfile, phase: str
    ) -> List[Pattern]:
        """Get expert-level implementation patterns"""
        patterns: List[Pattern] = []

        if profile.complexity.value == "complex":
            patterns.append(
                Pattern(
                    name="Enterprise Coordination Pattern",
                    purpose="Manage complex agent interactions in enterprise environments",
                    implementation="Use formal handoff protocols with validation gates",
                    benefits=[
                        "Audit trails",
                        "Error recovery",
                        "Scalability",
                        "Compliance",
                    ],
                    examples=[
                        "Formal code review workflows",
                        "Multi-stage validation",
                        "Approval chains",
                    ],
                )
            )

            patterns.append(
                Pattern(
                    name="Domain-Driven Design Pattern",
                    purpose="Align software with business domains",
                    implementation="Model business domains explicitly in code structure",
                    benefits=[
                        "Business alignment",
                        "Clear boundaries",
                        "Ubiquitous language",
                    ],
                    examples=[
                        "Bounded contexts",
                        "Aggregates",
                        "Domain events",
                    ],
                )
            )

        if profile.architecture_pattern.value == "microservices":
            patterns.append(
                Pattern(
                    name="Service Mesh Pattern",
                    purpose="Manage microservices communication and observability",
                    implementation="Use service mesh for traffic management and monitoring",
                    benefits=[
                        "Observability",
                        "Security",
                        "Traffic management",
                        "Resilience",
                    ],
                    examples=["Istio", "Linkerd", "Consul Connect"],
                )
            )

        return patterns

    def _create_microservices_pattern(self, phase: str) -> Pattern:
        """Create microservices-specific pattern"""
        return Pattern(
            name="Microservices Communication Pattern",
            purpose="Enable efficient inter-service communication",
            implementation="Use API gateways, service discovery, and circuit breakers",
            benefits=[
                "Resilience",
                "Scalability",
                "Service isolation",
                "Independent deployment",
            ],
            examples=[
                "REST APIs with OpenAPI",
                "gRPC for internal communication",
                "Event-driven with message queues",
            ],
        )

    def _create_serverless_pattern(self, phase: str) -> Pattern:
        """Create serverless-specific pattern"""
        return Pattern(
            name="Serverless Event Pattern",
            purpose="Design event-driven serverless architectures",
            implementation="Use events to trigger functions, maintain stateless design",
            benefits=[
                "Cost efficiency",
                "Automatic scaling",
                "Reduced operations",
                "Event-driven design",
            ],
            examples=[
                "Lambda with API Gateway",
                "Event Bridge for orchestration",
                "Step Functions for workflows",
            ],
        )

    def _create_monolithic_pattern(self, phase: str) -> Pattern:
        """Create monolithic-specific pattern"""
        return Pattern(
            name="Modular Monolith Pattern",
            purpose="Maintain modularity within monolithic architecture",
            implementation="Use clear module boundaries and dependency rules",
            benefits=[
                "Simplicity",
                "Easy deployment",
                "Shared resources",
                "Consistent transactions",
            ],
            examples=[
                "Package by feature",
                "Layered architecture",
                "Domain modules",
            ],
        )

    def _create_event_driven_pattern(self, phase: str) -> Pattern:
        """Create event-driven architecture pattern"""
        return Pattern(
            name="Event Sourcing Pattern",
            purpose="Capture all changes as events",
            implementation="Store events instead of state, rebuild state from events",
            benefits=[
                "Audit trail",
                "Time travel",
                "Event replay",
                "CQRS compatibility",
            ],
            examples=[
                "Event store",
                "Projections",
                "Snapshots",
            ],
        )

    def _create_spa_pattern(self, framework: str, phase: str) -> Pattern:
        """Create SPA framework pattern"""
        return Pattern(
            name=f"{framework.title()} Component Pattern",
            purpose=f"Build reusable {framework} components",
            implementation="Create atomic, composable components with clear props",
            benefits=[
                "Reusability",
                "Testability",
                "Maintainability",
                "Consistency",
            ],
            examples=[
                "Atomic design",
                "Container/Presentational",
                "Compound components",
            ],
        )

    def _create_api_pattern(self, framework: str, phase: str) -> Pattern:
        """Create API framework pattern"""
        return Pattern(
            name=f"{framework.title()} API Pattern",
            purpose=f"Build robust APIs with {framework}",
            implementation="Use framework best practices for API design",
            benefits=[
                "Consistency",
                "Documentation",
                "Validation",
                "Security",
            ],
            examples=[
                "RESTful endpoints",
                "Request validation",
                "Error handling",
                "Authentication",
            ],
        )

    def _create_fullstack_pattern(self, framework: str, phase: str) -> Pattern:
        """Create fullstack framework pattern"""
        return Pattern(
            name=f"{framework.title()} Fullstack Pattern",
            purpose=f"Build fullstack applications with {framework}",
            implementation="Leverage SSR/SSG capabilities and API routes",
            benefits=[
                "SEO optimization",
                "Performance",
                "Developer experience",
                "Type safety",
            ],
            examples=[
                "Server components",
                "API routes",
                "Static generation",
                "Incremental regeneration",
            ],
        )