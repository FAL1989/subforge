#!/usr/bin/env python3
"""
Comprehensive Authentication System Tests for SubForge
Tests token lifecycle, permissions, security hardening, edge cases, and integration
Created: 2025-09-05 17:15 UTC-3 São Paulo
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import secrets
import hmac
import hashlib

# Import the authentication module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from subforge.core.authentication import (
    AgentToken, TokenStore, AuthenticationManager,
    SecurityAuditLog, Permission, Role, require_auth,
    ROLE_PERMISSIONS
)


class TestTokenLifecycle:
    """Test token creation, expiry, refresh, and revocation"""
    
    @pytest.mark.asyncio
    async def test_token_creation_with_different_roles(self):
        """Test creating tokens with all available roles"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            for role in Role:
                token = await auth_manager.create_token(
                    agent_id=f"agent_{role.value}",
                    role=role
                )
                
                assert token.agent_id == f"agent_{role.value}"
                assert token.role == role
                assert token.permissions == ROLE_PERMISSIONS[role]
                assert token.token is not None
                assert '.' in token.token  # Should be signed
    
    @pytest.mark.asyncio
    async def test_token_expiry_validation(self):
        """Test that expired tokens are properly handled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create token with very short lifetime
            token = await auth_manager.create_token(
                agent_id="test_agent",
                role=Role.SPECIALIST,
                lifetime=timedelta(seconds=-1)  # Already expired
            )
            
            assert token.is_expired()
            
            # Try to authenticate with expired token
            authenticated = await auth_manager.authenticate(token.token)
            assert authenticated is None
    
    @pytest.mark.asyncio
    async def test_token_refresh_mechanism(self):
        """Test token refresh using refresh token"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create token with refresh capability
            original_token = await auth_manager.create_token(
                agent_id="refresh_test",
                role=Role.ORCHESTRATOR,
                lifetime=timedelta(hours=2)
            )
            
            assert original_token.refresh_token is not None
            
            # Refresh the token
            new_token = await auth_manager.refresh_token(original_token.refresh_token)
            
            assert new_token is not None
            assert new_token.agent_id == original_token.agent_id
            assert new_token.role == original_token.role
            assert new_token.token != original_token.token
            
            # Old token should be revoked
            old_auth = await auth_manager.authenticate(original_token.token)
            assert old_auth is None
    
    @pytest.mark.asyncio
    async def test_token_revocation_and_blacklisting(self):
        """Test token revocation and blacklist functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            token = await auth_manager.create_token(
                agent_id="revoke_test",
                role=Role.SPECIALIST
            )
            
            # Verify token works
            auth1 = await auth_manager.authenticate(token.token)
            assert auth1 is not None
            
            # Revoke token
            await auth_manager.revoke_token(token.token)
            
            # Token should no longer work
            auth2 = await auth_manager.authenticate(token.token)
            assert auth2 is None
            
            # Check token is in revoked list
            assert token.token in auth_manager.token_store.revoked_tokens
    
    @pytest.mark.asyncio
    async def test_concurrent_token_operations(self):
        """Test concurrent token creation and authentication"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create multiple tokens concurrently
            tasks = []
            for i in range(10):
                tasks.append(auth_manager.create_token(
                    agent_id=f"concurrent_{i}",
                    role=Role.SPECIALIST
                ))
            
            tokens = await asyncio.gather(*tasks)
            
            # Verify all tokens are unique
            token_strings = [t.token for t in tokens]
            assert len(set(token_strings)) == 10
            
            # Authenticate all tokens concurrently
            auth_tasks = [auth_manager.authenticate(t.token) for t in tokens]
            results = await asyncio.gather(*auth_tasks)
            
            # All should authenticate successfully
            assert all(r is not None for r in results)


