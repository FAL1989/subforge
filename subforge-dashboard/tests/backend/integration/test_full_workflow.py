"""
Full workflow integration test
Demonstrates complete testing of agent lifecycle with tasks and WebSocket updates
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy import select

from app.models.agent import Agent
from app.models.task import Task
from tests.utils.test_helpers import (
    APITestHelper,
    DatabaseTestHelper, 
    WebSocketTestHelper,
    TestDataGenerator,
    assert_dict_subset
)


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.websocket
class TestFullAgentWorkflow:
    """Complete integration test of agent workflow"""
    
    async def test_complete_agent_task_workflow(self, test_client: AsyncClient, test_session):
        """Test complete workflow: create agent, assign task, execute, complete"""
        
        # Initialize helpers
        api_helper = APITestHelper(test_client)
        db_helper = DatabaseTestHelper(test_session)
        ws_helper = WebSocketTestHelper()
        
        # Track WebSocket messages
        websocket_messages = []
        
        def mock_websocket_broadcast(message):
            websocket_messages.append(message)
            ws_helper.on_message(json.dumps(message))
            return AsyncMock()
        
        with patch('app.websocket.manager.websocket_manager.broadcast_json', side_effect=mock_websocket_broadcast):
            
            # Step 1: Create agent
            print("🤖 Creating agent...")
            agent_data = TestDataGenerator.agent_data(
                name="workflow-test-agent",
                agent_type="integration-test",
                status="idle",
                tools=["read", "write", "execute"],
                capabilities=["python", "testing", "integration"]
            )
            
            agent = await api_helper.create_agent(**agent_data)
            agent_id = agent["id"]
            
            # Verify agent creation in database
            db_agent = await test_session.execute(select(Agent).where(Agent.id == agent_id))
            db_agent = db_agent.scalar_one_or_none()
            assert db_agent is not None
            assert db_agent.name == agent_data["name"]
            
            # Verify WebSocket notification for agent creation
            agent_created_messages = ws_helper.get_messages_by_type("agent_created")
            assert len(agent_created_messages) == 1
            assert agent_created_messages[0]["data"]["name"] == agent_data["name"]
            
            print(f"✅ Agent created: {agent['name']} ({agent_id})")
            
            # Step 2: Create and assign task to agent
            print("📋 Creating and assigning task...")
            task_data = TestDataGenerator.task_data(
                title="Integration Test Task",
                description="A comprehensive integration test task",
                priority="high",
                agent_id=agent_id,
                estimated_duration=600,
                metadata={
                    "test_type": "integration",
                    "workflow_step": "execution"
                }
            )
            
            task = await api_helper.create_task(**task_data)
            task_id = task["id"]
            
            # Verify task in database
            db_task = await test_session.execute(select(Task).where(Task.id == task_id))
            db_task = db_task.scalar_one_or_none()
            assert db_task is not None
            assert str(db_task.agent_id) == agent_id
            
            print(f"✅ Task created and assigned: {task['title']} ({task_id})")
            
            # Step 3: Update agent status to busy with current task
            print("🔄 Updating agent status...")
            status_update_data = {
                "status": "busy",
                "current_task_id": task_id,
                "current_task_title": task_data["title"]
            }
            
            status_response = await test_client.patch(
                f"/api/v1/agents/{agent_id}/status",
                json=status_update_data
            )
            assert status_response.status_code == 200
            
            updated_agent = status_response.json()
            assert updated_agent["status"] == "busy"
            assert updated_agent["current_task"]["id"] == task_id
            
            # Verify agent status update WebSocket message
            status_update_messages = ws_helper.get_messages_by_type("agent_status_updated")
            assert len(status_update_messages) == 1
            assert status_update_messages[0]["data"]["status"] == "busy"
            
            print("✅ Agent status updated to busy")
            
            # Step 4: Start task execution
            print("▶️ Starting task execution...")
            start_response = await test_client.patch(f"/api/v1/tasks/{task_id}/start")
            assert start_response.status_code == 200
            
            started_task = start_response.json()
            assert started_task["status"] == "in_progress"
            assert started_task["started_at"] is not None
            
            # Verify task start WebSocket message
            task_update_messages = ws_helper.get_messages_by_type("task_updated")
            assert len([msg for msg in task_update_messages if msg["data"]["status"] == "in_progress"]) >= 1
            
            print("✅ Task execution started")
            
            # Step 5: Simulate task progress updates
            print("📈 Updating task progress...")
            progress_steps = [25, 50, 75, 90]
            
            for progress in progress_steps:
                progress_response = await test_client.patch(
                    f"/api/v1/tasks/{task_id}/progress",
                    json={"progress": progress}
                )
                assert progress_response.status_code == 200
                
                updated_task = progress_response.json()
                assert updated_task["progress"] == progress
                
                # Small delay to simulate real progress
                await asyncio.sleep(0.1)
            
            # Verify progress update WebSocket messages
            progress_messages = ws_helper.get_messages_by_type("task_progress_updated")
            assert len(progress_messages) == len(progress_steps)
            
            print("✅ Task progress updated through all stages")
            
            # Step 6: Update agent metrics during execution
            print("📊 Updating agent performance metrics...")
            metrics_data = {
                "tasks_completed": 15,
                "tasks_failed": 2,
                "avg_response_time": 1.2,
                "uptime_percentage": 98.5
            }
            
            metrics_response = await test_client.patch(
                f"/api/v1/agents/{agent_id}/metrics",
                json=metrics_data
            )
            assert metrics_response.status_code == 200
            
            updated_metrics = metrics_response.json()["performance_metrics"]
            assert updated_metrics["tasks_completed"] == metrics_data["tasks_completed"]
            assert updated_metrics["avg_response_time"] == metrics_data["avg_response_time"]
            
            # Success rate should be calculated: 15/(15+2) * 100 = 88.24%
            expected_success_rate = (15 / (15 + 2)) * 100
            assert abs(updated_metrics["success_rate"] - expected_success_rate) < 0.01
            
            print("✅ Agent metrics updated")
            
            # Step 7: Complete task with result
            print("🏁 Completing task...")
            completion_data = {
                "result": {
                    "status": "success",
                    "output": "Integration test completed successfully",
                    "execution_time": 580,
                    "tests_passed": 42,
                    "coverage": 95.2
                }
            }
            
            completion_response = await test_client.patch(
                f"/api/v1/tasks/{task_id}/complete",
                json=completion_data
            )
            assert completion_response.status_code == 200
            
            completed_task = completion_response.json()
            assert completed_task["status"] == "completed"
            assert completed_task["progress"] == 100
            assert completed_task["completed_at"] is not None
            assert completed_task["result"]["status"] == "success"
            
            print("✅ Task completed successfully")
            
            # Step 8: Update agent status back to idle
            print("💤 Setting agent back to idle...")
            idle_status_data = {
                "status": "idle",
                "current_task_id": None,
                "current_task_title": None
            }
            
            idle_response = await test_client.patch(
                f"/api/v1/agents/{agent_id}/status",
                json=idle_status_data
            )
            assert idle_response.status_code == 200
            
            idle_agent = idle_response.json()
            assert idle_agent["status"] == "idle"
            assert idle_agent["current_task"]["id"] is None
            
            print("✅ Agent returned to idle status")
            
            # Step 9: Verify final state in database
            print("🔍 Verifying final database state...")
            
            # Check final agent state
            final_agent = await test_session.execute(select(Agent).where(Agent.id == agent_id))
            final_agent = final_agent.scalar_one_or_none()
            
            assert final_agent.status == "idle"
            assert final_agent.current_task_id is None
            assert final_agent.tasks_completed == metrics_data["tasks_completed"]
            assert final_agent.tasks_failed == metrics_data["tasks_failed"]
            
            # Check final task state
            final_task = await test_session.execute(select(Task).where(Task.id == task_id))
            final_task = final_task.scalar_one_or_none()
            
            assert final_task.status == "completed"
            assert final_task.progress == 100
            assert final_task.completed_at is not None
            assert str(final_task.agent_id) == agent_id
            
            print("✅ Database state verified")
            
            # Step 10: Verify complete WebSocket message flow
            print("📡 Verifying WebSocket message flow...")
            
            expected_message_types = [
                "agent_created",
                "task_created", 
                "agent_status_updated",  # busy
                "task_updated",          # started
                "task_progress_updated", # multiple progress updates
                "agent_metrics_updated",
                "task_updated",          # completed
                "agent_status_updated"   # idle
            ]
            
            for message_type in expected_message_types:
                messages = ws_helper.get_messages_by_type(message_type)
                assert len(messages) >= 1, f"Expected at least one {message_type} message"
            
            # Verify we have multiple progress messages
            progress_messages = ws_helper.get_messages_by_type("task_progress_updated")
            assert len(progress_messages) == 4  # One for each progress step
            
            print("✅ WebSocket message flow verified")
            
            # Step 11: Cleanup
            print("🧹 Cleaning up test data...")
            
            delete_task_response = await test_client.delete(f"/api/v1/tasks/{task_id}")
            assert delete_task_response.status_code == 200
            
            delete_agent_response = await test_client.delete(f"/api/v1/agents/{agent_id}")
            assert delete_agent_response.status_code == 200
            
            # Verify cleanup WebSocket messages
            delete_messages = ws_helper.get_messages_by_type("agent_deleted")
            assert len(delete_messages) == 1
            
            print("✅ Test data cleaned up")
            
            # Final verification - records should be deleted
            deleted_agent = await test_session.execute(select(Agent).where(Agent.id == agent_id))
            deleted_task = await test_session.execute(select(Task).where(Task.id == task_id))
            
            assert deleted_agent.scalar_one_or_none() is None
            assert deleted_task.scalar_one_or_none() is None
            
            print("🎉 Complete agent workflow test passed!")
    
    async def test_error_handling_workflow(self, test_client: AsyncClient, test_session):
        """Test workflow error handling scenarios"""
        
        api_helper = APITestHelper(test_client)
        
        with patch('app.websocket.manager.websocket_manager.broadcast_json', return_value=AsyncMock()):
            
            # Create agent
            agent = await api_helper.create_agent(name="error-test-agent")
            agent_id = agent["id"]
            
            # Create task
            task = await api_helper.create_task(
                title="Error Test Task",
                agent_id=agent_id
            )
            task_id = task["id"]
            
            # Start task
            await test_client.patch(f"/api/v1/tasks/{task_id}/start")
            
            # Simulate task failure
            failure_data = {
                "result": {
                    "status": "failure",
                    "error": "Simulated test failure",
                    "error_code": "TEST_ERROR"
                }
            }
            
            failure_response = await test_client.patch(
                f"/api/v1/tasks/{task_id}/fail",
                json=failure_data
            )
            
            if failure_response.status_code == 200:
                failed_task = failure_response.json()
                assert failed_task["status"] == "failed"
                assert failed_task["result"]["status"] == "failure"
            
            # Update agent status to error
            error_status = {
                "status": "error",
                "current_task_id": task_id,
                "error_message": "Task execution failed"
            }
            
            error_response = await test_client.patch(
                f"/api/v1/agents/{agent_id}/status",
                json=error_status
            )
            assert error_response.status_code == 200
            
            error_agent = error_response.json()
            assert error_agent["status"] == "error"
            
            # Update agent metrics to reflect failure
            failure_metrics = {
                "tasks_failed": 1
            }
            
            metrics_response = await test_client.patch(
                f"/api/v1/agents/{agent_id}/metrics",
                json=failure_metrics
            )
            assert metrics_response.status_code == 200
            
            updated_agent = metrics_response.json()
            assert updated_agent["performance_metrics"]["tasks_failed"] == 1
            
            # Cleanup
            await test_client.delete(f"/api/v1/tasks/{task_id}")
            await test_client.delete(f"/api/v1/agents/{agent_id}")
    
    async def test_concurrent_operations(self, test_client: AsyncClient, test_session):
        """Test concurrent operations on agents and tasks"""
        
        api_helper = APITestHelper(test_client)
        
        with patch('app.websocket.manager.websocket_manager.broadcast_json', return_value=AsyncMock()):
            
            # Create multiple agents concurrently
            agent_tasks = []
            for i in range(5):
                agent_data = TestDataGenerator.agent_data(
                    name=f"concurrent-agent-{i}",
                    agent_type="concurrent-test"
                )
                agent_tasks.append(api_helper.create_agent(**agent_data))
            
            agents = await asyncio.gather(*agent_tasks)
            agent_ids = [agent["id"] for agent in agents]
            
            assert len(agents) == 5
            
            # Create tasks for each agent concurrently
            task_creation_tasks = []
            for i, agent_id in enumerate(agent_ids):
                task_data = TestDataGenerator.task_data(
                    title=f"Concurrent Task {i}",
                    agent_id=agent_id
                )
                task_creation_tasks.append(api_helper.create_task(**task_data))
            
            tasks = await asyncio.gather(*task_creation_tasks)
            task_ids = [task["id"] for task in tasks]
            
            assert len(tasks) == 5
            
            # Update all agent statuses concurrently
            status_update_tasks = []
            for agent_id, task_id in zip(agent_ids, task_ids):
                status_data = {
                    "status": "busy",
                    "current_task_id": task_id
                }
                update_task = test_client.patch(
                    f"/api/v1/agents/{agent_id}/status",
                    json=status_data
                )
                status_update_tasks.append(update_task)
            
            status_responses = await asyncio.gather(*status_update_tasks)
            
            # Verify all updates succeeded
            for response in status_responses:
                assert response.status_code == 200
                agent_data = response.json()
                assert agent_data["status"] == "busy"
            
            # Cleanup all resources concurrently
            cleanup_tasks = []
            for task_id in task_ids:
                cleanup_tasks.append(test_client.delete(f"/api/v1/tasks/{task_id}"))
            for agent_id in agent_ids:
                cleanup_tasks.append(test_client.delete(f"/api/v1/agents/{agent_id}"))
            
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            print("✅ Concurrent operations test completed")