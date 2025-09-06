#!/usr/bin/env python3
"""
Test suite for Context Enricher module
Tests enrichment pipeline, guidelines, constraints, and best practices
"""

import pytest
from unittest.mock import Mock

from subforge.core.context.enricher import ContextEnricher
from subforge.core.context.types import TechnicalContext, ValidationGate
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity,
)


class TestContextEnricher:
    """Test ContextEnricher functionality"""
    
    @pytest.fixture
    def enricher(self):
        """Create ContextEnricher instance"""
        return ContextEnricher()
    
    @pytest.fixture
    def base_context(self):
        """Create base technical context"""
        return TechnicalContext(
            phase="generation",
            primary_language="python",
            deployment_target="cloud",
            testing_strategy="comprehensive",
            ci_cd_integration=True
        )
    
    @pytest.fixture
    def mock_profile(self):
        """Create mock project profile"""
        profile = Mock(spec=ProjectProfile)
        profile.name = "test-project"
        profile.technology_stack = TechnologyStack(
            languages={"python", "typescript"},
            frameworks={"fastapi", "react"},
            databases={"postgresql"},
            tools={"docker"},
            package_managers={"pip", "npm"},
        )
        profile.architecture_pattern = ArchitecturePattern.MICROSERVICES
        profile.complexity = ProjectComplexity.COMPLEX
        profile.file_count = 1500
        profile.lines_of_code = 150000
        profile.has_tests = True
        profile.has_ci_cd = True
        profile.has_docker = True
        profile.team_size_estimate = 6  # Add missing attribute
        return profile
    
    def test_guideline_enrichment_microservices(self, enricher, base_context):
        """Test architecture guidelines enrichment for microservices"""
        enriched = enricher.enrich_with_guidelines(base_context, "microservices")
        
        assert "architectural_guidelines" in enriched
        assert "service_guidelines" in enriched
        
        guidelines = enriched["architectural_guidelines"]
        assert any("business capabilities" in g for g in guidelines)
        assert any("data management" in g for g in guidelines)
        
        service_guidelines = enriched["service_guidelines"]
        assert "Each service owns its data" in service_guidelines
        assert "Services communicate through well-defined APIs" in service_guidelines
    
    def test_guideline_enrichment_serverless(self, enricher, base_context):
        """Test architecture guidelines enrichment for serverless"""
        enriched = enricher.enrich_with_guidelines(base_context, "serverless")
        
        assert "architectural_guidelines" in enriched
        assert "function_guidelines" in enriched
        
        function_guidelines = enriched["function_guidelines"]
        assert "Keep functions small and focused" in function_guidelines
        assert "Design for statelessness" in function_guidelines
    
    def test_guideline_enrichment_monolithic(self, enricher, base_context):
        """Test architecture guidelines enrichment for monolithic"""
        enriched = enricher.enrich_with_guidelines(base_context, "monolithic")
        
        assert "architectural_guidelines" in enriched
        assert "module_guidelines" in enriched
        
        module_guidelines = enriched["module_guidelines"]
        assert "Maintain clear module boundaries" in module_guidelines
        assert "Use dependency injection" in module_guidelines
    
    def test_guideline_enrichment_default(self, enricher, base_context):
        """Test default architecture guidelines"""
        enriched = enricher.enrich_with_guidelines(base_context, "unknown_architecture")
        
        assert "architectural_guidelines" in enriched
        guidelines = enriched["architectural_guidelines"]
        assert any("SOLID" in g for g in guidelines)
        assert any("KISS" in g for g in guidelines)
        assert any("DRY" in g for g in guidelines)
    
    def test_constraint_enrichment_large_codebase(self, enricher, base_context, mock_profile):
        """Test project constraints enrichment for large codebases"""
        enriched = enricher.enrich_with_constraints(base_context, mock_profile)
        
        assert "project_constraints" in enriched
        constraints = enriched["project_constraints"]
        
        assert "Large codebase - focus on modularity and organization" in constraints
        assert "Enterprise scale - emphasize documentation and standards" in constraints
    
    def test_constraint_enrichment_python(self, enricher, base_context):
        """Test constraints for Python projects"""
        profile = Mock(spec=ProjectProfile)
        profile.technology_stack = TechnologyStack(
            languages={"python"},
            frameworks=set(),
            databases=set(),
            tools=set(),
            package_managers={"pip"},
        )
        profile.file_count = 100
        profile.lines_of_code = 10000
        profile.has_docker = False
        profile.has_ci_cd = False
        
        enriched = enricher.enrich_with_constraints(base_context, profile)
        constraints = enriched["project_constraints"]
        
        assert "Python - maintain PEP 8 compliance" in constraints
    
    def test_constraint_enrichment_typescript(self, enricher, base_context):
        """Test constraints for TypeScript projects"""
        profile = Mock(spec=ProjectProfile)
        profile.technology_stack = TechnologyStack(
            languages={"TypeScript"},
            frameworks=set(),
            databases=set(),
            tools=set(),
            package_managers={"npm"},
        )
        profile.file_count = 100
        profile.lines_of_code = 10000
        profile.has_docker = False
        profile.has_ci_cd = False
        
        enriched = enricher.enrich_with_constraints(base_context, profile)
        constraints = enriched["project_constraints"]
        
        assert "TypeScript - enforce strict type checking" in constraints
    
    def test_constraint_enrichment_infrastructure(self, enricher, base_context, mock_profile):
        """Test infrastructure constraints"""
        enriched = enricher.enrich_with_constraints(base_context, mock_profile)
        constraints = enriched["project_constraints"]
        
        assert "Containerized - ensure Docker best practices" in constraints
        assert "CI/CD enabled - maintain pipeline compatibility" in constraints
    
    def test_best_practices_enrichment_generation(self, enricher, base_context):
        """Test best practices enrichment for generation phase"""
        base_context["phase"] = "generation"
        enriched = enricher.enrich_with_best_practices(base_context)
        
        assert "best_practices" in enriched
        practices = enriched["best_practices"]
        
        assert "Generate clear, maintainable code" in practices
        assert "Include comprehensive documentation" in practices
    
    def test_best_practices_enrichment_analysis(self, enricher):
        """Test best practices enrichment for analysis phase"""
        context = TechnicalContext(
            phase="analysis",
            primary_language="python",
            deployment_target="cloud",
            testing_strategy="basic",
            ci_cd_integration=False
        )
        
        enriched = enricher.enrich_with_best_practices(context)
        practices = enriched["best_practices"]
        
        assert "Thorough dependency analysis" in practices
        assert "Accurate complexity assessment" in practices
    
    def test_best_practices_enrichment_testing(self, enricher, base_context):
        """Test testing practices enrichment"""
        enriched = enricher.enrich_with_best_practices(base_context)
        
        assert "testing_practices" in enriched
        practices = enriched["testing_practices"]
        
        assert "Write tests before fixing bugs" in practices
        assert "Maintain test coverage above 80%" in practices
    
    def test_best_practices_enrichment_cicd(self, enricher, base_context):
        """Test CI/CD practices enrichment"""
        enriched = enricher.enrich_with_best_practices(base_context)
        
        assert "ci_cd_practices" in enriched
        practices = enriched["ci_cd_practices"]
        
        assert "Run tests on every commit" in practices
        assert "Automate code quality checks" in practices
    
    def test_enrichment_pipeline(self, enricher, base_context, mock_profile):
        """Test full enrichment flow"""
        # Apply all enrichments in sequence
        context = enricher.enrich_with_guidelines(base_context, "microservices")
        context = enricher.enrich_with_constraints(context, mock_profile)
        context = enricher.enrich_with_best_practices(context)
        
        # Verify all enrichments are present
        assert "architectural_guidelines" in context
        assert "service_guidelines" in context
        assert "project_constraints" in context
        assert "best_practices" in context
        assert "testing_practices" in context
        assert "ci_cd_practices" in context
    
    def test_enrichment_validation(self, enricher, base_context):
        """Test validation during enrichment"""
        # Test that enrichment doesn't override existing fields
        base_context["custom_field"] = "custom_value"
        
        enriched = enricher.enrich_with_guidelines(base_context, "microservices")
        
        assert enriched["custom_field"] == "custom_value"
        assert "architectural_guidelines" in enriched
    
    def test_references_generation_python(self, enricher):
        """Test reference generation for Python projects"""
        profile = Mock(spec=ProjectProfile)
        profile.technology_stack = TechnologyStack(
            languages={"python"},
            frameworks={"fastapi"},
            databases=set(),
            tools=set(),
            package_managers={"pip"},
        )
        
        references = enricher.enrich_with_references(profile, "generation")
        
        assert any("pep8.org" in ref for ref in references)
        assert any("python.org" in ref for ref in references)
        assert any("pytest.org" in ref for ref in references)
        assert any("fastapi" in ref.lower() for ref in references)
    
    def test_references_generation_javascript(self, enricher):
        """Test reference generation for JavaScript projects"""
        profile = Mock(spec=ProjectProfile)
        profile.technology_stack = TechnologyStack(
            languages={"javascript"},
            frameworks={"react"},
            databases=set(),
            tools=set(),
            package_managers={"npm"},
        )
        
        references = enricher.enrich_with_references(profile, "generation")
        
        assert any("developer.mozilla.org" in ref for ref in references)
        assert any("nodejs.org" in ref for ref in references)
        assert any("jestjs.io" in ref for ref in references)
        assert any("reactjs.org" in ref for ref in references)
    
    def test_success_criteria_analysis_phase(self, enricher, mock_profile):
        """Test success criteria for analysis phase"""
        criteria = enricher.define_success_criteria("analysis", mock_profile)
        
        assert "Project structure is fully analyzed and documented" in criteria
        assert "Technology stack is accurately identified" in criteria
        assert "Architecture pattern is correctly classified" in criteria
        assert "Enterprise standards are met" in criteria  # Due to complex profile
        assert "Team collaboration workflows are defined" in criteria  # Team size > 5
    
    def test_success_criteria_generation_phase(self, enricher, mock_profile):
        """Test success criteria for generation phase"""
        criteria = enricher.define_success_criteria("generation", mock_profile)
        
        assert "CLAUDE.md is generated with project-specific configuration" in criteria
        assert "All selected agents are properly configured" in criteria
        assert "All generated files pass validation gates" in criteria
        assert "Enterprise standards are met" in criteria
    
    def test_validation_gates_generation(self, enricher, mock_profile):
        """Test validation gate creation for generation phase"""
        gates = enricher.create_validation_gates("generation", mock_profile)
        
        assert len(gates) > 0
        
        # Check for specific gates
        gate_names = [g["name"] for g in gates]
        assert "CLAUDE.md Syntax Validation" in gate_names
        assert "Agent Configuration Validation" in gate_names
        assert "Test Coverage Check" in gate_names
        assert "Docker Build Validation" in gate_names
        
        # Verify gate structure
        for gate in gates:
            assert "name" in gate
            assert "test" in gate
            assert "command" in gate
            assert "expected" in gate
            assert "on_failure" in gate
            assert "type" in gate
            assert "severity" in gate
    
    def test_validation_gates_analysis(self, enricher, mock_profile):
        """Test validation gate creation for analysis phase"""
        gates = enricher.create_validation_gates("analysis", mock_profile)
        
        assert len(gates) > 0
        
        gate_names = [g["name"] for g in gates]
        assert "Project Structure Validation" in gate_names
    
    def test_registry_initialization(self, enricher):
        """Test that all registries are properly initialized"""
        assert enricher._guidelines_registry is not None
        assert "microservices" in enricher._guidelines_registry
        assert "serverless" in enricher._guidelines_registry
        assert "monolithic" in enricher._guidelines_registry
        assert "default" in enricher._guidelines_registry
        
        assert enricher._constraints_registry is not None
        assert "performance" in enricher._constraints_registry
        assert "security" in enricher._constraints_registry
        assert "scalability" in enricher._constraints_registry
        
        assert enricher._best_practices_registry is not None
        assert "generation" in enricher._best_practices_registry
        assert "analysis" in enricher._best_practices_registry
        assert "selection" in enricher._best_practices_registry
        assert "default" in enricher._best_practices_registry