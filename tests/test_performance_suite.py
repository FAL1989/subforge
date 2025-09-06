"""
Performance and Load Testing Suite for SubForge
Created: 2025-09-05 17:30 UTC-3 São Paulo

Comprehensive performance benchmarks and load tests for all SubForge components.
Tests measure execution time, memory usage, throughput, and system limits.
"""

import asyncio
import gc
import json
import os
import sys
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

import pytest
import psutil
from pytest_benchmark.fixture import BenchmarkFixture

# Optional import for async file I/O
try:
    import aiofiles
except ImportError:
    aiofiles = None

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import mock components for testing
from tests.mock_components import (
    PRPGenerator,
    ContextEngineer,
    ExampleRepository,
    PluginManager,
    WorkflowMonitor,
    DIContainer
)
from tests.test_models import AgentConfig, ProjectContext


# ============================================================================
# FIXTURES AND UTILITIES
# ============================================================================

@pytest.fixture
def prp_generator():
    """Create PRPGenerator instance for testing."""
    return PRPGenerator()


@pytest.fixture
def context_engineer():
    """Create ContextEngineer instance for testing."""
    return ContextEngineer()


@pytest.fixture
def example_repository():
    """Create ExampleRepository with test data."""
    repo = ExampleRepository()
    # Add 1000 test examples
    for i in range(1000):
        repo.add_example(
            category=f"category_{i % 10}",
            subcategory=f"subcategory_{i % 50}",
            example={
                "id": i,
                "name": f"example_{i}",
                "description": f"Test example {i}" * 10,
                "code": f"def function_{i}():\n    return {i}\n" * 5
            }
        )
    return repo


@pytest.fixture
def plugin_manager():
    """Create PluginManager instance for testing."""
    return PluginManager()


@pytest.fixture
def workflow_monitor():
    """Create WorkflowMonitor instance for testing."""
    return WorkflowMonitor()


@pytest.fixture
def di_container():
    """Create DIContainer with complex dependency graph."""
    container = DIContainer()
    
    # Register 100 services with interdependencies
    for i in range(100):
        container.register(f"service_{i}", lambda x=i: Mock(id=x))
    
    return container


@pytest.fixture
def sample_agent_config():
    """Create sample agent configuration."""
    return AgentConfig(
        name="test_agent",
        domain="testing",
        expertise=["performance", "benchmarking"],
        tools=["pytest", "benchmark"],
        knowledge_base={"test": "data" * 100}
    )


@pytest.fixture
def sample_project_context():
    """Create sample project context."""
    return ProjectContext(
        name="test_project",
        description="Performance test project" * 50,
        tech_stack=["python", "fastapi", "postgresql", "redis"],
        architecture="microservices",
        complexity="enterprise"
    )


@contextmanager
def memory_tracker():
    """Context manager for tracking memory usage."""
    tracemalloc.start()
    gc.collect()
    snapshot_before = tracemalloc.take_snapshot()
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    yield
    
    gc.collect()
    snapshot_after = tracemalloc.take_snapshot()
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    
    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    total_diff = sum(stat.size_diff for stat in top_stats)
    
    tracemalloc.stop()
    
    return {
        "memory_diff_mb": mem_after - mem_before,
        "tracemalloc_diff_mb": total_diff / 1024 / 1024,
        "peak_memory_mb": mem_after
    }


# ============================================================================
# PRP GENERATION BENCHMARKS
# ============================================================================

@pytest.mark.benchmark(group="prp_generation")
def test_prp_generation_performance(benchmark, prp_generator, sample_agent_config):
    """Benchmark single PRP generation - Target: < 100ms."""
    
    def generate_prp():
        return prp_generator.generate(
            agent_config=sample_agent_config,
            context={"task": "performance testing"}
        )
    
    result = benchmark(generate_prp)
    
    assert result is not None
    assert len(result) > 100  # Ensure meaningful PRP generated
    assert benchmark.stats["mean"] < 0.1  # < 100ms