class TestPermissionSystem:
    """Test RBAC, permission checks, and inheritance"""
    
    @pytest.mark.asyncio
    async def test_permission_escalation_prevention(self):
        """Test that lower roles cannot escalate to higher permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create guest token
            guest_token = await auth_manager.create_token(
                agent_id="guest_user",
                role=Role.GUEST
            )
            
            # Guest should not have admin permissions
            assert not guest_token.has_permission(Permission.ADMIN)
            assert not guest_token.has_permission(Permission.MANAGE_TOKENS)
            
            # Try to perform admin action
            authorized = await auth_manager.authorize(
                guest_token,
                Permission.ADMIN
            )
            assert not authorized
    
    @pytest.mark.asyncio
    async def test_role_based_access_control(self):
        """Test RBAC with different role permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            test_cases = [
                (Role.ADMIN, Permission.ADMIN, True),
                (Role.ADMIN, Permission.MANAGE_TOKENS, True),
                (Role.ORCHESTRATOR, Permission.CREATE_HANDOFF, True),
                (Role.ORCHESTRATOR, Permission.ADMIN, False),
                (Role.SPECIALIST, Permission.EXECUTE, True),
                (Role.SPECIALIST, Permission.MANAGE_TOKENS, False),
                (Role.REVIEWER, Permission.READ, True),
                (Role.REVIEWER, Permission.WRITE, False),
                (Role.OBSERVER, Permission.VIEW_LOGS, True),
                (Role.OBSERVER, Permission.EXECUTE, False),
                (Role.GUEST, Permission.READ, True),
                (Role.GUEST, Permission.WRITE, False),
            ]
            
            for role, permission, expected in test_cases:
                token = await auth_manager.create_token(
                    agent_id=f"test_{role.value}",
                    role=role
                )
                authorized = await auth_manager.authorize(token, permission)
                assert authorized == expected, f"Failed for {role} with {permission}"
    
    @pytest.mark.asyncio
    async def test_permission_inheritance(self):
        """Test that higher roles inherit lower role permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Admin should have all permissions
            admin_token = await auth_manager.create_token(
                agent_id="admin",
                role=Role.ADMIN
            )
            
            for permission in Permission:
                assert admin_token.has_permission(permission)
            
            # Orchestrator should have specialist permissions
            orch_token = await auth_manager.create_token(
                agent_id="orchestrator",
                role=Role.ORCHESTRATOR
            )
            
            specialist_perms = ROLE_PERMISSIONS[Role.SPECIALIST]
            for perm in specialist_perms:
                assert orch_token.has_permission(perm)
    
    @pytest.mark.asyncio
    async def test_cross_role_permission_checks(self):
        """Test permission checks across different roles"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create tokens for different roles
            admin = await auth_manager.create_token("admin", Role.ADMIN)
            specialist = await auth_manager.create_token("spec", Role.SPECIALIST)
            
            # Admin can update specialist permissions
            success = await auth_manager.update_permissions(
                "spec",
                Role.ORCHESTRATOR,
                admin
            )
            assert success
            
            # Specialist cannot update admin permissions (returns False, doesn't raise)
            success = await auth_manager.update_permissions(
                "admin",
                Role.GUEST,
                specialist
            )
            assert not success  # Should return False due to lack of permissions
    
    @pytest.mark.asyncio
    async def test_admin_override_capabilities(self):
        """Test admin override capabilities"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create admin and regular user
            admin = await auth_manager.create_token("admin", Role.ADMIN)
            user = await auth_manager.create_token("user", Role.SPECIALIST)
            
            # Admin can revoke user token
            await auth_manager.revoke_token(user.token, admin.agent_id)
            
            # User token should be revoked
            auth = await auth_manager.authenticate(user.token)
            assert auth is None
            
            # Admin can change user role
            user2 = await auth_manager.create_token("user2", Role.SPECIALIST)
            success = await auth_manager.update_permissions(
                "user2",
                Role.REVIEWER,
                admin
            )
            assert success


class TestSecurityHardening:
    """Test security features like brute force protection and rate limiting"""
    
    @pytest.mark.asyncio
    async def test_brute_force_protection(self):
        """Test account lockout after failed attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create a token
            token = await auth_manager.create_token("test_user", Role.SPECIALIST)
            
            # Record multiple failed attempts
            for i in range(5):
                await auth_manager._record_failed_attempt("test_user")
            
            # Account should be locked
            assert auth_manager._is_locked_out("test_user")
            
            # Authentication should fail even with valid token
            auth = await auth_manager.authenticate(token.token)
            assert auth is None
    
    @pytest.mark.asyncio
    async def test_rate_limiting_validation(self):
        """Test rate limiting for authentication attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create token with limited permissions
            token = await auth_manager.create_token("rate_test", Role.GUEST)
            
            # Fail authorization multiple times
            for i in range(6):
                await auth_manager.authorize(token, Permission.ADMIN)
            
            # Check if account is locked
            assert auth_manager._is_locked_out("rate_test")
    
    @pytest.mark.asyncio
    async def test_token_signature_verification(self):
        """Test token signature verification prevents tampering"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            token = await auth_manager.create_token("sig_test", Role.SPECIALIST)
            
            # Tamper with token
            tampered = token.token.replace('a', 'b')
            
            # Should fail authentication
            auth = await auth_manager.authenticate(tampered)
            assert auth is None
            
            # Original should work
            auth2 = await auth_manager.authenticate(token.token)
            assert auth2 is not None
    
    @pytest.mark.asyncio
    async def test_session_hijacking_prevention(self):
        """Test measures against session hijacking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            token = await auth_manager.create_token("session_test", Role.SPECIALIST)
            
            # Authenticate from original "session"
            auth1 = await auth_manager.authenticate(token.token)
            assert auth1 is not None
            
            # Track usage stats
            original_count = auth1.usage_count
            
            # Multiple authentications should update usage stats
            for i in range(3):
                await auth_manager.authenticate(token.token)
            
            # Get updated token
            auth2 = await auth_manager.token_store.get_token(token.token)
            assert auth2.usage_count > original_count
            assert auth2.last_used is not None
    
    @pytest.mark.asyncio
    async def test_replay_attack_prevention(self):
        """Test prevention of replay attacks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            token = await auth_manager.create_token("replay_test", Role.SPECIALIST)
            
            # Revoke token
            await auth_manager.revoke_token(token.token)
            
            # Replayed token should fail
            auth = await auth_manager.authenticate(token.token)
            assert auth is None
            
            # Token should be in revoked list
            assert token.token in auth_manager.token_store.revoked_tokens


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_expired_token_handling(self):
        """Test handling of expired tokens"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create already expired token
            token = await auth_manager.create_token(
                agent_id="expired_test",
                role=Role.SPECIALIST,
                lifetime=timedelta(seconds=-10)
            )
            
            # Should not authenticate
            auth = await auth_manager.authenticate(token.token)
            assert auth is None
            
            # Cleanup should remove it
            await auth_manager.token_store.cleanup_expired()
            assert token.token not in auth_manager.token_store.active_tokens
    
    @pytest.mark.asyncio
    async def test_invalid_token_format(self):
        """Test handling of malformed tokens"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            invalid_tokens = [
                "invalid",
                "no.signature",
                "too.many.parts.here",
                "",
                "a" * 1000,  # Very long token
                "special!@#$%^&*()chars"
            ]
            
            for invalid in invalid_tokens:
                auth = await auth_manager.authenticate(invalid)
                assert auth is None
    
    @pytest.mark.asyncio
    async def test_missing_permissions(self):
        """Test handling of missing permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create token with custom limited permissions
            token = await auth_manager.create_token(
                agent_id="limited",
                role=Role.SPECIALIST,
                custom_permissions=[Permission.READ]
            )
            
            # Should only have READ permission
            assert token.has_permission(Permission.READ)
            assert not token.has_permission(Permission.WRITE)
            assert not token.has_permission(Permission.EXECUTE)
    
    @pytest.mark.asyncio
    async def test_concurrent_authentication_attempts(self):
        """Test handling of concurrent authentication"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            token = await auth_manager.create_token("concurrent", Role.SPECIALIST)
            
            # Authenticate concurrently
            tasks = [auth_manager.authenticate(token.token) for _ in range(20)]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(r is not None for r in results)
            
            # Check usage count increased appropriately
            final_token = await auth_manager.token_store.get_token(token.token)
            assert final_token.usage_count >= 20
    
    @pytest.mark.asyncio
    async def test_token_collision_handling(self):
        """Test handling of potential token collisions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create many tokens to test uniqueness
            tokens = []
            for i in range(100):
                token = await auth_manager.create_token(
                    agent_id=f"collision_{i}",
                    role=Role.SPECIALIST
                )
                tokens.append(token.token)
            
            # All tokens should be unique
            assert len(set(tokens)) == 100


class TestIntegration:
    """Test integration with other components"""
    
    @pytest.mark.asyncio
    async def test_authentication_with_communication_handler(self):
        """Test authentication integration with CommunicationHandler"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create tokens for different agents
            sender_token = await auth_manager.create_token("sender", Role.SPECIALIST)
            receiver_token = await auth_manager.create_token("receiver", Role.SPECIALIST)
            
            # Simulate handoff creation requiring permission
            can_create = await auth_manager.authorize(
                sender_token,
                Permission.CREATE_HANDOFF,
                resource="handoff_123"
            )
            assert can_create
            
            # Receiver can read handoff
            can_read = await auth_manager.authorize(
                receiver_token,
                Permission.READ_HANDOFF,
                resource="handoff_123"
            )
            assert can_read
    
    @pytest.mark.asyncio
    async def test_multi_agent_authentication_flow(self):
        """Test authentication flow with multiple agents"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create orchestrator and specialist tokens
            orch = await auth_manager.create_token("orchestrator", Role.ORCHESTRATOR)
            spec1 = await auth_manager.create_token("specialist1", Role.SPECIALIST)
            spec2 = await auth_manager.create_token("specialist2", Role.SPECIALIST)
            
            # Orchestrator can manage handoffs
            assert await auth_manager.authorize(orch, Permission.CREATE_HANDOFF)
            assert await auth_manager.authorize(orch, Permission.DELETE_HANDOFF)
            
            # Specialists have limited permissions
            assert await auth_manager.authorize(spec1, Permission.READ)
            assert not await auth_manager.authorize(spec1, Permission.DELETE_HANDOFF)
    
    @pytest.mark.asyncio
    async def test_token_persistence_and_recovery(self):
        """Test token persistence across restarts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tokens
            auth_manager1 = AuthenticationManager(Path(tmpdir))
            token1 = await auth_manager1.create_token("persist1", Role.SPECIALIST)
            token2 = await auth_manager1.create_token("persist2", Role.ORCHESTRATOR)
            
            # Simulate restart by creating new manager with same path
            auth_manager2 = AuthenticationManager(Path(tmpdir))
            
            # Tokens should still be valid
            auth1 = await auth_manager2.authenticate(token1.token)
            auth2 = await auth_manager2.authenticate(token2.token)
            
            assert auth1 is not None
            assert auth1.agent_id == "persist1"
            assert auth2 is not None
            assert auth2.agent_id == "persist2"
    
    @pytest.mark.asyncio
    async def test_audit_logging_verification(self):
        """Test audit logging for security events"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Perform various operations
            token = await auth_manager.create_token("audit_test", Role.SPECIALIST)
            await auth_manager.authorize(token, Permission.READ, "resource1")
            await auth_manager.authorize(token, Permission.ADMIN, "resource2")  # Should fail
            await auth_manager.revoke_token(token.token)
            
            # Check audit log exists
            audit_file = Path(tmpdir) / "auth" / "audit" / "security_audit.log"
            assert audit_file.exists()
            
            # Verify log contains expected entries
            with open(audit_file, 'r') as f:
                log_content = f.read()
                assert "TOKEN_CREATED" in log_content
                assert "AUTH_SUCCESS" in log_content
                assert "AUTH_FAILURE" in log_content
                assert "TOKEN_REVOKED" in log_content


class TestRequireAuthDecorator:
    """Test the require_auth decorator functionality"""
    
    @pytest.mark.asyncio
    async def test_decorator_authentication(self):
        """Test require_auth decorator basic functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            @require_auth(permission=Permission.EXECUTE)
            async def protected_function(data, **kwargs):
                return f"Executed with {data}"
            
            # Create token with permission
            token = await auth_manager.create_token("decorator_test", Role.SPECIALIST)
            
            # Call with valid token
            result = await protected_function(
                "test_data",
                auth_token=token.token,
                auth_manager=auth_manager
            )
            assert result == "Executed with test_data"
            
            # Call without token should fail
            with pytest.raises(PermissionError):
                await protected_function("test_data", auth_manager=auth_manager)
    
    @pytest.mark.asyncio
    async def test_decorator_with_insufficient_permissions(self):
        """Test decorator with insufficient permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            @require_auth(permission=Permission.ADMIN)
            async def admin_only_function(**kwargs):
                return "Admin action performed"
            
            # Create non-admin token
            token = await auth_manager.create_token("user", Role.SPECIALIST)
            
            # Should fail with insufficient permissions
            with pytest.raises(PermissionError) as exc_info:
                await admin_only_function(
                    auth_token=token.token,
                    auth_manager=auth_manager
                )
            assert "ADMIN permission" in str(exc_info.value)


class TestTokenStore:
    """Test TokenStore specific functionality"""
    
    @pytest.mark.asyncio
    async def test_token_storage_and_retrieval(self):
        """Test storing and retrieving tokens"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TokenStore(Path(tmpdir))
            
            # Create and store token
            token = AgentToken(
                agent_id="store_test",
                token="test_token_123",
                role=Role.SPECIALIST,
                permissions=list(ROLE_PERMISSIONS[Role.SPECIALIST])
            )
            
            await store.store_token(token)
            
            # Retrieve token
            retrieved = await store.get_token("test_token_123")
            assert retrieved is not None
            assert retrieved.agent_id == "store_test"
            assert retrieved.usage_count == 1  # Updated on retrieval
    
    @pytest.mark.asyncio
    async def test_token_cleanup(self):
        """Test cleanup of expired tokens"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TokenStore(Path(tmpdir))
            
            # Create expired token
            expired = AgentToken(
                agent_id="expired",
                token="expired_123",
                role=Role.SPECIALIST,
                permissions=[],
                expires_at=datetime.now() - timedelta(hours=1)
            )
            
            # Create valid token
            valid = AgentToken(
                agent_id="valid",
                token="valid_123",
                role=Role.SPECIALIST,
                permissions=[],
                expires_at=datetime.now() + timedelta(hours=1)
            )
            
            await store.store_token(expired)
            await store.store_token(valid)
            
            # Cleanup
            await store.cleanup_expired()
            
            # Only valid token should remain
            assert "valid_123" in store.active_tokens
            assert "expired_123" not in store.active_tokens


class TestSecurityAuditLog:
    """Test security audit logging functionality"""
    
    def test_audit_log_creation(self):
        """Test audit log initialization and basic logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_log = SecurityAuditLog(Path(tmpdir))
            
            # Log various events
            audit_log.log_auth_success("agent1", "READ", "resource1")
            audit_log.log_auth_failure("agent2", "WRITE", "resource2", "no_permission")
            audit_log.log_token_created("agent3", "SPECIALIST", None)
            audit_log.log_suspicious_activity("agent4", "brute_force", "5 attempts")
            
            # Check log file exists and contains entries
            log_file = Path(tmpdir) / "security_audit.log"
            assert log_file.exists()
            
            with open(log_file, 'r') as f:
                content = f.read()
                assert "AUTH_SUCCESS" in content
                assert "AUTH_FAILURE" in content
                assert "TOKEN_CREATED" in content
                assert "SUSPICIOUS_ACTIVITY" in content


