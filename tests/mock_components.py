"""
Mock Components for Performance Testing
Created: 2025-09-05 17:35 UTC-3 São Paulo

Mock implementations of SubForge components for performance testing.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from unittest.mock import Mock


class PRPGenerator:
    """Mock PRP Generator for performance testing."""
    
    def __init__(self):
        self.templates = {}
        self.cache = {}
    
    def generate(self, agent_config, context: Dict) -> str:
        """Generate a mock PRP."""
        # Simulate processing
        time.sleep(0.001)
        
        prp = f"""
        Agent: {agent_config.name}
        Domain: {agent_config.domain}
        Expertise: {', '.join(agent_config.expertise)}
        Tools: {', '.join(agent_config.tools)}
        Context: {json.dumps(context)}
        Knowledge: {len(agent_config.knowledge_base)} items
        """
        return prp * 10  # Make it larger for realistic testing
    
    def render_template(self, template_name: str, data: Dict) -> str:
        """Render a template with data."""
        # Simulate template rendering
        result = f"Template: {template_name}\n"
        for key, value in data.items():
            result += f"{key}: {value}\n"
        return result


class ContextEngineer:
    """Mock Context Engineer for performance testing."""
    
    def __init__(self):
        self.cache = {}
        self.contexts = []
    
    def create_context(self, project, task: str, additional_context: Dict = None) -> Dict:
        """Create a context package."""
        context = {
            "project": project.name,
            "task": task,
            "timestamp": time.time(),
            "tech_stack": project.tech_stack,
            "complexity": project.complexity,
            "additional": additional_context or {}
        }
        self.contexts.append(context)
        return context
    
    def get_or_create(self, cache_key: str, factory):
        """Get from cache or create new."""
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = factory()
        self.cache[cache_key] = result
        return result
    
    def merge_contexts(self, contexts: List[Dict]) -> Dict:
        """Merge multiple contexts."""
        merged = {}
        for ctx in contexts:
            merged.update(ctx)
        return merged


class ExampleRepository:
    """Mock Example Repository for performance testing."""
    
    def __init__(self):
        self.examples = defaultdict(lambda: defaultdict(list))
    
    def add_example(self, category: str, subcategory: str, example: Dict):
        """Add an example to the repository."""
        self.examples[category][subcategory].append(example)
    
    def search(self, category: str = None, limit: int = 10) -> List[Dict]:
        """Search for examples."""
        results = []
        
        if category and category in self.examples:
            for subcategory, examples in self.examples[category].items():
                results.extend(examples[:limit])
                if len(results) >= limit:
                    break
        else:
            for cat, subcats in self.examples.items():
                for subcat, examples in subcats.items():
                    results.extend(examples[:limit])
                    if len(results) >= limit:
                        return results[:limit]
        
        return results[:limit]


class PluginManager:
    """Mock Plugin Manager for performance testing."""
    
    def __init__(self):
        self.plugins = {}
    
    def load_plugin(self, plugin_id: str, config: Dict):
        """Load a plugin."""
        # Simulate plugin loading
        time.sleep(0.01)
        self.plugins[plugin_id] = config
        return config
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict]:
        """Get a loaded plugin."""
        return self.plugins.get(plugin_id)


class WorkflowMonitor:
    """Mock Workflow Monitor for performance testing."""
    
    def __init__(self):
        self.workflows = {}
        self.metrics = defaultdict(list)
    
    def register_workflow(self, workflow_id: str, config: Dict):
        """Register a workflow."""
        self.workflows[workflow_id] = {
            "id": workflow_id,
            "config": config,
            "status": "registered",
            "start_time": None,
            "end_time": None
        }
    
    def start_workflow(self, workflow_id: str):
        """Start a workflow."""
        if workflow_id not in self.workflows:
            self.workflows[workflow_id] = {"id": workflow_id}
        
        self.workflows[workflow_id]["status"] = "running"
        self.workflows[workflow_id]["start_time"] = time.time()
    
    def complete_workflow(self, workflow_id: str):
        """Complete a workflow."""
        if workflow_id in self.workflows:
            self.workflows[workflow_id]["status"] = "completed"
            self.workflows[workflow_id]["end_time"] = time.time()
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow by ID."""
        return self.workflows.get(workflow_id)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[str]:
        """Get workflow status."""
        workflow = self.workflows.get(workflow_id)
        return workflow["status"] if workflow else None
    
    def add_metrics(self, workflow_id: str, metrics: Dict):
        """Add metrics for a workflow."""
        self.metrics[workflow_id].append({
            "timestamp": time.time(),
            **metrics
        })
    
    def calculate_aggregate_metrics(self) -> Dict:
        """Calculate aggregate metrics across all workflows."""
        all_metrics = []
        for workflow_metrics in self.metrics.values():
            all_metrics.extend(workflow_metrics)
        
        if not all_metrics:
            return {}
        
        # Calculate aggregates
        durations = [m.get("duration", 0) for m in all_metrics]
        cpu_usages = [m.get("cpu_usage", 0) for m in all_metrics]
        memory_usages = [m.get("memory_usage", 0) for m in all_metrics]
        
        return {
            "total_workflows": len(self.workflows),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "avg_cpu": sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0,
            "avg_memory": sum(memory_usages) / len(memory_usages) if memory_usages else 0,
            "success_rate": sum(1 for m in all_metrics if m.get("success", False)) / len(all_metrics) if all_metrics else 0
        }
    
    async def async_write(self, file_path: Path, data: Dict):
        """Async write to file."""
        # Simulate async write
        await asyncio.sleep(0.0001)
        # In real implementation, would write to file
        return True
    
    def aggregate(self, metrics_data: List[Dict], operations: List[str]) -> Dict:
        """Aggregate metrics with specified operations."""
        import statistics
        
        values = [m.get("value", 0) for m in metrics_data]
        
        result = {}
        if "mean" in operations:
            result["mean"] = statistics.mean(values)
        if "median" in operations:
            result["median"] = statistics.median(values)
        if "std" in operations:
            result["std"] = statistics.stdev(values) if len(values) > 1 else 0
        if "percentile_95" in operations:
            sorted_values = sorted(values)
            idx = int(len(sorted_values) * 0.95)
            result["percentile_95"] = sorted_values[idx] if sorted_values else 0
        
        return result


class DIContainer:
    """Mock Dependency Injection Container for performance testing."""
    
    def __init__(self):
        self.services = {}
        self.instances = {}
    
    def register(self, service_id: str, factory):
        """Register a service."""
        self.services[service_id] = factory
    
    def resolve(self, service_id: str):
        """Resolve a service."""
        if service_id in self.instances:
            return self.instances[service_id]
        
        if service_id in self.services:
            instance = self.services[service_id]()
            self.instances[service_id] = instance
            return instance
        
        return None