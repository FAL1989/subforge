"""
Metrics Collection System for SubForge
Track performance, efficiency, and success metrics with memory-efficient storage
"""

import asyncio
import aiofiles
import json
import time
import gc
from collections import deque, defaultdict
from functools import lru_cache
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Deque, Optional, Set
from datetime import datetime, timedelta
from asyncio import Queue, Semaphore, Task
import logging

logger = logging.getLogger(__name__)


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
    """Collect and analyze SubForge execution metrics with O(1) lookups and memory limits"""
    
    # Memory management constants
    MAX_EXECUTIONS = 1000  # Maximum executions to keep in memory
    MAX_PARALLEL_GROUPS = 500  # Maximum parallel groups to track
    MAX_SESSION_AGE_HOURS = 24  # Archive sessions older than this
    CLEANUP_INTERVAL_SECONDS = 3600  # Run cleanup every hour
    
    # Async I/O performance constants
    WRITE_BUFFER_SIZE = 100  # Buffer metrics before flushing
    WRITE_FLUSH_INTERVAL = 10  # Seconds between automatic flushes
    MAX_CONCURRENT_WRITES = 5  # Maximum concurrent file write operations
    WRITE_RETRY_ATTEMPTS = 3  # Number of retry attempts for failed writes

    def __init__(self, project_path: str, max_executions: int = None, max_groups: int = None):
        self.project_path = Path(project_path)
        self.metrics_dir = self.project_path / ".subforge" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure memory limits
        self.max_executions = max_executions or self.MAX_EXECUTIONS
        self.max_groups = max_groups or self.MAX_PARALLEL_GROUPS
        
        # Async write management
        self.write_queue: Queue[Tuple[str, Dict[str, Any]]] = Queue(maxsize=self.WRITE_BUFFER_SIZE * 2)
        self.write_semaphore = Semaphore(self.MAX_CONCURRENT_WRITES)
        self.pending_metrics: Dict[str, Any] = {}  # Buffer for coalescing metrics
        self.write_task: Optional[Task] = None
        self.last_flush_time = time.time()
        self.write_errors: Deque[Dict[str, Any]] = deque(maxlen=50)  # Track write errors
        
        # Use deques for bounded collections
        self.current_session = {
            "session_id": f"session_{int(time.time())}",
            "start_time": time.time(),
            "executions": deque(maxlen=self.max_executions),
            "parallel_groups": deque(maxlen=self.max_groups),
            "token_total": 0,
        }
        
        # O(1) lookup indexes
        self.execution_index: Dict[str, Dict[str, Any]] = {}  # execution_id -> execution data
        self.agent_executions_index: Dict[str, Set[str]] = defaultdict(set)  # agent -> set of execution_ids
        self.task_execution_index: Dict[str, str] = {}  # task_id -> execution_id
        self.status_index: Dict[str, Set[str]] = defaultdict(set)  # status -> set of execution_ids
        self.parallel_execution_index: Set[str] = set()  # Set of parallel execution_ids
        self.agent_duration_cache: Dict[str, float] = {}  # agent -> total duration (cached)
        
        # Archive management
        self.archive_dir = self.metrics_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        self.last_cleanup_time = time.time()
        self.archived_sessions = 0
        
        # Session history with bounded size
        self.session_history: Deque[Dict] = deque(maxlen=100)
        
        # Initialize caches
        self._metrics_cache = None
        self._efficiency_cache = None
        
        # Start background write processor
        self._start_write_processor()

    def start_execution(
        self, task_id: str, agent: str, task_type: str, parallel: bool = False
    ) -> str:
        """Start tracking an execution with automatic cleanup"""
        # Periodic cleanup check
        current_time = time.time()
        if current_time - self.last_cleanup_time > self.CLEANUP_INTERVAL_SECONDS:
            self._perform_cleanup()
            self.last_cleanup_time = current_time
        
        execution_id = f"{task_id}_{int(current_time)}"
        
        # Create lightweight execution record
        execution = {
            "id": execution_id,
            "task_id": task_id[:50] if len(task_id) > 50 else task_id,  # Limit ID size
            "agent": agent[:30] if len(agent) > 30 else agent,  # Limit agent name size
            "task_type": task_type[:30] if len(task_type) > 30 else task_type,
            "start_time": current_time,
            "parallel": parallel,
            "status": "running",
        }
        
        # Deque automatically removes oldest when maxlen is reached
        self.current_session["executions"].append(execution)
        
        # Update O(1) indexes
        self.execution_index[execution_id] = execution
        self.agent_executions_index[agent].add(execution_id)
        self.task_execution_index[task_id] = execution_id
        self.status_index["running"].add(execution_id)
        if parallel:
            self.parallel_execution_index.add(execution_id)
        
        # Clear caches when data changes
        self._clear_caches()
        
        return execution_id

    def end_execution(
        self, execution_id: str, status: str = "completed", errors: List[str] = None
    ):
        """End tracking an execution using O(1) lookup"""
        # O(1) lookup from index
        execution = self.execution_index.get(execution_id)
        if not execution:
            # Fallback to linear search for compatibility
            for exec in self.current_session["executions"]:
                if exec["id"] == execution_id:
                    execution = exec
                    break
            if not execution:
                return
        
        # Update execution data
        execution["end_time"] = time.time()
        execution["duration"] = execution["end_time"] - execution["start_time"]
        execution["status"] = status
        if errors:
            execution["errors"] = errors
        
        # Update status index
        self.status_index["running"].discard(execution_id)
        self.status_index[status].add(execution_id)
        
        # Update agent duration cache if completed
        if status == "completed":
            agent = execution.get("agent", "unknown")
            if agent in self.agent_duration_cache:
                self.agent_duration_cache[agent] += execution["duration"]
            else:
                self.agent_duration_cache[agent] = execution["duration"]
        
        # Clear caches when data changes
        self._clear_caches()

    def track_parallel_group(self, tasks: List[str], duration: float):
        """Track a parallel execution group with memory limits"""
        # Limit the number of tasks stored to prevent memory issues
        tasks_to_store = tasks[:20] if len(tasks) > 20 else tasks  # Max 20 tasks per group
        
        group_data = {
            "tasks": tasks_to_store,
            "task_count": len(tasks),  # Store total count separately
            "duration": round(duration, 2),  # Round to save memory
            "speedup": round(len(tasks) / max(duration, 0.1), 2),
            "timestamp": time.time(),
        }
        
        # Deque automatically removes oldest when maxlen is reached
        self.current_session["parallel_groups"].append(group_data)

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate session metrics using O(1) indexes and caching"""
        # Check if we have a cached result
        if hasattr(self, '_metrics_cache') and self._metrics_cache is not None:
            return self._metrics_cache
        # Use indexes for O(1) performance
        total_executions = len(self.execution_index)
        
        if total_executions == 0:
            return {"message": "No executions to analyze"}
        
        # O(1) counts using indexes
        parallel_count = len(self.parallel_execution_index)
        sequential_count = total_executions - parallel_count
        
        # Use cached durations for O(1) calculation
        total_duration = sum(self.agent_duration_cache.values())

        # Calculate efficiency from bounded parallel groups
        parallel_groups = list(self.current_session["parallel_groups"])
        if parallel_groups:
            # Only process last 100 groups for efficiency calculation
            recent_groups = parallel_groups[-100:] if len(parallel_groups) > 100 else parallel_groups
            avg_speedup = sum(g["speedup"] for g in recent_groups) / len(recent_groups)
        else:
            avg_speedup = 1.0
        
        # Agent utilization using O(1) cached data
        agent_times = dict(self.agent_duration_cache)  # Copy cached durations

        # Success rate using O(1) index lookup
        completed = len(self.status_index.get("completed", set()))
        success_rate = (completed / total_executions) * 100 if total_executions else 0

        metrics = {
            "session_id": self.current_session["session_id"],
            "total_executions": total_executions,
            "parallel_executions": parallel_count,
            "sequential_executions": sequential_count,
            "total_duration": round(total_duration, 2),
            "average_speedup": round(avg_speedup, 2),
            "parallelization_ratio": round(
                parallel_count / total_executions if total_executions else 0, 3
            ),
            "success_rate": round(success_rate, 1),
            "agent_utilization": {k: round(v, 2) for k, v in agent_times.items()},
            "token_usage": self.current_session.get("token_total", 0),
            "efficiency_score": round(self._calculate_efficiency_score(), 1),
            "memory_status": self._get_memory_status(),
        }
        
        # Cache the result
        self._metrics_cache = metrics
        return metrics

    def _calculate_efficiency_score(self) -> float:
        """Calculate overall efficiency score using O(1) indexes"""
        # Check for cached result
        if hasattr(self, '_efficiency_cache') and self._efficiency_cache is not None:
            return self._efficiency_cache
        factors = []

        # Parallelization factor using indexes
        total_executions = len(self.execution_index)
        if total_executions > 0:
            parallel_count = len(self.parallel_execution_index)
            parallel_ratio = parallel_count / total_executions
            factors.append(parallel_ratio * 30)  # 30 points max

        # Success rate factor using indexes
        completed = len(self.status_index.get("completed", set()))
        if total_executions > 0:
            success_rate = completed / total_executions
            factors.append(success_rate * 40)  # 40 points max

        # Speedup factor
        parallel_groups = list(self.current_session["parallel_groups"])
        if parallel_groups:
            recent_groups = parallel_groups[-100:] if len(parallel_groups) > 100 else parallel_groups
            avg_speedup = sum(g["speedup"] for g in recent_groups) / len(recent_groups)
            speedup_score = min(avg_speedup / 4, 1.0)  # Cap at 4x speedup
            factors.append(speedup_score * 30)  # 30 points max

        efficiency = sum(factors) if factors else 0
        # Cache the result
        self._efficiency_cache = efficiency
        return efficiency

    async def save_metrics(self):
        """Save metrics to file with automatic archival using async I/O"""
        # Clear cache to get fresh metrics
        self._clear_caches()
        metrics = self.calculate_metrics()
        
        # Add to session history
        self.session_history.append({
            "session_id": self.current_session["session_id"],
            "timestamp": time.time(),
            "summary": {
                "total_executions": metrics.get("total_executions", 0),
                "efficiency_score": metrics.get("efficiency_score", 0),
                "success_rate": metrics.get("success_rate", 0),
            }
        })
        
        # Save session metrics asynchronously
        session_file = self.metrics_dir / f"{self.current_session['session_id']}.json"
        essential_metrics = {k: v for k, v in metrics.items() 
                           if k != "agent_utilization" or len(str(v)) < 1000}
        
        await self._async_write_file(session_file, essential_metrics)
        
        # Update aggregate metrics asynchronously
        await self._async_update_aggregate_metrics(metrics)
        
        # Archive old sessions if needed
        await self._async_archive_old_sessions()
        
        return metrics

    async def _async_update_aggregate_metrics(self, session_metrics: Dict[str, Any]):
        """Update aggregate metrics file using async I/O"""
        aggregate_file = self.metrics_dir / "aggregate_metrics.json"

        if aggregate_file.exists():
            async with aiofiles.open(aggregate_file, "r") as f:
                content = await f.read()
                aggregate = json.loads(content)
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

        # Save updated aggregate asynchronously
        await self._async_write_file(aggregate_file, aggregate)

    def get_performance_report(self) -> str:
        """Generate performance report with memory status"""
        metrics = self.calculate_metrics()
        memory_status = metrics.get("memory_status", {})
        
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

💾 Memory Status:
• Executions in Memory: {memory_status.get('executions_count', 0)}/{memory_status.get('max_executions', 0)}
• Archived Sessions: {memory_status.get('archived_sessions', 0)}
• Memory Health: {memory_status.get('health', 'unknown')}

👥 Agent Utilization (Top 10):
"""
        
        # Show only top 10 agents to limit report size
        agent_times = metrics.get("agent_utilization", {})
        sorted_agents = sorted(agent_times.items(), key=lambda x: x[1], reverse=True)[:10]
        for agent, time_used in sorted_agents:
            report += f"• {agent}: {time_used:.2f}s\n"
        
        if len(agent_times) > 10:
            report += f"  ... and {len(agent_times) - 10} more agents\n"
        
        return report
    
    def _perform_cleanup(self):
        """Perform periodic cleanup of old data"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (self.MAX_SESSION_AGE_HOURS * 3600)
            
            # Clean old execution records (keep only recent ones)
            executions = list(self.current_session["executions"])
            if executions:
                # Remove completed executions older than 1 hour
                one_hour_ago = current_time - 3600
                recent_executions = [
                    e for e in executions 
                    if e.get("status") == "running" or e.get("start_time", 0) > one_hour_ago
                ]
                
                # If we removed items, update the deque and indexes
                if len(recent_executions) < len(executions):
                    # Clean up indexes for removed executions
                    removed_executions = [e for e in executions if e not in recent_executions]
                    for exec in removed_executions:
                        exec_id = exec.get("id")
                        if exec_id:
                            # Remove from all indexes
                            self.execution_index.pop(exec_id, None)
                            agent = exec.get("agent", "unknown")
                            self.agent_executions_index[agent].discard(exec_id)
                            task_id = exec.get("task_id")
                            if task_id in self.task_execution_index:
                                del self.task_execution_index[task_id]
                            status = exec.get("status", "unknown")
                            self.status_index[status].discard(exec_id)
                            self.parallel_execution_index.discard(exec_id)
                    
                    self.current_session["executions"].clear()
                    self.current_session["executions"].extend(recent_executions[-self.max_executions:])
                    
                    # Clear caches after cleanup
                    self._clear_caches()
            
            # Clean old session files
            for session_file in self.metrics_dir.glob("session_*.json"):
                try:
                    if session_file.stat().st_mtime < cutoff_time:
                        session_file.unlink()
                except Exception:
                    pass
            
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            # Silently handle cleanup errors to not disrupt operations
            pass
    
    async def _async_archive_old_sessions(self):
        """Archive old session data to reduce memory usage using async I/O"""
        try:
            current_time = time.time()
            archive_threshold = current_time - (12 * 3600)  # Archive sessions older than 12 hours
            
            # Find old session files
            sessions_to_archive = []
            for session_file in self.metrics_dir.glob("session_*.json"):
                try:
                    if session_file.stat().st_mtime < archive_threshold:
                        sessions_to_archive.append(session_file)
                except Exception:
                    continue
            
            if len(sessions_to_archive) >= 10:  # Archive in batches
                # Create archive
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_file = self.archive_dir / f"metrics_archive_{timestamp}.json"
                
                # Read all files to archive in parallel
                read_tasks = []
                for session_file in sessions_to_archive[:10]:
                    read_tasks.append(self._async_read_and_delete_file(session_file))
                
                # Wait for all reads to complete
                archived_data = await asyncio.gather(*read_tasks, return_exceptions=True)
                
                # Filter out errors and None values
                archived_data = [data for data in archived_data if isinstance(data, dict)]
                
                if archived_data:
                    archive_content = {
                        "archived_at": current_time,
                        "sessions": archived_data
                    }
                    await self._async_write_file(archive_file, archive_content)
                    self.archived_sessions += len(archived_data)
        
        except Exception as e:
            logger.error(f"Error during session archival: {e}")
    
    def _get_memory_status(self) -> Dict[str, Any]:
        """Get current memory usage status"""
        executions_count = len(self.current_session["executions"])
        groups_count = len(self.current_session["parallel_groups"])
        
        # Calculate memory health
        usage_ratio = executions_count / self.max_executions
        if usage_ratio < 0.7:
            health = "healthy"
        elif usage_ratio < 0.9:
            health = "moderate"
        else:
            health = "near_limit"
        
        return {
            "executions_count": executions_count,
            "max_executions": self.max_executions,
            "parallel_groups_count": groups_count,
            "max_groups": self.max_groups,
            "archived_sessions": self.archived_sessions,
            "session_history_count": len(self.session_history),
            "health": health
        }
    
    def _clear_caches(self):
        """Clear internal caches when data changes"""
        self._metrics_cache = None
        self._efficiency_cache = None
    
    def get_execution_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """O(1) lookup for execution by ID"""
        return self.execution_index.get(execution_id)
    
    def get_executions_by_agent(self, agent: str) -> List[Dict[str, Any]]:
        """O(1) lookup for all executions by an agent"""
        execution_ids = self.agent_executions_index.get(agent, set())
        return [self.execution_index[eid] for eid in execution_ids if eid in self.execution_index]
    
    def get_executions_by_status(self, status: str) -> List[Dict[str, Any]]:
        """O(1) lookup for all executions with a status"""
        execution_ids = self.status_index.get(status, set())
        return [self.execution_index[eid] for eid in execution_ids if eid in self.execution_index]
    
    def get_execution_by_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """O(1) lookup for execution by task ID"""
        execution_id = self.task_execution_index.get(task_id)
        if execution_id:
            return self.execution_index.get(execution_id)
        return None
    
    async def _async_write_file(self, file_path: Path, data: Dict[str, Any], retry_attempts: int = None):
        """Write file asynchronously with retry logic"""
        retry_attempts = retry_attempts or self.WRITE_RETRY_ATTEMPTS
        
        for attempt in range(retry_attempts):
            try:
                async with self.write_semaphore:
                    async with aiofiles.open(file_path, 'w') as f:
                        await f.write(json.dumps(data, indent=2))
                return  # Success
            except Exception as e:
                if attempt == retry_attempts - 1:
                    logger.error(f"Failed to write {file_path} after {retry_attempts} attempts: {e}")
                    self.write_errors.append({
                        "timestamp": time.time(),
                        "file": str(file_path),
                        "error": str(e)
                    })
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
    
    async def _async_read_and_delete_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read and delete a file asynchronously"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = json.loads(content)
            
            # Delete the file after successful read
            file_path.unlink()
            return data
        except Exception as e:
            logger.error(f"Failed to read/delete {file_path}: {e}")
            return None
    
    def _start_write_processor(self):
        """Start background task for periodic metric flushing"""
        async def write_processor():
            """Background task that periodically saves metrics"""
            while True:
                try:
                    await asyncio.sleep(self.WRITE_FLUSH_INTERVAL)
                    
                    # Auto-save metrics if we have pending data
                    if len(self.execution_index) > 0:
                        current_time = time.time()
                        if current_time - self.last_flush_time > self.WRITE_FLUSH_INTERVAL:
                            await self.save_metrics()
                            self.last_flush_time = current_time
                            
                except Exception as e:
                    logger.error(f"Error in metrics write processor: {e}")
        
        # Start the write processor task
        self.write_task = asyncio.create_task(write_processor())
    
    async def shutdown(self):
        """Graceful shutdown - save final metrics and clean up"""
        try:
            # Save final metrics
            await self.save_metrics()
            
            # Cancel the write processor task
            if self.write_task and not self.write_task.done():
                self.write_task.cancel()
                try:
                    await self.write_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("MetricsCollector shutdown complete")
        except Exception as e:
            logger.error(f"Error during metrics collector shutdown: {e}")
    
    def save_metrics_sync(self):
        """Synchronous wrapper for save_metrics for backwards compatibility"""
        return asyncio.run(self.save_metrics())
    
    def _update_aggregate_metrics(self, session_metrics: Dict[str, Any]):
        """Legacy synchronous method for backwards compatibility"""
        asyncio.run(self._async_update_aggregate_metrics(session_metrics))
    
    def _archive_old_sessions(self):
        """Legacy synchronous method for backwards compatibility"""
        asyncio.run(self._async_archive_old_sessions())


class PerformanceTracker:
    """Track and optimize SubForge performance with O(1) lookups"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector
        self.optimizations = []
        self._bottleneck_cache = None
        self._cache_time = 0

    def analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks with caching"""
        # Check for cached result
        current_time = time.time()
        if hasattr(self, '_bottleneck_cache') and hasattr(self, '_cache_time'):
            if current_time - self._cache_time < 60:  # Cache for 60 seconds
                return self._bottleneck_cache
        
        # Use cached metrics for O(1) access
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

        # Cache the result
        self._bottleneck_cache = bottlenecks
        self._cache_time = current_time
        return bottlenecks

    def suggest_optimizations(self) -> List[str]:
        """Suggest performance optimizations using cached analysis"""
        # Use cached bottleneck analysis
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