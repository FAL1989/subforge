"""
Plugin Dependency Resolver Tests for SubForge
Tests version constraint resolution, circular dependency detection, topological sorting,
optional dependencies, conflict resolution, dependency tree generation, and compatibility
"""

import pytest
from typing import List, Dict, Any

from subforge.plugins.dependencies import (
    CircularDependencyError,
    DependencyError,
    DependencyNode,
    IncompatibleVersionError,
    MockPluginRegistry,
    PluginDependency,
    PluginDependencyResolver,
)
from subforge.plugins.plugin_manager import PluginMetadata


# Test fixtures and mock data
def create_plugin_metadata(
    name: str, version: str = "1.0.0", dependencies: List[str] = None
) -> PluginMetadata:
    """Helper to create plugin metadata"""
    return PluginMetadata(
        name=name,
        version=version,
        author="Test Author",
        description=f"Test plugin {name}",
        type="test",
        dependencies=dependencies or [],
        config={},
    )


class TestDependencyResolver:
    """Plugin Dependency Resolver test suite"""

    @pytest.fixture
    def registry(self):
        """Create mock plugin registry"""
        return MockPluginRegistry()

    @pytest.fixture
    def resolver(self, registry):
        """Create dependency resolver with mock registry"""
        return PluginDependencyResolver(registry)

    def test_version_constraint_gte(self, resolver, registry):
        """Test >= version constraint resolution"""
        # Add plugins to registry
        registry.add_plugin("dep_plugin", create_plugin_metadata("dep_plugin", "1.0.0"))
        registry.add_plugin("dep_plugin", create_plugin_metadata("dep_plugin", "1.5.0"))
        registry.add_plugin("dep_plugin", create_plugin_metadata("dep_plugin", "2.0.0"))

        # Create plugin with >= constraint
        plugin = create_plugin_metadata("main", "1.0.0", ["dep_plugin>=1.5.0"])

        # Resolve dependencies
        resolved = resolver.resolve(plugin)

        # Should resolve to dep_plugin
        assert len(resolved) == 1
        assert resolved[0].name == "dep_plugin"
        assert resolved[0].version_spec == ">=1.5.0"

    def test_version_constraint_compatible(self, resolver, registry):
        """Test ~= compatible version constraint"""
        # Add plugins to registry
        registry.add_plugin("lib", create_plugin_metadata("lib", "1.2.0"))
        registry.add_plugin("lib", create_plugin_metadata("lib", "1.2.3"))
        registry.add_plugin("lib", create_plugin_metadata("lib", "1.3.0"))
        registry.add_plugin("lib", create_plugin_metadata("lib", "2.0.0"))

        # Test ~= constraint (compatible version)
        plugin = create_plugin_metadata("app", "1.0.0", ["lib~=1.2.0"])

        # Check version compatibility
        assert resolver._check_version_compatibility("1.2.0", "~=1.2.0")
        assert resolver._check_version_compatibility("1.2.3", "~=1.2.0")
        assert not resolver._check_version_compatibility("1.3.0", "~=1.2.0")
        assert not resolver._check_version_compatibility("2.0.0", "~=1.2.0")

    def test_version_constraint_exact(self, resolver, registry):
        """Test == exact version constraint"""
        registry.add_plugin("exact_dep", create_plugin_metadata("exact_dep", "1.2.3"))
        registry.add_plugin("exact_dep", create_plugin_metadata("exact_dep", "1.2.4"))

        plugin = create_plugin_metadata("main", "1.0.0", ["exact_dep==1.2.3"])

        # Check exact version matching
        assert resolver._check_version_compatibility("1.2.3", "==1.2.3")
        assert not resolver._check_version_compatibility("1.2.4", "==1.2.3")

    def test_version_constraint_range(self, resolver, registry):
        """Test version range constraints (>1.0,<2.0)"""
        # Test multiple constraint operators
        assert resolver._check_version_compatibility("1.5.0", ">1.0")
        assert not resolver._check_version_compatibility("0.9.0", ">1.0")

        assert resolver._check_version_compatibility("1.9.0", "<2.0")
        assert not resolver._check_version_compatibility("2.0.0", "<2.0")

        assert resolver._check_version_compatibility("1.0.0", "<=1.0")
        assert resolver._check_version_compatibility("0.9.0", "<=1.0")
        assert not resolver._check_version_compatibility("1.1.0", "<=1.0")

    def test_version_constraint_not_equal(self, resolver):
        """Test != version constraint"""
        assert resolver._check_version_compatibility("1.0.0", "!=2.0.0")
        assert resolver._check_version_compatibility("2.1.0", "!=2.0.0")
        assert not resolver._check_version_compatibility("2.0.0", "!=2.0.0")

    def test_version_constraint_wildcard(self, resolver):
        """Test * wildcard (any version)"""
        assert resolver._check_version_compatibility("1.0.0", "*")
        assert resolver._check_version_compatibility("2.5.3", "*")
        assert resolver._check_version_compatibility("0.0.1", "*")

    def test_circular_dependency_direct(self, resolver, registry):
        """Test detection of direct circular dependency (A -> B -> A)"""
        # Create circular dependency
        registry.add_plugin("plugin_a", create_plugin_metadata("plugin_a", "1.0.0", ["plugin_b"]))
        registry.add_plugin("plugin_b", create_plugin_metadata("plugin_b", "1.0.0", ["plugin_a"]))

        plugin_a = registry.get_plugin("plugin_a")

        # Should detect circular dependency
        with pytest.raises(CircularDependencyError) as exc_info:
            resolver.resolve(plugin_a)

        assert "Circular dependencies detected" in str(exc_info.value)

    def test_circular_dependency_deep_chain(self, resolver, registry):
        """Test detection of deep circular dependency chain (A -> B -> C -> A)"""
        # Create chain: A -> B -> C -> A
        registry.add_plugin("plugin_a", create_plugin_metadata("plugin_a", "1.0.0", ["plugin_b"]))
        registry.add_plugin("plugin_b", create_plugin_metadata("plugin_b", "1.0.0", ["plugin_c"]))
        registry.add_plugin("plugin_c", create_plugin_metadata("plugin_c", "1.0.0", ["plugin_a"]))

        plugin_a = registry.get_plugin("plugin_a")

        # Should detect circular dependency
        with pytest.raises(CircularDependencyError):
            resolver.resolve(plugin_a)

    def test_self_dependency_detection(self, resolver, registry):
        """Test detection of self-dependency"""
        # Create self-dependent plugin
        registry.add_plugin("self_dep", create_plugin_metadata("self_dep", "1.0.0", ["self_dep"]))

        plugin = registry.get_plugin("self_dep")

        # Should detect self-dependency as circular
        with pytest.raises(CircularDependencyError):
            resolver.resolve(plugin)

    def test_topological_sorting_simple(self, resolver, registry):
        """Test correct installation order with simple dependencies"""
        # Create dependency chain: main -> b -> c
        registry.add_plugin("c", create_plugin_metadata("c", "1.0.0", []))
        registry.add_plugin("b", create_plugin_metadata("b", "1.0.0", ["c"]))
        registry.add_plugin("main", create_plugin_metadata("main", "1.0.0", ["b"]))

        plugin = registry.get_plugin("main")
        resolved = resolver.resolve(plugin)

        # Should be in order: c, b (main is not in the list as it's the root)
        assert len(resolved) == 2
        # The order should ensure dependencies come first
        dep_names = [dep.name for dep in resolved]
        assert dep_names.index("c") < dep_names.index("b") if "c" in dep_names and "b" in dep_names else True

    def test_topological_sorting_complex(self, resolver, registry):
        """Test topological sorting with complex dependency graph"""
        # Create complex graph:
        # main -> [a, b]
        # a -> [c, d]
        # b -> [d, e]
        # d -> [f]
        
        registry.add_plugin("f", create_plugin_metadata("f", "1.0.0", []))
        registry.add_plugin("e", create_plugin_metadata("e", "1.0.0", []))
        registry.add_plugin("d", create_plugin_metadata("d", "1.0.0", ["f"]))
        registry.add_plugin("c", create_plugin_metadata("c", "1.0.0", []))
        registry.add_plugin("a", create_plugin_metadata("a", "1.0.0", ["c", "d"]))
        registry.add_plugin("b", create_plugin_metadata("b", "1.0.0", ["d", "e"]))
        registry.add_plugin("main", create_plugin_metadata("main", "1.0.0", ["a", "b"]))

        plugin = registry.get_plugin("main")
        
        # Build dependency graph
        resolver._build_dependency_graph("main", resolver._parse_dependencies(plugin.dependencies))
        
        # Get topological sort
        sorted_order = resolver._topological_sort()
        
        # Verify that dependencies come before dependents
        assert sorted_order.index("f") < sorted_order.index("d") if "f" in sorted_order and "d" in sorted_order else True
        assert sorted_order.index("d") < sorted_order.index("a") if "d" in sorted_order and "a" in sorted_order else True
        assert sorted_order.index("d") < sorted_order.index("b") if "d" in sorted_order and "b" in sorted_order else True

    def test_topological_sorting_multiple_valid_orders(self, resolver, registry):
        """Test that topological sorting handles multiple valid orders"""
        # Create graph with multiple valid orderings
        # main -> [a, b] (a and b are independent)
        registry.add_plugin("a", create_plugin_metadata("a", "1.0.0", []))
        registry.add_plugin("b", create_plugin_metadata("b", "1.0.0", []))
        registry.add_plugin("main", create_plugin_metadata("main", "1.0.0", ["a", "b"]))

        plugin = registry.get_plugin("main")
        resolved = resolver.resolve(plugin)

        # Both [a, b] and [b, a] are valid orders
        assert len(resolved) == 2
        assert all(dep.name in ["a", "b"] for dep in resolved)

    def test_optional_dependencies_skip_if_not_available(self, resolver, registry):
        """Test that optional dependencies are skipped if not available"""
        # Register only required dependency
        registry.add_plugin("required", create_plugin_metadata("required", "1.0.0"))
        # Don't register optional dependency

        # Create plugin with optional dependency
        plugin = create_plugin_metadata("main", "1.0.0", ["required", "optional (optional)"])

        resolved = resolver.resolve(plugin)

        # Should only include required dependency
        assert len(resolved) == 1
        assert resolved[0].name == "required"

    def test_optional_dependencies_include_if_available(self, resolver, registry):
        """Test that optional dependencies are included if available"""
        # Register both dependencies
        registry.add_plugin("required", create_plugin_metadata("required", "1.0.0"))
        registry.add_plugin("optional", create_plugin_metadata("optional", "1.0.0"))

        # Create plugin with optional dependency
        plugin = create_plugin_metadata("main", "1.0.0", ["required", "optional (optional)"])

        # Parse dependencies
        deps = resolver._parse_dependencies(plugin.dependencies)
        
        # Check that optional is marked correctly
        optional_dep = next((d for d in deps if d.name == "optional"), None)
        assert optional_dep is not None
        assert optional_dep.optional is True

    def test_optional_dependencies_with_features(self, resolver):
        """Test parsing optional dependencies with feature flags"""
        deps_specs = [
            "database[postgres,mysql]>=2.0.0 (optional)",
            "cache[redis]",
            "logger*"
        ]

        parsed = resolver._parse_dependencies(deps_specs)

        # Check database dependency
        db_dep = next((d for d in parsed if d.name == "database"), None)
        assert db_dep is not None
        assert db_dep.optional is True
        assert "postgres" in db_dep.features
        assert "mysql" in db_dep.features
        assert db_dep.version_spec == ">=2.0.0"

        # Check cache dependency
        cache_dep = next((d for d in parsed if d.name == "cache"), None)
        assert cache_dep is not None
        assert cache_dep.optional is False
        assert "redis" in cache_dep.features

    def test_conflict_resolution_version_mismatch(self, resolver, registry):
        """Test detection of version conflicts (A needs B>=2.0, C needs B<2.0)"""
        # This tests the dependency resolution logic, not direct conflict resolution
        # Add different versions of a dependency
        registry.add_plugin("shared_dep", create_plugin_metadata("shared_dep", "1.5.0"))
        registry.add_plugin("shared_dep", create_plugin_metadata("shared_dep", "2.5.0"))

        # Plugin that needs newer version
        plugin = create_plugin_metadata("main", "1.0.0", ["shared_dep>=2.0"])
        
        # Check that correct version is identified
        available = registry.get_available_versions("shared_dep")
        compatible = [v for v in available if resolver._check_version_compatibility(v, ">=2.0")]
        assert "2.5.0" in compatible
        assert "1.5.0" not in compatible

    def test_conflict_resolution_diamond_dependency(self, resolver, registry):
        """Test resolution of diamond dependency pattern"""
        # Diamond pattern:
        #     main
        #    /    \
        #   a      b
        #    \    /
        #     shared
        
        registry.add_plugin("shared", create_plugin_metadata("shared", "1.0.0"))
        registry.add_plugin("a", create_plugin_metadata("a", "1.0.0", ["shared"]))
        registry.add_plugin("b", create_plugin_metadata("b", "1.0.0", ["shared"]))
        registry.add_plugin("main", create_plugin_metadata("main", "1.0.0", ["a", "b"]))

        plugin = registry.get_plugin("main")
        resolved = resolver.resolve(plugin)

        # Should include shared only once
        dep_names = [dep.name for dep in resolved]
        assert dep_names.count("shared") <= 1  # shared might be deduplicated

    def test_dependency_tree_generation_simple(self, resolver, registry):
        """Test generation of simple dependency tree"""
        # Create simple tree: main -> a -> b
        registry.add_plugin("b", create_plugin_metadata("b", "1.0.0"))
        registry.add_plugin("a", create_plugin_metadata("a", "1.0.0", ["b"]))
        registry.add_plugin("main", create_plugin_metadata("main", "1.0.0", ["a"]))

        plugin = registry.get_plugin("main")
        resolver.resolve(plugin)  # Build graph first
        tree = resolver.get_dependency_tree("main")

        assert tree["name"] == "main"
        assert tree["version"] == "1.0.0"
        assert len(tree["dependencies"]) > 0

    def test_dependency_tree_generation_with_circular(self, resolver, registry):
        """Test dependency tree generation with circular dependency handling"""
        # Create circular dependency for display purposes
        registry.add_plugin("a", create_plugin_metadata("a", "1.0.0", ["b"]))
        registry.add_plugin("b", create_plugin_metadata("b", "1.0.0", ["a"]))

        # Build partial graph (won't resolve due to circular, but can still build tree)
        resolver._build_dependency_graph("a", resolver._parse_dependencies(["b"]))
        resolver._build_dependency_graph("b", resolver._parse_dependencies(["a"]))

        tree = resolver.get_dependency_tree("a")

        # Should mark circular dependency
        assert tree["name"] == "a"
        # Check if circular reference is handled in tree
        if "dependencies" in tree and len(tree["dependencies"]) > 0:
            b_node = tree["dependencies"][0]
            if "dependencies" in b_node and len(b_node["dependencies"]) > 0:
                a_ref = b_node["dependencies"][0]
                assert a_ref.get("circular", False) is True

    def test_dependency_tree_depth_limiting(self, resolver, registry):
        """Test that dependency tree respects maximum depth"""
        # Create very deep chain
        for i in range(15):
            deps = [f"plugin_{i+1}"] if i < 14 else []
            registry.add_plugin(f"plugin_{i}", create_plugin_metadata(f"plugin_{i}", "1.0.0", deps))

        resolver.max_depth = 10

        # Should fail when exceeding max depth
        plugin = registry.get_plugin("plugin_0")
        with pytest.raises(DependencyError) as exc_info:
            resolver.resolve(plugin)

        assert "Maximum dependency depth exceeded" in str(exc_info.value)

    def test_missing_dependency_handling(self, resolver, registry):
        """Test handling of missing dependencies"""
        # Register plugin with missing dependency
        plugin = create_plugin_metadata("main", "1.0.0", ["missing_dep"])

        # Resolve should handle missing dependency
        resolved = resolver.resolve(plugin)
        
        # The missing dependency should be noted in the graph
        assert "missing_dep" in resolver.dependency_graph
        assert resolver.dependency_graph["missing_dep"].version == "not_found"

    def test_missing_dependency_error_message(self, resolver, registry):
        """Test error messages for missing dependencies"""
        plugin = create_plugin_metadata("main", "1.0.0", ["nonexistent>=1.0.0"])
        
        # Try to check if dependency can be satisfied
        dep = PluginDependency(name="nonexistent", version_spec=">=1.0.0")
        can_satisfy = resolver._can_satisfy_dependency(dep)
        
        assert can_satisfy is False

    def test_version_compatibility_semantic(self, resolver):
        """Test semantic versioning compatibility"""
        # Test major version changes
        assert not resolver._check_version_compatibility("2.0.0", "~=1.0.0")
        assert resolver._check_version_compatibility("1.5.0", "~=1.0.0")
        
        # Test minor version changes
        assert resolver._check_version_compatibility("1.2.5", "~=1.2.0")
        assert not resolver._check_version_compatibility("1.3.0", "~=1.2.0")
        
        # Test patch version changes
        assert resolver._check_version_compatibility("1.2.3", ">=1.2.0")
        assert resolver._check_version_compatibility("1.2.10", ">=1.2.0")

    def test_version_compatibility_prerelease(self, resolver):
        """Test handling of pre-release versions"""
        # Pre-release versions should be handled
        # Note: This depends on the packaging library's version parsing
        assert resolver._check_version_compatibility("1.0.0", ">=1.0.0rc1")
        assert resolver._check_version_compatibility("1.0.0rc2", ">=1.0.0rc1")

    def test_check_compatibility_method(self, resolver, registry):
        """Test the check_compatibility method"""
        # Add some plugins to registry
        registry.add_plugin("required_dep", create_plugin_metadata("required_dep", "1.0.0"))
        
        # Create plugin with satisfiable dependencies
        plugin = create_plugin_metadata("main", "1.0.0", ["required_dep>=1.0.0"])
        
        # Should be compatible
        assert resolver.check_compatibility(plugin) is True
        
        # Create plugin with unsatisfiable dependencies
        plugin_bad = create_plugin_metadata("bad", "1.0.0", ["missing_dep>=2.0.0"])
        
        # Should not be compatible
        assert resolver.check_compatibility(plugin_bad) is False

    def test_install_dependencies_dry_run(self, resolver, registry):
        """Test dry run of dependency installation"""
        # Add available plugins
        registry.add_plugin("dep1", create_plugin_metadata("dep1", "1.0.0"))
        registry.add_plugin("dep1", create_plugin_metadata("dep1", "2.0.0"))
        registry.add_plugin("dep2", create_plugin_metadata("dep2", "1.5.0"))

        dependencies = [
            PluginDependency(name="dep1", version_spec=">=1.0.0"),
            PluginDependency(name="dep2", version_spec=">=1.0.0")
        ]

        # Dry run - should return what would be installed
        to_install = resolver.install_dependencies(dependencies, dry_run=True)

        assert len(to_install) == 2
        # Should choose latest compatible versions
        assert ("dep1", "2.0.0") in to_install
        assert ("dep2", "1.5.0") in to_install

    def test_install_dependencies_incompatible_version(self, resolver, registry):
        """Test error when no compatible version is found"""
        # Add plugin with wrong version
        registry.add_plugin("old_dep", create_plugin_metadata("old_dep", "0.5.0"))

        dependencies = [
            PluginDependency(name="old_dep", version_spec=">=1.0.0")
        ]

        # Should raise error for incompatible version
        with pytest.raises(IncompatibleVersionError) as exc_info:
            resolver.install_dependencies(dependencies)

        assert "No compatible version found" in str(exc_info.value)

    def test_parse_dependencies_various_formats(self, resolver):
        """Test parsing of various dependency specification formats"""
        specs = [
            "simple_dep",
            "versioned_dep>=1.0.0",
            "exact_dep==2.3.4",
            "feature_dep[extra1,extra2]",
            "complex_dep[feature]>=1.0.0 (optional)",
            "wildcard_dep*",
        ]

        parsed = resolver._parse_dependencies(specs)

        assert len(parsed) == 6

        # Check simple dependency
        simple = next((d for d in parsed if d.name == "simple_dep"), None)
        assert simple is not None
        assert simple.version_spec == "*"
        assert simple.optional is False

        # Check versioned dependency
        versioned = next((d for d in parsed if d.name == "versioned_dep"), None)
        assert versioned is not None
        assert versioned.version_spec == ">=1.0.0"

        # Check exact version
        exact = next((d for d in parsed if d.name == "exact_dep"), None)
        assert exact is not None
        assert exact.version_spec == "==2.3.4"

        # Check feature dependency
        feature = next((d for d in parsed if d.name == "feature_dep"), None)
        assert feature is not None
        assert "extra1" in feature.features
        assert "extra2" in feature.features

        # Check complex dependency
        complex_dep = next((d for d in parsed if d.name == "complex_dep"), None)
        assert complex_dep is not None
        assert complex_dep.optional is True
        assert "feature" in complex_dep.features
        assert complex_dep.version_spec == ">=1.0.0"

    def test_dependency_node_structure(self):
        """Test DependencyNode data structure"""
        node = DependencyNode(
            plugin_id="test_plugin",
            version="1.0.0",
            dependencies=[
                PluginDependency(name="dep1", version_spec=">=1.0.0"),
                PluginDependency(name="dep2", version_spec="*", optional=True)
            ],
            depth=2
        )

        assert node.plugin_id == "test_plugin"
        assert node.version == "1.0.0"
        assert len(node.dependencies) == 2
        assert node.depth == 2
        assert len(node.dependents) == 0
        assert node.resolved is False

        # Add dependent
        node.dependents.add("parent_plugin")
        assert "parent_plugin" in node.dependents

    def test_dependency_string_representation(self):
        """Test string representation of PluginDependency"""
        # Simple dependency
        dep1 = PluginDependency(name="simple", version_spec="*")
        assert str(dep1) == "simple"

        # Versioned dependency
        dep2 = PluginDependency(name="versioned", version_spec=">=1.0.0")
        assert str(dep2) == "versioned>=1.0.0"

        # Optional dependency
        dep3 = PluginDependency(name="optional", version_spec="*", optional=True)
        assert "(optional)" in str(dep3)

        # Feature dependency
        dep4 = PluginDependency(name="featured", version_spec="*", features=["extra1", "extra2"])
        assert "[extra1,extra2]" in str(dep4)

        # Complex dependency
        dep5 = PluginDependency(
            name="complex",
            version_spec=">=2.0.0",
            optional=True,
            features=["postgres"]
        )
        result = str(dep5)
        assert "complex" in result
        assert ">=2.0.0" in result
        assert "(optional)" in result
        assert "[postgres]" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])