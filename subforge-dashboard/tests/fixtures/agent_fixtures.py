"""
Test fixtures for agent-related tests
"""

import pytest
from typing import List, Dict, Any
import uuid
from datetime import datetime, timedelta

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


@pytest.fixture
def agent_factory():
    """Factory for creating agent test data"""
    def _create_agent_data(
        name: str = "test-agent",
        agent_type: str = "test",
        status: str = "idle",
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "name": name,
            "agent_type": agent_type,
            "status": status,
            "description": f"Test agent: {name}",
            "model": "claude-3-sonnet",
            "tools": ["read", "write", "edit"],
            "capabilities": ["python", "testing"],
            "configuration": {"test_mode": True},
            **kwargs
        }
    return _create_agent_data


@pytest.fixture
def sample_agents_data(agent_factory):
    """Sample agent data for testing"""
    return [
        agent_factory("frontend-dev", "frontend-developer", "active"),
        agent_factory("backend-dev", "backend-developer", "busy"),
        agent_factory("data-scientist", "data-scientist", "idle"),
        agent_factory("devops-engineer", "devops-engineer", "active"),
        agent_factory("code-reviewer", "code-reviewer", "busy"),
        agent_factory("test-engineer", "test-engineer", "error"),
    ]


@pytest.fixture
async def sample_agents(test_session, sample_agents_data):
    """Create sample agents in database"""
    agents = []
    for agent_data in sample_agents_data:
        agent = Agent(**agent_data)
        test_session.add(agent)
        agents.append(agent)
    
    await test_session.commit()
    
    for agent in agents:
        await test_session.refresh(agent)
    
    return agents


@pytest.fixture
def agent_performance_data():
    """Sample agent performance data"""
    return [
        {
            "agent_id": str(uuid.uuid4()),
            "tasks_completed": 25,
            "tasks_failed": 3,
            "avg_response_time": 1.2,
            "uptime_percentage": 98.5,
            "success_rate": 89.3
        },
        {
            "agent_id": str(uuid.uuid4()),
            "tasks_completed": 42,
            "tasks_failed": 1,
            "avg_response_time": 0.8,
            "uptime_percentage": 99.2,
            "success_rate": 97.7
        },
        {
            "agent_id": str(uuid.uuid4()),
            "tasks_completed": 18,
            "tasks_failed": 5,
            "avg_response_time": 2.1,
            "uptime_percentage": 94.1,
            "success_rate": 78.3
        }
    ]


@pytest.fixture
def agent_status_updates():
    """Sample agent status update data"""
    return [
        {
            "status": "active",
            "current_task_id": str(uuid.uuid4()),
            "current_task_title": "Building React components"
        },
        {
            "status": "busy",
            "current_task_id": str(uuid.uuid4()),
            "current_task_title": "API endpoint optimization"
        },
        {
            "status": "idle"
        },
        {
            "status": "error",
            "error_message": "Connection timeout"
        }
    ]


@pytest.fixture
def agent_heartbeat_data():
    """Sample agent heartbeat data"""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "active",
        "current_task_id": str(uuid.uuid4()),
        "metrics": {
            "cpu_usage": 45.2,
            "memory_usage": 68.7,
            "active_connections": 12
        }
    }


