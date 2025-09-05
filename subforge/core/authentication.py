#!/usr/bin/env python3
"""
Authentication and Authorization System for SubForge
Provides token-based authentication, RBAC, and security audit logging
"""

import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor


class Permission(Enum):
    """Agent permission levels"""
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"
    CREATE_HANDOFF = "CREATE_HANDOFF"
    READ_HANDOFF = "READ_HANDOFF"
    DELETE_HANDOFF = "DELETE_HANDOFF"
    MODIFY_CONFIG = "MODIFY_CONFIG"
    VIEW_LOGS = "VIEW_LOGS"
    MANAGE_TOKENS = "MANAGE_TOKENS"


class Role(Enum):
    """Agent roles with predefined permission sets"""
    ADMIN = "ADMIN"
    ORCHESTRATOR = "ORCHESTRATOR"
    SPECIALIST = "SPECIALIST"
    REVIEWER = "REVIEWER"
    OBSERVER = "OBSERVER"
    GUEST = "GUEST"


# Role-based permission mappings
ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],  # All permissions
    Role.ORCHESTRATOR: [
        Permission.READ, Permission.WRITE, Permission.EXECUTE,
        Permission.CREATE_HANDOFF, Permission.READ_HANDOFF,
        Permission.DELETE_HANDOFF, Permission.VIEW_LOGS
    ],
    Role.SPECIALIST: [
        Permission.READ, Permission.WRITE, Permission.EXECUTE,
        Permission.CREATE_HANDOFF, Permission.READ_HANDOFF
    ],
    Role.REVIEWER: [
        Permission.READ, Permission.READ_HANDOFF, Permission.VIEW_LOGS
    ],
    Role.OBSERVER: [
        Permission.READ, Permission.VIEW_LOGS
    ],
    Role.GUEST: [
        Permission.READ
    ]
}


