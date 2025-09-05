"""
SubForge Plugin Dependency Resolver
Manages plugin dependencies and compatibility checking
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from packaging import version

from subforge.core.context.exceptions import SubForgeError
from subforge.plugins.plugin_manager import PluginMetadata


class DependencyError(SubForgeError):
    """Raised for dependency-related errors"""


class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected"""


class IncompatibleVersionError(DependencyError):
    """Raised when version requirements cannot be satisfied"""


@dataclass
class PluginDependency:
    """Represents a plugin dependency"""

    name: str
    version_spec: str = "*"  # Version specification (e.g., ">=1.0.0", "~1.2.0", "*")
    optional: bool = False
    features: List[str] = field(default_factory=list)  # Optional features required

    def __str__(self) -> str:
        """String representation"""
        spec = f"{self.name}{self.version_spec}" if self.version_spec != "*" else self.name
        if self.optional:
            spec = f"{spec} (optional)"
        if self.features:
            spec = f"{spec}[{','.join(self.features)}]"
        return spec


@dataclass
class DependencyNode:
    """Node in dependency graph"""

    plugin_id: str
    version: str
    dependencies: List[PluginDependency]
    dependents: Set[str] = field(default_factory=set)
    depth: int = 0
    resolved: bool = False


class IPluginRegistry:
    """Interface for plugin registry"""

    def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get plugin metadata"""
        raise NotImplementedError

    def get_available_versions(self, plugin_id: str) -> List[str]:
        """Get available versions for a plugin"""
        raise NotImplementedError

    def is_installed(self, plugin_id: str, version: Optional[str] = None) -> bool:
        """Check if plugin is installed"""
        raise NotImplementedError


class MockPluginRegistry(IPluginRegistry):
    """Mock plugin registry for testing"""

    def __init__(self):
        """Initialize mock registry"""
        self.plugins: Dict[str, Dict[str, PluginMetadata]] = {}

    def add_plugin(self, plugin_id: str, metadata: PluginMetadata):
        """Add plugin to registry"""
        if plugin_id not in self.plugins:
            self.plugins[plugin_id] = {}
        self.plugins[plugin_id][metadata.version] = metadata

    def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get latest version of plugin"""
        if plugin_id not in self.plugins:
            return None

        versions = self.plugins[plugin_id]
        if not versions:
            return None

        # Get latest version
        latest_version = max(versions.keys(), key=lambda v: version.parse(v))
        return versions[latest_version]

    def get_available_versions(self, plugin_id: str) -> List[str]:
        """Get available versions for a plugin"""
        if plugin_id not in self.plugins:
            return []
        return list(self.plugins[plugin_id].keys())

    def is_installed(self, plugin_id: str, version_str: Optional[str] = None) -> bool:
        """Check if plugin is installed"""
        if plugin_id not in self.plugins:
            return False

        if version_str:
            return version_str in self.plugins[plugin_id]

        return len(self.plugins[plugin_id]) > 0


