"""
SubForge Plugin Manager
Manages loading, validation, and execution of SubForge plugins
"""

import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


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


class PluginManager:
    """Manages SubForge plugins"""

    def __init__(self, plugins_dir: Optional[Path] = None):
        """Initialize plugin manager"""
        if plugins_dir:
            self.plugins_dir = Path(plugins_dir)
        else:
            self.plugins_dir = Path.home() / ".subforge" / "plugins"

        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        # Plugin registry
        self.plugins: Dict[str, SubForgePlugin] = {}
        self.metadata: Dict[str, PluginMetadata] = {}

        # Plugin types
        self.agent_plugins: Dict[str, AgentPlugin] = {}
        self.workflow_plugins: Dict[str, WorkflowPlugin] = {}

        # Load built-in plugins
        self._load_builtin_plugins()

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
        ]

        for agent_name in builtin_agents:
            # Create mock plugin for demonstration
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
        Load a plugin from file

        Args:
            plugin_path: Path to plugin file

        Returns:
            True if successfully loaded
        """
        if not plugin_path.exists():
            print(f"❌ Plugin not found: {plugin_path}")
            return False

        try:
            # Load plugin module
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
                ):
                    plugin_class = attr
                    break

            if not plugin_class:
                print(f"❌ No plugin class found in {plugin_path}")
                return False

            # Instantiate and register plugin
            plugin = plugin_class()
            metadata = plugin.get_metadata()

            return self.register_plugin(metadata.name, plugin)

        except Exception as e:
            print(f"❌ Failed to load plugin: {e}")
            return False

    def register_plugin(self, name: str, plugin: SubForgePlugin) -> bool:
        """
        Register a plugin

        Args:
            name: Plugin name
            plugin: Plugin instance

        Returns:
            True if successfully registered
        """
        try:
            # Validate plugin
            if not plugin.validate():
                print(f"❌ Plugin validation failed: {name}")
                return False

            # Get metadata
            metadata = plugin.get_metadata()

            # Initialize plugin
            if not plugin.initialize(metadata.config):
                print(f"❌ Plugin initialization failed: {name}")
                return False

            # Register plugin
            self.plugins[name] = plugin
            self.metadata[name] = metadata

            # Register by type
            if isinstance(plugin, AgentPlugin):
                self.agent_plugins[name] = plugin
            elif isinstance(plugin, WorkflowPlugin):
                self.workflow_plugins[name] = plugin

            print(f"✅ Plugin registered: {name}")
            return True

        except Exception as e:
            print(f"❌ Failed to register plugin {name}: {e}")
            return False

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin"""
        if name not in self.plugins:
            return False

        # Cleanup plugin
        plugin = self.plugins[name]
        plugin.cleanup()

        # Remove from registries
        del self.plugins[name]
        del self.metadata[name]

        if name in self.agent_plugins:
            del self.agent_plugins[name]
        if name in self.workflow_plugins:
            del self.workflow_plugins[name]

        print(f"✅ Plugin unregistered: {name}")
        return True

    def execute_plugin(self, name: str, context: Dict[str, Any]) -> Any:
        """Execute a plugin"""
        if name not in self.plugins:
            raise ValueError(f"Plugin not found: {name}")

        plugin = self.plugins[name]
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
        return {
            "name": metadata.name,
            "version": metadata.version,
            "author": metadata.author,
            "description": metadata.description,
            "type": metadata.type,
            "dependencies": metadata.dependencies,
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
        """Load all plugins from plugins directory"""
        count = 0

        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.stem.startswith("_"):
                continue

            if self.load_plugin(plugin_file):
                count += 1

        return count

    def create_plugin_template(self, name: str, plugin_type: str) -> bool:
        """Create a plugin template file"""
        template = f'''"""
{name.replace('_', ' ').title()} Plugin for SubForge
Custom {plugin_type} plugin implementation
"""

from subforge.plugins.plugin_manager import {plugin_type.title()}Plugin, PluginMetadata


class {name.title().replace('_', '')}Plugin({plugin_type.title()}Plugin):
    """Custom {plugin_type} plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="{name}",
            version="1.0.0",
            author="Your Name",
            description="Description of your plugin",
            type="{plugin_type}",
            dependencies=[],
            config={{}}
        )
    
    def initialize(self, config):
        """Initialize plugin"""
        # Add initialization logic
        return True
    
    def execute(self, context):
        """Execute plugin"""
        # Add execution logic
        pass
    
    def validate(self):
        """Validate plugin configuration"""
        # Add validation logic
        return True
'''

        if plugin_type == "agent":
            template += '''
    def generate_agent(self, project_profile):
        """Generate agent configuration"""
        return {
            "name": self.get_metadata().name,
            "model": "sonnet",
            "description": "Your agent description",
            "tools": self.get_agent_tools(),
            "context": "Your agent context"
        }
    
    def get_agent_tools(self):
        """Return required tools"""
        return ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
'''

        plugin_file = self.plugins_dir / f"{name}.py"
        plugin_file.write_text(template)

        print(f"✅ Plugin template created: {plugin_file}")
        return True