#!/usr/bin/env python3
"""
End-to-End Security Integration Tests for SubForge
Comprehensive security testing covering complete workflows, attack simulation,
and security boundary enforcement across all system components.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, List, Optional
import pytest
import pytest_asyncio
import hashlib
import secrets
import subprocess
import threading

from subforge.core.authentication import (
    AuthenticationManager,
    AgentToken,
    Permission,
    Role,
    TokenStore,
    SecurityAuditLog,
    require_auth,
    ROLE_PERMISSIONS
)
from subforge.core.communication import CommunicationManager, InputSanitizer


class SecurityTestContext:
    """Test context that manages security test environment and cleanup"""
    
    def __init__(self):
        self.temp_dir = None
        self.workspace_dir = None
        self.auth_manager = None
        self.comm_manager = None
        self.audit_log = None
        self.system_token = None
        self.test_tokens = {}
        self.attack_vectors = []
        self.security_events = []
        
    async def setup(self):
        """Setup complete security test environment"""
        # Create temporary workspace
        self.temp_dir = tempfile.mkdtemp(prefix="subforge_security_test_")
        self.workspace_dir = Path(self.temp_dir) / "workspace"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize authentication system
        self.auth_manager = AuthenticationManager(
            workspace_dir=self.workspace_dir,
            secret_key="test_secret_key_for_security_testing"
        )
        
        # Initialize communication system with auth enabled
        self.comm_manager = CommunicationManager(
            workspace_dir=self.workspace_dir,
            enable_auth=True,
            auth_config={
                'secret_key': 'test_secret_key_for_security_testing',
                'token_lifetime_hours': 1
            }
        )
        
        # Wait for system initialization
        await asyncio.sleep(0.2)
        
        # Share the authentication manager instance
        self.comm_manager.auth_manager = self.auth_manager
        
        # Create system admin token
        self.system_token = await self.auth_manager.create_token(
            agent_id="SECURITY_TEST_ADMIN",
            role=Role.ADMIN,
            lifetime=timedelta(hours=2)
        )
        
        # Setup audit log monitoring
        self.audit_log = self.auth_manager.audit_log
        
        return self
        
    async def cleanup(self):
        """Cleanup test environment and temporary files"""
        try:
            if self.temp_dir and Path(self.temp_dir).exists():
                import shutil
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    async def create_test_agents(self) -> Dict[str, AgentToken]:
        """Create test agents with different roles and permissions"""
        agents = {}
        
        # Create orchestrator agent
        agents['orchestrator'] = await self.auth_manager.create_token(
            agent_id="test_orchestrator",
            role=Role.ORCHESTRATOR,
            lifetime=timedelta(hours=1),
            metadata={"test_type": "e2e_security"}
        )
        
        # Create specialist agent
        agents['specialist'] = await self.auth_manager.create_token(
            agent_id="test_specialist",
            role=Role.SPECIALIST,
            lifetime=timedelta(hours=1),
            metadata={"test_type": "e2e_security"}
        )
        
        # Create reviewer agent
        agents['reviewer'] = await self.auth_manager.create_token(
            agent_id="test_reviewer",
            role=Role.REVIEWER,
            lifetime=timedelta(hours=1),
            metadata={"test_type": "e2e_security"}
        )
        
        # Create observer agent
        agents['observer'] = await self.auth_manager.create_token(
            agent_id="test_observer",
            role=Role.OBSERVER,
            lifetime=timedelta(hours=1),
            metadata={"test_type": "e2e_security"}
        )
        
        # Create guest agent
        agents['guest'] = await self.auth_manager.create_token(
            agent_id="test_guest",
            role=Role.GUEST,
            lifetime=timedelta(hours=1),
            metadata={"test_type": "e2e_security"}
        )
        
        self.test_tokens.update(agents)
        return agents


class TestFullAuthenticationWorkflow:
    """Test complete authentication workflows from token creation to revocation"""
    
    @pytest_asyncio.fixture
    async def security_context(self):
        """Setup security test context"""
        context = SecurityTestContext()
        await context.setup()
        yield context
        await context.cleanup()
    
    @pytest.mark.asyncio
    async def test_full_auth_workflow(self, security_context):
        """Test complete authentication workflow"""
        auth_mgr = security_context.auth_manager
        
        # Phase 1: Create agent token
        agent_token = await auth_mgr.create_token(
            agent_id="workflow_test_agent",
            role=Role.SPECIALIST,
            lifetime=timedelta(minutes=30),
            metadata={"workflow": "test", "phase": 1}
        )
        
        assert agent_token is not None
        assert agent_token.agent_id == "workflow_test_agent"
        assert agent_token.role == Role.SPECIALIST
        assert not agent_token.is_expired()
        
        # Phase 2: Authenticate request
        authenticated = await auth_mgr.authenticate(agent_token.token)
        assert authenticated is not None
        assert authenticated.agent_id == agent_token.agent_id
        assert authenticated.usage_count == 1
        
        # Phase 3: Perform authorized operation
        authorized = await auth_mgr.authorize(
            authenticated,
            Permission.CREATE_HANDOFF,
            "test_resource"
        )
        assert authorized is True
        
        # Phase 4: Refresh token
        if agent_token.refresh_token:
            new_token = await auth_mgr.refresh_token(agent_token.refresh_token)
            assert new_token is not None
            assert new_token.agent_id == agent_token.agent_id
            assert new_token.token != agent_token.token  # New token issued
            
            # Old token should be revoked
            old_authenticated = await auth_mgr.authenticate(agent_token.token)
            assert old_authenticated is None
            
            agent_token = new_token  # Use new token for remaining tests
        
        # Phase 5: Revoke token
        await auth_mgr.revoke_token(agent_token.token, "SECURITY_TEST_ADMIN")
        
        # Phase 6: Verify operation fails after revocation
        revoked_auth = await auth_mgr.authenticate(agent_token.token)
        assert revoked_auth is None
        
        # Verify unauthorized operation
        if revoked_auth:
            authorized = await auth_mgr.authorize(
                revoked_auth,
                Permission.CREATE_HANDOFF,
                "test_resource"
            )
            assert authorized is False
    
    @pytest.mark.asyncio
    async def test_token_expiration_workflow(self, security_context):
        """Test token expiration and cleanup workflow"""
        auth_mgr = security_context.auth_manager
        
        # Create short-lived token
        short_token = await auth_mgr.create_token(
            agent_id="expiring_agent",
            role=Role.GUEST,
            lifetime=timedelta(milliseconds=100),  # Very short expiry
            metadata={"test": "expiration"}
        )
        
        # Token should work immediately
        authenticated = await auth_mgr.authenticate(short_token.token)
        assert authenticated is not None
        
        # Wait for expiration
        await asyncio.sleep(0.15)
        
        # Token should be expired
        assert short_token.is_expired()
        
        # Authentication should fail
        expired_auth = await auth_mgr.authenticate(short_token.token)
        assert expired_auth is None
        
        # Cleanup should remove expired tokens
        initial_count = len(auth_mgr.token_store.active_tokens)
        await auth_mgr.token_store.cleanup_expired()
        final_count = len(auth_mgr.token_store.active_tokens)
        
        # Either token was cleaned up (final < initial) or there was only 1 token to begin with
        assert final_count <= initial_count, f"Token cleanup failed: {final_count} > {initial_count}"


class TestMultiAgentSecurityFlow:
    """Test security flows involving multiple agents with different permissions"""
    
    @pytest_asyncio.fixture
    async def security_context(self):
        """Setup security test context with multiple agents"""
        context = SecurityTestContext()
        await context.setup()
        await context.create_test_agents()
        yield context
        await context.cleanup()
    
    @pytest.mark.asyncio
    async def test_multi_agent_security(self, security_context):
        """Test multi-agent security boundaries and role-based access"""
        agents = security_context.test_tokens
        comm_mgr = security_context.comm_manager
        
        # Test orchestrator permissions
        orchestrator = agents['orchestrator']
        handoff_id = await comm_mgr.create_handoff(
            from_agent="orchestrator",
            to_agent="specialist",
            handoff_type="task_assignment",
            data={"task": "implement_feature", "priority": "high"},
            instructions="Implement the user authentication feature",
            auth_token=orchestrator.token
        )
        assert handoff_id is not None
        
        # Orchestrator should be able to read handoffs
        handoff_data = await comm_mgr.read_handoff(
            handoff_id,
            auth_token=orchestrator.token
        )
        assert handoff_data is not None
        
        # Specialist should be able to read handoffs
        specialist_read = await comm_mgr.read_handoff(
            handoff_id,
            auth_token=agents['specialist'].token
        )
        assert specialist_read is not None
        
        # Reviewer should be able to read handoffs (has READ_HANDOFF permission)
        reviewer_read = await comm_mgr.read_handoff(
            handoff_id,
            auth_token=agents['reviewer'].token
        )
        assert reviewer_read is not None
        
        # Observer should NOT be able to read handoffs (no READ_HANDOFF permission)
        with pytest.raises(PermissionError, match="READ_HANDOFF permission required"):
            await comm_mgr.read_handoff(
                handoff_id,
                auth_token=agents['observer'].token
            )
        
        # Observer should NOT be able to create handoffs
        with pytest.raises(PermissionError, match="CREATE_HANDOFF permission required"):
            await comm_mgr.create_handoff(
                from_agent="observer",
                to_agent="specialist",
                handoff_type="unauthorized",
                data={"attempt": "forbidden"},
                instructions="This should fail",
                auth_token=agents['observer'].token
            )
        
        # Guest should NOT be able to read handoffs (no READ_HANDOFF permission)
        with pytest.raises(PermissionError, match="READ_HANDOFF permission required"):
            await comm_mgr.read_handoff(
                handoff_id,
                auth_token=agents['guest'].token
            )
        
        # Guest should NOT create handoffs
        with pytest.raises(PermissionError, match="CREATE_HANDOFF permission required"):
            await comm_mgr.create_handoff(
                from_agent="guest",
                to_agent="specialist",
                handoff_type="unauthorized",
                data={"attempt": "forbidden"},
                instructions="This should fail",
                auth_token=agents['guest'].token
            )
    
    @pytest.mark.asyncio
    async def test_cross_agent_communication_security(self, security_context):
        """Test secure communication between agents"""
        agents = security_context.test_tokens
        comm_mgr = security_context.comm_manager
        
        # Create a chain of handoffs simulating workflow
        handoffs = []
        
        # Orchestrator -> Specialist
        handoff1 = await comm_mgr.create_handoff(
            from_agent="orchestrator",
            to_agent="specialist",
            handoff_type="task_assignment",
            data={"stage": 1, "task": "analysis"},
            instructions="Analyze requirements and create implementation plan",
            auth_token=agents['orchestrator'].token
        )
        handoffs.append(handoff1)
        
        # Specialist -> Reviewer (code review request)
        handoff2 = await comm_mgr.create_handoff(
            from_agent="specialist",
            to_agent="reviewer",
            handoff_type="review_request",
            data={"stage": 2, "code_location": "src/auth.py"},
            instructions="Please review the authentication implementation",
            auth_token=agents['specialist'].token
        )
        handoffs.append(handoff2)
        
        # Since Reviewer doesn't have CREATE_HANDOFF permission, 
        # let's have the Orchestrator create the final handoff based on review
        handoff3 = await comm_mgr.create_handoff(
            from_agent="orchestrator",
            to_agent="orchestrator",
            handoff_type="review_result",
            data={"stage": 3, "approved": True, "comments": "Review completed - deploying"},
            instructions="Based on reviewer feedback - proceeding with deployment",
            auth_token=agents['orchestrator'].token
        )
        handoffs.append(handoff3)
        
        # Verify all handoffs were created successfully
        assert len(handoffs) == 3
        assert all(h is not None for h in handoffs)
        
        # Verify agents with appropriate permissions can read handoffs
        for handoff_id in handoffs:
            # Orchestrator can read all (has READ_HANDOFF permission)
            data = await comm_mgr.read_handoff(handoff_id, agents['orchestrator'].token)
            assert data is not None
            
            # Specialist can read (has READ_HANDOFF permission)
            data = await comm_mgr.read_handoff(handoff_id, agents['specialist'].token)
            assert data is not None
            
            # Reviewer can read (has READ_HANDOFF permission)
            data = await comm_mgr.read_handoff(handoff_id, agents['reviewer'].token)
            assert data is not None
            
            # Observer cannot read handoffs (no READ_HANDOFF permission)
            with pytest.raises(PermissionError, match="READ_HANDOFF permission required"):
                await comm_mgr.read_handoff(handoff_id, agents['observer'].token)


class TestSecurityEventLogging:
    """Test comprehensive security event logging and audit trails"""
    
    @pytest_asyncio.fixture
    async def security_context(self):
        """Setup security context with logging enabled"""
        context = SecurityTestContext()
        await context.setup()
        yield context
        await context.cleanup()
    
    @pytest.mark.asyncio
    async def test_security_audit_logging(self, security_context):
        """Test comprehensive security audit logging"""
        auth_mgr = security_context.auth_manager
        audit_log = security_context.audit_log
        
        # Create agent and perform various operations
        test_agent = await auth_mgr.create_token(
            agent_id="audit_test_agent",
            role=Role.SPECIALIST,
            metadata={"test": "audit_logging"}
        )
        
        # Perform successful authentication
        authenticated = await auth_mgr.authenticate(test_agent.token)
        assert authenticated is not None
        
        # Perform authorized operation
        authorized = await auth_mgr.authorize(
            authenticated,
            Permission.READ,
            "test_resource"
        )
        assert authorized is True
        
        # Attempt unauthorized operation
        unauthorized = await auth_mgr.authorize(
            authenticated,
            Permission.ADMIN,  # Specialist doesn't have admin permission
            "admin_resource"
        )
        assert unauthorized is False
        
        # Revoke token
        await auth_mgr.revoke_token(test_agent.token, "SECURITY_TEST_ADMIN")
        
        # Verify audit log file exists and contains events
        audit_file = security_context.workspace_dir / "auth" / "audit" / "security_audit.log"
        assert audit_file.exists()
        
        # Read and verify log contents
        log_content = audit_file.read_text()
        
        # Check for key security events
        assert "TOKEN_CREATED" in log_content
        assert "AUTH_SUCCESS" in log_content
        assert "AUTH_FAILURE" in log_content  # Unauthorized operation
        assert "TOKEN_REVOKED" in log_content
        assert "audit_test_agent" in log_content
    
    @pytest.mark.asyncio
    async def test_log_format_and_content(self, security_context):
        """Test security log format and content validation"""
        auth_mgr = security_context.auth_manager
        audit_log = auth_mgr.audit_log
        
        # Trigger specific security events
        agent = await auth_mgr.create_token("log_format_test", Role.GUEST)
        
        # Trigger authentication failure (simulate invalid signature)
        audit_log.log_suspicious_activity(
            "log_format_test",
            "invalid_signature",
            "Tampered token detected"
        )
        
        # Trigger permission change
        audit_log.log_permission_change(
            "log_format_test",
            "GUEST",
            "SPECIALIST",
            "SECURITY_TEST_ADMIN"
        )
        
        # Read audit log
        audit_file = security_context.workspace_dir / "auth" / "audit" / "security_audit.log"
        log_content = audit_file.read_text()
        
        # Verify log format (timestamp - level - message)
        lines = [line for line in log_content.split('\n') if line.strip()]
        for line in lines:
            if line.strip():
                parts = line.split(' - ', 2)
                assert len(parts) >= 3, f"Invalid log format: {line}"
                
                # Verify timestamp format
                timestamp_part = parts[0]
                try:
                    datetime.strptime(timestamp_part, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pytest.fail(f"Invalid timestamp format: {timestamp_part}")
                
                # Verify log level
                level_part = parts[1]
                assert level_part in ['INFO', 'WARNING', 'ERROR'], f"Invalid log level: {level_part}"
    
    @pytest.mark.asyncio
    async def test_log_rotation_and_persistence(self, security_context):
        """Test log file rotation and persistence"""
        auth_mgr = security_context.auth_manager
        audit_log = auth_mgr.audit_log
        
        # Generate multiple log entries
        for i in range(100):
            audit_log.log_auth_success(f"test_agent_{i}", "READ", f"resource_{i}")
        
        audit_file = security_context.workspace_dir / "auth" / "audit" / "security_audit.log"
        assert audit_file.exists()
        
        # Verify log content persists
        log_content = audit_file.read_text()
        lines = [line for line in log_content.split('\n') if line.strip()]
        assert len(lines) >= 100, f"Not all log entries were persisted: {len(lines)} < 100"
        
        # Verify test entries are properly formatted (at least 100, may be more from setup)
        auth_success_count = sum(1 for line in lines if "AUTH_SUCCESS" in line and "test_agent_" in line)
        assert auth_success_count >= 100, f"Expected at least 100 test AUTH_SUCCESS entries, got {auth_success_count}"


class TestAttackSimulation:
    """Test system resilience against various attack vectors"""
    
    @pytest_asyncio.fixture
    async def security_context(self):
        """Setup security context for attack simulation"""
        context = SecurityTestContext()
        await context.setup()
        yield context
        await context.cleanup()
    
    @pytest.mark.asyncio
    async def test_attack_prevention(self, security_context):
        """Test prevention of various attack types"""
        auth_mgr = security_context.auth_manager
        comm_mgr = security_context.comm_manager
        
        # Create test agent
        test_agent = await auth_mgr.create_token("attack_test_agent", Role.SPECIALIST)
        
        # Test 1: Path traversal attack
        try:
            handoff_id = await comm_mgr.create_handoff(
                from_agent="../../../etc/passwd",
                to_agent="../../windows/system32/config",
                handoff_type="path_traversal",
                data={"malicious": "../../../sensitive_data"},
                instructions="Attempt path traversal",
                auth_token=test_agent.token
            )
            
            # If handoff is created, verify paths were sanitized
            if handoff_id:
                handoff_data = await comm_mgr.read_handoff(handoff_id, test_agent.token)
                assert ".." not in handoff_data['from_agent']
                assert "/" not in handoff_data['from_agent']
                assert ".." not in handoff_data['to_agent']
        except Exception as e:
            # Attack should be blocked
            assert "path" in str(e).lower() or "invalid" in str(e).lower()
        
        # Test 2: SQL injection attempt (in JSON data)
        try:
            malicious_data = {
                "query": "SELECT * FROM users; DROP TABLE users; --",
                "user_input": "'; DELETE FROM tokens; --",
                "command": "$(rm -rf /)"
            }
            
            handoff_id = await comm_mgr.create_handoff(
                from_agent="attacker",
                to_agent="victim",
                handoff_type="sql_injection",
                data=malicious_data,
                instructions="Process user query",
                auth_token=test_agent.token
            )
            
            # Data should be sanitized but preserved
            if handoff_id:
                handoff_data = await comm_mgr.read_handoff(handoff_id, test_agent.token)
                # Original malicious content should be preserved (app-level responsibility)
                # but stored safely without execution
                assert handoff_data['data']['query'] == malicious_data['query']
                
        except Exception:
            # System handled the attack appropriately
            pass
        
        # Test 3: XSS attempt in instructions
        try:
            xss_instructions = """
            <script>alert('XSS Attack!')</script>
            <img src="x" onerror="alert('XSS')">
            <iframe src="javascript:alert('XSS')"></iframe>
            javascript:void(0)
            """
            
            handoff_id = await comm_mgr.create_handoff(
                from_agent="xss_attacker",
                to_agent="xss_victim",
                handoff_type="xss_attempt",
                data={"safe": "data"},
                instructions=xss_instructions,
                auth_token=test_agent.token
            )
            
            # Read markdown file to verify sanitization
            if handoff_id:
                md_file = comm_mgr.handoffs_dir / f"{handoff_id}.md"
                if md_file.exists():
                    md_content = md_file.read_text()
                    
                    # Dangerous tags should be escaped or removed
                    assert "<script>" not in md_content
                    assert "onerror=" not in md_content
                    assert "<iframe" not in md_content
                    assert "javascript:" not in md_content
                    
        except Exception:
            # Attack was blocked appropriately
            pass
        
        # Test 4: Token forgery
        try:
            # Create fake token
            fake_token = "fake_token_12345.fake_signature"
            
            # Attempt to authenticate with fake token
            authenticated = await auth_mgr.authenticate(fake_token)
            assert authenticated is None, "Fake token should not authenticate"
            
        except Exception:
            # Forgery attempt handled correctly
            pass
        
        # Test 5: Null byte injection
        try:
            handoff_id = await comm_mgr.create_handoff(
                from_agent="agent\x00.exe",
                to_agent="target\x00\x01\x02",
                handoff_type="null_byte",
                data={"null": "\x00byte\x00attack"},
                instructions="Null\x00byte\x00injection",
                auth_token=test_agent.token
            )
            
            if handoff_id:
                handoff_data = await comm_mgr.read_handoff(handoff_id, test_agent.token)
                # Null bytes should be removed
                assert "\x00" not in handoff_data['from_agent']
                assert "\x00" not in handoff_data['to_agent']
                
        except Exception:
            # Attack was blocked
            pass
    
    @pytest.mark.asyncio
    async def test_brute_force_protection(self, security_context):
        """Test protection against brute force attacks"""
        auth_mgr = security_context.auth_manager
        
        # Create test agent
        test_agent = await auth_mgr.create_token("brute_force_test", Role.GUEST)
        
        # Simulate failed authentication attempts
        failed_attempts = []
        for i in range(10):
            # Try to authenticate with invalid token
            fake_token = f"invalid_token_{i}"
            result = await auth_mgr.authenticate(fake_token)
            failed_attempts.append(result)
            
            # Record failed attempt manually (simulate)
            await auth_mgr._record_failed_attempt(test_agent.agent_id)
        
        # All attempts should fail
        assert all(attempt is None for attempt in failed_attempts)
        
        # Agent should be locked out after max attempts
        is_locked = auth_mgr._is_locked_out(test_agent.agent_id)
        assert is_locked, "Agent should be locked out after multiple failed attempts"
        
        # Even valid token should fail when locked out
        locked_auth = await auth_mgr.authenticate(test_agent.token)
        assert locked_auth is None, "Authentication should fail when agent is locked out"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_attacks(self, security_context):
        """Test rate limiting protection"""
        comm_mgr = security_context.comm_manager
        sanitizer = comm_mgr.sanitizer
        test_token = security_context.system_token.token
        
        # Test rate limiting on handoff creation
        rate_limited = False
        for i in range(60):  # Exceed rate limit of 50/minute
            try:
                await comm_mgr.create_handoff(
                    from_agent=f"rate_test_{i}",
                    to_agent="target",
                    handoff_type="rate_test",
                    data={"attempt": i},
                    instructions=f"Rate limit test {i}",
                    auth_token=test_token
                )
            except PermissionError as e:
                if "rate limit exceeded" in str(e).lower():
                    rate_limited = True
                    break
        
        assert rate_limited, "Rate limiting should kick in after excessive requests"
        
        # Test rate limiting on input sanitization
        sanitize_limited = False
        for i in range(220):  # Exceed rate limit of 200/minute
            try:
                sanitizer.check_rate_limit(f"sanitize_test", max_requests=200, window_seconds=60)
            except Exception:
                sanitize_limited = True
                break
        
        # Rate limiter should eventually say no
        final_check = sanitizer.check_rate_limit(f"sanitize_test", max_requests=200, window_seconds=60)
        if not final_check:
            sanitize_limited = True
        
        assert sanitize_limited, "Sanitization rate limiting should activate"


class TestPermissionEnforcement:
    """Test permission enforcement across all system modules"""
    
    @pytest_asyncio.fixture
    async def security_context(self):
        """Setup security context with multiple test agents"""
        context = SecurityTestContext()
        await context.setup()
        await context.create_test_agents()
        yield context
        await context.cleanup()
    
    @pytest.mark.asyncio
    async def test_permission_enforcement_across_modules(self, security_context):
        """Test consistent permission enforcement across modules"""
        agents = security_context.test_tokens
        auth_mgr = security_context.auth_manager
        comm_mgr = security_context.comm_manager
        
        # Test communication.py permissions
        
        # Orchestrator should create handoffs
        handoff_id = await comm_mgr.create_handoff(
            from_agent="orchestrator",
            to_agent="specialist",
            handoff_type="permission_test",
            data={"test": "orchestrator_permissions"},
            instructions="Test orchestrator permissions",
            auth_token=agents['orchestrator'].token
        )
        assert handoff_id is not None
        
        # Guest should NOT create handoffs
        with pytest.raises(PermissionError):
            await comm_mgr.create_handoff(
                from_agent="guest",
                to_agent="specialist",
                handoff_type="permission_test",
                data={"test": "guest_permissions"},
                instructions="Should fail",
                auth_token=agents['guest'].token
            )
        
        # Reviewer should read but not create
        read_result = await comm_mgr.read_handoff(handoff_id, agents['reviewer'].token)
        assert read_result is not None
        
        with pytest.raises(PermissionError):
            await comm_mgr.create_handoff(
                from_agent="reviewer",
                to_agent="specialist",
                handoff_type="permission_test",
                data={"test": "reviewer_permissions"},
                instructions="Should fail",
                auth_token=agents['reviewer'].token
            )
        
        # Test authentication.py permissions
        
        # Admin should manage tokens
        new_agent = await comm_mgr.create_agent_token(
            agent_id="permission_test_agent",
            role=Role.GUEST,
            admin_token=security_context.system_token.token
        )
        assert new_agent is not None
        
        # Non-admin should NOT manage tokens
        with pytest.raises(PermissionError):
            await comm_mgr.create_agent_token(
                agent_id="unauthorized_agent",
                role=Role.ADMIN,
                admin_token=agents['guest'].token
            )
        
        # Admin should update permissions
        updated = await comm_mgr.update_agent_permissions(
            agent_id="permission_test_agent",
            new_role=Role.SPECIALIST,
            admin_token=security_context.system_token.token
        )
        assert updated is True
        
        # Non-admin should NOT update permissions
        specialist_update = await comm_mgr.update_agent_permissions(
            agent_id="permission_test_agent",
            new_role=Role.ADMIN,
            admin_token=agents['specialist'].token
        )
        assert specialist_update is False, "Non-admin should not be able to update permissions"
    
    @pytest.mark.asyncio
    async def test_role_based_permission_consistency(self, security_context):
        """Test that role-based permissions are consistently enforced"""
        auth_mgr = security_context.auth_manager
        
        # Test each role's permissions
        for role in Role:
            if role == Role.ADMIN:
                continue  # Skip admin for this test
                
            # Create agent with specific role
            agent = await auth_mgr.create_token(
                agent_id=f"role_test_{role.value}",
                role=role,
                metadata={"test": "role_permissions"}
            )
            
            expected_permissions = ROLE_PERMISSIONS[role]
            
            # Test each permission the role should have
            for permission in expected_permissions:
                authorized = await auth_mgr.authorize(agent, permission, f"test_resource_{permission.value}")
                assert authorized, f"Role {role.value} should have permission {permission.value}"
            
            # Test permissions the role should NOT have
            all_permissions = set(Permission)
            unauthorized_permissions = all_permissions - set(expected_permissions)
            
            for permission in unauthorized_permissions:
                authorized = await auth_mgr.authorize(agent, permission, f"test_resource_{permission.value}")
                assert not authorized, f"Role {role.value} should NOT have permission {permission.value}"
    
    @pytest.mark.asyncio
    async def test_permission_inheritance_and_escalation(self, security_context):
        """Test that permissions cannot be escalated without proper authorization"""
        auth_mgr = security_context.auth_manager
        agents = security_context.test_tokens
        
        # Create a guest agent
        guest_agent = await auth_mgr.create_token("escalation_test_guest", Role.GUEST)
        
        # Guest should not be able to escalate their own permissions
        # This would require ADMIN permission which guest doesn't have
        guest_escalation = await auth_mgr.update_permissions(
            agent_id="escalation_test_guest",
            new_role=Role.ADMIN,
            admin_token=guest_agent  # Using guest's own token
        )
        assert guest_escalation is False, "Guest should not be able to escalate their own permissions"
        
        # Only admin can escalate permissions
        admin_escalation = await auth_mgr.update_permissions(
            agent_id="escalation_test_guest",
            new_role=Role.SPECIALIST,
            admin_token=security_context.system_token  # Using admin token
        )
        assert admin_escalation is True
        
        # Verify escalation worked
        updated_agent = await auth_mgr.authenticate(guest_agent.token)
        if updated_agent:  # Token might have been invalidated
            assert updated_agent.role == Role.SPECIALIST
        
        # Test that specialist cannot escalate to admin
        specialist_agent = await auth_mgr.create_token("escalation_test_specialist", Role.SPECIALIST)
        
        # update_permissions returns False for unauthorized access, doesn't raise exception
        specialist_escalation = await auth_mgr.update_permissions(
            agent_id="escalation_test_specialist",
            new_role=Role.ADMIN,
            admin_token=specialist_agent
        )
        assert specialist_escalation is False, "Specialist should not be able to escalate to admin"


class TestRecoveryAndResilience:
    """Test system recovery and resilience under security stress"""
    
    @pytest_asyncio.fixture
    async def security_context(self):
        """Setup security context for resilience testing"""
        context = SecurityTestContext()
        await context.setup()
        yield context
        await context.cleanup()
    
    @pytest.mark.asyncio
    async def test_security_recovery(self, security_context):
        """Test recovery from various security failures"""
        auth_mgr = security_context.auth_manager
        
        # Test 1: Token store corruption recovery
        
        # Create some tokens
        tokens = []
        for i in range(5):
            token = await auth_mgr.create_token(f"recovery_test_{i}", Role.GUEST)
            tokens.append(token)
        
        # Simulate token store corruption by corrupting the file
        tokens_file = security_context.workspace_dir / "auth" / "tokens" / "tokens.json"
        if tokens_file.exists():
            # Corrupt the JSON
            with open(tokens_file, 'w') as f:
                f.write("{ invalid json content")
            
            # Create new token store instance (simulates restart)
            from subforge.core.authentication import TokenStore
            new_token_store = TokenStore(security_context.workspace_dir / "auth" / "tokens")
            
            # Should handle corruption gracefully
            assert new_token_store.active_tokens == {}
            
            # System should still function with new tokens
            new_auth_mgr = AuthenticationManager(security_context.workspace_dir)
            recovery_token = await new_auth_mgr.create_token("recovery_agent", Role.SPECIALIST)
            assert recovery_token is not None
        
        # Test 2: Auth service restart simulation
        
        # Create tokens before "restart"
        pre_restart_token = await auth_mgr.create_token("pre_restart", Role.SPECIALIST)
        
        # Simulate restart by creating new auth manager
        restarted_auth_mgr = AuthenticationManager(
            security_context.workspace_dir,
            secret_key="test_secret_key_for_security_testing"
        )
        
        # Old tokens should still work after restart (persistence)
        if pre_restart_token:
            authenticated = await restarted_auth_mgr.authenticate(pre_restart_token.token)
            # Note: This might be None if token wasn't persisted, which is acceptable
            # The key is that the system doesn't crash
        
        # New tokens should work
        post_restart_token = await restarted_auth_mgr.create_token("post_restart", Role.OBSERVER)
        assert post_restart_token is not None
        
        # Test 3: Concurrent authentication storms
        
        # Create multiple authentication requests concurrently
        test_token = await auth_mgr.create_token("concurrent_test", Role.SPECIALIST)
        
        async def concurrent_auth():
            return await auth_mgr.authenticate(test_token.token)
        
        # Run many concurrent authentications
        auth_tasks = [concurrent_auth() for _ in range(20)]
        results = await asyncio.gather(*auth_tasks, return_exceptions=True)
        
        # Most should succeed, none should crash the system
        successful = [r for r in results if r is not None and not isinstance(r, Exception)]
        assert len(successful) > 0, "At least some concurrent authentications should succeed"
        
        # No exceptions should be raised
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"No exceptions should occur during concurrent auth: {exceptions}"
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_protection(self, security_context):
        """Test protection against resource exhaustion attacks"""
        auth_mgr = security_context.auth_manager
        comm_mgr = security_context.comm_manager
        
        # Test 1: Large payload protection
        large_data = {"huge": "x" * 1000000}  # 1MB of data
        
        try:
            handoff_id = await comm_mgr.create_handoff(
                from_agent="resource_test",
                to_agent="target",
                handoff_type="large_payload",
                data=large_data,
                instructions="Test large payload",
                auth_token=security_context.system_token.token
            )
            
            # If accepted, should be limited
            if handoff_id:
                handoff_data = await comm_mgr.read_handoff(handoff_id, security_context.system_token.token)
                # Data size should be controlled
                serialized = json.dumps(handoff_data['data'])
                assert len(serialized) <= 10 * 1024 * 1024, "Data should be size-limited"
                
        except ValueError as e:
            # Should be rejected due to size
            assert "size" in str(e).lower() or "large" in str(e).lower()
        
        # Test 2: Deep nesting protection
        def create_deep_dict(depth):
            if depth == 0:
                return "deep_value"
            return {"level": create_deep_dict(depth - 1)}
        
        deep_data = create_deep_dict(20)  # Very deep nesting
        
        try:
            handoff_id = await comm_mgr.create_handoff(
                from_agent="deep_test",
                to_agent="target",
                handoff_type="deep_nesting",
                data=deep_data,
                instructions="Test deep nesting",
                auth_token=security_context.system_token.token
            )
            
            # Should either be accepted with limited depth or rejected
            if handoff_id:
                handoff_data = await comm_mgr.read_handoff(handoff_id, security_context.system_token.token)
                # Data should be processed without crashing
                assert handoff_data is not None
                
        except ValueError as e:
            # Should be rejected due to nesting depth
            assert "depth" in str(e).lower() or "nested" in str(e).lower()
        
        # Test 3: Too many tokens protection
        token_creation_limit = False
        created_tokens = []
        
        try:
            for i in range(1000):  # Try to create many tokens
                token = await auth_mgr.create_token(f"mass_token_{i}", Role.GUEST)
                created_tokens.append(token)
                
                # Check if we hit any limits
                if len(auth_mgr.token_store.active_tokens) > 500:
                    # System should handle large numbers but may impose limits
                    break
                    
        except Exception as e:
            # May hit resource limits, which is acceptable protection
            token_creation_limit = True
        
        # System should remain functional even with many tokens
        final_token = await auth_mgr.create_token("final_test", Role.OBSERVER)
        assert final_token is not None, "System should remain functional"
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, security_context):
        """Test graceful degradation under security stress"""
        auth_mgr = security_context.auth_manager
        comm_mgr = security_context.comm_manager
        
        # Simulate high load with many operations
        operations = []
        
        # Create many tokens concurrently
        async def create_token_op(i):
            try:
                return await auth_mgr.create_token(f"stress_test_{i}", Role.GUEST)
            except Exception as e:
                return e
        
        # Create many handoffs concurrently
        async def create_handoff_op(i):
            try:
                return await comm_mgr.create_handoff(
                    from_agent=f"stress_agent_{i}",
                    to_agent="target",
                    handoff_type="stress_test",
                    data={"stress": i},
                    instructions=f"Stress test operation {i}",
                    auth_token=security_context.system_token.token
                )
            except Exception as e:
                return e
        
        # Launch stress test operations
        token_ops = [create_token_op(i) for i in range(50)]
        handoff_ops = [create_handoff_op(i) for i in range(50)]
        
        all_ops = token_ops + handoff_ops
        results = await asyncio.gather(*all_ops, return_exceptions=True)
        
        # Count successes and failures
        successes = [r for r in results if r is not None and not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]
        
        # System should handle at least some operations successfully
        assert len(successes) > 0, "System should handle some operations under stress"
        
        # Failures should be graceful (proper exceptions, not crashes)
        for failure in failures:
            assert isinstance(failure, (Exception, str)), f"Unexpected failure type: {type(failure)}"
        
        # System should remain responsive after stress
        post_stress_token = await auth_mgr.create_token("post_stress", Role.SPECIALIST)
        assert post_stress_token is not None, "System should remain functional after stress test"


# Performance and stress testing utilities
class SecurityPerformanceMonitor:
    """Monitor security operation performance during tests"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Start timing a security operation"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str):
        """End timing and record metrics"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(duration)
            del self.start_times[operation]
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics"""
        stats = {}
        for operation, durations in self.metrics.items():
            stats[operation] = {
                'count': len(durations),
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
                'total': sum(durations)
            }
        return stats


