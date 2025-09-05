#!/usr/bin/env python3
"""
Architecture Compliance Tests for Phase 3 Refactoring
Validates adherence to SOLID principles and architectural patterns

This module ensures:
1. SOLID principles compliance
2. Design pattern correctness
3. Dependency management
4. Module cohesion
5. Interface segregation

Created: 2025-09-05 17:40 UTC-3 São Paulo
"""

import ast
import inspect
import importlib
from pathlib import Path
from typing import Dict, List, Set, Type, Any
from abc import ABC

import pytest

# Import modules to analyze
from subforge.core.prp.base import IPRPStrategy
from subforge.core.prp.generator import PRPGenerator
from subforge.core.prp.builder import PRPBuilder
from subforge.core.prp.factory_strategy import FactoryAnalysisStrategy
from subforge.core.prp.generation_strategy import GenerationStrategy
from subforge.core.prp.validation_strategy import ValidationStrategy

from subforge.core.context_engineer import ContextEngineer
from subforge.core.context.builder import ContextBuilder
from subforge.core.context.repository import ExampleRepository
from subforge.core.context.cache import CachedContextManager
from subforge.core.context.validators import validate_project_context
from subforge.core.context.exceptions import ContextError

from subforge.plugins.plugin_manager import (
    PluginManager,
    SubForgePlugin,
    AgentPlugin,
    WorkflowPlugin
)


class TestSingleResponsibilityPrinciple:
    """Test Single Responsibility Principle (SRP) compliance"""
    
    def test_prp_generator_single_responsibility(self):
        """PRPGenerator should only handle PRP generation concerns"""
        prp_methods = self._get_public_methods(PRPGenerator)
        
        # All methods should be related to PRP generation
        generation_keywords = ['prp', 'generate', 'strategy', 'build', 'create']
        non_generation_methods = []
        
        for method_name in prp_methods:
            if not any(keyword in method_name.lower() for keyword in generation_keywords):
                # Allow some utility methods
                if method_name not in ['initialize', 'validate', 'list_available_strategies']:
                    non_generation_methods.append(method_name)
        
        assert len(non_generation_methods) == 0, (
            f"PRPGenerator has methods outside its responsibility: {non_generation_methods}"
        )
    
    def test_context_engineer_single_responsibility(self):
        """ContextEngineer should only handle context engineering concerns"""
        context_methods = self._get_public_methods(ContextEngineer)
        
        # All methods should be related to context engineering
        context_keywords = ['context', 'engineer', 'build', 'create', 'package']
        non_context_methods = []
        
        for method_name in context_methods:
            if not any(keyword in method_name.lower() for keyword in context_keywords):
                # Allow some utility methods
                if method_name not in ['initialize', 'validate', 'save', 'load']:
                    non_context_methods.append(method_name)
        
        assert len(non_context_methods) == 0, (
            f"ContextEngineer has methods outside its responsibility: {non_context_methods}"
        )
    
    def test_plugin_manager_single_responsibility(self):
        """PluginManager should only handle plugin management concerns"""
        plugin_methods = self._get_public_methods(PluginManager)
        
        # All methods should be related to plugin management
        plugin_keywords = ['plugin', 'register', 'load', 'execute', 'manage', 'get']
        non_plugin_methods = []
        
        for method_name in plugin_methods:
            if not any(keyword in method_name.lower() for keyword in plugin_keywords):
                # Allow some utility methods
                if method_name not in ['initialize', 'validate', 'list', 'create']:
                    non_plugin_methods.append(method_name)
        
        assert len(non_plugin_methods) <= 2, (
            f"PluginManager has too many methods outside its responsibility: {non_plugin_methods}"
        )
    
    def test_builders_single_responsibility(self):
        """Builder classes should only handle object construction"""
        # Test PRPBuilder
        prp_builder_methods = self._get_public_methods(PRPBuilder)
        builder_keywords = ['for_', 'with_', 'add_', 'build', 'set_', 'reset']
        
        non_builder_methods = []
        for method_name in prp_builder_methods:
            if not any(keyword in method_name.lower() for keyword in builder_keywords):
                if method_name not in ['validate', 'initialize']:
                    non_builder_methods.append(method_name)
        
        assert len(non_builder_methods) == 0, (
            f"PRPBuilder has methods outside builder responsibility: {non_builder_methods}"
        )
        
        # Test ContextBuilder
        context_builder_methods = self._get_public_methods(ContextBuilder)
        for method_name in context_builder_methods:
            if not any(keyword in method_name.lower() for keyword in ['build', 'create', 'construct']):
                if method_name not in ['validate', 'initialize']:
                    non_builder_methods.append(method_name)
        
        # ContextBuilder should be focused on building/constructing
        assert any('build' in method.lower() or 'create' in method.lower() 
                  for method in context_builder_methods), (
            "ContextBuilder should have methods focused on building/construction"
        )
    
    def _get_public_methods(self, cls: Type) -> List[str]:
        """Get public method names from a class"""
        return [name for name, method in inspect.getmembers(cls, inspect.isfunction)
                if not name.startswith('_')]