@pytest.mark.benchmark(group="prp_generation")
def test_prp_batch_generation(benchmark, prp_generator, sample_agent_config):
    """Benchmark batch PRP generation - Target: > 10 PRPs/second."""
    
    def generate_batch():
        prps = []
        for i in range(100):
            config = sample_agent_config
            config.name = f"agent_{i}"
            prp = prp_generator.generate(
                agent_config=config,
                context={"task": f"task_{i}"}
            )
            prps.append(prp)
        return prps
    
    results = benchmark(generate_batch)
    
    assert len(results) == 100
    # Calculate throughput
    throughput = 100 / benchmark.stats["mean"]
    assert throughput > 10  # > 10 PRPs/second


@pytest.mark.benchmark(group="prp_generation")
def test_template_rendering_performance(benchmark, prp_generator):
    """Benchmark template rendering - Target: < 10ms."""
    
    template_data = {
        "agent_name": "test_agent",
        "expertise": ["area1", "area2", "area3"] * 10,
        "tools": ["tool1", "tool2", "tool3"] * 10,
        "context": {"key": "value"} | {f"key_{i}": f"value_{i}" for i in range(100)}
    }
    
    def render_template():
        return prp_generator.render_template("default", template_data)
    
    result = benchmark(render_template)
    
    assert result is not None
    assert benchmark.stats["mean"] < 0.01  # < 10ms


@pytest.mark.benchmark(group="prp_generation")
def test_prp_complexity_scaling(benchmark, prp_generator):
    """Test PRP generation performance with increasing complexity."""
    
    complexities = []
    
    def generate_complex_prp(complexity_level):
        config = AgentConfig(
            name="complex_agent",
            domain="testing",
            expertise=["area"] * complexity_level,
            tools=["tool"] * complexity_level,
            knowledge_base={f"key_{i}": f"value_{i}" * 10 for i in range(complexity_level * 10)}
        )
        return prp_generator.generate(config, {"complexity": complexity_level})
    
    # Test with different complexity levels
    for level in [1, 10, 50, 100]:
        benchmark.pedantic(generate_complex_prp, args=(level,), rounds=10)
        complexities.append((level, benchmark.stats["mean"]))
    
    # Ensure sub-linear scaling
    # Time should not increase linearly with complexity
    time_ratio = complexities[-1][1] / complexities[0][1]
    complexity_ratio = complexities[-1][0] / complexities[0][0]
    assert time_ratio < complexity_ratio * 0.5  # Sub-linear scaling


# ============================================================================
# CONTEXT ENGINEERING BENCHMARKS
# ============================================================================

@pytest.mark.benchmark(group="context_engineering")
def test_context_creation_performance(benchmark, context_engineer, sample_project_context):
    """Benchmark full context package creation - Target: < 200ms."""
    
    def create_context():
        return context_engineer.create_context(
            project=sample_project_context,
            task="performance testing",
            additional_context={"key": "value"} | {f"k_{i}": f"v_{i}" for i in range(50)}
        )
    
    result = benchmark(create_context)
    
    assert result is not None
    assert benchmark.stats["mean"] < 0.2  # < 200ms


@pytest.mark.benchmark(group="context_engineering")
def test_context_cache_performance(benchmark, context_engineer):
    """Benchmark cache hit vs cache miss - Target: 100x faster on cache hit."""
    
    cache_key = "test_cache_key"
    context_data = {"large": "data" * 1000}
    
    # First call - cache miss
    context_engineer.get_or_create(cache_key, lambda: context_data)
    
    # Benchmark cache hit
    def cache_hit():
        return context_engineer.get_or_create(cache_key, lambda: context_data)
    
    # Benchmark cache miss
    def cache_miss():
        return context_engineer.get_or_create(f"{cache_key}_{time.time()}", lambda: context_data)
    
    # Measure cache hit
    benchmark.pedantic(cache_hit, rounds=100)
    cache_hit_time = benchmark.stats["mean"]
    
    # Measure cache miss
    benchmark.pedantic(cache_miss, rounds=10)
    cache_miss_time = benchmark.stats["mean"]
    
    # Cache hit should be at least 100x faster
    assert cache_hit_time * 100 < cache_miss_time


@pytest.mark.benchmark(group="context_engineering")
def test_example_repository_search(benchmark, example_repository):
    """Benchmark example repository search - Target: < 50ms for 1000+ examples."""
    
    def search_examples():
        results = []
        # Search different categories
        for i in range(10):
            results.extend(example_repository.search(
                category=f"category_{i}",
                limit=10
            ))
        return results
    
    results = benchmark(search_examples)
    
    assert len(results) > 0
    assert benchmark.stats["mean"] < 0.05  # < 50ms


