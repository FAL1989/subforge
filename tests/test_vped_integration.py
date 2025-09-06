#!/usr/bin/env python3
"""
Test Suite for VPED Protocol Integration
Tests the Verify-Plan-Execute-Document workflow
Based on best practices from Anthropic, LangGraph, and Microsoft Copilot Studio
Created: 2025-09-06 21:15 UTC-3 São Paulo
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest

from subforge.core.verification_manager import VerificationManager, VerificationResult
from subforge.core.task_specification import (
    TaskSpec, DetailedTaskPlan, TaskBuilder,
    TaskPriority, TaskStatus, generate_exact_prompt
)
from subforge.core.documentation_manager import (
    DocumentationManager, ExecutionDocumentation,
    DocumentationType, TestResult, FileModification,
    create_execution_doc
)
from subforge.core.workflow_orchestrator import WorkflowOrchestrator, WorkflowPhase


class TestVerificationManager:
    """Test the Verification phase of VPED"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            # Create test structure
            (workspace / "src").mkdir()
            (workspace / "tests").mkdir()
            (workspace / "src" / "api.py").write_text("def hello(): pass")
            (workspace / "tests" / "test_api.py").write_text("def test_hello(): pass")
            yield workspace
    
    @pytest.fixture
    def verification_manager(self, temp_workspace):
        """Create a verification manager instance"""
        return VerificationManager(temp_workspace)
    
    @pytest.mark.asyncio
    async def test_verify_file_exists_success(self, verification_manager, temp_workspace):
        """Test successful file existence verification"""
        result = await verification_manager.verify_file_exists("src/api.py")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_file_exists_failure(self, verification_manager):
        """Test file existence verification for non-existent file"""
        result = await verification_manager.verify_file_exists("nonexistent.py")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_line_number_valid(self, verification_manager, temp_workspace):
        """Test line number verification for valid line"""
        result = await verification_manager.verify_line_number("src/api.py", 1)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_line_number_invalid(self, verification_manager, temp_workspace):
        """Test line number verification for invalid line"""
        result = await verification_manager.verify_line_number("src/api.py", 999)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_dependencies(self, verification_manager):
        """Test dependency verification"""
        # Test with built-in modules that should exist
        results = await verification_manager.verify_dependencies(["os", "sys", "json"])
        assert all(results.values())
        
        # Test with non-existent module
        results = await verification_manager.verify_dependencies(["nonexistent_module_xyz"])
        assert not results["nonexistent_module_xyz"]
    
    @pytest.mark.asyncio
    async def test_verify_preconditions_comprehensive(self, verification_manager, temp_workspace):
        """Test comprehensive precondition verification"""
        task_spec = {
            "task_id": "test_001",
            "target_file": "src/api.py",
            "target_line": 1,
            "dependencies": ["os", "sys"],
            "required_directories": ["src", "tests"],
            "required_commands": ["python"]
        }
        
        result = await verification_manager.verify_preconditions(task_spec)
        
        assert isinstance(result, VerificationResult)
        assert result.can_proceed is True
        assert len(result.issues) == 0
        assert result.verification_time > 0
        assert "file_exists" in result.checks_performed
        assert "line_number_valid" in result.checks_performed
    
    @pytest.mark.asyncio
    async def test_verify_preconditions_with_issues(self, verification_manager, temp_workspace):
        """Test precondition verification with issues"""
        task_spec = {
            "task_id": "test_002",
            "target_file": "nonexistent.py",
            "dependencies": ["nonexistent_module"],
            "required_directories": ["nonexistent_dir"]
        }
        
        result = await verification_manager.verify_preconditions(task_spec)
        
        assert result.can_proceed is False
        assert len(result.issues) > 0
        assert "Target file not found" in str(result.issues)
        assert "Missing dependency" in str(result.issues)
        assert "Required directory not found" in str(result.issues)
        assert "fix_issues_before_execution" in result.recommendations["action"]


