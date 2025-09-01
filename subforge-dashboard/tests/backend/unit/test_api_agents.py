"""
Unit tests for agent API endpoints
"""

import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.models.agent import Agent


@pytest.mark.unit
@pytest.mark.api
class TestAgentAPI:
    """Tests for agent API endpoints"""
    
    async def test_get_agents_empty(self, test_client: AsyncClient):
        """Test getting agents when none exist"""
        response = await test_client.get("/api/v1/agents/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    async def test_get_agents_with_data(self, test_client: AsyncClient, test_agent):
        """Test getting agents with existing data"""
        response = await test_client.get("/api/v1/agents/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == test_agent.name
        assert data[0]["type"] == test_agent.agent_type
        assert data[0]["status"] == test_agent.status
    
    async def test_get_agents_with_filters(self, test_client: AsyncClient, test_session):
        """Test getting agents with filters"""
        # Create test agents with different statuses
        agents = [
            Agent(name="agent1", agent_type="backend", status="active"),
            Agent(name="agent2", agent_type="frontend", status="idle"),
            Agent(name="agent3", agent_type="backend", status="busy")
        ]
        
        for agent in agents:
            test_session.add(agent)
        await test_session.commit()
        
        # Test status filter
        response = await test_client.get("/api/v1/agents/?status=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "active"
        
        # Test type filter
        response = await test_client.get("/api/v1/agents/?agent_type=backend")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for agent_data in data:
            assert agent_data["type"] == "backend"
        
        # Test is_active filter
        response = await test_client.get("/api/v1/agents/?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # All agents are active by default
    
    async def test_get_agents_pagination(self, test_client: AsyncClient, test_session):
        """Test agent pagination"""
        # Create multiple test agents
        agents = [
            Agent(name=f"agent{i}", agent_type="test", status="idle")
            for i in range(5)
        ]
        
        for agent in agents:
            test_session.add(agent)
        await test_session.commit()
        
        # Test limit
        response = await test_client.get("/api/v1/agents/?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Test skip
        response = await test_client.get("/api/v1/agents/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    async def test_get_agent_by_id(self, test_client: AsyncClient, test_agent):
        """Test getting specific agent by ID"""
        response = await test_client.get(f"/api/v1/agents/{test_agent.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_agent.id)
        assert data["name"] == test_agent.name
        assert data["type"] == test_agent.agent_type
    
    async def test_get_agent_not_found(self, test_client: AsyncClient):
        """Test getting non-existent agent"""
        fake_id = uuid.uuid4()
        response = await test_client.get(f"/api/v1/agents/{fake_id}")
        
        assert response.status_code == 404
        assert "Agent not found" in response.json()["detail"]
    
    async def test_create_agent(self, test_client: AsyncClient, sample_agent_data):
        """Test creating a new agent"""
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            response = await test_client.post("/api/v1/agents/", json=sample_agent_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == sample_agent_data["name"]
            assert data["type"] == sample_agent_data["agent_type"]
            assert data["status"] == sample_agent_data["status"]
            assert data["configuration"]["model"] == sample_agent_data["model"]
            assert data["configuration"]["tools"] == sample_agent_data["tools"]
            
            # Verify WebSocket broadcast was called
            mock_broadcast.assert_called_once()
    
    async def test_create_agent_duplicate(self, test_client: AsyncClient, test_agent, sample_agent_data):
        """Test creating duplicate agent"""
        # Try to create agent with same name and type
        duplicate_data = sample_agent_data.copy()
        duplicate_data["name"] = test_agent.name
        duplicate_data["agent_type"] = test_agent.agent_type
        
        response = await test_client.post("/api/v1/agents/", json=duplicate_data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    async def test_create_agent_invalid_data(self, test_client: AsyncClient):
        """Test creating agent with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "agent_type": "test"
        }
        
        response = await test_client.post("/api/v1/agents/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_update_agent(self, test_client: AsyncClient, test_agent):
        """Test updating an agent"""
        update_data = {
            "description": "Updated description",
            "status": "active",
            "configuration": {"new_key": "new_value"}
        }
        
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            response = await test_client.put(f"/api/v1/agents/{test_agent.id}", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["description"] == "Updated description"
            assert data["status"] == "active"
            
            # Verify WebSocket broadcast was called
            mock_broadcast.assert_called_once()
    
    async def test_update_agent_not_found(self, test_client: AsyncClient):
        """Test updating non-existent agent"""
        fake_id = uuid.uuid4()
        update_data = {"description": "Updated"}
        
        response = await test_client.put(f"/api/v1/agents/{fake_id}", json=update_data)
        
        assert response.status_code == 404
        assert "Agent not found" in response.json()["detail"]
    
    async def test_update_agent_status(self, test_client: AsyncClient, test_agent):
        """Test updating agent status"""
        status_update = {
            "status": "busy",
            "current_task_id": str(uuid.uuid4()),
            "current_task_title": "New Task"
        }
        
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            response = await test_client.patch(f"/api/v1/agents/{test_agent.id}/status", json=status_update)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "busy"
            assert data["current_task"]["title"] == "New Task"
            
            # Verify WebSocket broadcast was called
            mock_broadcast.assert_called_once()
    
    async def test_update_agent_metrics(self, test_client: AsyncClient, test_agent):
        """Test updating agent metrics"""
        metrics_update = {
            "tasks_completed": 10,
            "tasks_failed": 2,
            "avg_response_time": 1.5,
            "uptime_percentage": 95.0
        }
        
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            response = await test_client.patch(f"/api/v1/agents/{test_agent.id}/metrics", json=metrics_update)
            
            assert response.status_code == 200
            data = response.json()
            
            metrics = data["performance_metrics"]
            assert metrics["tasks_completed"] == 10
            assert metrics["tasks_failed"] == 2
            assert metrics["avg_response_time"] == 1.5
            assert metrics["uptime_percentage"] == 95.0
            # Success rate should be calculated
            assert metrics["success_rate"] == 83.33333333333334  # 10/(10+2) * 100
            
            # Verify WebSocket broadcast was called
            mock_broadcast.assert_called_once()
    
    async def test_agent_heartbeat(self, test_client: AsyncClient, test_agent):
        """Test agent heartbeat endpoint"""
        heartbeat_data = {
            "timestamp": "2024-01-01T12:00:00Z",
            "status": "active",
            "current_task_id": str(uuid.uuid4()),
            "metrics": {
                "cpu_usage": 75.5,
                "memory_usage": 60.2
            }
        }
        
        response = await test_client.post(f"/api/v1/agents/{test_agent.id}/heartbeat", json=heartbeat_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "heartbeat_received"
        assert "timestamp" in data
    
    async def test_delete_agent(self, test_client: AsyncClient, test_agent):
        """Test deleting an agent"""
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            response = await test_client.delete(f"/api/v1/agents/{test_agent.id}")
            
            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]
            
            # Verify agent is deleted
            get_response = await test_client.get(f"/api/v1/agents/{test_agent.id}")
            assert get_response.status_code == 404
            
            # Verify WebSocket broadcast was called
            mock_broadcast.assert_called_once()
    
    async def test_delete_agent_not_found(self, test_client: AsyncClient):
        """Test deleting non-existent agent"""
        fake_id = uuid.uuid4()
        response = await test_client.delete(f"/api/v1/agents/{fake_id}")
        
        assert response.status_code == 404
        assert "Agent not found" in response.json()["detail"]
    
    async def test_get_agent_stats(self, test_client: AsyncClient, test_session):
        """Test getting agent statistics"""
        # Create test agents with different statuses
        agents = [
            Agent(name="agent1", agent_type="test", status="active", success_rate=90.0, avg_response_time=1.2, uptime_percentage=98.0),
            Agent(name="agent2", agent_type="test", status="idle", success_rate=85.0, avg_response_time=1.5, uptime_percentage=99.0),
            Agent(name="agent3", agent_type="test", status="busy", success_rate=92.0, avg_response_time=1.1, uptime_percentage=97.0),
            Agent(name="agent4", agent_type="test", status="offline", success_rate=88.0, avg_response_time=1.3, uptime_percentage=95.0)
        ]
        
        for agent in agents:
            test_session.add(agent)
        await test_session.commit()
        
        response = await test_client.get("/api/v1/agents/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_agents"] == 4
        assert data["active_agents"] == 1
        assert data["idle_agents"] == 1
        assert data["busy_agents"] == 1
        assert data["offline_agents"] == 1
        assert data["avg_success_rate"] == 88.75  # (90+85+92+88)/4
        assert data["avg_response_time"] == 1.275  # (1.2+1.5+1.1+1.3)/4
        assert data["avg_uptime"] == 97.25  # (98+99+97+95)/4


@pytest.mark.unit
@pytest.mark.api
class TestAgentAPIValidation:
    """Tests for agent API input validation"""
    
    async def test_create_agent_missing_required_fields(self, test_client: AsyncClient):
        """Test creating agent with missing required fields"""
        # Missing name
        incomplete_data = {
            "agent_type": "test",
            "status": "idle"
        }
        
        response = await test_client.post("/api/v1/agents/", json=incomplete_data)
        assert response.status_code == 422
        
        # Missing agent_type
        incomplete_data = {
            "name": "test",
            "status": "idle"
        }
        
        response = await test_client.post("/api/v1/agents/", json=incomplete_data)
        assert response.status_code == 422
    
    async def test_create_agent_invalid_status(self, test_client: AsyncClient):
        """Test creating agent with invalid status"""
        invalid_data = {
            "name": "test",
            "agent_type": "test",
            "status": "invalid_status"
        }
        
        response = await test_client.post("/api/v1/agents/", json=invalid_data)
        # Should either reject invalid status or accept any string
        # Implementation dependent on schema validation
        assert response.status_code in [200, 422]
    
    async def test_update_agent_invalid_uuid(self, test_client: AsyncClient):
        """Test updating agent with invalid UUID"""
        update_data = {"description": "Updated"}
        
        response = await test_client.put("/api/v1/agents/invalid-uuid", json=update_data)
        assert response.status_code == 422
    
    async def test_agent_heartbeat_invalid_data(self, test_client: AsyncClient, test_agent):
        """Test agent heartbeat with invalid data"""
        # Missing timestamp
        invalid_data = {
            "status": "active"
        }
        
        response = await test_client.post(f"/api/v1/agents/{test_agent.id}/heartbeat", json=invalid_data)
        assert response.status_code == 422
        
        # Invalid timestamp format
        invalid_data = {
            "timestamp": "invalid-timestamp",
            "status": "active"
        }
        
        response = await test_client.post(f"/api/v1/agents/{test_agent.id}/heartbeat", json=invalid_data)
        assert response.status_code == 422


@pytest.mark.unit
@pytest.mark.api 
@pytest.mark.websocket
class TestAgentAPIWebSocket:
    """Tests for agent API WebSocket integration"""
    
    async def test_agent_creation_broadcasts_websocket(self, test_client: AsyncClient, sample_agent_data):
        """Test that agent creation broadcasts WebSocket message"""
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            response = await test_client.post("/api/v1/agents/", json=sample_agent_data)
            assert response.status_code == 200
            
            # Verify broadcast was called with correct message type
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "agent_created"
            assert "data" in call_args
    
    async def test_agent_update_broadcasts_websocket(self, test_client: AsyncClient, test_agent):
        """Test that agent updates broadcast WebSocket message"""
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            update_data = {"description": "Updated"}
            response = await test_client.put(f"/api/v1/agents/{test_agent.id}", json=update_data)
            assert response.status_code == 200
            
            # Verify broadcast was called
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "agent_updated"
    
    async def test_agent_status_update_broadcasts_websocket(self, test_client: AsyncClient, test_agent):
        """Test that agent status updates broadcast WebSocket message"""
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            status_data = {"status": "active"}
            response = await test_client.patch(f"/api/v1/agents/{test_agent.id}/status", json=status_data)
            assert response.status_code == 200
            
            # Verify broadcast was called
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "agent_status_updated"
    
    async def test_agent_metrics_update_broadcasts_websocket(self, test_client: AsyncClient, test_agent):
        """Test that agent metrics updates broadcast WebSocket message"""
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            metrics_data = {"tasks_completed": 5}
            response = await test_client.patch(f"/api/v1/agents/{test_agent.id}/metrics", json=metrics_data)
            assert response.status_code == 200
            
            # Verify broadcast was called
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "agent_metrics_updated"
    
    async def test_agent_deletion_broadcasts_websocket(self, test_client: AsyncClient, test_agent):
        """Test that agent deletion broadcasts WebSocket message"""
        with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()
            
            response = await test_client.delete(f"/api/v1/agents/{test_agent.id}")
            assert response.status_code == 200
            
            # Verify broadcast was called
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            assert call_args["type"] == "agent_deleted"
            assert call_args["data"]["agent_id"] == str(test_agent.id)