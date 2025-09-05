#!/usr/bin/env python3
"""
SubForge Workflow Monitor
Real-time monitoring and tracking for SubForge workflows
"""

import asyncio
import aiofiles
import json
import time
import gc
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Deque, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from asyncio import Queue, Task

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class AgentStatus(Enum):
    """Individual agent execution status"""
    IDLE = "idle"
    BUSY = "busy"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentExecution:
    """Tracks individual agent execution"""
    agent_name: str
    task_id: str
    start_time: float
    end_time: Optional[float]
    status: AgentStatus
    task_description: str
    output: Dict[str, Any]
    error_message: Optional[str]
    
    def duration(self) -> Optional[float]:
        """Calculate execution duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def is_active(self) -> bool:
        """Check if agent is currently executing"""
        return self.status in [AgentStatus.BUSY]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            **asdict(self),
            "status": self.status.value,
            "duration": self.duration()
        }


@dataclass
class WorkflowExecution:
    """Tracks complete workflow execution with O(1) lookups"""
    workflow_id: str
    project_path: str
    user_request: str
    start_time: float
    end_time: Optional[float]
    status: WorkflowStatus
    current_phase: str
    agent_executions: List[AgentExecution]
    parallel_groups: List[List[str]]  # Groups of agents executing in parallel
    # O(1) lookup indexes
    _agent_execution_index: Dict[Tuple[str, str], AgentExecution] = field(default_factory=dict, repr=False)
    _agent_task_index: Dict[str, List[str]] = field(default_factory=dict, repr=False)
    
    def duration(self) -> Optional[float]:
        """Calculate total workflow duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def get_active_agents(self) -> Set[str]:
        """Get list of currently active agents with caching"""
        # Use internal cache
        if not hasattr(self, '_active_agents_cache'):
            self._active_agents_cache = None
        
        if self._active_agents_cache is None:
            self._active_agents_cache = {
                exec.agent_name for exec in self.agent_executions 
                if exec.is_active()
            }
        return self._active_agents_cache
    
    def get_completed_agents(self) -> Set[str]:
        """Get list of completed agents with caching"""
        # Use internal cache
        if not hasattr(self, '_completed_agents_cache'):
            self._completed_agents_cache = None
            
        if self._completed_agents_cache is None:
            self._completed_agents_cache = {
                exec.agent_name for exec in self.agent_executions
                if exec.status == AgentStatus.COMPLETED
            }
        return self._completed_agents_cache
    
    def get_failed_agents(self) -> Set[str]:
        """Get list of failed agents with caching"""
        # Use internal cache
        if not hasattr(self, '_failed_agents_cache'):
            self._failed_agents_cache = None
            
        if self._failed_agents_cache is None:
            self._failed_agents_cache = {
                exec.agent_name for exec in self.agent_executions
                if exec.status == AgentStatus.FAILED
            }
        return self._failed_agents_cache
    
    def add_agent_execution(self, execution: AgentExecution):
        """Add agent execution and update indexes"""
        self.agent_executions.append(execution)
        # Update index for O(1) lookup
        key = (execution.agent_name, execution.task_id)
        self._agent_execution_index[key] = execution
        # Update task index
        if execution.agent_name not in self._agent_task_index:
            self._agent_task_index[execution.agent_name] = []
        self._agent_task_index[execution.agent_name].append(execution.task_id)
        # Clear caches when data changes
        self._active_agents_cache = None
        self._completed_agents_cache = None
        self._failed_agents_cache = None
    
    def get_agent_execution(self, agent_name: str, task_id: str) -> Optional[AgentExecution]:
        """O(1) lookup for agent execution"""
        return self._agent_execution_index.get((agent_name, task_id))
    
    def update_agent_execution(self, agent_name: str, task_id: str, **updates):
        """Update agent execution using O(1) lookup"""
        execution = self._agent_execution_index.get((agent_name, task_id))
        if execution:
            for key, value in updates.items():
                if hasattr(execution, key):
                    setattr(execution, key, value)
            # Clear caches when data changes
            self._active_agents_cache = None
            self._completed_agents_cache = None
            self._failed_agents_cache = None
    
    def is_running(self) -> bool:
        """Check if workflow is currently running"""
        return self.status == WorkflowStatus.RUNNING
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "workflow_id": self.workflow_id,
            "project_path": self.project_path,
            "user_request": self.user_request,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status.value,
            "current_phase": self.current_phase,
            "duration": self.duration(),
            "agent_executions": [exec.to_dict() for exec in self.agent_executions],
            "parallel_groups": self.parallel_groups,
            "active_agents": list(self.get_active_agents()),
            "completed_agents": list(self.get_completed_agents()),
            "failed_agents": list(self.get_failed_agents())
        }