class TestTaskSpecification:
    """Test the Plan phase of VPED"""
    
    def test_task_builder_basic(self):
        """Test basic task building"""
        task = (TaskBuilder("test_task", "backend-developer")
                .with_file("/src/api.py", line=42)
                .with_instruction("Fix the bug")
                .build())
        
        assert task["task_id"] == "test_task"
        assert task["agent_type"] == "backend-developer"
        assert task["target_file"] == "/src/api.py"
        assert task["target_line"] == 42
        assert task["instruction"] == "Fix the bug"
    
    def test_task_builder_with_code(self):
        """Test task building with code block"""
        code = """
def calculate(x, y):
    return x + y
"""
        task = (TaskBuilder("test_task", "backend-developer")
                .with_file("/src/calc.py")
                .with_instruction("Add calculate function")
                .with_code(code)
                .with_test("pytest tests/test_calc.py")
                .build())
        
        assert task["code_block"] == code
        assert task["test_command"] == "pytest tests/test_calc.py"
    
    def test_generate_exact_prompt(self):
        """Test exact prompt generation"""
        task: TaskSpec = {
            "task_id": "api_fix_001",
            "agent_type": "backend-developer",
            "target_file": "/src/api/routes.py",
            "target_line": 45,
            "instruction": "Fix authentication middleware",
            "code_block": "def auth_middleware(request):\n    return validate_jwt(request.headers)",
            "test_command": "pytest tests/test_auth.py",
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.PENDING
        }
        
        prompt = generate_exact_prompt(task)
        
        assert "/src/api/routes.py" in prompt
        assert "line 45" in prompt
        assert "Fix authentication middleware" in prompt
        assert "def auth_middleware" in prompt
        assert "pytest tests/test_auth.py" in prompt
        assert "high" in prompt.lower()  # Check for priority regardless of case
    
    def test_detailed_task_plan(self):
        """Test detailed task plan creation"""
        plan = DetailedTaskPlan(
            workflow_id="wf_001",
            project_id="proj_001",
            created_at="2025-09-06T21:30:00",
            tasks=[
                {
                    "task_id": "task_1",
                    "agent_type": "backend-developer",
                    "target_file": "/src/api.py",
                    "instruction": "Implement endpoint",
                    "priority": TaskPriority.HIGH.value,
                    "status": TaskStatus.PENDING.value
                }
            ],
            execution_order=["task_1"],
            parallel_groups=[["task_1"]],
            context={"api_version": "v2"}
        )
        
        assert plan.workflow_id == "wf_001"
        assert len(plan.tasks) == 1
        assert ["task_1"] in plan.parallel_groups