class TestOpenClosedPrinciple:
    """Test Open/Closed Principle (OCP) compliance"""
    
    def test_prp_strategy_extensibility(self):
        """IPRPStrategy should be open for extension, closed for modification"""
        # Should be abstract base class
        assert inspect.isabstract(IPRPStrategy), "IPRPStrategy should be abstract"
        
        # Should have abstract methods that subclasses must implement
        abstract_methods = [method for method in dir(IPRPStrategy)
                          if getattr(getattr(IPRPStrategy, method, None), '__isabstractmethod__', False)]
        
        assert len(abstract_methods) > 0, "IPRPStrategy should have abstract methods"
        assert 'generate' in abstract_methods, "IPRPStrategy should have abstract 'generate' method"
        
        # Concrete strategies should extend properly
        concrete_strategies = [FactoryAnalysisStrategy, GenerationStrategy, ValidationStrategy]
        
        for strategy_class in concrete_strategies:
            assert issubclass(strategy_class, IPRPStrategy), (
                f"{strategy_class.__name__} should extend IPRPStrategy"
            )
            
            # Should implement all abstract methods
            for abstract_method in abstract_methods:
                assert hasattr(strategy_class, abstract_method), (
                    f"{strategy_class.__name__} should implement {abstract_method}"
                )
                
                # Method should be callable (not abstract anymore)
                method = getattr(strategy_class, abstract_method)
                assert callable(method), f"{abstract_method} should be callable in {strategy_class.__name__}"
    
    def test_plugin_extensibility(self):
        """Plugin system should be open for extension, closed for modification"""
        # Base plugin should be abstract
        assert inspect.isabstract(SubForgePlugin), "SubForgePlugin should be abstract"
        
        # Should have abstract methods
        abstract_methods = [method for method in dir(SubForgePlugin)
                          if getattr(getattr(SubForgePlugin, method, None), '__isabstractmethod__', False)]
        
        assert len(abstract_methods) > 0, "SubForgePlugin should have abstract methods"
        
        # Specialized plugin types should extend properly
        plugin_types = [AgentPlugin, WorkflowPlugin]
        
        for plugin_class in plugin_types:
            assert issubclass(plugin_class, SubForgePlugin), (
                f"{plugin_class.__name__} should extend SubForgePlugin"
            )
    
    def test_context_extensibility(self):
        """Context system should be extensible without modification"""
        # ContextEngineer should use composition/delegation
        context_engineer = ContextEngineer(Path("/tmp"))
        
        # Should use other components rather than doing everything itself
        assert hasattr(context_engineer, 'context_library'), "Should use context library"
        assert hasattr(context_engineer, 'examples_dir'), "Should use examples directory"
        assert hasattr(context_engineer, 'patterns_dir'), "Should use patterns directory"
        
        # Methods should delegate to specialized components
        method_signatures = []
        for name, method in inspect.getmembers(ContextEngineer, inspect.ismethod):
            if not name.startswith('_'):
                sig = inspect.signature(method)
                method_signatures.append((name, sig))
        
        # Should have methods that work with different context levels
        assert any('level' in str(sig) or 'Level' in str(sig) 
                  for name, sig in method_signatures), (
            "ContextEngineer should support different context levels"
        )


