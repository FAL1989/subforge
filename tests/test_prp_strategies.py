#!/usr/bin/env python3
"""
Comprehensive test suite for PRP Strategy Pattern implementation
Tests all strategy implementations including factory, generation, and validation
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from subforge.core.context_engineer import ContextPackage
from subforge.core.project_analyzer import ProjectProfile
from subforge.core.prp.base import PRP, PRPType
from subforge.core.prp.factory_strategy import FactoryAnalysisStrategy
from subforge.core.prp.generation_strategy import GenerationStrategy
from subforge.core.prp.registry import PRPStrategyRegistry
from subforge.core.prp.validation_strategy import ValidationStrategy
from subforge.core.prp_template_loader import PRPTemplateLoader


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace directory"""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_template_loader():
    """Create mock template loader"""
    loader = Mock(spec=PRPTemplateLoader)
    loader.render = Mock(return_value="Rendered template content")
    loader.validate_template = Mock(return_value=True)
    return loader


@pytest.fixture
def mock_project_profile():
    """Create mock project profile"""
    profile = Mock(spec=ProjectProfile)
    profile.name = "TestProject"
    profile.path = Path("/test/project")
    profile.language = "python"
    profile.framework = "fastapi"
    profile.complexity = "medium"
    profile.estimated_team_size = 5
    profile.total_files = 100
    profile.total_lines = 5000
    return profile


@pytest.fixture
def mock_context_package():
    """Create mock context package"""
    package = Mock(spec=ContextPackage)
    package.project_context = {"type": "backend", "stack": "python"}
    package.examples = ["example1", "example2"]
    package.patterns = ["pattern1", "pattern2"]
    package.to_markdown = Mock(return_value="# Context Package\n\nMocked content")
    return package


class TestFactoryAnalysisStrategy:
    """Test suite for Factory Analysis Strategy"""
    
    @pytest.fixture
    def strategy(self, temp_workspace, mock_template_loader):
        """Create factory analysis strategy instance"""
        return FactoryAnalysisStrategy(temp_workspace, mock_template_loader)
    
    def test_initialization(self, strategy, temp_workspace):
        """Test strategy initialization"""
        assert strategy.workspace_dir == temp_workspace
        assert strategy.template_loader is not None
        assert (temp_workspace / "PRPs").exists()
        assert (temp_workspace / "PRPs" / "generated").exists()
    
    def test_required_context_keys(self, strategy):
        """Test required context keys"""
        required = strategy.get_required_context_keys()
        assert "project_profile" in required
        assert "context_package" in required
        assert "user_request" in required
        assert len(required) == 3
    
    @pytest.mark.asyncio
    async def test_factory_analysis_generation(self, strategy, mock_project_profile, mock_context_package):
        """Test factory analysis PRP generation"""
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "user_request": "Create a comprehensive agent team"
        }
        
        prp = await strategy.generate(context)
        
        assert prp is not None
        assert prp.type == PRPType.FACTORY_ANALYSIS
        assert "TestProject" in prp.title
        assert prp.context_package == mock_context_package
        assert prp.execution_prompt is not None
        assert len(prp.validation_checklist) > 0
        assert len(prp.success_metrics) > 0
        assert prp.output_specification is not None
    
    @pytest.mark.asyncio
    async def test_factory_template_usage(self, temp_workspace):
        """Test that factory strategy uses correct template"""
        mock_loader = Mock(spec=PRPTemplateLoader)
        mock_loader.render = Mock(return_value="Template rendered content")
        
        strategy = FactoryAnalysisStrategy(temp_workspace, mock_loader)
        
        context = {
            "project_profile": Mock(name="TestProject"),
            "context_package": Mock(),
            "user_request": "Test request"
        }
        
        with patch.object(strategy, '_generate_execution_prompt', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Execution prompt"
            await strategy.generate(context)
            mock_gen.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_factory_context_validation(self, strategy):
        """Test context validation"""
        # Test with missing keys
        incomplete_context = {"project_profile": Mock()}
        
        with pytest.raises(ValueError, match="Missing required context keys"):
            await strategy.generate(incomplete_context)
    
    @pytest.mark.asyncio
    async def test_factory_prp_saving(self, strategy, mock_project_profile, mock_context_package, temp_workspace):
        """Test that generated PRP is saved correctly"""
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "user_request": "Save test"
        }
        
        prp = await strategy.generate(context)
        
        # Check that files were created
        prp_file = temp_workspace / "PRPs" / "generated" / f"{prp.id}.md"
        meta_file = temp_workspace / "PRPs" / "generated" / f"{prp.id}_meta.json"
        
        assert prp_file.exists()
        assert meta_file.exists()
        
        # Verify metadata content
        with open(meta_file, 'r') as f:
            metadata = json.load(f)
            assert metadata['id'] == prp.id
            assert metadata['type'] == PRPType.FACTORY_ANALYSIS.value
    
    def test_factory_validation_checklist_creation(self, strategy):
        """Test validation checklist creation"""
        checklist = strategy._create_validation_checklist()
        
        assert isinstance(checklist, list)
        assert len(checklist) > 0
        assert all(isinstance(item, str) for item in checklist)
    
    def test_factory_success_metrics_creation(self, strategy):
        """Test success metrics creation"""
        metrics = strategy._create_success_metrics()
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert all(isinstance(item, str) for item in metrics)


