"""
API v1 endpoints for SubForge Dashboard
"""

from fastapi import APIRouter
from .agents import router as agents_router
from .tasks import router as tasks_router
from .workflows import router as workflows_router
from .system import router as system_router

api_router = APIRouter()

api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(system_router, prefix="/system", tags=["system"])