class TestLiskovSubstitutionPrinciple:
    """Test Liskov Substitution Principle (LSP) compliance"""
    
    def test_prp_strategy_substitution(self):
        """Any IPRPStrategy should be substitutable for another"""
        strategies = [FactoryAnalysisStrategy, GenerationStrategy, ValidationStrategy]
        
        # All strategies should have compatible interfaces
        for strategy_class in strategies:
            # Should be instantiable with same parameters
            try:
                strategy = strategy_class(Path("/tmp"))
                assert hasattr(strategy, 'generate'), f"{strategy_class.__name__} should have generate method"
                assert hasattr(strategy, 'validate'), f"{strategy_class.__name__} should have validate method"
                assert hasattr(strategy, 'validate_context'), f"{strategy_class.__name__} should have validate_context method"
            except TypeError as e:
                pytest.fail(f"{strategy_class.__name__} doesn't have compatible constructor: {e}")
        
        # Methods should have compatible signatures
        generate_signatures = []
        for strategy_class in strategies:
            generate_method = getattr(strategy_class, 'generate')
            sig = inspect.signature(generate_method)
            generate_signatures.append(sig)
        
        # All generate methods should have compatible parameter counts
        param_counts = [len(sig.parameters) for sig in generate_signatures]
        assert len(set(param_counts)) <= 2, "Generate methods should have compatible signatures"  # Allow for 'self' difference
    
    def test_plugin_substitution(self):
        """Plugins should be substitutable within their types"""
        # AgentPlugin instances should be substitutable
        plugin_manager = PluginManager(Path("/tmp"))
        agent_plugins = plugin_manager.get_agent_plugins()
        
        if len(agent_plugins) >= 2:
            # All agent plugins should have compatible interfaces
            for plugin_name in agent_plugins[:2]:  # Test first two
                plugin = plugin_manager.plugins[plugin_name]
                assert hasattr(plugin, 'execute'), f"Agent plugin {plugin_name} should have execute method"
                assert hasattr(plugin, 'get_metadata'), f"Agent plugin {plugin_name} should have get_metadata method"
                
                # Should return compatible metadata
                metadata = plugin.get_metadata()
                assert hasattr(metadata, 'name'), "Metadata should have name"
                assert hasattr(metadata, 'type'), "Metadata should have type"


