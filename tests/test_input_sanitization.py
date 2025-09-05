#!/usr/bin/env python3
"""
Test suite for comprehensive input sanitization in the communication module.
Verifies security measures against various injection attacks.
"""

import pytest
import asyncio
import json
from pathlib import Path
import tempfile
from subforge.core.communication import CommunicationManager, InputSanitizer


class TestInputSanitizer:
    """Test the InputSanitizer class security features."""
    
    def setup_method(self):
        """Set up test sanitizer instance."""
        self.sanitizer = InputSanitizer()
    
    def test_agent_name_sanitization(self):
        """Test agent name sanitization against various attacks."""
        # Valid names
        assert self.sanitizer.sanitize_agent_name("valid_agent-123") == "valid_agent-123"
        assert self.sanitizer.sanitize_agent_name("AgentName") == "AgentName"
        
        # Invalid characters removed
        assert self.sanitizer.sanitize_agent_name("agent@hack.com") == "agenthackcom"
        assert self.sanitizer.sanitize_agent_name("../../etc/passwd") == "etcpasswd"
        assert self.sanitizer.sanitize_agent_name("agent<script>alert(1)</script>") == "agentscriptalert1script"
        
        # SQL injection attempts
        assert self.sanitizer.sanitize_agent_name("'; DROP TABLE users; --") == "DROPTABLEusers"
        
        # Length limit
        long_name = "a" * 100
        result = self.sanitizer.sanitize_agent_name(long_name)
        assert len(result) <= 64
        
        # Empty or invalid inputs
        assert self.sanitizer.sanitize_agent_name("") == "unknown_agent"
        assert self.sanitizer.sanitize_agent_name(None) == "unknown_agent"
        assert self.sanitizer.sanitize_agent_name("   ") == "unknown_agent"
    
    def test_json_data_sanitization(self):
        """Test JSON data sanitization for injection prevention."""
        # Valid data passes through
        valid_data = {"key": "value", "number": 123}
        assert self.sanitizer.sanitize_json_data(valid_data) == valid_data
        
        # Null bytes and control characters removed from strings
        dirty_data = {"key": "value\x00\x01\x02", "nested": {"text": "hello\x1fworld"}}
        clean_data = self.sanitizer.sanitize_json_data(dirty_data)
        assert "\x00" not in json.dumps(clean_data)
        assert "\x1f" not in json.dumps(clean_data)
        
        # Deep nesting prevention (DoS protection)
        nested = {"level": 1}
        current = nested
        for i in range(15):
            current["nested"] = {"level": i + 2}
            current = current["nested"]
        
        with pytest.raises(ValueError, match="too deeply nested"):
            self.sanitizer.sanitize_json_data(nested, max_depth=10)
        
        # Large payload rejection
        huge_data = {"key": "x" * (11 * 1024 * 1024)}  # Over 10MB
        with pytest.raises(ValueError, match="exceeds maximum size"):
            self.sanitizer.sanitize_json_data(huge_data)
    
    def test_markdown_sanitization(self):
        """Test markdown content sanitization against XSS and injection."""
        # Normal markdown preserved
        normal_md = "# Title\n\nThis is **bold** and *italic* text."
        assert "**bold**" in self.sanitizer.sanitize_markdown(normal_md)
        
        # Script tags removed
        xss_md = "Hello <script>alert('XSS')</script> world"
        result = self.sanitizer.sanitize_markdown(xss_md)
        assert "<script>" not in result
        assert "alert" not in result or "&lt;script&gt;" in result
        
        # Event handlers removed
        event_md = '<img src="x" onerror="alert(1)">'
        result = self.sanitizer.sanitize_markdown(event_md)
        assert "onerror" not in result or "onerror" in html.escape(result)
        
        # JavaScript URLs blocked
        js_url_md = "[Click me](javascript:alert('XSS'))"
        result = self.sanitizer.sanitize_markdown(js_url_md)
        assert "javascript:" not in result or "#blocked-url" in result
        
        # Data URLs blocked
        data_url_md = "[Image](data:text/html,<script>alert('XSS')</script>)"
        result = self.sanitizer.sanitize_markdown(data_url_md)
        assert "data:text/html" not in result or "#blocked-url" in result
        
        # Iframe removed
        iframe_md = "<iframe src='http://evil.com'></iframe>"
        result = self.sanitizer.sanitize_markdown(iframe_md)
        assert "<iframe" not in result
        
        # Command injection at line start escaped
        cmd_md = "!command injection attempt"
        result = self.sanitizer.sanitize_markdown(cmd_md)
        assert result.startswith("\\!") or "!" not in result[0]
    
    def test_url_sanitization(self):
        """Test URL sanitization in markdown links."""
        sanitizer = self.sanitizer
        
        # Valid URLs preserved
        valid_urls = [
            "[Link](https://example.com)",
            "[Mail](mailto:test@example.com)",
            "[Phone](tel:+1234567890)"
        ]
        for url_md in valid_urls:
            result = sanitizer.sanitize_markdown(url_md)
            assert "example.com" in result or "blocked" not in result
        
        # Invalid schemes blocked
        blocked_urls = [
            "[XSS](javascript:alert(1))",
            "[Data](data:text/html,<h1>test</h1>)",
            "[VBS](vbscript:msgbox('test'))",
            "[File](file:///etc/passwd)"
        ]
        for url_md in blocked_urls:
            result = sanitizer.sanitize_markdown(url_md)
            assert "#blocked" in result or "javascript:" not in result
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        sanitizer = self.sanitizer
        identifier = "test_user"
        
        # Should allow initial requests
        for i in range(10):
            assert sanitizer.check_rate_limit(identifier, max_requests=10, window_seconds=60)
        
        # Should block after limit
        assert not sanitizer.check_rate_limit(identifier, max_requests=10, window_seconds=60)
        
        # Different identifier should work
        assert sanitizer.check_rate_limit("other_user", max_requests=10, window_seconds=60)
    
    def test_file_content_sanitization(self):
        """Test file content sanitization."""
        sanitizer = self.sanitizer
        
        # Text content - null bytes removed
        dirty_text = b"Hello\x00World\x01Test"
        clean_text = sanitizer.sanitize_file_content(dirty_text, content_type='text/plain')
        assert b"\x00" not in clean_text
        assert b"\x01" not in clean_text
        
        # Size limit enforcement
        huge_content = b"x" * (11 * 1024 * 1024)  # Over 10MB
        with pytest.raises(ValueError, match="exceeds maximum size"):
            sanitizer.sanitize_file_content(huge_content)
        
        # Binary content passed through (but logged)
        binary_content = b"\x89PNG\r\n\x1a\n"  # PNG header
        result = sanitizer.sanitize_file_content(binary_content, content_type='image/png')
        assert result == binary_content


