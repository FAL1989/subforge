"""
Database models for SubForge workflow history and persistence
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Integer, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Session
from datetime import datetime
import uuid

from ..database.base import Base


class WorkflowHistory(Base):
    """
    Historical record of workflow executions with complete lifecycle data
    """
    __tablename__ = "workflow_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Execution metadata
    execution_id = Column(String(255), nullable=False, index=True)  # Unique execution instance
    execution_number = Column(Integer, nullable=False, default=1)  # Execution attempt number
    
    # Workflow details at execution time
    workflow_name = Column(String(255), nullable=False, index=True)
    workflow_type = Column(String(100), nullable=True, index=True)
    project_id = Column(String(255), nullable=True, index=True)
    project_name = Column(String(255), nullable=True)
    
    # Execution status and results
    status = Column(String(50), nullable=False, index=True)  # running, completed, failed, cancelled
    final_result = Column(String(50), nullable=True, index=True)  # success, failure, partial
    
    # Time tracking
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Progress and metrics
    total_phases = Column(Integer, nullable=False, default=0)
    completed_phases = Column(Integer, nullable=False, default=0)
    failed_phases = Column(Integer, nullable=False, default=0)
    skipped_phases = Column(Integer, nullable=False, default=0)
    
    total_tasks = Column(Integer, nullable=False, default=0)
    completed_tasks = Column(Integer, nullable=False, default=0)
    failed_tasks = Column(Integer, nullable=False, default=0)
    
    # Quality metrics
    success_rate = Column(Float, nullable=False, default=0.0)
    quality_score = Column(Float, nullable=True)
    efficiency_score = Column(Float, nullable=True)
    
    # Configuration and parameters
    configuration = Column(JSON, nullable=False, default=dict)
    parameters = Column(JSON, nullable=False, default=dict)
    environment_info = Column(JSON, nullable=False, default=dict)
    
    # Agent assignments and performance
    assigned_agents = Column(JSON, nullable=False, default=list)
    agent_performance_summary = Column(JSON, nullable=False, default=dict)
    
    # Error and issue tracking
    error_messages = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=False, default=list)
    critical_issues = Column(JSON, nullable=False, default=list)
    
    # Resource utilization
    resource_usage = Column(JSON, nullable=False, default=dict)  # CPU, memory, disk usage
    
    # Audit trail
    triggered_by = Column(String(255), nullable=True)  # user, system, schedule, etc.
    trigger_event = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    phases = relationship("PhaseHistory", back_populates="workflow_history", cascade="all, delete-orphan")
    handoffs = relationship("HandoffHistory", back_populates="workflow_history", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_workflow_history_status_time', 'status', 'started_at'),
        Index('idx_workflow_history_project_time', 'project_id', 'started_at'),
        Index('idx_workflow_history_execution', 'workflow_id', 'execution_number'),
        Index('idx_workflow_history_duration', 'duration_seconds'),
    )

    def __repr__(self) -> str:
        return f"<WorkflowHistory(id={self.id}, workflow_name='{self.workflow_name}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert workflow history to dictionary"""
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id),
            "execution_id": self.execution_id,
            "execution_number": self.execution_number,
            "workflow": {
                "name": self.workflow_name,
                "type": self.workflow_type,
                "project_id": self.project_id,
                "project_name": self.project_name
            },
            "status": self.status,
            "final_result": self.final_result,
            "time_tracking": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_seconds": self.duration_seconds
            },
            "progress": {
                "phases": {
                    "total": self.total_phases,
                    "completed": self.completed_phases,
                    "failed": self.failed_phases,
                    "skipped": self.skipped_phases
                },
                "tasks": {
                    "total": self.total_tasks,
                    "completed": self.completed_tasks,
                    "failed": self.failed_tasks
                }
            },
            "quality_metrics": {
                "success_rate": self.success_rate,
                "quality_score": self.quality_score,
                "efficiency_score": self.efficiency_score
            },
            "agents": {
                "assigned": self.assigned_agents,
                "performance_summary": self.agent_performance_summary
            },
            "issues": {
                "errors": self.error_messages,
                "warnings": self.warnings,
                "critical": self.critical_issues
            },
            "resource_usage": self.resource_usage,
            "trigger": {
                "by": self.triggered_by,
                "event": self.trigger_event
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PhaseHistory(Base):
    """
    Historical record of individual workflow phases
    """
    __tablename__ = "phase_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_history_id = Column(UUID(as_uuid=True), ForeignKey("workflow_history.id"), nullable=False, index=True)
    
    # Phase identification
    phase_name = Column(String(255), nullable=False, index=True)
    phase_type = Column(String(100), nullable=True, index=True)
    phase_order = Column(Integer, nullable=False, index=True)
    
    # Status and results
    status = Column(String(50), nullable=False, index=True)  # pending, running, completed, failed, skipped
    result = Column(String(50), nullable=True, index=True)   # success, failure, partial
    
    # Time tracking
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Agent assignment
    assigned_agent_id = Column(String(255), nullable=True, index=True)
    assigned_agent_name = Column(String(255), nullable=True)
    agent_utilization = Column(Float, nullable=True)  # Percentage of time agent spent on this phase
    
    # Phase configuration and parameters
    phase_config = Column(JSON, nullable=False, default=dict)
    input_parameters = Column(JSON, nullable=False, default=dict)
    output_results = Column(JSON, nullable=False, default=dict)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    
    # Task tracking within phase
    total_tasks = Column(Integer, nullable=False, default=0)
    completed_tasks = Column(Integer, nullable=False, default=0)
    failed_tasks = Column(Integer, nullable=False, default=0)
    
    # Dependencies and relationships
    dependencies = Column(JSON, nullable=False, default=list)  # Other phases this depends on
    dependents = Column(JSON, nullable=False, default=list)    # Other phases depending on this
    
    # Error and issue tracking
    error_messages = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=False, default=list)
    
    # Resource usage
    resource_usage = Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow_history = relationship("WorkflowHistory", back_populates="phases")

    # Indexes for performance
    __table_args__ = (
        Index('idx_phase_history_workflow_order', 'workflow_history_id', 'phase_order'),
        Index('idx_phase_history_status_time', 'status', 'started_at'),
        Index('idx_phase_history_agent', 'assigned_agent_id', 'started_at'),
        Index('idx_phase_history_duration', 'duration_seconds'),
    )

    def __repr__(self) -> str:
        return f"<PhaseHistory(id={self.id}, phase_name='{self.phase_name}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert phase history to dictionary"""
        return {
            "id": str(self.id),
            "workflow_history_id": str(self.workflow_history_id),
            "phase": {
                "name": self.phase_name,
                "type": self.phase_type,
                "order": self.phase_order
            },
            "status": self.status,
            "result": self.result,
            "time_tracking": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_seconds": self.duration_seconds
            },
            "agent": {
                "id": self.assigned_agent_id,
                "name": self.assigned_agent_name,
                "utilization": self.agent_utilization
            },
            "config": self.phase_config,
            "parameters": {
                "input": self.input_parameters,
                "output": self.output_results
            },
            "quality_metrics": {
                "quality_score": self.quality_score,
                "performance_score": self.performance_score
            },
            "tasks": {
                "total": self.total_tasks,
                "completed": self.completed_tasks,
                "failed": self.failed_tasks
            },
            "relationships": {
                "dependencies": self.dependencies,
                "dependents": self.dependents
            },
            "issues": {
                "errors": self.error_messages,
                "warnings": self.warnings
            },
            "resource_usage": self.resource_usage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class HandoffHistory(Base):
    """
    Historical record of handoffs between workflow phases and agents
    """
    __tablename__ = "handoff_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_history_id = Column(UUID(as_uuid=True), ForeignKey("workflow_history.id"), nullable=False, index=True)
    
    # Handoff identification
    handoff_name = Column(String(255), nullable=False, index=True)
    handoff_type = Column(String(100), nullable=True, index=True)  # phase_to_phase, agent_to_agent
    
    # Source and target information
    source_phase_name = Column(String(255), nullable=True, index=True)
    target_phase_name = Column(String(255), nullable=True, index=True)
    source_agent_id = Column(String(255), nullable=True, index=True)
    target_agent_id = Column(String(255), nullable=True, index=True)
    
    # Status and results
    status = Column(String(50), nullable=False, index=True)  # pending, in_progress, completed, failed
    result = Column(String(50), nullable=True, index=True)   # success, failure, partial
    
    # Time tracking
    initiated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Handoff data and validation
    handoff_data = Column(JSON, nullable=False, default=dict)  # Data being handed off
    validation_rules = Column(JSON, nullable=False, default=dict)
    validation_results = Column(JSON, nullable=False, default=dict)
    
    # Quality metrics
    data_quality_score = Column(Float, nullable=True)
    handoff_efficiency_score = Column(Float, nullable=True)
    
    # Error and issue tracking
    error_messages = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=False, default=list)
    validation_failures = Column(JSON, nullable=False, default=list)
    
    # Context and metadata
    context_info = Column(JSON, nullable=False, default=dict)
    handoff_metadata = Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow_history = relationship("WorkflowHistory", back_populates="handoffs")

    # Indexes for performance
    __table_args__ = (
        Index('idx_handoff_history_workflow_time', 'workflow_history_id', 'initiated_at'),
        Index('idx_handoff_history_status', 'status', 'initiated_at'),
        Index('idx_handoff_history_agents', 'source_agent_id', 'target_agent_id'),
        Index('idx_handoff_history_phases', 'source_phase_name', 'target_phase_name'),
        Index('idx_handoff_history_duration', 'duration_seconds'),
    )

    def __repr__(self) -> str:
        return f"<HandoffHistory(id={self.id}, handoff_name='{self.handoff_name}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert handoff history to dictionary"""
        return {
            "id": str(self.id),
            "workflow_history_id": str(self.workflow_history_id),
            "handoff": {
                "name": self.handoff_name,
                "type": self.handoff_type
            },
            "source": {
                "phase_name": self.source_phase_name,
                "agent_id": self.source_agent_id
            },
            "target": {
                "phase_name": self.target_phase_name,
                "agent_id": self.target_agent_id
            },
            "status": self.status,
            "result": self.result,
            "time_tracking": {
                "initiated_at": self.initiated_at.isoformat() if self.initiated_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_seconds": self.duration_seconds
            },
            "data": {
                "handoff_data": self.handoff_data,
                "validation_rules": self.validation_rules,
                "validation_results": self.validation_results
            },
            "quality_metrics": {
                "data_quality_score": self.data_quality_score,
                "handoff_efficiency_score": self.handoff_efficiency_score
            },
            "issues": {
                "errors": self.error_messages,
                "warnings": self.warnings,
                "validation_failures": self.validation_failures
            },
            "context": self.context_info,
            "metadata": self.handoff_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AgentPerformanceMetrics(Base):
    """
    Performance metrics and analytics for individual agents over time
    """
    __tablename__ = "agent_performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Agent identification
    agent_id = Column(String(255), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)
    agent_type = Column(String(100), nullable=True, index=True)
    
    # Time period for metrics
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(50), nullable=False, index=True)  # hour, day, week, month
    
    # Performance metrics
    total_workflows = Column(Integer, nullable=False, default=0)
    successful_workflows = Column(Integer, nullable=False, default=0)
    failed_workflows = Column(Integer, nullable=False, default=0)
    
    total_phases = Column(Integer, nullable=False, default=0)
    successful_phases = Column(Integer, nullable=False, default=0)
    failed_phases = Column(Integer, nullable=False, default=0)
    
    total_tasks = Column(Integer, nullable=False, default=0)
    successful_tasks = Column(Integer, nullable=False, default=0)
    failed_tasks = Column(Integer, nullable=False, default=0)
    
    # Time metrics
    total_active_time_seconds = Column(Float, nullable=False, default=0.0)
    average_task_duration_seconds = Column(Float, nullable=True)
    average_phase_duration_seconds = Column(Float, nullable=True)
    
    # Quality metrics
    average_quality_score = Column(Float, nullable=True)
    average_performance_score = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    
    # Utilization metrics
    utilization_percentage = Column(Float, nullable=False, default=0.0)
    idle_time_seconds = Column(Float, nullable=False, default=0.0)
    overload_incidents = Column(Integer, nullable=False, default=0)
    
    # Error and issue tracking
    total_errors = Column(Integer, nullable=False, default=0)
    total_warnings = Column(Integer, nullable=False, default=0)
    critical_issues = Column(Integer, nullable=False, default=0)
    
    # Resource usage
    average_cpu_usage = Column(Float, nullable=True)
    average_memory_usage = Column(Float, nullable=True)
    peak_resource_usage = Column(JSON, nullable=False, default=dict)
    
    # Collaboration metrics
    successful_handoffs = Column(Integer, nullable=False, default=0)
    failed_handoffs = Column(Integer, nullable=False, default=0)
    average_handoff_time_seconds = Column(Float, nullable=True)
    
    # Specialization metrics (tasks by category)
    task_category_performance = Column(JSON, nullable=False, default=dict)
    skill_proficiency_scores = Column(JSON, nullable=False, default=dict)
    
    # Trend data
    performance_trend = Column(String(50), nullable=True, index=True)  # improving, declining, stable
    trend_confidence = Column(Float, nullable=True)
    
    # Learning and adaptation metrics
    learning_rate = Column(Float, nullable=True)
    adaptation_score = Column(Float, nullable=True)
    improvement_rate = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    calculated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index('idx_agent_perf_agent_period', 'agent_id', 'period_start', 'period_end'),
        Index('idx_agent_perf_type_period', 'agent_type', 'period_type', 'period_start'),
        Index('idx_agent_perf_quality', 'average_quality_score', 'period_start'),
        Index('idx_agent_perf_utilization', 'utilization_percentage', 'period_start'),
        Index('idx_agent_perf_trend', 'performance_trend', 'period_start'),
    )

    def __repr__(self) -> str:
        return f"<AgentPerformanceMetrics(agent_id='{self.agent_id}', period='{self.period_type}', quality={self.average_quality_score})>"

    def to_dict(self) -> dict:
        """Convert agent performance metrics to dictionary"""
        return {
            "id": str(self.id),
            "agent": {
                "id": self.agent_id,
                "name": self.agent_name,
                "type": self.agent_type
            },
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat() if self.period_end else None,
                "type": self.period_type
            },
            "performance": {
                "workflows": {
                    "total": self.total_workflows,
                    "successful": self.successful_workflows,
                    "failed": self.failed_workflows,
                    "success_rate": self.successful_workflows / self.total_workflows if self.total_workflows > 0 else 0
                },
                "phases": {
                    "total": self.total_phases,
                    "successful": self.successful_phases,
                    "failed": self.failed_phases,
                    "success_rate": self.successful_phases / self.total_phases if self.total_phases > 0 else 0
                },
                "tasks": {
                    "total": self.total_tasks,
                    "successful": self.successful_tasks,
                    "failed": self.failed_tasks,
                    "success_rate": self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0
                }
            },
            "time_metrics": {
                "total_active_time_seconds": self.total_active_time_seconds,
                "average_task_duration_seconds": self.average_task_duration_seconds,
                "average_phase_duration_seconds": self.average_phase_duration_seconds
            },
            "quality_metrics": {
                "average_quality_score": self.average_quality_score,
                "average_performance_score": self.average_performance_score,
                "consistency_score": self.consistency_score
            },
            "utilization": {
                "utilization_percentage": self.utilization_percentage,
                "idle_time_seconds": self.idle_time_seconds,
                "overload_incidents": self.overload_incidents
            },
            "issues": {
                "total_errors": self.total_errors,
                "total_warnings": self.total_warnings,
                "critical_issues": self.critical_issues
            },
            "resource_usage": {
                "average_cpu_usage": self.average_cpu_usage,
                "average_memory_usage": self.average_memory_usage,
                "peak_resource_usage": self.peak_resource_usage
            },
            "collaboration": {
                "successful_handoffs": self.successful_handoffs,
                "failed_handoffs": self.failed_handoffs,
                "average_handoff_time_seconds": self.average_handoff_time_seconds,
                "handoff_success_rate": self.successful_handoffs / (self.successful_handoffs + self.failed_handoffs) if (self.successful_handoffs + self.failed_handoffs) > 0 else 0
            },
            "specialization": {
                "task_category_performance": self.task_category_performance,
                "skill_proficiency_scores": self.skill_proficiency_scores
            },
            "trends": {
                "performance_trend": self.performance_trend,
                "trend_confidence": self.trend_confidence,
                "learning_rate": self.learning_rate,
                "adaptation_score": self.adaptation_score,
                "improvement_rate": self.improvement_rate
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None
        }

    def calculate_success_rates(self) -> dict:
        """Calculate various success rates for the agent"""
        workflow_success_rate = self.successful_workflows / self.total_workflows if self.total_workflows > 0 else 0
        phase_success_rate = self.successful_phases / self.total_phases if self.total_phases > 0 else 0
        task_success_rate = self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0
        handoff_success_rate = self.successful_handoffs / (self.successful_handoffs + self.failed_handoffs) if (self.successful_handoffs + self.failed_handoffs) > 0 else 0
        
        return {
            "workflow_success_rate": workflow_success_rate,
            "phase_success_rate": phase_success_rate,
            "task_success_rate": task_success_rate,
            "handoff_success_rate": handoff_success_rate,
            "overall_success_rate": (workflow_success_rate + phase_success_rate + task_success_rate) / 3
        }

    def is_performing_well(self, threshold: float = 0.8) -> bool:
        """Check if agent is performing above threshold"""
        success_rates = self.calculate_success_rates()
        return success_rates["overall_success_rate"] >= threshold and self.utilization_percentage >= 0.7