class TestGenerationStrategy:
    """Test suite for Generation Strategy"""
    
    @pytest.fixture
    def strategy(self, temp_workspace, mock_template_loader):
        """Create generation strategy instance"""
        return GenerationStrategy(temp_workspace, mock_template_loader)
    
    def test_initialization(self, strategy):
        """Test strategy initialization"""
        assert strategy.subagent_generators is not None
        assert "claude-md-generator" in strategy.subagent_generators
        assert "agent-generator" in strategy.subagent_generators
        assert "workflow-generator" in strategy.subagent_generators
        assert "orchestrator" in strategy.subagent_generators
    
    def test_required_context_keys(self, strategy):
        """Test required context keys"""
        required = strategy.get_required_context_keys()
        assert "project_profile" in required
        assert "context_package" in required
        assert "analysis_outputs" in required
        assert "subagent_type" in required
        assert len(required) == 4
    
    @pytest.mark.asyncio
    async def test_generation_for_all_subagent_types(self, strategy, mock_project_profile, mock_context_package):
        """Test generation for all supported subagent types"""
        subagent_types = ["claude-md-generator", "agent-generator", "workflow-generator", "orchestrator"]
        
        for subagent_type in subagent_types:
            context = {
                "project_profile": mock_project_profile,
                "context_package": mock_context_package,
                "analysis_outputs": {"agents": [], "workflows": []},
                "subagent_type": subagent_type
            }
            
            prp = await strategy.generate(context)
            
            assert prp is not None
            assert prp.type == PRPType.FACTORY_GENERATION
            assert subagent_type.replace('-', ' ').title() in prp.title
            assert prp.execution_prompt is not None
    
    @pytest.mark.asyncio
    async def test_generation_template_variables(self, temp_workspace):
        """Test template variable substitution in generation"""
        mock_loader = Mock(spec=PRPTemplateLoader)
        mock_loader.render = Mock(return_value="Rendered with {variable}")
        
        strategy = GenerationStrategy(temp_workspace, mock_loader)
        
        context = {
            "project_profile": Mock(name="TestProject"),
            "context_package": Mock(),
            "analysis_outputs": {"test": "value"},
            "subagent_type": "agent-generator"
        }
        
        prp = await strategy.generate(context)
        assert prp.execution_prompt is not None
    
    @pytest.mark.asyncio
    async def test_generation_validation(self, strategy, mock_project_profile, mock_context_package):
        """Test generated PRP validation"""
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "analysis_outputs": {},
            "subagent_type": "claude-md-generator"
        }
        
        prp = await strategy.generate(context)
        
        # Validate the generated PRP
        assert strategy.validate(prp)
        assert prp.id is not None
        assert prp.type is not None
        assert prp.title is not None
        assert prp.context_package is not None
        assert prp.execution_prompt is not None
        assert prp.validation_checklist is not None
        assert prp.success_metrics is not None
        assert prp.output_specification is not None
        assert prp.created_at is not None
    
    @pytest.mark.asyncio
    async def test_unknown_subagent_type(self, strategy, mock_project_profile, mock_context_package):
        """Test handling of unknown subagent type"""
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "analysis_outputs": {},
            "subagent_type": "unknown-generator"
        }
        
        # Should still generate a PRP with default prompt
        prp = await strategy.generate(context)
        assert prp is not None
    
    @pytest.mark.asyncio
    async def test_claude_md_specific_generation(self, strategy, mock_project_profile, mock_context_package):
        """Test Claude MD specific generation logic"""
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "analysis_outputs": {"agents": ["frontend", "backend"]},
            "subagent_type": "claude-md-generator"
        }
        
        prp = await strategy.generate(context)
        
        # Check for Claude MD specific elements
        assert "Claude Md Generator" in prp.title
        assert prp.validation_checklist is not None
        assert prp.success_metrics is not None