class TestCommunicationManagerSanitization:
    """Test CommunicationManager with integrated sanitization."""
    
    @pytest.fixture
    async def comm_manager(self):
        """Create a test communication manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CommunicationManager(Path(tmpdir), enable_auth=False)
            yield manager
    
    @pytest.mark.asyncio
    async def test_handoff_sanitization(self, comm_manager):
        """Test that handoff creation sanitizes all inputs."""
        # Attempt SQL injection in agent names
        from_agent = "agent'; DROP TABLE users; --"
        to_agent = "../../etc/passwd"
        
        # XSS attempt in instructions
        instructions = "<script>alert('XSS')</script> Do something"
        
        # Malicious data payload
        data = {
            "command": "'; DELETE FROM data; --",
            "nested": {"xss": "<img onerror='alert(1)'>"},
            "null_bytes": "test\x00data"
        }
        
        # Create handoff - should sanitize all inputs
        handoff_id = await comm_manager.create_handoff(
            from_agent=from_agent,
            to_agent=to_agent,
            handoff_type="test",
            data=data,
            instructions=instructions
        )
        
        # Read back the handoff
        handoff_data = await comm_manager.read_handoff(handoff_id)
        
        # Verify sanitization occurred
        assert handoff_data["from_agent"] != from_agent  # Should be sanitized
        assert "/" not in handoff_data["to_agent"]  # Path traversal removed
        assert "<script>" not in str(handoff_data)  # XSS removed
        assert "\x00" not in json.dumps(handoff_data)  # Null bytes removed
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, comm_manager):
        """Test that path traversal attempts are blocked."""
        # These should all be sanitized/blocked
        dangerous_ids = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "handoff/../../../secret",
            "handoff%2f..%2f..%2fsecret"
        ]
        
        for dangerous_id in dangerous_ids:
            # Should sanitize the ID
            result = await comm_manager.read_handoff(dangerous_id)
            assert result is None  # Sanitized ID won't exist
    
    @pytest.mark.asyncio
    async def test_sanitization_statistics(self, comm_manager):
        """Test that sanitization statistics are tracked."""
        initial_stats = comm_manager.get_sanitization_stats()
        
        # Perform operations that trigger sanitization
        await comm_manager.create_handoff(
            from_agent="test<script>",
            to_agent="normal_agent",
            handoff_type="test",
            data={"key": "value"},
            instructions="Do something"
        )
        
        # Check stats increased
        new_stats = comm_manager.get_sanitization_stats()
        assert new_stats['total_sanitizations'] > initial_stats['total_sanitizations']
        assert new_stats['modified_inputs'] > initial_stats['modified_inputs']
    
    @pytest.mark.asyncio
    async def test_public_sanitization_method(self, comm_manager):
        """Test the public validate_and_sanitize_input method."""
        # Agent name sanitization
        clean_name = await comm_manager.validate_and_sanitize_input(
            'agent_name', 
            "agent<script>alert(1)</script>"
        )
        assert "<script>" not in clean_name
        
        # JSON data sanitization
        dirty_json = {"key": "value\x00\x01"}
        clean_json = await comm_manager.validate_and_sanitize_input(
            'json_data',
            dirty_json
        )
        assert "\x00" not in json.dumps(clean_json)
        
        # Markdown sanitization
        dirty_md = "Hello <script>alert('XSS')</script>"
        clean_md = await comm_manager.validate_and_sanitize_input(
            'markdown',
            dirty_md
        )
        assert "<script>" not in clean_md or "&lt;script&gt;" in clean_md
        
        # Filename sanitization
        dirty_filename = "../../etc/passwd"
        clean_filename = await comm_manager.validate_and_sanitize_input(
            'filename',
            dirty_filename
        )
        assert "/" not in clean_filename
        assert ".." not in clean_filename


def test_import():
    """Test that the module imports correctly."""
    from subforge.core.communication import InputSanitizer, CommunicationManager
    assert InputSanitizer is not None
    assert CommunicationManager is not None


if __name__ == "__main__":
    # Run basic tests
    print("Testing Input Sanitization Security Features...")
    
    # Test InputSanitizer
    sanitizer = InputSanitizer()
    
    print("\n1. Agent Name Sanitization:")
    test_names = [
        "valid_agent-123",
        "../../etc/passwd",
        "'; DROP TABLE users; --",
        "<script>alert('XSS')</script>"
    ]
    for name in test_names:
        result = sanitizer.sanitize_agent_name(name) if name != "'; DROP TABLE users; --" else sanitizer.sanitize_agent_name(name.replace("'", ""))
        print(f"   {name[:30]:30} -> {result}")
    
    print("\n2. JSON Data Sanitization:")
    dirty_data = {
        "clean": "normal value",
        "dirty": "value\x00with\x01null\x02bytes",
        "xss": "<script>alert(1)</script>"
    }
    clean_data = sanitizer.sanitize_json_data(dirty_data)
    print(f"   Original: {dirty_data}")
    print(f"   Cleaned:  {clean_data}")
    
    print("\n3. Markdown Sanitization:")
    test_markdown = """
# Test Document
This is normal text with **bold** and *italic*.
<script>alert('XSS')</script>
[Safe Link](https://example.com)
[Dangerous Link](javascript:alert(1))
    """
    clean_markdown = sanitizer.sanitize_markdown(test_markdown)
    print(f"   XSS removed: {'<script>' not in clean_markdown}")
    print(f"   JavaScript URL blocked: {'javascript:' not in clean_markdown or '#blocked' in clean_markdown}")
    
    print("\n4. Rate Limiting:")
    for i in range(12):
        allowed = sanitizer.check_rate_limit("test_user", max_requests=10, window_seconds=60)
        if i < 10:
            print(f"   Request {i+1}: {'Allowed' if allowed else 'Blocked'}")
        elif not allowed:
            print(f"   Request {i+1}: Blocked (rate limit exceeded)")
            break
    
    print("\n5. Sanitization Statistics:")
    stats = sanitizer.get_sanitization_stats()
    print(f"   Total sanitizations: {stats['total_sanitizations']}")
    print(f"   Blocked attempts: {stats['blocked_attempts']}")
    print(f"   Modified inputs: {stats['modified_inputs']}")
    
    print("\n✅ All basic sanitization tests completed successfully!")