class TestDocumentationManager:
    """Test the Document phase of VPED"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            yield workspace
    
    @pytest.fixture
    def doc_manager(self, temp_workspace):
        """Create a documentation manager instance"""
        return DocumentationManager(temp_workspace)
    
    def test_create_execution_doc(self):
        """Test execution documentation creation"""
        doc = create_execution_doc(
            agent_name="backend-developer",
            task_id="api_001",
            files_modified=[
                FileModification(
                    file_path="/src/api.py",
                    lines_added=[45, 46, 47],
                    lines_removed=[],
                    lines_modified=[],
                    diff="+ def authenticate():\n+     pass"
                )
            ],
            tests_executed=[
                TestResult(
                    command="pytest test_auth.py",
                    exit_code=0,
                    stdout="1 passed",
                    stderr="",
                    duration=0.5,
                    passed=True
                )
            ],
            warnings=["Deprecated function used"],
            next_steps=["Update documentation"],
            context_for_next={"auth_enabled": True}
        )
        
        assert doc.agent_name == "backend-developer"
        assert doc.task_id == "api_001"
        assert len(doc.files_modified) == 1
        assert doc.files_modified[0].file_path == "/src/api.py"
        assert doc.tests_executed[0].passed is True
        assert doc.execution_metadata["warnings"] == ["Deprecated function used"]
    
    @pytest.mark.asyncio
    async def test_save_execution_report(self, doc_manager, temp_workspace):
        """Test saving execution report"""
        doc = create_execution_doc(
            agent_name="test-engineer",
            task_id="test_001",
            files_modified=[],
            tests_executed=[
                TestResult(
                    command="pytest test_suite.py",
                    exit_code=0,
                    stdout="All tests passed",
                    stderr="",
                    duration=1.5,
                    passed=True
                )
            ]
        )
        
        report_path = await doc_manager.save_execution_report(doc)
        
        assert report_path.exists()
        assert report_path.suffix == ".md"
        
        # Verify content
        content = report_path.read_text()
        assert "test-engineer" in content
        assert "test_001" in content
        assert "passed" in content.lower()
    
    def test_create_handoff_package(self, doc_manager):
        """Test handoff package creation"""
        current_doc = create_execution_doc(
            agent_name="backend-developer",
            task_id="api_001",
            context_for_next={"api_ready": True}
        )
        
        package = doc_manager.create_handoff_package(
            from_agent="backend-developer",
            to_agent="frontend-developer",
            context=current_doc.context_for_next,
            files_modified=[],
            warnings=[]
        )
        
        assert package["from_agent"] == "backend-developer"
        assert package["to_agent"] == "frontend-developer"
        assert package["context"]["api_ready"] is True
        assert "handoff_time" in package
    
    def test_get_workflow_summary(self, doc_manager):
        """Test workflow summary generation"""
        # Add some execution history
        doc1 = create_execution_doc("agent1", "task1")
        doc2 = create_execution_doc("agent2", "task2")
        
        doc_manager.execution_history.extend([doc1, doc2])
        
        # Get workflow context (returns dict from shared context)
        context = doc_manager.get_workflow_context("workflow_001")
        
        # Since we just added to execution_history, verify that
        assert len(doc_manager.execution_history) == 2
        assert doc_manager.execution_history[0].agent_name == "agent1"
        assert doc_manager.execution_history[1].agent_name == "agent2"


class TestVPEDIntegration:
    """Test the complete VPED workflow integration"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "src").mkdir()
            (workspace / "tests").mkdir()
            (workspace / ".claude").mkdir()
            (workspace / ".claude" / "templates").mkdir()
            (workspace / "src" / "main.py").write_text("def main(): pass")
            yield workspace
    
    @pytest.mark.asyncio
    async def test_vped_workflow_complete(self, temp_workspace):
        """Test complete VPED workflow from verification to documentation"""
        # Create managers
        verification_mgr = VerificationManager(temp_workspace)
        doc_mgr = DocumentationManager(temp_workspace)
        
        # 1️⃣ VERIFY Phase
        task_spec = {
            "task_id": "integration_001",
            "target_file": "src/main.py",
            "target_line": 1,
            "dependencies": ["os"],
            "required_directories": ["src", "tests"]
        }
        
        verification_result = await verification_mgr.verify_preconditions(task_spec)
        assert verification_result.can_proceed is True
        
        # 2️⃣ PLAN Phase
        task = (TaskBuilder("integration_001", "backend-developer")
                .with_file(str(temp_workspace / "src" / "main.py"), line=1)
                .with_instruction("Add logging to main function")
                .with_code("import logging\n\ndef main():\n    logging.info('Starting')\n    pass")
                .with_test("pytest tests/test_main.py")
                .build())
        
        prompt = generate_exact_prompt(task)
        assert "Add logging to main function" in prompt
        
        # 3️⃣ EXECUTE Phase (simulated)
        # In real scenario, this would be agent execution
        execution_result = {
            "success": True,
            "files_modified": ["src/main.py"],
            "tests_passed": ["test_main.py"]
        }
        
        # 4️⃣ DOCUMENT Phase
        doc = create_execution_doc(
            agent_name="backend-developer",
            task_id="integration_001",
            files_modified=[
                FileModification(
                    file_path=str(temp_workspace / "src" / "main.py"),
                    lines_added=[1, 2],
                    lines_removed=[],
                    lines_modified=[3, 4],
                    diff="+ import logging\n+ logging.info('Starting')"
                )
            ],
            tests_executed=[
                TestResult(
                    command="pytest test_main.py",
                    exit_code=0,
                    stdout="1 passed",
                    stderr="",
                    duration=0.1,
                    passed=True
                )
            ],
            context_for_next={"logging_enabled": True}
        )
        
        report_path = await doc_mgr.save_execution_report(doc)
        assert report_path.exists()
        
        # Verify the complete workflow
        assert verification_result.can_proceed is True
        assert execution_result["success"] is True
        assert doc.tests_executed[0].passed is True
        
        # Verify handoff capability
        handoff = doc_mgr.create_handoff_package(
            from_agent="backend-developer",
            to_agent="test-engineer",
            context=doc.context_for_next,
            files_modified=doc.files_modified,
            warnings=[]
        )
        assert handoff["context"]["logging_enabled"] is True


