"""
Enhanced API v2 with advanced features
"""

from fastapi import APIRouter

from . import (
    agents,
    analytics,
    background_tasks,
    files,
    system,
    tasks,
    websocket_api,
    workflows,
)

# Create API v2 router
api_v2_router = APIRouter(prefix="/v2", tags=["v2"])

# Include sub-routers
api_v2_router.include_router(agents.router, prefix="/agents", tags=["agents-v2"])
api_v2_router.include_router(tasks.router, prefix="/tasks", tags=["tasks-v2"])
api_v2_router.include_router(
    workflows.router, prefix="/workflows", tags=["workflows-v2"]
)
api_v2_router.include_router(system.router, prefix="/system", tags=["system-v2"])
api_v2_router.include_router(files.router, prefix="/files", tags=["files-v2"])
api_v2_router.include_router(
    websocket_api.router, prefix="/websocket", tags=["websocket-v2"]
)
api_v2_router.include_router(
    background_tasks.router, prefix="/background-tasks", tags=["background-tasks-v2"]
)
api_v2_router.include_router(
    analytics.router, prefix="/analytics", tags=["analytics-v2"]
)