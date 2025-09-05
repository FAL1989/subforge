#!/usr/bin/env python3
"""
Test suite for the authentication and authorization system
"""

import asyncio
import json
import tempfile
from pathlib import Path
from datetime import timedelta
import pytest

from subforge.core.authentication import (
    AuthenticationManager,
    AgentToken,
    Permission,
    Role,
    TokenStore,
    SecurityAuditLog,
    require_auth
)
from subforge.core.communication import CommunicationManager


class TestAuthenticationSystem:
    """Test cases for authentication system"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    async def auth_manager(self, temp_workspace):
        """Create authentication manager instance"""
        return AuthenticationManager(temp_workspace)
    
    @pytest.fixture
    async def comm_manager(self, temp_workspace):
        """Create communication manager with auth enabled"""
        manager = CommunicationManager(temp_workspace, enable_auth=True)
        # Wait for system token creation
        await asyncio.sleep(0.1)
        return manager
    
    @pytest.mark.asyncio
    async def test_token_creation(self, auth_manager):
        """Test creating authentication tokens"""
        # Create token for specialist agent
        token = await auth_manager.create_token(
            agent_id="test_specialist",
            role=Role.SPECIALIST,
            lifetime=timedelta(hours=2)
        )
        
        assert token.agent_id == "test_specialist"
        assert token.role == Role.SPECIALIST
        assert Permission.CREATE_HANDOFF in token.permissions
        assert Permission.READ_HANDOFF in token.permissions
        assert Permission.ADMIN not in token.permissions
        assert token.expires_at is not None
    
    @pytest.mark.asyncio
    async def test_token_authentication(self, auth_manager):
        """Test token authentication flow"""
        # Create a token
        token = await auth_manager.create_token(
            agent_id="auth_test",
            role=Role.SPECIALIST
        )
        
        # Authenticate with valid token
        authenticated = await auth_manager.authenticate(token.token)
        assert authenticated is not None
        assert authenticated.agent_id == "auth_test"
        assert authenticated.usage_count == 1
        
        # Test with invalid token
        invalid = await auth_manager.authenticate("invalid_token")
        assert invalid is None
    
    @pytest.mark.asyncio
    async def test_authorization(self, auth_manager):
        """Test permission-based authorization"""
        # Create tokens with different roles
        admin_token = await auth_manager.create_token(
            agent_id="admin",
            role=Role.ADMIN
        )
        
        specialist_token = await auth_manager.create_token(
            agent_id="specialist",
            role=Role.SPECIALIST
        )
        
        observer_token = await auth_manager.create_token(
            agent_id="observer",
            role=Role.OBSERVER
        )
        
        # Test admin permissions
        assert await auth_manager.authorize(admin_token, Permission.ADMIN)
        assert await auth_manager.authorize(admin_token, Permission.CREATE_HANDOFF)
        
        # Test specialist permissions
        assert await auth_manager.authorize(specialist_token, Permission.CREATE_HANDOFF)
        assert not await auth_manager.authorize(specialist_token, Permission.ADMIN)
        
        # Test observer permissions
        assert await auth_manager.authorize(observer_token, Permission.READ)
        assert not await auth_manager.authorize(observer_token, Permission.WRITE)
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, auth_manager):
        """Test token refresh mechanism"""
        # Create token with refresh capability
        original_token = await auth_manager.create_token(
            agent_id="refresh_test",
            role=Role.SPECIALIST,
            lifetime=timedelta(hours=2)
        )
        
        assert original_token.refresh_token is not None
        
        # Refresh the token
        new_token = await auth_manager.refresh_token(original_token.refresh_token)
        assert new_token is not None
        assert new_token.agent_id == "refresh_test"
        assert new_token.token != original_token.token
        
        # Original token should be revoked
        old_auth = await auth_manager.authenticate(original_token.token)
        assert old_auth is None
    
    @pytest.mark.asyncio
    async def test_token_revocation(self, auth_manager):
        """Test token revocation"""
        # Create a token
        token = await auth_manager.create_token(
            agent_id="revoke_test",
            role=Role.SPECIALIST
        )
        
        # Verify it works
        auth = await auth_manager.authenticate(token.token)
        assert auth is not None
        
        # Revoke the token
        await auth_manager.revoke_token(token.token)
        
        # Verify it's revoked
        auth_after = await auth_manager.authenticate(token.token)
        assert auth_after is None
    
    @pytest.mark.asyncio
    async def test_permission_update(self, auth_manager):
        """Test updating agent permissions"""
        # Create admin and regular tokens
        admin_token = await auth_manager.create_token(
            agent_id="admin",
            role=Role.ADMIN
        )
        
        user_token = await auth_manager.create_token(
            agent_id="user",
            role=Role.OBSERVER
        )
        
        # Verify initial permissions
        assert not await auth_manager.authorize(user_token, Permission.WRITE)
        
        # Update permissions
        updated = await auth_manager.update_permissions(
            agent_id="user",
            new_role=Role.SPECIALIST,
            admin_token=admin_token
        )
        assert updated
        
        # Re-authenticate and verify new permissions
        auth = await auth_manager.authenticate(user_token.token)
        assert await auth_manager.authorize(auth, Permission.WRITE)
    
    @pytest.mark.asyncio
    async def test_lockout_mechanism(self, auth_manager):
        """Test account lockout after failed attempts"""
        # Create a valid token
        token = await auth_manager.create_token(
            agent_id="lockout_test",
            role=Role.SPECIALIST
        )
        
        # Simulate multiple failed authorization attempts
        for _ in range(6):
            await auth_manager.authorize(
                token, 
                Permission.ADMIN  # Permission the token doesn't have
            )
        
        # Account should be locked out
        auth = await auth_manager.authenticate(token.token)
        assert auth is None  # Authentication fails due to lockout
    
    @pytest.mark.asyncio
    async def test_communication_with_auth(self, comm_manager):
        """Test communication manager with authentication"""
        # Create tokens for different agents
        sender_token = await comm_manager.create_agent_token(
            agent_id="sender",
            role=Role.SPECIALIST
        )
        
        reader_token = await comm_manager.create_agent_token(
            agent_id="reader",
            role=Role.REVIEWER
        )
        
        # Create handoff with valid token
        handoff_id = await comm_manager.create_handoff(
            from_agent="sender",
            to_agent="receiver",
            handoff_type="task",
            data={"message": "test data"},
            instructions="Process this task",
            auth_token=sender_token.token
        )
        assert handoff_id is not None
        
        # Read handoff with valid token
        handoff_data = await comm_manager.read_handoff(
            handoff_id=handoff_id,
            auth_token=reader_token.token
        )
        assert handoff_data is not None
        assert handoff_data["from_agent"] == "sender"
        
        # Try to create handoff with reader token (should fail)
        with pytest.raises(PermissionError):
            await comm_manager.create_handoff(
                from_agent="reader",
                to_agent="receiver",
                handoff_type="task",
                data={"message": "unauthorized"},
                instructions="Should fail",
                auth_token=reader_token.token
            )
    
    @pytest.mark.asyncio
    async def test_decorator_authentication(self, auth_manager):
        """Test the @require_auth decorator"""
        
        class TestService:
            def __init__(self):
                self.auth_manager = auth_manager
                self.auth_token = None
            
            @require_auth(permission=Permission.WRITE)
            async def protected_method(self, data: str, authenticated_token=None):
                return f"Success: {data}, Agent: {authenticated_token.agent_id}"
            
            @require_auth(permission=Permission.ADMIN)
            async def admin_only_method(self, authenticated_token=None):
                return f"Admin access granted for {authenticated_token.agent_id}"
        
        service = TestService()
        
        # Create tokens
        writer_token = await auth_manager.create_token(
            agent_id="writer",
            role=Role.SPECIALIST
        )
        
        admin_token = await auth_manager.create_token(
            agent_id="admin",
            role=Role.ADMIN
        )
        
        # Test with valid writer token
        service.auth_token = writer_token.token
        result = await service.protected_method("test data")
        assert "Success" in result
        assert "writer" in result
        
        # Test admin method with writer token (should fail)
        with pytest.raises(PermissionError):
            await service.admin_only_method()
        
        # Test admin method with admin token
        service.auth_token = admin_token.token
        admin_result = await service.admin_only_method()
        assert "Admin access granted" in admin_result
    
    @pytest.mark.asyncio
    async def test_token_persistence(self, temp_workspace):
        """Test token storage persistence"""
        # Create tokens with first manager
        auth_manager1 = AuthenticationManager(temp_workspace)
        token1 = await auth_manager1.create_token(
            agent_id="persistent",
            role=Role.SPECIALIST
        )
        
        # Create second manager (should load existing tokens)
        auth_manager2 = AuthenticationManager(temp_workspace)
        
        # Authenticate with token from first manager
        auth = await auth_manager2.authenticate(token1.token)
        assert auth is not None
        assert auth.agent_id == "persistent"
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, temp_workspace):
        """Test security audit logging"""
        auth_manager = AuthenticationManager(temp_workspace)
        
        # Create token and perform operations
        token = await auth_manager.create_token(
            agent_id="audit_test",
            role=Role.SPECIALIST
        )
        
        # Successful authentication
        await auth_manager.authenticate(token.token)
        
        # Failed authorization
        await auth_manager.authorize(token, Permission.ADMIN)
        
        # Revoke token
        await auth_manager.revoke_token(token.token)
        
        # Check audit log exists
        audit_file = temp_workspace / "auth" / "audit" / "security_audit.log"
        assert audit_file.exists()
        
        # Verify log contents
        with open(audit_file, 'r') as f:
            log_content = f.read()
            assert "TOKEN_CREATED" in log_content
            assert "AUTH_FAILURE" in log_content
            assert "TOKEN_REVOKED" in log_content


# Example usage script
async def example_usage():
    """Demonstrate authentication system usage"""
    
    # Setup
    workspace = Path("./test_workspace")
    workspace.mkdir(exist_ok=True)
    
    # Initialize communication manager with authentication
    comm_manager = CommunicationManager(
        workspace_dir=workspace,
        enable_auth=True,
        auth_config={
            'token_lifetime_hours': 24,
            'secret_key': 'your-secret-key-here'  # In production, use environment variable
        }
    )
    
    # Wait for system token
    await asyncio.sleep(0.1)
    
    print("=== Authentication System Example ===\n")
    
    # Create tokens for different agents
    print("1. Creating agent tokens...")
    
    orchestrator_token = await comm_manager.create_agent_token(
        agent_id="orchestrator_001",
        role=Role.ORCHESTRATOR
    )
    print(f"✓ Orchestrator token created: {orchestrator_token.token[:20]}...")
    
    specialist_token = await comm_manager.create_agent_token(
        agent_id="backend_specialist",
        role=Role.SPECIALIST
    )
    print(f"✓ Specialist token created: {specialist_token.token[:20]}...")
    
    reviewer_token = await comm_manager.create_agent_token(
        agent_id="code_reviewer",
        role=Role.REVIEWER
    )
    print(f"✓ Reviewer token created: {reviewer_token.token[:20]}...")
    
    # Create handoff with authentication
    print("\n2. Creating authenticated handoff...")
    handoff_id = await comm_manager.create_handoff(
        from_agent="orchestrator_001",
        to_agent="backend_specialist",
        handoff_type="implementation",
        data={
            "task": "Implement user authentication",
            "requirements": ["JWT tokens", "Refresh mechanism", "Rate limiting"]
        },
        instructions="Implement the authentication module following security best practices",
        auth_token=orchestrator_token.token
    )
    print(f"✓ Handoff created: {handoff_id}")
    
    # Read handoff with different tokens
    print("\n3. Testing permission-based access...")
    
    # Specialist can read
    handoff_data = await comm_manager.read_handoff(
        handoff_id=handoff_id,
        auth_token=specialist_token.token
    )
    print(f"✓ Specialist successfully read handoff")
    
    # Reviewer can also read
    handoff_data = await comm_manager.read_handoff(
        handoff_id=handoff_id,
        auth_token=reviewer_token.token
    )
    print(f"✓ Reviewer successfully read handoff")
    
    # But reviewer cannot create handoffs
    try:
        await comm_manager.create_handoff(
            from_agent="code_reviewer",
            to_agent="backend_specialist",
            handoff_type="review",
            data={"comment": "Review needed"},
            instructions="Review the code",
            auth_token=reviewer_token.token
        )
    except PermissionError as e:
        print(f"✗ Reviewer blocked from creating handoff: {e}")
    
    # Validate tokens
    print("\n4. Validating tokens...")
    token_info = await comm_manager.validate_token(specialist_token.token)
    if token_info:
        print(f"✓ Token valid for {token_info['agent_id']}")
        print(f"  Role: {token_info['role']}")
        print(f"  Permissions: {', '.join(token_info['permissions'][:3])}...")
    
    # Check auth status
    print("\n5. Authentication system status:")
    status = comm_manager.get_auth_status()
    print(f"  Enabled: {status['enabled']}")
    print(f"  Has auth manager: {status['has_auth_manager']}")
    print(f"  Has system token: {status['has_system_token']}")
    print(f"  Auth directory: {status['auth_directory']}")
    
    # Token refresh example
    print("\n6. Token refresh mechanism...")
    if specialist_token.refresh_token:
        new_token = await comm_manager.refresh_agent_token(specialist_token.refresh_token)
        if new_token:
            print(f"✓ Token refreshed successfully")
            print(f"  New token: {new_token.token[:20]}...")
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())