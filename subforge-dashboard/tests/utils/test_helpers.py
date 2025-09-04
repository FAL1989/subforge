"""
Test utilities and helper functions
"""

import asyncio
import json
import random
import string
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDataGenerator:
    """Generate test data for various scenarios"""

    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate random string"""
        return "".join(random.choices(string.ascii_lowercase, k=length))

    @staticmethod
    def random_email() -> str:
        """Generate random email"""
        username = TestDataGenerator.random_string(8)
        domain = TestDataGenerator.random_string(6)
        return f"{username}@{domain}.com"

    @staticmethod
    def random_uuid() -> str:
        """Generate random UUID string"""
        return str(uuid.uuid4())

    @staticmethod
    def random_datetime(days_ago: int = 30) -> datetime:
        """Generate random datetime within specified days"""
        base = datetime.utcnow() - timedelta(days=days_ago)
        random_days = random.randint(0, days_ago)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)

        return base + timedelta(
            days=random_days, hours=random_hours, minutes=random_minutes
        )

    @staticmethod
    def agent_data(**overrides) -> Dict[str, Any]:
        """Generate agent test data"""
        data = {
            "name": f"test-agent-{TestDataGenerator.random_string(6)}",
            "agent_type": random.choice(
                ["frontend", "backend", "fullstack", "devops", "qa"]
            ),
            "status": random.choice(["active", "idle", "busy", "offline"]),
            "description": f"Test agent {TestDataGenerator.random_string(10)}",
            "model": random.choice(
                ["claude-3-sonnet", "claude-3-haiku", "claude-3-opus"]
            ),
            "tools": random.sample(["read", "write", "edit", "bash", "grep"], 3),
            "capabilities": random.sample(
                ["python", "javascript", "typescript", "docker"], 2
            ),
            "configuration": {
                "max_concurrent_tasks": random.randint(1, 5),
                "timeout": random.randint(60, 600),
                "test_mode": True,
            },
        }
        data.update(overrides)
        return data

    @staticmethod
    def task_data(**overrides) -> Dict[str, Any]:
        """Generate task test data"""
        data = {
            "title": f"Test Task {TestDataGenerator.random_string(8)}",
            "description": f"Task description {TestDataGenerator.random_string(20)}",
            "priority": random.choice(["low", "medium", "high", "urgent"]),
            "status": random.choice(["pending", "in_progress", "completed", "failed"]),
            "estimated_duration": random.randint(300, 3600),
            "metadata": {
                "complexity": random.choice(["simple", "medium", "complex"]),
                "test_mode": True,
            },
        }
        data.update(overrides)
        return data

    @staticmethod
    def workflow_data(**overrides) -> Dict[str, Any]:
        """Generate workflow test data"""
        num_steps = random.randint(2, 5)
        steps = []

        for i in range(num_steps):
            step = {
                "name": f"step_{i+1}",
                "type": "task",
                "dependencies": [
                    f"step_{j+1}" for j in range(i) if random.choice([True, False])
                ],
            }
            steps.append(step)

        data = {
            "name": f"test-workflow-{TestDataGenerator.random_string(6)}",
            "description": f"Test workflow {TestDataGenerator.random_string(15)}",
            "status": random.choice(["pending", "running", "completed", "failed"]),
            "configuration": {
                "max_parallel_tasks": random.randint(1, 3),
                "timeout": random.randint(1800, 7200),
            },
            "steps": steps,
        }
        data.update(overrides)
        return data


class APITestHelper:
    """Helper for API testing"""

    def __init__(self, client: AsyncClient):
        self.client = client

    async def create_agent(self, **data) -> Dict[str, Any]:
        """Create agent via API"""
        agent_data = TestDataGenerator.agent_data(**data)
        response = await self.client.post("/api/v1/agents/", json=agent_data)
        assert response.status_code == 200
        return response.json()

    async def create_task(self, **data) -> Dict[str, Any]:
        """Create task via API"""
        task_data = TestDataGenerator.task_data(**data)
        response = await self.client.post("/api/v1/tasks/", json=task_data)
        assert response.status_code == 200
        return response.json()

    async def create_workflow(self, **data) -> Dict[str, Any]:
        """Create workflow via API"""
        workflow_data = TestDataGenerator.workflow_data(**data)
        response = await self.client.post("/api/v1/workflows/", json=workflow_data)
        assert response.status_code == 200
        return response.json()

    async def wait_for_condition(
        self,
        condition: Callable[[], bool],
        timeout: float = 10.0,
        interval: float = 0.1,
    ) -> bool:
        """Wait for condition to become true"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if (
                await condition()
                if asyncio.iscoroutinefunction(condition)
                else condition()
            ):
                return True
            await asyncio.sleep(interval)

        return False


