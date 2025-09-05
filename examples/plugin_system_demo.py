#!/usr/bin/env python3
"""
Comprehensive demo of the enhanced SubForge Plugin System
Shows DI Container, lifecycle management, sandboxing, and dependency resolution
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from subforge.core.di_container import DIContainer, ServiceLifecycle
from subforge.plugins.config import PluginConfig, PluginPermission, PluginLoadStrategy
from subforge.plugins.plugin_manager_v2 import (
    AgentPlugin,
    PluginManager,
    PluginMetadata,
    SubForgePlugin,
    WorkflowPlugin,
)


# Example custom plugin
class DataAnalysisPlugin(AgentPlugin):
    """Custom data analysis agent plugin"""
    
    def __init__(self):
        super().__init__()
        self.analysis_tools = []
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="data_analyst",
            version="2.0.0",
            author="SubForge Demo",
            description="Advanced data analysis specialist agent",
            type="agent",
            dependencies=["statistics_lib>=1.0.0", "ml_toolkit>=2.0.0 (optional)"],
            config={
                "max_dataset_size": 1000000,
                "supported_formats": ["csv", "json", "parquet"],
                "enable_ml": True,
            }
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize with configuration"""
        self.analysis_tools = ["pandas", "numpy", "matplotlib", "seaborn"]
        print(f"✅ Data Analysis Plugin initialized with tools: {self.analysis_tools}")
        return True
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute analysis"""
        return self.generate_agent(context.get("project_profile", {}))
    
    def generate_agent(self, project_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data analyst agent configuration"""
        return {
            "name": "data_analyst",
            "model": "opus",  # Use more powerful model for analysis
            "description": "Expert in data analysis, statistics, and visualization",
            "tools": self.get_agent_tools(),
            "context": """You are a data analysis expert with deep knowledge of:
            - Statistical analysis and hypothesis testing
            - Data visualization and storytelling
            - Machine learning and predictive modeling
            - Big data processing and optimization""",
            "capabilities": [
                "Exploratory data analysis",
                "Statistical modeling",
                "Data visualization",
                "Predictive analytics",
                "Report generation",
            ],
            "analysis_tools": self.analysis_tools,
        }
    
    def get_agent_tools(self) -> List[str]:
        return ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Python", "SQL"]
    
    def validate(self) -> bool:
        """Validate plugin configuration"""
        # Check if required tools are available
        return len(self.analysis_tools) > 0


