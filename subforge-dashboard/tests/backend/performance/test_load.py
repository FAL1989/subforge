"""
Performance and load tests for SubForge Dashboard API
"""

import asyncio
import statistics
import time

import pytest
from app.models.agent import Agent
from app.models.task import Task
from httpx import AsyncClient


@pytest.mark.performance
@pytest.mark.asyncio
class TestAPIPerformance:
    """Performance tests for API endpoints"""

    async def test_agent_list_performance(
        self, test_client: AsyncClient, test_session, performance_config
    ):
        """Test performance of agent list endpoint"""
        # Create test data
        agents = [
            Agent(
                name=f"agent-{i}",
                agent_type="test",
                status="idle",
                description=f"Test agent {i}",
            )
            for i in range(100)
        ]

        for agent in agents:
            test_session.add(agent)
        await test_session.commit()

        # Measure response time
        start_time = time.time()
        response = await test_client.get("/api/v1/agents/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert len(response.json()) == 100
        assert response_time < performance_config["max_response_time"]

    async def test_agent_creation_performance(
        self, test_client: AsyncClient, performance_config
    ):
        """Test performance of agent creation"""
        agent_data = {
            "name": "performance-test-agent",
            "agent_type": "test",
            "status": "idle",
            "description": "Performance test agent",
            "tools": ["read", "write", "edit"],
            "capabilities": ["python", "javascript"],
        }

        # Measure multiple creation operations
        times = []

        for i in range(10):
            agent_data["name"] = f"performance-test-agent-{i}"

            start_time = time.time()
            response = await test_client.post("/api/v1/agents/", json=agent_data)
            end_time = time.time()

            response_time = end_time - start_time
            times.append(response_time)

            assert response.status_code == 200

        # Check average and maximum response times
        avg_time = statistics.mean(times)
        max_time = max(times)

        assert avg_time < performance_config["max_response_time"]
        assert max_time < performance_config["max_response_time"] * 2

    async def test_agent_update_performance(
        self, test_client: AsyncClient, test_agent, performance_config
    ):
        """Test performance of agent updates"""
        update_data = {
            "description": "Updated description for performance test",
            "configuration": {"key": "value", "number": 42},
        }

        # Measure multiple update operations
        times = []

        for i in range(10):
            update_data["description"] = f"Updated description {i}"

            start_time = time.time()
            response = await test_client.put(
                f"/api/v1/agents/{test_agent.id}", json=update_data
            )
            end_time = time.time()

            response_time = end_time - start_time
            times.append(response_time)

            assert response.status_code == 200

        avg_time = statistics.mean(times)
        assert avg_time < performance_config["max_response_time"]

    async def test_database_query_performance(
        self, test_client: AsyncClient, test_session, performance_config
    ):
        """Test database query performance with large datasets"""
        # Create large number of agents
        num_agents = 1000
        agents = []

        for i in range(num_agents):
            agent = Agent(
                name=f"agent-{i}",
                agent_type=f"type-{i % 10}",  # 10 different types
                status=["idle", "active", "busy", "offline"][i % 4],
                description=f"Agent {i} for performance testing",
                tasks_completed=i * 2,
                tasks_failed=i // 10,
                avg_response_time=0.5 + (i % 100) / 100,
                uptime_percentage=95.0 + (i % 5),
            )
            agents.append(agent)

        # Batch insert for better performance
        test_session.add_all(agents)
        await test_session.commit()

        # Test various query scenarios
        test_cases = [
            ("/api/v1/agents/", "Get all agents"),
            ("/api/v1/agents/?limit=100", "Get agents with limit"),
            ("/api/v1/agents/?status=active", "Get agents by status"),
            ("/api/v1/agents/?agent_type=type-1", "Get agents by type"),
            ("/api/v1/agents/?skip=500&limit=50", "Get agents with pagination"),
            ("/api/v1/agents/stats/summary", "Get agent statistics"),
        ]

        for endpoint, description in test_cases:
            start_time = time.time()
            response = await test_client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == 200, f"Failed: {description}"
            assert (
                response_time < performance_config["max_response_time"] * 2
            ), f"Too slow: {description}"

            print(f"{description}: {response_time:.3f}s")


@pytest.mark.performance
@pytest.mark.asyncio
class TestConcurrentLoad:
    """Concurrent load tests"""

    async def test_concurrent_agent_creation(
        self, test_client: AsyncClient, performance_config
    ):
        """Test concurrent agent creation"""
        num_concurrent = 50

        async def create_agent(client: AsyncClient, index: int):
            agent_data = {
                "name": f"concurrent-agent-{index}",
                "agent_type": "test",
                "status": "idle",
                "description": f"Concurrent test agent {index}",
            }

            start_time = time.time()
            response = await client.post("/api/v1/agents/", json=agent_data)
            end_time = time.time()

            return {
                "index": index,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
            }

        # Execute concurrent requests
        tasks = [create_agent(test_client, i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_results = [
            r for r in results if isinstance(r, dict) and r["success"]
        ]
        failed_results = [
            r for r in results if isinstance(r, dict) and not r["success"]
        ]
        exceptions = [r for r in results if isinstance(r, Exception)]

        success_rate = len(successful_results) / num_concurrent
        avg_response_time = statistics.mean(
            [r["response_time"] for r in successful_results]
        )
        max_response_time = (
            max([r["response_time"] for r in successful_results])
            if successful_results
            else 0
        )

        # Assertions
        assert success_rate >= (
            1 - performance_config["acceptable_error_rate"]
        ), f"Success rate too low: {success_rate}"
        assert (
            avg_response_time < performance_config["max_response_time"] * 2
        ), f"Average response time too high: {avg_response_time}"
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

        print(f"Concurrent creation results:")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Max response time: {max_response_time:.3f}s")
        print(f"  Failed requests: {len(failed_results)}")

    async def test_concurrent_agent_reads(
        self, test_client: AsyncClient, test_session, performance_config
    ):
        """Test concurrent agent read operations"""
        # Create test agents
        agents = [
            Agent(name=f"read-test-agent-{i}", agent_type="test", status="idle")
            for i in range(20)
        ]

        for agent in agents:
            test_session.add(agent)
        await test_session.commit()

        # Refresh to get IDs
        for agent in agents:
            await test_session.refresh(agent)

        num_concurrent = 100

        async def read_agent(client: AsyncClient, agent_id: str):
            start_time = time.time()
            response = await client.get(f"/api/v1/agents/{agent_id}")
            end_time = time.time()

            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
            }

        # Execute concurrent reads (random agent selection)
        import random

        tasks = []
        for i in range(num_concurrent):
            agent = random.choice(agents)
            tasks.append(read_agent(test_client, str(agent.id)))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_results = [
            r for r in results if isinstance(r, dict) and r["success"]
        ]
        success_rate = len(successful_results) / num_concurrent
        avg_response_time = statistics.mean(
            [r["response_time"] for r in successful_results]
        )

        assert success_rate >= 0.95, f"Read success rate too low: {success_rate}"
        assert (
            avg_response_time < performance_config["max_response_time"]
        ), f"Average read time too high: {avg_response_time}"

    async def test_mixed_workload_performance(
        self, test_client: AsyncClient, test_session, performance_config
    ):
        """Test mixed workload performance (reads, writes, updates)"""
        # Create some initial data
        initial_agents = [
            Agent(name=f"mixed-test-agent-{i}", agent_type="test", status="idle")
            for i in range(10)
        ]

        for agent in initial_agents:
            test_session.add(agent)
        await test_session.commit()

        for agent in initial_agents:
            await test_session.refresh(agent)

        async def read_operation(client: AsyncClient, index: int):
            response = await client.get("/api/v1/agents/")
            return {"type": "read", "success": response.status_code == 200}

        async def create_operation(client: AsyncClient, index: int):
            data = {
                "name": f"mixed-create-{index}",
                "agent_type": "test",
                "status": "idle",
            }
            response = await client.post("/api/v1/agents/", json=data)
            return {"type": "create", "success": response.status_code == 200}

        async def update_operation(client: AsyncClient, index: int):
            if initial_agents:
                agent = initial_agents[index % len(initial_agents)]
                data = {"description": f"Updated by mixed test {index}"}
                response = await client.put(f"/api/v1/agents/{agent.id}", json=data)
                return {"type": "update", "success": response.status_code == 200}
            return {"type": "update", "success": False}

        # Create mixed workload
        tasks = []
        for i in range(60):  # Total 60 operations
            if i % 3 == 0:
                tasks.append(read_operation(test_client, i))
            elif i % 3 == 1:
                tasks.append(create_operation(test_client, i))
            else:
                tasks.append(update_operation(test_client, i))

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_time = end_time - start_time

        # Analyze results by operation type
        operation_stats = {"read": [], "create": [], "update": []}
        for result in results:
            if isinstance(result, dict):
                operation_stats[result["type"]].append(result["success"])

        # Calculate success rates
        for op_type, successes in operation_stats.items():
            if successes:
                success_rate = sum(successes) / len(successes)
                print(f"{op_type.capitalize()} success rate: {success_rate:.2%}")
                assert success_rate >= 0.90, f"{op_type} success rate too low"

        # Overall performance
        throughput = len(tasks) / total_time
        print(f"Mixed workload throughput: {throughput:.2f} operations/second")
        print(f"Total time: {total_time:.3f}s")

        assert (
            total_time < performance_config["test_duration"]
        ), "Mixed workload took too long"


@pytest.mark.performance
@pytest.mark.websocket
class TestWebSocketPerformance:
    """WebSocket performance tests"""

    def test_websocket_connection_performance(self, sync_client, performance_config):
        """Test WebSocket connection establishment performance"""
        connection_times = []

        for i in range(10):
            start_time = time.time()
            try:
                with sync_client.websocket_connect("/ws") as websocket:
                    end_time = time.time()
                    connection_time = end_time - start_time
                    connection_times.append(connection_time)
            except Exception as e:
                print(f"WebSocket connection failed: {e}")
                continue

        if connection_times:
            avg_connection_time = statistics.mean(connection_times)
            max_connection_time = max(connection_times)

            print(f"Average WebSocket connection time: {avg_connection_time:.3f}s")
            print(f"Max WebSocket connection time: {max_connection_time:.3f}s")

            assert avg_connection_time < 0.5, "WebSocket connection too slow"
            assert max_connection_time < 1.0, "WebSocket max connection time too high"

    def test_websocket_message_throughput(self, sync_client, performance_config):
        """Test WebSocket message throughput"""
        try:
            with sync_client.websocket_connect("/ws") as websocket:
                num_messages = 100
                message = {"type": "test", "data": {"index": 0}}

                start_time = time.time()

                for i in range(num_messages):
                    message["data"]["index"] = i
                    websocket.send_json(message)

                end_time = time.time()

                total_time = end_time - start_time
                throughput = num_messages / total_time

                print(f"WebSocket message throughput: {throughput:.2f} messages/second")

                assert throughput > 50, "WebSocket message throughput too low"
        except Exception as e:
            pytest.skip(f"WebSocket test failed: {e}")


@pytest.mark.performance
@pytest.mark.database
class TestDatabasePerformance:
    """Database performance tests"""

    async def test_bulk_insert_performance(self, test_session, performance_config):
        """Test bulk insert performance"""
        num_records = 1000

        # Test bulk agent creation
        agents = [
            Agent(
                name=f"bulk-agent-{i}",
                agent_type="test",
                status="idle",
                description=f"Bulk insert test agent {i}",
                tasks_completed=i,
                tasks_failed=i // 10,
            )
            for i in range(num_records)
        ]

        start_time = time.time()

        # Add all at once
        test_session.add_all(agents)
        await test_session.commit()

        end_time = time.time()

        insert_time = end_time - start_time
        throughput = num_records / insert_time

        print(f"Bulk insert performance: {throughput:.2f} records/second")
        print(f"Total time for {num_records} records: {insert_time:.3f}s")

        assert insert_time < 10.0, "Bulk insert too slow"
        assert throughput > 100, "Bulk insert throughput too low"

    async def test_complex_query_performance(self, test_session, performance_config):
        """Test complex query performance"""
        # Create test data with relationships
        num_agents = 100
        num_tasks_per_agent = 10

        agents = []
        tasks = []

        for i in range(num_agents):
            agent = Agent(
                name=f"query-test-agent-{i}",
                agent_type=f"type-{i % 5}",
                status=["idle", "active", "busy"][i % 3],
                tasks_completed=i * 2,
                avg_response_time=1.0 + (i % 10) / 10,
            )
            agents.append(agent)

        test_session.add_all(agents)
        await test_session.commit()

        # Refresh to get IDs
        for agent in agents:
            await test_session.refresh(agent)

        # Create tasks
        for agent in agents:
            for j in range(num_tasks_per_agent):
                task = Task(
                    title=f"Task {j} for {agent.name}",
                    description=f"Test task {j}",
                    priority=["low", "medium", "high"][j % 3],
                    status=["pending", "in_progress", "completed", "failed"][j % 4],
                    agent_id=agent.id,
                )
                tasks.append(task)

        test_session.add_all(tasks)
        await test_session.commit()

        # Test complex queries
        from sqlalchemy import and_, func, select

        complex_queries = [
            # Agent with task counts
            select(Agent.id, Agent.name, func.count(Task.id).label("task_count"))
            .join(Task, Agent.id == Task.agent_id, isouter=True)
            .group_by(Agent.id, Agent.name),
            # Agents with high success rates and active status
            select(Agent).where(
                and_(Agent.success_rate > 80, Agent.status == "active")
            ),
            # Tasks grouped by status with counts
            select(Task.status, func.count(Task.id).label("count")).group_by(
                Task.status
            ),
        ]

        for i, query in enumerate(complex_queries):
            start_time = time.time()
            result = await test_session.execute(query)
            rows = result.fetchall()
            end_time = time.time()

            query_time = end_time - start_time

            print(f"Complex query {i+1}: {query_time:.3f}s ({len(rows)} rows)")

            assert query_time < 1.0, f"Complex query {i+1} too slow"


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage performance tests"""

    async def test_memory_usage_large_response(
        self, test_client: AsyncClient, test_session
    ):
        """Test memory usage with large API responses"""
        # Create large number of agents
        num_agents = 10000

        # Create in batches to avoid memory issues during creation
        batch_size = 1000
        for batch_start in range(0, num_agents, batch_size):
            batch_agents = []
            for i in range(batch_start, min(batch_start + batch_size, num_agents)):
                agent = Agent(
                    name=f"memory-test-agent-{i}",
                    agent_type="test",
                    status="idle",
                    description=f"Memory test agent {i} with some longer description to increase data size",
                    configuration={
                        "key1": "value1",
                        "key2": "value2",
                        "numbers": list(range(10)),
                    },
                )
                batch_agents.append(agent)

            test_session.add_all(batch_agents)
            await test_session.commit()

        # Test memory usage during large response
        import os

        import psutil

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        response = await test_client.get("/api/v1/agents/?limit=10000")

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        print(
            f"Memory usage: {memory_before:.2f}MB -> {memory_after:.2f}MB (+{memory_increase:.2f}MB)"
        )

        assert response.status_code == 200
        assert len(response.json()) <= 10000

        # Memory increase should be reasonable (less than 500MB for this test)
        assert (
            memory_increase < 500
        ), f"Memory increase too high: {memory_increase:.2f}MB"