class TestValidationStrategy:
    """Test suite for Validation Strategy"""
    
    @pytest.fixture
    def strategy(self, temp_workspace, mock_template_loader):
        """Create validation strategy instance"""
        return ValidationStrategy(temp_workspace, mock_template_loader)
    
    def test_initialization(self, strategy, temp_workspace):
        """Test strategy initialization"""
        assert strategy.workspace_dir == temp_workspace
        assert strategy.template_loader is not None
    
    def test_required_context_keys(self, strategy):
        """Test required context keys"""
        required = strategy.get_required_context_keys()
        assert "project_profile" in required
        assert "context_package" in required
        assert "validation_scope" in required
        assert "artifacts_to_validate" in required
        assert len(required) == 4
    
    @pytest.mark.asyncio
    async def test_validation_prp_generation(self, strategy, mock_project_profile, mock_context_package):
        """Test validation PRP creation"""
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "validation_scope": "comprehensive",
            "artifacts_to_validate": ["agent1.md", "workflow1.py", "config.yaml"]
        }
        
        prp = await strategy.generate(context)
        
        assert prp is not None
        assert prp.type == PRPType.VALIDATION_COMPREHENSIVE
        assert "Comprehensive Validation" in prp.title
        assert prp.execution_prompt is not None
        assert len(prp.validation_checklist) > 0
    
    @pytest.mark.asyncio
    async def test_validation_checklist_creation(self, strategy, mock_project_profile, mock_context_package):
        """Test validation checklist creation with different scopes"""
        scopes = ["unit", "integration", "comprehensive", "security"]
        
        for scope in scopes:
            context = {
                "project_profile": mock_project_profile,
                "context_package": mock_context_package,
                "validation_scope": scope,
                "artifacts_to_validate": ["test.py"]
            }
            
            prp = await strategy.generate(context)
            
            assert len(prp.validation_checklist) > 0
            assert all(isinstance(item, str) for item in prp.validation_checklist)
    
    @pytest.mark.asyncio
    async def test_validation_metrics(self, strategy, mock_project_profile, mock_context_package):
        """Test validation metrics generation"""
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "validation_scope": "performance",
            "artifacts_to_validate": ["api.py", "database.py"]
        }
        
        prp = await strategy.generate(context)
        
        assert len(prp.success_metrics) > 0
        assert all(isinstance(metric, str) for metric in prp.success_metrics)
    
    @pytest.mark.asyncio
    async def test_validation_output_specification(self, strategy, mock_project_profile, mock_context_package):
        """Test validation output specification"""
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "validation_scope": "comprehensive",
            "artifacts_to_validate": []
        }
        
        prp = await strategy.generate(context)
        
        assert prp.output_specification is not None
        assert isinstance(prp.output_specification, dict)
    
    @pytest.mark.asyncio
    async def test_validation_scope_specific_logic(self, strategy, mock_project_profile, mock_context_package):
        """Test that different validation scopes produce different outputs"""
        scope1_context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "validation_scope": "security",
            "artifacts_to_validate": ["auth.py"]
        }
        
        scope2_context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "validation_scope": "performance",
            "artifacts_to_validate": ["auth.py"]
        }
        
        prp1 = await strategy.generate(scope1_context)
        prp2 = await strategy.generate(scope2_context)
        
        # Different scopes should produce different content
        assert prp1.execution_prompt != prp2.execution_prompt
        assert "security" in prp1.title.lower()
        assert "performance" in prp2.title.lower()