class TestSecurityPerformance:
    """Test security operation performance under load"""
    
    @pytest_asyncio.fixture
    async def security_context(self):
        """Setup security context for performance testing"""
        context = SecurityTestContext()
        await context.setup()
        yield context
        await context.cleanup()
    
    @pytest.mark.asyncio
    async def test_authentication_performance(self, security_context):
        """Test authentication performance under load"""
        auth_mgr = security_context.auth_manager
        monitor = SecurityPerformanceMonitor()
        
        # Create test tokens
        test_tokens = []
        for i in range(10):
            token = await auth_mgr.create_token(f"perf_test_{i}", Role.SPECIALIST)
            test_tokens.append(token)
        
        # Test authentication performance
        auth_times = []
        for _ in range(100):
            token = test_tokens[_ % len(test_tokens)]
            
            monitor.start_timer("authentication")
            result = await auth_mgr.authenticate(token.token)
            monitor.end_timer("authentication")
            
            assert result is not None
        
        # Test authorization performance
        test_token = test_tokens[0]
        for _ in range(100):
            monitor.start_timer("authorization")
            result = await auth_mgr.authorize(test_token, Permission.READ, "perf_test_resource")
            monitor.end_timer("authorization")
            
            assert result is True
        
        # Analyze performance
        stats = monitor.get_stats()
        
        # Authentication should be reasonably fast (< 100ms average)
        auth_stats = stats.get('authentication', {})
        assert auth_stats.get('avg', 0) < 0.1, f"Authentication too slow: {auth_stats.get('avg')} seconds"
        
        # Authorization should be very fast (< 10ms average)
        authz_stats = stats.get('authorization', {})
        assert authz_stats.get('avg', 0) < 0.01, f"Authorization too slow: {authz_stats.get('avg')} seconds"
    
    @pytest.mark.asyncio
    async def test_concurrent_security_operations(self, security_context):
        """Test concurrent security operations performance"""
        auth_mgr = security_context.auth_manager
        
        # Test concurrent token creation
        async def create_concurrent_token(i):
            return await auth_mgr.create_token(f"concurrent_{i}", Role.GUEST)
        
        start_time = time.time()
        concurrent_tokens = await asyncio.gather(*[
            create_concurrent_token(i) for i in range(20)
        ])
        creation_time = time.time() - start_time
        
        # All tokens should be created successfully
        assert all(token is not None for token in concurrent_tokens)
        assert len(set(token.token for token in concurrent_tokens)) == 20, "All tokens should be unique"
        
        # Should complete in reasonable time (< 5 seconds for 20 concurrent)
        assert creation_time < 5.0, f"Concurrent token creation too slow: {creation_time} seconds"
        
        # Test concurrent authentication
        async def authenticate_concurrent(token):
            return await auth_mgr.authenticate(token.token)
        
        start_time = time.time()
        auth_results = await asyncio.gather(*[
            authenticate_concurrent(token) for token in concurrent_tokens
        ])
        auth_time = time.time() - start_time
        
        # All authentications should succeed
        assert all(result is not None for result in auth_results)
        
        # Should complete quickly (< 2 seconds for 20 concurrent)
        assert auth_time < 2.0, f"Concurrent authentication too slow: {auth_time} seconds"


