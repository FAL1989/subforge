#!/usr/bin/env python3
"""
Migration script to update plugin_manager.py to use the new V2 architecture
This preserves backward compatibility while adding new features
"""

import shutil
from pathlib import Path


def migrate_plugin_manager():
    """Migrate plugin_manager.py to use V2 architecture"""
    
    plugin_dir = Path(__file__).parent
    old_file = plugin_dir / "plugin_manager.py"
    backup_file = plugin_dir / "plugin_manager_legacy.py"
    v2_file = plugin_dir / "plugin_manager_v2.py"
    
    # Create backup of original
    if old_file.exists() and not backup_file.exists():
        shutil.copy2(old_file, backup_file)
        print(f"✅ Created backup: {backup_file}")
    
    # Create new plugin_manager.py that imports from V2
    new_content = '''"""
SubForge Plugin Manager
Enhanced plugin management with DI Container, lifecycle, sandboxing, and dependencies

This module provides backward compatibility while using the new V2 architecture.
"""

# Import everything from V2
from subforge.plugins.plugin_manager_v2 import (
    # Core classes
    PluginMetadata,
    SubForgePlugin,
    AgentPlugin,
    WorkflowPlugin,
    PluginManagerV2,
    PluginManager,  # Alias for backward compatibility
)

# Re-export for backward compatibility
__all__ = [
    "PluginMetadata",
    "SubForgePlugin", 
    "AgentPlugin",
    "WorkflowPlugin",
    "PluginManager",
    "PluginManagerV2",
]

# Optional: Add deprecation warning for old usage
def get_plugin_manager(*args, **kwargs):
    """
    Factory function to get plugin manager instance
    Provides migration path from old to new API
    """
    import warnings
    
    # Check if old-style arguments are used
    if args and isinstance(args[0], (str, Path)):
        warnings.warn(
            "Passing plugins_dir directly is deprecated. "
            "Use PluginConfig instead: PluginManager(config=PluginConfig(plugin_dir=path))",
            DeprecationWarning,
            stacklevel=2
        )
        
        from subforge.plugins.config import PluginConfig
        from pathlib import Path
        
        config = PluginConfig(plugin_dir=Path(args[0]))
        return PluginManagerV2(config=config)
    
    return PluginManagerV2(*args, **kwargs)
'''
    
    # Write new plugin_manager.py
    old_file.write_text(new_content)
    print(f"✅ Updated {old_file} to use V2 architecture")
    print("ℹ️  Original file backed up to plugin_manager_legacy.py")
    print("ℹ️  Full V2 implementation in plugin_manager_v2.py")
    

def create_example_usage():
    """Create example usage file"""
    
    example_file = Path(__file__).parent / "example_usage.py"
    
    example_content = '''#!/usr/bin/env python3
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
    
    print("\\n=== Advanced Usage ===")
    advanced_usage()
    
    print("\\n=== Lifecycle Management ===")
    lifecycle_management()
'''
    
    example_file.write_text(example_content)
    print(f"✅ Created example usage: {example_file}")


if __name__ == "__main__":
    print("🔄 Starting Plugin Manager migration to V2...")
    
    migrate_plugin_manager()
    create_example_usage()
    
    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Test your existing code - it should work without changes")
    print("2. Review example_usage.py for new features")
    print("3. Update your code to use new features gradually")
    print("4. Run tests to ensure everything works")