@dataclass
class AgentToken:
    """Secure token for agent authentication"""
    agent_id: str
    token: str
    role: Role
    permissions: List[Permission] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if token has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def has_permission(self, permission: Union[Permission, str]) -> bool:
        """Check if token has specific permission"""
        if isinstance(permission, str):
            try:
                permission = Permission(permission)
            except ValueError:
                return False
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert token to dictionary for storage"""
        return {
            "agent_id": self.agent_id,
            "token": self.token,
            "role": self.role.value,
            "permissions": [p.value for p in self.permissions],
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "refresh_token": self.refresh_token,
            "metadata": self.metadata,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentToken':
        """Create token from dictionary"""
        return cls(
            agent_id=data["agent_id"],
            token=data["token"],
            role=Role(data["role"]),
            permissions=[Permission(p) for p in data.get("permissions", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            refresh_token=data.get("refresh_token"),
            metadata=data.get("metadata", {}),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            usage_count=data.get("usage_count", 0)
        )


class TokenStore:
    """Secure storage for agent tokens"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.tokens_file = self.storage_path / "tokens.json"
        self.revoked_file = self.storage_path / "revoked_tokens.json"
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
        self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from persistent storage"""
        self.active_tokens: Dict[str, AgentToken] = {}
        self.revoked_tokens: Set[str] = set()
        
        # Load active tokens
        if self.tokens_file.exists():
            try:
                with open(self.tokens_file, 'r') as f:
                    data = json.load(f)
                    for token_data in data.values():
                        token = AgentToken.from_dict(token_data)
                        if not token.is_expired():
                            self.active_tokens[token.token] = token
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Failed to load tokens: {e}")
        
        # Load revoked tokens
        if self.revoked_file.exists():
            try:
                with open(self.revoked_file, 'r') as f:
                    self.revoked_tokens = set(json.load(f))
            except (json.JSONDecodeError) as e:
                self.logger.error(f"Failed to load revoked tokens: {e}")
    
    def _save_tokens(self):
        """Save tokens to persistent storage"""
        try:
            # Save active tokens
            tokens_data = {
                token: token_obj.to_dict() 
                for token, token_obj in self.active_tokens.items()
            }
            with open(self.tokens_file, 'w') as f:
                json.dump(tokens_data, f, indent=2)
            
            # Save revoked tokens
            with open(self.revoked_file, 'w') as f:
                json.dump(list(self.revoked_tokens), f, indent=2)
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to save tokens: {e}")
    
    async def store_token(self, token: AgentToken):
        """Store a new token"""
        async with self._lock:
            self.active_tokens[token.token] = token
            self._save_tokens()
            self.logger.info(f"Token stored for agent {token.agent_id}")
    
    async def get_token(self, token_str: str) -> Optional[AgentToken]:
        """Retrieve a token and update usage stats"""
        async with self._lock:
            if token_str in self.revoked_tokens:
                return None
            
            token = self.active_tokens.get(token_str)
            if token and not token.is_expired():
                # Update usage statistics
                token.last_used = datetime.now()
                token.usage_count += 1
                self._save_tokens()
                return token
            elif token and token.is_expired():
                # Remove expired token
                del self.active_tokens[token_str]
                self._save_tokens()
            
            return None
    
    async def revoke_token(self, token_str: str):
        """Revoke a token"""
        async with self._lock:
            if token_str in self.active_tokens:
                del self.active_tokens[token_str]
            self.revoked_tokens.add(token_str)
            self._save_tokens()
            self.logger.info(f"Token revoked: {token_str[:8]}...")
    
    async def cleanup_expired(self):
        """Remove expired tokens from storage"""
        async with self._lock:
            expired = [
                token for token, token_obj in self.active_tokens.items()
                if token_obj.is_expired()
            ]
            for token in expired:
                del self.active_tokens[token]
            
            if expired:
                self._save_tokens()
                self.logger.info(f"Cleaned up {len(expired)} expired tokens")


class SecurityAuditLog:
    """Audit logging for security events"""
    
    def __init__(self, log_path: Path):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.log_path / "security_audit.log"
        self.logger = logging.getLogger("security_audit")
        
        # Setup file handler for audit logs
        handler = logging.FileHandler(self.audit_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_auth_success(self, agent_id: str, permission: str, resource: str):
        """Log successful authentication"""
        self.logger.info(
            f"AUTH_SUCCESS - Agent: {agent_id}, Permission: {permission}, Resource: {resource}"
        )
    
    def log_auth_failure(self, agent_id: str, permission: str, resource: str, reason: str):
        """Log failed authentication attempt"""
        self.logger.warning(
            f"AUTH_FAILURE - Agent: {agent_id}, Permission: {permission}, "
            f"Resource: {resource}, Reason: {reason}"
        )
    
    def log_token_created(self, agent_id: str, role: str, expires_at: Optional[datetime]):
        """Log token creation"""
        expiry = expires_at.isoformat() if expires_at else "never"
        self.logger.info(
            f"TOKEN_CREATED - Agent: {agent_id}, Role: {role}, Expires: {expiry}"
        )
    
    def log_token_revoked(self, agent_id: str, token_preview: str):
        """Log token revocation"""
        self.logger.info(
            f"TOKEN_REVOKED - Agent: {agent_id}, Token: {token_preview}"
        )
    
    def log_permission_change(self, agent_id: str, old_role: str, new_role: str, admin_id: str):
        """Log permission changes"""
        self.logger.info(
            f"PERMISSION_CHANGE - Agent: {agent_id}, Old: {old_role}, "
            f"New: {new_role}, Admin: {admin_id}"
        )
    
    def log_suspicious_activity(self, agent_id: str, activity: str, details: str):
        """Log suspicious activities"""
        self.logger.warning(
            f"SUSPICIOUS_ACTIVITY - Agent: {agent_id}, Activity: {activity}, Details: {details}"
        )


class AuthenticationManager:
    """Main authentication and authorization manager"""
    
    def __init__(self, workspace_dir: Path, secret_key: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir)
        self.auth_dir = self.workspace_dir / "auth"
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.token_store = TokenStore(self.auth_dir / "tokens")
        self.audit_log = SecurityAuditLog(self.auth_dir / "audit")
        self.logger = logging.getLogger(__name__)
        
        # Setup secret key for token signing
        self.secret_key = secret_key or self._load_or_create_secret()
        
        # Token configuration
        self.default_token_lifetime = timedelta(hours=24)
        self.refresh_token_lifetime = timedelta(days=7)
        
        # Rate limiting
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def _load_or_create_secret(self) -> str:
        """Load or create secret key for token signing"""
        secret_file = self.auth_dir / ".secret_key"
        if secret_file.exists():
            with open(secret_file, 'r') as f:
                return f.read().strip()
        else:
            secret = secrets.token_hex(32)
            with open(secret_file, 'w') as f:
                f.write(secret)
            # Secure file permissions (Unix-like systems)
            secret_file.chmod(0o600)
            return secret
    
    def _sign_token(self, token: str) -> str:
        """Sign token with HMAC for integrity verification"""
        signature = hmac.new(
            self.secret_key.encode(),
            token.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{token}.{signature}"
    
    def _verify_signature(self, signed_token: str) -> Optional[str]:
        """Verify token signature"""
        try:
            token, signature = signed_token.rsplit('.', 1)
            expected_signature = hmac.new(
                self.secret_key.encode(),
                token.encode(),
                hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(signature, expected_signature):
                return token
        except ValueError:
            pass
        return None
    
    async def create_token(
        self,
        agent_id: str,
        role: Role,
        custom_permissions: Optional[List[Permission]] = None,
        lifetime: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentToken:
        """Create a new authentication token for an agent"""
        # Generate secure random token
        raw_token = secrets.token_urlsafe(32)
        signed_token = self._sign_token(raw_token)
        
        # Setup permissions
        permissions = custom_permissions or list(ROLE_PERMISSIONS[role])
        
        # Calculate expiration
        lifetime = lifetime or self.default_token_lifetime
        expires_at = datetime.now() + lifetime if lifetime else None
        
        # Generate refresh token for long-lived sessions
        refresh_token = None
        if lifetime and lifetime > timedelta(hours=1):
            refresh_token = secrets.token_urlsafe(32)
        
        # Create token object
        token = AgentToken(
            agent_id=agent_id,
            token=signed_token,
            role=role,
            permissions=permissions,
            expires_at=expires_at,
            refresh_token=refresh_token,
            metadata=metadata or {}
        )
        
        # Store token
        await self.token_store.store_token(token)
        
        # Audit log
        self.audit_log.log_token_created(agent_id, role.value, expires_at)
        
        return token
    
    async def authenticate(self, token_str: str) -> Optional[AgentToken]:
        """Authenticate using token"""
        # Verify signature
        if not self._verify_signature(token_str):
            self.audit_log.log_suspicious_activity(
                "unknown", "invalid_signature", f"Token: {token_str[:8]}..."
            )
            return None
        
        # Retrieve token
        token = await self.token_store.get_token(token_str)
        if not token:
            return None
        
        # Check if agent is locked out
        if self._is_locked_out(token.agent_id):
            self.audit_log.log_auth_failure(
                token.agent_id, "AUTH", "token", "account_locked"
            )
            return None
        
        return token
    
    async def authorize(
        self,
        token: AgentToken,
        permission: Permission,
        resource: Optional[str] = None
    ) -> bool:
        """Authorize an action based on token permissions"""
        # Check if token has required permission
        if not token.has_permission(permission):
            self.audit_log.log_auth_failure(
                token.agent_id,
                permission.value,
                resource or "unknown",
                "insufficient_permissions"
            )
            await self._record_failed_attempt(token.agent_id)
            return False
        
        # Log successful authorization
        self.audit_log.log_auth_success(
            token.agent_id,
            permission.value,
            resource or "unknown"
        )
        return True
    
    async def refresh_token(self, refresh_token_str: str) -> Optional[AgentToken]:
        """Refresh an expired token using refresh token"""
        # Find token with matching refresh token
        for token in self.token_store.active_tokens.values():
            if token.refresh_token == refresh_token_str:
                # Revoke old token
                await self.token_store.revoke_token(token.token)
                
                # Create new token with same permissions
                new_token = await self.create_token(
                    agent_id=token.agent_id,
                    role=token.role,
                    custom_permissions=token.permissions,
                    lifetime=self.default_token_lifetime,
                    metadata=token.metadata
                )
                
                self.logger.info(f"Token refreshed for agent {token.agent_id}")
                return new_token
        
        self.audit_log.log_suspicious_activity(
            "unknown", "invalid_refresh", f"Token: {refresh_token_str[:8]}..."
        )
        return None
    
    async def revoke_token(self, token_str: str, admin_id: Optional[str] = None):
        """Revoke a token"""
        token = await self.token_store.get_token(token_str)
        if token:
            await self.token_store.revoke_token(token_str)
            self.audit_log.log_token_revoked(
                token.agent_id,
                token_str[:8] + "..."
            )
    
    async def update_permissions(
        self,
        agent_id: str,
        new_role: Role,
        admin_token: AgentToken
    ) -> bool:
        """Update agent permissions (requires ADMIN permission)"""
        # Verify admin has permission
        if not await self.authorize(admin_token, Permission.ADMIN):
            return False
        
        # Find and update agent tokens
        updated = False
        for token in list(self.token_store.active_tokens.values()):
            if token.agent_id == agent_id:
                old_role = token.role
                token.role = new_role
                token.permissions = list(ROLE_PERMISSIONS[new_role])
                updated = True
                
                self.audit_log.log_permission_change(
                    agent_id, old_role.value, new_role.value, admin_token.agent_id
                )
        
        if updated:
            self.token_store._save_tokens()
        
        return updated
    
    def _is_locked_out(self, agent_id: str) -> bool:
        """Check if agent is locked out due to failed attempts"""
        if agent_id not in self.failed_attempts:
            return False
        
        # Remove old attempts
        cutoff = datetime.now() - self.lockout_duration
        self.failed_attempts[agent_id] = [
            attempt for attempt in self.failed_attempts[agent_id]
            if attempt > cutoff
        ]
        
        return len(self.failed_attempts[agent_id]) >= self.max_failed_attempts
    
    async def _record_failed_attempt(self, agent_id: str):
        """Record a failed authentication attempt"""
        if agent_id not in self.failed_attempts:
            self.failed_attempts[agent_id] = []
        
        self.failed_attempts[agent_id].append(datetime.now())
        
        if len(self.failed_attempts[agent_id]) >= self.max_failed_attempts:
            self.audit_log.log_suspicious_activity(
                agent_id, "account_locked", 
                f"Too many failed attempts ({self.max_failed_attempts})"
            )


def require_auth(permission: Optional[Permission] = None, resource: Optional[str] = None):
    """
    Decorator for methods requiring authentication and authorization
    
    Args:
        permission: Required permission for the operation
        resource: Optional resource identifier for audit logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract token from arguments or context
            token = kwargs.get('auth_token')
            if not token:
                # Try to get from first argument if it's a class method
                if args and hasattr(args[0], 'auth_token'):
                    token = args[0].auth_token
            
            if not token:
                raise PermissionError("Authentication required: No token provided")
            
            # Get auth manager from context
            auth_manager = kwargs.get('auth_manager')
            if not auth_manager and args and hasattr(args[0], 'auth_manager'):
                auth_manager = args[0].auth_manager
            
            if not auth_manager:
                raise RuntimeError("No authentication manager available")
            
            # Authenticate
            authenticated_token = await auth_manager.authenticate(token)
            if not authenticated_token:
                raise PermissionError("Authentication failed: Invalid or expired token")
            
            # Authorize if permission specified
            if permission:
                authorized = await auth_manager.authorize(
                    authenticated_token, permission, resource
                )
                if not authorized:
                    raise PermissionError(f"Authorization failed: Requires {permission.value} permission")
            
            # Call the original function with authenticated token
            kwargs['authenticated_token'] = authenticated_token
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Run async version in event loop for sync functions
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Export main components
__all__ = [
    'AuthenticationManager',
    'AgentToken',
    'Permission',
    'Role',
    'TokenStore',
    'SecurityAuditLog',
    'require_auth',
    'ROLE_PERMISSIONS'
]