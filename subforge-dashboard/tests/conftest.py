"""
Global pytest configuration and fixtures for SubForge Dashboard tests
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
import tempfile
import shutil
from pathlib import Path
import uuid

# Backend imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.agent import Agent
from app.models.task import Task
from app.models.workflow import Workflow
from app.models.system_metrics import SystemMetrics


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def test_client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with dependency override"""
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client(test_session) -> Generator[TestClient, None, None]:
    """Create synchronous test client for WebSocket testing"""
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


# Mock fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=True)
    mock.expire = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager"""
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.broadcast_json = AsyncMock()
    mock.send_personal_message = AsyncMock()
    return mock


@pytest.fixture
def mock_celery_task():
    """Mock Celery task"""
    mock = AsyncMock()
    mock.delay = AsyncMock()
    mock.apply_async = AsyncMock()
    return mock


# Data fixtures
@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing"""
    return {
        "name": "test-agent",
        "agent_type": "backend-developer",
        "status": "idle",
        "description": "Test agent for backend development",
        "model": "claude-3-sonnet",
        "tools": ["read", "write", "edit", "bash"],
        "capabilities": ["python", "fastapi", "sqlalchemy"],
        "configuration": {
            "max_concurrent_tasks": 3,
            "timeout": 300
        }
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "title": "Test Task",
        "description": "A test task for validation",
        "priority": "medium",
        "status": "pending",
        "agent_id": None,
        "metadata": {
            "estimated_duration": 600,
            "complexity": "medium"
        }
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing"""
    return {
        "name": "test-workflow",
        "description": "Test workflow for validation",
        "status": "pending",
        "configuration": {
            "max_parallel_tasks": 2,
            "timeout": 1800
        },
        "steps": [
            {
                "name": "step1",
                "type": "task",
                "dependencies": []
            },
            {
                "name": "step2", 
                "type": "task",
                "dependencies": ["step1"]
            }
        ]
    }


@pytest_asyncio.fixture
async def test_agent(test_session, sample_agent_data):
    """Create test agent in database"""
    agent = Agent(**sample_agent_data)
    test_session.add(agent)
    await test_session.commit()
    await test_session.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def test_task(test_session, sample_task_data):
    """Create test task in database"""
    task = Task(**sample_task_data)
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def test_workflow(test_session, sample_workflow_data):
    """Create test workflow in database"""
    workflow = Workflow(**sample_workflow_data)
    test_session.add(workflow)
    await test_session.commit()
    await test_session.refresh(workflow)
    return workflow


# Temporary directory fixtures
@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_files_dir(temp_dir):
    """Create test files directory with sample files"""
    files_dir = temp_dir / "test_files"
    files_dir.mkdir()
    
    # Create sample files
    (files_dir / "test.txt").write_text("Test content")
    (files_dir / "test.py").write_text("print('Hello World')")
    (files_dir / "test.json").write_text('{"key": "value"}')
    
    return files_dir


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance tests"""
    return {
        "max_response_time": 1.0,  # seconds
        "max_concurrent_requests": 100,
        "test_duration": 30,  # seconds
        "acceptable_error_rate": 0.01  # 1%
    }


# Security testing fixtures
@pytest.fixture
def security_payloads():
    """Common security test payloads"""
    return {
        "sql_injection": [
            "'; DROP TABLE agents; --",
            "' OR '1'='1",
            "1; EXEC xp_cmdshell('dir');--"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "$(whoami)"
        ]
    }


# Test data cleanup
@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data(test_session):
    """Automatically cleanup test data after each test"""
    yield
    
    # Clean up all test data
    await test_session.execute("DELETE FROM agents")
    await test_session.execute("DELETE FROM tasks")
    await test_session.execute("DELETE FROM workflows")
    await test_session.execute("DELETE FROM system_metrics")
    await test_session.commit()


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    
    yield
    
    # Clean up
    for key in ["TESTING", "DATABASE_URL", "SECRET_KEY", "REDIS_URL"]:
        if key in os.environ:
            del os.environ[key]


# Utility functions for tests
def create_uuid():
    """Create UUID for testing"""
    return uuid.uuid4()


def assert_dict_subset(subset: dict, full_dict: dict):
    """Assert that subset is contained in full_dict"""
    for key, value in subset.items():
        assert key in full_dict, f"Key '{key}' not found in full_dict"
        assert full_dict[key] == value, f"Value mismatch for key '{key}': expected {value}, got {full_dict[key]}"