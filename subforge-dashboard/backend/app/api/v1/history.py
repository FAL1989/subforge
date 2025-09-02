"""
History API endpoints for SubForge Dashboard
Provides access to workflow history and analytics data
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.session import get_db
from ...services.persistence import persistence_service
from ...models.database import WorkflowHistory, PhaseHistory, HandoffHistory, AgentPerformanceMetrics

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/workflows")
async def get_workflow_history(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status_filter: Optional[str] = Query(None, description="Filter by workflow status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter")
):
    """
    Get workflow execution history with optional filtering
    
    Returns paginated list of workflow history records
    """
    try:
        date_range = None
        if start_date or end_date:
            start = start_date or datetime.utcnow() - timedelta(days=30)
            end = end_date or datetime.utcnow()
            date_range = (start, end)
        
        workflows, total_count = await persistence_service.get_workflow_history(
            db, 
            project_id=project_id,
            limit=limit,
            offset=offset,
            status_filter=status_filter,
            date_range=date_range
        )
        
        return {
            "workflows": [workflow.to_dict() for workflow in workflows],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving workflow history: {str(e)}")


@router.get("/workflows/{workflow_history_id}")
async def get_workflow_history_detail(
    workflow_history_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed workflow history including phases and handoffs
    """
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Get workflow history with related data
        query = select(WorkflowHistory).where(
            WorkflowHistory.id == workflow_history_id
        ).options(
            selectinload(WorkflowHistory.phases),
            selectinload(WorkflowHistory.handoffs)
        )
        
        result = await db.execute(query)
        workflow_history = result.scalar_one_or_none()
        
        if not workflow_history:
            raise HTTPException(status_code=404, detail="Workflow history not found")
        
        # Convert to dictionary with full detail
        workflow_data = workflow_history.to_dict()
        workflow_data["phases"] = [phase.to_dict() for phase in workflow_history.phases]
        workflow_data["handoffs"] = [handoff.to_dict() for handoff in workflow_history.handoffs]
        
        return workflow_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving workflow detail: {str(e)}")


@router.get("/agents/performance")
async def get_agent_performance_history(
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    period_type: Optional[str] = Query(None, description="Filter by period type (hour, day, week, month)"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Get agent performance metrics history
    
    Returns performance metrics for agents over time
    """
    try:
        date_range = None
        if start_date or end_date:
            start = start_date or datetime.utcnow() - timedelta(days=7)
            end = end_date or datetime.utcnow()
            date_range = (start, end)
        
        metrics = await persistence_service.get_agent_performance_metrics(
            db,
            agent_id=agent_id,
            period_type=period_type,
            date_range=date_range,
            limit=limit
        )
        
        return {
            "metrics": [metric.to_dict() for metric in metrics],
            "summary": {
                "total_records": len(metrics),
                "agents_covered": len(set(m.agent_id for m in metrics)),
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving agent performance: {str(e)}")


@router.get("/analytics/summary")
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics")
):
    """
    Get aggregated analytics summary for workflows
    
    Returns high-level metrics and KPIs
    """
    try:
        date_range = None
        if start_date or end_date:
            start = start_date or datetime.utcnow() - timedelta(days=30)
            end = end_date or datetime.utcnow()
            date_range = (start, end)
        
        summary = await persistence_service.get_workflow_analytics_summary(
            db, date_range=date_range
        )
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics summary: {str(e)}")


@router.get("/phases")
async def get_phase_history(
    db: AsyncSession = Depends(get_db),
    workflow_history_id: Optional[str] = Query(None, description="Filter by workflow history ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status_filter: Optional[str] = Query(None, description="Filter by phase status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Get phase execution history
    """
    try:
        from sqlalchemy import select, and_
        
        query = select(PhaseHistory)
        conditions = []
        
        if workflow_history_id:
            conditions.append(PhaseHistory.workflow_history_id == workflow_history_id)
        if agent_id:
            conditions.append(PhaseHistory.assigned_agent_id == agent_id)
        if status_filter:
            conditions.append(PhaseHistory.status == status_filter)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(PhaseHistory.started_at.desc()).limit(limit)
        
        result = await db.execute(query)
        phases = result.scalars().all()
        
        return {
            "phases": [phase.to_dict() for phase in phases],
            "total_records": len(phases)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving phase history: {str(e)}")


@router.get("/handoffs")
async def get_handoff_history(
    db: AsyncSession = Depends(get_db),
    workflow_history_id: Optional[str] = Query(None, description="Filter by workflow history ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID (source or target)"),
    status_filter: Optional[str] = Query(None, description="Filter by handoff status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Get handoff execution history
    """
    try:
        from sqlalchemy import select, and_, or_
        
        query = select(HandoffHistory)
        conditions = []
        
        if workflow_history_id:
            conditions.append(HandoffHistory.workflow_history_id == workflow_history_id)
        if agent_id:
            conditions.append(
                or_(
                    HandoffHistory.source_agent_id == agent_id,
                    HandoffHistory.target_agent_id == agent_id
                )
            )
        if status_filter:
            conditions.append(HandoffHistory.status == status_filter)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(HandoffHistory.initiated_at.desc()).limit(limit)
        
        result = await db.execute(query)
        handoffs = result.scalars().all()
        
        return {
            "handoffs": [handoff.to_dict() for handoff in handoffs],
            "total_records": len(handoffs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving handoff history: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_records(
    db: AsyncSession = Depends(get_db),
    retention_days: int = Query(90, ge=1, le=365, description="Number of days to retain")
):
    """
    Clean up old historical records beyond retention period
    
    Requires appropriate permissions
    """
    try:
        result = await persistence_service.cleanup_old_records(
            db, retention_days=retention_days
        )
        
        return {
            "message": "Cleanup completed successfully",
            "deleted_records": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")


@router.post("/agents/{agent_id}/performance")
async def calculate_agent_performance(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for calculation"),
    end_date: Optional[datetime] = Query(None, description="End date for calculation"),
    period_type: str = Query("day", description="Period type for calculation")
):
    """
    Manually trigger agent performance calculation for a specific period
    """
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=1)
        if not end_date:
            end_date = datetime.utcnow()
        
        metrics = await persistence_service.calculate_and_store_agent_performance(
            db, agent_id, start_date, end_date, period_type
        )
        
        return {
            "message": "Performance calculation completed",
            "metrics": metrics.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating performance: {str(e)}")