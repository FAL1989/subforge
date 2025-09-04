"""
Integration tests for API endpoints with database and WebSocket
"""

from unittest.mock import AsyncMock, patch

import pytest
from app.models.agent import Agent
from app.models.task import Task
from app.models.workflow import Workflow
from httpx import AsyncClient
from sqlalchemy import select


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.database
class TestAgentAPIIntegration:
    """Integration tests for agent API with database"""

    async def test_complete_agent_lifecycle(
        self, test_client: AsyncClient, test_session
    ):
        """Test complete agent lifecycle: create, read, update, delete"""

        # 1. Create agent
        agent_data = {
            "name": "integration-test-agent",
            "agent_type": "test-integration",
            "status": "idle",
            "description": "Integration test agent",
            "model": "claude-3-sonnet",
            "tools": ["read", "write", "edit"],
            "capabilities": ["python", "testing"],
            "configuration": {"test_mode": True},
        }

        with patch(
            "app.websocket.manager.websocket_manager.broadcast_json"
        ) as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()

            create_response = await test_client.post("/api/v1/agents/", json=agent_data)
            assert create_response.status_code == 200

            created_agent = create_response.json()
            agent_id = created_agent["id"]

            # Verify WebSocket broadcast
            mock_broadcast.assert_called_once()
            broadcast_data = mock_broadcast.call_args[0][0]
            assert broadcast_data["type"] == "agent_created"

        # 2. Read agent
        get_response = await test_client.get(f"/api/v1/agents/{agent_id}")
        assert get_response.status_code == 200

        retrieved_agent = get_response.json()
        assert retrieved_agent["name"] == agent_data["name"]
        assert retrieved_agent["type"] == agent_data["agent_type"]
        assert retrieved_agent["configuration"]["model"] == agent_data["model"]

        # 3. Update agent
        update_data = {
            "description": "Updated integration test agent",
            "status": "active",
            "configuration": {"test_mode": False, "updated": True},
        }

        with patch(
            "app.websocket.manager.websocket_manager.broadcast_json"
        ) as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()

            update_response = await test_client.put(
                f"/api/v1/agents/{agent_id}", json=update_data
            )
            assert update_response.status_code == 200

            updated_agent = update_response.json()
            assert updated_agent["description"] == update_data["description"]
            assert updated_agent["status"] == update_data["status"]

            # Verify WebSocket broadcast
            mock_broadcast.assert_called_once()

        # 4. Verify in database
        result = await test_session.execute(select(Agent).where(Agent.id == agent_id))
        db_agent = result.scalar_one_or_none()
        assert db_agent is not None
        assert db_agent.description == update_data["description"]
        assert db_agent.status == update_data["status"]

        # 5. Delete agent
        with patch(
            "app.websocket.manager.websocket_manager.broadcast_json"
        ) as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()

            delete_response = await test_client.delete(f"/api/v1/agents/{agent_id}")
            assert delete_response.status_code == 200

            # Verify WebSocket broadcast
            mock_broadcast.assert_called_once()
            broadcast_data = mock_broadcast.call_args[0][0]
            assert broadcast_data["type"] == "agent_deleted"

        # 6. Verify deletion
        get_deleted_response = await test_client.get(f"/api/v1/agents/{agent_id}")
        assert get_deleted_response.status_code == 404

        # Verify in database
        result = await test_session.execute(select(Agent).where(Agent.id == agent_id))
        db_agent = result.scalar_one_or_none()
        assert db_agent is None

    async def test_agent_with_tasks_integration(
        self, test_client: AsyncClient, test_session
    ):
        """Test agent with associated tasks"""

        # Create agent
        agent_data = {
            "name": "task-agent",
            "agent_type": "task-handler",
            "status": "idle",
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            create_response = await test_client.post("/api/v1/agents/", json=agent_data)
            assert create_response.status_code == 200
            agent_id = create_response.json()["id"]

        # Create tasks assigned to agent
        task_data = {
            "title": "Integration Test Task",
            "description": "A task for integration testing",
            "priority": "high",
            "status": "pending",
            "agent_id": agent_id,
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            task_response = await test_client.post("/api/v1/tasks/", json=task_data)
            assert task_response.status_code == 200
            task_id = task_response.json()["id"]

        # Update agent status
        status_update = {
            "status": "busy",
            "current_task_id": task_id,
            "current_task_title": task_data["title"],
        }

        with patch(
            "app.websocket.manager.websocket_manager.broadcast_json"
        ) as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()

            status_response = await test_client.patch(
                f"/api/v1/agents/{agent_id}/status", json=status_update
            )
            assert status_response.status_code == 200

            updated_agent = status_response.json()
            assert updated_agent["status"] == "busy"
            assert updated_agent["current_task"]["id"] == task_id
            assert updated_agent["current_task"]["title"] == task_data["title"]

        # Verify task assignment in database
        result = await test_session.execute(select(Task).where(Task.id == task_id))
        db_task = result.scalar_one_or_none()
        assert db_task is not None
        assert str(db_task.agent_id) == agent_id

        # Clean up
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            await test_client.delete(f"/api/v1/tasks/{task_id}")
            await test_client.delete(f"/api/v1/agents/{agent_id}")

    async def test_agent_metrics_integration(self, test_client: AsyncClient):
        """Test agent metrics update and calculation"""

        # Create agent
        agent_data = {
            "name": "metrics-agent",
            "agent_type": "metrics-test",
            "status": "idle",
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            create_response = await test_client.post("/api/v1/agents/", json=agent_data)
            agent_id = create_response.json()["id"]

        # Update metrics multiple times
        metrics_updates = [
            {"tasks_completed": 5, "tasks_failed": 1, "avg_response_time": 1.2},
            {"tasks_completed": 10, "tasks_failed": 2, "avg_response_time": 1.1},
            {"tasks_completed": 15, "tasks_failed": 2, "avg_response_time": 1.0},
        ]

        for metrics in metrics_updates:
            with patch(
                "app.websocket.manager.websocket_manager.broadcast_json"
            ) as mock_broadcast:
                mock_broadcast.return_value = AsyncMock()

                response = await test_client.patch(
                    f"/api/v1/agents/{agent_id}/metrics", json=metrics
                )
                assert response.status_code == 200

                agent_data = response.json()
                performance = agent_data["performance_metrics"]

                # Verify success rate calculation
                expected_success_rate = (
                    metrics["tasks_completed"]
                    / (metrics["tasks_completed"] + metrics["tasks_failed"])
                ) * 100
                assert abs(performance["success_rate"] - expected_success_rate) < 0.01

                # Verify other metrics
                assert performance["tasks_completed"] == metrics["tasks_completed"]
                assert performance["tasks_failed"] == metrics["tasks_failed"]
                assert performance["avg_response_time"] == metrics["avg_response_time"]

                # Verify WebSocket broadcast
                mock_broadcast.assert_called_once()
                broadcast_data = mock_broadcast.call_args[0][0]
                assert broadcast_data["type"] == "agent_metrics_updated"

        # Clean up
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            await test_client.delete(f"/api/v1/agents/{agent_id}")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.database
class TestTaskAPIIntegration:
    """Integration tests for task API with database"""

    async def test_complete_task_workflow(self, test_client: AsyncClient, test_session):
        """Test complete task workflow with status transitions"""

        # Create agent first
        agent_data = {
            "name": "workflow-agent",
            "agent_type": "workflow-test",
            "status": "idle",
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            agent_response = await test_client.post("/api/v1/agents/", json=agent_data)
            agent_id = agent_response.json()["id"]

        # Create task
        task_data = {
            "title": "Workflow Integration Test",
            "description": "Testing task workflow",
            "priority": "medium",
            "status": "pending",
            "estimated_duration": 1800,
            "metadata": {"test_mode": True},
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            create_response = await test_client.post("/api/v1/tasks/", json=task_data)
            assert create_response.status_code == 200
            task_id = create_response.json()["id"]

        # Assign task to agent
        assign_data = {"agent_id": agent_id}

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            assign_response = await test_client.patch(
                f"/api/v1/tasks/{task_id}/assign", json=assign_data
            )
            assert assign_response.status_code == 200

        # Start task
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            start_response = await test_client.patch(f"/api/v1/tasks/{task_id}/start")
            assert start_response.status_code == 200

            started_task = start_response.json()
            assert started_task["status"] == "in_progress"
            assert started_task["started_at"] is not None

        # Update progress
        progress_data = {"progress": 50}

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            progress_response = await test_client.patch(
                f"/api/v1/tasks/{task_id}/progress", json=progress_data
            )
            assert progress_response.status_code == 200
            assert progress_response.json()["progress"] == 50

        # Complete task
        completion_data = {"result": {"output": "Task completed successfully"}}

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            complete_response = await test_client.patch(
                f"/api/v1/tasks/{task_id}/complete", json=completion_data
            )
            assert complete_response.status_code == 200

            completed_task = complete_response.json()
            assert completed_task["status"] == "completed"
            assert completed_task["completed_at"] is not None
            assert completed_task["progress"] == 100

        # Verify in database
        result = await test_session.execute(select(Task).where(Task.id == task_id))
        db_task = result.scalar_one_or_none()
        assert db_task is not None
        assert db_task.status == "completed"
        assert db_task.progress == 100

        # Clean up
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            await test_client.delete(f"/api/v1/tasks/{task_id}")
            await test_client.delete(f"/api/v1/agents/{agent_id}")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.database
class TestWorkflowIntegration:
    """Integration tests for workflow functionality"""

    async def test_workflow_with_tasks(self, test_client: AsyncClient, test_session):
        """Test workflow creation and task management"""

        workflow_data = {
            "name": "integration-workflow",
            "description": "Integration test workflow",
            "configuration": {"max_parallel_tasks": 2},
            "steps": [
                {"name": "step1", "type": "task", "dependencies": []},
                {"name": "step2", "type": "task", "dependencies": ["step1"]},
                {"name": "step3", "type": "task", "dependencies": ["step2"]},
            ],
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            create_response = await test_client.post(
                "/api/v1/workflows/", json=workflow_data
            )
            assert create_response.status_code == 200

            workflow = create_response.json()
            workflow_id = workflow["id"]
            assert len(workflow["steps"]) == 3

        # Create tasks for workflow
        task_ids = []
        for i, step in enumerate(workflow_data["steps"]):
            task_data = {
                "title": f"Task for {step['name']}",
                "description": f"Task for workflow step {step['name']}",
                "priority": "medium",
                "status": "pending",
                "workflow_id": workflow_id,
                "metadata": {"step_name": step["name"], "step_index": i},
            }

            with patch("app.websocket.manager.websocket_manager.broadcast_json"):
                task_response = await test_client.post("/api/v1/tasks/", json=task_data)
                assert task_response.status_code == 200
                task_ids.append(task_response.json()["id"])

        # Start workflow
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            start_response = await test_client.patch(
                f"/api/v1/workflows/{workflow_id}/start"
            )
            assert start_response.status_code == 200

            started_workflow = start_response.json()
            assert started_workflow["status"] == "running"

        # Verify workflow tasks in database
        result = await test_session.execute(
            select(Task).where(Task.workflow_id == workflow_id)
        )
        workflow_tasks = result.scalars().all()
        assert len(workflow_tasks) == 3

        # Update workflow progress
        progress_data = {"progress": 33.3, "current_step": 1}

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            progress_response = await test_client.patch(
                f"/api/v1/workflows/{workflow_id}/progress", json=progress_data
            )
            assert progress_response.status_code == 200

        # Complete workflow
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            complete_response = await test_client.patch(
                f"/api/v1/workflows/{workflow_id}/complete"
            )
            assert complete_response.status_code == 200

            completed_workflow = complete_response.json()
            assert completed_workflow["status"] == "completed"
            assert completed_workflow["progress"] == 100.0

        # Clean up
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            for task_id in task_ids:
                await test_client.delete(f"/api/v1/tasks/{task_id}")
            await test_client.delete(f"/api/v1/workflows/{workflow_id}")


@pytest.mark.integration
@pytest.mark.websocket
class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality with API"""

    async def test_agent_updates_broadcast_websocket(self, test_client: AsyncClient):
        """Test that agent updates are properly broadcast via WebSocket"""

        # Mock WebSocket manager
        with patch("app.websocket.manager.websocket_manager") as mock_ws_manager:
            mock_ws_manager.broadcast_json = AsyncMock()

            # Create agent
            agent_data = {
                "name": "ws-test-agent",
                "agent_type": "websocket-test",
                "status": "idle",
            }
            create_response = await test_client.post("/api/v1/agents/", json=agent_data)
            agent_id = create_response.json()["id"]

            # Verify creation broadcast
            mock_ws_manager.broadcast_json.assert_called()
            create_call = mock_ws_manager.broadcast_json.call_args_list[0]
            assert create_call[0][0]["type"] == "agent_created"

            # Update agent status
            status_data = {
                "status": "active",
                "current_task_title": "WebSocket test task",
            }
            await test_client.patch(
                f"/api/v1/agents/{agent_id}/status", json=status_data
            )

            # Verify status update broadcast
            status_call = mock_ws_manager.broadcast_json.call_args_list[1]
            assert status_call[0][0]["type"] == "agent_status_updated"
            assert status_call[0][0]["data"]["status"] == "active"

            # Update metrics
            metrics_data = {"tasks_completed": 5, "tasks_failed": 1}
            await test_client.patch(
                f"/api/v1/agents/{agent_id}/metrics", json=metrics_data
            )

            # Verify metrics update broadcast
            metrics_call = mock_ws_manager.broadcast_json.call_args_list[2]
            assert metrics_call[0][0]["type"] == "agent_metrics_updated"

            # Delete agent
            await test_client.delete(f"/api/v1/agents/{agent_id}")

            # Verify deletion broadcast
            delete_call = mock_ws_manager.broadcast_json.call_args_list[3]
            assert delete_call[0][0]["type"] == "agent_deleted"

    async def test_task_updates_broadcast_websocket(self, test_client: AsyncClient):
        """Test that task updates are properly broadcast via WebSocket"""

        with patch("app.websocket.manager.websocket_manager") as mock_ws_manager:
            mock_ws_manager.broadcast_json = AsyncMock()

            # Create task
            task_data = {
                "title": "WebSocket Task",
                "description": "Task for WebSocket testing",
                "priority": "high",
                "status": "pending",
            }
            create_response = await test_client.post("/api/v1/tasks/", json=task_data)
            task_id = create_response.json()["id"]

            # Verify task creation broadcast
            create_call = mock_ws_manager.broadcast_json.call_args_list[0]
            assert create_call[0][0]["type"] == "task_created"

            # Start task
            await test_client.patch(f"/api/v1/tasks/{task_id}/start")

            # Verify task start broadcast
            start_call = mock_ws_manager.broadcast_json.call_args_list[1]
            assert start_call[0][0]["type"] == "task_updated"
            assert start_call[0][0]["data"]["status"] == "in_progress"

            # Update progress
            progress_data = {"progress": 75}
            await test_client.patch(
                f"/api/v1/tasks/{task_id}/progress", json=progress_data
            )

            # Verify progress broadcast
            progress_call = mock_ws_manager.broadcast_json.call_args_list[2]
            assert progress_call[0][0]["type"] == "task_progress_updated"
            assert progress_call[0][0]["data"]["progress"] == 75

            # Clean up
            await test_client.delete(f"/api/v1/tasks/{task_id}")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.performance
class TestAPIPerformanceIntegration:
    """Integration tests for API performance with database"""

    async def test_bulk_operations_performance(
        self, test_client: AsyncClient, test_session
    ):
        """Test performance of bulk operations"""

        # Create multiple agents
        agent_ids = []

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            for i in range(20):
                agent_data = {
                    "name": f"perf-agent-{i}",
                    "agent_type": "performance-test",
                    "status": "idle",
                }

                response = await test_client.post("/api/v1/agents/", json=agent_data)
                assert response.status_code == 200
                agent_ids.append(response.json()["id"])

        # Test bulk retrieval performance
        import time

        start_time = time.time()

        response = await test_client.get("/api/v1/agents/?limit=20")

        end_time = time.time()
        retrieval_time = end_time - start_time

        assert response.status_code == 200
        assert len(response.json()) == 20
        assert retrieval_time < 1.0  # Should retrieve within 1 second

        # Test bulk updates performance
        start_time = time.time()

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            for agent_id in agent_ids:
                update_data = {"description": f"Updated agent {agent_id}"}
                response = await test_client.put(
                    f"/api/v1/agents/{agent_id}", json=update_data
                )
                assert response.status_code == 200

        end_time = time.time()
        update_time = end_time - start_time

        assert update_time < 5.0  # Should update all within 5 seconds

        # Clean up
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            for agent_id in agent_ids:
                await test_client.delete(f"/api/v1/agents/{agent_id}")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.database
class TestDatabaseConsistency:
    """Integration tests for database consistency"""

    async def test_transaction_consistency(
        self, test_client: AsyncClient, test_session
    ):
        """Test database transaction consistency"""

        # Create agent and task in a workflow that should maintain consistency
        agent_data = {
            "name": "consistency-agent",
            "agent_type": "consistency-test",
            "status": "idle",
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            agent_response = await test_client.post("/api/v1/agents/", json=agent_data)
            agent_id = agent_response.json()["id"]

            task_data = {
                "title": "Consistency Test Task",
                "description": "Testing database consistency",
                "priority": "medium",
                "status": "pending",
                "agent_id": agent_id,
            }

            task_response = await test_client.post("/api/v1/tasks/", json=task_data)
            task_id = task_response.json()["id"]

        # Verify both records exist in database
        agent_result = await test_session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        task_result = await test_session.execute(select(Task).where(Task.id == task_id))

        db_agent = agent_result.scalar_one_or_none()
        db_task = task_result.scalar_one_or_none()

        assert db_agent is not None
        assert db_task is not None
        assert str(db_task.agent_id) == agent_id

        # Update agent status with task reference
        status_data = {
            "status": "busy",
            "current_task_id": task_id,
            "current_task_title": task_data["title"],
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            await test_client.patch(
                f"/api/v1/agents/{agent_id}/status", json=status_data
            )

        # Verify consistency after update
        agent_result = await test_session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        updated_agent = agent_result.scalar_one_or_none()

        assert updated_agent.status == "busy"
        assert str(updated_agent.current_task_id) == task_id
        assert updated_agent.current_task_title == task_data["title"]

        # Clean up
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            await test_client.delete(f"/api/v1/tasks/{task_id}")
            await test_client.delete(f"/api/v1/agents/{agent_id}")

    async def test_cascade_operations(self, test_client: AsyncClient, test_session):
        """Test cascade delete operations if implemented"""

        # Create workflow with tasks
        workflow_data = {
            "name": "cascade-test-workflow",
            "description": "Testing cascade operations",
            "steps": [{"name": "step1", "type": "task", "dependencies": []}],
        }

        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            workflow_response = await test_client.post(
                "/api/v1/workflows/", json=workflow_data
            )
            workflow_id = workflow_response.json()["id"]

            # Create task in workflow
            task_data = {
                "title": "Cascade Test Task",
                "description": "Task for cascade testing",
                "workflow_id": workflow_id,
                "priority": "medium",
                "status": "pending",
            }

            task_response = await test_client.post("/api/v1/tasks/", json=task_data)
            task_id = task_response.json()["id"]

        # Verify both exist
        workflow_result = await test_session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        task_result = await test_session.execute(select(Task).where(Task.id == task_id))

        assert workflow_result.scalar_one_or_none() is not None
        assert task_result.scalar_one_or_none() is not None

        # Delete workflow (should handle task relationship appropriately)
        with patch("app.websocket.manager.websocket_manager.broadcast_json"):
            delete_response = await test_client.delete(
                f"/api/v1/workflows/{workflow_id}"
            )
            # Response depends on cascade implementation
            assert delete_response.status_code in [
                200,
                409,
            ]  # 409 if cascade not allowed

            # If workflow deleted successfully, clean up any remaining tasks
            if delete_response.status_code == 200:
                # Verify workflow is deleted
                workflow_result = await test_session.execute(
                    select(Workflow).where(Workflow.id == workflow_id)
                )
                assert workflow_result.scalar_one_or_none() is None
            else:
                # Clean up manually if cascade delete not implemented
                await test_client.delete(f"/api/v1/tasks/{task_id}")
                await test_client.delete(f"/api/v1/workflows/{workflow_id}")