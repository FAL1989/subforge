"""
Persistence service for storing SubForge workflow history and analytics data
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import (
    AgentPerformanceMetrics,
    HandoffHistory,
    PhaseHistory,
    WorkflowHistory,
)

logger = logging.getLogger(__name__)


class PersistenceService:
    """
    Service for persisting and querying SubForge workflow history and metrics
    """

    def __init__(self):
        self.logger = logger

    async def store_workflow_execution(
        self,
        session: AsyncSession,
        workflow_data: Dict[str, Any],
        execution_metadata: Dict[str, Any] = None,
    ) -> WorkflowHistory:
        """
        Store a complete workflow execution in the history

        Args:
            session: Database session
            workflow_data: Complete workflow execution data
            execution_metadata: Additional metadata about the execution

        Returns:
            WorkflowHistory: Created workflow history record
        """
        try:
            # Create workflow history record
            workflow_history = WorkflowHistory(
                workflow_id=workflow_data.get("workflow_id"),
                execution_id=workflow_data.get("execution_id", str(uuid.uuid4())),
                execution_number=workflow_data.get("execution_number", 1),
                workflow_name=workflow_data.get("name", "Unknown Workflow"),
                workflow_type=workflow_data.get("type", "default"),
                project_id=workflow_data.get("project_id"),
                project_name=workflow_data.get("project_name"),
                status=workflow_data.get("status", "completed"),
                final_result=workflow_data.get("final_result", "success"),
                started_at=workflow_data.get("started_at", datetime.utcnow()),
                completed_at=workflow_data.get("completed_at"),
                duration_seconds=workflow_data.get("duration_seconds"),
                total_phases=workflow_data.get("total_phases", 0),
                completed_phases=workflow_data.get("completed_phases", 0),
                failed_phases=workflow_data.get("failed_phases", 0),
                skipped_phases=workflow_data.get("skipped_phases", 0),
                total_tasks=workflow_data.get("total_tasks", 0),
                completed_tasks=workflow_data.get("completed_tasks", 0),
                failed_tasks=workflow_data.get("failed_tasks", 0),
                success_rate=workflow_data.get("success_rate", 0.0),
                quality_score=workflow_data.get("quality_score"),
                efficiency_score=workflow_data.get("efficiency_score"),
                configuration=workflow_data.get("configuration", {}),
                parameters=workflow_data.get("parameters", {}),
                environment_info=execution_metadata or {},
                assigned_agents=workflow_data.get("assigned_agents", []),
                agent_performance_summary=workflow_data.get(
                    "agent_performance_summary", {}
                ),
                error_messages=workflow_data.get("error_messages", []),
                warnings=workflow_data.get("warnings", []),
                critical_issues=workflow_data.get("critical_issues", []),
                resource_usage=workflow_data.get("resource_usage", {}),
                triggered_by=workflow_data.get("triggered_by"),
                trigger_event=workflow_data.get("trigger_event"),
            )

            session.add(workflow_history)
            await session.flush()

            self.logger.info(
                f"Stored workflow execution history: {workflow_history.id}"
            )
            return workflow_history

        except Exception as e:
            self.logger.error(f"Error storing workflow execution: {str(e)}")
            await session.rollback()
            raise

    async def store_phase_execution(
        self,
        session: AsyncSession,
        workflow_history_id: uuid.UUID,
        phase_data: Dict[str, Any],
    ) -> PhaseHistory:
        """
        Store a phase execution record

        Args:
            session: Database session
            workflow_history_id: ID of the parent workflow history
            phase_data: Phase execution data

        Returns:
            PhaseHistory: Created phase history record
        """
        try:
            phase_history = PhaseHistory(
                workflow_history_id=workflow_history_id,
                phase_name=phase_data.get("name", "Unknown Phase"),
                phase_type=phase_data.get("type", "default"),
                phase_order=phase_data.get("order", 0),
                status=phase_data.get("status", "completed"),
                result=phase_data.get("result", "success"),
                started_at=phase_data.get("started_at"),
                completed_at=phase_data.get("completed_at"),
                duration_seconds=phase_data.get("duration_seconds"),
                assigned_agent_id=phase_data.get("assigned_agent_id"),
                assigned_agent_name=phase_data.get("assigned_agent_name"),
                agent_utilization=phase_data.get("agent_utilization"),
                phase_config=phase_data.get("config", {}),
                input_parameters=phase_data.get("input_parameters", {}),
                output_results=phase_data.get("output_results", {}),
                quality_score=phase_data.get("quality_score"),
                performance_score=phase_data.get("performance_score"),
                total_tasks=phase_data.get("total_tasks", 0),
                completed_tasks=phase_data.get("completed_tasks", 0),
                failed_tasks=phase_data.get("failed_tasks", 0),
                dependencies=phase_data.get("dependencies", []),
                dependents=phase_data.get("dependents", []),
                error_messages=phase_data.get("error_messages", []),
                warnings=phase_data.get("warnings", []),
                resource_usage=phase_data.get("resource_usage", {}),
            )

            session.add(phase_history)
            await session.flush()

            self.logger.info(f"Stored phase execution history: {phase_history.id}")
            return phase_history

        except Exception as e:
            self.logger.error(f"Error storing phase execution: {str(e)}")
            await session.rollback()
            raise

    async def store_handoff_execution(
        self,
        session: AsyncSession,
        workflow_history_id: uuid.UUID,
        handoff_data: Dict[str, Any],
    ) -> HandoffHistory:
        """
        Store a handoff execution record

        Args:
            session: Database session
            workflow_history_id: ID of the parent workflow history
            handoff_data: Handoff execution data

        Returns:
            HandoffHistory: Created handoff history record
        """
        try:
            handoff_history = HandoffHistory(
                workflow_history_id=workflow_history_id,
                handoff_name=handoff_data.get("name", "Unknown Handoff"),
                handoff_type=handoff_data.get("type", "phase_to_phase"),
                source_phase_name=handoff_data.get("source_phase_name"),
                target_phase_name=handoff_data.get("target_phase_name"),
                source_agent_id=handoff_data.get("source_agent_id"),
                target_agent_id=handoff_data.get("target_agent_id"),
                status=handoff_data.get("status", "completed"),
                result=handoff_data.get("result", "success"),
                initiated_at=handoff_data.get("initiated_at", datetime.utcnow()),
                completed_at=handoff_data.get("completed_at"),
                duration_seconds=handoff_data.get("duration_seconds"),
                handoff_data=handoff_data.get("handoff_data", {}),
                validation_rules=handoff_data.get("validation_rules", {}),
                validation_results=handoff_data.get("validation_results", {}),
                data_quality_score=handoff_data.get("data_quality_score"),
                handoff_efficiency_score=handoff_data.get("handoff_efficiency_score"),
                error_messages=handoff_data.get("error_messages", []),
                warnings=handoff_data.get("warnings", []),
                validation_failures=handoff_data.get("validation_failures", []),
                context_info=handoff_data.get("context_info", {}),
                handoff_metadata=handoff_data.get("metadata", {}),
            )

            session.add(handoff_history)
            await session.flush()

            self.logger.info(f"Stored handoff execution history: {handoff_history.id}")
            return handoff_history

        except Exception as e:
            self.logger.error(f"Error storing handoff execution: {str(e)}")
            await session.rollback()
            raise

    async def calculate_and_store_agent_performance(
        self,
        session: AsyncSession,
        agent_id: str,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "day",
    ) -> AgentPerformanceMetrics:
        """
        Calculate and store agent performance metrics for a given period

        Args:
            session: Database session
            agent_id: Agent identifier
            period_start: Start of the measurement period
            period_end: End of the measurement period
            period_type: Type of period (hour, day, week, month)

        Returns:
            AgentPerformanceMetrics: Created performance metrics record
        """
        try:
            # Get agent data from phase history
            phase_query = select(PhaseHistory).where(
                and_(
                    PhaseHistory.assigned_agent_id == agent_id,
                    PhaseHistory.started_at >= period_start,
                    PhaseHistory.started_at <= period_end,
                )
            )
            phase_results = await session.execute(phase_query)
            phases = phase_results.scalars().all()

            # Get handoff data
            handoff_query = select(HandoffHistory).where(
                and_(
                    or_(
                        HandoffHistory.source_agent_id == agent_id,
                        HandoffHistory.target_agent_id == agent_id,
                    ),
                    HandoffHistory.initiated_at >= period_start,
                    HandoffHistory.initiated_at <= period_end,
                )
            )
            handoff_results = await session.execute(handoff_query)
            handoffs = handoff_results.scalars().all()

            # Get workflow data
            workflow_query = select(WorkflowHistory).where(
                and_(
                    WorkflowHistory.started_at >= period_start,
                    WorkflowHistory.started_at <= period_end,
                )
            )
            workflow_results = await session.execute(workflow_query)
            workflows = workflow_results.scalars().all()

            # Filter workflows where agent was involved
            agent_workflows = [
                w
                for w in workflows
                if any(agent.get("id") == agent_id for agent in w.assigned_agents)
            ]

            # Calculate metrics
            total_workflows = len(agent_workflows)
            successful_workflows = len(
                [w for w in agent_workflows if w.final_result == "success"]
            )
            failed_workflows = len(
                [w for w in agent_workflows if w.final_result == "failure"]
            )

            total_phases = len(phases)
            successful_phases = len([p for p in phases if p.result == "success"])
            failed_phases = len([p for p in phases if p.result == "failure"])

            # Calculate task metrics from phases
            total_tasks = sum(p.total_tasks for p in phases)
            successful_tasks = sum(p.completed_tasks for p in phases)
            failed_tasks = sum(p.failed_tasks for p in phases)

            # Calculate time metrics
            total_active_time = sum(
                p.duration_seconds for p in phases if p.duration_seconds is not None
            )

            avg_task_duration = (
                total_active_time / total_tasks if total_tasks > 0 else None
            )

            avg_phase_duration = (
                total_active_time / total_phases if total_phases > 0 else None
            )

            # Calculate quality metrics
            quality_scores = [
                p.quality_score for p in phases if p.quality_score is not None
            ]
            avg_quality_score = (
                sum(quality_scores) / len(quality_scores) if quality_scores else None
            )

            performance_scores = [
                p.performance_score for p in phases if p.performance_score is not None
            ]
            avg_performance_score = (
                sum(performance_scores) / len(performance_scores)
                if performance_scores
                else None
            )

            # Calculate handoff metrics
            source_handoffs = [h for h in handoffs if h.source_agent_id == agent_id]
            target_handoffs = [h for h in handoffs if h.target_agent_id == agent_id]

            successful_handoffs = len([h for h in handoffs if h.result == "success"])
            failed_handoffs = len([h for h in handoffs if h.result == "failure"])

            handoff_durations = [
                h.duration_seconds for h in handoffs if h.duration_seconds is not None
            ]
            avg_handoff_duration = (
                sum(handoff_durations) / len(handoff_durations)
                if handoff_durations
                else None
            )

            # Calculate utilization (simplified - based on active time vs period duration)
            period_duration = (period_end - period_start).total_seconds()
            utilization_percentage = (
                min(100.0, (total_active_time / period_duration) * 100)
                if period_duration > 0
                else 0.0
            )

            # Get agent name from phases (assuming it's consistent)
            agent_name = phases[0].assigned_agent_name if phases else agent_id

            # Create performance metrics record
            performance_metrics = AgentPerformanceMetrics(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_type="subforge_agent",  # Default type
                period_start=period_start,
                period_end=period_end,
                period_type=period_type,
                total_workflows=total_workflows,
                successful_workflows=successful_workflows,
                failed_workflows=failed_workflows,
                total_phases=total_phases,
                successful_phases=successful_phases,
                failed_phases=failed_phases,
                total_tasks=total_tasks,
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                total_active_time_seconds=total_active_time,
                average_task_duration_seconds=avg_task_duration,
                average_phase_duration_seconds=avg_phase_duration,
                average_quality_score=avg_quality_score,
                average_performance_score=avg_performance_score,
                utilization_percentage=utilization_percentage,
                idle_time_seconds=max(0, period_duration - total_active_time),
                successful_handoffs=successful_handoffs,
                failed_handoffs=failed_handoffs,
                average_handoff_time_seconds=avg_handoff_duration,
                calculated_at=datetime.utcnow(),
            )

            session.add(performance_metrics)
            await session.flush()

            self.logger.info(
                f"Calculated and stored agent performance metrics: {performance_metrics.id}"
            )
            return performance_metrics

        except Exception as e:
            self.logger.error(f"Error calculating agent performance: {str(e)}")
            await session.rollback()
            raise

    async def get_workflow_history(
        self,
        session: AsyncSession,
        workflow_id: Optional[uuid.UUID] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        status_filter: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Tuple[List[WorkflowHistory], int]:
        """
        Get workflow history records with optional filtering

        Args:
            session: Database session
            workflow_id: Filter by specific workflow ID
            project_id: Filter by project ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            status_filter: Filter by status
            date_range: Filter by date range (start, end)

        Returns:
            Tuple[List[WorkflowHistory], int]: List of workflow history records and total count
        """
        try:
            # Build query
            query = select(WorkflowHistory)
            count_query = select(func.count(WorkflowHistory.id))

            # Apply filters
            conditions = []
            if workflow_id:
                conditions.append(WorkflowHistory.workflow_id == workflow_id)
            if project_id:
                conditions.append(WorkflowHistory.project_id == project_id)
            if status_filter:
                conditions.append(WorkflowHistory.status == status_filter)
            if date_range:
                start_date, end_date = date_range
                conditions.append(WorkflowHistory.started_at >= start_date)
                conditions.append(WorkflowHistory.started_at <= end_date)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

            # Apply ordering, limit, and offset
            query = query.order_by(desc(WorkflowHistory.started_at))
            query = query.offset(offset).limit(limit)

            # Execute queries
            result = await session.execute(query)
            workflows = result.scalars().all()

            count_result = await session.execute(count_query)
            total_count = count_result.scalar()

            return workflows, total_count

        except Exception as e:
            self.logger.error(f"Error getting workflow history: {str(e)}")
            raise

    async def get_agent_performance_metrics(
        self,
        session: AsyncSession,
        agent_id: Optional[str] = None,
        period_type: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 100,
    ) -> List[AgentPerformanceMetrics]:
        """
        Get agent performance metrics with optional filtering

        Args:
            session: Database session
            agent_id: Filter by specific agent ID
            period_type: Filter by period type (hour, day, week, month)
            date_range: Filter by date range
            limit: Maximum number of records to return

        Returns:
            List[AgentPerformanceMetrics]: List of agent performance metrics
        """
        try:
            query = select(AgentPerformanceMetrics)

            conditions = []
            if agent_id:
                conditions.append(AgentPerformanceMetrics.agent_id == agent_id)
            if period_type:
                conditions.append(AgentPerformanceMetrics.period_type == period_type)
            if date_range:
                start_date, end_date = date_range
                conditions.append(AgentPerformanceMetrics.period_start >= start_date)
                conditions.append(AgentPerformanceMetrics.period_end <= end_date)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(AgentPerformanceMetrics.period_start))
            query = query.limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

        except Exception as e:
            self.logger.error(f"Error getting agent performance metrics: {str(e)}")
            raise

    async def get_workflow_analytics_summary(
        self,
        session: AsyncSession,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics summary for workflows

        Args:
            session: Database session
            date_range: Optional date range filter

        Returns:
            Dict[str, Any]: Analytics summary
        """
        try:
            # Build base query
            query = select(WorkflowHistory)

            if date_range:
                start_date, end_date = date_range
                query = query.where(
                    and_(
                        WorkflowHistory.started_at >= start_date,
                        WorkflowHistory.started_at <= end_date,
                    )
                )

            result = await session.execute(query)
            workflows = result.scalars().all()

            if not workflows:
                return {
                    "total_workflows": 0,
                    "success_rate": 0.0,
                    "average_duration": 0.0,
                    "total_tasks": 0,
                    "performance_summary": {},
                }

            # Calculate summary metrics
            total_workflows = len(workflows)
            successful_workflows = len(
                [w for w in workflows if w.final_result == "success"]
            )
            success_rate = (
                successful_workflows / total_workflows if total_workflows > 0 else 0.0
            )

            durations = [
                w.duration_seconds for w in workflows if w.duration_seconds is not None
            ]
            average_duration = sum(durations) / len(durations) if durations else 0.0

            total_tasks = sum(w.total_tasks for w in workflows)
            completed_tasks = sum(w.completed_tasks for w in workflows)

            quality_scores = [
                w.quality_score for w in workflows if w.quality_score is not None
            ]
            average_quality = (
                sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            )

            efficiency_scores = [
                w.efficiency_score for w in workflows if w.efficiency_score is not None
            ]
            average_efficiency = (
                sum(efficiency_scores) / len(efficiency_scores)
                if efficiency_scores
                else 0.0
            )

            return {
                "total_workflows": total_workflows,
                "successful_workflows": successful_workflows,
                "failed_workflows": total_workflows - successful_workflows,
                "success_rate": success_rate,
                "average_duration_seconds": average_duration,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "task_completion_rate": (
                    completed_tasks / total_tasks if total_tasks > 0 else 0.0
                ),
                "average_quality_score": average_quality,
                "average_efficiency_score": average_efficiency,
                "period_start": date_range[0].isoformat() if date_range else None,
                "period_end": date_range[1].isoformat() if date_range else None,
            }

        except Exception as e:
            self.logger.error(f"Error getting workflow analytics summary: {str(e)}")
            raise

    async def cleanup_old_records(
        self, session: AsyncSession, retention_days: int = 90
    ) -> Dict[str, int]:
        """
        Clean up old historical records beyond retention period

        Args:
            session: Database session
            retention_days: Number of days to retain

        Returns:
            Dict[str, int]: Count of deleted records by type
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Delete old workflow history (cascades to phases and handoffs)
            workflow_query = select(WorkflowHistory).where(
                WorkflowHistory.started_at < cutoff_date
            )
            workflow_result = await session.execute(workflow_query)
            old_workflows = workflow_result.scalars().all()

            workflow_count = len(old_workflows)
            for workflow in old_workflows:
                await session.delete(workflow)

            # Delete old agent performance metrics
            metrics_query = select(AgentPerformanceMetrics).where(
                AgentPerformanceMetrics.period_start < cutoff_date
            )
            metrics_result = await session.execute(metrics_query)
            old_metrics = metrics_result.scalars().all()

            metrics_count = len(old_metrics)
            for metric in old_metrics:
                await session.delete(metric)

            await session.commit()

            self.logger.info(
                f"Cleaned up {workflow_count} old workflow records and {metrics_count} old metric records"
            )

            return {
                "workflow_history_deleted": workflow_count,
                "performance_metrics_deleted": metrics_count,
            }

        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {str(e)}")
            await session.rollback()
            raise


# Global instance
persistence_service = PersistenceService()