class TestStrategyRegistry:
    """Test suite for Strategy Registry"""
    
    @pytest.fixture
    def registry(self, temp_workspace, mock_template_loader):
        """Create registry instance"""
        return PRPStrategyRegistry(temp_workspace, mock_template_loader)
    
    def test_registry_initialization(self, registry):
        """Test registry initialization with default strategies"""
        assert registry.workspace_dir is not None
        assert registry.template_loader is not None
        
        # Check default strategies are registered
        assert registry.has_strategy(PRPType.FACTORY_ANALYSIS)
        assert registry.has_strategy(PRPType.FACTORY_GENERATION)
        assert registry.has_strategy(PRPType.VALIDATION_COMPREHENSIVE)
    
    def test_registry_registration(self, registry, temp_workspace):
        """Test strategy registration"""
        # Create a mock strategy
        mock_strategy = Mock(spec=FactoryAnalysisStrategy)
        
        # Register it for a new type
        registry.register(PRPType.AGENT_SPECIALIZATION, mock_strategy)
        
        assert registry.has_strategy(PRPType.AGENT_SPECIALIZATION)
        retrieved = registry.get_strategy(PRPType.AGENT_SPECIALIZATION)
        assert retrieved == mock_strategy
    
    def test_registry_retrieval(self, registry):
        """Test strategy retrieval by type"""
        # Get factory analysis strategy
        strategy = registry.get_strategy(PRPType.FACTORY_ANALYSIS)
        assert isinstance(strategy, FactoryAnalysisStrategy)
        
        # Get generation strategy
        strategy = registry.get_strategy(PRPType.FACTORY_GENERATION)
        assert isinstance(strategy, GenerationStrategy)
        
        # Get validation strategy
        strategy = registry.get_strategy(PRPType.VALIDATION_COMPREHENSIVE)
        assert isinstance(strategy, ValidationStrategy)
    
    def test_registry_errors(self, registry):
        """Test error handling for unknown types"""
        with pytest.raises(ValueError, match="No strategy registered"):
            registry.get_strategy(PRPType.WORKFLOW_OPTIMIZATION)
    
    def test_registry_replacement(self, registry):
        """Test replacing existing strategies"""
        # Get original strategy
        original = registry.get_strategy(PRPType.FACTORY_ANALYSIS)
        
        # Create and register replacement
        mock_strategy = Mock(spec=FactoryAnalysisStrategy)
        registry.register(PRPType.FACTORY_ANALYSIS, mock_strategy)
        
        # Get replaced strategy
        replaced = registry.get_strategy(PRPType.FACTORY_ANALYSIS)
        assert replaced == mock_strategy
        assert replaced != original
    
    def test_registry_lazy_instantiation(self, registry):
        """Test that strategies are instantiated lazily"""
        # Clear existing strategies
        registry._strategies.clear()
        
        # Strategy should not be instantiated yet
        assert PRPType.FACTORY_ANALYSIS not in registry._strategies
        
        # Get strategy - should instantiate it
        strategy = registry.get_strategy(PRPType.FACTORY_ANALYSIS)
        
        # Now it should be in the cache
        assert PRPType.FACTORY_ANALYSIS in registry._strategies
        assert isinstance(strategy, FactoryAnalysisStrategy)
    
    def test_list_registered_types(self, registry):
        """Test listing registered PRP types"""
        types = registry.list_registered_types()
        
        assert PRPType.FACTORY_ANALYSIS in types
        assert PRPType.FACTORY_GENERATION in types
        assert PRPType.VALIDATION_COMPREHENSIVE in types
        assert len(types) >= 3
    
    def test_unregister_strategy(self, registry):
        """Test unregistering a strategy"""
        # Verify strategy exists
        assert registry.has_strategy(PRPType.FACTORY_ANALYSIS)
        
        # Unregister it
        registry.unregister(PRPType.FACTORY_ANALYSIS)
        
        # Verify it's gone
        assert not registry.has_strategy(PRPType.FACTORY_ANALYSIS)
        
        with pytest.raises(ValueError):
            registry.get_strategy(PRPType.FACTORY_ANALYSIS)
    
    def test_clear_registry(self, registry):
        """Test clearing all strategies"""
        # Verify strategies exist
        assert len(registry.list_registered_types()) > 0
        
        # Clear registry
        registry.clear()
        
        # Verify all are gone
        assert len(registry.list_registered_types()) == 0
    
    def test_reload_defaults(self, registry):
        """Test reloading default strategies"""
        # Clear registry
        registry.clear()
        assert len(registry.list_registered_types()) == 0
        
        # Reload defaults
        registry.reload_defaults()
        
        # Verify defaults are back
        assert registry.has_strategy(PRPType.FACTORY_ANALYSIS)
        assert registry.has_strategy(PRPType.FACTORY_GENERATION)
        assert registry.has_strategy(PRPType.VALIDATION_COMPREHENSIVE)


