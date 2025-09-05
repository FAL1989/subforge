#!/usr/bin/env python3
"""
Performance Benchmarks for Phase 3 Refactoring
Ensures refactoring maintained or improved performance

This module provides:
1. Baseline performance measurements
2. Memory usage profiling  
3. Scalability testing
4. Regression detection
5. Performance reporting

Created: 2025-09-05 17:35 UTC-3 São Paulo
"""

import asyncio
import gc
import psutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from contextlib import contextmanager

import pytest
import pytest_benchmark

# Import components to benchmark
from subforge.core.prp import (
    PRPGenerator,
    PRPType, 
    create_prp_generator,
    create_fluent_builder
)
from subforge.core.context_engineer import (
    ContextEngineer,
    ContextLevel,
    create_context_engineer
)
from subforge.plugins.plugin_manager import PluginManager
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity
)


@dataclass
class PerformanceMetrics:
    """Performance measurement data"""
    operation: str
    duration_ms: float
    memory_peak_mb: float
    memory_current_mb: float
    cpu_percent: float
    iterations: int
    timestamp: float


@contextmanager
def performance_monitor():
    """Context manager for monitoring performance metrics"""
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_cpu = process.cpu_percent()
    start_time = time.perf_counter()
    
    # Force garbage collection for consistent measurements
    gc.collect()
    
    try:
        yield
    finally:
        end_time = time.perf_counter()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = process.cpu_percent()
        
        # Store metrics (could be extended to write to file/database)
        duration_ms = (end_time - start_time) * 1000
        memory_delta = end_memory - start_memory