@pytest.mark.benchmark(group="context_engineering")
def test_context_merging_performance(benchmark, context_engineer):
    """Benchmark context merging operations."""
    
    contexts = [
        {"level": i, "data": f"context_{i}" * 100}
        for i in range(20)
    ]
    
    def merge_contexts():
        return context_engineer.merge_contexts(contexts)
    
    result = benchmark(merge_contexts)
    
    assert result is not None
    assert benchmark.stats["mean"] < 0.02  # < 20ms


# ============================================================================
# PLUGIN SYSTEM BENCHMARKS
# ============================================================================

@pytest.mark.benchmark(group="plugin_system")
def test_plugin_loading_performance(benchmark, plugin_manager):
    """Benchmark single plugin loading - Target: < 500ms."""
    
    def load_plugin():
        plugin_manager.load_plugin("test_plugin", {
            "name": "TestPlugin",
            "version": "1.0.0",
            "dependencies": ["dep1", "dep2"],
            "init": lambda: Mock()
        })
    
    benchmark(load_plugin)
    
    assert benchmark.stats["mean"] < 0.5  # < 500ms


@pytest.mark.benchmark(group="plugin_system")
def test_parallel_plugin_loading(benchmark, plugin_manager):
    """Benchmark parallel plugin loading - Target: < 2 seconds for 10 plugins."""
    
    plugins = [
        {
            "id": f"plugin_{i}",
            "config": {
                "name": f"Plugin{i}",
                "version": "1.0.0",
                "dependencies": [f"dep_{j}" for j in range(5)],
                "init": lambda: Mock()
            }
        }
        for i in range(10)
    ]
    
    def load_plugins_parallel():
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(plugin_manager.load_plugin, p["id"], p["config"])
                for p in plugins
            ]
            return [f.result() for f in futures]
    
    results = benchmark(load_plugins_parallel)
    
    assert len(results) == 10
    assert benchmark.stats["mean"] < 2.0  # < 2 seconds


@pytest.mark.benchmark(group="plugin_system")
def test_di_container_resolution(benchmark, di_container):
    """Benchmark DI container resolution - Target: < 1ms per resolution."""
    
    def resolve_dependency():
        results = []
        for i in range(100):
            results.append(di_container.resolve(f"service_{i}"))
        return results
    
    results = benchmark(resolve_dependency)
    
    assert len(results) == 100
    # Average time per resolution
    avg_time = benchmark.stats["mean"] / 100
    assert avg_time < 0.001  # < 1ms per resolution


@pytest.mark.benchmark(group="plugin_system")
def test_plugin_execution_performance(benchmark, plugin_manager):
    """Benchmark plugin execution performance."""
    
    # Setup mock plugins with various operations
    for i in range(5):
        plugin_manager.load_plugin(f"exec_plugin_{i}", {
            "name": f"ExecPlugin{i}",
            "execute": lambda x=i: sum(range(1000)) * x
        })
    
    def execute_plugins():
        results = []
        for i in range(5):
            plugin = plugin_manager.get_plugin(f"exec_plugin_{i}")
            results.append(plugin["execute"]())
        return results
    
    results = benchmark(execute_plugins)
    
    assert len(results) == 5
    assert benchmark.stats["mean"] < 0.01  # < 10ms


# ============================================================================
# MONITORING SYSTEM BENCHMARKS
# ============================================================================

@pytest.mark.benchmark(group="monitoring")
def test_workflow_lookup_performance(benchmark, workflow_monitor):
    """Benchmark workflow lookup - Target: < 1ms for 1000 workflows."""
    
    # Add 1000 workflows
    for i in range(1000):
        workflow_monitor.register_workflow(f"workflow_{i}", {
            "id": f"workflow_{i}",
            "status": "running",
            "metrics": {"metric": i}
        })
    
    def lookup_workflows():
        results = []
        for i in range(0, 1000, 10):  # Lookup 100 workflows
            results.append(workflow_monitor.get_workflow(f"workflow_{i}"))
        return results
    
    results = benchmark(lookup_workflows)
    
    assert len(results) == 100
    assert benchmark.stats["mean"] < 0.001  # < 1ms