class PluginDependencyResolver:
    """
    Resolves plugin dependencies and checks compatibility
    """

    def __init__(self, registry: IPluginRegistry, max_depth: int = 10):
        """
        Initialize dependency resolver

        Args:
            registry: Plugin registry
            max_depth: Maximum dependency depth
        """
        self.registry = registry
        self.max_depth = max_depth
        self.dependency_graph: Dict[str, DependencyNode] = {}

    def resolve(self, plugin_metadata: PluginMetadata) -> List[PluginDependency]:
        """
        Resolve all dependencies for a plugin

        Args:
            plugin_metadata: Plugin metadata

        Returns:
            List of resolved dependencies in installation order

        Raises:
            DependencyError: If dependencies cannot be resolved
        """
        # Parse dependencies from metadata
        dependencies = self._parse_dependencies(plugin_metadata.dependencies)

        # Build dependency graph
        self._build_dependency_graph(plugin_metadata.name, dependencies)

        # Check for circular dependencies
        if self._has_circular_dependencies():
            raise CircularDependencyError(
                f"Circular dependencies detected for {plugin_metadata.name}"
            )

        # Topological sort for installation order
        resolved_order = self._topological_sort()

        # Convert to dependency list
        result = []
        for plugin_id in resolved_order:
            if plugin_id != plugin_metadata.name:  # Don't include self
                node = self.dependency_graph[plugin_id]
                for dep in dependencies:
                    if dep.name == plugin_id:
                        result.append(dep)
                        break

        return result

    def _parse_dependencies(self, dependency_specs: List[str]) -> List[PluginDependency]:
        """
        Parse dependency specifications

        Args:
            dependency_specs: List of dependency specifications

        Returns:
            List of parsed dependencies
        """
        dependencies = []

        for spec in dependency_specs:
            # Parse dependency specification
            # Format: name[features]version_spec (optional)
            match = re.match(
                r"^([a-zA-Z0-9_-]+)(?:\[([^\]]+)\])?([>=<~!]+[0-9.]+|\*)?(?:\s+\((optional)\))?$",
                spec,
            )

            if not match:
                # Simple format: just name
                dependencies.append(PluginDependency(name=spec))
            else:
                name = match.group(1)
                features = match.group(2).split(",") if match.group(2) else []
                version_spec = match.group(3) or "*"
                optional = match.group(4) == "optional"

                dependencies.append(
                    PluginDependency(
                        name=name,
                        version_spec=version_spec,
                        optional=optional,
                        features=features,
                    )
                )

        return dependencies

    def _build_dependency_graph(
        self, plugin_id: str, dependencies: List[PluginDependency], depth: int = 0
    ):
        """
        Build dependency graph recursively

        Args:
            plugin_id: Plugin ID
            dependencies: Plugin dependencies
            depth: Current depth in dependency tree
        """
        if depth > self.max_depth:
            raise DependencyError(f"Maximum dependency depth exceeded for {plugin_id}")

        # Get plugin metadata
        plugin_meta = self.registry.get_plugin(plugin_id)
        if plugin_meta:
            plugin_version = plugin_meta.version
        else:
            plugin_version = "unknown"

        # Create or update node
        if plugin_id not in self.dependency_graph:
            self.dependency_graph[plugin_id] = DependencyNode(
                plugin_id=plugin_id,
                version=plugin_version,
                dependencies=dependencies,
                depth=depth,
            )
        else:
            # Update depth if deeper
            if depth > self.dependency_graph[plugin_id].depth:
                self.dependency_graph[plugin_id].depth = depth

        # Process each dependency
        for dep in dependencies:
            if dep.optional:
                # Skip optional dependencies if not installed
                if not self.registry.is_installed(dep.name):
                    continue

            # Add to dependents
            if dep.name in self.dependency_graph:
                self.dependency_graph[dep.name].dependents.add(plugin_id)
            else:
                # Recursively build graph for dependency
                dep_meta = self.registry.get_plugin(dep.name)
                if dep_meta:
                    sub_deps = self._parse_dependencies(dep_meta.dependencies)
                    self._build_dependency_graph(dep.name, sub_deps, depth + 1)
                else:
                    # Create node for missing dependency
                    self.dependency_graph[dep.name] = DependencyNode(
                        plugin_id=dep.name,
                        version="not_found",
                        dependencies=[],
                        depth=depth + 1,
                    )

            # Add dependent relationship
            self.dependency_graph[dep.name].dependents.add(plugin_id)

    def _has_circular_dependencies(self) -> bool:
        """
        Check for circular dependencies using DFS

        Returns:
            True if circular dependencies exist
        """
        visited = set()
        rec_stack = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = self.dependency_graph.get(node_id)
            if node:
                for dep in node.dependencies:
                    if dep.name not in visited:
                        if has_cycle(dep.name):
                            return True
                    elif dep.name in rec_stack:
                        return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.dependency_graph:
            if node_id not in visited:
                if has_cycle(node_id):
                    return True

        return False

    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort on dependency graph

        Returns:
            List of plugin IDs in installation order
        """
        # Calculate in-degree for each node
        in_degree = {node_id: 0 for node_id in self.dependency_graph}

        for node_id, node in self.dependency_graph.items():
            for dep in node.dependencies:
                if dep.name in in_degree:
                    in_degree[dep.name] += 1

        # Queue for nodes with no dependencies
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort queue to ensure deterministic order
            queue.sort()
            node_id = queue.pop(0)
            result.append(node_id)

            # Update in-degrees
            node = self.dependency_graph[node_id]
            for dep in node.dependencies:
                if dep.name in in_degree:
                    in_degree[dep.name] -= 1
                    if in_degree[dep.name] == 0:
                        queue.append(dep.name)

        # Check if all nodes are processed
        if len(result) != len(self.dependency_graph):
            unprocessed = set(self.dependency_graph.keys()) - set(result)
            raise DependencyError(f"Could not resolve dependencies for: {unprocessed}")

        # Reverse to get installation order (dependencies first)
        return list(reversed(result))

    def check_compatibility(self, plugin_metadata: PluginMetadata) -> bool:
        """
        Check if plugin is compatible with current system

        Args:
            plugin_metadata: Plugin metadata

        Returns:
            True if compatible
        """
        try:
            # Check SubForge version compatibility
            if hasattr(plugin_metadata, "subforge_version"):
                if not self._check_version_compatibility(
                    "1.0.0", plugin_metadata.subforge_version  # Current SubForge version
                ):
                    return False

            # Check dependencies
            dependencies = self._parse_dependencies(plugin_metadata.dependencies)
            for dep in dependencies:
                if not dep.optional:
                    # Check if dependency can be satisfied
                    if not self._can_satisfy_dependency(dep):
                        return False

            return True

        except Exception:
            return False

    def _can_satisfy_dependency(self, dependency: PluginDependency) -> bool:
        """
        Check if a dependency can be satisfied

        Args:
            dependency: Dependency to check

        Returns:
            True if dependency can be satisfied
        """
        # Check if plugin exists
        available_versions = self.registry.get_available_versions(dependency.name)
        if not available_versions:
            return False

        # Check version compatibility
        if dependency.version_spec == "*":
            return True

        # Find compatible version
        for available_version in available_versions:
            if self._check_version_compatibility(available_version, dependency.version_spec):
                return True

        return False

    def _check_version_compatibility(self, installed: str, required: str) -> bool:
        """
        Check if installed version satisfies requirement

        Args:
            installed: Installed version
            required: Required version specification

        Returns:
            True if compatible
        """
        if required == "*":
            return True

        try:
            installed_ver = version.parse(installed)

            # Parse requirement operators
            if required.startswith(">="):
                required_ver = version.parse(required[2:])
                return installed_ver >= required_ver
            elif required.startswith(">"):
                required_ver = version.parse(required[1:])
                return installed_ver > required_ver
            elif required.startswith("<="):
                required_ver = version.parse(required[2:])
                return installed_ver <= required_ver
            elif required.startswith("<"):
                required_ver = version.parse(required[1:])
                return installed_ver < required_ver
            elif required.startswith("=="):
                required_ver = version.parse(required[2:])
                return installed_ver == required_ver
            elif required.startswith("~="):
                # Compatible version (same major.minor)
                required_ver = version.parse(required[2:])
                return (
                    installed_ver.major == required_ver.major
                    and installed_ver.minor == required_ver.minor
                    and installed_ver >= required_ver
                )
            elif required.startswith("!="):
                required_ver = version.parse(required[2:])
                return installed_ver != required_ver
            else:
                # Exact version match
                required_ver = version.parse(required)
                return installed_ver == required_ver

        except Exception:
            return False

    def install_dependencies(
        self, dependencies: List[PluginDependency], dry_run: bool = False
    ) -> List[Tuple[str, str]]:
        """
        Install required dependencies

        Args:
            dependencies: List of dependencies to install
            dry_run: If True, only return what would be installed

        Returns:
            List of (plugin_id, version) tuples that were/would be installed
        """
        to_install = []

        for dep in dependencies:
            if dep.optional and not self.registry.is_installed(dep.name):
                continue

            # Find best version to install
            available_versions = self.registry.get_available_versions(dep.name)
            compatible_versions = [
                v
                for v in available_versions
                if self._check_version_compatibility(v, dep.version_spec)
            ]

            if not compatible_versions:
                raise IncompatibleVersionError(
                    f"No compatible version found for {dep.name} (required: {dep.version_spec})"
                )

            # Choose latest compatible version
            best_version = max(compatible_versions, key=lambda v: version.parse(v))

            if not self.registry.is_installed(dep.name, best_version):
                to_install.append((dep.name, best_version))

        if not dry_run:
            # TODO: Actual installation logic would go here
            for plugin_id, plugin_version in to_install:
                print(f"Installing {plugin_id} version {plugin_version}")

        return to_install

    def get_dependency_tree(self, plugin_id: str) -> Dict[str, Any]:
        """
        Get dependency tree for a plugin

        Args:
            plugin_id: Plugin ID

        Returns:
            Dependency tree as nested dictionary
        """

        def build_tree(node_id: str, visited: Set[str]) -> Dict[str, Any]:
            if node_id in visited:
                return {"name": node_id, "circular": True}

            visited.add(node_id)
            node = self.dependency_graph.get(node_id)

            if not node:
                return {"name": node_id, "version": "not_found", "dependencies": []}

            tree = {
                "name": node_id,
                "version": node.version,
                "dependencies": [],
            }

            for dep in node.dependencies:
                tree["dependencies"].append(build_tree(dep.name, visited.copy()))

            return tree

        return build_tree(plugin_id, set())