#!/usr/bin/env python3
"""
SubForge Workflow Monitor
Real-time monitoring and tracking for SubForge workflows
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

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
    """Tracks complete workflow execution"""
    workflow_id: str
    project_path: str
    user_request: str
    start_time: float
    end_time: Optional[float]
    status: WorkflowStatus
    current_phase: str
    agent_executions: List[AgentExecution]
    parallel_groups: List[List[str]]  # Groups of agents executing in parallel
    
    def duration(self) -> Optional[float]:
        """Calculate total workflow duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def get_active_agents(self) -> Set[str]:
        """Get list of currently active agents"""
        return {
            exec.agent_name for exec in self.agent_executions 
            if exec.is_active()
        }
    
    def get_completed_agents(self) -> Set[str]:
        """Get list of completed agents"""
        return {
            exec.agent_name for exec in self.agent_executions
            if exec.status == AgentStatus.COMPLETED
        }
    
    def get_failed_agents(self) -> Set[str]:
        """Get list of failed agents"""
        return {
            exec.agent_name for exec in self.agent_executions
            if exec.status == AgentStatus.FAILED
        }
    
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
    """Real-time workflow monitoring and tracking"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.monitoring_dir = self.project_path / ".subforge" / "monitoring"
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        # Active workflows tracking
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.completed_workflows: List[WorkflowExecution] = []
        
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
        
        # Monitoring metrics
        self.start_time = time.time()
        self.total_workflows = 0
        self.successful_workflows = 0
        self.failed_workflows = 0
        
    def start_workflow(self, workflow_id: str, user_request: str) -> WorkflowExecution:
        """Start monitoring a new workflow"""
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            project_path=str(self.project_path),
            user_request=user_request,
            start_time=time.time(),
            end_time=None,
            status=WorkflowStatus.RUNNING,
            current_phase="requirements",
            agent_executions=[],
            parallel_groups=[]
        )
        
        self.active_workflows[workflow_id] = workflow
        self.total_workflows += 1
        
        # Trigger callbacks
        self._trigger_event("workflow_started", workflow)
        
        # Save workflow state
        self._save_workflow_state(workflow)
        
        logger.info(f"Started monitoring workflow: {workflow_id}")
        return workflow
    
    def end_workflow(self, workflow_id: str, status: WorkflowStatus, error_message: Optional[str] = None):
        """End workflow monitoring"""
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not found in active workflows")
            return
        
        workflow = self.active_workflows[workflow_id]
        workflow.end_time = time.time()
        workflow.status = status
        
        # Update statistics
        if status == WorkflowStatus.COMPLETED:
            self.successful_workflows += 1
            self._trigger_event("workflow_completed", workflow)
        elif status == WorkflowStatus.FAILED:
            self.failed_workflows += 1
            self._trigger_event("workflow_failed", workflow, error_message)
        
        # Move to completed workflows
        self.completed_workflows.append(workflow)
        del self.active_workflows[workflow_id]
        
        # Save final state
        self._save_workflow_state(workflow)
        
        logger.info(f"Ended workflow monitoring: {workflow_id} (Status: {status.value})")
    
    def update_phase(self, workflow_id: str, phase: str):
        """Update current workflow phase"""
        if workflow_id in self.active_workflows:
            old_phase = self.active_workflows[workflow_id].current_phase
            self.active_workflows[workflow_id].current_phase = phase
            
            self._trigger_event("phase_changed", workflow_id, old_phase, phase)
            self._save_workflow_state(self.active_workflows[workflow_id])
            
            logger.info(f"Workflow {workflow_id} phase changed: {old_phase} -> {phase}")
    
    def start_agent_execution(
        self, 
        workflow_id: str, 
        agent_name: str, 
        task_id: str, 
        task_description: str
    ) -> Optional[AgentExecution]:
        """Start tracking agent execution"""
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not found for agent {agent_name}")
            return None
        
        execution = AgentExecution(
            agent_name=agent_name,
            task_id=task_id,
            start_time=time.time(),
            end_time=None,
            status=AgentStatus.BUSY,
            task_description=task_description,
            output={},
            error_message=None
        )
        
        self.active_workflows[workflow_id].agent_executions.append(execution)
        
        # Trigger callbacks
        self._trigger_event("agent_started", workflow_id, execution)
        
        # Save state
        self._save_workflow_state(self.active_workflows[workflow_id])
        
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
        """End agent execution tracking"""
        if workflow_id not in self.active_workflows:
            return
        
        workflow = self.active_workflows[workflow_id]
        
        # Find the execution
        execution = None
        for exec in workflow.agent_executions:
            if exec.agent_name == agent_name and exec.task_id == task_id:
                execution = exec
                break
        
        if not execution:
            logger.warning(f"Agent execution not found: {agent_name}:{task_id}")
            return
        
        # Update execution
        execution.end_time = time.time()
        execution.status = status
        execution.output = output
        execution.error_message = error_message
        
        # Trigger callbacks
        if status == AgentStatus.COMPLETED:
            self._trigger_event("agent_completed", workflow_id, execution)
        elif status == AgentStatus.FAILED:
            self._trigger_event("agent_failed", workflow_id, execution, error_message)
        
        # Save state
        self._save_workflow_state(workflow)
        
        logger.info(f"Ended agent execution: {agent_name} in workflow {workflow_id} (Status: {status.value})")
    
    def set_parallel_group(self, workflow_id: str, agent_names: List[str]):
        """Mark a group of agents as executing in parallel"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].parallel_groups.append(agent_names)
            self._save_workflow_state(self.active_workflows[workflow_id])
            
            logger.info(f"Set parallel group in workflow {workflow_id}: {agent_names}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current status of a workflow"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id].to_dict()
        
        # Check completed workflows
        for workflow in self.completed_workflows:
            if workflow.workflow_id == workflow_id:
                return workflow.to_dict()
        
        return None
    
    def get_all_workflows(self) -> Dict[str, Any]:
        """Get status of all workflows"""
        return {
            "active": [w.to_dict() for w in self.active_workflows.values()],
            "completed": [w.to_dict() for w in self.completed_workflows[-10:]],  # Last 10
            "statistics": {
                "total_workflows": self.total_workflows,
                "successful_workflows": self.successful_workflows,
                "failed_workflows": self.failed_workflows,
                "success_rate": self.successful_workflows / max(self.total_workflows, 1) * 100,
                "uptime": time.time() - self.start_time
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
    
    def export_monitoring_data(self, output_file: Optional[Path] = None) -> Path:
        """Export all monitoring data to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.monitoring_dir / f"monitoring_export_{timestamp}.json"
        
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
                "success_rate": self.successful_workflows / max(self.total_workflows, 1) * 100
            },
            "active_workflows": [w.to_dict() for w in self.active_workflows.values()],
            "completed_workflows": [w.to_dict() for w in self.completed_workflows],
            "real_time_metrics": self.get_real_time_metrics()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
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
    
    def _save_workflow_state(self, workflow: WorkflowExecution):
        """Save workflow state to disk"""
        try:
            state_file = self.monitoring_dir / f"workflow_{workflow.workflow_id}.json"
            with open(state_file, 'w') as f:
                json.dump(workflow.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
    
    def _count_recent_workflows(self, seconds: int) -> int:
        """Count workflows started in the last N seconds"""
        cutoff_time = time.time() - seconds
        count = 0
        
        for workflow in self.active_workflows.values():
            if workflow.start_time >= cutoff_time:
                count += 1
        
        for workflow in self.completed_workflows:
            if workflow.start_time >= cutoff_time:
                count += 1
        
        return count
    
    def _calculate_average_duration(self) -> float:
        """Calculate average workflow duration for completed workflows"""
        completed_durations = [
            w.duration() for w in self.completed_workflows 
            if w.duration() is not None
        ]
        
        if not completed_durations:
            return 0.0
        
        return sum(completed_durations) / len(completed_durations)
    
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
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old monitoring data"""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        
        # Clean completed workflows
        self.completed_workflows = [
            w for w in self.completed_workflows 
            if w.start_time >= cutoff_time
        ]
        
        # Clean old state files
        for state_file in self.monitoring_dir.glob("workflow_*.json"):
            try:
                if state_file.stat().st_mtime < cutoff_time:
                    state_file.unlink()
                    logger.info(f"Cleaned old state file: {state_file}")
            except Exception as e:
                logger.error(f"Failed to clean state file {state_file}: {e}")
        
        logger.info(f"Cleaned monitoring data older than {days_to_keep} days")


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