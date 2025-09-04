#!/usr/bin/env python3
"""
Test Parallel Execution in SubForge
Demonstra a capacidade de execução paralela real
"""

import asyncio
import sys
from pathlib import Path

# Add subforge to path
sys.path.insert(0, str(Path(__file__).parent))

from subforge.monitoring.metrics_collector import MetricsCollector, PerformanceTracker
from subforge.orchestration.parallel_executor import ParallelExecutor


async def test_parallel_execution():
    """Test real parallel execution capabilities"""

    print("🚀 SubForge Parallel Execution Test")
    print("=" * 50)

    # Initialize components
    project_path = Path.cwd()
    executor = ParallelExecutor(str(project_path))
    metrics = MetricsCollector(str(project_path))
    tracker = PerformanceTracker(metrics)

    print("\n📊 Starting metrics collection...")

    # Test 1: Parallel Analysis
    print("\n🔍 Test 1: Parallel Analysis (5 agents simultaneously)")
    print("-" * 40)

    exec_id = metrics.start_execution(
        "test_analysis", "orchestrator", "parallel_analysis", parallel=True
    )

    analysis_results = await executor.execute_parallel_analysis(
        "Analyze SubForge for optimization opportunities"
    )

    metrics.end_execution(exec_id, "completed")

    print(
        f"✅ Analysis completed with {len(analysis_results['findings'])} agent reports"
    )

    # Test 2: Parallel Research
    print("\n🔬 Test 2: Parallel Research (3 topics × 3 sources = 9 parallel)")
    print("-" * 40)

    exec_id = metrics.start_execution(
        "test_research", "orchestrator", "parallel_research", parallel=True
    )

    research_topics = [
        "Claude Code agent orchestration",
        "parallel execution patterns",
        "context management systems",
    ]

    research_results = await executor.execute_parallel_research(research_topics)

    metrics.end_execution(exec_id, "completed")

    print(
        f"✅ Research completed: {len(research_results['best_practices'])} practices found"
    )

    # Test 3: Smart Implementation
    print("\n⚡ Test 3: Smart Implementation (parallel + sequential)")
    print("-" * 40)

    implementation_tasks = [
        # Parallel group 1 (no dependencies)
        {
            "agent": "@backend-developer",
            "task": "create_api_structure",
            "description": "Create API structure",
            "dependencies": None,
        },
        {
            "agent": "@frontend-developer",
            "task": "create_ui_components",
            "description": "Create UI components",
            "dependencies": None,
        },
        {
            "agent": "@data-scientist",
            "task": "prepare_ml_models",
            "description": "Prepare ML models",
            "dependencies": None,
        },
        # Sequential group (has dependencies)
        {
            "agent": "@test-engineer",
            "task": "write_integration_tests",
            "description": "Write integration tests",
            "dependencies": ["create_api_structure", "create_ui_components"],
        },
        {
            "agent": "@code-reviewer",
            "task": "final_review",
            "description": "Final code review",
            "dependencies": ["write_integration_tests"],
        },
    ]

    exec_id = metrics.start_execution(
        "test_implementation", "orchestrator", "smart_implementation", parallel=True
    )

    implementation_results = await executor.execute_smart_implementation(
        implementation_tasks
    )

    metrics.end_execution(exec_id, "completed")

    print(f"✅ Implementation completed: {len(implementation_results)} tasks executed")
    print(f"   • Parallel tasks: 3")
    print(f"   • Sequential tasks: 2")

    # Generate performance report
    print("\n" + "=" * 50)
    print(metrics.get_performance_report())

    # Analyze bottlenecks
    print("\n🔍 Bottleneck Analysis:")
    print("-" * 40)

    bottlenecks = tracker.analyze_bottlenecks()
    if bottlenecks:
        for bottleneck in bottlenecks:
            print(f"⚠️ {bottleneck['description']}")
            print(f"   → {bottleneck['suggestion']}")
    else:
        print("✅ No bottlenecks detected!")

    # Get optimization suggestions
    print("\n💡 Optimization Suggestions:")
    print("-" * 40)

    suggestions = tracker.suggest_optimizations()
    if suggestions:
        for suggestion in suggestions:
            print(f"• {suggestion}")
    else:
        print("✅ System running optimally!")

    # Save metrics
    final_metrics = metrics.save_metrics()
    print(
        f"\n📁 Metrics saved to: .subforge/metrics/{metrics.current_session['session_id']}.json"
    )

    return final_metrics


def main():
    """Main entry point"""
    print("\n🎯 SubForge Parallel Execution Test Suite")
    print("Testing real parallel capabilities with Task tool")
    print("=" * 60)

    # Run async test
    results = asyncio.run(test_parallel_execution())

    print("\n✨ Test Complete!")
    print(f"Efficiency Score: {results['efficiency_score']:.1f}/100")

    if results["efficiency_score"] >= 80:
        print("🏆 Excellent performance!")
    elif results["efficiency_score"] >= 60:
        print("👍 Good performance with room for improvement")
    else:
        print("⚠️ Performance needs optimization")


if __name__ == "__main__":
    main()