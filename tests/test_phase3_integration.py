#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Phase 3 Refactoring
Tests all refactored components: PRP Generator, Context Engineer, Plugin Manager

This test suite validates:
1. PRP Generator Strategy Pattern implementation
2. Context Engineer modularization and type safety  
3. Plugin Manager DI Container and lifecycle
4. End-to-end workflow integration
5. Performance benchmarks
6. Architecture compliance

Created: 2025-09-05 17:30 UTC-3 São Paulo
"""

import asyncio
import inspect
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest

# Import refactored modules for testing
from subforge.core.prp import (
    PRPGenerator, 
    PRPType,
    create_prp_generator,
    create_fluent_builder,
    FactoryAnalysisStrategy,
    GenerationStrategy, 
    ValidationStrategy,
    PRPBuilder
)
from subforge.core.context_engineer import (
    ContextEngineer,
    ContextLevel,
    ContextPackage,
    create_context_engineer
)
from subforge.core.context.types import (
    ProjectContext,
    TechnicalContext,
    Example,
    Pattern,
    ValidationGate,
    TechStack,
    PreviousOutput,
    ContextPackageDict
)
from subforge.core.context.exceptions import (
    ContextError,
    InvalidProfileError,
    ValidationError,
    ContextGenerationError
)
from subforge.core.context.validators import (
    validate_project_context,
    validate_technical_context,
    validate_context_package_data
)
from subforge.plugins.plugin_manager import (
    PluginManager,
    SubForgePlugin,
    AgentPlugin,
    WorkflowPlugin,
    PluginMetadata
)
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity
)


@pytest.fixture
def workspace_dir():
    """Create temporary workspace directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_project_profile():
    """Create comprehensive project profile for testing"""
    return ProjectProfile(
        name="TestIntegrationProject",
        path=Path("/tmp/test_project"),
        technology_stack=TechnologyStack(
            languages={"python", "typescript", "javascript"},
            frameworks={"fastapi", "react", "nextjs"},
            databases={"postgresql", "redis"},
            tools={"docker", "pytest", "jest"},
            package_managers={"pip", "npm"}
        ),
        architecture_pattern=ArchitecturePattern.JAMSTACK,
        complexity=ProjectComplexity.ENTERPRISE,
        team_size_estimate=8,
        has_tests=True,
        has_ci_cd=True,
        has_docker=True,
        file_count=1292,
        lines_of_code=257891,
        has_docs=True,
        recommended_subagents=[
            "api-developer", "frontend-developer", "backend-developer",
            "test-engineer", "devops-engineer", "security-auditor"
        ],
        integration_requirements=["fastapi", "postgresql", "redis", "react"]
    )


@pytest.fixture
def sample_context_package():
    """Create sample context package for testing"""
    return ContextPackage(
        project_context=ProjectContext(
            name="TestProject",
            path="/tmp/test",
            architecture_pattern="jamstack", 
            complexity_level="enterprise",
            languages=["python", "typescript"],
            frameworks=["fastapi", "react"],
            databases=["postgresql"],
            tools=["docker"],
            team_size_estimate=8,
            has_tests=True,
            has_ci_cd=True,
            has_docker=True,
            file_count=1292,
            lines_of_code=257891
        ),
        technical_context=TechnicalContext(
            phase="analysis",
            primary_language="python", 
            deployment_target="cloud",
            testing_strategy="comprehensive",
            ci_cd_integration=True,
            analysis_depth="deep",
            discovery_areas=["architecture", "dependencies", "patterns"]
        ),
        examples=[],
        patterns=[],
        validation_gates=[],
        references=[],
        success_criteria=[]
    )


