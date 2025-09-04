"""
SubForge API routes for workflow monitoring and integration
"""

import logging
from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from ..models.subforge_models import (
        WorkflowContext,
        WorkflowMetrics,
        WorkflowSummary,
    )
    from ..services.subforge_integration import subforge_integration
    from ..websocket.manager import websocket_manager
except ImportError:
    # Fallback for direct execution
    from models.subforge_models import (
        WorkflowContext,
        WorkflowMetrics,
        WorkflowSummary,
    )
    from services.subforge_integration import subforge_integration
    from websocket.manager import websocket_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/subforge", tags=["subforge"])


class ScanRequest(BaseModel):
    """Request model for scan operations"""

    force_rescan: bool = False
    include_inactive: bool = True


class WebSocketMessage(BaseModel):
    """WebSocket message model"""

    type: str
    data: Dict[str, Any]


@router.get("/workflows", response_model=List[WorkflowSummary])
async def get_workflows():
    """
    Get list of all SubForge workflows with summary information
    """
    try:
        workflows = subforge_integration.get_workflows()
        logger.info(f"Retrieved {len(workflows)} workflows")
        return workflows

    except Exception as e:
        logger.error(f"Error retrieving workflows: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflows")


@router.get("/workflow/{workflow_id}", response_model=WorkflowContext)
async def get_workflow(workflow_id: str):
    """
    Get detailed information about a specific workflow
    """
    try:
        workflow = subforge_integration.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=404, detail=f"Workflow '{workflow_id}' not found"
            )

        logger.info(f"Retrieved workflow: {workflow_id}")
        return workflow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow")


@router.get("/workflow/{workflow_id}/context", response_model=Dict[str, Any])
async def get_workflow_context(workflow_id: str):
    """
    Get the raw workflow context for a specific workflow
    """
    try:
        workflow = subforge_integration.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=404, detail=f"Workflow '{workflow_id}' not found"
            )

        # Return as dictionary with additional metadata
        context_data = workflow.dict()
        context_data["_metadata"] = {
            "retrieved_at": workflow.updated_at or workflow.created_at,
            "workflow_id": workflow_id,
            "api_version": "1.0",
        }

        logger.info(f"Retrieved context for workflow: {workflow_id}")
        return context_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving context for workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve workflow context"
        )


@router.get("/workflow/{workflow_id}/phases")
async def get_workflow_phases(workflow_id: str):
    """
    Get phase information for a specific workflow
    """
    try:
        workflow = subforge_integration.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=404, detail=f"Workflow '{workflow_id}' not found"
            )

        phases_data = []
        for phase_name, phase_result in workflow.phase_results.items():
            phases_data.append(
                {
                    "name": phase_name,
                    "status": phase_result.status,
                    "duration": phase_result.duration,
                    "start_time": phase_result.start_time,
                    "end_time": phase_result.end_time,
                    "outputs": phase_result.outputs,
                    "errors": phase_result.errors,
                    "warnings": phase_result.warnings,
                }
            )

        response_data = {
            "workflow_id": workflow_id,
            "total_phases": len(phases_data),
            "completed_phases": len(workflow.get_completed_phases()),
            "failed_phases": len(workflow.get_failed_phases()),
            "current_phase": workflow.get_current_phase(),
            "phases": phases_data,
        }

        logger.info(f"Retrieved phases for workflow: {workflow_id}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving phases for workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve workflow phases"
        )


@router.get("/workflow/{workflow_id}/tasks")
async def get_workflow_tasks(workflow_id: str):
    """
    Get tasks for a specific workflow
    """
    try:
        workflow = subforge_integration.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=404, detail=f"Workflow '{workflow_id}' not found"
            )

        tasks_data = []
        for task in workflow.tasks:
            tasks_data.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "phase": task.phase,
                    "assigned_agent": task.assigned_agent,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "completed_at": task.completed_at,
                    "duration": task.duration,
                    "dependencies": task.dependencies,
                    "tags": task.tags,
                }
            )

        response_data = {
            "workflow_id": workflow_id,
            "total_tasks": len(tasks_data),
            "tasks": tasks_data,
        }

        logger.info(f"Retrieved tasks for workflow: {workflow_id}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tasks for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow tasks")


@router.get("/workflow/{workflow_id}/activities")
async def get_workflow_activities(workflow_id: str):
    """
    Get agent activities for a specific workflow
    """
    try:
        workflow = subforge_integration.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=404, detail=f"Workflow '{workflow_id}' not found"
            )

        activities_data = []
        for activity in workflow.agent_activities:
            activities_data.append(
                {
                    "agent_id": activity.agent_id,
                    "agent_name": activity.agent_name,
                    "activity_type": activity.activity_type,
                    "description": activity.description,
                    "timestamp": activity.timestamp,
                    "duration": activity.duration,
                    "status": activity.status,
                    "task_id": activity.task_id,
                    "metadata": activity.metadata,
                }
            )

        response_data = {
            "workflow_id": workflow_id,
            "total_activities": len(activities_data),
            "activities": activities_data,
        }

        logger.info(f"Retrieved activities for workflow: {workflow_id}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving activities for workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve workflow activities"
        )