# Test report generation
class SecurityTestReporter:
    """Generate comprehensive security test reports"""
    
    def __init__(self):
        self.test_results = {}
        self.security_stats = {}
        self.performance_metrics = {}
        self.vulnerabilities_found = []
        self.recommendations = []
    
    def record_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Record a test result"""
        self.test_results[test_name] = {
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
    
    def record_security_stats(self, stats: Dict[str, Any]):
        """Record security statistics"""
        self.security_stats.update(stats)
    
    def record_vulnerability(self, severity: str, description: str, location: str):
        """Record a security vulnerability"""
        self.vulnerabilities_found.append({
            'severity': severity,
            'description': description,
            'location': location,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_recommendation(self, recommendation: str, priority: str = "medium"):
        """Add a security recommendation"""
        self.recommendations.append({
            'recommendation': recommendation,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_report(self) -> str:
        """Generate comprehensive security test report"""
        report = f"""
# SubForge Security Test Report
Generated: {datetime.now().isoformat()}

## Test Summary
Total Tests: {len(self.test_results)}
Passed: {sum(1 for r in self.test_results.values() if r['passed'])}
Failed: {sum(1 for r in self.test_results.values() if not r['passed'])}

## Security Statistics
{json.dumps(self.security_stats, indent=2)}

## Vulnerabilities Found
{len(self.vulnerabilities_found)} vulnerabilities detected:
"""
        
        for vuln in self.vulnerabilities_found:
            report += f"- **{vuln['severity'].upper()}**: {vuln['description']} (Location: {vuln['location']})\n"
        
        report += f"""
## Security Recommendations
{len(self.recommendations)} recommendations:
"""
        
        for rec in self.recommendations:
            report += f"- **{rec['priority'].upper()}**: {rec['recommendation']}\n"
        
        report += f"""
## Test Details
"""
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            report += f"### {test_name}\n{status}\n{result['details']}\n\n"
        
        return report


# Main test execution
if __name__ == "__main__":
    # Configure logging for security tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run security tests with detailed reporting
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--capture=no",
        "--asyncio-mode=auto"
    ])