class TestPRPRefactoring:
    """Test refactored PRP Generator with Strategy Pattern"""
    
    @pytest.mark.asyncio
    async def test_strategy_pattern_works(self, workspace_dir, sample_project_profile, sample_context_package):
        """Test each strategy works independently with Strategy Pattern"""
        generator = create_prp_generator(workspace_dir)
        
        # Test Factory Analysis Strategy
        factory_context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "user_request": "Analyze project structure"
        }
        
        factory_prp = await generator.generate_prp(PRPType.FACTORY_ANALYSIS, factory_context)
        assert factory_prp is not None
        assert factory_prp.type == PRPType.FACTORY_ANALYSIS
        assert "Factory Analysis" in factory_prp.title
        
        # Test Generation Strategy
        generation_context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "analysis_outputs": {"complete": True},
            "subagent_type": "test-engineer"
        }
        
        generation_prp = await generator.generate_prp(PRPType.FACTORY_GENERATION, generation_context)
        assert generation_prp is not None
        assert generation_prp.type == PRPType.FACTORY_GENERATION
        assert "test-engineer" in generation_prp.id
        
        # Test Validation Strategy  
        validation_context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "validation_scope": "full_project",
            "artifacts_to_validate": ["tests/", "pytest.ini"]
        }
        
        validation_prp = await generator.generate_prp(PRPType.VALIDATION_COMPREHENSIVE, validation_context)
        assert validation_prp is not None
        assert validation_prp.type == PRPType.VALIDATION_COMPREHENSIVE
    
    @pytest.mark.asyncio
    async def test_template_loading(self, workspace_dir):
        """Verify external templates load correctly"""
        generator = PRPGenerator(workspace_dir)
        
        # Check template directories exist or are created
        templates_dir = workspace_dir / "templates"
        assert templates_dir.exists() or generator._ensure_templates_exist()
        
        # Test template loading for each strategy type
        strategies = generator.list_available_strategies()
        assert len(strategies) >= 3
        assert "factory_analysis" in strategies
        assert "factory_generation" in strategies
        assert "validation_comprehensive" in strategies
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self, workspace_dir, sample_project_profile, sample_context_package):
        """Ensure old API still works after refactoring"""
        generator = create_prp_generator(workspace_dir)
        
        # Test old method signatures still work
        old_style_prp = generator.generate_factory_analysis_prp(
            sample_project_profile,
            sample_context_package,
            "Test old API compatibility"
        )
        
        assert old_style_prp is not None
        assert old_style_prp.type == PRPType.FACTORY_ANALYSIS
        
        # Test factory generation old API
        old_generation_prp = generator.generate_factory_generation_prp(
            sample_project_profile,
            sample_context_package,
            {"analysis": "complete"},
            "legacy-agent"
        )
        
        assert old_generation_prp.type == PRPType.FACTORY_GENERATION
        assert "legacy-agent" in old_generation_prp.id
    
    def test_builder_pattern(self, sample_context_package):
        """Test PRPBuilder fluent interface"""
        builder = create_fluent_builder()
        
        # Test fluent builder pattern
        prp = (builder
            .for_project("IntegrationTest")
            .for_analysis()
            .with_context_package(sample_context_package)
            .with_execution_prompt("Build comprehensive test suite")
            .with_standard_analysis_checklist()
            .add_success_metric("All tests pass")
            .add_success_metric("Coverage >= 90%")
            .build())
        
        assert prp.id.startswith("integrationtest_")
        assert prp.type == PRPType.FACTORY_ANALYSIS
        assert "All tests pass" in prp.success_metrics
        assert "Coverage >= 90%" in prp.success_metrics
        assert len(prp.validation_checklist) > 0
        
        # Test builder reset functionality
        prp2 = (builder
            .for_project("SecondTest")
            .for_generation("custom-agent")
            .with_context_package(sample_context_package)
            .with_execution_prompt("Generate custom agent")
            .build())
        
        assert prp2.id != prp.id
        assert prp2.type == PRPType.FACTORY_GENERATION
        assert "custom-agent" in prp2.id

    def test_strategy_registration(self, workspace_dir):
        """Test strategy registration and discovery"""
        generator = PRPGenerator(workspace_dir)
        
        # Test strategy registry
        strategies = generator.list_available_strategies()
        assert isinstance(strategies, list)
        assert all(isinstance(s, str) for s in strategies)
        
        # Test strategy validation
        for strategy_name in strategies:
            assert generator._get_strategy(strategy_name) is not None


