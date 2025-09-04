"""
Enhanced Agents API v2 with advanced features
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...services.api_enhancement import (
    api_enhancement_service,
    get_current_user,
    require_auth,
)
from ...services.background_tasks import TaskPriority, background_task_service
from ...services.redis_service import redis_service
from ...websocket.enhanced_manager import MessageType, enhanced_websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# Enhanced Pydantic models
class AgentConfiguration(BaseModel):
    model: str = "claude-3-sonnet"
    tools: List[str] = Field(default_factory=lambda: ["read", "write", "edit"])
    capabilities: List[str] = Field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 300
    custom_instructions: Optional[str] = None
    environment_vars: Dict[str, str] = Field(default_factory=dict)


class AgentMetrics(BaseModel):
    tasks_completed: int = 0
    tasks_failed: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    total_runtime: float = 0.0
    last_activity: Optional[datetime] = None
    error_count: int = 0
    uptime_percentage: float = 100.0


class Agent(BaseModel):
    id: str
    name: str
    type: str
    status: str = "active"
    current_task: Optional[str] = None
    configuration: AgentConfiguration = Field(default_factory=AgentConfiguration)
    metrics: AgentMetrics = Field(default_factory=AgentMetrics)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentCreateRequest(BaseModel):
    name: str
    type: str
    configuration: Optional[AgentConfiguration] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    current_task: Optional[str] = None
    configuration: Optional[AgentConfiguration] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class BulkAgentOperation(BaseModel):
    agent_ids: List[str]
    operation: str  # "start", "stop", "restart", "delete", "update"
    parameters: Optional[Dict[str, Any]] = None


class AgentSearchFilters(BaseModel):
    status: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


# Utility functions
async def get_agent_from_cache_or_storage(agent_id: str) -> Optional[Agent]:
    """Get agent from cache or storage"""
    # Try Redis cache first
    cached_agent = await redis_service.hget("agents", agent_id)
    if cached_agent:
        return Agent(**cached_agent)

    # TODO: Get from database if not in cache
    return None


async def cache_agent(agent: Agent):
    """Cache agent data"""
    await redis_service.hset("agents", agent.id, agent.dict())


async def invalidate_agent_cache(agent_id: Optional[str] = None):
    """Invalidate agent cache"""
    if agent_id:
        await redis_service.hdel("agents", agent_id)
    else:
        # Invalidate all agent cache
        await redis_service.delete("agents")


# API Endpoints


@router.get(
    "/",
    response_model=List[Agent],
    summary="List all agents with advanced filtering and pagination",
)
@api_enhancement_service.cache_response(ttl=60, prefix="agents_list")
@api_enhancement_service.rate_limit(requests_per_minute=100)
async def list_agents(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of agents to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of agents to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by agent type"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    search: Optional[str] = Query(
        None, description="Search in agent names and descriptions"
    ),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
):
    """List all agents with advanced filtering and pagination"""
    try:
        # Build search filters
        filters = AgentSearchFilters()
        if status:
            filters.status = status
        if type:
            filters.type = type
        if tags:
            filters.tags = [tag.strip() for tag in tags.split(",")]

        # Get agents from cache/storage
        all_agents_data = await redis_service.hgetall("agents")
        agents = []

        for agent_id, agent_data in all_agents_data.items():
            try:
                agent = Agent(**agent_data)

                # Apply filters
                if filters.status and agent.status != filters.status:
                    continue
                if filters.type and agent.type != filters.type:
                    continue
                if filters.tags and not any(tag in agent.tags for tag in filters.tags):
                    continue
                if search and search.lower() not in agent.name.lower():
                    continue

                agents.append(agent)

            except Exception as e:
                logger.warning(f"Error parsing agent data for {agent_id}: {e}")

        # Sort agents
        reverse_sort = sort_order == "desc"
        if sort_by == "name":
            agents.sort(key=lambda a: a.name.lower(), reverse=reverse_sort)
        elif sort_by == "status":
            agents.sort(key=lambda a: a.status, reverse=reverse_sort)
        elif sort_by == "updated_at":
            agents.sort(key=lambda a: a.updated_at, reverse=reverse_sort)
        else:  # default to created_at
            agents.sort(key=lambda a: a.created_at, reverse=reverse_sort)

        # Apply pagination
        total_count = len(agents)
        paginated_agents = agents[skip : skip + limit]

        # Add pagination headers
        response_headers = {
            "X-Total-Count": str(total_count),
            "X-Page-Size": str(limit),
            "X-Current-Page": str(skip // limit + 1),
            "X-Total-Pages": str((total_count + limit - 1) // limit),
        }

        return JSONResponse(
            content=[agent.dict() for agent in paginated_agents],
            headers=response_headers,
        )

    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents",
        )


@router.get(
    "/{agent_id}",
    response_model=Agent,
    summary="Get agent by ID with detailed information",
)
@api_enhancement_service.cache_response(ttl=30, prefix="agent_detail")
@api_enhancement_service.rate_limit(requests_per_minute=200)
async def get_agent(agent_id: str, request: Request):
    """Get detailed information about a specific agent"""
    agent = await get_agent_from_cache_or_storage(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    return agent


@router.post(
    "/",
    response_model=Agent,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
)
@api_enhancement_service.rate_limit(requests_per_minute=20, per_user=True)
@require_auth
async def create_agent(
    request: AgentCreateRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks_service=Depends(lambda: background_task_service),
):
    """Create a new agent with configuration"""
    try:
        # Generate agent ID
        agent_id = str(uuid4())

        # Create agent
        agent = Agent(
            id=agent_id,
            name=request.name,
            type=request.type,
            configuration=request.configuration or AgentConfiguration(),
            tags=request.tags or [],
            metadata=request.metadata or {},
        )

        # Cache agent
        await cache_agent(agent)

        # Invalidate list cache
        await api_enhancement_service.invalidate_cache("agents_list")

        # Submit background task for agent initialization
        task_id = await background_task_service.submit_task(
            "process_agent_configuration",
            task_args=(agent_id, agent.configuration.dict()),
            priority=TaskPriority.HIGH,
            metadata={"agent_name": agent.name, "created_by": current_user.get("id")},
        )

        # Broadcast agent creation
        await enhanced_websocket_manager.broadcast_to_all(
            {
                "type": MessageType.AGENT_UPDATE,
                "data": {
                    "event": "agent_created",
                    "agent": agent.dict(),
                    "background_task_id": task_id,
                },
            }
        )

        logger.info(f"Created agent {agent_id}: {agent.name}")
        return agent

    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent",
        )


@router.put(
    "/{agent_id}",
    response_model=Agent,
    summary="Update agent configuration and properties",
)
@api_enhancement_service.rate_limit(requests_per_minute=50, per_user=True)
@require_auth
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing agent"""
    try:
        # Get existing agent
        agent = await get_agent_from_cache_or_storage(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        agent.updated_at = datetime.utcnow()

        # Cache updated agent
        await cache_agent(agent)

        # Invalidate caches
        await api_enhancement_service.invalidate_cache("agents_list")
        await api_enhancement_service.invalidate_cache("agent_detail")

        # Broadcast update
        await enhanced_websocket_manager.broadcast_to_all(
            {
                "type": MessageType.AGENT_UPDATE,
                "data": {
                    "event": "agent_updated",
                    "agent": agent.dict(),
                    "updated_by": current_user.get("id"),
                },
            }
        )

        logger.info(f"Updated agent {agent_id}")
        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent",
        )