@pytest.fixture
def bulk_agent_data(agent_factory):
    """Generate bulk agent data for performance testing"""
    def _generate_bulk_data(count: int = 100) -> List[Dict[str, Any]]:
        agents = []
        agent_types = ["frontend", "backend", "fullstack", "devops", "qa", "data"]
        statuses = ["active", "idle", "busy", "offline"]
        
        for i in range(count):
            agent_data = agent_factory(
                name=f"bulk-agent-{i}",
                agent_type=agent_types[i % len(agent_types)],
                status=statuses[i % len(statuses)],
                description=f"Bulk test agent {i}",
                configuration={
                    "bulk_test": True,
                    "index": i,
                    "batch_size": count
                }
            )
            
            # Add some variation to metrics
            agent_data.update({
                "tasks_completed": i * 2,
                "tasks_failed": max(0, i // 10),
                "avg_response_time": 0.5 + (i % 20) / 10,
                "uptime_percentage": 95.0 + (i % 5)
            })
            
            agents.append(agent_data)
        
        return agents
    
    return _generate_bulk_data


@pytest.fixture
async def performance_agents(test_session, bulk_agent_data):
    """Create agents for performance testing"""
    agents_data = bulk_agent_data(50)  # 50 agents for performance tests
    agents = []
    
    for agent_data in agents_data:
        agent = Agent(**agent_data)
        agents.append(agent)
    
    test_session.add_all(agents)
    await test_session.commit()
    
    for agent in agents:
        await test_session.refresh(agent)
    
    return agents


@pytest.fixture
def agent_websocket_messages():
    """Sample WebSocket messages for agent updates"""
    return [
        {
            "type": "agent_created",
            "data": {
                "id": str(uuid.uuid4()),
                "name": "new-agent",
                "type": "test",
                "status": "idle",
                "created_at": datetime.utcnow().isoformat()
            }
        },
        {
            "type": "agent_updated",
            "data": {
                "id": str(uuid.uuid4()),
                "name": "updated-agent",
                "description": "Updated description",
                "updated_at": datetime.utcnow().isoformat()
            }
        },
        {
            "type": "agent_status_updated",
            "data": {
                "agent_id": str(uuid.uuid4()),
                "status": "busy",
                "current_task": {
                    "id": str(uuid.uuid4()),
                    "title": "Processing data"
                }
            }
        },
        {
            "type": "agent_metrics_updated",
            "data": {
                "agent_id": str(uuid.uuid4()),
                "metrics": {
                    "tasks_completed": 15,
                    "tasks_failed": 2,
                    "success_rate": 88.2,
                    "avg_response_time": 1.3,
                    "uptime_percentage": 97.5
                }
            }
        },
        {
            "type": "agent_deleted",
            "data": {
                "agent_id": str(uuid.uuid4())
            }
        }
    ]


@pytest.fixture
def invalid_agent_data():
    """Invalid agent data for validation testing"""
    return [
        # Missing required fields
        {
            "agent_type": "test",
            "status": "idle"
            # Missing name
        },
        {
            "name": "test-agent",
            "status": "idle"
            # Missing agent_type
        },
        # Invalid field values
        {
            "name": "",  # Empty name
            "agent_type": "test",
            "status": "idle"
        },
        {
            "name": "test-agent",
            "agent_type": "",  # Empty type
            "status": "idle"
        },
        {
            "name": "test-agent",
            "agent_type": "test",
            "status": "invalid_status"  # Invalid status
        },
        # Invalid data types
        {
            "name": 123,  # Should be string
            "agent_type": "test",
            "status": "idle"
        },
        {
            "name": "test-agent",
            "agent_type": "test",
            "status": "idle",
            "tools": "not_a_list"  # Should be list
        },
        {
            "name": "test-agent",
            "agent_type": "test",
            "status": "idle",
            "configuration": "not_a_dict"  # Should be dict
        }
    ]


@pytest.fixture
def agent_schema_factory():
    """Factory for creating agent schema objects"""
    def _create_agent_create(
        name: str = "test-agent",
        agent_type: str = "test",
        **kwargs
    ) -> AgentCreate:
        return AgentCreate(
            name=name,
            agent_type=agent_type,
            status=kwargs.get("status", "idle"),
            description=kwargs.get("description", f"Test agent: {name}"),
            model=kwargs.get("model", "claude-3-sonnet"),
            tools=kwargs.get("tools", ["read", "write"]),
            capabilities=kwargs.get("capabilities", ["python"]),
            configuration=kwargs.get("configuration", {})
        )
    
    def _create_agent_update(**kwargs) -> AgentUpdate:
        return AgentUpdate(**kwargs)
    
    return {
        "create": _create_agent_create,
        "update": _create_agent_update
    }


@pytest.fixture
def historical_agent_data():
    """Historical agent data for time-series testing"""
    base_time = datetime.utcnow() - timedelta(days=7)
    
    data = []
    for i in range(168):  # 7 days * 24 hours
        timestamp = base_time + timedelta(hours=i)
        data.append({
            "timestamp": timestamp,
            "agent_count": 5 + (i % 3),  # Varies between 5-7 agents
            "active_agents": 2 + (i % 4),  # Varies between 2-5 active
            "avg_response_time": 0.8 + (i % 10) / 10,  # Varies between 0.8-1.7
            "success_rate": 85 + (i % 15),  # Varies between 85-99%
            "total_tasks": i * 2 + 50,  # Accumulating tasks
        })
    
    return data


@pytest.fixture
def agent_error_scenarios():
    """Error scenarios for agent testing"""
    return [
        {
            "name": "network_timeout",
            "description": "Network timeout during API call",
            "error_code": "NETWORK_TIMEOUT",
            "status_code": 408
        },
        {
            "name": "database_connection",
            "description": "Database connection failed",
            "error_code": "DB_CONNECTION_FAILED",
            "status_code": 503
        },
        {
            "name": "validation_error",
            "description": "Invalid input data",
            "error_code": "VALIDATION_ERROR",
            "status_code": 422
        },
        {
            "name": "permission_denied",
            "description": "Insufficient permissions",
            "error_code": "PERMISSION_DENIED",
            "status_code": 403
        },
        {
            "name": "resource_not_found",
            "description": "Agent not found",
            "error_code": "NOT_FOUND",
            "status_code": 404
        }
    ]


@pytest.fixture
def mock_external_services():
    """Mock external services for agent testing"""
    return {
        "claude_api": {
            "base_url": "https://api.anthropic.com/v1",
            "responses": {
                "chat_completion": {
                    "id": "msg_123",
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Test response"}],
                    "model": "claude-3-sonnet",
                    "usage": {"input_tokens": 10, "output_tokens": 20}
                }
            }
        },
        "github_api": {
            "base_url": "https://api.github.com",
            "responses": {
                "user": {"login": "test-user", "id": 12345},
                "repos": [{"name": "test-repo", "full_name": "test-user/test-repo"}]
            }
        },
        "monitoring": {
            "base_url": "https://monitoring.example.com",
            "responses": {
                "metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 68.7,
                    "disk_usage": 42.1
                }
            }
        }
    }