class TestStrategyIntegration:
    """Integration tests for the entire strategy system"""
    
    @pytest.fixture
    def full_context(self, mock_project_profile, mock_context_package):
        """Create full context for testing"""
        return {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "user_request": "Create comprehensive agent team",
            "analysis_outputs": {
                "agents": ["frontend", "backend", "devops"],
                "workflows": ["deployment", "testing"]
            },
            "subagent_type": "agent-generator",
            "validation_scope": "comprehensive",
            "artifacts_to_validate": ["agent1.md", "workflow1.py"]
        }
    
    @pytest.mark.asyncio
    async def test_complete_factory_workflow(self, temp_workspace, mock_template_loader, full_context):
        """Test complete factory workflow from analysis to validation"""
        registry = PRPStrategyRegistry(temp_workspace, mock_template_loader)
        
        # Phase 1: Analysis
        analysis_strategy = registry.get_strategy(PRPType.FACTORY_ANALYSIS)
        analysis_prp = await analysis_strategy.generate({
            "project_profile": full_context["project_profile"],
            "context_package": full_context["context_package"],
            "user_request": full_context["user_request"]
        })
        assert analysis_prp.type == PRPType.FACTORY_ANALYSIS
        
        # Phase 2: Generation
        generation_strategy = registry.get_strategy(PRPType.FACTORY_GENERATION)
        generation_prp = await generation_strategy.generate({
            "project_profile": full_context["project_profile"],
            "context_package": full_context["context_package"],
            "analysis_outputs": full_context["analysis_outputs"],
            "subagent_type": full_context["subagent_type"]
        })
        assert generation_prp.type == PRPType.FACTORY_GENERATION
        
        # Phase 3: Validation
        validation_strategy = registry.get_strategy(PRPType.VALIDATION_COMPREHENSIVE)
        validation_prp = await validation_strategy.generate({
            "project_profile": full_context["project_profile"],
            "context_package": full_context["context_package"],
            "validation_scope": full_context["validation_scope"],
            "artifacts_to_validate": full_context["artifacts_to_validate"]
        })
        assert validation_prp.type == PRPType.VALIDATION_COMPREHENSIVE
        
        # Verify all PRPs were saved
        generated_dir = temp_workspace / "PRPs" / "generated"
        assert len(list(generated_dir.glob("*.md"))) == 3
        assert len(list(generated_dir.glob("*_meta.json"))) == 3
    
    @pytest.mark.asyncio
    async def test_parallel_strategy_execution(self, temp_workspace, mock_template_loader, full_context):
        """Test parallel execution of multiple strategies"""
        registry = PRPStrategyRegistry(temp_workspace, mock_template_loader)
        
        # Create tasks for parallel execution
        tasks = []
        
        # Multiple generation strategies for different subagents
        for subagent in ["claude-md-generator", "agent-generator", "workflow-generator"]:
            strategy = registry.get_strategy(PRPType.FACTORY_GENERATION)
            context = {
                "project_profile": full_context["project_profile"],
                "context_package": full_context["context_package"],
                "analysis_outputs": full_context["analysis_outputs"],
                "subagent_type": subagent
            }
            tasks.append(strategy.generate(context))
        
        # Execute all in parallel
        prps = await asyncio.gather(*tasks)
        
        # Verify all completed successfully
        assert len(prps) == 3
        assert all(prp.type == PRPType.FACTORY_GENERATION for prp in prps)
        assert all(prp.id is not None for prp in prps)
    
    @pytest.mark.asyncio
    async def test_strategy_error_handling(self, temp_workspace, mock_template_loader):
        """Test error handling in strategies"""
        registry = PRPStrategyRegistry(temp_workspace, mock_template_loader)
        
        # Test with invalid context
        strategy = registry.get_strategy(PRPType.FACTORY_ANALYSIS)
        
        with pytest.raises(ValueError, match="Missing required context keys"):
            await strategy.generate({})
        
        # Test with partial context
        with pytest.raises(ValueError):
            await strategy.generate({"project_profile": Mock()})