class DatabaseTestHelper:
    """Helper for database testing"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count_records(self, model_class) -> int:
        """Count records in table"""
        from sqlalchemy import func, select

        result = await self.session.execute(
            select(func.count()).select_from(model_class)
        )
        return result.scalar()

    async def cleanup_table(self, model_class):
        """Clean up all records in table"""
        from sqlalchemy import delete

        await self.session.execute(delete(model_class))
        await self.session.commit()

    async def verify_foreign_key_constraint(
        self, model_class, field_name: str, invalid_id: str
    ):
        """Verify foreign key constraint"""
        try:
            obj = model_class(**{field_name: invalid_id, "name": "test"})
            self.session.add(obj)
            await self.session.commit()
            return False  # Should not succeed
        except Exception:
            await self.session.rollback()
            return True  # Expected to fail


class WebSocketTestHelper:
    """Helper for WebSocket testing"""

    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.connected = False

    def on_message(self, message: str):
        """Handle WebSocket message"""
        try:
            data = json.loads(message)
            self.messages.append(data)
        except json.JSONDecodeError:
            pass

    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get messages of specific type"""
        return [msg for msg in self.messages if msg.get("type") == message_type]

    def clear_messages(self):
        """Clear message history"""
        self.messages.clear()

    def wait_for_message_type(
        self, message_type: str, timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """Wait for message of specific type"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            messages = self.get_messages_by_type(message_type)
            if messages:
                return messages[-1]  # Return latest message
            time.sleep(0.1)

        return None


class PerformanceTestHelper:
    """Helper for performance testing"""

    def __init__(self):
        self.timings: List[float] = []

    def time_operation(self, operation: Callable) -> Any:
        """Time an operation and store result"""
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(operation):
                result = asyncio.run(operation())
            else:
                result = operation()

            end_time = time.time()
            self.timings.append(end_time - start_time)
            return result
        except Exception as e:
            end_time = time.time()
            self.timings.append(end_time - start_time)
            raise e

    @property
    def average_time(self) -> float:
        """Get average execution time"""
        return sum(self.timings) / len(self.timings) if self.timings else 0

    @property
    def max_time(self) -> float:
        """Get maximum execution time"""
        return max(self.timings) if self.timings else 0

    @property
    def min_time(self) -> float:
        """Get minimum execution time"""
        return min(self.timings) if self.timings else 0

    def percentile(self, p: float) -> float:
        """Get percentile execution time"""
        if not self.timings:
            return 0

        sorted_timings = sorted(self.timings)
        index = int(len(sorted_timings) * p / 100)
        return sorted_timings[min(index, len(sorted_timings) - 1)]

    def clear_timings(self):
        """Clear timing history"""
        self.timings.clear()


class SecurityTestHelper:
    """Helper for security testing"""

    @staticmethod
    def sql_injection_payloads() -> List[str]:
        """Common SQL injection payloads"""
        return [
            "'; DROP TABLE agents; --",
            "' OR '1'='1",
            "1; EXEC xp_cmdshell('dir');--",
            "' UNION SELECT NULL, username, password FROM users--",
            "admin'--",
            "' OR 1=1--",
        ]

    @staticmethod
    def xss_payloads() -> List[str]:
        """Common XSS payloads"""
        return [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src='javascript:alert(`XSS`)'>",
        ]

    @staticmethod
    def command_injection_payloads() -> List[str]:
        """Common command injection payloads"""
        return [
            "; ls -la",
            "| cat /etc/passwd",
            "$(whoami)",
            "`id`",
            "; rm -rf /",
            "& net user",
        ]

    @staticmethod
    def is_sanitized(input_data: str, output_data: str) -> bool:
        """Check if output is properly sanitized"""
        dangerous_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
            "DROP TABLE",
            "UNION SELECT",
            "xp_cmdshell",
        ]

        output_lower = output_data.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in output_lower:
                return False

        return True


def assert_dict_subset(subset: Dict, full_dict: Dict, path: str = ""):
    """Assert that subset is contained in full_dict with detailed error messages"""
    for key, expected_value in subset.items():
        current_path = f"{path}.{key}" if path else key

        assert key in full_dict, f"Missing key '{current_path}' in response"

        actual_value = full_dict[key]

        if isinstance(expected_value, dict) and isinstance(actual_value, dict):
            assert_dict_subset(expected_value, actual_value, current_path)
        else:
            assert (
                actual_value == expected_value
            ), f"Value mismatch at '{current_path}': expected {expected_value}, got {actual_value}"


def assert_response_schema(
    response_data: Dict, required_fields: List[str], optional_fields: List[str] = None
):
    """Assert response matches expected schema"""
    optional_fields = optional_fields or []

    # Check required fields
    for field in required_fields:
        assert field in response_data, f"Required field '{field}' missing from response"

    # Check no unexpected fields (unless in optional)
    all_allowed_fields = set(required_fields + optional_fields)
    actual_fields = set(response_data.keys())

    unexpected_fields = actual_fields - all_allowed_fields
    assert not unexpected_fields, f"Unexpected fields in response: {unexpected_fields}"


def mock_websocket_message(message_type: str, data: Dict[str, Any]) -> str:
    """Create mock WebSocket message"""
    return json.dumps(
        {"type": message_type, "data": data, "timestamp": datetime.utcnow().isoformat()}
    )


def create_test_user_agent() -> str:
    """Create test user agent string"""
    return f"SubForge-Test-Client/{TestDataGenerator.random_string(6)}"