class TestContextRefactoring:
    """Test modularized Context Engineer"""
    
    def test_type_safety(self, workspace_dir, sample_project_profile):
        """Verify no Dict[str, Any] usage - all types are properly defined"""
        engineer = ContextEngineer(workspace_dir)
        
        # Build contexts and verify they return proper types
        project_context = engineer._build_project_context(sample_project_profile)
        assert isinstance(project_context, dict)
        # Validate it matches ProjectContext structure
        validate_project_context(project_context)
        
        technical_context = engineer._build_technical_context(sample_project_profile, "integration")
        assert isinstance(technical_context, dict)
        # Validate it matches TechnicalContext structure  
        validate_technical_context(technical_context)
        
        # Test validation gates return proper ValidationGate types
        gates = engineer._create_validation_gates("integration", sample_project_profile)
        assert isinstance(gates, list)
        for gate in gates:
            # Should not raise validation error
            validate_validation_gate = engineer._validate_gate_structure
            assert validate_validation_gate(gate)
    
    def test_module_separation(self, workspace_dir):
        """Test each module works independently"""
        engineer = ContextEngineer(workspace_dir)
        
        # Test builder module
        from subforge.core.context.builder import ContextBuilder
        builder = ContextBuilder(workspace_dir)
        assert builder is not None
        
        # Test repository module  
        from subforge.core.context.repository import ContextRepository
        repo = ContextRepository(workspace_dir)
        assert repo is not None
        
        # Test pattern extractor module
        from subforge.core.context.patterns import PatternExtractor  
        extractor = PatternExtractor()
        assert extractor is not None
        
        # Test cache module
        from subforge.core.context.cache import ContextCache
        cache = ContextCache()
        assert cache is not None
    
    def test_caching_works(self, workspace_dir, sample_project_profile):
        """Verify cache hit/miss behavior"""
        engineer = ContextEngineer(workspace_dir)
        
        # First call should be cache miss
        start_time = time.time()
        context1 = engineer.engineer_context(sample_project_profile, ContextLevel.COMPREHENSIVE)
        first_call_time = time.time() - start_time
        
        # Second call should be cache hit (faster)
        start_time = time.time()
        context2 = engineer.engineer_context(sample_project_profile, ContextLevel.COMPREHENSIVE)
        second_call_time = time.time() - start_time
        
        # Cache hit should be significantly faster
        assert second_call_time < first_call_time * 0.8  # At least 20% faster
        
        # Contexts should be equivalent
        assert context1.project_context == context2.project_context
        assert context1.technical_context == context2.technical_context
    
    def test_error_handling(self, workspace_dir):
        """Test custom exceptions are properly raised"""
        engineer = ContextEngineer(workspace_dir)
        
        # Test with invalid profile
        invalid_profile = Mock()
        invalid_profile.name = ""  # Invalid name
        invalid_profile.path = Path("/nonexistent")  # Invalid path
        
        with pytest.raises((ContextError, InvalidProfileError, ValidationError)):
            engineer.engineer_context(invalid_profile, ContextLevel.BASIC)
        
        # Test context generation error handling
        with patch('subforge.core.context_engineer.ContextEngineer._build_project_context') as mock_build:
            mock_build.side_effect = Exception("Simulated error")
            
            with pytest.raises(ContextGenerationError):
                engineer.engineer_context(sample_project_profile, ContextLevel.BASIC)

    def test_modular_imports(self):
        """Test all context modules can be imported independently"""
        # Test all modules can be imported without circular dependencies
        import subforge.core.context.types
        import subforge.core.context.exceptions  
        import subforge.core.context.validators
        import subforge.core.context.builder
        import subforge.core.context.repository
        import subforge.core.context.patterns
        import subforge.core.context.cache
        import subforge.core.context.enricher
        
        # Each module should have expected functionality
        assert hasattr(subforge.core.context.types, 'ProjectContext')
        assert hasattr(subforge.core.context.exceptions, 'ContextError')
        assert hasattr(subforge.core.context.validators, 'validate_project_context')