@router.delete(
    "/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an agent"
)
@api_enhancement_service.rate_limit(requests_per_minute=20, per_user=True)
@require_auth
async def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an agent"""
    try:
        # Check if agent exists
        agent = await get_agent_from_cache_or_storage(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Remove from cache
        await invalidate_agent_cache(agent_id)

        # Invalidate list cache
        await api_enhancement_service.invalidate_cache("agents_list")

        # Broadcast deletion
        await enhanced_websocket_manager.broadcast_to_all(
            {
                "type": MessageType.AGENT_UPDATE,
                "data": {
                    "event": "agent_deleted",
                    "agent_id": agent_id,
                    "deleted_by": current_user.get("id"),
                },
            }
        )

        logger.info(f"Deleted agent {agent_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent",
        )


@router.post("/bulk-operation", summary="Perform bulk operations on multiple agents")
@api_enhancement_service.rate_limit(requests_per_minute=10, per_user=True)
@require_auth
async def bulk_agent_operation(
    request: BulkAgentOperation,
    current_user: dict = Depends(get_current_user),
    background_tasks_service=Depends(lambda: background_task_service),
):
    """Perform bulk operations on multiple agents"""
    try:
        results = []

        for agent_id in request.agent_ids:
            try:
                agent = await get_agent_from_cache_or_storage(agent_id)
                if not agent:
                    results.append(
                        {
                            "agent_id": agent_id,
                            "success": False,
                            "error": "Agent not found",
                        }
                    )
                    continue

                # Perform operation
                if request.operation == "start":
                    agent.status = "active"
                elif request.operation == "stop":
                    agent.status = "inactive"
                elif request.operation == "restart":
                    agent.status = "restarting"
                elif request.operation == "delete":
                    await invalidate_agent_cache(agent_id)
                    results.append(
                        {"agent_id": agent_id, "success": True, "action": "deleted"}
                    )
                    continue
                elif request.operation == "update" and request.parameters:
                    for field, value in request.parameters.items():
                        if hasattr(agent, field):
                            setattr(agent, field, value)

                agent.updated_at = datetime.utcnow()
                await cache_agent(agent)

                results.append(
                    {"agent_id": agent_id, "success": True, "action": request.operation}
                )

            except Exception as e:
                logger.error(f"Error in bulk operation for agent {agent_id}: {e}")
                results.append(
                    {"agent_id": agent_id, "success": False, "error": str(e)}
                )

        # Invalidate caches
        await api_enhancement_service.invalidate_cache("agents_list")

        # Broadcast bulk operation
        await enhanced_websocket_manager.broadcast_to_all(
            {
                "type": MessageType.AGENT_UPDATE,
                "data": {
                    "event": "bulk_operation",
                    "operation": request.operation,
                    "results": results,
                    "performed_by": current_user.get("id"),
                },
            }
        )

        return {
            "operation": request.operation,
            "total_agents": len(request.agent_ids),
            "successful": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error in bulk agent operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk operation",
        )


@router.post(
    "/{agent_id}/configuration/upload", summary="Upload agent configuration file"
)
@api_enhancement_service.rate_limit(requests_per_minute=10, per_user=True)
@require_auth
async def upload_agent_configuration(
    agent_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload and apply agent configuration from file"""
    try:
        # Validate file type
        if not file.filename.endswith((".json", ".yaml", ".yml")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON and YAML configuration files are supported",
            )

        # Get agent
        agent = await get_agent_from_cache_or_storage(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Read and parse configuration
        content = await file.read()

        if file.filename.endswith(".json"):
            import json

            config_data = json.loads(content.decode("utf-8"))
        else:  # YAML
            import yaml

            config_data = yaml.safe_load(content.decode("utf-8"))

        # Update agent configuration
        try:
            agent.configuration = AgentConfiguration(**config_data)
            agent.updated_at = datetime.utcnow()

            await cache_agent(agent)
            await api_enhancement_service.invalidate_cache("agent_detail")

            # Submit background task for configuration processing
            task_id = await background_task_service.submit_task(
                "process_agent_configuration",
                task_args=(agent_id, agent.configuration.dict()),
                metadata={
                    "uploaded_by": current_user.get("id"),
                    "filename": file.filename,
                },
            )

            return {
                "message": "Configuration uploaded successfully",
                "agent_id": agent_id,
                "background_task_id": task_id,
                "configuration": agent.configuration.dict(),
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid configuration format: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading configuration for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload configuration",
        )


@router.get(
    "/{agent_id}/metrics",
    response_model=AgentMetrics,
    summary="Get detailed agent metrics",
)
@api_enhancement_service.cache_response(ttl=30)
@api_enhancement_service.rate_limit(requests_per_minute=100)
async def get_agent_metrics(agent_id: str, request: Request):
    """Get detailed metrics for a specific agent"""
    agent = await get_agent_from_cache_or_storage(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    return agent.metrics


@router.get("/{agent_id}/logs", summary="Get agent execution logs")
@api_enhancement_service.rate_limit(requests_per_minute=50)
async def get_agent_logs(
    agent_id: str,
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
):
    """Get execution logs for a specific agent"""
    # This would typically read from log files or a logging service
    # For now, return mock data
    logs = []
    for i in range(min(limit, 50)):
        logs.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": f"Agent {agent_id} executed task successfully",
                "details": {"task_id": f"task_{i}", "duration": 1.5 + i * 0.1},
            }
        )

    return {
        "agent_id": agent_id,
        "logs": logs,
        "total_count": len(logs),
        "level_filter": level,
    }