#!/usr/bin/env python3
"""
Example usage of the enhanced Plugin Manager with DI Container
"""

from pathlib import Path
from subforge.core.di_container import DIContainer, get_container
from subforge.plugins.config import PluginConfig, PluginPermission
from subforge.plugins.plugin_manager import PluginManager


def basic_usage():
    """Basic plugin manager usage"""
    
    # Create plugin manager with default config
    manager = PluginManager()
    
    # List available plugins
    plugins = manager.list_plugins()
    print(f"Available plugins: {plugins}")
    
    # Get plugin status
    status = manager.get_plugin_status()
    print(f"Plugin status: {status}")
    

def advanced_usage():
    """Advanced usage with custom configuration and DI"""
    
    # Create custom configuration
    config = PluginConfig(
        plugin_dir=Path.home() / ".subforge" / "custom_plugins",
        max_plugins=50,
        auto_activate=True,
        check_dependencies=True,
        security={
            "enable_sandbox": True,
            "allowed_permissions": [
                PluginPermission.FILE_READ,
                PluginPermission.SYSTEM_INFO,
            ],
            "max_memory_mb": 256,
            "max_cpu_percent": 25,
            "timeout_seconds": 20,
        }
    )
    
    # Create DI container and register services
    container = DIContainer()
    
    # You can register your own services
    # container.register(YourService, YourServiceImpl, lifecycle="singleton")
    
    # Create plugin manager with custom config and container
    manager = PluginManager(config=config, container=container)
    
    # Load all plugins from directory
    count = manager.load_all_plugins()
    print(f"Loaded {count} plugins")
    
    # Create a new plugin template
    manager.create_plugin_template("my_custom_agent", "agent")
    
    # Execute a plugin with sandboxing
    context = {"project_profile": {"name": "MyProject"}}
    result = manager.execute_plugin("aws_specialist", context)
    print(f"Plugin result: {result}")
    
    # Check plugin dependencies
    tree = manager.get_dependency_tree("aws_specialist")
    print(f"Dependency tree: {tree}")
    

def lifecycle_management():
    """Plugin lifecycle management example"""
    
    manager = PluginManager()
    
    # Activate a plugin
    manager.activate_plugin("aws_specialist")
    
    # Deactivate a plugin  
    manager.deactivate_plugin("aws_specialist")
    
    # Update a plugin
    manager.update_plugin("aws_specialist", "2.0.0")
    
    # Unregister a plugin
    manager.unregister_plugin("aws_specialist")
    

if __name__ == "__main__":
    print("=== Basic Usage ===")
    basic_usage()
    
    print("\n=== Advanced Usage ===")
    advanced_usage()
    
    print("\n=== Lifecycle Management ===")
    lifecycle_management()
