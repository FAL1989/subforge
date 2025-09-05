#!/usr/bin/env python3
"""
Test suite for Context Engineer type safety improvements
Validates that all Dict[str, Any] usages have been replaced with proper TypedDict types
"""

import pytest
import tempfile
from pathlib import Path
from typing import get_type_hints

from subforge.core.context_engineer import (
    ContextEngineer,
    ContextLevel,
    ContextPackage,
    create_context_engineer,
)
from subforge.core.context.types import (
    ProjectContext,
    TechnicalContext,
    Example,
    Pattern,
    ValidationGate,
    TechStack,
    PreviousOutput,
    ContextPackageDict,
)
from subforge.core.context.exceptions import (
    ContextError,
    InvalidProfileError,
    ValidationError,
    ContextGenerationError,
)
from subforge.core.context.validators import (
    validate_project_profile,
    validate_project_context,
    validate_technical_context,
    validate_example,
    validate_pattern,
    validate_validation_gate,
    validate_context_package_data,
)
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity,
)


class TestTypeSafety:
    """Test type safety improvements"""

    def test_tech_stack_type(self):
        """Test TechStack TypedDict"""
        tech_stack = TechStack(
            languages=["python", "javascript"],
            frameworks=["fastapi", "react"],
            databases=["postgresql"],
            tools=["docker", "git"]
        )
        
        assert isinstance(tech_stack["languages"], list)
        assert isinstance(tech_stack["frameworks"], list)
        assert isinstance(tech_stack["databases"], list)
        assert isinstance(tech_stack["tools"], list)

    def test_project_context_type(self):
        """Test ProjectContext TypedDict with all required fields"""
        context = ProjectContext(
            name="TestProject",
            path="/tmp/test",
            architecture_pattern="modular",
            complexity_level="medium",
            languages=["python"],
            frameworks=["fastapi"],
            databases=["postgresql"],
            tools=["docker"],
            team_size_estimate=5,
            has_tests=True,
            has_ci_cd=True,
            has_docker=True,
            file_count=100,
            lines_of_code=5000
        )
        
        # Verify all fields are present and typed correctly
        assert context["complexity_level"] in ["simple", "medium", "complex", "enterprise"]
        assert isinstance(context["team_size_estimate"], int)
        assert isinstance(context["has_tests"], bool)

    def test_technical_context_type(self):
        """Test TechnicalContext TypedDict with optional fields"""
        context = TechnicalContext(
            phase="analysis",
            primary_language="python",
            deployment_target="cloud",
            testing_strategy="comprehensive",
            ci_cd_integration=True
        )
        
        # Add optional fields
        context["analysis_depth"] = "deep"
        context["discovery_areas"] = ["architecture", "dependencies"]
        
        assert context["deployment_target"] in ["cloud", "traditional"]
        assert context["testing_strategy"] in ["comprehensive", "basic"]
        assert "analysis_depth" in context  # Optional field

    def test_example_type(self):
        """Test Example TypedDict"""
        example = Example(
            title="Test Example",
            purpose="Testing",
            language="python",
            code="print('test')",
            notes="Test note"
        )
        
        # Optional field
        example["framework"] = "fastapi"
        example["tags"] = ["api", "test"]
        
        assert all(field in example for field in ["title", "purpose", "language", "code", "notes"])
        assert "framework" in example  # Optional field

    def test_pattern_type(self):
        """Test Pattern TypedDict"""
        pattern = Pattern(
            name="Test Pattern",
            purpose="Testing patterns",
            implementation="Pattern implementation",
            benefits=["Benefit 1", "Benefit 2"],
            examples=["Example 1"]
        )
        
        # Optional fields
        pattern["applicability"] = "All projects"
        pattern["description"] = "Detailed description"
        
        assert isinstance(pattern["benefits"], list)
        assert isinstance(pattern["examples"], list)

    def test_validation_gate_type(self):
        """Test ValidationGate TypedDict"""
        gate = ValidationGate(
            name="Syntax Check",
            test="Check syntax",
            command="python -m py_compile",
            expected="No errors",
            on_failure="Fix syntax errors"
        )
        
        # Optional fields
        gate["type"] = "syntax"
        gate["severity"] = "critical"
        
        assert gate["type"] in ["syntax", "semantic", "security", "performance"]
        assert gate["severity"] in ["critical", "high", "medium", "low"]

    def test_context_package_dict_type(self):
        """Test ContextPackageDict serialization type"""
        package_dict = ContextPackageDict(
            project_context=ProjectContext(
                name="Test",
                path="/tmp",
                architecture_pattern="modular",
                complexity_level="simple",
                languages=["python"],
                frameworks=[],
                databases=[],
                tools=[],
                team_size_estimate=1,
                has_tests=False,
                has_ci_cd=False,
                has_docker=False,
                file_count=1,
                lines_of_code=10
            ),
            technical_context=TechnicalContext(
                phase="test",
                primary_language="python",
                deployment_target="traditional",
                testing_strategy="basic",
                ci_cd_integration=False
            ),
            examples=[],
            patterns=[],
            validation_gates=[],
            references=[],
            success_criteria=[],
            generated_at="2024-01-01T00:00:00"
        )
        
        assert "project_context" in package_dict
        assert "technical_context" in package_dict
        assert "generated_at" in package_dict