class PerformanceBenchmarks:
    """Performance benchmark suite"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each benchmark test"""
        # Clean memory before each test
        gc.collect()
        
        # Create temporary workspace
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir)
        
        # Create sample project profile
        self.sample_profile = ProjectProfile(
            name="BenchmarkProject",
            path=Path("/tmp/benchmark"),
            technology_stack=TechnologyStack(
                languages={"python", "typescript", "javascript"},
                frameworks={"fastapi", "react", "nextjs"},
                databases={"postgresql", "redis"},
                tools={"docker", "pytest", "jest"},
                package_managers={"pip", "npm"}
            ),
            architecture_pattern=ArchitecturePattern.JAMSTACK,
            complexity=ProjectComplexity.ENTERPRISE,
            team_size_estimate=8,
            has_tests=True,
            has_ci_cd=True,
            has_docker=True,
            file_count=1292,
            lines_of_code=257891,
            has_docs=True,
            recommended_subagents=["api-developer", "test-engineer"],
            integration_requirements=["fastapi", "postgresql"]
        )
    
    def test_prp_generation_baseline(self, benchmark):
        """Benchmark PRP generation performance"""
        generator = create_prp_generator(self.workspace)
        
        context = {
            "project_profile": self.sample_profile,
            "context_package": None,  # Minimal context for baseline
            "user_request": "Generate performance test"
        }
        
        def generate_prp():
            return asyncio.run(generator.generate_prp(PRPType.FACTORY_ANALYSIS, context))
        
        result = benchmark.pedantic(generate_prp, iterations=10, rounds=3)
        assert result is not None
        
        # Performance assertions
        stats = benchmark.stats
        assert stats.mean < 1.0  # Should complete in less than 1 second on average
        assert stats.stddev < 0.5  # Low variance
    
    def test_prp_generation_complex(self, benchmark):
        """Benchmark PRP generation with complex context"""
        generator = create_prp_generator(self.workspace)
        engineer = create_context_engineer(self.workspace)
        
        # Create comprehensive context package
        context_package = engineer.engineer_context(
            self.sample_profile, 
            ContextLevel.COMPREHENSIVE
        )
        
        context = {
            "project_profile": self.sample_profile,
            "context_package": context_package,
            "user_request": "Create comprehensive enterprise test suite with full coverage"
        }
        
        def generate_complex_prp():
            return asyncio.run(generator.generate_prp(PRPType.FACTORY_ANALYSIS, context))
        
        result = benchmark.pedantic(generate_complex_prp, iterations=5, rounds=3)
        assert result is not None
        
        # Complex operations may take longer but should still be reasonable
        stats = benchmark.stats
        assert stats.mean < 3.0  # Should complete in less than 3 seconds
    
    def test_context_engineering_baseline(self, benchmark):
        """Benchmark context engineering performance"""
        engineer = create_context_engineer(self.workspace)
        
        def engineer_context():
            return engineer.engineer_context(self.sample_profile, ContextLevel.BASIC)
        
        result = benchmark.pedantic(engineer_context, iterations=10, rounds=3)
        assert result is not None
        
        stats = benchmark.stats
        assert stats.mean < 0.5  # Basic context should be fast
    
    def test_context_engineering_comprehensive(self, benchmark):
        """Benchmark comprehensive context engineering"""
        engineer = create_context_engineer(self.workspace)
        
        def engineer_comprehensive_context():
            return engineer.engineer_context(self.sample_profile, ContextLevel.COMPREHENSIVE)
        
        result = benchmark.pedantic(engineer_comprehensive_context, iterations=5, rounds=3)
        assert result is not None
        
        stats = benchmark.stats
        assert stats.mean < 2.0  # Comprehensive context should still be reasonable
    
    def test_plugin_manager_initialization(self, benchmark):
        """Benchmark plugin manager initialization"""
        def init_plugin_manager():
            return PluginManager(self.workspace / "plugins")
        
        result = benchmark.pedantic(init_plugin_manager, iterations=10, rounds=3)
        assert result is not None
        assert len(result.plugins) > 0
        
        stats = benchmark.stats
        assert stats.mean < 0.2  # Plugin manager init should be fast
    
    def test_plugin_execution(self, benchmark):
        """Benchmark plugin execution"""
        plugin_manager = PluginManager(self.workspace / "plugins")
        agent_plugins = plugin_manager.get_agent_plugins()
        
        if not agent_plugins:
            pytest.skip("No agent plugins available for benchmarking")
        
        plugin_name = agent_plugins[0]
        context = {"project_profile": self.sample_profile.__dict__}
        
        def execute_plugin():
            return plugin_manager.execute_plugin(plugin_name, context)
        
        result = benchmark.pedantic(execute_plugin, iterations=20, rounds=3)
        assert result is not None
        
        stats = benchmark.stats
        assert stats.mean < 0.1  # Plugin execution should be very fast
    
    def test_fluent_builder_performance(self, benchmark):
        """Benchmark fluent builder pattern performance"""
        def build_with_fluent_builder():
            builder = create_fluent_builder()
            return (builder
                .for_project("BenchmarkProject")
                .for_analysis()
                .with_execution_prompt("Benchmark test")
                .with_standard_analysis_checklist()
                .add_success_metric("Performance acceptable")
                .build())
        
        result = benchmark.pedantic(build_with_fluent_builder, iterations=50, rounds=3)
        assert result is not None
        
        stats = benchmark.stats
        assert stats.mean < 0.05  # Builder pattern should be very fast
    
    def test_memory_usage_prp_generation(self):
        """Test memory usage during PRP generation"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        generator = create_prp_generator(self.workspace)
        context = {
            "project_profile": self.sample_profile,
            "context_package": None,
            "user_request": "Memory test"
        }
        
        # Generate multiple PRPs to test memory accumulation
        for i in range(10):
            prp = asyncio.run(generator.generate_prp(PRPType.FACTORY_ANALYSIS, context))
            assert prp is not None
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = peak_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB for 10 PRPs)
        assert memory_growth < 50, f"Memory growth too high: {memory_growth}MB"
    
    def test_memory_usage_context_engineering(self):
        """Test memory usage during context engineering"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        engineer = create_context_engineer(self.workspace)
        
        # Engineer multiple contexts to test memory accumulation
        for i in range(5):
            context = engineer.engineer_context(self.sample_profile, ContextLevel.COMPREHENSIVE)
            assert context is not None
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = peak_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for 5 comprehensive contexts)
        assert memory_growth < 100, f"Memory growth too high: {memory_growth}MB"
    
    def test_scalability_multiple_projects(self, benchmark):
        """Test performance scalability with multiple projects"""
        generator = create_prp_generator(self.workspace)
        
        # Create multiple project profiles
        projects = []
        for i in range(5):
            profile = ProjectProfile(
                name=f"ScaleProject{i}",
                path=Path(f"/tmp/scale{i}"),
                technology_stack=TechnologyStack(
                    languages={"python"},
                    frameworks={"fastapi"},
                    databases=set(),
                    tools={"pytest"},
                    package_managers={"pip"}
                ),
                architecture_pattern=ArchitecturePattern.MODULAR,
                complexity=ProjectComplexity.MEDIUM,
                team_size_estimate=3,
                has_tests=True,
                has_ci_cd=False,
                has_docker=False,
                file_count=100 * (i + 1),  # Varying complexity
                lines_of_code=5000 * (i + 1),
                has_docs=False,
                recommended_subagents=[],
                integration_requirements=[]
            )
            projects.append(profile)
        
        def generate_for_multiple_projects():
            results = []
            for profile in projects:
                context = {
                    "project_profile": profile,
                    "context_package": None,
                    "user_request": f"Scale test for {profile.name}"
                }
                prp = asyncio.run(generator.generate_prp(PRPType.FACTORY_ANALYSIS, context))
                results.append(prp)
            return results
        
        results = benchmark.pedantic(generate_for_multiple_projects, iterations=3, rounds=2)
        assert len(results) == 5
        assert all(prp is not None for prp in results)
        
        # Should scale reasonably with number of projects
        stats = benchmark.stats
        assert stats.mean < 5.0  # 5 projects should complete in less than 5 seconds
    
    def test_concurrent_operations(self):
        """Test performance under concurrent operations"""
        async def concurrent_prp_generation():
            generator = create_prp_generator(self.workspace)
            engineer = create_context_engineer(self.workspace)
            
            # Prepare contexts for concurrent generation
            contexts = []
            for i in range(3):
                context = {
                    "project_profile": self.sample_profile,
                    "context_package": None,
                    "user_request": f"Concurrent test {i}"
                }
                contexts.append(context)
            
            # Generate PRPs concurrently
            tasks = [
                generator.generate_prp(PRPType.FACTORY_ANALYSIS, ctx)
                for ctx in contexts
            ]
            
            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks)
            duration = time.perf_counter() - start_time
            
            return results, duration
        
        results, duration = asyncio.run(concurrent_prp_generation())
        
        assert len(results) == 3
        assert all(prp is not None for prp in results)
        # Concurrent operations should be faster than sequential
        assert duration < 2.0  # Should complete in less than 2 seconds
    
    def test_cache_performance(self, benchmark):
        """Test caching performance improvements"""
        engineer = create_context_engineer(self.workspace)
        
        def first_context_call():
            """First call - should be cache miss"""
            return engineer.engineer_context(self.sample_profile, ContextLevel.BASIC)
        
        def cached_context_call():
            """Second call - should be cache hit"""
            return engineer.engineer_context(self.sample_profile, ContextLevel.BASIC)
        
        # Measure first call (cache miss)
        first_result = benchmark.pedantic(first_context_call, iterations=3, rounds=1)
        first_stats = benchmark.stats
        
        # Clear benchmark stats for second measurement
        benchmark.reset()
        
        # Measure second call (cache hit)  
        second_result = benchmark.pedantic(cached_context_call, iterations=10, rounds=3)
        second_stats = benchmark.stats
        
        assert first_result is not None
        assert second_result is not None
        
        # Cache hit should be significantly faster
        speedup_ratio = first_stats.mean / second_stats.mean
        assert speedup_ratio > 2.0, f"Cache speedup insufficient: {speedup_ratio}x"
    
    def test_regression_detection(self):
        """Detect performance regressions from baseline"""
        # This would typically compare against stored baseline metrics
        # For now, we'll test that operations complete within acceptable limits
        
        with performance_monitor():
            # PRP Generation
            generator = create_prp_generator(self.workspace)
            context = {
                "project_profile": self.sample_profile,
                "context_package": None,
                "user_request": "Regression test"
            }
            
            start_time = time.perf_counter()
            prp = asyncio.run(generator.generate_prp(PRPType.FACTORY_ANALYSIS, context))
            prp_duration = time.perf_counter() - start_time
            
            assert prp is not None
            assert prp_duration < 2.0  # Baseline: should complete in under 2 seconds
        
        with performance_monitor():
            # Context Engineering
            engineer = create_context_engineer(self.workspace)
            
            start_time = time.perf_counter()
            context_pkg = engineer.engineer_context(self.sample_profile, ContextLevel.BASIC)
            context_duration = time.perf_counter() - start_time
            
            assert context_pkg is not None
            assert context_duration < 1.0  # Baseline: should complete in under 1 second
        
        with performance_monitor():
            # Plugin Manager
            start_time = time.perf_counter()
            plugin_manager = PluginManager(self.workspace / "plugins")
            plugin_count = plugin_manager.load_all_plugins()
            plugin_duration = time.perf_counter() - start_time
            
            assert plugin_count > 0
            assert plugin_duration < 0.5  # Baseline: should complete in under 0.5 seconds


