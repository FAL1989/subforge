"""
SubForge Integration Service for monitoring and integrating with SubForge workflows
"""

import os
import json
import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

try:
    from ..models.subforge_models import (
        WorkflowContext,
        WorkflowSummary,
        WorkflowMetrics,
        FileSystemEvent as FSEvent,
        EventType,
        WorkflowStatus,
        PhaseResult,
        AgentActivity,
        Task,
        SubForgeIntegrationConfig
    )
    from ..websocket.manager import websocket_manager
    from ..core.config import settings
    from ..database.session import get_db
    from .persistence import persistence_service
except ImportError:
    # Fallback for direct execution
    from models.subforge_models import (
        WorkflowContext,
        WorkflowSummary,
        WorkflowMetrics,
        FileSystemEvent as FSEvent,
        EventType,
        WorkflowStatus,
        PhaseResult,
        AgentActivity,
        Task,
        SubForgeIntegrationConfig
    )
    from websocket.manager import websocket_manager
    from core.config import settings
    from database.session import get_db
    from persistence import persistence_service

logger = logging.getLogger(__name__)


class SubForgeFileHandler(FileSystemEventHandler):
    """File system event handler for SubForge directory monitoring"""
    
    def __init__(self, integration_service):
        self.integration_service = integration_service
        super().__init__()
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if not event.is_directory and self._is_relevant_file(event.src_path):
            asyncio.create_task(
                self.integration_service.handle_file_event(
                    EventType.MODIFIED, event.src_path
                )
            )
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if not event.is_directory and self._is_relevant_file(event.src_path):
            asyncio.create_task(
                self.integration_service.handle_file_event(
                    EventType.CREATED, event.src_path
                )
            )
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events"""
        if not event.is_directory and self._is_relevant_file(event.src_path):
            asyncio.create_task(
                self.integration_service.handle_file_event(
                    EventType.DELETED, event.src_path
                )
            )
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move events"""
        if not event.is_directory and self._is_relevant_file(event.dest_path):
            asyncio.create_task(
                self.integration_service.handle_file_event(
                    EventType.MOVED, event.dest_path
                )
            )
    
    def _is_relevant_file(self, file_path: str) -> bool:
        """Check if file is relevant for monitoring"""
        file_path = Path(file_path)
        return (
            file_path.name == "workflow_context.json" or
            file_path.suffix in ['.json', '.md', '.log'] or
            file_path.parent.name in ['analysis', 'generation', 'deployment', 'validation']
        )