class TestPluginManagerRefactoring:
    """Test Plugin Manager DI Container and lifecycle"""
    
    def test_dependency_injection_container(self, workspace_dir):
        """Test DI container functionality"""
        plugin_manager = PluginManager(workspace_dir / "plugins")
        
        # Test plugin registration with dependencies
        plugin_count_before = len(plugin_manager.plugins)
        
        # Built-in plugins should be auto-registered
        assert plugin_count_before > 0
        assert len(plugin_manager.agent_plugins) > 0
        
        # Test dependency resolution (built-in plugins have no dependencies)
        for plugin_name, plugin in plugin_manager.plugins.items():
            metadata = plugin.get_metadata()
            assert isinstance(metadata.dependencies, list)
    
    def test_plugin_lifecycle(self, workspace_dir):
        """Test plugin lifecycle management"""
        plugin_manager = PluginManager(workspace_dir / "plugins")
        
        # Test plugin registration lifecycle
        initial_count = len(plugin_manager.plugins)
        
        # Create a test plugin
        class TestLifecyclePlugin(SubForgePlugin):
            def __init__(self):
                self.initialized = False
                self.executed = False
                self.cleaned_up = False
            
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="test_lifecycle",
                    version="1.0.0", 
                    author="Test",
                    description="Test plugin lifecycle",
                    type="test",
                    dependencies=[],
                    config={}
                )
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                self.initialized = True
                return True
            
            def execute(self, context: Dict[str, Any]) -> Any:
                self.executed = True
                return "test_result"
            
            def cleanup(self):
                self.cleaned_up = True
        
        test_plugin = TestLifecyclePlugin()
        
        # Test registration
        assert plugin_manager.register_plugin("test_lifecycle", test_plugin)
        assert test_plugin.initialized
        assert len(plugin_manager.plugins) == initial_count + 1
        
        # Test execution
        result = plugin_manager.execute_plugin("test_lifecycle", {})
        assert result == "test_result"
        assert test_plugin.executed
        
        # Test unregistration and cleanup
        assert plugin_manager.unregister_plugin("test_lifecycle")
        assert test_plugin.cleaned_up
        assert len(plugin_manager.plugins) == initial_count
    
    def test_plugin_validation(self, workspace_dir):
        """Test plugin validation during registration"""
        plugin_manager = PluginManager(workspace_dir / "plugins")
        
        # Test invalid plugin (fails validation)
        class InvalidPlugin(SubForgePlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="invalid",
                    version="1.0.0",
                    author="Test", 
                    description="Invalid plugin",
                    type="test",
                    dependencies=[],
                    config={}
                )
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                return True
            
            def execute(self, context: Dict[str, Any]) -> Any:
                return None
            
            def validate(self) -> bool:
                return False  # Always fails validation
        
        invalid_plugin = InvalidPlugin()
        
        # Should fail to register due to validation failure
        initial_count = len(plugin_manager.plugins)
        assert not plugin_manager.register_plugin("invalid", invalid_plugin)
        assert len(plugin_manager.plugins) == initial_count
    
    def test_agent_plugin_integration(self, workspace_dir, sample_project_profile):
        """Test agent plugin integration with project profiles"""
        plugin_manager = PluginManager(workspace_dir / "plugins")
        
        # Test agent plugin execution
        agent_plugins = plugin_manager.get_agent_plugins()
        assert len(agent_plugins) > 0
        
        # Test executing an agent plugin
        agent_name = agent_plugins[0]
        context = {"project_profile": sample_project_profile.__dict__}
        
        result = plugin_manager.execute_plugin(agent_name, context)
        assert isinstance(result, dict)
        assert "name" in result
        assert "tools" in result
        assert "context" in result