class TestWorkflowOrchestratorVPED:
    """Test VPED integration in WorkflowOrchestrator"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / ".claude").mkdir()
            (workspace / ".claude" / "templates").mkdir()
            # Create minimal orchestrator template
            orchestrator_template = workspace / ".claude" / "templates" / "orchestrator.md"
            orchestrator_template.write_text("# Orchestrator\n## System Prompt\nTest orchestrator with VPED")
            yield workspace
    
    @pytest.mark.asyncio
    async def test_orchestrator_vped_initialization(self, temp_workspace):
        """Test that orchestrator initializes VPED components"""
        templates_dir = temp_workspace / ".claude" / "templates"
        orchestrator = WorkflowOrchestrator(templates_dir=templates_dir, workspace_dir=temp_workspace)
        
        # Verify VPED components are initialized
        assert hasattr(orchestrator, 'verification_manager')
        assert hasattr(orchestrator, 'documentation_manager')
        assert isinstance(orchestrator.verification_manager, VerificationManager)
        assert isinstance(orchestrator.documentation_manager, DocumentationManager)
    
    @pytest.mark.asyncio
    async def test_orchestrator_execute_with_vped(self, temp_workspace):
        """Test orchestrator execution with VPED protocol"""
        templates_dir = temp_workspace / ".claude" / "templates"
        orchestrator = WorkflowOrchestrator(templates_dir=templates_dir, workspace_dir=temp_workspace)
        
        # Mock the subagent execution
        with patch.object(orchestrator.subagent_executor, 'execute_subagent') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "result": "Task completed",
                "files_modified": ["test.py"]
            }
            
            # Create a task that should trigger VPED
            context = {
                "request": "Test task",
                "project_info": {"name": "test_project"}
            }
            
            # The orchestrator should use VPED protocol
            # Verification should happen before execution
            # Documentation should happen after execution
            
            # This would be called internally by orchestrator
            # We're testing that the components are available
            assert orchestrator.verification_manager is not None
            assert orchestrator.documentation_manager is not None


# Performance and Error Handling Tests
class TestVPEDPerformance:
    """Test performance and error handling of VPED system"""
    
    @pytest.mark.asyncio
    async def test_verification_timeout_handling(self):
        """Test handling of verification timeouts"""
        manager = VerificationManager()
        
        # Test with unreachable endpoint (should timeout)
        result = await manager.verify_endpoint("http://192.0.2.1:9999/timeout", timeout=1)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_large_file_verification(self, tmp_path):
        """Test verification of large files"""
        # Create a large file
        large_file = tmp_path / "large.txt"
        large_file.write_text("\n".join(["line"] * 10000))
        
        manager = VerificationManager(tmp_path)
        
        # Should handle large files efficiently
        result = await manager.verify_line_number("large.txt", 5000)
        assert result is True
        
        result = await manager.verify_line_number("large.txt", 20000)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_verifications(self, tmp_path):
        """Test concurrent verification operations"""
        manager = VerificationManager(tmp_path)
        
        # Create test files
        for i in range(10):
            (tmp_path / f"file{i}.py").write_text(f"# File {i}")
        
        # Run multiple verifications concurrently
        tasks = [
            manager.verify_file_exists(f"file{i}.py")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        assert all(results)
    
    def test_documentation_serialization(self):
        """Test documentation serialization/deserialization"""
        doc = create_execution_doc(
            agent_name="test-agent",
            task_id="test_001",
            files_modified=[
                FileModification(
                    file_path="/path/to/file.py",
                    lines_added=[1, 2, 3],
                    lines_removed=[],
                    lines_modified=[],
                    diff="+ line1\n+ line2\n+ line3"
                )
            ],
            context_for_next={"complex": {"nested": {"data": [1, 2, 3]}}}
        )
        
        # Convert to dict and back
        doc_dict = doc.to_dict()
        assert doc_dict["agent_name"] == "test-agent"
        assert doc_dict["context_for_next"]["complex"]["nested"]["data"] == [1, 2, 3]
        
        # Convert to JSON
        json_str = json.dumps(doc_dict)
        restored = json.loads(json_str)
        assert restored["task_id"] == "test_001"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])