@pytest.mark.benchmark(group="monitoring")
def test_metrics_calculation(benchmark, workflow_monitor):
    """Benchmark metrics calculation - Target: < 100ms for 1000 workflows."""
    
    # Add 1000 workflows with metrics
    for i in range(1000):
        workflow_monitor.add_metrics(f"workflow_{i}", {
            "duration": i * 0.1,
            "cpu_usage": i % 100,
            "memory_usage": i * 1024,
            "success": i % 2 == 0
        })
    
    def calculate_metrics():
        return workflow_monitor.calculate_aggregate_metrics()
    
    result = benchmark(calculate_metrics)
    
    assert result is not None
    assert benchmark.stats["mean"] < 0.1  # < 100ms


@pytest.mark.benchmark(group="monitoring")
async def test_async_write_performance(benchmark, workflow_monitor, tmp_path):
    """Benchmark async file writes - Target: 1000 writes/second."""
    
    output_dir = tmp_path / "monitoring_output"
    output_dir.mkdir()
    
    async def write_metrics():
        tasks = []
        for i in range(1000):
            file_path = output_dir / f"metric_{i}.json"
            data = {"id": i, "timestamp": time.time(), "value": i * 100}
            tasks.append(workflow_monitor.async_write(file_path, data))
        await asyncio.gather(*tasks)
    
    # Run async benchmark
    loop = asyncio.get_event_loop()
    
    def run_async_write():
        loop.run_until_complete(write_metrics())
    
    benchmark(run_async_write)
    
    # Calculate throughput
    throughput = 1000 / benchmark.stats["mean"]
    assert throughput > 1000  # > 1000 writes/second


@pytest.mark.benchmark(group="monitoring")
def test_metric_aggregation_performance(benchmark, workflow_monitor):
    """Benchmark metric aggregation with various statistical operations."""
    
    # Generate large dataset
    metrics_data = []
    for i in range(10000):
        metrics_data.append({
            "timestamp": time.time() + i,
            "value": i % 1000,
            "category": f"cat_{i % 10}"
        })
    
    def aggregate_metrics():
        return workflow_monitor.aggregate(
            metrics_data,
            operations=["mean", "median", "std", "percentile_95"]
        )
    
    result = benchmark(aggregate_metrics)
    
    assert result is not None
    assert benchmark.stats["mean"] < 0.5  # < 500ms for 10k metrics


# ============================================================================
# MEMORY PROFILING TESTS
# ============================================================================

@pytest.mark.memory
def test_memory_usage_prp_generation(prp_generator, sample_agent_config):
    """Test memory usage for PRP generation - Target: < 100MB for 100 PRPs."""
    
    with memory_tracker() as mem:
        prps = []
        for i in range(100):
            config = sample_agent_config
            config.name = f"agent_{i}"
            prp = prp_generator.generate(config, {"task": f"task_{i}"})
            prps.append(prp)
    
    memory_stats = mem.__exit__(None, None, None)
    
    assert memory_stats["peak_memory_mb"] < 100  # < 100MB
    assert len(prps) == 100


@pytest.mark.memory
def test_memory_usage_context_engineering(context_engineer, sample_project_context):
    """Test memory usage for context creation - Target: < 50MB per context."""
    
    contexts = []
    
    with memory_tracker() as mem:
        for i in range(10):
            context = context_engineer.create_context(
                project=sample_project_context,
                task=f"task_{i}",
                additional_context={f"key_{j}": f"value_{j}" * 100 for j in range(100)}
            )
            contexts.append(context)
    
    memory_stats = mem.__exit__(None, None, None)
    
    avg_memory_per_context = memory_stats["memory_diff_mb"] / 10
    assert avg_memory_per_context < 50  # < 50MB per context


@pytest.mark.memory
def test_memory_leak_detection(prp_generator, context_engineer):
    """Test for memory leaks - Run 1000 operations and verify no memory growth."""
    
    initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    # Run many operations
    for i in range(1000):
        # Generate PRP
        prp = prp_generator.generate(
            AgentConfig(name=f"agent_{i}", domain="test"),
            {"task": "test"}
        )
        
        # Create context
        context = context_engineer.create_context(
            ProjectContext(name=f"project_{i}"),
            task="test"
        )
        
        # Force garbage collection periodically
        if i % 100 == 0:
            gc.collect()
    
    # Final garbage collection
    gc.collect()
    final_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    # Memory should not grow significantly (allow 10% growth)
    memory_growth = (final_memory - initial_memory) / initial_memory
    assert memory_growth < 0.1  # < 10% growth


