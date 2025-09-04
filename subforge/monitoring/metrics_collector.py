"""
Metrics Collection System for SubForge
Track performance, efficiency, and success metrics
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ExecutionMetrics:
    """Metrics for a single execution"""

    task_id: str
    agent: str
    task_type: str
    start_time: float
    end_time: float
    duration: float
    status: str
    parallel: bool
    token_usage: int = 0
    errors: List[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class MetricsCollector:
    """Collect and analyze SubForge execution metrics"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.metrics_dir = self.project_path / ".subforge" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self.current_session = {
            "session_id": f"session_{int(time.time())}",
            "start_time": time.time(),
            "executions": [],
            "parallel_groups": [],
            "token_total": 0,
        }

    def start_execution(
        self, task_id: str, agent: str, task_type: str, parallel: bool = False
    ) -> str:
        """Start tracking an execution"""
        execution_id = f"{task_id}_{int(time.time())}"

        self.current_session["executions"].append(
            {
                "id": execution_id,
                "task_id": task_id,
                "agent": agent,
                "task_type": task_type,
                "start_time": time.time(),
                "parallel": parallel,
                "status": "running",
            }
        )

        return execution_id

    def end_execution(
        self, execution_id: str, status: str = "completed", errors: List[str] = None
    ):
        """End tracking an execution"""
        for execution in self.current_session["executions"]:
            if execution["id"] == execution_id:
                execution["end_time"] = time.time()
                execution["duration"] = execution["end_time"] - execution["start_time"]
                execution["status"] = status
                if errors:
                    execution["errors"] = errors
                break

    def track_parallel_group(self, tasks: List[str], duration: float):
        """Track a parallel execution group"""
        self.current_session["parallel_groups"].append(
            {
                "tasks": tasks,
                "duration": duration,
                "speedup": len(tasks) / max(duration, 0.1),  # Theoretical speedup
                "timestamp": time.time(),
            }
        )

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate session metrics"""
        executions = self.current_session["executions"]

        if not executions:
            return {"message": "No executions to analyze"}

        # Calculate basic metrics
        total_duration = sum(e.get("duration", 0) for e in executions)
        parallel_executions = [e for e in executions if e.get("parallel")]
        sequential_executions = [e for e in executions if not e.get("parallel")]

        # Calculate efficiency
        if self.current_session["parallel_groups"]:
            avg_speedup = sum(
                g["speedup"] for g in self.current_session["parallel_groups"]
            ) / len(self.current_session["parallel_groups"])
        else:
            avg_speedup = 1.0

        # Agent utilization
        agent_times = {}
        for execution in executions:
            agent = execution.get("agent", "unknown")
            if agent not in agent_times:
                agent_times[agent] = 0
            agent_times[agent] += execution.get("duration", 0)

        # Success rate
        completed = len([e for e in executions if e.get("status") == "completed"])
        success_rate = (completed / len(executions)) * 100 if executions else 0

        metrics = {
            "session_id": self.current_session["session_id"],
            "total_executions": len(executions),
            "parallel_executions": len(parallel_executions),
            "sequential_executions": len(sequential_executions),
            "total_duration": total_duration,
            "average_speedup": avg_speedup,
            "parallelization_ratio": (
                len(parallel_executions) / len(executions) if executions else 0
            ),
            "success_rate": success_rate,
            "agent_utilization": agent_times,
            "token_usage": self.current_session.get("token_total", 0),
            "efficiency_score": self._calculate_efficiency_score(),
        }

        return metrics

    def _calculate_efficiency_score(self) -> float:
        """Calculate overall efficiency score (0-100)"""
        factors = []

        # Parallelization factor
        executions = self.current_session["executions"]
        if executions:
            parallel_ratio = len([e for e in executions if e.get("parallel")]) / len(
                executions
            )
            factors.append(parallel_ratio * 30)  # 30 points max

        # Success rate factor
        completed = len([e for e in executions if e.get("status") == "completed"])
        if executions:
            success_rate = completed / len(executions)
            factors.append(success_rate * 40)  # 40 points max

        # Speedup factor
        if self.current_session["parallel_groups"]:
            avg_speedup = sum(
                g["speedup"] for g in self.current_session["parallel_groups"]
            ) / len(self.current_session["parallel_groups"])
            speedup_score = min(avg_speedup / 4, 1.0)  # Cap at 4x speedup
            factors.append(speedup_score * 30)  # 30 points max

        return sum(factors) if factors else 0

    def save_metrics(self):
        """Save metrics to file"""
        metrics = self.calculate_metrics()

        # Save session metrics
        session_file = self.metrics_dir / f"{self.current_session['session_id']}.json"
        with open(session_file, "w") as f:
            json.dump(metrics, f, indent=2)

        # Update aggregate metrics
        self._update_aggregate_metrics(metrics)

        return metrics

    def _update_aggregate_metrics(self, session_metrics: Dict[str, Any]):
        """Update aggregate metrics file"""
        aggregate_file = self.metrics_dir / "aggregate_metrics.json"

        if aggregate_file.exists():
            with open(aggregate_file, "r") as f:
                aggregate = json.load(f)
        else:
            aggregate = {
                "total_sessions": 0,
                "total_executions": 0,
                "average_efficiency": 0,
                "best_efficiency": 0,
                "total_token_usage": 0,
            }

        # Update aggregate
        aggregate["total_sessions"] += 1
        aggregate["total_executions"] += session_metrics["total_executions"]
        aggregate["total_token_usage"] += session_metrics["token_usage"]

        # Update efficiency metrics
        current_efficiency = session_metrics["efficiency_score"]
        aggregate["average_efficiency"] = (
            aggregate["average_efficiency"] * (aggregate["total_sessions"] - 1)
            + current_efficiency
        ) / aggregate["total_sessions"]
        aggregate["best_efficiency"] = max(
            aggregate["best_efficiency"], current_efficiency
        )

        # Save updated aggregate
        with open(aggregate_file, "w") as f:
            json.dump(aggregate, f, indent=2)

    def get_performance_report(self) -> str:
        """Generate performance report"""
        metrics = self.calculate_metrics()

        report = f"""
