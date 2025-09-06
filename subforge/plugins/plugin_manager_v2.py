"""
SubForge Plugin Manager V2
Enhanced plugin manager with DI Container, lifecycle management, sandboxing, and dependency resolution
"""

import asyncio
import concurrent.futures
import importlib.util
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from subforge.core.di_container import DIContainer, get_container
from subforge.plugins.config import PluginConfig, PluginLoadStrategy
from subforge.plugins.dependencies import (
    MockPluginRegistry,
    PluginDependency,
    PluginDependencyResolver,
)
from subforge.plugins.lifecycle import LocalPluginStore, PluginLifecycle, PluginState
from subforge.plugins.sandbox import PluginSandbox


@dataclass
class PluginMetadata:
    """Plugin metadata"""

    name: str
    version: str
    author: str
    description: str
    type: str  # "agent", "workflow", "analyzer", "generator"
    dependencies: List[str]
    config: Dict[str, Any]


class SubForgePlugin(ABC):
    """Base class for all SubForge plugins"""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin"""

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute plugin functionality"""

    def validate(self) -> bool:
        """Validate plugin configuration"""
        return True

    def cleanup(self):
        """Cleanup plugin resources"""


class AgentPlugin(SubForgePlugin):
    """Plugin for custom agent templates"""

    @abstractmethod
    def generate_agent(self, project_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent configuration"""

    @abstractmethod
    def get_agent_tools(self) -> List[str]:
        """Return required tools for the agent"""


class WorkflowPlugin(SubForgePlugin):
    """Plugin for custom workflows"""

    @abstractmethod
    def get_workflow_phases(self) -> List[str]:
        """Return workflow phases"""

    @abstractmethod
    def execute_phase(self, phase: str, context: Dict[str, Any]) -> Any:
        """Execute a workflow phase"""


class PluginManagerV2:
    """Enhanced plugin manager with DI Container integration"""

    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        container: Optional[DIContainer] = None,
    ):
        """
        Initialize plugin manager with dependency injection

        Args:
            config: Plugin configuration
            container: DI container for dependency injection
        """
        # Configuration
        self.config = config or PluginConfig()

        # DI Container
        self.container = container or get_container()

        # Initialize components through DI
        self.plugin_store = LocalPluginStore(self.config.cache_dir)
        self.plugin_lifecycle = PluginLifecycle(self.plugin_store, self.config)
        self.plugin_sandbox = PluginSandbox(self.config.security)
        self.plugin_registry = MockPluginRegistry()
        self.dependency_resolver = PluginDependencyResolver(
            self.plugin_registry, self.config.max_dependency_depth
        )

        # Plugin registry
        self.plugins: Dict[str, SubForgePlugin] = {}
        self.metadata: Dict[str, PluginMetadata] = {}

        # Plugin types
        self.agent_plugins: Dict[str, AgentPlugin] = {}
        self.workflow_plugins: Dict[str, WorkflowPlugin] = {}

        # Async event loop for lifecycle operations
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Load built-in plugins based on strategy
        if self.config.load_strategy == PluginLoadStrategy.EAGER:
            self._load_builtin_plugins()

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create async event loop"""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _load_builtin_plugins(self):
        """Load built-in plugins"""
        # Built-in agent plugins
        builtin_agents = [
            "aws_specialist",
            "gcp_specialist",
            "azure_specialist",
            "blockchain_developer",
            "game_developer",
            "mobile_developer",
            "data_engineer",
            "ml_engineer",
            "devops_engineer",
            "security_engineer",
        ]

        for agent_name in builtin_agents:
            self._register_builtin_agent(agent_name)

    def _register_builtin_agent(self, name: str):
        """Register a built-in agent plugin"""

        class BuiltinAgent(AgentPlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name=name,
                    version="1.0.0",
                    author="SubForge",
                    description=f"Built-in {name.replace('_', ' ').title()} agent",
                    type="agent",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            def execute(self, context: Dict[str, Any]) -> Any:
                return self.generate_agent(context.get("project_profile", {}))

            def generate_agent(self, project_profile: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "name": name,
                    "model": "sonnet",
                    "description": f"Specialist in {name.replace('_', ' ')}",
                    "tools": self.get_agent_tools(),
                    "context": f"Expert in {name.replace('_', ' ')} development",
                }

            def get_agent_tools(self) -> List[str]:
                return ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]

        plugin = BuiltinAgent()
        self.register_plugin(name, plugin)

    def load_plugin(self, plugin_path: Path) -> bool:
        """
        Load a plugin from file with security and dependency checking

        Args:
            plugin_path: Path to plugin file

        Returns:
            True if successfully loaded
        """
        if not plugin_path.exists():
            print(f"❌ Plugin not found: {plugin_path}")
            return False

        # Check file size limit
        file_size_mb = plugin_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_plugin_size_mb:
            print(
                f"❌ Plugin file too large: {file_size_mb:.2f}MB (max: {self.config.max_plugin_size_mb}MB)"
            )
            return False

        try:
            # Load plugin module in sandboxed environment if enabled
            if self.config.security.enable_sandbox:
                return self._load_plugin_sandboxed(plugin_path)
            else:
                return self._load_plugin_direct(plugin_path)

        except Exception as e:
            print(f"❌ Failed to load plugin: {e}")
            return False

    def _load_plugin_direct(self, plugin_path: Path) -> bool:
        """Load plugin directly without sandbox"""
        spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)

        if not spec or not spec.loader:
            return False

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find plugin class
        plugin_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, SubForgePlugin)
                and attr != SubForgePlugin
                and attr != AgentPlugin
                and attr != WorkflowPlugin
            ):
                plugin_class = attr
                break

        if not plugin_class:
            print(f"❌ No plugin class found in {plugin_path}")
            return False

        # Use DI container to instantiate plugin with dependencies
        plugin = (
            self.container.resolve(plugin_class)
            if self.container.is_registered(plugin_class)
            else plugin_class()
        )
        metadata = plugin.get_metadata()

        return self.register_plugin(metadata.name, plugin)

    def _load_plugin_sandboxed(self, plugin_path: Path) -> bool:
        """Load plugin in sandboxed environment"""
        # TODO: Implement sandboxed loading with multiprocessing
        # For now, fallback to direct loading with warning
        print("⚠️  Sandboxed loading not yet implemented, using direct loading")
        return self._load_plugin_direct(plugin_path)

    def register_plugin(self, name: str, plugin: SubForgePlugin) -> bool:
        """
        Register a plugin with lifecycle management and dependency resolution

        Args:
            name: Plugin name
            plugin: Plugin instance

        Returns:
            True if successfully registered
        """
        try:
            # Get metadata
            metadata = plugin.get_metadata()

            # Check plugin count limit
            if len(self.plugins) >= self.config.max_plugins:
                print(f"❌ Maximum plugin limit reached: {self.config.max_plugins}")
                return False

            # Check dependencies if enabled
            if self.config.check_dependencies and metadata.dependencies:
                # Add to registry for dependency resolution
                self.plugin_registry.add_plugin(name, metadata)

                # Resolve dependencies
                try:
                    resolved_deps = self.dependency_resolver.resolve(metadata)
                    if resolved_deps:
                        print(f"📦 Plugin {name} has dependencies: {[str(d) for d in resolved_deps]}")

                        # Install dependencies if auto-install enabled
                        if self.config.auto_update:
                            to_install = self.dependency_resolver.install_dependencies(
                                resolved_deps, dry_run=True
                            )
                            if to_install:
                                print(f"📥 Would install: {to_install}")
                except Exception as e:
                    print(f"⚠️  Dependency resolution failed: {e}")
                    if not metadata.config.get("ignore_dependencies", False):
                        return False

            # Use lifecycle manager for installation
            # Create a new thread to run the async operation to avoid event loop conflicts
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.plugin_lifecycle.install(plugin, name))
                success = future.result()

            if success:
                # Register plugin locally
                self.plugins[name] = plugin
                self.metadata[name] = metadata

                # Register by type
                if isinstance(plugin, AgentPlugin):
                    self.agent_plugins[name] = plugin
                elif isinstance(plugin, WorkflowPlugin):
                    self.workflow_plugins[name] = plugin

                # Auto-activate if configured
                if self.config.auto_activate:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.plugin_lifecycle.activate(name))
                        future.result()

                # Register in DI container for future dependency injection
                self.container.register_instance(type(plugin), plugin)

                return True

            return False

        except Exception as e:
            print(f"❌ Failed to register plugin {name}: {e}")
            return False

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin using lifecycle manager"""
        if name not in self.plugins:
            return False

        try:
            # Use lifecycle manager for uninstallation
            loop = self._get_event_loop()
            success = loop.run_until_complete(self.plugin_lifecycle.uninstall(name))

            if success:
                # Remove from local registries
                plugin = self.plugins[name]
                del self.plugins[name]
                del self.metadata[name]

                if name in self.agent_plugins:
                    del self.agent_plugins[name]
                if name in self.workflow_plugins:
                    del self.workflow_plugins[name]

                return True

            return False

        except Exception as e:
            print(f"❌ Failed to unregister plugin {name}: {e}")
            return False

    def execute_plugin(self, name: str, context: Dict[str, Any]) -> Any:
        """Execute a plugin with sandbox protection"""
        if name not in self.plugins:
            raise ValueError(f"Plugin not found: {name}")

        plugin = self.plugins[name]

        # Check if plugin is active
        plugin_state = self.plugin_lifecycle.get_plugin_state(name)
        if plugin_state != PluginState.ACTIVE:
            # Auto-activate if configured
            if self.config.auto_activate:
                loop = self._get_event_loop()
                loop.run_until_complete(self.plugin_lifecycle.activate(name))
            else:
                raise ValueError(f"Plugin {name} is not active (state: {plugin_state})")

        # Execute in sandbox if enabled
        if self.config.security.enable_sandbox:
            return self.plugin_sandbox.execute_in_sandbox(plugin, "execute", context)
        else:
            return plugin.execute(context)

    def get_agent_plugins(self) -> List[str]:
        """Get list of agent plugins"""
        return list(self.agent_plugins.keys())

    def get_workflow_plugins(self) -> List[str]:
        """Get list of workflow plugins"""
        return list(self.workflow_plugins.keys())

    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get plugin information"""
        if name not in self.metadata:
            return None

        metadata = self.metadata[name]
        state = self.plugin_lifecycle.get_plugin_state(name)

        return {
            "name": metadata.name,
            "version": metadata.version,
            "author": metadata.author,
            "description": metadata.description,
            "type": metadata.type,
            "dependencies": metadata.dependencies,
            "state": state.value if state else "unknown",
        }

    def list_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all plugins by type"""
        result = {"agents": [], "workflows": [], "other": []}

        for name, metadata in self.metadata.items():
            info = self.get_plugin_info(name)
            if info:
                if metadata.type == "agent":
                    result["agents"].append(info)
                elif metadata.type == "workflow":
                    result["workflows"].append(info)
                else:
                    result["other"].append(info)

        return result

    def load_all_plugins(self) -> int:
        """Load all plugins from plugins directory with parallel loading"""
        count = 0
        plugin_files = [
            f for f in self.config.plugin_dir.glob("*.py") if not f.stem.startswith("_")
        ]

        if self.config.parallel_loading and len(plugin_files) > 1:
            # Load plugins in parallel
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(self.config.max_parallel_loads, len(plugin_files))
            ) as executor:
                results = executor.map(self.load_plugin, plugin_files)
                count = sum(1 for r in results if r)
        else:
            # Load plugins sequentially
            for plugin_file in plugin_files:
                if self.load_plugin(plugin_file):
                    count += 1

        print(f"📦 Loaded {count} plugins from {self.config.plugin_dir}")
        return count

    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins"""
        all_states = self.plugin_lifecycle.get_all_plugins()
        status = {}

        for plugin_id, state_info in all_states.items():
            status[plugin_id] = {
                "state": state_info.state.value,
                "version": state_info.version,
                "last_updated": state_info.last_updated.isoformat(),
                "health_check_passed": state_info.health_check_passed,
                "error_message": state_info.error_message,
            }

        return status

    def activate_plugin(self, name: str) -> bool:
        """Activate a plugin"""
        if name not in self.plugins:
            print(f"❌ Plugin not found: {name}")
            return False

        loop = self._get_event_loop()
        return loop.run_until_complete(self.plugin_lifecycle.activate(name))

    def deactivate_plugin(self, name: str) -> bool:
        """Deactivate a plugin"""
        if name not in self.plugins:
            print(f"❌ Plugin not found: {name}")
            return False

        loop = self._get_event_loop()
        return loop.run_until_complete(self.plugin_lifecycle.deactivate(name))

    def update_plugin(self, name: str, version: str) -> bool:
        """Update a plugin to a new version"""
        if name not in self.plugins:
            print(f"❌ Plugin not found: {name}")
            return False

        loop = self._get_event_loop()
        return loop.run_until_complete(self.plugin_lifecycle.update(name, version))

    def get_dependency_tree(self, name: str) -> Dict[str, Any]:
        """Get dependency tree for a plugin"""
        if name not in self.metadata:
            return {}

        metadata = self.metadata[name]
        self.plugin_registry.add_plugin(name, metadata)

        # Build dependency graph
        resolved_deps = self.dependency_resolver.resolve(metadata)
        return self.dependency_resolver.get_dependency_tree(name)

    def validate_config(self) -> bool:
        """Validate plugin manager configuration"""
        return self.config.validate()

    def export_config(self) -> Dict[str, Any]:
        """Export current configuration"""
        return {
            "config": self.config.to_dict(),
            "plugins": list(self.plugins.keys()),
            "status": self.get_plugin_status(),
        }

    def create_plugin_template(self, name: str, plugin_type: str) -> bool:
        """Create a plugin template file with proper structure"""
        template = f'''"""
{name.replace('_', ' ').title()} Plugin for SubForge
Custom {plugin_type} plugin implementation
Generated with DI Container support
"""

from typing import Dict, Any, List
from subforge.plugins.plugin_manager_v2 import {plugin_type.title()}Plugin, PluginMetadata


class {name.title().replace('_', '')}Plugin({plugin_type.title()}Plugin):
    """Custom {plugin_type} plugin with enhanced features"""
    
    def __init__(self):
        """Initialize plugin"""
        super().__init__()
        self._initialized = False
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="{name}",
            version="1.0.0",
            author="Your Name",
            description="Description of your {plugin_type} plugin",
            type="{plugin_type}",
            dependencies=[],  # Add dependencies like ["plugin_name>=1.0.0"]
            config={{
                "enabled": True,
                "ignore_dependencies": False,
                # Add custom configuration
            }}
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        try:
            # Add initialization logic
            self._initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize: {{e}}")
            return False
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute plugin functionality"""
        if not self._initialized:
            raise RuntimeError("Plugin not initialized")
        
        # Add execution logic
        result = {{}}
        
'''

        if plugin_type == "agent":
            template += '''        # For agent plugins, generate agent configuration
        return self.generate_agent(context.get("project_profile", {}))
    
    def generate_agent(self, project_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent configuration"""
        return {
            "name": self.get_metadata().name,
            "model": "sonnet",
            "description": "Your agent description",
            "tools": self.get_agent_tools(),
            "context": "Your agent context and expertise",
            "capabilities": [
                # Add specific capabilities
            ],
            "limitations": [
                # Add known limitations
            ]
        }
    
    def get_agent_tools(self) -> List[str]:
        """Return required tools for the agent"""
        return ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    
    def validate(self) -> bool:
        """Validate plugin configuration and dependencies"""
        # Add validation logic
        return super().validate() and self._initialized
'''

        elif plugin_type == "workflow":
            template += '''        # For workflow plugins, execute workflow phases
        phase = context.get("phase", "default")
        return self.execute_phase(phase, context)
    
    def get_workflow_phases(self) -> List[str]:
        """Return workflow phases"""
        return [
            "initialization",
            "validation",
            "processing",
            "finalization"
        ]
    
    def execute_phase(self, phase: str, context: Dict[str, Any]) -> Any:
        """Execute a specific workflow phase"""
        phases = {
            "initialization": self._init_phase,
            "validation": self._validate_phase,
            "processing": self._process_phase,
            "finalization": self._finalize_phase,
        }
        
        if phase not in phases:
            raise ValueError(f"Unknown phase: {phase}")
        
        return phases[phase](context)
    
    def _init_phase(self, context: Dict[str, Any]) -> Any:
        """Initialize workflow"""
        return {"status": "initialized"}
    
    def _validate_phase(self, context: Dict[str, Any]) -> Any:
        """Validate workflow inputs"""
        return {"status": "validated"}
    
    def _process_phase(self, context: Dict[str, Any]) -> Any:
        """Process workflow main logic"""
        return {"status": "processed"}
    
    def _finalize_phase(self, context: Dict[str, Any]) -> Any:
        """Finalize workflow"""
        return {"status": "finalized"}
'''

        template += '''
    def cleanup(self):
        """Cleanup plugin resources"""
        # Add cleanup logic
        self._initialized = False
        super().cleanup()


# Optional: Export plugin for registration
__plugin__ = {name.title().replace('_', '')}Plugin
'''

        plugin_file = self.config.plugin_dir / f"{name}.py"
        plugin_file.write_text(template)

        print(f"✅ Plugin template created: {plugin_file}")
        return True


# Backward compatibility alias
PluginManager = PluginManagerV2