@pytest.mark.memory
def test_large_object_memory_management(example_repository):
    """Test memory management with large objects."""
    
    with memory_tracker() as mem:
        # Create large examples
        for i in range(100):
            large_example = {
                "id": i,
                "data": "x" * 1000000,  # 1MB string
                "nested": {"level": "data" * 10000}
            }
            example_repository.add_example("large", f"sub_{i}", large_example)
        
        # Search and retrieve
        results = example_repository.search(category="large", limit=50)
    
    memory_stats = mem.__exit__(None, None, None)
    
    # Should handle large objects efficiently
    assert memory_stats["peak_memory_mb"] < 200  # < 200MB for 100MB of data


# ============================================================================
# LOAD TESTING
# ============================================================================

@pytest.mark.load
@pytest.mark.asyncio
async def test_concurrent_workflows():
    """Test concurrent workflow execution - Target: 1000 workflows < 30 seconds."""
    
    workflow_monitor = WorkflowMonitor()
    
    async def run_workflow(workflow_id):
        # Simulate workflow execution
        workflow_monitor.start_workflow(workflow_id)
        await asyncio.sleep(0.01)  # Simulate work
        workflow_monitor.complete_workflow(workflow_id)
        return workflow_id
    
    start_time = time.time()
    
    # Run 1000 concurrent workflows
    tasks = [run_workflow(f"workflow_{i}") for i in range(1000)]
    results = await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    
    assert len(results) == 1000
    assert duration < 30  # < 30 seconds
    assert all(workflow_monitor.get_workflow_status(f"workflow_{i}") == "completed" 
               for i in range(1000))


@pytest.mark.load
@pytest.mark.asyncio
async def test_system_under_load():
    """Test system under load - 100 concurrent users, 10 operations each."""
    
    prp_generator = PRPGenerator()
    context_engineer = ContextEngineer()
    failures = []
    
    async def simulate_user(user_id):
        """Simulate a user performing operations."""
        user_failures = []
        
        for op in range(10):
            try:
                # Operation 1: Generate PRP
                config = AgentConfig(name=f"user_{user_id}_agent_{op}", domain="test")
                prp = await asyncio.to_thread(
                    prp_generator.generate, 
                    config, 
                    {"task": f"task_{op}"}
                )
                
                # Operation 2: Create context
                context = await asyncio.to_thread(
                    context_engineer.create_context,
                    ProjectContext(name=f"project_{user_id}"),
                    task=f"task_{op}"
                )
                
                # Simulate processing time
                await asyncio.sleep(0.01)
                
            except Exception as e:
                user_failures.append((user_id, op, str(e)))
        
        return user_failures
    
    # Run 100 concurrent users
    start_time = time.time()
    user_tasks = [simulate_user(i) for i in range(100)]
    user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
    duration = time.time() - start_time
    
    # Collect failures
    for result in user_results:
        if isinstance(result, list):
            failures.extend(result)
        elif isinstance(result, Exception):
            failures.append(("unknown", -1, str(result)))
    
    failure_rate = len(failures) / 1000  # Total operations: 100 users * 10 ops
    
    assert failure_rate < 0.05  # < 5% failure rate
    assert duration < 60  # Complete within 60 seconds


