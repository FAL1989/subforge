#!/usr/bin/env python3
"""
Test suite for refactored PRP Generator with Strategy Pattern
"""

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from subforge.core.context_engineer import ContextPackage
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity,
)
from subforge.core.prp import (
    PRPGenerator,
    PRPType,
    create_prp_generator,
    create_fluent_builder,
    FactoryAnalysisStrategy,
    GenerationStrategy,
    ValidationStrategy,
)


@pytest.fixture
def workspace_dir():
    """Create temporary workspace directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_project_profile():
    """Create sample project profile for testing"""
    return ProjectProfile(
        name="TestProject",
        path=Path("/tmp/test_project"),
        technology_stack=TechnologyStack(
            languages=["python", "typescript"],
            frameworks=["fastapi", "react"],
            databases=["postgresql"],
            tools=["docker", "pytest"],
        ),
        architecture_pattern=ArchitecturePattern.MICROSERVICES,
        complexity=ProjectComplexity.MEDIUM,
        team_size_estimate=5,
        has_tests=True,
        has_ci_cd=True,
        dominant_language="python",
        loc_stats={"python": 5000, "typescript": 3000},
        file_count=100,
    )


@pytest.fixture
def sample_context_package():
    """Create sample context package for testing"""
    return ContextPackage(
        project_context={"description": "Test project context"},
        relevant_examples=[],
        best_practices=[],
        constraints=[],
        success_criteria=[],
        timestamp=datetime.now(),
    )


class TestPRPGenerator:
    """Test the main PRP Generator"""
    
    def test_backward_compatibility(self, workspace_dir, sample_project_profile, sample_context_package):
        """Test that old API still works"""
        generator = create_prp_generator(workspace_dir)
        
        # Test factory analysis generation
        prp = generator.generate_factory_analysis_prp(
            sample_project_profile,
            sample_context_package,
            "Create a comprehensive test suite"
        )
        
        assert prp is not None
        assert prp.type == PRPType.FACTORY_ANALYSIS
        assert "Factory Analysis" in prp.title
        
    def test_factory_generation(self, workspace_dir, sample_project_profile, sample_context_package):
        """Test factory generation PRP"""
        generator = PRPGenerator(workspace_dir)
        
        prp = generator.generate_factory_generation_prp(
            sample_project_profile,
            sample_context_package,
            {"analysis": "complete"},
            "agent-generator"
        )
        
        assert prp.type == PRPType.FACTORY_GENERATION
        assert "agent-generator" in prp.id
        
    @pytest.mark.asyncio
    async def test_async_generation(self, workspace_dir, sample_project_profile, sample_context_package):
        """Test async PRP generation"""
        generator = PRPGenerator(workspace_dir)
        
        context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "user_request": "Test async generation"
        }
        
        prp = await generator.generate_prp(PRPType.FACTORY_ANALYSIS, context)
        assert prp is not None
        
    def test_strategy_listing(self, workspace_dir):
        """Test listing available strategies"""
        generator = PRPGenerator(workspace_dir)
        strategies = generator.list_available_strategies()
        
        assert "factory_analysis" in strategies
        assert "factory_generation" in strategies
        assert "validation_comprehensive" in strategies


class TestStrategies:
    """Test individual strategy implementations"""
    
    @pytest.mark.asyncio
    async def test_factory_analysis_strategy(self, workspace_dir, sample_project_profile, sample_context_package):
        """Test factory analysis strategy"""
        strategy = FactoryAnalysisStrategy(workspace_dir)
        
        context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "user_request": "Analyze project structure"
        }
        
        assert strategy.validate_context(context)
        
        prp = await strategy.generate(context)
        assert strategy.validate(prp)
        assert prp.type == PRPType.FACTORY_ANALYSIS
        
    @pytest.mark.asyncio
    async def test_generation_strategy(self, workspace_dir, sample_project_profile, sample_context_package):
        """Test generation strategy"""
        strategy = GenerationStrategy(workspace_dir)
        
        context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "analysis_outputs": {"complete": True},
            "subagent_type": "claude-md-generator"
        }
        
        prp = await strategy.generate(context)
        assert prp.type == PRPType.FACTORY_GENERATION
        assert "claude-md-generator" in prp.title.lower()
        
    @pytest.mark.asyncio
    async def test_validation_strategy(self, workspace_dir, sample_project_profile, sample_context_package):
        """Test validation strategy"""
        strategy = ValidationStrategy(workspace_dir)
        
        context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "validation_scope": "full_project",
            "artifacts_to_validate": ["config.yaml", "agents/"]
        }
        
        prp = await strategy.generate(context)
        assert prp.type == PRPType.VALIDATION_COMPREHENSIVE
        assert "validation" in prp.title.lower()


class TestPRPBuilder:
    """Test PRP Builder functionality"""
    
    def test_fluent_builder(self, sample_context_package):
        """Test fluent builder interface"""
        builder = create_fluent_builder()
        
        prp = (builder
            .for_project("TestProject")
            .for_analysis()
            .with_context_package(sample_context_package)
            .with_execution_prompt("Test prompt")
            .with_standard_analysis_checklist()
            .add_success_metric("Test completed")
            .build())
        
        assert prp.id.startswith("testproject_")
        assert prp.type == PRPType.FACTORY_ANALYSIS
        assert "Test completed" in prp.success_metrics
        assert len(prp.validation_checklist) > 0
        
    def test_builder_validation(self, sample_context_package):
        """Test builder validates required fields"""
        builder = create_fluent_builder()
        
        # Missing required fields should raise error
        with pytest.raises(ValueError) as exc_info:
            builder.build()
        
        assert "Missing required fields" in str(exc_info.value)
        
    def test_builder_reset(self, sample_context_package):
        """Test builder resets after build"""
        builder = create_fluent_builder()
        
        # Build first PRP
        prp1 = (builder
            .for_project("Project1")
            .for_analysis()
            .with_context_package(sample_context_package)
            .with_execution_prompt("Prompt 1")
            .build())
        
        # Build second PRP (builder should be reset)
        prp2 = (builder
            .for_project("Project2")
            .for_generation("agent-generator")
            .with_context_package(sample_context_package)
            .with_execution_prompt("Prompt 2")
            .build())
        
        assert prp1.id != prp2.id
        assert prp1.type != prp2.type


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_format_functions(self):
        """Test formatting utility functions"""
        from subforge.core.prp.utils import (
            format_checklist,
            format_metrics,
            format_analysis_insights,
        )
        
        # Test checklist formatting
        checklist = format_checklist(["Item 1", "Item 2"])
        assert "- [ ] Item 1" in checklist
        assert "- [ ] Item 2" in checklist
        
        # Test metrics formatting
        metrics = format_metrics(["Metric 1", "Metric 2"])
        assert "- Metric 1" in metrics
        assert "- Metric 2" in metrics
        
        # Test insights formatting
        insights = format_analysis_insights({"key": "value", "list": [1, 2, 3]})
        assert "Key: value" in insights
        assert "List: 1, 2, 3" in insights


if __name__ == "__main__":
    pytest.main([__file__, "-v"])