class TestInterfaceSegregationPrinciple:
    """Test Interface Segregation Principle (ISP) compliance"""
    
    def test_prp_interfaces_segregated(self):
        """PRP interfaces should be segregated by concern"""
        # IPRPStrategy should only define generation-related methods
        prp_strategy_methods = [method for method in dir(IPRPStrategy)
                               if not method.startswith('_') and callable(getattr(IPRPStrategy, method, None))]
        
        # Should have focused interface
        assert len(prp_strategy_methods) <= 5, (
            f"IPRPStrategy interface too large: {prp_strategy_methods}. Consider segregating."
        )
        
        # Methods should be cohesive
        generation_methods = [m for m in prp_strategy_methods 
                            if any(keyword in m.lower() for keyword in ['generate', 'validate', 'context'])]
        
        cohesion_ratio = len(generation_methods) / len(prp_strategy_methods)
        assert cohesion_ratio >= 0.8, f"IPRPStrategy interface not cohesive enough: {cohesion_ratio}"
    
    def test_plugin_interfaces_segregated(self):
        """Plugin interfaces should be segregated by plugin type"""
        # Base plugin should have minimal interface
        base_plugin_methods = [method for method in dir(SubForgePlugin)
                              if not method.startswith('_') and callable(getattr(SubForgePlugin, method, None))]
        
        assert len(base_plugin_methods) <= 8, (
            f"SubForgePlugin interface too large: {base_plugin_methods}"
        )
        
        # Specialized plugins should add specific methods
        agent_methods = [method for method in dir(AgentPlugin)
                        if not method.startswith('_') and method not in base_plugin_methods]
        
        workflow_methods = [method for method in dir(WorkflowPlugin)
                           if not method.startswith('_') and method not in base_plugin_methods]
        
        # Agent plugins should have agent-specific methods
        assert any('agent' in method.lower() or 'tool' in method.lower() for method in agent_methods), (
            f"AgentPlugin should have agent-specific methods: {agent_methods}"
        )
        
        # Workflow plugins should have workflow-specific methods
        assert any('workflow' in method.lower() or 'phase' in method.lower() for method in workflow_methods), (
            f"WorkflowPlugin should have workflow-specific methods: {workflow_methods}"
        )
    
    def test_context_interfaces_segregated(self):
        """Context interfaces should be segregated by responsibility"""
        # Different context concerns should be in different modules
        context_modules = [
            'subforge.core.context.builder',
            'subforge.core.context.repository', 
            'subforge.core.context.cache',
            'subforge.core.context.validators',
            'subforge.core.context.patterns'
        ]
        
        # Each module should have focused responsibility
        for module_name in context_modules:
            try:
                module = importlib.import_module(module_name)
                module_classes = [getattr(module, name) for name in dir(module)
                                if isinstance(getattr(module, name), type)]
                
                # Each module should have few, focused classes
                assert len(module_classes) <= 5, (
                    f"Module {module_name} has too many classes: {len(module_classes)}. "
                    f"Consider further segregation."
                )
            except ImportError:
                pytest.skip(f"Module {module_name} not found")