class TestValidators:
    """Test validation functions"""

    def test_validate_project_context_valid(self):
        """Test validation of valid project context"""
        context = ProjectContext(
            name="ValidProject",
            path=str(Path.cwd()),  # Use current directory to ensure it exists
            architecture_pattern="modular",
            complexity_level="medium",
            languages=["python"],
            frameworks=["fastapi"],
            databases=["postgresql"],
            tools=["docker"],
            team_size_estimate=5,
            has_tests=True,
            has_ci_cd=True,
            has_docker=True,
            file_count=100,
            lines_of_code=5000
        )
        
        # Should not raise any exception
        validate_project_context(context)

    def test_validate_project_context_invalid_complexity(self):
        """Test validation catches invalid complexity level"""
        context = ProjectContext(
            name="InvalidProject",
            path=str(Path.cwd()),
            architecture_pattern="modular",
            complexity_level="invalid",  # Invalid value
            languages=["python"],
            frameworks=[],
            databases=[],
            tools=[],
            team_size_estimate=1,
            has_tests=False,
            has_ci_cd=False,
            has_docker=False,
            file_count=1,
            lines_of_code=10
        )
        
        with pytest.raises(ValidationError):
            validate_project_context(context)

    def test_validate_technical_context_valid(self):
        """Test validation of valid technical context"""
        context = TechnicalContext(
            phase="analysis",
            primary_language="python",
            deployment_target="cloud",
            testing_strategy="comprehensive",
            ci_cd_integration=True
        )
        
        # Should not raise any exception
        validate_technical_context(context)

    def test_validate_technical_context_invalid_deployment(self):
        """Test validation catches invalid deployment target"""
        context = TechnicalContext(
            phase="analysis",
            primary_language="python",
            deployment_target="invalid",  # Invalid value
            testing_strategy="comprehensive",
            ci_cd_integration=True
        )
        
        with pytest.raises(ValidationError):
            validate_technical_context(context)

    def test_validate_example_valid(self):
        """Test validation of valid example"""
        example = Example(
            title="Valid Example",
            purpose="Testing",
            language="python",
            code="print('test')",
            notes="Test note"
        )
        
        # Should not raise any exception
        validate_example(example)

    def test_validate_example_missing_field(self):
        """Test validation catches missing required field"""
        example = {
            "title": "Invalid Example",
            "purpose": "Testing",
            "language": "python",
            # Missing 'code' field
            "notes": "Test note"
        }
        
        with pytest.raises(ValidationError):
            validate_example(example)

    def test_validate_pattern_valid(self):
        """Test validation of valid pattern"""
        pattern = Pattern(
            name="Valid Pattern",
            purpose="Testing",
            implementation="Implementation",
            benefits=["Benefit 1"],
            examples=["Example 1"]
        )
        
        # Should not raise any exception
        validate_pattern(pattern)

    def test_validate_pattern_empty_benefits(self):
        """Test validation catches empty benefits list"""
        pattern = Pattern(
            name="Invalid Pattern",
            purpose="Testing",
            implementation="Implementation",
            benefits=[],  # Empty list
            examples=["Example 1"]
        )
        
        with pytest.raises(ValidationError):
            validate_pattern(pattern)

    def test_validate_validation_gate_valid(self):
        """Test validation of valid validation gate"""
        gate = ValidationGate(
            name="Valid Gate",
            test="Test description",
            command="echo test",
            expected="test",
            on_failure="Fix it"
        )
        
        # Should not raise any exception
        validate_validation_gate(gate)

    def test_validate_validation_gate_invalid_type(self):
        """Test validation catches invalid gate type"""
        gate = ValidationGate(
            name="Invalid Gate",
            test="Test description",
            command="echo test",
            expected="test",
            on_failure="Fix it",
            type="invalid"  # Invalid type
        )
        
        with pytest.raises(ValidationError):
            validate_validation_gate(gate)