class StressTests:
    """Stress testing for refactored components"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for stress tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir)
    
    def test_large_project_handling(self):
        """Test handling of very large projects"""
        large_profile = ProjectProfile(
            name="VeryLargeProject",
            path=Path("/tmp/very_large"),
            technology_stack=TechnologyStack(
                languages={"python", "typescript", "javascript", "java", "go"},
                frameworks={"fastapi", "react", "nextjs", "spring", "gin"},
                databases={"postgresql", "redis", "elasticsearch", "mongodb"},
                tools={"docker", "kubernetes", "pytest", "jest", "gradle"},
                package_managers={"pip", "npm", "yarn", "maven"}
            ),
            architecture_pattern=ArchitecturePattern.MICROSERVICES,
            complexity=ProjectComplexity.ENTERPRISE,
            team_size_estimate=20,
            has_tests=True,
            has_ci_cd=True,
            has_docker=True,
            file_count=10000,  # Very large project
            lines_of_code=1000000,  # 1M LOC
            has_docs=True,
            recommended_subagents=[
                "api-developer", "frontend-developer", "backend-developer",
                "devops-engineer", "database-specialist", "security-auditor",
                "performance-optimizer", "test-engineer", "code-reviewer"
            ],
            integration_requirements=[
                "microservices", "api-gateway", "service-mesh",
                "monitoring", "logging", "tracing"
            ]
        )
        
        # Test context engineering with large project
        engineer = create_context_engineer(self.workspace)
        
        start_time = time.perf_counter()
        context = engineer.engineer_context(large_profile, ContextLevel.COMPREHENSIVE)
        duration = time.perf_counter() - start_time
        
        assert context is not None
        assert duration < 5.0  # Even large projects should complete in reasonable time
        assert len(context.project_context["languages"]) == 5
        assert len(context.project_context["frameworks"]) == 5
        assert context.project_context["team_size_estimate"] == 20
    
    def test_memory_stress(self):
        """Test memory usage under stress"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        generator = create_prp_generator(self.workspace)
        engineer = create_context_engineer(self.workspace)
        
        # Create multiple contexts and PRPs rapidly
        for i in range(20):
            profile = ProjectProfile(
                name=f"StressProject{i}",
                path=Path(f"/tmp/stress{i}"),
                technology_stack=TechnologyStack(
                    languages={"python", "typescript"},
                    frameworks={"fastapi", "react"},
                    databases={"postgresql"},
                    tools={"docker", "pytest"},
                    package_managers={"pip", "npm"}
                ),
                architecture_pattern=ArchitecturePattern.FULLSTACK,
                complexity=ProjectComplexity.MEDIUM,
                team_size_estimate=5,
                has_tests=True,
                has_ci_cd=True,
                has_docker=True,
                file_count=500,
                lines_of_code=25000,
                has_docs=False,
                recommended_subagents=["test-engineer"],
                integration_requirements=["fastapi"]
            )
            
            # Generate context and PRP
            context = engineer.engineer_context(profile, ContextLevel.BASIC)
            prp_context = {
                "project_profile": profile,
                "context_package": context,
                "user_request": f"Stress test {i}"
            }
            prp = asyncio.run(generator.generate_prp(PRPType.FACTORY_ANALYSIS, prp_context))
            
            assert context is not None
            assert prp is not None
            
            # Check memory every 5 iterations
            if i % 5 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - initial_memory
                
                # Memory growth should not be excessive
                # Allow up to 200MB growth for 20 iterations
                assert memory_growth < 200, f"Excessive memory growth: {memory_growth}MB at iteration {i}"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_growth = final_memory - initial_memory
        
        # Final memory check
        assert total_growth < 250, f"Total memory growth too high: {total_growth}MB"


if __name__ == "__main__":
    # Run performance benchmarks
    pytest.main([
        __file__,
        "-v",
        "--benchmark-only",
        "--benchmark-sort=mean",
        "--benchmark-columns=mean,stddev,median,ops,rounds",
        "--benchmark-histogram=histogram"
    ])