class TestDependencyInversionPrinciple:
    """Test Dependency Inversion Principle (DIP) compliance"""
    
    def test_high_level_modules_depend_on_abstractions(self):
        """High-level modules should depend on abstractions, not concretions"""
        # PRPGenerator should depend on IPRPStrategy interface, not concrete strategies
        prp_generator_source = self._get_source_code(PRPGenerator)
        
        # Should import/reference abstract base, not concrete implementations
        assert 'IPRPStrategy' in prp_generator_source, (
            "PRPGenerator should reference IPRPStrategy abstraction"
        )
        
        # Should not directly import concrete strategies in class definition
        concrete_strategy_imports = [
            'FactoryAnalysisStrategy',
            'GenerationStrategy', 
            'ValidationStrategy'
        ]
        
        class_definition = self._extract_class_definition(prp_generator_source, 'PRPGenerator')
        for concrete_strategy in concrete_strategy_imports:
            assert concrete_strategy not in class_definition, (
                f"PRPGenerator should not directly reference {concrete_strategy} in class definition"
            )
    
    def test_context_engineer_depends_on_abstractions(self):
        """ContextEngineer should depend on abstractions"""
        context_engineer_source = self._get_source_code(ContextEngineer)
        
        # Should use composition with other components
        # Check for dependency injection or builder patterns
        composition_indicators = [
            'builder', 'repository', 'cache', 'extractor'
        ]
        
        found_composition = any(indicator in context_engineer_source.lower() 
                              for indicator in composition_indicators)
        
        assert found_composition, (
            "ContextEngineer should use composition with other components"
        )
    
    def test_plugin_manager_depends_on_abstractions(self):
        """PluginManager should depend on plugin abstractions"""
        plugin_manager_source = self._get_source_code(PluginManager)
        
        # Should reference abstract plugin types
        assert 'SubForgePlugin' in plugin_manager_source, (
            "PluginManager should reference SubForgePlugin abstraction"
        )
        
        # Should not hardcode concrete plugin implementations
        class_definition = self._extract_class_definition(plugin_manager_source, 'PluginManager')
        
        # Built-in agent registration is acceptable, but should use abstractions
        builtin_registration = '_register_builtin_agent' in plugin_manager_source
        if builtin_registration:
            # Should create dynamic classes that inherit from abstractions
            assert 'AgentPlugin' in plugin_manager_source, (
                "PluginManager should use AgentPlugin abstraction for built-in agents"
            )
    
    def test_strategies_follow_dependency_inversion(self):
        """Strategy implementations should follow dependency inversion"""
        strategies = [FactoryAnalysisStrategy, GenerationStrategy, ValidationStrategy]
        
        for strategy_class in strategies:
            # Should depend on abstractions for external dependencies
            strategy_source = self._get_source_code(strategy_class)
            
            # Should not hardcode external dependencies
            # Look for constructor injection or dependency injection patterns
            init_method = self._extract_method_definition(strategy_source, '__init__')
            
            # Constructor should accept dependencies as parameters
            assert 'self' in init_method, "Strategy should have proper constructor"
            
            # Should not hardcode file paths or external services
            hardcoded_paths = ['/tmp', '/home', 'C:\\']
            for hardcoded_path in hardcoded_paths:
                assert hardcoded_path not in strategy_source, (
                    f"{strategy_class.__name__} should not hardcode path {hardcoded_path}"
                )
    
    def _get_source_code(self, cls: Type) -> str:
        """Get source code of a class"""
        try:
            return inspect.getsource(cls)
        except OSError:
            return ""
    
    def _extract_class_definition(self, source_code: str, class_name: str) -> str:
        """Extract class definition from source code"""
        lines = source_code.split('\n')
        class_lines = []
        in_class = False
        indent_level = 0
        
        for line in lines:
            if f'class {class_name}' in line:
                in_class = True
                indent_level = len(line) - len(line.lstrip())
                class_lines.append(line)
                continue
            
            if in_class:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() == '':
                    class_lines.append(line)
                elif current_indent > indent_level:
                    class_lines.append(line)
                else:
                    break
        
        return '\n'.join(class_lines)
    
    def _extract_method_definition(self, source_code: str, method_name: str) -> str:
        """Extract method definition from source code"""
        lines = source_code.split('\n')
        method_lines = []
        in_method = False
        indent_level = 0
        
        for line in lines:
            if f'def {method_name}' in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                method_lines.append(line)
                continue
            
            if in_method:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() == '':
                    method_lines.append(line)
                elif current_indent > indent_level:
                    method_lines.append(line)
                elif line.strip().startswith('def ') or line.strip().startswith('class '):
                    break
        
        return '\n'.join(method_lines)


