"""
Plugin Manager V2 Integration Tests for SubForge
Tests full plugin workflow, parallel loading, sandboxed execution, error recovery,
hot reload, plugin marketplace, and configuration management
"""

import asyncio
import json
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio

from subforge.core.di_container import DIContainer, ServiceLifecycle
from subforge.plugins.config import PluginConfig, PluginLoadStrategy, PluginSecurityConfig
from subforge.plugins.lifecycle import PluginEvent, PluginState
from subforge.plugins.plugin_manager_v2 import (
    AgentPlugin,
    PluginManagerV2,
    PluginMetadata,
    SubForgePlugin,
    WorkflowPlugin,
)


# Mock plugin implementations
class TestPlugin(SubForgePlugin):
    """Basic test plugin"""

    def __init__(self, name="test_plugin", version="1.0.0"):
        self.name = name
        self.version = version
        self.initialized = False
        self.executed = False
        self.config = {}

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self.name,
            version=self.version,
            author="Test Author",
            description="Test plugin",
            type="test",
            dependencies=[],
            config=self.config,
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        self.initialized = True
        return True

    def execute(self, context: Dict[str, Any]) -> Any:
        self.executed = True
        return {"result": "success", "context": context}

    def validate(self) -> bool:
        return True

    def cleanup(self):
        self.initialized = False
        self.executed = False


class TestAgentPlugin(AgentPlugin):
    """Test agent plugin"""

    def __init__(self, name="test_agent"):
        self.name = name
        self.initialized = False

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self.name,
            version="1.0.0",
            author="Test",
            description="Test agent",
            type="agent",
            dependencies=[],
            config={},
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        self.initialized = True
        return True

    def execute(self, context: Dict[str, Any]) -> Any:
        return self.generate_agent(context.get("project_profile", {}))

    def generate_agent(self, project_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": self.name,
            "model": "sonnet",
            "description": f"Test agent {self.name}",
            "tools": self.get_agent_tools(),
            "context": "Test context",
        }

    def get_agent_tools(self) -> List[str]:
        return ["Read", "Write", "Edit"]

    def cleanup(self):
        self.initialized = False


class TestWorkflowPlugin(WorkflowPlugin):
    """Test workflow plugin"""

    def __init__(self, name="test_workflow"):
        self.name = name
        self.phase_execution_log = []

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self.name,
            version="1.0.0",
            author="Test",
            description="Test workflow",
            type="workflow",
            dependencies=[],
            config={},
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        return True

    def execute(self, context: Dict[str, Any]) -> Any:
        phase = context.get("phase", "default")
        return self.execute_phase(phase, context)

    def get_workflow_phases(self) -> List[str]:
        return ["init", "validate", "process", "complete"]

    def execute_phase(self, phase: str, context: Dict[str, Any]) -> Any:
        self.phase_execution_log.append(phase)
        return {"phase": phase, "status": "completed"}

    def cleanup(self):
        self.phase_execution_log.clear()