class TestCustomPermissions:
    """Test custom permissions and role modifications"""
    
    @pytest.mark.asyncio
    async def test_custom_permissions(self):
        """Test creating tokens with custom permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            # Create token with custom permissions
            custom_perms = [Permission.READ, Permission.VIEW_LOGS]
            token = await auth_manager.create_token(
                agent_id="custom",
                role=Role.SPECIALIST,  # Role doesn't matter with custom perms
                custom_permissions=custom_perms
            )
            
            # Should only have specified permissions
            assert token.has_permission(Permission.READ)
            assert token.has_permission(Permission.VIEW_LOGS)
            assert not token.has_permission(Permission.WRITE)
            assert not token.has_permission(Permission.EXECUTE)


class TestLockoutMechanism:
    """Test account lockout and recovery"""
    
    @pytest.mark.asyncio
    async def test_lockout_duration(self):
        """Test that lockout expires after duration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            auth_manager.lockout_duration = timedelta(seconds=1)  # Short for testing
            
            # Trigger lockout
            for i in range(5):
                await auth_manager._record_failed_attempt("lockout_test")
            
            assert auth_manager._is_locked_out("lockout_test")
            
            # Wait for lockout to expire
            await asyncio.sleep(1.5)
            
            # Should no longer be locked out
            assert not auth_manager._is_locked_out("lockout_test")


# Performance and stress tests
class TestPerformance:
    """Test performance under load"""
    
    @pytest.mark.asyncio
    async def test_high_volume_token_creation(self):
        """Test creating many tokens quickly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_manager = AuthenticationManager(Path(tmpdir))
            
            start_time = datetime.now()
            
            # Create 100 tokens
            tasks = []
            for i in range(100):
                tasks.append(auth_manager.create_token(
                    agent_id=f"perf_{i}",
                    role=Role.SPECIALIST
                ))
            
            tokens = await asyncio.gather(*tasks)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Should complete in reasonable time
            assert duration < 10  # 10 seconds for 100 tokens
            assert len(tokens) == 100
            
            # All tokens should be unique
            token_strings = [t.token for t in tokens]
            assert len(set(token_strings)) == 100


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])