class SubForgeIntegrationService:
    """Service for integrating with SubForge workflows"""
    
    def __init__(self, config: SubForgeIntegrationConfig = None):
        self.config = config or SubForgeIntegrationConfig()
        self.workflows: Dict[str, WorkflowContext] = {}
        self.observer: Optional[Observer] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self._last_scan: Optional[datetime] = None
        self._active_workflows: Set[str] = set()
        
        # Initialize base paths
        self.project_root = settings.SUBFORGE_ROOT
        self.subforge_dir = self.project_root / self.config.subforge_dir
        
        logger.info(f"SubForge integration initialized. Monitoring: {self.subforge_dir}")
    
    async def start_monitoring(self):
        """Start file system monitoring and periodic tasks"""
        try:
            # Initial scan
            await self.scan_workflows()
            
            # Start file system monitoring
            if self.config.enable_real_time_monitoring:
                await self._start_file_monitoring()
            
            # Start periodic monitoring task
            self.monitoring_task = asyncio.create_task(self._periodic_monitoring())
            
            logger.info("SubForge monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start SubForge monitoring: {e}")
            raise
    
    async def stop_monitoring(self):
        """Stop file system monitoring and periodic tasks"""
        try:
            # Stop file system observer
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                self.observer = None
            
            # Cancel monitoring task
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                self.monitoring_task = None
            
            logger.info("SubForge monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping SubForge monitoring: {e}")
    
    async def _start_file_monitoring(self):
        """Start file system monitoring using watchdog"""
        if not self.subforge_dir.exists():
            logger.warning(f"SubForge directory does not exist: {self.subforge_dir}")
            return
        
        try:
            self.observer = Observer()
            event_handler = SubForgeFileHandler(self)
            self.observer.schedule(event_handler, str(self.subforge_dir), recursive=True)
            self.observer.start()
            
            logger.info(f"File system monitoring started for: {self.subforge_dir}")
            
        except Exception as e:
            logger.error(f"Failed to start file system monitoring: {e}")
            raise
    
    async def _periodic_monitoring(self):
        """Periodic monitoring task"""
        while True:
            try:
                await asyncio.sleep(self.config.scan_interval)
                await self.scan_workflows()
                await self._cleanup_old_workflows()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic monitoring: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def handle_file_event(self, event_type: EventType, file_path: str):
        """Handle file system events"""
        try:
            file_path_obj = Path(file_path)
            workflow_id = self._extract_workflow_id(file_path_obj)
            
            if not workflow_id:
                return
            
            # Create file system event
            fs_event = FSEvent(
                event_type=event_type,
                file_path=str(file_path_obj),
                timestamp=datetime.utcnow(),
                workflow_id=workflow_id,
                is_workflow_file=file_path_obj.name == "workflow_context.json"
            )
            
            # Process the event
            if fs_event.is_workflow_file and event_type in [EventType.CREATED, EventType.MODIFIED]:
                await self._process_workflow_file(workflow_id, file_path_obj)
            
            # Broadcast real-time update
            if self.config.websocket_broadcast:
                await self._broadcast_file_event(fs_event)
            
            logger.debug(f"Processed file event: {event_type} - {file_path}")
            
        except Exception as e:
            logger.error(f"Error handling file event {event_type} - {file_path}: {e}")
    
    async def scan_workflows(self) -> List[str]:
        """Scan SubForge directory for workflows"""
        if not self.subforge_dir.exists():
            logger.warning(f"SubForge directory not found: {self.subforge_dir}")
            return []
        
        discovered_workflows = []
        
        try:
            # Find all workflow directories
            for workflow_dir in self.subforge_dir.iterdir():
                if workflow_dir.is_dir() and workflow_dir.name.startswith('subforge_'):
                    workflow_context_file = workflow_dir / "workflow_context.json"
                    
                    if workflow_context_file.exists():
                        workflow_id = workflow_dir.name
                        discovered_workflows.append(workflow_id)
                        
                        # Process if not already loaded or if file is newer
                        should_reload = (
                            workflow_id not in self.workflows or
                            workflow_context_file.stat().st_mtime > self._last_scan.timestamp()
                            if self._last_scan else True
                        )
                        
                        if should_reload:
                            await self._process_workflow_file(workflow_id, workflow_context_file)
            
            # Update active workflows
            self._active_workflows = set(discovered_workflows)
            self._last_scan = datetime.utcnow()
            
            # Remove workflows that no longer exist
            removed_workflows = set(self.workflows.keys()) - self._active_workflows
            for workflow_id in removed_workflows:
                self.workflows.pop(workflow_id, None)
                logger.info(f"Removed workflow: {workflow_id}")
            
            logger.info(f"Scanned {len(discovered_workflows)} SubForge workflows")
            
            # Broadcast workflow update
            if self.config.websocket_broadcast and discovered_workflows:
                await self._broadcast_workflow_list_update()
            
            return discovered_workflows
            
        except Exception as e:
            logger.error(f"Error scanning workflows: {e}")
            return []
    
    async def _process_workflow_file(self, workflow_id: str, file_path: Path):
        """Process a workflow context file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse and validate workflow context
            workflow_context = self._parse_workflow_context(workflow_id, data)
            
            # Store workflow
            was_new = workflow_id not in self.workflows
            self.workflows[workflow_id] = workflow_context
            
            # Update workflow metrics
            workflow_context.update_metrics()
            
            logger.info(f"{'Loaded new' if was_new else 'Updated'} workflow: {workflow_id}")
            
            # Persist workflow data if completed or failed
            if workflow_context.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                await self.persist_workflow_execution(workflow_context)
            
            # Broadcast workflow update
            if self.config.websocket_broadcast:
                await self._broadcast_workflow_update(workflow_context, is_new=was_new)
            
        except Exception as e:
            logger.error(f"Error processing workflow file {file_path}: {e}")
    
    def _parse_workflow_context(self, workflow_id: str, data: Dict[str, Any]) -> WorkflowContext:
        """Parse raw workflow data into WorkflowContext model"""
        try:
            # Ensure required fields
            data.setdefault('project_id', workflow_id)
            
            # Parse phase results
            phase_results = {}
            if 'phase_results' in data:
                for phase_name, result_data in data['phase_results'].items():
                    if isinstance(result_data, dict):
                        result_data.setdefault('phase', phase_name)
                        phase_results[phase_name] = PhaseResult(**result_data)
            data['phase_results'] = phase_results
            
            # Determine workflow status
            if 'status' not in data:
                data['status'] = self._determine_workflow_status(phase_results)
            
            # Create workflow context
            workflow_context = WorkflowContext(**data)
            
            # Extract additional information
            self._enrich_workflow_context(workflow_context, data)
            
            return workflow_context
            
        except Exception as e:
            logger.error(f"Error parsing workflow context for {workflow_id}: {e}")
            # Return minimal workflow context
            return WorkflowContext(
                project_id=workflow_id,
                user_request=data.get('user_request', 'Unknown request'),
                project_path=data.get('project_path', ''),
                communication_dir=data.get('communication_dir', ''),
                status=WorkflowStatus.FAILED
            )
    
    def _determine_workflow_status(self, phase_results: Dict[str, PhaseResult]) -> WorkflowStatus:
        """Determine workflow status based on phase results"""
        if not phase_results:
            return WorkflowStatus.ACTIVE
        
        completed_phases = [r for r in phase_results.values() if r.status == 'completed']
        failed_phases = [r for r in phase_results.values() if r.status == 'failed']
        in_progress_phases = [r for r in phase_results.values() if r.status == 'in_progress']
        
        if failed_phases:
            return WorkflowStatus.FAILED
        elif in_progress_phases:
            return WorkflowStatus.ACTIVE
        elif len(completed_phases) == len(phase_results):
            return WorkflowStatus.COMPLETED
        else:
            return WorkflowStatus.ACTIVE
    
    def _enrich_workflow_context(self, workflow_context: WorkflowContext, raw_data: Dict[str, Any]):
        """Enrich workflow context with additional parsed information"""
        # Extract tasks from phase outputs
        tasks = []
        for phase_name, phase_result in workflow_context.phase_results.items():
            # Look for task information in phase outputs
            phase_outputs = phase_result.outputs
            if 'tasks' in phase_outputs:
                for task_data in phase_outputs['tasks']:
                    if isinstance(task_data, dict):
                        task = Task(
                            id=task_data.get('id', f"{phase_name}_{len(tasks)}"),
                            title=task_data.get('title', f"Task from {phase_name}"),
                            description=task_data.get('description'),
                            status=task_data.get('status', 'pending'),
                            phase=phase_name,
                            **{k: v for k, v in task_data.items() if k not in ['id', 'title', 'description', 'status']}
                        )
                        tasks.append(task)
        
        workflow_context.tasks = tasks
        
        # Extract agent activities (mock for now - would need real agent tracking)
        activities = []
        for phase_name, phase_result in workflow_context.phase_results.items():
            if phase_result.status in ['completed', 'in_progress']:
                activity = AgentActivity(
                    agent_id=f"{phase_name}_agent",
                    agent_name=f"{phase_name.title()} Agent",
                    activity_type="phase_execution",
                    description=f"Executing {phase_name} phase",
                    timestamp=phase_result.start_time or datetime.utcnow(),
                    duration=phase_result.duration,
                    status="completed" if phase_result.status == "completed" else "active",
                    workflow_id=workflow_context.project_id,
                    metadata={'phase': phase_name}
                )
                activities.append(activity)
        
        workflow_context.agent_activities = activities
    
    def _extract_workflow_id(self, file_path: Path) -> Optional[str]:
        """Extract workflow ID from file path"""
        parts = file_path.parts
        for part in parts:
            if part.startswith('subforge_'):
                return part
        return None
    
    async def _cleanup_old_workflows(self):
        """Clean up old workflow data"""
        if not self.config.cleanup_after_days:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.cleanup_after_days)
        cleaned_count = 0
        
        for workflow_id, workflow in list(self.workflows.items()):
            if workflow.created_at and workflow.created_at < cutoff_date:
                self.workflows.pop(workflow_id, None)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old workflows")
    
    async def _broadcast_file_event(self, event: FSEvent):
        """Broadcast file system event via WebSocket"""
        try:
            await websocket_manager.broadcast_json({
                "type": "subforge_file_event",
                "data": event.dict()
            })
        except Exception as e:
            logger.error(f"Error broadcasting file event: {e}")
    
    async def _broadcast_workflow_update(self, workflow: WorkflowContext, is_new: bool = False):
        """Broadcast workflow update via WebSocket"""
        try:
            await websocket_manager.broadcast_json({
                "type": "subforge_workflow_update",
                "data": {
                    "workflow_id": workflow.project_id,
                    "workflow": workflow.dict(),
                    "is_new": is_new
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting workflow update: {e}")
    
    async def _broadcast_workflow_list_update(self):
        """Broadcast workflow list update via WebSocket"""
        try:
            workflow_summaries = [self._create_workflow_summary(w) for w in self.workflows.values()]
            await websocket_manager.broadcast_json({
                "type": "subforge_workflow_list_update",
                "data": {
                    "workflows": [w.dict() for w in workflow_summaries],
                    "total_count": len(workflow_summaries)
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting workflow list update: {e}")
    
    # Public API methods
    
    def get_workflows(self) -> List[WorkflowSummary]:
        """Get list of workflow summaries"""
        return [self._create_workflow_summary(workflow) for workflow in self.workflows.values()]
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowContext]:
        """Get specific workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def _create_workflow_summary(self, workflow: WorkflowContext) -> WorkflowSummary:
        """Create workflow summary from full context"""
        return WorkflowSummary(
            project_id=workflow.project_id,
            user_request=workflow.user_request,
            status=workflow.status,
            progress_percentage=workflow.progress_percentage,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            current_phase=workflow.get_current_phase(),
            total_phases=workflow.total_phases,
            completed_phases=workflow.completed_phases,
            failed_phases=workflow.failed_phases,
            agent_count=len(workflow.deployed_agents)
        )
    
    def get_workflow_metrics(self) -> WorkflowMetrics:
        """Get aggregated workflow metrics"""
        total_workflows = len(self.workflows)
        active_workflows = len([w for w in self.workflows.values() if w.status == WorkflowStatus.ACTIVE])
        completed_workflows = len([w for w in self.workflows.values() if w.status == WorkflowStatus.COMPLETED])
        failed_workflows = len([w for w in self.workflows.values() if w.status == WorkflowStatus.FAILED])
        
        # Calculate success rate
        success_rate = (completed_workflows / total_workflows * 100) if total_workflows > 0 else 0.0
        
        # Get recent activities
        all_activities = []
        for workflow in self.workflows.values():
            all_activities.extend(workflow.agent_activities)
        
        # Sort by timestamp and get recent ones
        recent_activities = sorted(all_activities, key=lambda x: x.timestamp, reverse=True)[:10]
        
        return WorkflowMetrics(
            total_workflows=total_workflows,
            active_workflows=active_workflows,
            completed_workflows=completed_workflows,
            failed_workflows=failed_workflows,
            success_rate=success_rate,
            recent_activities=recent_activities
        )

    async def persist_workflow_execution(self, workflow: WorkflowContext):
        """
        Persist workflow execution data to database for historical tracking
        
        Args:
            workflow: WorkflowContext to persist
        """
        try:
            async for db_session in get_db():
                # Prepare workflow data for persistence
                workflow_data = {
                    'workflow_id': workflow.project_id,
                    'execution_id': f"{workflow.project_id}_{datetime.utcnow().isoformat()}",
                    'execution_number': 1,  # Could be calculated based on existing records
                    'name': workflow.user_request[:255] if workflow.user_request else 'Unknown Workflow',
                    'type': 'subforge_workflow',
                    'project_id': workflow.project_id,
                    'project_name': workflow.project_path.split('/')[-1] if workflow.project_path else workflow.project_id,
                    'status': workflow.status.value.lower(),
                    'final_result': self._determine_final_result(workflow),
                    'started_at': workflow.created_at or datetime.utcnow(),
                    'completed_at': workflow.updated_at if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED] else None,
                    'duration_seconds': self._calculate_workflow_duration(workflow),
                    'total_phases': workflow.total_phases,
                    'completed_phases': workflow.completed_phases,
                    'failed_phases': workflow.failed_phases,
                    'skipped_phases': 0,  # Calculate if available
                    'total_tasks': len(workflow.tasks) if workflow.tasks else 0,
                    'completed_tasks': len([t for t in workflow.tasks if t.status == 'completed']) if workflow.tasks else 0,
                    'failed_tasks': len([t for t in workflow.tasks if t.status == 'failed']) if workflow.tasks else 0,
                    'success_rate': workflow.progress_percentage or 0.0,
                    'quality_score': self._calculate_quality_score(workflow),
                    'efficiency_score': self._calculate_efficiency_score(workflow),
                    'configuration': workflow.to_dict().get('configuration', {}),
                    'parameters': workflow.to_dict().get('parameters', {}),
                    'assigned_agents': self._extract_agent_list(workflow),
                    'agent_performance_summary': self._calculate_agent_performance_summary(workflow),
                    'error_messages': self._extract_error_messages(workflow),
                    'warnings': self._extract_warnings(workflow),
                    'critical_issues': self._extract_critical_issues(workflow),
                    'resource_usage': self._extract_resource_usage(workflow),
                    'triggered_by': 'subforge_system',
                    'trigger_event': {'source': 'file_system_monitor', 'timestamp': datetime.utcnow().isoformat()}
                }
                
                # Store workflow history
                workflow_history = await persistence_service.store_workflow_execution(
                    db_session, workflow_data
                )
                
                # Store phase history
                for phase_name, phase_result in workflow.phase_results.items():
                    phase_data = {
                        'name': phase_name,
                        'type': 'subforge_phase',
                        'order': self._get_phase_order(phase_name, workflow),
                        'status': phase_result.status or 'unknown',
                        'result': 'success' if phase_result.status == 'completed' else 'failure' if phase_result.status == 'failed' else 'pending',
                        'started_at': phase_result.start_time,
                        'completed_at': phase_result.end_time,
                        'duration_seconds': phase_result.duration,
                        'assigned_agent_id': f"{phase_name}_agent",
                        'assigned_agent_name': f"{phase_name.title()} Agent",
                        'agent_utilization': 100.0 if phase_result.status == 'completed' else None,
                        'config': {'phase_name': phase_name},
                        'input_parameters': phase_result.inputs or {},
                        'output_results': phase_result.outputs or {},
                        'quality_score': self._calculate_phase_quality_score(phase_result),
                        'performance_score': self._calculate_phase_performance_score(phase_result),
                        'total_tasks': len([t for t in workflow.tasks if t.phase == phase_name]) if workflow.tasks else 0,
                        'completed_tasks': len([t for t in workflow.tasks if t.phase == phase_name and t.status == 'completed']) if workflow.tasks else 0,
                        'failed_tasks': len([t for t in workflow.tasks if t.phase == phase_name and t.status == 'failed']) if workflow.tasks else 0,
                        'dependencies': self._get_phase_dependencies(phase_name, workflow),
                        'dependents': self._get_phase_dependents(phase_name, workflow),
                        'error_messages': phase_result.errors or [],
                        'warnings': phase_result.warnings or [],
                        'resource_usage': {}
                    }
                    
                    await persistence_service.store_phase_execution(
                        db_session, workflow_history.id, phase_data
                    )
                
                # Store handoff history (if handoffs are tracked)
                handoffs = self._extract_handoffs(workflow)
                for handoff_data in handoffs:
                    await persistence_service.store_handoff_execution(
                        db_session, workflow_history.id, handoff_data
                    )
                
                # Calculate and store agent performance metrics
                await self._store_agent_performance_metrics(db_session, workflow)
                
                logger.info(f"Persisted workflow execution: {workflow_history.id}")
                
        except Exception as e:
            logger.error(f"Error persisting workflow execution: {e}")

    def _determine_final_result(self, workflow: WorkflowContext) -> str:
        """Determine final result of workflow"""
        if workflow.status == WorkflowStatus.COMPLETED:
            return 'success'
        elif workflow.status == WorkflowStatus.FAILED:
            return 'failure'
        else:
            return 'partial'

    def _calculate_workflow_duration(self, workflow: WorkflowContext) -> Optional[float]:
        """Calculate workflow duration in seconds"""
        if workflow.created_at and workflow.updated_at:
            return (workflow.updated_at - workflow.created_at).total_seconds()
        return None

    def _calculate_quality_score(self, workflow: WorkflowContext) -> Optional[float]:
        """Calculate overall quality score for workflow"""
        if not workflow.phase_results:
            return None
        
        completed_phases = [p for p in workflow.phase_results.values() if p.status == 'completed']
        if not completed_phases:
            return None
        
        # Simple quality score based on completion without errors
        error_count = sum(len(p.errors or []) for p in completed_phases)
        total_phases = len(completed_phases)
        
        if total_phases == 0:
            return None
        
        # Score decreases with more errors
        base_score = 100.0
        error_penalty = min(error_count * 10, 50)  # Max 50 point penalty
        return max(base_score - error_penalty, 0.0)

    def _calculate_efficiency_score(self, workflow: WorkflowContext) -> Optional[float]:
        """Calculate efficiency score based on completion rate and speed"""
        if workflow.total_phases == 0:
            return None
        
        completion_rate = (workflow.completed_phases / workflow.total_phases) * 100
        
        # Factor in duration if available
        duration_factor = 1.0
        if hasattr(workflow, 'expected_duration') and workflow.created_at and workflow.updated_at:
            actual_duration = (workflow.updated_at - workflow.created_at).total_seconds()
            expected_duration = getattr(workflow, 'expected_duration', actual_duration)
            if expected_duration > 0:
                duration_factor = min(expected_duration / actual_duration, 2.0)  # Cap at 2x efficiency
        
        return min(completion_rate * duration_factor, 100.0)

    def _extract_agent_list(self, workflow: WorkflowContext) -> List[Dict[str, Any]]:
        """Extract list of agents involved in workflow"""
        agents = []
        for phase_name in workflow.phase_results.keys():
            agent = {
                'id': f"{phase_name}_agent",
                'name': f"{phase_name.title()} Agent",
                'type': 'subforge_phase_agent',
                'phase': phase_name
            }
            if agent not in agents:
                agents.append(agent)
        return agents

    def _calculate_agent_performance_summary(self, workflow: WorkflowContext) -> Dict[str, Any]:
        """Calculate agent performance summary"""
        summary = {}
        for phase_name, phase_result in workflow.phase_results.items():
            agent_id = f"{phase_name}_agent"
            summary[agent_id] = {
                'phase': phase_name,
                'status': phase_result.status,
                'duration': phase_result.duration,
                'error_count': len(phase_result.errors or []),
                'warning_count': len(phase_result.warnings or [])
            }
        return summary

    def _extract_error_messages(self, workflow: WorkflowContext) -> List[str]:
        """Extract all error messages from workflow"""
        errors = []
        for phase_result in workflow.phase_results.values():
            if phase_result.errors:
                errors.extend(phase_result.errors)
        return errors

    def _extract_warnings(self, workflow: WorkflowContext) -> List[str]:
        """Extract all warning messages from workflow"""
        warnings = []
        for phase_result in workflow.phase_results.values():
            if phase_result.warnings:
                warnings.extend(phase_result.warnings)
        return warnings

    def _extract_critical_issues(self, workflow: WorkflowContext) -> List[Dict[str, Any]]:
        """Extract critical issues from workflow"""
        critical_issues = []
        for phase_name, phase_result in workflow.phase_results.items():
            if phase_result.status == 'failed':
                issue = {
                    'phase': phase_name,
                    'type': 'phase_failure',
                    'severity': 'critical',
                    'message': f"Phase {phase_name} failed",
                    'errors': phase_result.errors or []
                }
                critical_issues.append(issue)
        return critical_issues

    def _extract_resource_usage(self, workflow: WorkflowContext) -> Dict[str, Any]:
        """Extract resource usage information"""
        # Placeholder - would need actual resource monitoring
        return {
            'cpu_usage': None,
            'memory_usage': None,
            'disk_usage': None,
            'network_usage': None
        }

    def _get_phase_order(self, phase_name: str, workflow: WorkflowContext) -> int:
        """Get the order of a phase in the workflow"""
        # Standard SubForge phases order
        phase_order_map = {
            'analysis': 1,
            'generation': 2,
            'deployment': 3,
            'validation': 4
        }
        return phase_order_map.get(phase_name.lower(), 999)

    def _calculate_phase_quality_score(self, phase_result: PhaseResult) -> Optional[float]:
        """Calculate quality score for individual phase"""
        if phase_result.status == 'completed':
            error_count = len(phase_result.errors or [])
            warning_count = len(phase_result.warnings or [])
            
            base_score = 100.0
            error_penalty = error_count * 15  # 15 points per error
            warning_penalty = warning_count * 5  # 5 points per warning
            
            return max(base_score - error_penalty - warning_penalty, 0.0)
        return None

    def _calculate_phase_performance_score(self, phase_result: PhaseResult) -> Optional[float]:
        """Calculate performance score for individual phase"""
        if phase_result.status == 'completed' and phase_result.duration:
            # Simple performance score based on completion
            return 100.0 if phase_result.duration < 3600 else 80.0  # 1 hour threshold
        return None

    def _get_phase_dependencies(self, phase_name: str, workflow: WorkflowContext) -> List[str]:
        """Get dependencies for a phase"""
        # Standard SubForge phase dependencies
        dependencies_map = {
            'generation': ['analysis'],
            'deployment': ['analysis', 'generation'],
            'validation': ['analysis', 'generation', 'deployment']
        }
        return dependencies_map.get(phase_name.lower(), [])

    def _get_phase_dependents(self, phase_name: str, workflow: WorkflowContext) -> List[str]:
        """Get phases that depend on this phase"""
        dependents_map = {
            'analysis': ['generation', 'deployment', 'validation'],
            'generation': ['deployment', 'validation'],
            'deployment': ['validation']
        }
        return dependents_map.get(phase_name.lower(), [])

    def _extract_handoffs(self, workflow: WorkflowContext) -> List[Dict[str, Any]]:
        """Extract handoff information between phases"""
        handoffs = []
        phases = list(workflow.phase_results.keys())
        
        for i in range(len(phases) - 1):
            source_phase = phases[i]
            target_phase = phases[i + 1]
            
            source_result = workflow.phase_results.get(source_phase)
            target_result = workflow.phase_results.get(target_phase)
            
            if source_result and target_result:
                handoff = {
                    'name': f"{source_phase}_to_{target_phase}",
                    'type': 'phase_to_phase',
                    'source_phase_name': source_phase,
                    'target_phase_name': target_phase,
                    'source_agent_id': f"{source_phase}_agent",
                    'target_agent_id': f"{target_phase}_agent",
                    'status': 'completed' if target_result.start_time else 'pending',
                    'result': 'success' if target_result.status == 'completed' else 'pending',
                    'initiated_at': source_result.end_time or datetime.utcnow(),
                    'completed_at': target_result.start_time,
                    'duration_seconds': None,
                    'handoff_data': source_result.outputs or {},
                    'validation_rules': {},
                    'validation_results': {},
                    'context_info': {'workflow_id': workflow.project_id},
                    'metadata': {'source_phase': source_phase, 'target_phase': target_phase}
                }
                handoffs.append(handoff)
        
        return handoffs

    async def _store_agent_performance_metrics(self, session, workflow: WorkflowContext):
        """Store agent performance metrics for workflow agents"""
        try:
            # Calculate metrics for each agent involved
            for phase_name, phase_result in workflow.phase_results.items():
                agent_id = f"{phase_name}_agent"
                
                # Use current hour as the period
                now = datetime.utcnow()
                period_start = now.replace(minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(hours=1)
                
                await persistence_service.calculate_and_store_agent_performance(
                    session, agent_id, period_start, period_end, "hour"
                )
                
        except Exception as e:
            logger.error(f"Error storing agent performance metrics: {e}")


# Global integration service instance
subforge_integration = SubForgeIntegrationService()