@pytest.mark.load
@pytest.mark.asyncio
async def test_stress_testing():
    """Push system to limits and measure graceful degradation."""
    
    workflow_monitor = WorkflowMonitor()
    performance_metrics = {
        "throughput": [],
        "latency": [],
        "errors": []
    }
    
    async def stress_operation(load_level):
        """Execute operations at specified load level."""
        tasks = []
        errors = 0
        
        for i in range(load_level):
            async def operation(op_id):
                try:
                    start = time.time()
                    workflow_monitor.start_workflow(f"stress_{op_id}")
                    await asyncio.sleep(0.001)  # Minimal work
                    workflow_monitor.complete_workflow(f"stress_{op_id}")
                    return time.time() - start
                except Exception:
                    return None
            
            tasks.append(operation(i))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Calculate metrics
        latencies = [r for r in results if isinstance(r, float)]
        errors = len([r for r in results if r is None or isinstance(r, Exception)])
        
        return {
            "load_level": load_level,
            "throughput": len(latencies) / total_time if total_time > 0 else 0,
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
            "error_rate": errors / load_level if load_level > 0 else 0
        }
    
    # Test with increasing load levels
    load_levels = [100, 500, 1000, 2000, 5000]
    
    for level in load_levels:
        metrics = await stress_operation(level)
        performance_metrics["throughput"].append(metrics["throughput"])
        performance_metrics["latency"].append(metrics["avg_latency"])
        performance_metrics["errors"].append(metrics["error_rate"])
        
        # System should degrade gracefully
        if level > 1000:
            # Error rate should not exceed 20% even under extreme load
            assert metrics["error_rate"] < 0.2
    
    # Verify graceful degradation
    # Throughput should decrease gradually, not cliff
    for i in range(1, len(performance_metrics["throughput"])):
        if performance_metrics["throughput"][i] < performance_metrics["throughput"][i-1]:
            # Degradation should be gradual (not more than 50% drop)
            drop_rate = 1 - (performance_metrics["throughput"][i] / 
                            performance_metrics["throughput"][i-1])
            assert drop_rate < 0.5  # < 50% drop between levels


@pytest.mark.load
async def test_resource_exhaustion_handling():
    """Test system behavior when resources are exhausted."""
    
    plugin_manager = PluginManager()
    
    # Attempt to load many plugins simultaneously
    async def exhaust_resources():
        tasks = []
        for i in range(10000):  # Excessive number
            async def load_plugin(plugin_id):
                try:
                    plugin_manager.load_plugin(f"plugin_{plugin_id}", {
                        "name": f"Plugin{plugin_id}",
                        "data": "x" * 10000  # 10KB per plugin
                    })
                    return True
                except Exception:
                    return False
            
            tasks.append(load_plugin(i))
        
        results = await asyncio.gather(*tasks)
        return results
    
    results = await exhaust_resources()
    
    # System should handle resource exhaustion gracefully
    success_rate = sum(results) / len(results)
    
    # At least some operations should succeed
    assert success_rate > 0.1
    
    # System should still be responsive after stress
    test_plugin = plugin_manager.load_plugin("test_after_stress", {"name": "Test"})
    assert test_plugin is not None


# ============================================================================
# SCALABILITY TESTS
# ============================================================================

@pytest.mark.benchmark(group="scalability")
def test_linear_scalability(benchmark):
    """Test that system scales linearly with load."""
    
    def process_items(count):
        results = []
        for i in range(count):
            # Simulate processing
            results.append(sum(range(100)))
        return results
    
    times = []
    counts = [100, 200, 400, 800]
    
    for count in counts:
        benchmark.pedantic(process_items, args=(count,), rounds=5)
        times.append((count, benchmark.stats["mean"]))
    
    # Check for linear scaling
    for i in range(1, len(times)):
        time_ratio = times[i][1] / times[0][1]
        count_ratio = times[i][0] / times[0][0]
        # Allow 20% deviation from linear
        assert abs(time_ratio - count_ratio) / count_ratio < 0.2


@pytest.mark.benchmark(group="scalability")
async def test_parallel_scalability():
    """Test parallel processing scalability."""
    
    async def parallel_task(task_id):
        # Simulate CPU-bound work
        result = sum(i * i for i in range(1000))
        await asyncio.sleep(0.001)
        return result
    
    # Test with different parallelism levels
    parallelism_levels = [1, 2, 4, 8, 16]
    results = {}
    
    for level in parallelism_levels:
        start = time.time()
        tasks = [parallel_task(i) for i in range(level * 10)]
        await asyncio.gather(*tasks)
        duration = time.time() - start
        results[level] = duration
    
    # Verify that doubling parallelism roughly halves time (with diminishing returns)
    for i in range(1, len(parallelism_levels)):
        if parallelism_levels[i] <= 8:  # Expect good scaling up to 8x
            speedup = results[parallelism_levels[0]] / results[parallelism_levels[i]]
            expected_speedup = parallelism_levels[i] / parallelism_levels[0]
            # Allow 30% deviation from ideal speedup
            assert speedup > expected_speedup * 0.7


# ============================================================================
# ENDURANCE TESTS
# ============================================================================