class TestRefactoringPerformance:
    """Ensure refactoring didn't degrade performance"""
    
    def benchmark_prp_generation(self, workspace_dir, sample_project_profile, sample_context_package, benchmark):
        """Measure PRP generation performance"""
        generator = create_prp_generator(workspace_dir)
        
        context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "user_request": "Performance test request"
        }
        
        def generate_prp():
            return asyncio.run(generator.generate_prp(PRPType.FACTORY_ANALYSIS, context))
        
        result = benchmark(generate_prp)
        assert result is not None
        assert result.type == PRPType.FACTORY_ANALYSIS
    
    def benchmark_context_engineering(self, workspace_dir, sample_project_profile, benchmark):
        """Measure context engineering performance"""
        engineer = create_context_engineer(workspace_dir)
        
        def engineer_context():
            return engineer.engineer_context(sample_project_profile, ContextLevel.COMPREHENSIVE)
        
        result = benchmark(engineer_context)
        assert result is not None
        assert isinstance(result, ContextPackage)
    
    def benchmark_memory_usage(self, workspace_dir, sample_project_profile, sample_context_package):
        """Check memory footprint of refactored components"""
        tracemalloc.start()
        
        # Test PRP Generator memory usage
        generator = create_prp_generator(workspace_dir)
        context = {
            "project_profile": sample_project_profile,
            "context_package": sample_context_package,
            "user_request": "Memory test"
        }
        
        prp = asyncio.run(generator.generate_prp(PRPType.FACTORY_ANALYSIS, context))
        
        # Test Context Engineer memory usage  
        engineer = create_context_engineer(workspace_dir)
        context_pkg = engineer.engineer_context(sample_project_profile, ContextLevel.COMPREHENSIVE)
        
        # Test Plugin Manager memory usage
        plugin_manager = PluginManager(workspace_dir / "plugins")
        plugin_manager.load_all_plugins()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be reasonable (less than 100MB peak)
        assert peak < 100 * 1024 * 1024  # 100MB threshold
        
        # Verify objects were created successfully
        assert prp is not None
        assert context_pkg is not None
        assert len(plugin_manager.plugins) > 0


class TestFullWorkflow:
    """Test complete workflow with refactored components"""
    
    @pytest.mark.asyncio
    async def test_full_subforge_workflow(self, workspace_dir, sample_project_profile):
        """Test complete SubForge workflow with all refactored components"""
        
        # 1. Initialize Context Engineer
        context_engineer = create_context_engineer(workspace_dir)
        
        # 2. Engineer comprehensive context
        context_package = context_engineer.engineer_context(
            sample_project_profile, 
            ContextLevel.COMPREHENSIVE
        )
        assert context_package is not None
        assert isinstance(context_package, ContextPackage)
        
        # 3. Initialize PRP Generator with strategy pattern
        prp_generator = create_prp_generator(workspace_dir)
        
        # 4. Generate analysis PRP using new strategy
        analysis_context = {
            "project_profile": sample_project_profile,
            "context_package": context_package,
            "user_request": "Create comprehensive test suite for enterprise project"
        }
        
        analysis_prp = await prp_generator.generate_prp(PRPType.FACTORY_ANALYSIS, analysis_context)
        assert analysis_prp is not None
        assert analysis_prp.type == PRPType.FACTORY_ANALYSIS
        
        # 5. Generate agent PRP using generation strategy
        generation_context = {
            "project_profile": sample_project_profile,
            "context_package": context_package,
            "analysis_outputs": {"comprehensive": True, "enterprise_ready": True},
            "subagent_type": "test-engineer"
        }
        
        generation_prp = await prp_generator.generate_prp(PRPType.FACTORY_GENERATION, generation_context)
        assert generation_prp is not None
        assert generation_prp.type == PRPType.FACTORY_GENERATION
        assert "test-engineer" in generation_prp.id
        
        # 6. Initialize Plugin Manager with DI container
        plugin_manager = PluginManager(workspace_dir / "plugins")
        
        # 7. Load and execute test-related plugins
        test_plugins = [name for name in plugin_manager.get_agent_plugins() 
                       if 'test' in name.lower() or 'quality' in name.lower()]
        
        if test_plugins:
            test_context = {"project_profile": sample_project_profile.__dict__}
            plugin_result = plugin_manager.execute_plugin(test_plugins[0], test_context)
            assert plugin_result is not None
            assert isinstance(plugin_result, dict)
        
        # 8. Generate validation PRP
        validation_context = {
            "project_profile": sample_project_profile,
            "context_package": context_package,
            "validation_scope": "full_project",
            "artifacts_to_validate": [
                "tests/", "pytest.ini", "jest.config.js",
                ".github/workflows/", "Dockerfile"
            ]
        }
        
        validation_prp = await prp_generator.generate_prp(PRPType.VALIDATION_COMPREHENSIVE, validation_context)
        assert validation_prp is not None
        assert validation_prp.type == PRPType.VALIDATION_COMPREHENSIVE
        
        # 9. Validate complete workflow results
        workflow_results = {
            "context_package": context_package,
            "analysis_prp": analysis_prp,
            "generation_prp": generation_prp,
            "validation_prp": validation_prp,
            "plugin_result": plugin_result if test_plugins else None
        }
        
        # All components should integrate seamlessly
        assert all(result is not None for key, result in workflow_results.items() 
                  if key != "plugin_result" or test_plugins)
        
        # Context package should contain enterprise-level details
        assert context_package.project_context["complexity_level"] == "enterprise"
        assert context_package.project_context["team_size_estimate"] == 8
        assert len(context_package.project_context["languages"]) >= 2
        assert len(context_package.project_context["frameworks"]) >= 2
        
        # PRPs should reference the context package
        assert analysis_prp.execution_prompt is not None
        assert generation_prp.execution_prompt is not None
        assert validation_prp.execution_prompt is not None