class TestPerformanceBenchmarks:
    """Performance benchmarks for strategy operations"""
    
    @pytest.mark.asyncio
    async def test_prp_generation_performance(self, temp_workspace, mock_template_loader, mock_project_profile, mock_context_package):
        """Benchmark PRP generation performance"""
        import time
        
        strategy = FactoryAnalysisStrategy(temp_workspace, mock_template_loader)
        context = {
            "project_profile": mock_project_profile,
            "context_package": mock_context_package,
            "user_request": "Performance test"
        }
        
        start = time.perf_counter()
        prp = await strategy.generate(context)
        end = time.perf_counter()
        
        generation_time = end - start
        
        # Should generate PRP in under 1 second
        assert generation_time < 1.0
        assert prp is not None
    
    @pytest.mark.asyncio
    async def test_registry_lookup_performance(self, temp_workspace, mock_template_loader):
        """Benchmark registry lookup performance"""
        import time
        
        registry = PRPStrategyRegistry(temp_workspace, mock_template_loader)
        
        start = time.perf_counter()
        for _ in range(100):
            strategy = registry.get_strategy(PRPType.FACTORY_ANALYSIS)
        end = time.perf_counter()
        
        lookup_time = (end - start) / 100
        
        # Average lookup should be under 1ms
        assert lookup_time < 0.001
    
    @pytest.mark.asyncio
    async def test_parallel_generation_scalability(self, temp_workspace, mock_template_loader, mock_project_profile, mock_context_package):
        """Test scalability with many parallel generations"""
        import time
        
        registry = PRPStrategyRegistry(temp_workspace, mock_template_loader)
        
        # Create 10 parallel generation tasks
        tasks = []
        for i in range(10):
            strategy = registry.get_strategy(PRPType.FACTORY_GENERATION)
            context = {
                "project_profile": mock_project_profile,
                "context_package": mock_context_package,
                "analysis_outputs": {},
                "subagent_type": f"generator-{i}"
            }
            tasks.append(strategy.generate(context))
        
        start = time.perf_counter()
        prps = await asyncio.gather(*tasks)
        end = time.perf_counter()
        
        total_time = end - start
        
        # Should complete all 10 in under 2 seconds
        assert total_time < 2.0
        assert len(prps) == 10
        assert all(prp is not None for prp in prps)


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])