class DataPipelineWorkflow(WorkflowPlugin):
    """Custom data pipeline workflow plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="data_pipeline",
            version="1.0.0",
            author="SubForge Demo",
            description="Automated data pipeline workflow",
            type="workflow",
            dependencies=["data_analyst"],  # Depends on data analyst plugin
            config={
                "stages": ["ingest", "validate", "transform", "analyze", "export"],
                "parallel_execution": True,
            }
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize workflow"""
        self.stages = config.get("stages", [])
        print(f"✅ Data Pipeline Workflow initialized with stages: {self.stages}")
        return True
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute workflow"""
        results = {}
        for stage in self.stages:
            results[stage] = self.execute_phase(stage, context)
        return results
    
    def get_workflow_phases(self) -> List[str]:
        """Return workflow phases"""
        return self.stages
    
    def execute_phase(self, phase: str, context: Dict[str, Any]) -> Any:
        """Execute a workflow phase"""
        print(f"🔄 Executing phase: {phase}")
        
        phase_handlers = {
            "ingest": lambda: {"status": "data ingested", "records": 1000},
            "validate": lambda: {"status": "data validated", "errors": 0},
            "transform": lambda: {"status": "data transformed", "operations": 5},
            "analyze": lambda: {"status": "analysis complete", "insights": 10},
            "export": lambda: {"status": "data exported", "format": "parquet"},
        }
        
        handler = phase_handlers.get(phase, lambda: {"status": f"{phase} completed"})
        return handler()


def demo_basic_usage():
    """Demonstrate basic plugin manager usage"""
    print("\n" + "=" * 60)
    print("DEMO: Basic Plugin Manager Usage")
    print("=" * 60)
    
    # Create plugin manager with default settings
    manager = PluginManager()
    
    # List built-in plugins
    plugins = manager.list_plugins()
    print(f"\n📦 Built-in plugins:")
    for plugin_type, plugin_list in plugins.items():
        if plugin_list:
            print(f"  {plugin_type}:")
            for plugin in plugin_list:
                print(f"    - {plugin['name']} v{plugin['version']}: {plugin['description']}")
    
    # Get specific plugin info
    aws_info = manager.get_plugin_info("aws_specialist")
    if aws_info:
        print(f"\n🔍 AWS Specialist Plugin:")
        print(f"  Version: {aws_info['version']}")
        print(f"  Author: {aws_info['author']}")
        print(f"  State: {aws_info['state']}")


def demo_custom_configuration():
    """Demonstrate custom configuration with security settings"""
    print("\n" + "=" * 60)
    print("DEMO: Custom Configuration with Security")
    print("=" * 60)
    
    # Create custom configuration
    config = PluginConfig(
        plugin_dir=Path.home() / ".subforge" / "demo_plugins",
        load_strategy=PluginLoadStrategy.LAZY,
        auto_activate=True,
        check_dependencies=True,
        max_plugins=50,
        security=PluginSecurityConfig(
            enable_sandbox=True,
            allowed_permissions=[
                PluginPermission.FILE_READ,
                PluginPermission.SYSTEM_INFO,
                PluginPermission.ENVIRONMENT,
            ],
            denied_permissions=[
                PluginPermission.EXECUTE,
                PluginPermission.NETWORK,
            ],
            max_memory_mb=256,
            max_cpu_percent=30,
            timeout_seconds=15,
        ),
        parallel_loading=True,
        max_parallel_loads=4,
    )
    
    # Validate configuration
    if config.validate():
        print("✅ Configuration is valid")
    
    # Export configuration
    config_dict = config.to_dict()
    print(f"\n📋 Configuration summary:")
    print(f"  Plugin directory: {config_dict['plugin_dir']}")
    print(f"  Load strategy: {config_dict['load_strategy']}")
    print(f"  Security enabled: {config_dict['security']['enable_sandbox']}")
    print(f"  Max memory: {config_dict['security']['max_memory_mb']}MB")
    print(f"  Allowed permissions: {config_dict['security']['allowed_permissions']}")
    
    return config


def demo_di_container():
    """Demonstrate Dependency Injection Container integration"""
    print("\n" + "=" * 60)
    print("DEMO: Dependency Injection Container")
    print("=" * 60)
    
    # Create DI container
    container = DIContainer()
    
    # Register services
    class LoggingService:
        def log(self, message: str):
            print(f"📝 LOG: {message}")
    
    class MetricsService:
        def __init__(self):
            self.metrics = {}
        
        def record(self, name: str, value: Any):
            self.metrics[name] = value
            print(f"📊 METRIC: {name} = {value}")
    
    class PluginMonitor:
        def __init__(self, logger: LoggingService, metrics: MetricsService):
            self.logger = logger
            self.metrics = metrics
        
        def monitor_plugin(self, plugin_name: str):
            self.logger.log(f"Monitoring plugin: {plugin_name}")
            self.metrics.record(f"{plugin_name}_monitored", True)
    
    # Register services with different lifecycles
    container.register(LoggingService, lifecycle=ServiceLifecycle.SINGLETON)
    container.register(MetricsService, lifecycle=ServiceLifecycle.SINGLETON)
    container.register(PluginMonitor)
    
    # Resolve service with automatic dependency injection
    monitor = container.resolve(PluginMonitor)
    monitor.monitor_plugin("data_analyst")
    
    print("\n✅ DI Container configured with services")
    
    # Show registered services
    services = container.get_all_services()
    print(f"\n📦 Registered services: {list(services.keys())}")
    
    return container


def demo_custom_plugins(container: DIContainer, config: PluginConfig):
    """Demonstrate custom plugin registration and execution"""
    print("\n" + "=" * 60)
    print("DEMO: Custom Plugin Registration")
    print("=" * 60)
    
    # Create plugin manager with custom config and DI container
    manager = PluginManager(config=config, container=container)
    
    # Register custom plugins
    data_plugin = DataAnalysisPlugin()
    pipeline_plugin = DataPipelineWorkflow()
    
    print("\n🔧 Registering custom plugins...")
    
    # Register data analysis plugin
    if manager.register_plugin("data_analyst", data_plugin):
        print("✅ Data Analysis Plugin registered")
    
    # Register pipeline workflow plugin
    if manager.register_plugin("data_pipeline", pipeline_plugin):
        print("✅ Data Pipeline Workflow registered")
    
    # Check plugin status
    status = manager.get_plugin_status()
    print(f"\n📊 Plugin Status:")
    for plugin_id, info in status.items():
        if plugin_id in ["data_analyst", "data_pipeline"]:
            print(f"  {plugin_id}:")
            print(f"    State: {info['state']}")
            print(f"    Version: {info['version']}")
    
    return manager


def demo_plugin_execution(manager: PluginManager):
    """Demonstrate plugin execution with sandboxing"""
    print("\n" + "=" * 60)
    print("DEMO: Plugin Execution")
    print("=" * 60)
    
    # Activate plugins
    print("\n🚀 Activating plugins...")
    manager.activate_plugin("data_analyst")
    manager.activate_plugin("data_pipeline")
    
    # Execute data analyst plugin
    print("\n🔄 Executing Data Analyst Plugin...")
    context = {
        "project_profile": {
            "name": "Analytics Project",
            "type": "data_science",
            "datasets": ["sales.csv", "customers.json"],
        }
    }
    
    result = manager.execute_plugin("data_analyst", context)
    print(f"\n📊 Data Analyst Agent Configuration:")
    print(f"  Model: {result['model']}")
    print(f"  Capabilities: {result['capabilities']}")
    print(f"  Tools: {result['analysis_tools']}")
    
    # Execute workflow plugin
    print("\n🔄 Executing Data Pipeline Workflow...")
    workflow_result = manager.execute_plugin("data_pipeline", context)
    print(f"\n📋 Workflow Results:")
    for stage, result in workflow_result.items():
        print(f"  {stage}: {result}")


def demo_dependency_resolution(manager: PluginManager):
    """Demonstrate dependency resolution"""
    print("\n" + "=" * 60)
    print("DEMO: Dependency Resolution")
    print("=" * 60)
    
    # Get dependency tree for data pipeline
    tree = manager.get_dependency_tree("data_pipeline")
    
    print(f"\n🌳 Dependency Tree for 'data_pipeline':")
    
    def print_tree(node, indent=0):
        prefix = "  " * indent + "├─ " if indent > 0 else ""
        print(f"{prefix}{node['name']} v{node['version']}")
        for dep in node.get("dependencies", []):
            print_tree(dep, indent + 1)
    
    print_tree(tree)


def demo_plugin_lifecycle(manager: PluginManager):
    """Demonstrate plugin lifecycle management"""
    print("\n" + "=" * 60)
    print("DEMO: Plugin Lifecycle Management")
    print("=" * 60)
    
    plugin_name = "data_analyst"
    
    # Check current state
    status = manager.get_plugin_status()
    current_state = status.get(plugin_name, {}).get("state", "unknown")
    print(f"\n📊 Current state of '{plugin_name}': {current_state}")
    
    # Deactivate plugin
    print(f"\n🔄 Deactivating '{plugin_name}'...")
    if manager.deactivate_plugin(plugin_name):
        print("✅ Plugin deactivated")
    
    # Check state after deactivation
    status = manager.get_plugin_status()
    current_state = status.get(plugin_name, {}).get("state", "unknown")
    print(f"📊 State after deactivation: {current_state}")
    
    # Reactivate plugin
    print(f"\n🔄 Reactivating '{plugin_name}'...")
    if manager.activate_plugin(plugin_name):
        print("✅ Plugin reactivated")
    
    # Final state check
    status = manager.get_plugin_status()
    current_state = status.get(plugin_name, {}).get("state", "unknown")
    print(f"📊 Final state: {current_state}")


def demo_template_generation(manager: PluginManager):
    """Demonstrate plugin template generation"""
    print("\n" + "=" * 60)
    print("DEMO: Plugin Template Generation")
    print("=" * 60)
    
    # Create agent plugin template
    print("\n📝 Creating agent plugin template...")
    manager.create_plugin_template("recommendation_engine", "agent")
    
    # Create workflow plugin template
    print("📝 Creating workflow plugin template...")
    manager.create_plugin_template("etl_workflow", "workflow")
    
    print("\n✅ Plugin templates created in plugin directory")


async def main():
    """Main demo function"""
    print("\n" + "🚀" * 30)
    print("  SUBFORGE PLUGIN SYSTEM V2 - COMPREHENSIVE DEMO")
    print("🚀" * 30)
    
    try:
        # Run demos
        demo_basic_usage()
        
        config = demo_custom_configuration()
        container = demo_di_container()
        
        manager = demo_custom_plugins(container, config)
        demo_plugin_execution(manager)
        demo_dependency_resolution(manager)
        demo_plugin_lifecycle(manager)
        demo_template_generation(manager)
        
        print("\n" + "✅" * 30)
        print("  ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("✅" * 30)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Handle missing import gracefully
    try:
        from subforge.plugins.config import PluginSecurityConfig
    except ImportError:
        print("⚠️  PluginSecurityConfig import failed, using dict instead")
        PluginSecurityConfig = dict
    
    # Run the demo
    asyncio.run(main())