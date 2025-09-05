#!/usr/bin/env python3
"""
Communication Manager - SubForge Factory
Manages inter-agent communication via structured markdown files
With enhanced security measures against path traversal attacks
With integrated authentication and authorization system
"""

import json
import logging
import os
import re
import html
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import asyncio
from urllib.parse import urlparse, quote

# Import authentication components
from .authentication import (
    AuthenticationManager,
    AgentToken,
    Permission,
    Role,
    require_auth
)


class InputSanitizer:
    """
    Comprehensive input sanitization for security.
    Provides methods to sanitize various input types to prevent injection attacks.
    """
    
    # Constants for validation
    MAX_AGENT_NAME_LENGTH = 64
    MAX_PAYLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_STRING_LENGTH = 100000  # 100KB for individual strings
    MAX_URL_LENGTH = 2048
    
    # Regex patterns for validation
    AGENT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    # Dangerous HTML/Script patterns for markdown
    DANGEROUS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<iframe[^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<embed[^>]*>', re.IGNORECASE),
        re.compile(r'<object[^>]*>.*?</object>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'data:text/html', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
        re.compile(r'<form[^>]*>', re.IGNORECASE),
        re.compile(r'<input[^>]*>', re.IGNORECASE),
    ]
    
    # Allowed markdown URL schemes
    ALLOWED_URL_SCHEMES = ['http', 'https', 'ftp', 'mailto', 'tel']
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the input sanitizer.
        
        Args:
            logger: Optional logger for security events
        """
        self.logger = logger or logging.getLogger(__name__)
        self._rate_limiter = {}  # Simple rate limiting cache
        self._sanitization_stats = {
            'total_sanitizations': 0,
            'blocked_attempts': 0,
            'modified_inputs': 0
        }
    
    def sanitize_agent_name(self, name: str) -> str:
        """
        Sanitize agent name to prevent injection attacks.
        
        Rules:
        - Only alphanumeric, underscore, and hyphen allowed
        - Maximum length of 64 characters
        - No special characters that could cause injection
        - Empty names become 'unknown_agent'
        
        Args:
            name: Raw agent name
            
        Returns:
            Sanitized agent name
            
        Raises:
            ValueError: If name is invalid after sanitization
        """
        self._log_sanitization('agent_name', name)
        
        if not name or not isinstance(name, str):
            self.logger.warning(f"Invalid agent name type: {type(name)}")
            return 'unknown_agent'
        
        # Strip whitespace
        name = name.strip()
        
        # Check length before processing
        if len(name) > self.MAX_AGENT_NAME_LENGTH:
            self.logger.warning(f"Agent name too long: {len(name)} chars")
            name = name[:self.MAX_AGENT_NAME_LENGTH]
            self._sanitization_stats['modified_inputs'] += 1
        
        # Remove any non-allowed characters
        original_name = name
        name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
        
        if name != original_name:
            self.logger.info(f"Sanitized agent name: '{original_name}' -> '{name}'")
            self._sanitization_stats['modified_inputs'] += 1
        
        # Validate against pattern
        if not self.AGENT_NAME_PATTERN.match(name):
            self.logger.warning(f"Agent name failed pattern validation: {name}")
            self._sanitization_stats['blocked_attempts'] += 1
            raise ValueError(f"Invalid agent name format: {name}")
        
        # Ensure not empty after sanitization
        if not name:
            return 'unknown_agent'
        
        return name
    
    def sanitize_json_data(self, data: Union[Dict, List, Any], max_depth: int = 10) -> Union[Dict, List, Any]:
        """
        Recursively sanitize JSON data to prevent injection attacks.
        
        Rules:
        - Validates JSON structure
        - Escapes string values
        - Enforces size limits
        - Prevents deeply nested structures (DoS prevention)
        - Removes null bytes and control characters
        
        Args:
            data: JSON-serializable data
            max_depth: Maximum nesting depth (default 10)
            
        Returns:
            Sanitized data
            
        Raises:
            ValueError: If data exceeds size limits or is malformed
        """
        self._log_sanitization('json_data', str(type(data)))
        
        # Check overall size
        try:
            data_size = len(json.dumps(data))
            if data_size > self.MAX_PAYLOAD_SIZE:
                self.logger.error(f"JSON payload too large: {data_size} bytes")
                self._sanitization_stats['blocked_attempts'] += 1
                raise ValueError(f"Payload exceeds maximum size of {self.MAX_PAYLOAD_SIZE} bytes")
        except (TypeError, RecursionError) as e:
            self.logger.error(f"Invalid JSON structure: {e}")
            raise ValueError(f"Invalid JSON structure: {e}")
        
        def _sanitize_recursive(obj: Any, depth: int = 0) -> Any:
            """Recursively sanitize JSON objects."""
            if depth > max_depth:
                self.logger.warning(f"Maximum nesting depth exceeded: {depth}")
                raise ValueError(f"JSON structure too deeply nested (max: {max_depth})")
            
            if isinstance(obj, dict):
                sanitized = {}
                for key, value in obj.items():
                    # Sanitize dictionary keys
                    if not isinstance(key, str):
                        key = str(key)
                    safe_key = self._sanitize_string(key, max_length=256)
                    sanitized[safe_key] = _sanitize_recursive(value, depth + 1)
                return sanitized
                
            elif isinstance(obj, list):
                return [_sanitize_recursive(item, depth + 1) for item in obj]
                
            elif isinstance(obj, str):
                return self._sanitize_string(obj)
                
            elif isinstance(obj, (int, float, bool, type(None))):
                return obj
                
            else:
                # Convert other types to string and sanitize
                return self._sanitize_string(str(obj))
        
        sanitized_data = _sanitize_recursive(data)
        return sanitized_data
    
    def sanitize_markdown(self, content: str, allow_html: bool = False) -> str:
        """
        Sanitize markdown content to prevent XSS and injection attacks.
        
        Rules:
        - Removes dangerous HTML/script tags
        - Escapes or removes event handlers
        - Validates and sanitizes URLs
        - Prevents markdown injection attacks
        - Optionally allows safe HTML subset
        
        Args:
            content: Raw markdown content
            allow_html: Whether to allow safe HTML subset (default False)
            
        Returns:
            Sanitized markdown content
        """
        self._log_sanitization('markdown', f"length={len(content) if content else 0}")
        
        if not content or not isinstance(content, str):
            return ''
        
        # Check content length
        if len(content) > self.MAX_STRING_LENGTH:
            self.logger.warning(f"Markdown content too long: {len(content)} chars")
            content = content[:self.MAX_STRING_LENGTH]
            self._sanitization_stats['modified_inputs'] += 1
        
        original_content = content
        
        # Remove dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(content):
                self.logger.warning(f"Dangerous pattern found in markdown: {pattern.pattern}")
                content = pattern.sub('', content)
                self._sanitization_stats['modified_inputs'] += 1
        
        # Remove null bytes and control characters (except newline, tab)
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        if not allow_html:
            # Escape all HTML if not allowed
            content = html.escape(content)
        else:
            # Allow only safe HTML tags
            safe_tags = ['p', 'br', 'strong', 'em', 'u', 'li', 'ul', 'ol', 'blockquote', 'code', 'pre', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            # More complex HTML sanitization would go here
            # For now, we'll just escape everything except basic formatting
            content = self._selective_html_escape(content, safe_tags)
        
        # Sanitize URLs in markdown links
        content = self._sanitize_markdown_urls(content)
        
        # Prevent markdown injection by escaping special characters at line start
        lines = content.split('\n')
        sanitized_lines = []
        for line in lines:
            # Escape potential command injection at line start
            if line.strip().startswith('!'):
                line = '\\' + line
            sanitized_lines.append(line)
        content = '\n'.join(sanitized_lines)
        
        if content != original_content:
            self.logger.info("Markdown content was sanitized")
        
        return content
    
    def _sanitize_string(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Basic string sanitization.
        
        Args:
            text: String to sanitize
            max_length: Optional maximum length
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Apply length limit
        if max_length is None:
            max_length = self.MAX_STRING_LENGTH
        if len(text) > max_length:
            text = text[:max_length]
            self._sanitization_stats['modified_inputs'] += 1
        
        return text
    
    def _sanitize_markdown_urls(self, content: str) -> str:
        """
        Sanitize URLs in markdown content.
        
        Args:
            content: Markdown content with potential URLs
            
        Returns:
            Content with sanitized URLs
        """
        # Pattern for markdown links: [text](url)
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        
        def sanitize_url(match):
            text = match.group(1)
            url = match.group(2)
            
            # Validate URL length
            if len(url) > self.MAX_URL_LENGTH:
                self.logger.warning(f"URL too long: {len(url)} chars")
                return f'[{text}](#invalid-url)'
            
            # Parse and validate URL scheme
            try:
                parsed = urlparse(url)
                if parsed.scheme and parsed.scheme.lower() not in self.ALLOWED_URL_SCHEMES:
                    self.logger.warning(f"Blocked URL scheme: {parsed.scheme}")
                    self._sanitization_stats['blocked_attempts'] += 1
                    return f'[{text}](#blocked-scheme)'
                
                # Prevent javascript: and data: URLs (double-check)
                if url.lower().startswith(('javascript:', 'data:', 'vbscript:')):
                    self.logger.warning(f"Blocked dangerous URL: {url[:50]}")
                    self._sanitization_stats['blocked_attempts'] += 1
                    return f'[{text}](#blocked-url)'
                    
            except Exception as e:
                self.logger.warning(f"Invalid URL format: {e}")
                return f'[{text}](#invalid-url)'
            
            # URL appears safe
            return match.group(0)
        
        return link_pattern.sub(sanitize_url, content)
    
    def _selective_html_escape(self, content: str, safe_tags: List[str]) -> str:
        """
        Selectively escape HTML, allowing only safe tags.
        
        Args:
            content: HTML content
            safe_tags: List of allowed tag names
            
        Returns:
            Selectively escaped HTML
        """
        # This is a simplified version. In production, use a proper HTML sanitizer like bleach
        for tag in safe_tags:
            # Temporarily replace safe tags with placeholders
            content = content.replace(f'<{tag}>', f'__SAFE_OPEN_{tag}__')
            content = content.replace(f'</{tag}>', f'__SAFE_CLOSE_{tag}__')
        
        # Escape everything else
        content = html.escape(content)
        
        # Restore safe tags
        for tag in safe_tags:
            content = content.replace(f'__SAFE_OPEN_{tag}__', f'<{tag}>')
            content = content.replace(f'__SAFE_CLOSE_{tag}__', f'</{tag}>')
        
        return content
    
    def check_rate_limit(self, identifier: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """
        Simple rate limiting check.
        
        Args:
            identifier: Unique identifier (e.g., agent_id, IP)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if within rate limit, False if exceeded
        """
        now = datetime.now()
        window_start = now.timestamp() - window_seconds
        
        if identifier not in self._rate_limiter:
            self._rate_limiter[identifier] = []
        
        # Clean old entries
        self._rate_limiter[identifier] = [
            ts for ts in self._rate_limiter[identifier]
            if ts > window_start
        ]
        
        # Check rate limit
        if len(self._rate_limiter[identifier]) >= max_requests:
            self.logger.warning(f"Rate limit exceeded for {identifier}")
            self._sanitization_stats['blocked_attempts'] += 1
            return False
        
        # Add current request
        self._rate_limiter[identifier].append(now.timestamp())
        return True
    
    def _log_sanitization(self, input_type: str, details: str = ""):
        """
        Log sanitization event for audit trail.
        
        Args:
            input_type: Type of input being sanitized
            details: Additional details
        """
        self._sanitization_stats['total_sanitizations'] += 1
        self.logger.debug(f"Sanitizing {input_type}: {details}")
    
    def get_sanitization_stats(self) -> Dict[str, int]:
        """
        Get sanitization statistics.
        
        Returns:
            Dictionary with sanitization statistics
        """
        return self._sanitization_stats.copy()
    
    def validate_file_size(self, size_bytes: int, max_size: Optional[int] = None) -> bool:
        """
        Validate file size is within acceptable limits.
        
        Args:
            size_bytes: Size of file in bytes
            max_size: Maximum allowed size (uses default if None)
            
        Returns:
            True if size is acceptable, False otherwise
        """
        if max_size is None:
            max_size = self.MAX_PAYLOAD_SIZE
        
        if size_bytes > max_size:
            self.logger.warning(f"File size {size_bytes} exceeds limit {max_size}")
            self._sanitization_stats['blocked_attempts'] += 1
            return False
        
        return True
    
    def sanitize_file_content(self, content: bytes, content_type: str = 'text/plain') -> bytes:
        """
        Sanitize file content based on content type.
        
        Args:
            content: Raw file content
            content_type: MIME type of content
            
        Returns:
            Sanitized content
            
        Raises:
            ValueError: If content is dangerous or invalid
        """
        # Check size
        if not self.validate_file_size(len(content)):
            raise ValueError("File content exceeds maximum size")
        
        # For text content, perform additional sanitization
        if content_type.startswith('text/') or content_type == 'application/json':
            try:
                text_content = content.decode('utf-8')
                # Remove null bytes and control characters
                text_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text_content)
                content = text_content.encode('utf-8')
            except UnicodeDecodeError:
                self.logger.warning("Failed to decode file content as UTF-8")
                # Content might be binary, return as-is but log the event
        
        return content


class CommunicationManager:
    """Manages structured communication between factory agents with enhanced security and authentication"""

    def __init__(self, workspace_dir: Path, enable_auth: bool = True, auth_config: Optional[Dict[str, Any]] = None):
        # Setup logging for security events first
        self.logger = logging.getLogger(__name__)
        
        # Initialize input sanitizer for comprehensive security
        self.sanitizer = InputSanitizer(logger=self.logger)
        
        # Convert to absolute path and set as workspace
        # The workspace itself is trusted, we validate subdirectories
        self.workspace_dir = Path(workspace_dir).resolve()
        if not self.workspace_dir.exists():
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Define allowed subdirectories (whitelist approach)
        self.allowed_subdirs = ["communication", "handoffs", "logs", "data", "auth"]
        
        # Setup communication directories with validation
        self.communication_dir = self._create_safe_directory(self.workspace_dir / "communication")
        self.handoffs_dir = self._create_safe_directory(self.communication_dir / "handoffs")
        
        # Initialize authentication system
        self.auth_enabled = enable_auth
        self.auth_manager = None
        self.system_token = None  # System token for internal operations
        
        if self.auth_enabled:
            self._initialize_authentication(auth_config or {})
    
    def _initialize_authentication(self, auth_config: Dict[str, Any]):
        """Initialize the authentication system with configuration"""
        try:
            # Create authentication manager
            self.auth_manager = AuthenticationManager(
                workspace_dir=self.workspace_dir,
                secret_key=auth_config.get('secret_key')
            )
            
            # Configure token lifetimes if provided
            if 'token_lifetime_hours' in auth_config:
                from datetime import timedelta
                self.auth_manager.default_token_lifetime = timedelta(
                    hours=auth_config['token_lifetime_hours']
                )
            
            # Create system token for internal operations
            asyncio.create_task(self._create_system_token())
            
            self.logger.info("Authentication system initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize authentication: {e}")
            self.auth_enabled = False
    
    async def _create_system_token(self):
        """Create a system token for internal operations"""
        if self.auth_manager:
            self.system_token = await self.auth_manager.create_token(
                agent_id="SYSTEM",
                role=Role.ADMIN,
                metadata={"type": "system", "created_by": "CommunicationManager"}
            )
            self.logger.info("System token created for internal operations")

    def _validate_safe_path(self, target_path: Path, base_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Validate that a path is safe and doesn't allow traversal outside allowed directories.
        
        Security measures:
        - Normalizes path to prevent ../ sequences
        - Checks path is within allowed base directory
        - Prevents symbolic link attacks
        - Validates against directory traversal patterns
        
        Args:
            target_path: Path to validate
            base_dir: Base directory to restrict access within (defaults to workspace)
            
        Returns:
            Normalized safe path or None if validation fails
        """
        if base_dir is None:
            base_dir = self.workspace_dir if hasattr(self, 'workspace_dir') else Path.cwd()
        
        # Use logger if available, otherwise fail silently (during init)
        has_logger = hasattr(self, 'logger')
        
        try:
            # Convert to Path objects and resolve to absolute paths
            target = Path(target_path).resolve()
            base = Path(base_dir).resolve()
            
            # Check for directory traversal sequences before normalization
            path_str = str(target_path)
            if any(traversal in path_str for traversal in ['../', '..\\', '%2e%2e', '%252e']):
                if has_logger:
                    self.logger.warning(f"Path traversal attempt detected: {path_str}")
                return None
            
            # Use os.path.commonpath for secure comparison
            try:
                common = Path(os.path.commonpath([str(base), str(target)]))
                if common != base:
                    if has_logger:
                        self.logger.warning(f"Path outside allowed directory: {target}")
                    return None
            except ValueError:
                # Paths are on different drives (Windows) or invalid
                if has_logger:
                    self.logger.warning(f"Invalid path comparison: {target} vs {base}")
                return None
            
            # Check if path exists and is not a symbolic link (prevent symlink attacks)
            if target.exists() and target.is_symlink():
                real_path = target.resolve()
                # Verify the symlink target is also within allowed directory
                if not self._validate_safe_path(real_path, base_dir):
                    if has_logger:
                        self.logger.warning(f"Symbolic link points outside allowed directory: {target}")
                    return None
            
            return target
            
        except (OSError, ValueError) as e:
            if has_logger:
                self.logger.error(f"Path validation error: {e}")
            return None
    
    def _create_safe_directory(self, directory: Path) -> Path:
        """
        Safely create a directory with validation.
        
        Args:
            directory: Directory path to create
            
        Returns:
            Created directory path
            
        Raises:
            ValueError: If directory path is unsafe
        """
        # Validate the directory path
        safe_dir = self._validate_safe_path(directory, self.workspace_dir)
        if not safe_dir:
            raise ValueError(f"Unsafe directory path: {directory}")
        
        # Check if directory name is in allowed list (for subdirectories)
        if safe_dir != self.workspace_dir:
            dir_parts = safe_dir.relative_to(self.workspace_dir).parts
            if dir_parts and not any(part in self.allowed_subdirs for part in dir_parts):
                self.logger.info(f"Creating new directory outside whitelist: {safe_dir}")
        
        # Create the directory
        safe_dir.mkdir(parents=True, exist_ok=True)
        return safe_dir
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path injection.
        Now uses the enhanced InputSanitizer for consistent security.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for use
        """
        # Use the sanitizer's agent name method as it has similar requirements
        # but we'll add file-specific handling
        if not filename or not isinstance(filename, str):
            return 'unnamed_file'
        
        # Remove any path separators and dangerous characters
        dangerous_chars = ['/', '\\', '..', '~', ':', '*', '?', '"', '<', '>', '|', '\0', '\n', '\r', '\t']
        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Limit length to prevent buffer overflow attacks
        max_length = 255
        if len(sanitized) > max_length:
            # Keep extension if possible
            ext_pos = sanitized.rfind('.')
            if ext_pos > 0 and ext_pos > max_length - 20:
                ext = sanitized[ext_pos:][:20]  # Max 20 chars for extension
                sanitized = sanitized[:max_length - len(ext)] + ext
            else:
                sanitized = sanitized[:max_length]
        
        # Ensure filename is not empty or dangerous
        if not sanitized or sanitized.strip() in ['', '.', '..', 'CON', 'PRN', 'AUX', 'NUL']:
            sanitized = 'unnamed_file'
        
        return sanitized

    async def create_handoff(
        self,
        from_agent: str,
        to_agent: str,
        handoff_type: str,
        data: Dict[str, Any],
        instructions: str,
        auth_token: Optional[str] = None,
    ) -> str:
        """
        Create a formal handoff between agents with security validation and authentication.
        
        Security measures:
        - Requires authentication token with CREATE_HANDOFF permission
        - Validates and sanitizes all input parameters
        - Uses secure file paths with validation
        - Prevents path injection in filenames
        - Logs security events and audit trail
        
        Args:
            from_agent: Source agent name
            to_agent: Target agent name
            handoff_type: Type of handoff
            data: Data to transfer
            instructions: Instructions for the target agent
            auth_token: Authentication token (required if auth is enabled)
            
        Returns:
            Secure handoff ID
            
        Raises:
            PermissionError: If authentication fails or insufficient permissions
            ValueError: If invalid parameters provided
        """
        # Authentication check if enabled
        if self.auth_enabled and self.auth_manager:
            if not auth_token:
                # Use system token for backward compatibility
                if self.system_token:
                    auth_token = self.system_token.token
                else:
                    raise PermissionError("Authentication required: No token provided")
            
            # Authenticate and authorize
            token = await self.auth_manager.authenticate(auth_token)
            if not token:
                raise PermissionError("Authentication failed: Invalid or expired token")
            
            # Check permission
            if not await self.auth_manager.authorize(token, Permission.CREATE_HANDOFF, f"handoff:{from_agent}->{to_agent}"):
                raise PermissionError("Authorization failed: CREATE_HANDOFF permission required")
            
            # Log the authenticated operation
            self.logger.info(f"Authenticated handoff creation by {token.agent_id}")
        
        # Apply rate limiting
        rate_limit_id = auth_token[:20] if auth_token else 'anonymous'
        if not self.sanitizer.check_rate_limit(f"create_handoff:{rate_limit_id}", max_requests=50, window_seconds=60):
            raise PermissionError("Rate limit exceeded for handoff creation")
        
        # Use enhanced sanitization for agent names
        from_agent = self.sanitizer.sanitize_agent_name(from_agent)
        to_agent = self.sanitizer.sanitize_agent_name(to_agent)
        handoff_type = self.sanitizer.sanitize_agent_name(handoff_type)  # Similar rules for type
        
        # Sanitize data payload
        data = self.sanitizer.sanitize_json_data(data)
        
        # Generate secure handoff ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Use a more secure hash to prevent predictability
        agent_hash = abs(hash(f"{from_agent}_{to_agent}_{timestamp}")) % 10000
        handoff_id = f"handoff_{timestamp}_{agent_hash:04x}"
        
        # Sanitize the handoff ID to ensure it's safe
        handoff_id = self._sanitize_filename(handoff_id)

        handoff_data = {
            "handoff_id": handoff_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "handoff_type": handoff_type,
            "data": data,
            "instructions": instructions,
            "timestamp": datetime.now().isoformat(),
            "status": "created",
        }

        try:
            # Validate and create JSON file path
            json_filename = self._sanitize_filename(f"{handoff_id}.json")
            handoff_file = self.handoffs_dir / json_filename
            
            # Validate the full path before writing
            safe_json_path = self._validate_safe_path(handoff_file, self.workspace_dir)
            if not safe_json_path:
                self.logger.error(f"Unsafe handoff path rejected: {handoff_file}")
                raise ValueError(f"Invalid handoff file path")
            
            # Save as JSON with secure file handling
            with open(safe_json_path, "w", encoding='utf-8') as f:
                json.dump(handoff_data, f, indent=2, ensure_ascii=False)

            # Sanitize instructions using markdown sanitizer
            safe_instructions = self.sanitizer.sanitize_markdown(instructions, allow_html=False)
            
            # Create Markdown content with fully sanitized data
            handoff_md = f"""# Handoff: {handoff_id}

**From**: @{from_agent}  
**To**: @{to_agent}  
**Type**: {handoff_type}  
**Created**: {handoff_data['timestamp']}

## Instructions
{safe_instructions}

## Data
```json
{json.dumps(data, indent=2, ensure_ascii=False)}
```
"""

            # Validate and create Markdown file path
            md_filename = self._sanitize_filename(f"{handoff_id}.md")
            handoff_md_file = self.handoffs_dir / md_filename
            
            # Validate the full path before writing
            safe_md_path = self._validate_safe_path(handoff_md_file, self.workspace_dir)
            if not safe_md_path:
                self.logger.error(f"Unsafe markdown path rejected: {handoff_md_file}")
                raise ValueError(f"Invalid markdown file path")
            
            # Save Markdown with secure file handling
            with open(safe_md_path, "w", encoding='utf-8') as f:
                f.write(handoff_md)

            # Log successful handoff creation
            self.logger.info(f"Handoff created: {handoff_id} from {from_agent} to {to_agent}")
            print(f"    📨 Created handoff {handoff_id}: @{from_agent} → @{to_agent}")
            return handoff_id
            
        except (OSError, IOError) as e:
            self.logger.error(f"Failed to create handoff: {e}")
            raise RuntimeError(f"Handoff creation failed: {e}")
    
    async def read_handoff(self, handoff_id: str, auth_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Safely read a handoff file with path validation and authentication.
        
        Args:
            handoff_id: ID of the handoff to read
            auth_token: Authentication token (required if auth is enabled)
            
        Returns:
            Handoff data or None if not found/invalid
            
        Raises:
            PermissionError: If authentication fails or insufficient permissions
        """
        # Authentication check if enabled
        if self.auth_enabled and self.auth_manager:
            if not auth_token:
                # Use system token for backward compatibility
                if self.system_token:
                    auth_token = self.system_token.token
                else:
                    raise PermissionError("Authentication required: No token provided")
            
            # Authenticate and authorize
            token = await self.auth_manager.authenticate(auth_token)
            if not token:
                raise PermissionError("Authentication failed: Invalid or expired token")
            
            # Check permission
            if not await self.auth_manager.authorize(token, Permission.READ_HANDOFF, f"handoff:{handoff_id}"):
                raise PermissionError("Authorization failed: READ_HANDOFF permission required")
        
        # Apply rate limiting for reads
        rate_limit_id = auth_token[:20] if auth_token else 'anonymous'
        if not self.sanitizer.check_rate_limit(f"read_handoff:{rate_limit_id}", max_requests=100, window_seconds=60):
            raise PermissionError("Rate limit exceeded for handoff reading")
        
        # Sanitize the handoff ID using enhanced sanitizer
        safe_handoff_id = self.sanitizer.sanitize_agent_name(handoff_id)
        
        # Construct and validate the file path
        handoff_file = self.handoffs_dir / f"{safe_handoff_id}.json"
        safe_path = self._validate_safe_path(handoff_file, self.workspace_dir)
        
        if not safe_path or not safe_path.exists():
            self.logger.warning(f"Handoff not found or invalid path: {handoff_id}")
            return None
        
        try:
            with open(safe_path, "r", encoding='utf-8') as f:
                return json.load(f)
        except (OSError, IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to read handoff {handoff_id}: {e}")
            return None
    
    async def list_handoffs(self, agent_name: Optional[str] = None, auth_token: Optional[str] = None) -> list:
        """
        Safely list handoffs with optional filtering by agent and authentication.
        
        Args:
            agent_name: Optional agent name to filter by
            auth_token: Authentication token (required if auth is enabled)
            
        Returns:
            List of handoff IDs
            
        Raises:
            PermissionError: If authentication fails or insufficient permissions
        """
        # Authentication check if enabled
        if self.auth_enabled and self.auth_manager:
            if not auth_token:
                # Use system token for backward compatibility
                if self.system_token:
                    auth_token = self.system_token.token
                else:
                    raise PermissionError("Authentication required: No token provided")
            
            # Authenticate and authorize
            token = await self.auth_manager.authenticate(auth_token)
            if not token:
                raise PermissionError("Authentication failed: Invalid or expired token")
            
            # Check permission
            if not await self.auth_manager.authorize(token, Permission.READ, "handoffs:list"):
                raise PermissionError("Authorization failed: READ permission required")
        handoffs = []
        
        # Validate the handoffs directory is safe
        safe_dir = self._validate_safe_path(self.handoffs_dir, self.workspace_dir)
        if not safe_dir or not safe_dir.exists():
            self.logger.warning("Handoffs directory not found or invalid")
            return handoffs
        
        try:
            # Safely iterate through JSON files
            for file_path in safe_dir.glob("*.json"):
                # Validate each file path
                if not self._validate_safe_path(file_path, self.workspace_dir):
                    self.logger.warning(f"Skipping potentially unsafe file: {file_path}")
                    continue
                
                if agent_name:
                    # Read and filter by agent name
                    handoff_data = self.read_handoff(file_path.stem)
                    if handoff_data and (
                        handoff_data.get('from_agent') == agent_name or 
                        handoff_data.get('to_agent') == agent_name
                    ):
                        handoffs.append(file_path.stem)
                else:
                    handoffs.append(file_path.stem)
                    
        except OSError as e:
            self.logger.error(f"Failed to list handoffs: {e}")
        
        return sorted(handoffs, reverse=True)  # Most recent first
    
    # Authentication Management Methods
    
    async def create_agent_token(
        self,
        agent_id: str,
        role: Role,
        admin_token: Optional[str] = None,
        custom_permissions: Optional[List[Permission]] = None,
        lifetime_hours: Optional[int] = None
    ) -> AgentToken:
        """
        Create a new authentication token for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            role: Role to assign to the agent
            admin_token: Admin token for authorization (required for non-system calls)
            custom_permissions: Optional custom permissions list
            lifetime_hours: Token lifetime in hours (uses default if not specified)
            
        Returns:
            Created AgentToken object
            
        Raises:
            PermissionError: If not authorized to create tokens
            RuntimeError: If authentication system is not enabled
        """
        if not self.auth_enabled or not self.auth_manager:
            raise RuntimeError("Authentication system is not enabled")
        
        # Check if this is a system call or requires admin authorization
        if admin_token:
            token = await self.auth_manager.authenticate(admin_token)
            if not token:
                raise PermissionError("Invalid admin token")
            
            if not await self.auth_manager.authorize(token, Permission.MANAGE_TOKENS):
                raise PermissionError("MANAGE_TOKENS permission required to create tokens")
        
        # Create the token
        from datetime import timedelta
        lifetime = timedelta(hours=lifetime_hours) if lifetime_hours else None
        
        new_token = await self.auth_manager.create_token(
            agent_id=agent_id,
            role=role,
            custom_permissions=custom_permissions,
            lifetime=lifetime
        )
        
        self.logger.info(f"Token created for agent {agent_id} with role {role.value}")
        return new_token
    
    async def revoke_agent_token(
        self,
        token_to_revoke: str,
        admin_token: Optional[str] = None
    ) -> bool:
        """
        Revoke an agent's authentication token.
        
        Args:
            token_to_revoke: Token string to revoke
            admin_token: Admin token for authorization
            
        Returns:
            True if successfully revoked, False otherwise
            
        Raises:
            PermissionError: If not authorized to revoke tokens
            RuntimeError: If authentication system is not enabled
        """
        if not self.auth_enabled or not self.auth_manager:
            raise RuntimeError("Authentication system is not enabled")
        
        # Check authorization
        if admin_token:
            token = await self.auth_manager.authenticate(admin_token)
            if not token:
                raise PermissionError("Invalid admin token")
            
            if not await self.auth_manager.authorize(token, Permission.MANAGE_TOKENS):
                raise PermissionError("MANAGE_TOKENS permission required to revoke tokens")
            
            admin_id = token.agent_id
        else:
            admin_id = "SYSTEM"
        
        # Revoke the token
        await self.auth_manager.revoke_token(token_to_revoke, admin_id)
        self.logger.info(f"Token revoked by {admin_id}")
        return True
    
    async def refresh_agent_token(
        self,
        refresh_token: str
    ) -> Optional[AgentToken]:
        """
        Refresh an expired token using a refresh token.
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            New AgentToken if successful, None otherwise
            
        Raises:
            RuntimeError: If authentication system is not enabled
        """
        if not self.auth_enabled or not self.auth_manager:
            raise RuntimeError("Authentication system is not enabled")
        
        new_token = await self.auth_manager.refresh_token(refresh_token)
        if new_token:
            self.logger.info(f"Token refreshed for agent {new_token.agent_id}")
        return new_token
    
    async def update_agent_permissions(
        self,
        agent_id: str,
        new_role: Role,
        admin_token: str
    ) -> bool:
        """
        Update an agent's role and permissions.
        
        Args:
            agent_id: ID of agent to update
            new_role: New role to assign
            admin_token: Admin token for authorization
            
        Returns:
            True if successfully updated, False otherwise
            
        Raises:
            PermissionError: If not authorized to update permissions
            RuntimeError: If authentication system is not enabled
        """
        if not self.auth_enabled or not self.auth_manager:
            raise RuntimeError("Authentication system is not enabled")
        
        # Authenticate admin
        token = await self.auth_manager.authenticate(admin_token)
        if not token:
            raise PermissionError("Invalid admin token")
        
        # Update permissions
        updated = await self.auth_manager.update_permissions(
            agent_id=agent_id,
            new_role=new_role,
            admin_token=token
        )
        
        if updated:
            self.logger.info(f"Permissions updated for agent {agent_id} to role {new_role.value}")
        
        return updated
    
    async def validate_token(
        self,
        token_str: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a token and return its information.
        
        Args:
            token_str: Token to validate
            
        Returns:
            Token information dict if valid, None otherwise
            
        Raises:
            RuntimeError: If authentication system is not enabled
        """
        if not self.auth_enabled or not self.auth_manager:
            raise RuntimeError("Authentication system is not enabled")
        
        token = await self.auth_manager.authenticate(token_str)
        if token:
            return {
                "agent_id": token.agent_id,
                "role": token.role.value,
                "permissions": [p.value for p in token.permissions],
                "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                "usage_count": token.usage_count,
                "last_used": token.last_used.isoformat() if token.last_used else None
            }
        return None
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get the current authentication system status.
        
        Returns:
            Dictionary with authentication system status
        """
        return {
            "enabled": self.auth_enabled,
            "has_auth_manager": self.auth_manager is not None,
            "has_system_token": self.system_token is not None,
            "workspace": str(self.workspace_dir),
            "auth_directory": str(self.workspace_dir / "auth") if self.auth_enabled else None
        }
    
    def get_sanitization_stats(self) -> Dict[str, Any]:
        """
        Get input sanitization statistics for security monitoring.
        
        Returns:
            Dictionary with sanitization statistics including:
            - total_sanitizations: Total number of sanitization operations
            - blocked_attempts: Number of blocked malicious attempts
            - modified_inputs: Number of inputs that were modified during sanitization
        """
        return self.sanitizer.get_sanitization_stats()
    
    async def validate_and_sanitize_input(
        self,
        input_type: str,
        value: Any,
        auth_token: Optional[str] = None
    ) -> Any:
        """
        Public method to validate and sanitize any input type.
        Useful for external components that need to sanitize data before processing.
        
        Args:
            input_type: Type of input ('agent_name', 'json_data', 'markdown')
            value: Value to sanitize
            auth_token: Optional authentication token for rate limiting
            
        Returns:
            Sanitized value
            
        Raises:
            ValueError: If input is invalid or dangerous
            PermissionError: If rate limit exceeded
        """
        # Apply rate limiting if token provided
        if auth_token:
            rate_limit_id = auth_token[:20]
            if not self.sanitizer.check_rate_limit(f"sanitize:{rate_limit_id}", max_requests=200, window_seconds=60):
                raise PermissionError("Rate limit exceeded for sanitization")
        
        if input_type == 'agent_name':
            return self.sanitizer.sanitize_agent_name(value)
        elif input_type == 'json_data':
            return self.sanitizer.sanitize_json_data(value)
        elif input_type == 'markdown':
            return self.sanitizer.sanitize_markdown(value, allow_html=False)
        elif input_type == 'filename':
            return self._sanitize_filename(value)
        else:
            raise ValueError(f"Unknown input type for sanitization: {input_type}")
    
    def reset_sanitization_stats(self) -> None:
        """
        Reset sanitization statistics. Should be called periodically
        or after exporting stats for monitoring.
        """
        self.sanitizer._sanitization_stats = {
            'total_sanitizations': 0,
            'blocked_attempts': 0,
            'modified_inputs': 0
        }
        self.logger.info("Sanitization statistics reset")