class TestContextPackage:
    """Test ContextPackage dataclass"""

    def test_context_package_creation(self):
        """Test creation of ContextPackage with typed fields"""
        package = ContextPackage(
            project_context=ProjectContext(
                name="Test",
                path="/tmp",
                architecture_pattern="modular",
                complexity_level="simple",
                languages=["python"],
                frameworks=[],
                databases=[],
                tools=[],
                team_size_estimate=1,
                has_tests=False,
                has_ci_cd=False,
                has_docker=False,
                file_count=1,
                lines_of_code=10
            ),
            technical_context=TechnicalContext(
                phase="test",
                primary_language="python",
                deployment_target="traditional",
                testing_strategy="basic",
                ci_cd_integration=False
            ),
            examples=[],
            patterns=[],
            validation_gates=[],
            references=[],
            success_criteria=[]
        )
        
        assert isinstance(package.project_context, dict)
        assert isinstance(package.technical_context, dict)
        assert isinstance(package.examples, list)

    def test_context_package_to_markdown(self):
        """Test markdown generation from context package"""
        package = ContextPackage(
            project_context=ProjectContext(
                name="TestProject",
                path="/tmp/test",
                architecture_pattern="modular",
                complexity_level="simple",
                languages=["python"],
                frameworks=["fastapi"],
                databases=[],
                tools=[],
                team_size_estimate=1,
                has_tests=False,
                has_ci_cd=False,
                has_docker=False,
                file_count=10,
                lines_of_code=100,
                has_docs=False,
                recommended_subagents=[],
                integration_requirements=[]
            ),
            technical_context=TechnicalContext(
                phase="generation",
                primary_language="python",
                deployment_target="traditional",
                testing_strategy="basic",
                ci_cd_integration=False
            ),
            examples=[
                Example(
                    title="Test Example",
                    purpose="Testing",
                    language="python",
                    code="print('test')",
                    notes="Test note"
                )
            ],
            patterns=[],
            validation_gates=[
                ValidationGate(
                    name="Test Gate",
                    test="Test validation",
                    command="echo test",
                    expected="test",
                    on_failure="Fix it",
                    type="syntax",
                    severity="high"
                )
            ],
            references=["https://example.com"],
            success_criteria=["Test passes"]
        )
        
        markdown = package.to_markdown()
        
        assert "# Context Package - TestProject" in markdown
        assert "## Project Context" in markdown
        assert "## Technical Context" in markdown
        assert "## Code Examples & Patterns" in markdown
        assert "## Validation Gates" in markdown
        assert "[HIGH]" in markdown  # Severity indicator
        assert "(syntax)" in markdown  # Type indicator

    def test_context_package_to_dict(self):
        """Test dictionary serialization of context package"""
        package = ContextPackage(
            project_context=ProjectContext(
                name="Test",
                path="/tmp",
                architecture_pattern="modular",
                complexity_level="simple",
                languages=["python"],
                frameworks=[],
                databases=[],
                tools=[],
                team_size_estimate=1,
                has_tests=False,
                has_ci_cd=False,
                has_docker=False,
                file_count=1,
                lines_of_code=10
            ),
            technical_context=TechnicalContext(
                phase="test",
                primary_language="python",
                deployment_target="traditional",
                testing_strategy="basic",
                ci_cd_integration=False
            ),
            examples=[],
            patterns=[],
            validation_gates=[],
            references=[],
            success_criteria=[]
        )
        
        package_dict = package.to_dict()
        
        assert "project_context" in package_dict
        assert "technical_context" in package_dict
        assert "generated_at" in package_dict
        assert isinstance(package_dict["generated_at"], str)