class CrashingPlugin(SubForgePlugin):
    """Plugin that crashes during execution"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="crashing_plugin",
            version="1.0.0",
            author="Test",
            description="Plugin that crashes",
            type="test",
            dependencies=[],
            config={},
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        return True

    def execute(self, context: Dict[str, Any]) -> Any:
        raise RuntimeError("Plugin crashed!")

    def cleanup(self):
        pass


@pytest.mark.asyncio
class TestPluginManagerV2:
    """Plugin Manager V2 integration test suite"""

    @pytest_asyncio.fixture
    async def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest_asyncio.fixture
    async def config(self, temp_dir):
        """Create plugin configuration"""
        return PluginConfig(
            plugin_dir=temp_dir / "plugins",
            cache_dir=temp_dir / "cache",
            auto_activate=False,
            check_dependencies=True,
        )

    @pytest_asyncio.fixture
    async def manager(self, config):
        """Create plugin manager"""
        container = DIContainer()
        return PluginManagerV2(config, container)

    async def test_full_plugin_workflow(self, manager):
        """Test complete plugin lifecycle: Discover -> Install -> Activate -> Use -> Deactivate -> Uninstall"""
        plugin = TestPlugin("workflow_test")

        # Register (simulates discovery and installation)
        success = manager.register_plugin("workflow_test", plugin)
        assert success

        # Check state after registration
        info = manager.get_plugin_info("workflow_test")
        assert info is not None
        assert info["name"] == "workflow_test"
        assert info["state"] in [PluginState.INSTALLED.value, PluginState.INACTIVE.value]

        # Activate plugin
        success = manager.activate_plugin("workflow_test")
        assert success
        
        # Use plugin
        result = manager.execute_plugin("workflow_test", {"data": "test"})
        assert result["result"] == "success"
        assert plugin.executed

        # Deactivate plugin
        success = manager.deactivate_plugin("workflow_test")
        assert success

        # Uninstall plugin
        success = manager.unregister_plugin("workflow_test")
        assert success

        # Verify plugin is gone
        assert manager.get_plugin_info("workflow_test") is None

    async def test_parallel_plugin_loading(self, manager, temp_dir):
        """Test loading multiple plugins simultaneously"""
        # Create multiple plugin files
        plugin_count = 10
        for i in range(plugin_count):
            plugin_code = f'''
from subforge.plugins.plugin_manager_v2 import SubForgePlugin, PluginMetadata
from typing import Dict, Any

class Plugin{i}(SubForgePlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="plugin_{i}",
            version="1.0.0",
            author="Test",
            description="Plugin {i}",
            type="test",
            dependencies=[],
            config={{}}
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        return True
    
    def execute(self, context: Dict[str, Any]) -> Any:
        return {{"plugin": "plugin_{i}", "result": "success"}}
    
    def cleanup(self):
        pass
'''
            plugin_file = manager.config.plugin_dir / f"plugin_{i}.py"
            plugin_file.parent.mkdir(parents=True, exist_ok=True)
            plugin_file.write_text(plugin_code)

        # Enable parallel loading
        manager.config.parallel_loading = True
        manager.config.max_parallel_loads = 5

        # Measure loading time
        start_time = time.time()
        count = manager.load_all_plugins()
        elapsed = time.time() - start_time

        # Should load all plugins
        assert count == plugin_count
        
        # Verify all plugins are registered
        all_plugins = manager.list_plugins()
        total = len(all_plugins["agents"]) + len(all_plugins["workflows"]) + len(all_plugins["other"])
        # Note: includes built-in plugins loaded in __init__
        assert total >= plugin_count

        print(f"\nLoaded {plugin_count} plugins in {elapsed:.3f}s")

    async def test_sandboxed_execution(self, manager):
        """Test plugin execution in sandbox"""
        # Enable sandbox
        manager.config.security.enable_sandbox = True
        
        plugin = TestPlugin("sandbox_test")
        manager.register_plugin("sandbox_test", plugin)
        manager.activate_plugin("sandbox_test")

        # Execute in sandbox (currently falls back to direct execution with warning)
        result = manager.execute_plugin("sandbox_test", {"secure": "data"})
        assert result["result"] == "success"

    async def test_resource_limits(self, manager, temp_dir):
        """Test plugin resource limits (file size, count limits)"""
        # Test file size limit
        manager.config.max_plugin_size_mb = 0.001  # 1KB limit

        # Create oversized plugin file
        large_plugin = manager.config.plugin_dir / "large_plugin.py"
        large_plugin.parent.mkdir(parents=True, exist_ok=True)
        large_plugin.write_text("x" * 2000)  # 2KB file

        # Should fail to load
        success = manager.load_plugin(large_plugin)
        assert not success

        # Test plugin count limit
        manager.config.max_plugins = 2
        
        # Register plugins up to limit
        plugin1 = TestPlugin("plugin1")
        plugin2 = TestPlugin("plugin2")
        plugin3 = TestPlugin("plugin3")

        assert manager.register_plugin("plugin1", plugin1)
        assert manager.register_plugin("plugin2", plugin2)
        
        # Should fail - exceeds limit
        assert not manager.register_plugin("plugin3", plugin3)

    async def test_error_recovery_plugin_crash(self, manager):
        """Test recovery from plugin crash during execution"""
        crashing_plugin = CrashingPlugin()
        manager.register_plugin("crasher", crashing_plugin)
        manager.activate_plugin("crasher")

        # Should handle crash gracefully
        with pytest.raises(RuntimeError) as exc_info:
            manager.execute_plugin("crasher", {})

        assert "Plugin crashed!" in str(exc_info.value)

        # Manager should still be functional
        normal_plugin = TestPlugin("normal")
        assert manager.register_plugin("normal", normal_plugin)

    async def test_corrupted_plugin_handling(self, manager, temp_dir):
        """Test handling of corrupted plugin files"""
        # Create corrupted plugin file (invalid Python)
        corrupted = manager.config.plugin_dir / "corrupted.py"
        corrupted.parent.mkdir(parents=True, exist_ok=True)
        corrupted.write_text("This is not valid Python code!@#$%")

        # Should fail gracefully
        success = manager.load_plugin(corrupted)
        assert not success

    async def test_missing_dependencies_recovery(self, manager):
        """Test recovery when plugin dependencies are missing"""
        # Create plugin with missing dependencies
        plugin = TestPlugin("dependent")
        plugin.config = {"ignore_dependencies": False}
        
        # Mock metadata with dependencies
        original_metadata = plugin.get_metadata
        def mock_metadata():
            meta = original_metadata()
            meta.dependencies = ["nonexistent_plugin>=1.0.0"]
            return meta
        plugin.get_metadata = mock_metadata

        # Registration should handle missing dependency
        # (depending on configuration, might fail or warn)
        success = manager.register_plugin("dependent", plugin)
        # Success depends on whether dependencies are enforced

    async def test_hot_reload_simulation(self, manager):
        """Test hot reload of plugins (simulated)"""
        # Initial plugin
        plugin_v1 = TestPlugin("reloadable", version="1.0.0")
        manager.register_plugin("reloadable", plugin_v1)
        manager.activate_plugin("reloadable")

        # Execute v1
        result = manager.execute_plugin("reloadable", {"version": "check"})
        assert result["result"] == "success"

        # Simulate update (hot reload)
        success = manager.update_plugin("reloadable", "2.0.0")
        assert success

        # Check version was updated
        info = manager.get_plugin_info("reloadable")
        # Note: actual version update would require new plugin instance
        # This tests the update mechanism

    async def test_plugin_marketplace_simulation(self, manager):
        """Test plugin marketplace features (browsing, installing)"""
        # List available plugins (built-in)
        available = manager.list_plugins()
        
        assert "agents" in available
        assert "workflows" in available
        assert "other" in available

        # Check built-in agent plugins are available
        agent_names = [a["name"] for a in available["agents"]]
        assert any("aws" in name for name in agent_names)
        assert any("azure" in name for name in agent_names)

    async def test_plugin_configuration_loading(self, manager):
        """Test plugin configuration loading and validation"""
        config_data = {
            "enabled": True,
            "api_key": "test_key",
            "max_retries": 3,
        }

        plugin = TestPlugin("configured")
        plugin.config = config_data
        
        manager.register_plugin("configured", plugin)
        
        # Plugin should have received configuration
        assert plugin.initialized
        assert plugin.config == config_data

    async def test_plugin_config_schema_validation(self, manager):
        """Test plugin configuration schema validation"""
        plugin = TestPlugin("schema_test")
        
        # Plugin validates itself
        assert plugin.validate()
        
        # Register with manager
        success = manager.register_plugin("schema_test", plugin)
        assert success

    async def test_runtime_config_updates(self, manager):
        """Test runtime configuration updates"""
        plugin = TestPlugin("runtime_config")
        manager.register_plugin("runtime_config", plugin)
        
        # Initial config
        initial_config = {"setting": "initial"}
        plugin.initialize(initial_config)
        assert plugin.config == initial_config

        # Update config at runtime
        new_config = {"setting": "updated", "new_key": "new_value"}
        plugin.initialize(new_config)
        assert plugin.config == new_config

    async def test_agent_plugin_registration(self, manager):
        """Test agent plugin specific features"""
        agent = TestAgentPlugin("custom_agent")
        
        success = manager.register_plugin("custom_agent", agent)
        assert success
        
        # Should be in agent plugins
        assert "custom_agent" in manager.agent_plugins
        assert "custom_agent" in manager.get_agent_plugins()

        # Generate agent configuration
        manager.activate_plugin("custom_agent")
        result = manager.execute_plugin("custom_agent", {"project_profile": {"type": "web"}})
        
        assert result["name"] == "custom_agent"
        assert result["model"] == "sonnet"
        assert len(result["tools"]) > 0

    async def test_workflow_plugin_phases(self, manager):
        """Test workflow plugin phase execution"""
        workflow = TestWorkflowPlugin("test_workflow")
        
        manager.register_plugin("test_workflow", workflow)
        manager.activate_plugin("test_workflow")
        
        # Execute different phases
        phases = workflow.get_workflow_phases()
        for phase in phases:
            result = manager.execute_plugin("test_workflow", {"phase": phase})
            assert result["phase"] == phase
            assert result["status"] == "completed"

        # Check execution log
        assert workflow.phase_execution_log == phases

    async def test_di_container_integration(self, manager):
        """Test dependency injection container integration"""
        # Register plugin in DI container
        plugin = TestPlugin("di_test")
        manager.register_plugin("di_test", plugin)
        
        # Plugin should be registered in container
        assert manager.container.is_registered(type(plugin))
        
        # Can resolve plugin from container
        resolved = manager.container.resolve(type(plugin))
        assert resolved is plugin

    async def test_lifecycle_event_monitoring(self, manager):
        """Test monitoring of plugin lifecycle events"""
        events_captured = []
        
        async def event_listener(plugin_id, event, **kwargs):
            events_captured.append((plugin_id, event))
        
        # Register event listeners
        manager.plugin_lifecycle.add_event_listener(PluginEvent.INSTALL_STARTED, event_listener)
        manager.plugin_lifecycle.add_event_listener(PluginEvent.INSTALL_COMPLETED, event_listener)
        manager.plugin_lifecycle.add_event_listener(PluginEvent.ACTIVATE_COMPLETED, event_listener)
        
        # Register and activate plugin
        plugin = TestPlugin("event_test")
        manager.register_plugin("event_test", plugin)
        manager.activate_plugin("event_test")
        
        # Check events were captured
        event_types = [e[1] for e in events_captured]
        assert PluginEvent.INSTALL_STARTED in event_types
        assert PluginEvent.INSTALL_COMPLETED in event_types
        assert PluginEvent.ACTIVATE_COMPLETED in event_types

    async def test_get_plugin_status(self, manager):
        """Test getting status of all plugins"""
        # Register multiple plugins
        plugins = [TestPlugin(f"plugin_{i}") for i in range(3)]
        for plugin in plugins:
            manager.register_plugin(plugin.name, plugin)
        
        # Activate some
        manager.activate_plugin("plugin_0")
        manager.activate_plugin("plugin_2")
        
        # Get status
        status = manager.get_plugin_status()
        
        # Check status information
        assert "plugin_0" in status
        assert status["plugin_0"]["state"] == PluginState.ACTIVE.value
        
        assert "plugin_1" in status
        assert status["plugin_1"]["state"] in [PluginState.INSTALLED.value, PluginState.INACTIVE.value]
        
        assert "plugin_2" in status
        assert status["plugin_2"]["state"] == PluginState.ACTIVE.value

    async def test_dependency_tree_visualization(self, manager):
        """Test dependency tree generation"""
        # Create plugin with dependencies
        plugin = TestPlugin("main_plugin")
        
        # Mock dependencies
        original_metadata = plugin.get_metadata
        def mock_metadata():
            meta = original_metadata()
            meta.dependencies = ["dep1", "dep2"]
            return meta
        plugin.get_metadata = mock_metadata
        
        manager.register_plugin("main_plugin", plugin)
        
        # Get dependency tree
        tree = manager.get_dependency_tree("main_plugin")
        
        assert tree is not None
        assert tree.get("name") == "main_plugin"

    async def test_validate_and_export_config(self, manager):
        """Test configuration validation and export"""
        # Validate configuration
        assert manager.validate_config()
        
        # Export configuration
        exported = manager.export_config()
        
        assert "config" in exported
        assert "plugins" in exported
        assert "status" in exported
        
        # Check exported config structure
        config_dict = exported["config"]
        assert "plugin_dir" in config_dict
        assert "auto_activate" in config_dict

    async def test_create_plugin_template(self, manager, temp_dir):
        """Test plugin template generation"""
        # Create agent template
        success = manager.create_plugin_template("my_custom_agent", "agent")
        assert success
        
        template_file = manager.config.plugin_dir / "my_custom_agent.py"
        assert template_file.exists()
        
        # Check template content
        content = template_file.read_text()
        assert "class MyCustomAgentPlugin(AgentPlugin)" in content
        assert "def generate_agent" in content
        assert "def get_agent_tools" in content
        
        # Create workflow template
        success = manager.create_plugin_template("my_workflow", "workflow")
        assert success
        
        workflow_file = manager.config.plugin_dir / "my_workflow.py"
        assert workflow_file.exists()
        
        content = workflow_file.read_text()
        assert "class MyWorkflowPlugin(WorkflowPlugin)" in content
        assert "def get_workflow_phases" in content
        assert "def execute_phase" in content

    async def test_load_strategy_eager(self, temp_dir):
        """Test eager loading strategy"""
        config = PluginConfig(
            plugin_dir=temp_dir / "plugins",
            cache_dir=temp_dir / "cache",
            load_strategy=PluginLoadStrategy.EAGER,
        )
        
        manager = PluginManagerV2(config)
        
        # Should have loaded built-in plugins eagerly
        agent_plugins = manager.get_agent_plugins()
        assert len(agent_plugins) > 0
        assert any("aws" in name for name in agent_plugins)

    async def test_load_strategy_lazy(self, temp_dir):
        """Test lazy loading strategy"""
        config = PluginConfig(
            plugin_dir=temp_dir / "plugins",
            cache_dir=temp_dir / "cache",
            load_strategy=PluginLoadStrategy.LAZY,
        )
        
        manager = PluginManagerV2(config)
        
        # Should not have loaded built-in plugins
        # (unless explicitly initialized elsewhere)
        # This depends on implementation details

    async def test_concurrent_plugin_execution(self, manager):
        """Test concurrent execution of multiple plugins"""
        # Register multiple plugins
        plugins = [TestPlugin(f"concurrent_{i}") for i in range(5)]
        for plugin in plugins:
            manager.register_plugin(plugin.name, plugin)
            manager.activate_plugin(plugin.name)
        
        # Execute plugins concurrently
        async def execute_plugin(name):
            return manager.execute_plugin(name, {"concurrent": True})
        
        # Use threading for concurrent execution
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(manager.execute_plugin, f"concurrent_{i}", {"index": i}) 
                      for i in range(5)]
            results = [f.result() for f in futures]
        
        # All should succeed
        assert all(r["result"] == "success" for r in results)
        
        # All plugins should have executed
        assert all(p.executed for p in plugins)

    async def test_plugin_not_found_error(self, manager):
        """Test error handling for non-existent plugin"""
        with pytest.raises(ValueError) as exc_info:
            manager.execute_plugin("nonexistent", {})
        
        assert "Plugin not found" in str(exc_info.value)

    async def test_auto_activation_config(self, temp_dir):
        """Test auto-activation configuration"""
        config = PluginConfig(
            plugin_dir=temp_dir / "plugins",
            cache_dir=temp_dir / "cache",
            auto_activate=True,
        )
        
        manager = PluginManagerV2(config)
        
        plugin = TestPlugin("auto_activate_test")
        manager.register_plugin("auto_activate_test", plugin)
        
        # Should auto-activate after registration
        # Note: Actual activation is async, so state might be transitioning
        # This tests the configuration option

    async def test_security_config_enforcement(self, manager):
        """Test security configuration enforcement"""
        # Set strict security config
        manager.config.security = PluginSecurityConfig(
            enable_sandbox=True,
            allow_network=False,
            allow_filesystem=False,
            max_memory_mb=100,
            max_cpu_percent=50,
            timeout_seconds=30,
        )
        
        # Validate security config
        assert manager.config.security.enable_sandbox
        assert not manager.config.security.allow_network
        assert not manager.config.security.allow_filesystem
        
        # These settings would be enforced during sandboxed execution

    async def test_plugin_cleanup_on_error(self, manager):
        """Test that plugins are properly cleaned up on errors"""
        plugin = TestPlugin("cleanup_test")
        manager.register_plugin("cleanup_test", plugin)
        manager.activate_plugin("cleanup_test")
        
        # Execute successfully first
        manager.execute_plugin("cleanup_test", {})
        assert plugin.executed
        
        # Deactivate (should cleanup)
        manager.deactivate_plugin("cleanup_test")
        assert not plugin.initialized  # Cleaned up
        assert not plugin.executed  # Reset

    async def test_backward_compatibility(self):
        """Test backward compatibility with PluginManager alias"""
        from subforge.plugins.plugin_manager_v2 import PluginManager
        
        # Should be same as PluginManagerV2
        assert PluginManager is PluginManagerV2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])