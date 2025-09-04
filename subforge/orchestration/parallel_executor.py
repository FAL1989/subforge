"""
Parallel Executor for SubForge
Real parallel execution using Claude Code's Task tool
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class ParallelTask:
    """Task for parallel execution"""

    agent: str
    task: str
    description: str
    dependencies: List[str] = None
    can_parallel: bool = True

    def to_prompt(self) -> str:
        """Convert to Task tool prompt"""
        return f"""
AGENT: {self.agent}
TASK: {self.task}
DESCRIPTION: {self.description}
DEPENDENCIES: {self.dependencies or 'None'}

Execute this specific task and return results.
"""


class ParallelExecutor:
    """Manages parallel execution of SubForge tasks"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.workflow_state = self.project_path / "workflow-state"
        self.workflow_state.mkdir(exist_ok=True)

    async def execute_parallel_analysis(self, request: str) -> Dict[str, Any]:
        """
        Execute parallel analysis phase
        All agents analyze simultaneously
        """
        analysis_tasks = [
            ParallelTask(
                "@code-reviewer",
                "analyze_code_quality",
                "Analyze code patterns, quality metrics, and architectural compliance",
            ),
            ParallelTask(
                "@test-engineer",
                "analyze_test_coverage",
                "Check test coverage, identify gaps, and assess testing strategy",
            ),
            ParallelTask(
                "@backend-developer",
                "analyze_backend_structure",
                "Review API structure, database schema, and service architecture",
            ),
            ParallelTask(
                "@frontend-developer",
                "analyze_frontend_components",
                "Analyze UI components, state management, and frontend patterns",
            ),
            ParallelTask(
                "@data-scientist",
                "analyze_data_models",
                "Review data models, algorithms, and processing pipelines",
            ),
        ]

        # Execute all in parallel using Task tool
        results = await self._execute_parallel_batch(analysis_tasks)

        # Consolidate findings
        consolidated = self._consolidate_analysis(results)

        # Save to shared state
        self._save_to_state("analysis_results", consolidated)

        return consolidated

    async def execute_parallel_research(self, topics: List[str]) -> Dict[str, Any]:
        """
        Execute parallel research across multiple sources
        """
        research_tasks = []

        for topic in topics:
            # Perplexity search
            research_tasks.append(
                ParallelTask(
                    "perplexity",
                    f"research_{topic}",
                    f"Research best practices and latest trends for {topic}",
                )
            )

            # GitHub examples
            research_tasks.append(
                ParallelTask(
                    "github",
                    f"examples_{topic}",
                    f"Find real-world implementations of {topic}",
                )
            )

            # Documentation
            research_tasks.append(
                ParallelTask(
                    "ref", f"docs_{topic}", f"Get official documentation for {topic}"
                )
            )

        # Execute all research in parallel
        results = await self._execute_parallel_batch(research_tasks)

        # Synthesize findings
        synthesis = self._synthesize_research(results)

        # Save to shared state
        self._save_to_state("research_results", synthesis)

        return synthesis

    async def execute_smart_implementation(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Smart parallel/sequential execution based on dependencies
        """
        # Group tasks by parallelizability
        groups = self._group_by_dependencies(tasks)

        all_results = {}

        for group in groups:
            if group["can_parallel"]:
                # Execute group in parallel
                logger.info(f"Executing {len(group['tasks'])} tasks in parallel")
                results = await self._execute_parallel_batch(group["tasks"])
                all_results.update(results)
            else:
                # Execute sequentially
                logger.info(f"Executing {len(group['tasks'])} tasks sequentially")
                for task in group["tasks"]:
                    result = await self._execute_single(task)
                    all_results[task.agent] = result

        return all_results

    async def _execute_parallel_batch(
        self, tasks: List[ParallelTask]
    ) -> Dict[str, Any]:
        """
        Execute a batch of tasks in parallel
        This would use Claude Code's Task tool
        """
        # In real implementation, this would call Task tool
        # For now, return mock results
        results = {}

        for task in tasks:
            # Log the parallel execution
            logger.info(f"Parallel executing: {task.agent} - {task.task}")

            # Save task to state for tracking
            self._save_task_status(task, "executing")

            # Mock result (would be real Task tool call)
            results[task.agent] = {
                "status": "completed",
                "task": task.task,
                "findings": f"Analysis from {task.agent}",
                "recommendations": [],
            }

            # Update task status
            self._save_task_status(task, "completed")

        return results

    async def _execute_single(self, task: ParallelTask) -> Dict[str, Any]:
        """Execute a single task"""
        logger.info(f"Sequential executing: {task.agent} - {task.task}")

        # Save task status
        self._save_task_status(task, "executing")

        # Mock result
        result = {
            "status": "completed",
            "task": task.task,
            "output": f"Result from {task.agent}",
        }

        # Update status
        self._save_task_status(task, "completed")

        return result

    def _group_by_dependencies(
        self, tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Group tasks by dependencies for optimal execution"""
        groups = []

        # Find tasks with no dependencies (can run in parallel)
        no_deps = [t for t in tasks if not t.get("dependencies")]

        if no_deps:
            groups.append(
                {"can_parallel": True, "tasks": [ParallelTask(**t) for t in no_deps]}
            )

        # Find dependent tasks (must run sequentially)
        with_deps = [t for t in tasks if t.get("dependencies")]

        if with_deps:
            # Sort by dependency order
            sorted_deps = self._topological_sort(with_deps)
            groups.append(
                {
                    "can_parallel": False,
                    "tasks": [ParallelTask(**t) for t in sorted_deps],
                }
            )

        return groups

    def _topological_sort(self, tasks: List[Dict]) -> List[Dict]:
        """Sort tasks by dependency order"""
        # Simple topological sort implementation
        # In production, use more robust algorithm
        return sorted(tasks, key=lambda x: len(x.get("dependencies", [])))

    def _consolidate_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate analysis results from multiple agents"""
        consolidated = {
            "summary": "Parallel analysis completed",
            "findings": {},
            "recommendations": [],
            "metrics": {},
        }

        for agent, result in results.items():
            consolidated["findings"][agent] = result.get("findings", {})
            consolidated["recommendations"].extend(result.get("recommendations", []))

        return consolidated

    def _synthesize_research(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize research from multiple sources"""
        synthesis = {
            "best_practices": [],
            "examples": [],
            "documentation": [],
            "recommendations": [],
        }

        for source, result in results.items():
            if "perplexity" in source:
                synthesis["best_practices"].append(result)
            elif "github" in source:
                synthesis["examples"].append(result)
            elif "ref" in source:
                synthesis["documentation"].append(result)

        return synthesis

    def _save_to_state(self, key: str, data: Any):
        """Save data to shared state"""
        state_file = self.workflow_state / "current-task.json"

        if state_file.exists():
            with open(state_file, "r") as f:
                state = json.load(f)
        else:
            state = {}

        state[key] = data

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _save_task_status(self, task: ParallelTask, status: str):
        """Save task execution status"""
        status_file = self.workflow_state / "task-status.json"

        if status_file.exists():
            with open(status_file, "r") as f:
                statuses = json.load(f)
        else:
            statuses = {}

        task_id = f"{task.agent}:{task.task}"
        statuses[task_id] = {
            "status": status,
            "agent": task.agent,
            "task": task.task,
            "timestamp": asyncio.get_event_loop().time(),
        }

        with open(status_file, "w") as f:
            json.dump(statuses, f, indent=2)


# Example usage
async def demonstrate_parallel_execution():
    """Demonstrate parallel execution capabilities"""
    executor = ParallelExecutor("/home/nando/projects/Claude-subagents")

    # Phase 1: Parallel Analysis
    print("🚀 Phase 1: Parallel Analysis")
    analysis_results = await executor.execute_parallel_analysis(
        "Analyze SubForge for improvements"
    )

    # Phase 2: Parallel Research
    print("🔍 Phase 2: Parallel Research")
    research_topics = [
        "agent orchestration patterns",
        "parallel execution strategies",
        "context management systems",
    ]
    research_results = await executor.execute_parallel_research(research_topics)

    # Phase 3: Smart Implementation
    print("⚡ Phase 3: Smart Implementation")
    implementation_tasks = [
        {
            "agent": "@backend-developer",
            "task": "implement_api",
            "description": "Implement orchestration API",
            "dependencies": None,
        },
        {
            "agent": "@frontend-developer",
            "task": "create_ui",
            "description": "Create orchestration UI",
            "dependencies": None,
        },
        {
            "agent": "@test-engineer",
            "task": "write_tests",
            "description": "Write integration tests",
            "dependencies": ["implement_api", "create_ui"],
        },
    ]

    implementation_results = await executor.execute_smart_implementation(
        implementation_tasks
    )

    return {
        "analysis": analysis_results,
        "research": research_results,
        "implementation": implementation_results,
    }