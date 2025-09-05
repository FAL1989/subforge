#!/usr/bin/env python3
"""
Context Enricher - Enriches context with guidelines, constraints, and best practices
"""

import logging
from typing import List, Dict, Any

from .types import TechnicalContext, ValidationGate
from ..project_analyzer import ProjectProfile

logger = logging.getLogger(__name__)


class ContextEnricher:
    """Enriches context with additional metadata and guidelines"""

    def __init__(self):
        self._guidelines_registry = self._initialize_guidelines()
        self._constraints_registry = self._initialize_constraints()
        self._best_practices_registry = self._initialize_best_practices()

    def enrich_with_guidelines(
        self, context: TechnicalContext, architecture: str
    ) -> TechnicalContext:
        """Add architecture-specific guidelines to context"""
        guidelines = self._guidelines_registry.get(
            architecture, self._guidelines_registry["default"]
        )
        
        context["architectural_guidelines"] = guidelines
        
        # Add specific guidelines based on architecture
        if architecture == "microservices":
            context["service_guidelines"] = [
                "Each service owns its data",
                "Services communicate through well-defined APIs",
                "Implement circuit breakers for resilience",
                "Use service discovery for dynamic routing",
            ]
        elif architecture == "serverless":
            context["function_guidelines"] = [
                "Keep functions small and focused",
                "Design for statelessness",
                "Optimize cold start performance",
                "Use managed services for state",
            ]
        elif architecture == "monolithic":
            context["module_guidelines"] = [
                "Maintain clear module boundaries",
                "Use dependency injection",
                "Keep database transactions consistent",
                "Implement caching strategically",
            ]
            
        return context

    def enrich_with_constraints(
        self, context: TechnicalContext, profile: ProjectProfile
    ) -> TechnicalContext:
        """Add project-specific constraints to context"""
        constraints = []
        
        # Size constraints
        if profile.file_count > 1000:
            constraints.append("Large codebase - focus on modularity and organization")
        if profile.lines_of_code > 100000:
            constraints.append("Enterprise scale - emphasize documentation and standards")
            
        # Technology constraints
        if "python" in [l.lower() for l in profile.technology_stack.languages]:
            constraints.append("Python - maintain PEP 8 compliance")
        if "typescript" in [l.lower() for l in profile.technology_stack.languages]:
            constraints.append("TypeScript - enforce strict type checking")
            
        # Infrastructure constraints
        if profile.has_docker:
            constraints.append("Containerized - ensure Docker best practices")
        if profile.has_ci_cd:
            constraints.append("CI/CD enabled - maintain pipeline compatibility")
            
        context["project_constraints"] = constraints
        return context

    def enrich_with_best_practices(
        self, context: TechnicalContext
    ) -> TechnicalContext:
        """Add general best practices to context"""
        phase = context.get("phase", "")
        
        best_practices = self._best_practices_registry.get(
            phase, self._best_practices_registry["default"]
        )
        
        context["best_practices"] = best_practices
        
        # Add specific practices based on context
        if context.get("testing_strategy") == "comprehensive":
            context["testing_practices"] = [
                "Write tests before fixing bugs",
                "Maintain test coverage above 80%",
                "Use test doubles for external dependencies",
                "Implement integration tests for critical paths",
            ]
            
        if context.get("ci_cd_integration"):
            context["ci_cd_practices"] = [
                "Run tests on every commit",
                "Automate code quality checks",
                "Use feature flags for gradual rollouts",
                "Implement rollback mechanisms",
            ]
            
        return context

    def enrich_with_references(
        self, profile: ProjectProfile, phase: str
    ) -> List[str]:
        """Build list of relevant references and documentation"""
        references = []

        # Language-specific references
        for lang in profile.technology_stack.languages:
            lang_lower = lang.lower()
            if lang_lower == "python":
                references.extend([
                    "https://pep8.org/ - Python Style Guide",
                    "https://docs.python.org/3/ - Python Documentation",
                    "https://pytest.org/ - Testing Framework",
                ])
            elif lang_lower == "javascript":
                references.extend([
                    "https://developer.mozilla.org/en-US/docs/Web/JavaScript - MDN JavaScript",
                    "https://nodejs.org/en/docs/ - Node.js Documentation",
                    "https://jestjs.io/ - Testing Framework",
                ])
            elif lang_lower == "typescript":
                references.extend([
                    "https://www.typescriptlang.org/docs/ - TypeScript Documentation",
                    "https://github.com/microsoft/TypeScript/wiki/Coding-guidelines - TS Guidelines",
                ])

        # Framework-specific references
        for framework in profile.technology_stack.frameworks:
            fw_lower = framework.lower()
            if fw_lower == "fastapi":
                references.append("https://fastapi.tiangolo.com/ - FastAPI Documentation")
            elif fw_lower == "react":
                references.append("https://reactjs.org/docs - React Documentation")
            elif fw_lower == "nextjs":
                references.append("https://nextjs.org/docs - Next.js Documentation")
            elif fw_lower == "django":
                references.append("https://docs.djangoproject.com/ - Django Documentation")
            elif fw_lower == "vue":
                references.append("https://vuejs.org/guide/ - Vue.js Documentation")

        return references

    def define_success_criteria(
        self, phase: str, profile: ProjectProfile
    ) -> List[str]:
        """Define clear success criteria for the phase"""
        criteria = []

        if phase == "analysis":
            criteria.extend([
                "Project structure is fully analyzed and documented",
                "Technology stack is accurately identified",
                "Architecture pattern is correctly classified",
                "Team size and complexity are appropriately estimated",
                "Dependencies are mapped and understood",
            ])
        elif phase == "generation":
            criteria.extend([
                "CLAUDE.md is generated with project-specific configuration",
                "All selected agents are properly configured",
                "Workflows are tailored to project architecture",
                "Commands are functional for the detected tech stack",
                "All generated files pass validation gates",
                "Documentation is clear and actionable",
            ])
        elif phase == "selection":
            criteria.extend([
                "Appropriate templates selected for project complexity",
                "All required agent roles are identified",
                "Workflows match architecture pattern",
                "Customization requirements are documented",
                "Template compatibility is verified",
            ])
        elif phase == "validation":
            criteria.extend([
                "All syntax validation passes",
                "Semantic validation confirms correctness",
                "Integration points are verified",
                "Performance benchmarks are met",
                "Security checks pass",
            ])

        # Add complexity-specific criteria
        if profile.complexity.value == "complex":
            criteria.append("Enterprise standards are met")
            criteria.append("Scalability requirements are addressed")
        
        if profile.team_size_estimate > 5:
            criteria.append("Team collaboration workflows are defined")
            criteria.append("Code review process is established")

        return criteria

    def create_validation_gates(
        self, phase: str, profile: ProjectProfile
    ) -> List[ValidationGate]:
        """Create executable validation gates for the phase"""
        gates: List[ValidationGate] = []

        if phase == "generation":
            gates.append(
                ValidationGate(
                    name="CLAUDE.md Syntax Validation",
                    test="Validate CLAUDE.md file syntax and completeness",
                    command="python -c \"import yaml; yaml.safe_load(open('CLAUDE.md'))\"",
                    expected="No syntax errors",
                    on_failure="Fix CLAUDE.md syntax issues and re-run generation",
                    type="syntax",
                    severity="critical",
                )
            )

            gates.append(
                ValidationGate(
                    name="Agent Configuration Validation",
                    test="Verify all generated agents have valid YAML frontmatter",
                    command="find .claude/agents -name '*.md' -exec python -c \"import yaml,sys; yaml.safe_load(open(sys.argv[1]).read().split('---')[1])\" {} \\;",
                    expected="All agent files parse successfully",
                    on_failure="Fix invalid agent configurations",
                    type="syntax",
                    severity="high",
                )
            )

            if profile.has_tests:
                gates.append(
                    ValidationGate(
                        name="Test Coverage Check",
                        test="Verify test coverage meets minimum threshold",
                        command="pytest --cov=. --cov-report=term-missing",
                        expected="Coverage above 80%",
                        on_failure="Add more tests to improve coverage",
                        type="semantic",
                        severity="medium",
                    )
                )

            if profile.has_docker:
                gates.append(
                    ValidationGate(
                        name="Docker Build Validation",
                        test="Verify Docker image builds successfully",
                        command="docker build -t test-build .",
                        expected="Build completes without errors",
                        on_failure="Fix Dockerfile issues",
                        type="integration",
                        severity="high",
                    )
                )

        elif phase == "analysis":
            gates.append(
                ValidationGate(
                    name="Project Structure Validation",
                    test="Verify project structure is analyzable",
                    command="find . -type f -name '*.py' -o -name '*.js' -o -name '*.ts' | head -n 1",
                    expected="At least one source file found",
                    on_failure="Ensure project contains source code",
                    type="semantic",
                    severity="critical",
                )
            )

        return gates

    def _initialize_guidelines(self) -> Dict[str, List[str]]:
        """Initialize architectural guidelines registry"""
        return {
            "microservices": [
                "Design services around business capabilities",
                "Decentralize data management",
                "Design for failure",
                "Implement smart endpoints and dumb pipes",
            ],
            "serverless": [
                "Embrace event-driven design",
                "Optimize for cost and performance",
                "Use managed services",
                "Design for statelessness",
            ],
            "monolithic": [
                "Maintain clear module boundaries",
                "Use layered architecture",
                "Centralize cross-cutting concerns",
                "Optimize database access",
            ],
            "default": [
                "Follow SOLID principles",
                "Keep it simple (KISS)",
                "Don't repeat yourself (DRY)",
                "You aren't gonna need it (YAGNI)",
            ],
        }

    def _initialize_constraints(self) -> Dict[str, List[str]]:
        """Initialize constraints registry"""
        return {
            "performance": [
                "Response time under 200ms",
                "Support 1000+ concurrent users",
                "Database queries optimized",
            ],
            "security": [
                "All inputs validated",
                "Authentication required",
                "Data encrypted at rest and in transit",
            ],
            "scalability": [
                "Horizontal scaling support",
                "Stateless design",
                "Cache implementation",
            ],
        }

    def _initialize_best_practices(self) -> Dict[str, List[str]]:
        """Initialize best practices registry"""
        return {
            "generation": [
                "Generate clear, maintainable code",
                "Include comprehensive documentation",
                "Follow project conventions",
                "Add helpful comments",
            ],
            "analysis": [
                "Thorough dependency analysis",
                "Accurate complexity assessment",
                "Complete technology stack identification",
            ],
            "selection": [
                "Choose appropriate templates",
                "Consider project constraints",
                "Plan for scalability",
            ],
            "default": [
                "Code clarity over cleverness",
                "Test early and often",
                "Document decisions",
                "Review before merge",
            ],
        }