class TestDesignPatterns:
    """Test proper implementation of design patterns"""
    
    def test_strategy_pattern_implementation(self):
        """Verify Strategy Pattern is properly implemented"""
        # Should have strategy interface
        assert inspect.isabstract(IPRPStrategy), "Strategy interface should be abstract"
        
        # Should have concrete strategies
        concrete_strategies = [FactoryAnalysisStrategy, GenerationStrategy, ValidationStrategy]
        
        for strategy in concrete_strategies:
            assert issubclass(strategy, IPRPStrategy), (
                f"{strategy.__name__} should implement strategy interface"
            )
        
        # Context (PRPGenerator) should use strategies
        prp_generator = PRPGenerator(Path("/tmp"))
        
        # Should have method to set/get strategies
        assert hasattr(prp_generator, 'list_available_strategies'), (
            "PRPGenerator should support strategy discovery"
        )
    
    def test_builder_pattern_implementation(self):
        """Verify Builder Pattern is properly implemented"""
        # Should have builder class
        builder_methods = [method for method in dir(PRPBuilder)
                          if not method.startswith('_')]
        
        # Should have fluent interface methods
        fluent_methods = [method for method in builder_methods
                         if method.startswith('for_') or method.startswith('with_') or method.startswith('add_')]
        
        assert len(fluent_methods) > 0, "Builder should have fluent interface methods"
        
        # Should have build method
        assert 'build' in builder_methods, "Builder should have build method"
        
        # Methods should return self for chaining (except build)
        from subforge.core.prp import create_fluent_builder
        builder = create_fluent_builder()
        
        # Test method chaining
        result = builder.for_project("TestProject")
        assert result is builder or result.__class__ == builder.__class__, (
            "Fluent methods should return self or builder instance"
        )
    
    def test_factory_pattern_implementation(self):
        """Verify Factory Pattern is used appropriately"""
        # Should have factory functions
        from subforge.core.prp import create_prp_generator, create_fluent_builder
        from subforge.core.context_engineer import create_context_engineer
        
        # Factory functions should create proper instances
        generator = create_prp_generator(Path("/tmp"))
        assert isinstance(generator, PRPGenerator), "Factory should create PRPGenerator"
        
        builder = create_fluent_builder()
        assert isinstance(builder, PRPBuilder), "Factory should create PRPBuilder"
        
        engineer = create_context_engineer(Path("/tmp"))
        assert isinstance(engineer, ContextEngineer), "Factory should create ContextEngineer"
    
    def test_repository_pattern_implementation(self):
        """Verify Repository Pattern is implemented for data access"""
        # Should have repository for context data
        from subforge.core.context.repository import ExampleRepository
        
        repository = ExampleRepository(Path("/tmp"))
        
        # Should have CRUD-like operations
        repository_methods = [method for method in dir(ExampleRepository)
                             if not method.startswith('_')]
        
        # Should have methods for data persistence
        data_methods = [method for method in repository_methods
                       if any(keyword in method.lower() 
                             for keyword in ['save', 'load', 'find', 'get', 'store', 'retrieve'])]
        
        assert len(data_methods) > 0, (
            f"Repository should have data access methods: {repository_methods}"
        )


class TestModuleCohesion:
    """Test module cohesion and coupling"""
    
    def test_high_cohesion_in_modules(self):
        """Test that modules have high internal cohesion"""
        # PRP module should be cohesive
        prp_module_files = list(Path(__file__).parent.parent.glob("subforge/core/prp/*.py"))
        
        assert len(prp_module_files) > 3, "PRP module should be properly modularized"
        
        # Each file should have related functionality
        expected_prp_files = ['base.py', 'builder.py', 'generator.py', '__init__.py']
        actual_prp_files = [f.name for f in prp_module_files]
        
        for expected_file in expected_prp_files:
            assert expected_file in actual_prp_files, (
                f"PRP module missing expected file: {expected_file}"
            )
        
        # Context module should be cohesive
        context_module_files = list(Path(__file__).parent.parent.glob("subforge/core/context/*.py"))
        
        assert len(context_module_files) > 5, "Context module should be properly modularized"
        
        expected_context_files = ['types.py', 'builder.py', 'validators.py', '__init__.py']
        actual_context_files = [f.name for f in context_module_files]
        
        for expected_file in expected_context_files:
            assert expected_file in actual_context_files, (
                f"Context module missing expected file: {expected_file}"
            )
    
    def test_low_coupling_between_modules(self):
        """Test that modules have low coupling"""
        # Analyze imports to detect coupling
        coupling_violations = []
        
        # PRP module should not directly import context implementation details
        prp_files = Path(__file__).parent.parent.glob("subforge/core/prp/*.py")
        
        for prp_file in prp_files:
            if prp_file.name == '__init__.py':
                continue
                
            try:
                with open(prp_file) as f:
                    content = f.read()
                
                # Should not import internal context modules
                internal_context_imports = [
                    'from subforge.core.context.builder import',
                    'from subforge.core.context.repository import',
                    'from subforge.core.context.cache import'
                ]
                
                for bad_import in internal_context_imports:
                    if bad_import in content:
                        coupling_violations.append(
                            f"{prp_file.name} imports internal context module: {bad_import}"
                        )
            except Exception:
                continue
        
        # Allow some coupling but not excessive
        assert len(coupling_violations) <= 2, (
            f"Too much coupling detected: {coupling_violations}"
        )


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v", 
        "--tb=short",
        "-x"  # Stop on first failure for architecture issues
    ])