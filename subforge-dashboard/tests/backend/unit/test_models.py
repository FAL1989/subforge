"""
Unit tests for SQLAlchemy models
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select

from app.models.agent import Agent
from app.models.task import Task
from app.models.workflow import Workflow
from app.models.system_metrics import SystemMetrics


@pytest.mark.unit
@pytest.mark.models
class TestAgentModel:
    """Tests for Agent model"""
    
    async def test_agent_creation(self, test_session):
        """Test creating an agent"""
        agent = Agent(
            name="test-agent",
            agent_type="backend-developer",
            status="idle",
            description="Test agent"
        )
        
        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)
        
        assert agent.id is not None
        assert agent.name == "test-agent"
        assert agent.agent_type == "backend-developer"
        assert agent.status == "idle"
        assert agent.created_at is not None
        assert agent.updated_at is not None
        assert agent.is_active is True
    
    async def test_agent_default_values(self, test_session):
        """Test agent default values"""
        agent = Agent(name="test", agent_type="test-type")
        
        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)
        
        assert agent.status == "idle"
        assert agent.model == "claude-3-sonnet"
        assert agent.tools == []
        assert agent.capabilities == []
        assert agent.configuration == {}
        assert agent.tasks_completed == 0
        assert agent.tasks_failed == 0
        assert agent.success_rate == 0.0
        assert agent.avg_response_time == 0.0
        assert agent.uptime_percentage == 100.0
        assert agent.is_active is True
    
    async def test_agent_to_dict(self, test_session):
        """Test agent to_dict method"""
        agent = Agent(
            name="test-agent",
            agent_type="backend-developer",
            status="active",
            description="Test agent",
            model="claude-3-opus",
            tools=["read", "write"],
            capabilities=["python", "fastapi"]
        )
        
        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)
        
        agent_dict = agent.to_dict()
        
        assert agent_dict["name"] == "test-agent"
        assert agent_dict["type"] == "backend-developer"
        assert agent_dict["status"] == "active"
        assert agent_dict["description"] == "Test agent"
        assert agent_dict["configuration"]["model"] == "claude-3-opus"
        assert agent_dict["configuration"]["tools"] == ["read", "write"]
        assert agent_dict["configuration"]["capabilities"] == ["python", "fastapi"]
        assert "performance_metrics" in agent_dict
        assert "created_at" in agent_dict
        assert "updated_at" in agent_dict
    
    async def test_update_activity(self, test_session):
        """Test updating activity timestamp"""
        agent = Agent(name="test", agent_type="test")
        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)
        
        original_activity = agent.last_activity
        
        # Wait a small amount to ensure different timestamp
        import asyncio
        await asyncio.sleep(0.01)
        
        agent.update_activity()
        
        assert agent.last_activity > original_activity
    
    async def test_update_heartbeat(self, test_session):
        """Test updating heartbeat timestamp"""
        agent = Agent(name="test", agent_type="test")
        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)
        
        original_heartbeat = agent.last_heartbeat
        
        # Wait a small amount to ensure different timestamp
        import asyncio
        await asyncio.sleep(0.01)
        
        agent.update_heartbeat()
        
        assert agent.last_heartbeat > original_heartbeat
    
    async def test_calculate_success_rate(self, test_session):
        """Test success rate calculation"""
        agent = Agent(name="test", agent_type="test")
        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)
        
        # Test with no tasks
        agent.calculate_success_rate()
        assert agent.success_rate == 0.0
        
        # Test with some tasks
        agent.tasks_completed = 8
        agent.tasks_failed = 2
        agent.calculate_success_rate()
        assert agent.success_rate == 80.0
        
        # Test with all successful tasks
        agent.tasks_completed = 10
        agent.tasks_failed = 0
        agent.calculate_success_rate()
        assert agent.success_rate == 100.0
        
        # Test with all failed tasks
        agent.tasks_completed = 0
        agent.tasks_failed = 5
        agent.calculate_success_rate()
        assert agent.success_rate == 0.0


@pytest.mark.unit
@pytest.mark.models
class TestTaskModel:
    """Tests for Task model"""
    
    async def test_task_creation(self, test_session):
        """Test creating a task"""
        task = Task(
            title="Test Task",
            description="A test task",
            priority="high",
            status="pending"
        )
        
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "A test task"
        assert task.priority == "high"
        assert task.status == "pending"
        assert task.created_at is not None
        assert task.updated_at is not None
    
    async def test_task_default_values(self, test_session):
        """Test task default values"""
        task = Task(title="Test", description="Test task")
        
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)
        
        assert task.priority == "medium"
        assert task.status == "pending"
        assert task.metadata == {}
        assert task.estimated_duration is None
        assert task.actual_duration is None
        assert task.progress == 0
    
    async def test_task_with_agent(self, test_session, test_agent):
        """Test task assignment to agent"""
        task = Task(
            title="Test Task",
            description="A test task",
            agent_id=test_agent.id
        )
        
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)
        
        assert task.agent_id == test_agent.id
    
    async def test_task_to_dict(self, test_session):
        """Test task to_dict method"""
        task = Task(
            title="Test Task",
            description="A test task",
            priority="high",
            status="in_progress",
            progress=50,
            metadata={"key": "value"}
        )
        
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)
        
        task_dict = task.to_dict()
        
        assert task_dict["title"] == "Test Task"
        assert task_dict["description"] == "A test task"
        assert task_dict["priority"] == "high"
        assert task_dict["status"] == "in_progress"
        assert task_dict["progress"] == 50
        assert task_dict["metadata"] == {"key": "value"}
        assert "created_at" in task_dict
        assert "updated_at" in task_dict


@pytest.mark.unit
@pytest.mark.models
class TestWorkflowModel:
    """Tests for Workflow model"""
    
    async def test_workflow_creation(self, test_session):
        """Test creating a workflow"""
        workflow = Workflow(
            name="test-workflow",
            description="A test workflow",
            status="pending"
        )
        
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        
        assert workflow.id is not None
        assert workflow.name == "test-workflow"
        assert workflow.description == "A test workflow"
        assert workflow.status == "pending"
        assert workflow.created_at is not None
        assert workflow.updated_at is not None
    
    async def test_workflow_default_values(self, test_session):
        """Test workflow default values"""
        workflow = Workflow(name="test", description="test workflow")
        
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        
        assert workflow.status == "pending"
        assert workflow.configuration == {}
        assert workflow.steps == []
        assert workflow.current_step == 0
        assert workflow.progress == 0.0
    
    async def test_workflow_with_steps(self, test_session):
        """Test workflow with steps"""
        steps = [
            {"name": "step1", "type": "task", "dependencies": []},
            {"name": "step2", "type": "task", "dependencies": ["step1"]}
        ]
        
        workflow = Workflow(
            name="test-workflow",
            description="Test workflow with steps",
            steps=steps
        )
        
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        
        assert len(workflow.steps) == 2
        assert workflow.steps[0]["name"] == "step1"
        assert workflow.steps[1]["dependencies"] == ["step1"]
    
    async def test_workflow_to_dict(self, test_session):
        """Test workflow to_dict method"""
        workflow = Workflow(
            name="test-workflow",
            description="Test workflow",
            status="running",
            progress=25.5,
            current_step=1,
            configuration={"timeout": 3600}
        )
        
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        
        workflow_dict = workflow.to_dict()
        
        assert workflow_dict["name"] == "test-workflow"
        assert workflow_dict["description"] == "Test workflow"
        assert workflow_dict["status"] == "running"
        assert workflow_dict["progress"] == 25.5
        assert workflow_dict["current_step"] == 1
        assert workflow_dict["configuration"] == {"timeout": 3600}
        assert "created_at" in workflow_dict
        assert "updated_at" in workflow_dict


@pytest.mark.unit
@pytest.mark.models
class TestSystemMetricsModel:
    """Tests for SystemMetrics model"""
    
    async def test_system_metrics_creation(self, test_session):
        """Test creating system metrics"""
        metrics = SystemMetrics(
            metric_name="cpu_usage",
            metric_value=75.5,
            unit="percent"
        )
        
        test_session.add(metrics)
        await test_session.commit()
        await test_session.refresh(metrics)
        
        assert metrics.id is not None
        assert metrics.metric_name == "cpu_usage"
        assert metrics.metric_value == 75.5
        assert metrics.unit == "percent"
        assert metrics.timestamp is not None
    
    async def test_system_metrics_with_metadata(self, test_session):
        """Test system metrics with metadata"""
        metadata = {"host": "server-01", "region": "us-west-2"}
        
        metrics = SystemMetrics(
            metric_name="memory_usage",
            metric_value=85.2,
            unit="percent",
            metadata=metadata
        )
        
        test_session.add(metrics)
        await test_session.commit()
        await test_session.refresh(metrics)
        
        assert metrics.metadata == metadata
    
    async def test_system_metrics_to_dict(self, test_session):
        """Test system metrics to_dict method"""
        metrics = SystemMetrics(
            metric_name="disk_usage",
            metric_value=42.8,
            unit="GB",
            metadata={"device": "/dev/sda1"}
        )
        
        test_session.add(metrics)
        await test_session.commit()
        await test_session.refresh(metrics)
        
        metrics_dict = metrics.to_dict()
        
        assert metrics_dict["metric_name"] == "disk_usage"
        assert metrics_dict["metric_value"] == 42.8
        assert metrics_dict["unit"] == "GB"
        assert metrics_dict["metadata"] == {"device": "/dev/sda1"}
        assert "timestamp" in metrics_dict


@pytest.mark.unit
@pytest.mark.models
@pytest.mark.database
class TestModelRelationships:
    """Tests for model relationships"""
    
    async def test_agent_task_relationship(self, test_session):
        """Test agent-task relationship"""
        # Create agent
        agent = Agent(name="test-agent", agent_type="test")
        test_session.add(agent)
        await test_session.commit()
        await test_session.refresh(agent)
        
        # Create task assigned to agent
        task = Task(
            title="Test Task",
            description="Test task",
            agent_id=agent.id
        )
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)
        
        # Verify relationship
        assert task.agent_id == agent.id
        
        # Query tasks by agent
        result = await test_session.execute(
            select(Task).where(Task.agent_id == agent.id)
        )
        agent_tasks = result.scalars().all()
        assert len(agent_tasks) == 1
        assert agent_tasks[0].title == "Test Task"
    
    async def test_workflow_task_relationship(self, test_session):
        """Test workflow-task relationship"""
        # Create workflow
        workflow = Workflow(name="test-workflow", description="Test workflow")
        test_session.add(workflow)
        await test_session.commit()
        await test_session.refresh(workflow)
        
        # Create tasks in workflow
        task1 = Task(
            title="Task 1",
            description="First task",
            workflow_id=workflow.id
        )
        task2 = Task(
            title="Task 2", 
            description="Second task",
            workflow_id=workflow.id
        )
        
        test_session.add_all([task1, task2])
        await test_session.commit()
        
        # Query tasks by workflow
        result = await test_session.execute(
            select(Task).where(Task.workflow_id == workflow.id)
        )
        workflow_tasks = result.scalars().all()
        assert len(workflow_tasks) == 2
        
        task_titles = {task.title for task in workflow_tasks}
        assert "Task 1" in task_titles
        assert "Task 2" in task_titles


@pytest.mark.unit
@pytest.mark.models
class TestModelValidation:
    """Tests for model validation and constraints"""
    
    async def test_agent_required_fields(self, test_session):
        """Test agent required fields validation"""
        # Missing name should fail
        with pytest.raises(Exception):
            agent = Agent(agent_type="test")
            test_session.add(agent)
            await test_session.commit()
        
        # Missing agent_type should fail
        with pytest.raises(Exception):
            agent = Agent(name="test")
            test_session.add(agent)
            await test_session.commit()
    
    async def test_task_required_fields(self, test_session):
        """Test task required fields validation"""
        # Missing title should fail
        with pytest.raises(Exception):
            task = Task(description="test")
            test_session.add(task)
            await test_session.commit()
        
        # Missing description should fail
        with pytest.raises(Exception):
            task = Task(title="test")
            test_session.add(task)
            await test_session.commit()
    
    async def test_workflow_required_fields(self, test_session):
        """Test workflow required fields validation"""
        # Missing name should fail
        with pytest.raises(Exception):
            workflow = Workflow(description="test")
            test_session.add(workflow)
            await test_session.commit()
        
        # Missing description should fail
        with pytest.raises(Exception):
            workflow = Workflow(name="test")
            test_session.add(workflow)
            await test_session.commit()
    
    async def test_system_metrics_required_fields(self, test_session):
        """Test system metrics required fields validation"""
        # Missing metric_name should fail
        with pytest.raises(Exception):
            metrics = SystemMetrics(metric_value=10.0, unit="percent")
            test_session.add(metrics)
            await test_session.commit()
        
        # Missing metric_value should fail
        with pytest.raises(Exception):
            metrics = SystemMetrics(metric_name="test", unit="percent")
            test_session.add(metrics)
            await test_session.commit()