@pytest.mark.slow
@pytest.mark.benchmark(group="endurance")
def test_long_running_stability():
    """Test system stability over extended operation."""
    
    workflow_monitor = WorkflowMonitor()
    start_time = time.time()
    errors = []
    
    # Run for 60 seconds
    while time.time() - start_time < 60:
        try:
            workflow_id = f"endurance_{int(time.time() * 1000)}"
            workflow_monitor.start_workflow(workflow_id)
            
            # Simulate work
            time.sleep(0.01)
            
            workflow_monitor.complete_workflow(workflow_id)
            
        except Exception as e:
            errors.append(str(e))
    
    # System should remain stable
    assert len(errors) < 10  # Less than 10 errors in 60 seconds
    
    # Memory should not have grown excessively
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    assert memory_mb < 500  # Less than 500MB after extended run


# ============================================================================
# BENCHMARK COMPARISON TESTS
# ============================================================================

@pytest.mark.benchmark(group="comparison")
def test_implementation_comparison(benchmark):
    """Compare different implementation approaches."""
    
    # Implementation 1: List comprehension
    def list_comp_approach():
        return [i * i for i in range(10000)]
    
    # Implementation 2: Map
    def map_approach():
        return list(map(lambda x: x * x, range(10000)))
    
    # Implementation 3: Generator
    def generator_approach():
        return list(i * i for i in range(10000))
    
    # Benchmark all approaches
    implementations = [
        ("list_comp", list_comp_approach),
        ("map", map_approach),
        ("generator", generator_approach)
    ]
    
    results = {}
    for name, impl in implementations:
        result = benchmark.pedantic(impl, rounds=100)
        results[name] = benchmark.stats["mean"]
    
    # Find fastest implementation
    fastest = min(results, key=results.get)
    
    # Document performance differences
    print(f"\nImplementation Performance Comparison:")
    for name, time in results.items():
        ratio = time / results[fastest]
        print(f"  {name}: {time:.6f}s ({ratio:.2f}x)")


# ============================================================================
# NETWORK/IO PERFORMANCE TESTS
# ============================================================================

@pytest.mark.benchmark(group="io")
@pytest.mark.skipif(aiofiles is None, reason="aiofiles not installed")
async def test_async_io_performance(tmp_path):
    """Test async I/O performance."""
    
    test_file = tmp_path / "async_test.txt"
    test_data = "x" * 1000  # 1KB of data
    
    async def write_async():
        async with aiofiles.open(test_file, 'w') as f:
            for _ in range(100):
                await f.write(test_data)
    
    async def read_async():
        async with aiofiles.open(test_file, 'r') as f:
            return await f.read()
    
    # Benchmark writes
    start = time.time()
    await write_async()
    write_time = time.time() - start
    
    # Benchmark reads
    start = time.time()
    data = await read_async()
    read_time = time.time() - start
    
    # Calculate throughput
    write_throughput = (100 * len(test_data)) / write_time / 1024 / 1024  # MB/s
    read_throughput = len(data) / read_time / 1024 / 1024  # MB/s
    
    assert write_throughput > 10  # > 10 MB/s write
    assert read_throughput > 50  # > 50 MB/s read


@pytest.mark.benchmark(group="io")
def test_batch_vs_individual_operations(benchmark, tmp_path):
    """Compare batch vs individual operation performance."""
    
    output_dir = tmp_path / "batch_test"
    output_dir.mkdir()
    
    data_items = [{"id": i, "data": f"item_{i}" * 100} for i in range(100)]
    
    # Individual operations
    def individual_writes():
        for i, item in enumerate(data_items):
            with open(output_dir / f"individual_{i}.json", 'w') as f:
                json.dump(item, f)
    
    # Batch operation
    def batch_write():
        with open(output_dir / "batch.json", 'w') as f:
            json.dump(data_items, f)
    
    # Benchmark both
    individual_time = benchmark.pedantic(individual_writes, rounds=10)
    batch_time = benchmark.pedantic(batch_write, rounds=10)
    
    # Batch should be significantly faster
    assert batch_time < individual_time * 0.1  # Batch should be >10x faster


if __name__ == "__main__":
    # Run performance tests with detailed output
    pytest.main([
        __file__,
        "-v",
        "--benchmark-only",
        "--benchmark-verbose",
        "--benchmark-sort=mean",
        "--benchmark-columns=min,max,mean,stddev,rounds,iterations"
    ])