#!/usr/bin/env python3
"""
Security Tests for CommunicationManager
Tests path traversal prevention, input sanitization, and secure file operations
"""

import asyncio
import tempfile
import pytest
from pathlib import Path
import json

from subforge.core.communication import CommunicationManager


class TestCommunicationSecurity:
    """Test suite for security features in CommunicationManager"""
    
    @pytest.fixture
    async def comm_manager(self):
        """Create a CommunicationManager instance with temporary workspace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "test_workspace"
            yield CommunicationManager(workspace)
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, comm_manager):
        """Test that path traversal attempts are sanitized"""
        # Attempt path traversal in agent names
        handoff_id = await comm_manager.create_handoff(
            from_agent="../../../etc/passwd",
            to_agent="../../sensitive_data",
            handoff_type="test",
            data={"test": "data"},
            instructions="Test path traversal"
        )
        
        # Verify the agent names were sanitized
        handoff_data = comm_manager.read_handoff(handoff_id)
        assert handoff_data is not None
        assert ".." not in handoff_data['from_agent']
        assert "/" not in handoff_data['from_agent']
        assert ".." not in handoff_data['to_agent']
        assert "/" not in handoff_data['to_agent']
    
    @pytest.mark.asyncio
    async def test_special_character_sanitization(self, comm_manager):
        """Test that special characters are properly sanitized"""
        dangerous_chars = "../../etc/*?<>|:passwd"
        
        handoff_id = await comm_manager.create_handoff(
            from_agent="agent1",
            to_agent="agent2",
            handoff_type=dangerous_chars,
            data={"test": "data"},
            instructions="Test special characters"
        )
        
        handoff_data = comm_manager.read_handoff(handoff_id)
        assert handoff_data is not None
        # Check that dangerous characters are removed
        for char in ['/', '\\', '..', '*', '?', '<', '>', '|', ':']:
            assert char not in handoff_data['handoff_type']
    
    @pytest.mark.asyncio
    async def test_null_byte_injection(self, comm_manager):
        """Test that null bytes are handled safely"""
        handoff_id = await comm_manager.create_handoff(
            from_agent="agent\x00.txt",
            to_agent="agent2",
            handoff_type="test",
            data={"test": "data"},
            instructions="Test null byte"
        )
        
        handoff_data = comm_manager.read_handoff(handoff_id)
        assert handoff_data is not None
        assert '\x00' not in handoff_data['from_agent']
    
    @pytest.mark.asyncio
    async def test_markdown_injection_prevention(self, comm_manager):
        """Test that markdown injection is prevented"""
        malicious_instructions = "```\n</code>\n# Injected Header\n```python\nmalicious_code()\n```"
        
        handoff_id = await comm_manager.create_handoff(
            from_agent="agent1",
            to_agent="agent2",
            handoff_type="test",
            data={"test": "data"},
            instructions=malicious_instructions
        )
        
        # Read the markdown file to verify escaping
        md_file = comm_manager.handoffs_dir / f"{handoff_id}.md"
        assert md_file.exists()
        content = md_file.read_text()
        
        # Check that backticks were escaped
        assert "\\`" in content or "\\#" in content
    
    @pytest.mark.asyncio
    async def test_filename_length_limit(self, comm_manager):
        """Test that very long filenames are truncated"""
        long_name = "a" * 500  # Exceeds max length of 255
        
        handoff_id = await comm_manager.create_handoff(
            from_agent=long_name,
            to_agent="agent2",
            handoff_type="test",
            data={"test": "data"},
            instructions="Test long filename"
        )
        
        handoff_data = comm_manager.read_handoff(handoff_id)
        assert handoff_data is not None
        assert len(handoff_data['from_agent']) <= 255
    
    def test_invalid_handoff_read(self, comm_manager):
        """Test that invalid handoff IDs are rejected"""
        # Attempt to read with path traversal
        result = comm_manager.read_handoff("../../../etc/passwd")
        assert result is None
        
        # Attempt to read non-existent handoff
        result = comm_manager.read_handoff("nonexistent_handoff")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_safe_file_operations(self, comm_manager):
        """Test that file operations are restricted to workspace"""
        # Create a normal handoff
        handoff_id = await comm_manager.create_handoff(
            from_agent="test_agent",
            to_agent="target_agent",
            handoff_type="test",
            data={"key": "value"},
            instructions="Test instructions"
        )
        
        # Verify files are created in the correct directory
        json_file = comm_manager.handoffs_dir / f"{handoff_id}.json"
        md_file = comm_manager.handoffs_dir / f"{handoff_id}.md"
        
        assert json_file.exists()
        assert md_file.exists()
        
        # Verify paths are within workspace
        assert str(comm_manager.workspace_dir) in str(json_file.resolve())
        assert str(comm_manager.workspace_dir) in str(md_file.resolve())
    
    def test_list_handoffs_safety(self, comm_manager):
        """Test that listing handoffs is safe"""
        # Should handle empty directory gracefully
        handoffs = comm_manager.list_handoffs()
        assert isinstance(handoffs, list)
        
        # Should filter by agent name safely
        handoffs = comm_manager.list_handoffs(agent_name="../etc/passwd")
        assert isinstance(handoffs, list)
    
    @pytest.mark.asyncio
    async def test_data_integrity(self, comm_manager):
        """Test that data is preserved correctly despite sanitization"""
        test_data = {
            "endpoint": "/api/users",
            "method": "POST",
            "payload": {"name": "Test User", "email": "test@example.com"}
        }
        
        handoff_id = await comm_manager.create_handoff(
            from_agent="api_client",
            to_agent="api_handler",
            handoff_type="api_request",
            data=test_data,
            instructions="Process API request"
        )
        
        # Read back and verify data integrity
        handoff_data = comm_manager.read_handoff(handoff_id)
        assert handoff_data is not None
        assert handoff_data['data'] == test_data
        assert handoff_data['instructions'] == "Process API request"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])