class TestModuleSize:
    """Validate refactoring achieved modularization goals"""
    
    def test_no_monolithic_files(self):
        """Ensure no file exceeds 300 lines after refactoring"""
        subforge_dir = Path(__file__).parent.parent / "subforge"
        
        large_files = []
        for py_file in subforge_dir.rglob("*.py"):
            if py_file.is_file():
                with open(py_file) as f:
                    lines = len(f.readlines())
                    if lines > 300:
                        large_files.append((py_file, lines))
        
        if large_files:
            file_list = "\n".join(f"  {file.relative_to(subforge_dir)}: {lines} lines" 
                                 for file, lines in large_files)
            pytest.fail(f"Files exceeding 300 lines found:\n{file_list}")
    
    def test_module_organization(self):
        """Test proper module organization"""
        subforge_dir = Path(__file__).parent.parent / "subforge"
        
        # Check PRP module structure
        prp_dir = subforge_dir / "core" / "prp"
        assert prp_dir.exists(), "PRP module directory not found"
        assert (prp_dir / "__init__.py").exists()
        assert (prp_dir / "base.py").exists()
        assert (prp_dir / "builder.py").exists()
        assert (prp_dir / "generator.py").exists()
        
        # Check Context module structure
        context_dir = subforge_dir / "core" / "context" 
        assert context_dir.exists(), "Context module directory not found"
        assert (context_dir / "__init__.py").exists()
        assert (context_dir / "types.py").exists()
        assert (context_dir / "builder.py").exists()
        assert (context_dir / "validators.py").exists()
        
        # Check Plugin module structure
        plugins_dir = subforge_dir / "plugins"
        assert plugins_dir.exists(), "Plugins module directory not found"
        assert (plugins_dir / "__init__.py").exists() 
        assert (plugins_dir / "plugin_manager.py").exists()