📊 SubForge Performance Report
{'=' * 40}

Session: {metrics['session_id']}
Total Executions: {metrics['total_executions']}
├── Parallel: {metrics['parallel_executions']}
└── Sequential: {metrics['sequential_executions']}

⚡ Performance Metrics:
• Parallelization Ratio: {metrics['parallelization_ratio']:.1%}
• Average Speedup: {metrics['average_speedup']:.2f}x
• Success Rate: {metrics['success_rate']:.1f}%
• Efficiency Score: {metrics['efficiency_score']:.1f}/100

⏱️ Time Analysis:
• Total Duration: {metrics['total_duration']:.2f}s
• Avg per Task: {metrics['total_duration']/max(metrics['total_executions'], 1):.2f}s

👥 Agent Utilization:
"""

        for agent, time_used in metrics["agent_utilization"].items():
            report += f"• {agent}: {time_used:.2f}s\n"

        return report


class PerformanceTracker:
    """Track and optimize SubForge performance"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector
        self.optimizations = []

    def analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        metrics = self.collector.calculate_metrics()
        bottlenecks = []

        # Check parallelization ratio
        if metrics["parallelization_ratio"] < 0.3:
            bottlenecks.append(
                {
                    "type": "low_parallelization",
                    "severity": "high",
                    "description": "Less than 30% of tasks running in parallel",
                    "suggestion": "Review task dependencies and increase parallel execution",
                }
            )

        # Check success rate
        if metrics["success_rate"] < 90:
            bottlenecks.append(
                {
                    "type": "high_failure_rate",
                    "severity": "critical",
                    "description": f"Success rate only {metrics['success_rate']:.1f}%",
                    "suggestion": "Review error logs and fix failing tasks",
                }
            )

        # Check speedup
        if metrics["average_speedup"] < 1.5 and metrics["parallel_executions"] > 0:
            bottlenecks.append(
                {
                    "type": "poor_speedup",
                    "severity": "medium",
                    "description": "Parallel execution not providing expected speedup",
                    "suggestion": "Optimize task granularity and reduce overhead",
                }
            )

        return bottlenecks

    def suggest_optimizations(self) -> List[str]:
        """Suggest performance optimizations"""
        bottlenecks = self.analyze_bottlenecks()
        suggestions = []

        for bottleneck in bottlenecks:
            suggestions.append(
                f"[{bottleneck['severity'].upper()}] {bottleneck['suggestion']}"
            )

        # Additional general suggestions
        metrics = self.collector.calculate_metrics()

        if metrics["efficiency_score"] < 70:
            suggestions.append(
                "Consider restructuring workflow for better parallelization"
            )

        if metrics["token_usage"] > 100000:
            suggestions.append(
                "High token usage detected - consider caching research results"
            )

        return suggestions