@router.post("/scan")
async def scan_workflows(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Trigger a scan of SubForge workflows
    """
    try:
        # Add scan task to background
        background_tasks.add_task(_perform_scan, request.force_rescan)

        return JSONResponse(
            status_code=202,
            content={
                "message": "Scan initiated successfully",
                "scan_type": "force" if request.force_rescan else "incremental",
                "status": "processing",
            },
        )

    except Exception as e:
        logger.error(f"Error initiating scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate scan")


async def _perform_scan(force_rescan: bool = False):
    """Background task to perform workflow scan"""
    try:
        logger.info(f"Starting workflow scan (force: {force_rescan})")

        if force_rescan:
            # Clear existing workflows for force rescan
            subforge_integration.workflows.clear()

        discovered_workflows = await subforge_integration.scan_workflows()

        # Broadcast scan completion
        await websocket_manager.broadcast_json(
            {
                "type": "subforge_scan_complete",
                "data": {
                    "discovered_count": len(discovered_workflows),
                    "workflows": discovered_workflows,
                    "scan_type": "force" if force_rescan else "incremental",
                },
            }
        )

        logger.info(f"Scan completed: {len(discovered_workflows)} workflows found")

    except Exception as e:
        logger.error(f"Error in scan task: {e}")

        # Broadcast scan error
        await websocket_manager.broadcast_json(
            {
                "type": "subforge_scan_error",
                "data": {
                    "error": str(e),
                    "scan_type": "force" if force_rescan else "incremental",
                },
            }
        )


@router.get("/metrics", response_model=WorkflowMetrics)
async def get_workflow_metrics():
    """
    Get aggregated metrics across all workflows
    """
    try:
        metrics = subforge_integration.get_workflow_metrics()
        logger.info("Retrieved workflow metrics")
        return metrics

    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve workflow metrics"
        )


@router.get("/status")
async def get_integration_status():
    """
    Get status of the SubForge integration service
    """
    try:
        is_monitoring = subforge_integration.monitoring_task is not None
        is_file_watching = (
            subforge_integration.observer is not None
            and subforge_integration.observer.is_alive()
        )

        status_data = {
            "service_status": "active" if is_monitoring else "inactive",
            "monitoring_enabled": is_monitoring,
            "file_watching_enabled": is_file_watching,
            "total_workflows": len(subforge_integration.workflows),
            "active_workflows": len(
                [
                    w
                    for w in subforge_integration.workflows.values()
                    if w.status == "active"
                ]
            ),
            "subforge_directory": str(subforge_integration.subforge_dir),
            "subforge_directory_exists": subforge_integration.subforge_dir.exists(),
            "last_scan": (
                subforge_integration._last_scan.isoformat()
                if subforge_integration._last_scan
                else None
            ),
            "configuration": {
                "scan_interval": subforge_integration.config.scan_interval,
                "max_workflows": subforge_integration.config.max_workflows,
                "cleanup_after_days": subforge_integration.config.cleanup_after_days,
                "enable_real_time_monitoring": subforge_integration.config.enable_real_time_monitoring,
            },
        }

        return status_data

    except Exception as e:
        logger.error(f"Error retrieving integration status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve integration status"
        )


@router.post("/start")
async def start_integration():
    """
    Start the SubForge integration monitoring
    """
    try:
        if subforge_integration.monitoring_task is not None:
            return JSONResponse(
                content={"message": "Integration already running", "status": "active"}
            )

        await subforge_integration.start_monitoring()

        return JSONResponse(
            content={"message": "Integration started successfully", "status": "active"}
        )

    except Exception as e:
        logger.error(f"Error starting integration: {e}")
        raise HTTPException(status_code=500, detail="Failed to start integration")


@router.post("/stop")
async def stop_integration():
    """
    Stop the SubForge integration monitoring
    """
    try:
        await subforge_integration.stop_monitoring()

        return JSONResponse(
            content={
                "message": "Integration stopped successfully",
                "status": "inactive",
            }
        )

    except Exception as e:
        logger.error(f"Error stopping integration: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop integration")


@router.websocket("/ws")
async def subforge_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time SubForge updates
    """
    client_info = {
        "host": websocket.client.host if websocket.client else "unknown",
        "user_agent": websocket.headers.get("user-agent", "unknown"),
        "endpoint": "subforge",
    }

    await websocket_manager.connect(websocket, client_info)

    try:
        # Send initial data
        workflows = subforge_integration.get_workflows()
        await websocket_manager.send_personal_message(
            websocket,
            {
                "type": "subforge_initial_data",
                "data": {
                    "workflows": [w.dict() for w in workflows],
                    "metrics": subforge_integration.get_workflow_metrics().dict(),
                    "status": "connected",
                },
            },
        )

        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            message_type = data.get("type", "unknown")

            if message_type == "ping":
                await websocket_manager.send_personal_message(
                    websocket,
                    {"type": "pong", "data": {"timestamp": data.get("timestamp")}},
                )

            elif message_type == "subscribe_workflow":
                workflow_id = data.get("workflow_id")
                if workflow_id:
                    # Send specific workflow data
                    workflow = subforge_integration.get_workflow(workflow_id)
                    if workflow:
                        await websocket_manager.send_personal_message(
                            websocket,
                            {
                                "type": "workflow_subscribed",
                                "data": {
                                    "workflow_id": workflow_id,
                                    "workflow": workflow.dict(),
                                },
                            },
                        )

            elif message_type == "unsubscribe_workflow":
                workflow_id = data.get("workflow_id")
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "workflow_unsubscribed",
                        "data": {"workflow_id": workflow_id},
                    },
                )

            else:
                logger.info(
                    f"Received unhandled SubForge WebSocket message: {message_type}"
                )

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"SubForge WebSocket error: {e}")
        websocket_manager.disconnect(websocket)