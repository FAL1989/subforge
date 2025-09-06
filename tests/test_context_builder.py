#!/usr/bin/env python3
"""
Test suite for Context Builder module
Tests builder pattern implementation, fluent interface, and validation
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from subforge.core.context.builder import ContextBuilder, ContextPackage
from subforge.core.context.types import (
    ProjectContext,
    TechnicalContext,
    Example,
    Pattern,
    ValidationGate,
    ContextPackageDict,
)
from subforge.core.context.exceptions import ContextGenerationError, ValidationError
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity,
)


class TestContextBuilder:
    """Test ContextBuilder fluent interface and construction"""
    
    @pytest.fixture
    def mock_profile(self, tmp_path):
        """Create a mock project profile for testing"""
        profile = Mock(spec=ProjectProfile)
        profile.name = "test-project"
        profile.path = tmp_path
        profile.architecture_pattern = ArchitecturePattern.MICROSERVICES
        profile.complexity = ProjectComplexity.COMPLEX
        profile.technology_stack = TechnologyStack(
            languages={"python", "typescript"},
            frameworks={"fastapi", "react"},
            databases={"postgresql"},
            tools={"docker", "git"},
            package_managers={"pip", "npm"},
        )
        profile.team_size_estimate = 5
        profile.has_tests = True
        profile.has_ci_cd = True
        profile.has_docker = True
        profile.file_count = 100
        profile.lines_of_code = 10000
        return profile
    
    def test_builder_pattern_implementation(self, mock_profile):
        """Test fluent interface returns self for chaining"""
        builder = ContextBuilder()
        
        # Test each method returns the builder instance
        assert builder.with_project_context(mock_profile) is builder
        assert builder.with_technical_context(mock_profile, "generation") is builder
        assert builder.with_examples([]) is builder
        assert builder.with_patterns([]) is builder
        assert builder.with_validation_gates([]) is builder
        assert builder.with_references([]) is builder
        assert builder.with_success_criteria([]) is builder
    
    @patch('subforge.core.context.validators.validate_context_package_data')
    def test_context_construction(self, mock_validate, mock_profile):
        """Test complete context package creation"""
        builder = ContextBuilder()
        
        example = Example(
            title="Test Example",
            purpose="Testing",
            language="python",
            code="print('test')",
            notes="Test note"
        )
        
        pattern = Pattern(
            name="Test Pattern",
            purpose="Testing pattern",
            implementation="Test implementation",
            benefits=["test benefit"],
            examples=["test example"]
        )
        
        gate = ValidationGate(
            name="Test Gate",
            test="Test validation",
            command="echo test",
            expected="test",
            on_failure="fix it",
            type="syntax",
            severity="high"
        )
        
        context = (builder
            .with_project_context(mock_profile)
            .with_technical_context(mock_profile, "generation")
            .with_examples([example])
            .with_patterns([pattern])
            .with_validation_gates([gate])
            .with_references(["test reference"])
            .with_success_criteria(["test criteria"])
            .build()
        )
        
        assert isinstance(context, ContextPackage)
        assert context.project_context["name"] == "test-project"
        assert context.technical_context["phase"] == "generation"
        assert len(context.examples) == 1
        assert len(context.patterns) == 1
        assert len(context.validation_gates) == 1
        assert len(context.references) == 1
        assert len(context.success_criteria) == 1
    
    def test_validation_during_build(self):
        """Test validation errors during build"""
        builder = ContextBuilder()
        
        # Missing required contexts
        with pytest.raises(ContextGenerationError) as exc:
            builder.build()
        assert "Project and technical contexts are required" in str(exc.value)
    
    @patch('subforge.core.context.validators.validate_context_package_data')
    def test_type_safety(self, mock_validate, mock_profile):
        """Verify TypedDict usage"""
        builder = ContextBuilder()
        context = (builder
            .with_project_context(mock_profile)
            .with_technical_context(mock_profile, "analysis")
            .build()
        )
        
        # Verify project context has correct type
        assert isinstance(context.project_context, dict)
        assert "name" in context.project_context
        assert "path" in context.project_context
        assert "architecture_pattern" in context.project_context
        
        # Verify technical context has correct type
        assert isinstance(context.technical_context, dict)
        assert "phase" in context.technical_context
        assert "primary_language" in context.technical_context
    
    @patch('subforge.core.context.validators.validate_context_package_data')
    def test_builder_reset(self, mock_validate, mock_profile):
        """Test builder can be reused"""
        builder = ContextBuilder()
        
        # Build first context
        context1 = (builder
            .with_project_context(mock_profile)
            .with_technical_context(mock_profile, "analysis")
            .with_success_criteria(["criteria1"])
            .build()
        )
        
        # Build second context with same builder
        context2 = (builder
            .with_project_context(mock_profile)
            .with_technical_context(mock_profile, "generation")
            .with_success_criteria(["criteria2"])
            .build()
        )
        
        assert context1.technical_context["phase"] == "analysis"
        assert context2.technical_context["phase"] == "generation"
        assert context1.success_criteria == ["criteria1"]
        assert context2.success_criteria == ["criteria2"]
    
    @patch('subforge.core.context.validators.validate_context_package_data')
    def test_phase_specific_context(self, mock_validate, mock_profile):
        """Test phase-specific context additions"""
        builder = ContextBuilder()
        
        # Test analysis phase
        context = (builder
            .with_project_context(mock_profile)
            .with_technical_context(mock_profile, "analysis")
            .build()
        )
        assert "analysis_depth" in context.technical_context
        assert "discovery_areas" in context.technical_context
        
        # Test selection phase
        builder = ContextBuilder()
        context = (builder
            .with_project_context(mock_profile)
            .with_technical_context(mock_profile, "selection")
            .build()
        )
        assert "template_criteria" in context.technical_context
        assert "customization_level" in context.technical_context
        
        # Test generation phase
        builder = ContextBuilder()
        context = (builder
            .with_project_context(mock_profile)
            .with_technical_context(mock_profile, "generation")
            .build()
        )
        assert "generation_targets" in context.technical_context
        assert "customization_required" in context.technical_context
        assert "integration_complexity" in context.technical_context
    
    @patch('subforge.core.context.builder.validate_context_package_data')
    def test_validation_error_handling(self, mock_validate, mock_profile):
        """Test handling of validation errors"""
        mock_validate.side_effect = ValidationError("Invalid data")
        
        builder = ContextBuilder()
        with pytest.raises(ContextGenerationError) as exc:
            builder.with_project_context(mock_profile).with_technical_context(mock_profile, "generation").build()
        assert "Failed to build context package" in str(exc.value)
    
    def test_get_template_criteria(self, mock_profile):
        """Test template criteria generation based on profile"""
        builder = ContextBuilder()
        criteria = builder._get_template_criteria(mock_profile)
        
        assert any("python" in c.lower() for c in criteria)
        assert any("typescript" in c.lower() for c in criteria)
        assert any("microservices" in c.lower() for c in criteria)
        assert any("complex" in c.lower() for c in criteria)
        assert any("testing" in c.lower() for c in criteria)
        assert any("ci" in c.lower() or "cd" in c.lower() for c in criteria)
        assert any("container" in c.lower() for c in criteria)


class TestContextPackage:
    """Test ContextPackage functionality"""
    
    @pytest.fixture
    def sample_package(self):
        """Create a sample context package"""
        project_context = ProjectContext(
            name="test-project",
            path="/test/path",
            architecture_pattern="microservices",
            complexity_level="complex",
            languages=["python", "typescript"],
            frameworks=["fastapi", "react"],
            databases=["postgresql"],
            tools=["docker"],
            team_size_estimate=5,
            has_tests=True,
            has_ci_cd=True,
            has_docker=True,
            file_count=100,
            lines_of_code=10000
        )
        
        technical_context = TechnicalContext(
            phase="generation",
            primary_language="python",
            deployment_target="cloud",
            testing_strategy="comprehensive",
            ci_cd_integration=True
        )
        
        example = Example(
            title="Test Example",
            purpose="Testing",
            language="python",
            code="print('test')",
            notes="Test note"
        )
        
        pattern = Pattern(
            name="Test Pattern",
            purpose="Testing",
            implementation="Test impl",
            benefits=["benefit1"],
            examples=["example1"]
        )
        
        gate = ValidationGate(
            name="Test Gate",
            test="Test validation",
            command="echo test",
            expected="success",
            on_failure="retry",
            type="syntax",
            severity="high"
        )
        
        return ContextPackage(
            project_context=project_context,
            technical_context=technical_context,
            examples=[example],
            patterns=[pattern],
            validation_gates=[gate],
            references=["ref1", "ref2"],
            success_criteria=["criteria1", "criteria2"]
        )
    
    def test_to_markdown(self, sample_package):
        """Test markdown generation"""
        markdown = sample_package.to_markdown()
        
        assert "# Context Package - test-project" in markdown
        assert "## Project Context" in markdown
        assert "## Technical Context" in markdown
        assert "## Code Examples & Patterns" in markdown
        assert "## Validation Gates" in markdown
        assert "## Success Criteria" in markdown
        assert "## References" in markdown
        assert "Generated by SubForge Context Engineer" in markdown
    
    def test_to_dict(self, sample_package):
        """Test dictionary conversion"""
        result = sample_package.to_dict()
        
        assert isinstance(result, dict)
        assert "project_context" in result
        assert "technical_context" in result
        assert "examples" in result
        assert "patterns" in result
        assert "validation_gates" in result
        assert "references" in result
        assert "success_criteria" in result
        assert "generated_at" in result
        
        # Verify ISO format timestamp
        datetime.fromisoformat(result["generated_at"])
    
    def test_format_dict_as_markdown(self, sample_package):
        """Test dictionary markdown formatting"""
        data = {"test_key": "test_value", "list_key": ["item1", "item2"]}
        markdown = sample_package._format_dict_as_markdown(data)
        
        assert "**Test Key**:" in markdown
        assert "test_value" in markdown
        assert "**List Key**:" in markdown
        assert "item1, item2" in markdown
    
    def test_format_examples_as_markdown_empty(self, sample_package):
        """Test examples formatting with no examples"""
        sample_package.examples = []
        markdown = sample_package._format_examples_as_markdown()
        assert markdown == "No specific examples available"
    
    def test_format_examples_as_markdown_with_data(self, sample_package):
        """Test examples formatting with data"""
        markdown = sample_package._format_examples_as_markdown()
        assert "### Example 1: Test Example" in markdown
        assert "**Purpose**: Testing" in markdown
        assert "```python" in markdown
        assert "print('test')" in markdown
        assert "**Notes**: Test note" in markdown
    
    def test_format_validation_gates_as_markdown_empty(self, sample_package):
        """Test validation gates formatting with no gates"""
        sample_package.validation_gates = []
        markdown = sample_package._format_validation_gates_as_markdown()
        assert markdown == "No validation gates defined"
    
    def test_format_validation_gates_as_markdown_with_data(self, sample_package):
        """Test validation gates formatting with data"""
        markdown = sample_package._format_validation_gates_as_markdown()
        assert "### Test Gate [HIGH] (syntax)" in markdown
        assert "- [ ] **Test**: Test validation" in markdown
        assert "- [ ] **Command**: `echo test`" in markdown
        assert "- [ ] **Expected**: success" in markdown
        assert "- [ ] **On Failure**: retry" in markdown
    
    def test_format_list_as_markdown(self, sample_package):
        """Test list markdown formatting"""
        items = ["item1", "item2", "item3"]
        markdown = sample_package._format_list_as_markdown(items)
        assert "- item1" in markdown
        assert "- item2" in markdown
        assert "- item3" in markdown
        
        # Test empty list
        markdown = sample_package._format_list_as_markdown([])
        assert markdown == "None specified"