class WorkflowMonitor:
    """Real-time workflow monitoring with O(1) lookups and memory-efficient storage"""
    
    # Performance configuration constants
    MAX_COMPLETED_WORKFLOWS = 1000  # Maximum completed workflows to keep in memory
    MAX_AGENT_EXECUTIONS_PER_WORKFLOW = 500  # Max agent executions per workflow
    CLEANUP_INTERVAL_HOURS = 24  # Cleanup workflows older than this
    MAX_MEMORY_MB = 100  # Maximum memory usage target in MB
    ARCHIVE_BATCH_SIZE = 100  # Workflows to archive in one batch
    
    # Async I/O performance constants
    WRITE_BUFFER_SIZE = 100  # Buffer writes before flushing
    WRITE_FLUSH_INTERVAL = 5  # Seconds between automatic flushes
    MAX_CONCURRENT_WRITES = 10  # Maximum concurrent file write operations
    WRITE_RETRY_ATTEMPTS = 3  # Number of retry attempts for failed writes
    WRITE_RETRY_DELAY = 0.5  # Seconds between retry attempts
    
    def __init__(self, project_path: str, max_completed: int = None, cleanup_hours: int = None):
        self.project_path = Path(project_path)
        self.monitoring_dir = self.project_path / ".subforge" / "monitoring"
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure memory limits
        self.max_completed = max_completed or self.MAX_COMPLETED_WORKFLOWS
        self.cleanup_hours = cleanup_hours or self.CLEANUP_INTERVAL_HOURS
        
        # Async write management
        self.write_queue: Queue[Tuple[Path, Dict[str, Any]]] = Queue(maxsize=self.WRITE_BUFFER_SIZE)
        self.write_task: Optional[Task] = None
        self.write_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_WRITES)
        self.pending_writes: Dict[str, Dict[str, Any]] = {}  # Coalesce writes by workflow_id
        self.last_flush_time = time.time()
        self.write_errors: Deque[Dict[str, Any]] = deque(maxlen=100)  # Track write errors
        
        # Active workflows tracking with O(1) lookup
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        # Use bounded deque for completed workflows to prevent unbounded growth
        self.completed_workflows: Deque[WorkflowExecution] = deque(maxlen=self.max_completed)
        
        # O(1) lookup indexes
        self.workflow_index: Dict[str, WorkflowExecution] = {}  # All workflows by ID
        self.execution_index: Dict[Tuple[str, str, str], AgentExecution] = {}  # (workflow_id, agent, task)
        self.agent_task_index: Dict[str, Set[str]] = {}  # agent -> set of workflow IDs
        self.phase_index: Dict[str, Set[str]] = {}  # phase -> set of workflow IDs
        self.status_index: Dict[WorkflowStatus, Set[str]] = {}  # status -> set of workflow IDs
        
        # Initialize status index
        for status in WorkflowStatus:
            self.status_index[status] = set()
        
        # Initialize internal caches
        self._avg_duration_cache = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            "workflow_started": [],
            "workflow_completed": [],
            "workflow_failed": [],
            "agent_started": [],
            "agent_completed": [],
            "agent_failed": [],
            "phase_changed": []
        }
        
        # Monitoring metrics with memory pooling
        self.start_time = time.time()
        self.total_workflows = 0
        self.successful_workflows = 0
        self.failed_workflows = 0
        
        # Archive management
        self.archive_dir = self.monitoring_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        self.last_cleanup_time = time.time()
        self.archived_count = 0
        
        # Start background write processor
        self._start_write_processor()
        
    def start_workflow(self, workflow_id: str, user_request: str) -> WorkflowExecution:
        """Start monitoring a new workflow with automatic cleanup check"""
        # Perform periodic cleanup check
        current_time = time.time()
        if current_time - self.last_cleanup_time > 3600:  # Check every hour
            asyncio.create_task(self._auto_cleanup())
            self.last_cleanup_time = current_time
        
        # Check active workflow limit to prevent runaway memory usage
        if len(self.active_workflows) >= 500:  # Maximum 500 concurrent workflows
            logger.warning(f"High number of active workflows: {len(self.active_workflows)}")
            # Force cleanup of stale active workflows
            self._cleanup_stale_active_workflows()
        
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            project_path=str(self.project_path),
            user_request=user_request[:500] if len(user_request) > 500 else user_request,  # Limit request size
            start_time=time.time(),
            end_time=None,
            status=WorkflowStatus.RUNNING,
            current_phase="requirements",
            agent_executions=[],
            parallel_groups=[]
        )
        
        # Update all indexes for O(1) access
        self.active_workflows[workflow_id] = workflow
        self.workflow_index[workflow_id] = workflow
        
        # Update phase index
        if "requirements" not in self.phase_index:
            self.phase_index["requirements"] = set()
        self.phase_index["requirements"].add(workflow_id)
        
        # Update status index
        self.status_index[WorkflowStatus.RUNNING].add(workflow_id)
        
        self.total_workflows += 1
        
        # Trigger callbacks
        self._trigger_event("workflow_started", workflow)
        
        # Save workflow state asynchronously
        asyncio.create_task(self._async_save_workflow_state(workflow))
        
        logger.info(f"Started monitoring workflow: {workflow_id}")
        return workflow
    
    def end_workflow(self, workflow_id: str, status: WorkflowStatus, error_message: Optional[str] = None):
        """End workflow monitoring with index updates"""
        # O(1) lookup
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            logger.warning(f"Workflow {workflow_id} not found in active workflows")
            return
        
        # Update workflow status
        old_status = workflow.status
        workflow.end_time = time.time()
        workflow.status = status
        
        # Update status index
        self.status_index[old_status].discard(workflow_id)
        self.status_index[status].add(workflow_id)
        
        # Update statistics
        if status == WorkflowStatus.COMPLETED:
            self.successful_workflows += 1
            self._trigger_event("workflow_completed", workflow)
        elif status == WorkflowStatus.FAILED:
            self.failed_workflows += 1
            self._trigger_event("workflow_failed", workflow, error_message)
        
        # Move to completed workflows (deque automatically manages size)
        self.completed_workflows.append(workflow)
        del self.active_workflows[workflow_id]
        
        # Trim agent executions if too large to save memory
        if len(workflow.agent_executions) > self.MAX_AGENT_EXECUTIONS_PER_WORKFLOW:
            workflow.agent_executions = workflow.agent_executions[-self.MAX_AGENT_EXECUTIONS_PER_WORKFLOW:]
        
        # Archive old workflows if needed
        if len(self.completed_workflows) >= self.max_completed:
            asyncio.create_task(self._archive_old_workflows())
        
        # Save final state with high priority
        asyncio.create_task(self._async_save_workflow_state(workflow, priority=True))
        
        logger.info(f"Ended workflow monitoring: {workflow_id} (Status: {status.value})")
    
    def update_phase(self, workflow_id: str, phase: str):
        """Update current workflow phase with index updates"""
        # O(1) lookup
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            old_phase = workflow.current_phase
            workflow.current_phase = phase
            
            # Update phase index
            if old_phase in self.phase_index:
                self.phase_index[old_phase].discard(workflow_id)
            if phase not in self.phase_index:
                self.phase_index[phase] = set()
            self.phase_index[phase].add(workflow_id)
            
            self._trigger_event("phase_changed", workflow_id, old_phase, phase)
            asyncio.create_task(self._async_save_workflow_state(workflow))
            
            logger.info(f"Workflow {workflow_id} phase changed: {old_phase} -> {phase}")
    
    def start_agent_execution(
        self, 
        workflow_id: str, 
        agent_name: str, 
        task_id: str, 
        task_description: str
    ) -> Optional[AgentExecution]:
        """Start tracking agent execution with memory limits"""
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not found for agent {agent_name}")
            return None
        
        workflow = self.active_workflows[workflow_id]
        
        # Limit agent executions per workflow
        if len(workflow.agent_executions) >= self.MAX_AGENT_EXECUTIONS_PER_WORKFLOW:
            logger.warning(f"Workflow {workflow_id} reached max agent executions limit")
            # Remove oldest completed executions to make room
            completed_execs = [e for e in workflow.agent_executions if e.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]]
            if completed_execs:
                workflow.agent_executions.remove(completed_execs[0])
        
        execution = AgentExecution(
            agent_name=agent_name,
            task_id=task_id,
            start_time=time.time(),
            end_time=None,
            status=AgentStatus.BUSY,
            task_description=task_description[:200] if len(task_description) > 200 else task_description,  # Limit size
            output={},
            error_message=None
        )
        
        # Use the new add_agent_execution method for proper indexing
        workflow.add_agent_execution(execution)
        
        # Update global execution index
        self.execution_index[(workflow_id, agent_name, task_id)] = execution
        
        # Update agent-task index
        if agent_name not in self.agent_task_index:
            self.agent_task_index[agent_name] = set()
        self.agent_task_index[agent_name].add(workflow_id)
        
        # Trigger callbacks
        self._trigger_event("agent_started", workflow_id, execution)
        
        # Save state asynchronously
        asyncio.create_task(self._async_save_workflow_state(self.active_workflows[workflow_id]))
        
        logger.info(f"Started agent execution: {agent_name} in workflow {workflow_id}")
        return execution
    
    def end_agent_execution(
        self, 
        workflow_id: str, 
        agent_name: str, 
        task_id: str,
        status: AgentStatus,
        output: Dict[str, Any],
        error_message: Optional[str] = None
    ):
        """End agent execution tracking with memory-efficient output storage"""
        if workflow_id not in self.active_workflows:
            return
        
        # O(1) workflow lookup
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return
        
        # O(1) execution lookup using index
        execution = self.execution_index.get((workflow_id, agent_name, task_id))
        if not execution:
            # Fallback to workflow's internal index
            execution = workflow.get_agent_execution(agent_name, task_id)
            if not execution:
                logger.warning(f"Agent execution not found: {agent_name}:{task_id}")
                return
        
        # Limit output size to prevent memory bloat
        if output:
            # Convert to string and truncate if too large
            output_str = str(output)
            if len(output_str) > 10000:  # Max 10KB per output
                output = {"truncated": True, "summary": output_str[:10000]}
        
        # Update execution
        execution.end_time = time.time()
        execution.status = status
        execution.output = output
        execution.error_message = error_message[:500] if error_message and len(error_message) > 500 else error_message
        
        # Trigger callbacks
        if status == AgentStatus.COMPLETED:
            self._trigger_event("agent_completed", workflow_id, execution)
        elif status == AgentStatus.FAILED:
            self._trigger_event("agent_failed", workflow_id, execution, error_message)
        
        # Save state asynchronously
        asyncio.create_task(self._async_save_workflow_state(workflow))
        
        logger.info(f"Ended agent execution: {agent_name} in workflow {workflow_id} (Status: {status.value})")
    
    def set_parallel_group(self, workflow_id: str, agent_names: List[str]):
        """Mark a group of agents as executing in parallel"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].parallel_groups.append(agent_names)
            asyncio.create_task(self._async_save_workflow_state(self.active_workflows[workflow_id]))
            
            logger.info(f"Set parallel group in workflow {workflow_id}: {agent_names}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current status of a workflow using O(1) lookup"""
        # O(1) lookup from index
        workflow = self.workflow_index.get(workflow_id)
        if workflow:
            return workflow.to_dict()
        
        return None
    
    def get_workflows_by_status(self, status: WorkflowStatus) -> List[WorkflowExecution]:
        """Get all workflows with a specific status using O(1) index lookup"""
        workflow_ids = self.status_index.get(status, set())
        return [self.workflow_index[wid] for wid in workflow_ids if wid in self.workflow_index]
    
    def get_workflows_by_phase(self, phase: str) -> List[WorkflowExecution]:
        """Get all workflows in a specific phase using O(1) index lookup"""
        workflow_ids = self.phase_index.get(phase, set())
        return [self.workflow_index[wid] for wid in workflow_ids if wid in self.workflow_index]
    
    def get_agent_workflows(self, agent_name: str) -> List[str]:
        """Get all workflow IDs where an agent is involved using O(1) lookup"""
        return list(self.agent_task_index.get(agent_name, set()))
    
    def get_all_workflows(self) -> Dict[str, Any]:
        """Get status of all workflows with memory-conscious response"""
        # Only return recent completed workflows to limit response size
        recent_completed = list(self.completed_workflows)[-10:] if self.completed_workflows else []
        
        return {
            "active": [w.to_dict() for w in self.active_workflows.values()],
            "completed": [w.to_dict() for w in recent_completed],
            "statistics": {
                "total_workflows": self.total_workflows,
                "successful_workflows": self.successful_workflows,
                "failed_workflows": self.failed_workflows,
                "success_rate": self.successful_workflows / max(self.total_workflows, 1) * 100,
                "uptime": time.time() - self.start_time,
                "archived_workflows": self.archived_count,
                "memory_status": self._get_memory_status()
            }
        }
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time monitoring metrics"""
        metrics = {
            "timestamp": time.time(),
            "active_workflows": len(self.active_workflows),
            "total_active_agents": sum(
                len(w.get_active_agents()) for w in self.active_workflows.values()
            ),
            "workflows_in_last_hour": self._count_recent_workflows(3600),
            "average_workflow_duration": self._calculate_average_duration(),
            "current_parallelization": self._calculate_current_parallelization(),
            "system_health": "healthy" if len(self.active_workflows) < 10 else "busy"
        }
        
        return metrics
    
    def register_callback(self, event: str, callback: callable):
        """Register event callback"""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
            logger.info(f"Registered callback for event: {event}")
    
    async def export_monitoring_data(self, output_file: Optional[Path] = None, include_all: bool = False) -> Path:
        """Export monitoring data to JSON file with memory-efficient options"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.monitoring_dir / f"monitoring_export_{timestamp}.json"
        
        # For large exports, only include summaries unless explicitly requested
        if include_all:
            completed_data = [w.to_dict() for w in self.completed_workflows]
        else:
            # Only export last 100 completed workflows by default
            recent_completed = list(self.completed_workflows)[-100:] if self.completed_workflows else []
            completed_data = [w.to_dict() for w in recent_completed]
        
        export_data = {
            "export_timestamp": time.time(),
            "project_path": str(self.project_path),
            "monitoring_period": {
                "start": self.start_time,
                "end": time.time(),
                "duration": time.time() - self.start_time
            },
            "statistics": {
                "total_workflows": self.total_workflows,
                "successful_workflows": self.successful_workflows,
                "failed_workflows": self.failed_workflows,
                "success_rate": self.successful_workflows / max(self.total_workflows, 1) * 100,
                "archived_count": self.archived_count
            },
            "active_workflows": [w.to_dict() for w in self.active_workflows.values()],
            "completed_workflows": completed_data,
            "real_time_metrics": self.get_real_time_metrics()
        }
        
        # Use async file I/O for large exports
        async with aiofiles.open(output_file, 'w') as f:
            await f.write(json.dumps(export_data, indent=2))
        
        logger.info(f"Exported monitoring data to: {output_file}")
        return output_file
    
    def _trigger_event(self, event: str, *args):
        """Trigger registered event callbacks"""
        if event in self.event_callbacks:
            for callback in self.event_callbacks[event]:
                try:
                    callback(*args)
                except Exception as e:
                    logger.error(f"Error in callback for event {event}: {e}")
    
    async def _async_save_workflow_state(self, workflow: WorkflowExecution, priority: bool = False):
        """Save workflow state to disk asynchronously with batching"""
        try:
            workflow_id = workflow.workflow_id
            workflow_data = workflow.to_dict()
            
            if priority:
                # High priority writes bypass the queue
                state_file = self.monitoring_dir / f"workflow_{workflow_id}.json"
                await self._write_file_with_retry(state_file, workflow_data)
            else:
                # Add to pending writes for batching
                self.pending_writes[workflow_id] = workflow_data
                
                # Check if we should flush
                current_time = time.time()
                if (len(self.pending_writes) >= self.WRITE_BUFFER_SIZE or 
                    current_time - self.last_flush_time > self.WRITE_FLUSH_INTERVAL):
                    await self._flush_pending_writes()
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            self.write_errors.append({
                "timestamp": time.time(),
                "workflow_id": workflow.workflow_id,
                "error": str(e)
            })
    
    async def _write_file_with_retry(self, file_path: Path, data: Dict[str, Any], attempts: int = None):
        """Write file with retry logic and error handling"""
        attempts = attempts or self.WRITE_RETRY_ATTEMPTS
        
        for attempt in range(attempts):
            try:
                async with self.write_semaphore:
                    async with aiofiles.open(file_path, 'w') as f:
                        await f.write(json.dumps(data, indent=2))
                return  # Success
            except Exception as e:
                if attempt == attempts - 1:
                    logger.error(f"Failed to write {file_path} after {attempts} attempts: {e}")
                    raise
                await asyncio.sleep(self.WRITE_RETRY_DELAY * (attempt + 1))
    
    async def _flush_pending_writes(self):
        """Flush all pending writes to disk in parallel"""
        if not self.pending_writes:
            return
        
        try:
            # Create write tasks for all pending writes
            write_tasks = []
            for workflow_id, workflow_data in self.pending_writes.items():
                state_file = self.monitoring_dir / f"workflow_{workflow_id}.json"
                task = asyncio.create_task(self._write_file_with_retry(state_file, workflow_data))
                write_tasks.append(task)
            
            # Execute all writes in parallel (limited by semaphore)
            if write_tasks:
                await asyncio.gather(*write_tasks, return_exceptions=True)
            
            # Clear pending writes and update flush time
            self.pending_writes.clear()
            self.last_flush_time = time.time()
            
        except Exception as e:
            logger.error(f"Error during batch write flush: {e}")
    
    def _start_write_processor(self):
        """Start background task for processing writes"""
        async def write_processor():
            """Background task that periodically flushes pending writes"""
            while True:
                try:
                    await asyncio.sleep(self.WRITE_FLUSH_INTERVAL)
                    if self.pending_writes:
                        await self._flush_pending_writes()
                except Exception as e:
                    logger.error(f"Error in write processor: {e}")
        
        # Start the write processor task
        self.write_task = asyncio.create_task(write_processor())
    
    def _save_workflow_state(self, workflow: WorkflowExecution):
        """Legacy synchronous save method for compatibility"""
        try:
            state_file = self.monitoring_dir / f"workflow_{workflow.workflow_id}.json"
            with open(state_file, 'w') as f:
                json.dump(workflow.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
    
    def _count_recent_workflows(self, seconds: int) -> int:
        """Count workflows started in the last N seconds efficiently"""
        cutoff_time = time.time() - seconds
        count = 0
        
        # Use set operations for faster counting
        for workflow_id in self.active_workflows:
            if self.active_workflows[workflow_id].start_time >= cutoff_time:
                count += 1
        
        # Iterate from the end since newer workflows are at the end of deque
        for i in range(min(100, len(self.completed_workflows))):
            try:
                workflow = self.completed_workflows[-(i+1)]
                if workflow.start_time >= cutoff_time:
                    count += 1
                else:
                    break  # Older workflows, can stop checking
            except IndexError:
                break
        
        return count
    
    def _calculate_average_duration(self) -> float:
        """Calculate average workflow duration efficiently"""
        # Cache the result internally
        if not hasattr(self, '_avg_duration_cache') or self._avg_duration_cache is None:
            # Only calculate on last 100 workflows for performance
            recent_workflows = list(self.completed_workflows)[-100:] if len(self.completed_workflows) > 100 else self.completed_workflows
            
            completed_durations = [
                w.duration() for w in recent_workflows 
                if w.duration() is not None
            ]
            
            if not completed_durations:
                self._avg_duration_cache = 0.0
            else:
                self._avg_duration_cache = sum(completed_durations) / len(completed_durations)
        
        return self._avg_duration_cache
    
    def _calculate_current_parallelization(self) -> float:
        """Calculate current parallelization ratio"""
        total_agents = 0
        parallel_agents = 0
        
        for workflow in self.active_workflows.values():
            for group in workflow.parallel_groups:
                if len(group) > 1:
                    total_agents += len(group)
                    parallel_agents += len(group)
                else:
                    total_agents += len(group)
        
        if total_agents == 0:
            return 0.0
        
        return parallel_agents / total_agents
    
    async def cleanup_old_data(self, hours_to_keep: Optional[int] = None):
        """Clean up old monitoring data with automatic archival"""
        hours = hours_to_keep or self.cleanup_hours
        cutoff_time = time.time() - (hours * 3600)
        
        # Archive old workflows before cleanup
        await self._archive_old_workflows()
        
        # Clean old state files
        cleaned_count = 0
        for state_file in self.monitoring_dir.glob("workflow_*.json"):
            try:
                if state_file.stat().st_mtime < cutoff_time:
                    state_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to clean state file {state_file}: {e}")
        
        # Force garbage collection after cleanup
        gc.collect()
        
        logger.info(f"Cleaned {cleaned_count} old state files (older than {hours} hours)")
    
    async def _auto_cleanup(self):
        """Automatic cleanup task that runs periodically"""
        try:
            await self.cleanup_old_data()
        except Exception as e:
            logger.error(f"Auto cleanup failed: {e}")
    
    def _cleanup_stale_active_workflows(self):
        """Clean up stale active workflows that may have been abandoned"""
        current_time = time.time()
        stale_threshold = 3600 * 6  # 6 hours
        
        stale_workflows = []
        for workflow_id, workflow in self.active_workflows.items():
            if current_time - workflow.start_time > stale_threshold:
                stale_workflows.append(workflow_id)
        
        for workflow_id in stale_workflows:
            logger.warning(f"Cleaning up stale workflow: {workflow_id}")
            self.end_workflow(workflow_id, WorkflowStatus.CANCELLED, "Workflow timed out")
        
        # Clear internal caches periodically
        self._avg_duration_cache = None
    
    async def _archive_old_workflows(self):
        """Archive old completed workflows to disk"""
        if len(self.completed_workflows) < self.ARCHIVE_BATCH_SIZE:
            return
        
        try:
            # Get oldest workflows to archive
            to_archive = []
            for _ in range(min(self.ARCHIVE_BATCH_SIZE, len(self.completed_workflows) // 2)):
                if self.completed_workflows:
                    to_archive.append(self.completed_workflows[0])
                    self.completed_workflows.popleft()
            
            if not to_archive:
                return
            
            # Create archive file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = self.archive_dir / f"archive_{timestamp}.json"
            
            archive_data = {
                "archived_at": time.time(),
                "workflow_count": len(to_archive),
                "workflows": [w.to_dict() for w in to_archive]
            }
            
            # Use async I/O for archive writes
            async with aiofiles.open(archive_file, 'w') as f:
                await f.write(json.dumps(archive_data))
            
            # Clean up indexes for archived workflows
            for workflow in to_archive:
                workflow_id = workflow.workflow_id
                # Remove from all indexes
                self.workflow_index.pop(workflow_id, None)
                for phase_set in self.phase_index.values():
                    phase_set.discard(workflow_id)
                for status_set in self.status_index.values():
                    status_set.discard(workflow_id)
                for agent_set in self.agent_task_index.values():
                    agent_set.discard(workflow_id)
                # Remove from execution index
                keys_to_remove = [k for k in self.execution_index if k[0] == workflow_id]
                for key in keys_to_remove:
                    del self.execution_index[key]
            
            self.archived_count += len(to_archive)
            logger.info(f"Archived {len(to_archive)} workflows to {archive_file}")
            
            # Clear caches after archiving
            self._avg_duration_cache = None
            
            # Force garbage collection after archiving
            gc.collect()
            
        except Exception as e:
            logger.error(f"Failed to archive workflows: {e}")
    
    def _get_memory_status(self) -> Dict[str, Any]:
        """Get current memory usage status"""
        return {
            "active_workflows": len(self.active_workflows),
            "completed_in_memory": len(self.completed_workflows),
            "max_completed_allowed": self.max_completed,
            "archived_total": self.archived_count,
            "memory_health": "healthy" if len(self.completed_workflows) < self.max_completed * 0.9 else "near_limit",
            "pending_writes": len(self.pending_writes),
            "write_errors": len(self.write_errors)
        }
    
    async def shutdown(self):
        """Graceful shutdown - flush all pending writes"""
        try:
            # Flush any pending writes
            if self.pending_writes:
                await self._flush_pending_writes()
            
            # Cancel the write processor task
            if self.write_task and not self.write_task.done():
                self.write_task.cancel()
                try:
                    await self.write_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("WorkflowMonitor shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Example usage and testing
if __name__ == "__main__":
    async def example_monitoring():
        """Example of how to use WorkflowMonitor"""
        monitor = WorkflowMonitor("/tmp/test_project")
        
        # Start a workflow
        workflow = monitor.start_workflow(
            "workflow_123", 
            "Create a web application with authentication"
        )
        
        # Register some callbacks
        def on_agent_completed(workflow_id, execution):
            print(f"Agent {execution.agent_name} completed in {execution.duration():.2f}s")
        
        monitor.register_callback("agent_completed", on_agent_completed)
        
        # Simulate agent executions
        monitor.start_agent_execution("workflow_123", "@backend-developer", "task_1", "Create API")
        await asyncio.sleep(1)  # Simulate work
        monitor.end_agent_execution(
            "workflow_123", "@backend-developer", "task_1", 
            AgentStatus.COMPLETED, {"api_endpoints": 5}
        )
        
        # Start parallel agents
        monitor.set_parallel_group("workflow_123", ["@frontend-developer", "@test-engineer"])
        monitor.start_agent_execution("workflow_123", "@frontend-developer", "task_2", "Create UI")
        monitor.start_agent_execution("workflow_123", "@test-engineer", "task_3", "Write tests")
        
        await asyncio.sleep(2)  # Simulate parallel work
        
        monitor.end_agent_execution(
            "workflow_123", "@frontend-developer", "task_2",
            AgentStatus.COMPLETED, {"components": 10}
        )
        monitor.end_agent_execution(
            "workflow_123", "@test-engineer", "task_3",
            AgentStatus.COMPLETED, {"tests": 25}
        )
        
        # End workflow
        monitor.end_workflow("workflow_123", WorkflowStatus.COMPLETED)
        
        # Get final metrics
        metrics = monitor.get_real_time_metrics()
        print(f"Final metrics: {json.dumps(metrics, indent=2)}")
        
        # Export data
        export_file = monitor.export_monitoring_data()
        print(f"Monitoring data exported to: {export_file}")
    
    asyncio.run(example_monitoring())