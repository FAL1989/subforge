"""
Test cases for the main FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import get_db
from app.database.base import Base


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_subforge_dashboard.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


def setup_module():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)


def teardown_module():
    """Cleanup test database"""
    Base.metadata.drop_all(bind=engine)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "SubForge Dashboard API"


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "checks" in data


def test_system_status_endpoint():
    """Test system status endpoint"""
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "tasks" in data
    assert "workflows" in data


def test_get_agents_empty():
    """Test getting agents when none exist"""
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    assert response.json() == []


def test_get_tasks_empty():
    """Test getting tasks when none exist"""
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_get_workflows_empty():
    """Test getting workflows when none exist"""
    response = client.get("/api/v1/workflows")
    assert response.status_code == 200
    assert response.json() == []


def test_create_agent():
    """Test creating a new agent"""
    agent_data = {
        "name": "Test Agent",
        "agent_type": "test-agent",
        "description": "A test agent",
        "tools": ["read", "write"],
        "capabilities": ["coding", "testing"]
    }
    
    response = client.post("/api/v1/agents", json=agent_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == agent_data["name"]
    assert data["type"] == agent_data["agent_type"]
    assert data["configuration"]["tools"] == agent_data["tools"]


def test_create_task():
    """Test creating a new task"""
    task_data = {
        "title": "Test Task",
        "description": "A test task",
        "priority": "medium",
        "tags": ["test", "backend"]
    }
    
    response = client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["priority"] == task_data["priority"]
    assert data["status"] == "pending"


def test_create_workflow():
    """Test creating a new workflow"""
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "workflow_type": "testing",
        "tags": ["test"]
    }
    
    response = client.post("/api/v1/workflows", json=workflow_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == workflow_data["name"]
    assert data["workflow_type"] == workflow_data["workflow_type"]


if __name__ == "__main__":
    pytest.main([__file__])