class TestTypeCoverage:
    """Verify type hints coverage"""
    
    def test_type_coverage(self):
        """Verify comprehensive type hints coverage"""
        from subforge.core.context_engineer import ContextEngineer
        from subforge.core.prp.generator import PRPGenerator
        
        # Test ContextEngineer methods have type hints
        for name, method in inspect.getmembers(ContextEngineer, inspect.isfunction):
            if not name.startswith('_'):  # Public methods
                sig = inspect.signature(method)
                for param_name, param in sig.parameters.items():
                    if param_name not in ['self', 'cls']:
                        assert param.annotation != inspect.Parameter.empty, (
                            f"Parameter {param_name} in {name} lacks type annotation"
                        )
        
        # Test PRPGenerator methods have type hints  
        for name, method in inspect.getmembers(PRPGenerator, inspect.isfunction):
            if not name.startswith('_'):  # Public methods
                sig = inspect.signature(method)
                for param_name, param in sig.parameters.items():
                    if param_name not in ['self', 'cls']:
                        assert param.annotation != inspect.Parameter.empty, (
                            f"Parameter {param_name} in {name} lacks type annotation"
                        )
    
    def test_no_any_usage(self):
        """Check for minimal Any usage in type hints"""
        import ast
        from pathlib import Path
        
        subforge_dir = Path(__file__).parent.parent / "subforge"
        any_usage = []
        
        for py_file in subforge_dir.rglob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file) as f:
                        tree = ast.parse(f.read())
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Subscript):
                            if (isinstance(node.value, ast.Name) and 
                                node.value.id == 'Dict' and
                                isinstance(node.slice, ast.Tuple) and
                                len(node.slice.elts) == 2 and
                                isinstance(node.slice.elts[1], ast.Name) and
                                node.slice.elts[1].id == 'Any'):
                                any_usage.append(str(py_file.relative_to(subforge_dir)))
                except:
                    continue  # Skip files that can't be parsed
        
        # Allow some Any usage but flag excessive usage
        if len(any_usage) > 5:
            pytest.fail(f"Too many Dict[str, Any] usages found in: {any_usage}")


class TestArchitectureCompliance:
    """Validate SOLID principles adherence"""
    
    def test_single_responsibility_principle(self):
        """Validate Single Responsibility Principle"""
        # Each class should have a single, well-defined responsibility
        
        from subforge.core.prp.generator import PRPGenerator
        from subforge.core.context.builder import ContextBuilder
        from subforge.core.context.repository import ContextRepository
        from subforge.plugins.plugin_manager import PluginManager
        
        # Test that classes have focused responsibilities
        # PRPGenerator should only generate PRPs
        prp_methods = [m for m in dir(PRPGenerator) if not m.startswith('_')]
        assert all('prp' in m.lower() or 'generate' in m.lower() or 'strategy' in m.lower() 
                  for m in prp_methods if not m in ['validate', 'initialize'])
        
        # ContextBuilder should only build contexts
        builder_methods = [m for m in dir(ContextBuilder) if not m.startswith('_')]
        # Methods should be focused on building/constructing
        assert any('build' in m.lower() or 'create' in m.lower() or 'construct' in m.lower()
                  for m in builder_methods)
    
    def test_dependency_inversion_principle(self):
        """Validate Dependency Inversion Principle"""
        # High-level modules should not depend on low-level modules
        # Both should depend on abstractions
        
        from subforge.core.prp.base import PRPStrategy
        from subforge.plugins.plugin_manager import SubForgePlugin
        
        # Strategies should inherit from abstract base
        from subforge.core.prp.generation_strategy import FactoryAnalysisStrategy
        assert issubclass(FactoryAnalysisStrategy, PRPStrategy)
        
        # Plugins should inherit from abstract base
        from subforge.plugins.plugin_manager import AgentPlugin
        assert issubclass(AgentPlugin, SubForgePlugin)
    
    def test_open_closed_principle(self):
        """Validate Open/Closed Principle"""
        # Classes should be open for extension, closed for modification
        
        from subforge.core.prp.base import PRPStrategy
        from subforge.plugins.plugin_manager import SubForgePlugin
        
        # Abstract classes should be extensible
        assert inspect.isabstract(PRPStrategy)
        assert inspect.isabstract(SubForgePlugin)
        
        # Concrete implementations should be easily extensible
        from subforge.core.prp.generation_strategy import FactoryAnalysisStrategy
        assert hasattr(FactoryAnalysisStrategy, 'generate')
        assert hasattr(FactoryAnalysisStrategy, 'validate')


if __name__ == "__main__":
    # Run tests with comprehensive output
    pytest.main([
        __file__, 
        "-v", 
        "--tb=short",
        "--durations=10",  # Show 10 slowest tests
        "--cov=subforge.core.prp",
        "--cov=subforge.core.context", 
        "--cov=subforge.plugins",
        "--cov-report=term-missing"
    ])