class TestContextEngineer:
    """Test ContextEngineer class with type safety"""

    def test_context_engineer_initialization(self):
        """Test ContextEngineer initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            engineer = ContextEngineer(workspace)
            
            assert engineer.workspace_dir == workspace
            assert engineer.context_library.exists()
            assert engineer.examples_dir.exists()
            assert engineer.patterns_dir.exists()

    def test_build_project_context(self):
        """Test building project context returns correct type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            engineer = ContextEngineer(workspace)
            
            # Create a mock profile
            profile = ProjectProfile(
                name="TestProject",
                path=Path("/tmp/test"),
                technology_stack=TechnologyStack(
                    languages={"python"},
                    frameworks={"fastapi"},
                    databases={"postgresql"},
                    tools={"docker"},
                    package_managers={"pip"}
                ),
                architecture_pattern=ArchitecturePattern.FULLSTACK,
                complexity=ProjectComplexity.MEDIUM,
                team_size_estimate=5,
                has_tests=True,
                has_ci_cd=True,
                has_docker=True,
                file_count=100,
                lines_of_code=5000,
                has_docs=True,
                recommended_subagents=["api-developer", "test-engineer"],
                integration_requirements=["fastapi", "postgresql"]
            )
            
            context = engineer._build_project_context(profile)
            
            # Verify it returns a valid ProjectContext
            assert isinstance(context, dict)
            assert context["name"] == "TestProject"
            assert context["complexity_level"] == "medium"
            assert "python" in context["languages"]

    def test_build_technical_context(self):
        """Test building technical context returns correct type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            engineer = ContextEngineer(workspace)
            
            profile = ProjectProfile(
                name="TestProject",
                path=Path("/tmp/test"),
                technology_stack=TechnologyStack(
                    languages={"python"},
                    frameworks=set(),
                    databases=set(),
                    tools=set(),
                    package_managers={"pip"}
                ),
                architecture_pattern=ArchitecturePattern.FULLSTACK,
                complexity=ProjectComplexity.SIMPLE,
                team_size_estimate=1,
                has_tests=False,
                has_ci_cd=False,
                has_docker=False,
                file_count=10,
                lines_of_code=100,
                has_docs=False,
                recommended_subagents=[],
                integration_requirements=[]
            )
            
            context = engineer._build_technical_context(profile, "analysis")
            
            # Verify it returns a valid TechnicalContext
            assert isinstance(context, dict)
            assert context["phase"] == "analysis"
            assert context["primary_language"] == "python"
            assert context["deployment_target"] in ["cloud", "traditional"]
            assert context["testing_strategy"] in ["comprehensive", "basic"]

    def test_create_validation_gates(self):
        """Test validation gates creation returns correct types"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            engineer = ContextEngineer(workspace)
            
            profile = ProjectProfile(
                name="TestProject",
                path=Path("/tmp/test"),
                technology_stack=TechnologyStack(
                    languages={"python"},
                    frameworks=set(),
                    databases=set(),
                    tools=set(),
                    package_managers={"pip"}
                ),
                architecture_pattern=ArchitecturePattern.FULLSTACK,
                complexity=ProjectComplexity.SIMPLE,
                team_size_estimate=1,
                has_tests=True,  # Enable test coverage gate
                has_ci_cd=False,
                has_docker=False,
                file_count=10,
                lines_of_code=100,
                has_docs=False,
                recommended_subagents=[],
                integration_requirements=[]
            )
            
            gates = engineer._create_validation_gates("generation", profile)
            
            # Verify gates are properly typed
            assert len(gates) >= 2  # At least syntax validation gates
            for gate in gates:
                assert "name" in gate
                assert "test" in gate
                assert "command" in gate
                assert "expected" in gate
                assert "on_failure" in gate
                if "type" in gate:
                    assert gate["type"] in ["syntax", "semantic", "security", "performance"]
                if "severity" in gate:
                    assert gate["severity"] in ["critical", "high", "medium", "low"]


def test_no_dict_any_in_signatures():
    """Verify that Dict[str, Any] is not used in public method signatures"""
    import inspect
    
    # Get all public methods of ContextEngineer
    engineer_methods = inspect.getmembers(ContextEngineer, predicate=inspect.isfunction)
    
    for name, method in engineer_methods:
        if not name.startswith('_'):  # Public methods only
            signature = inspect.signature(method)
            for param_name, param in signature.parameters.items():
                if param.annotation and 'Dict[str, Any]' in str(param.annotation):
                    pytest.fail(
                        f"Method {name} still uses Dict[str, Any] in parameter {param_name}. "
                        f"Should use specific TypedDict instead."
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])