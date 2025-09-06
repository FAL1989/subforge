"""
SubForge Plugin Sandbox
Provides secure execution environment for plugins
"""

import asyncio
import multiprocessing
import os
import resource
import signal
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from subforge.core.context.exceptions import ContextError as SubForgeError
from subforge.plugins.config import PluginPermission, PluginSecurityConfig
from subforge.plugins.plugin_manager import SubForgePlugin


class PluginSandboxError(SubForgeError):
    """Raised for sandbox-related errors"""


class SecurityViolation(PluginSandboxError):
    """Raised when a plugin violates security constraints"""


class ResourceLimitExceeded(PluginSandboxError):
    """Raised when a plugin exceeds resource limits"""


class PluginSandbox:
    """
    Provides a secure execution environment for plugins
    """

    def __init__(self, security_config: PluginSecurityConfig):
        """
        Initialize plugin sandbox

        Args:
            security_config: Security configuration
        """
        self.security_config = security_config
        self._original_limits = {}
        self._restricted_modules = {
            "os",
            "sys",
            "subprocess",
            "multiprocessing",
            "threading",
            "__builtins__",
        }

    def execute_in_sandbox(
        self, plugin: SubForgePlugin, method: str, context: Dict[str, Any]
    ) -> Any:
        """
        Execute a plugin method in a sandboxed environment

        Args:
            plugin: Plugin instance
            method: Method name to execute
            context: Execution context

        Returns:
            Method execution result

        Raises:
            PluginSandboxError: If execution fails
            SecurityViolation: If plugin violates security constraints
        """
        if not self.security_config.enable_sandbox:
            # Direct execution without sandbox
            return getattr(plugin, method)(context)

        # Execute in separate process for isolation
        with multiprocessing.Pool(processes=1) as pool:
            try:
                result = pool.apply_async(
                    self._sandboxed_execution,
                    args=(plugin, method, context, self.security_config),
                )

                # Wait with timeout
                return result.get(timeout=self.security_config.timeout_seconds)

            except multiprocessing.TimeoutError:
                raise ResourceLimitExceeded(
                    f"Plugin execution exceeded timeout of {self.security_config.timeout_seconds}s"
                )
            except Exception as e:
                raise PluginSandboxError(f"Plugin execution failed: {e}")

    @staticmethod
    def _sandboxed_execution(
        plugin: SubForgePlugin,
        method: str,
        context: Dict[str, Any],
        security_config: PluginSecurityConfig,
    ) -> Any:
        """
        Execute plugin in sandboxed process

        Args:
            plugin: Plugin instance
            method: Method to execute
            context: Execution context
            security_config: Security configuration

        Returns:
            Execution result
        """
        # Set resource limits
        PluginSandbox._set_resource_limits(security_config)

        # Set up restricted environment
        restricted_env = PluginSandbox._create_restricted_environment(security_config)

        # Execute with restrictions
        try:
            # Get method
            plugin_method = getattr(plugin, method)

            # Execute in restricted environment
            with PluginSandbox._restricted_execution(security_config):
                return plugin_method(context)

        except Exception as e:
            raise PluginSandboxError(f"Sandboxed execution failed: {e}")

    @staticmethod
    def _set_resource_limits(security_config: PluginSecurityConfig):
        """
        Set resource limits for the process

        Args:
            security_config: Security configuration
        """
        # Memory limit
        memory_limit = security_config.max_memory_mb * 1024 * 1024  # Convert to bytes
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

        # CPU time limit (soft limit only, hard limit unchanged)
        cpu_limit = security_config.timeout_seconds
        soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
        resource.setrlimit(resource.RLIMIT_CPU, (min(cpu_limit, hard), hard))

        # File descriptor limit
        resource.setrlimit(resource.RLIMIT_NOFILE, (100, 100))

        # Process limit
        resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))

    @staticmethod
    def _create_restricted_environment(
        security_config: PluginSecurityConfig,
    ) -> Dict[str, Any]:
        """
        Create a restricted execution environment

        Args:
            security_config: Security configuration

        Returns:
            Restricted environment dictionary
        """
        env = {}

        # Create safe builtins
        safe_builtins = {
            "None": None,
            "True": True,
            "False": False,
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,
        }

        # Add permission-based functions
        if PluginPermission.FILE_READ in security_config.allowed_permissions:
            safe_builtins["open"] = PluginSandbox._restricted_open_read

        env["__builtins__"] = safe_builtins
        return env

    @staticmethod
    def _restricted_open_read(filename: str, mode: str = "r", *args, **kwargs):
        """
        Restricted file open for reading only

        Args:
            filename: File to open
            mode: File mode
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            File handle

        Raises:
            SecurityViolation: If attempting to write or access restricted path
        """
        # Only allow read modes
        if "w" in mode or "a" in mode or "x" in mode or "+" in mode:
            raise SecurityViolation("Write operations not permitted")

        # Check path restrictions
        file_path = Path(filename).resolve()

        # Default denied paths
        denied_paths = [Path("/etc"), Path("/sys"), Path("/proc")]
        for denied_path in denied_paths:
            if denied_path in file_path.parents or file_path == denied_path:
                raise SecurityViolation(f"Access to {file_path} is denied")

        return open(filename, mode, *args, **kwargs)

    @staticmethod
    @contextmanager
    def _restricted_execution(security_config: PluginSecurityConfig):
        """
        Context manager for restricted execution

        Args:
            security_config: Security configuration
        """
        # Store original modules
        original_modules = {}
        restricted_imports = [
            "subprocess",
            "os.system",
            "os.popen",
            "os.execv",
            "multiprocessing",
            "threading",
        ]

        # Temporarily remove dangerous modules
        import sys

        for module_name in restricted_imports:
            if "." in module_name:
                parent, attr = module_name.rsplit(".", 1)
                if parent in sys.modules:
                    parent_module = sys.modules[parent]
                    if hasattr(parent_module, attr):
                        original_modules[module_name] = getattr(parent_module, attr)
                        delattr(parent_module, attr)
            elif module_name in sys.modules:
                original_modules[module_name] = sys.modules[module_name]
                del sys.modules[module_name]

        try:
            yield
        finally:
            # Restore modules
            for module_name, module in original_modules.items():
                if "." in module_name:
                    parent, attr = module_name.rsplit(".", 1)
                    if parent in sys.modules:
                        setattr(sys.modules[parent], attr, module)
                else:
                    sys.modules[module_name] = module


class PermissionChecker:
    """
    Checks and enforces plugin permissions
    """

    def __init__(self, allowed_permissions: Set[PluginPermission]):
        """
        Initialize permission checker

        Args:
            allowed_permissions: Set of allowed permissions
        """
        self.allowed_permissions = allowed_permissions

    def check_permission(self, permission: PluginPermission) -> bool:
        """
        Check if a permission is allowed

        Args:
            permission: Permission to check

        Returns:
            True if permission is allowed
        """
        return permission in self.allowed_permissions

    def require_permission(self, permission: PluginPermission):
        """
        Require a permission, raise exception if not allowed

        Args:
            permission: Required permission

        Raises:
            SecurityViolation: If permission is not allowed
        """
        if not self.check_permission(permission):
            raise SecurityViolation(f"Permission {permission.value} is not allowed")

    def check_file_access(self, path: Path, write: bool = False) -> bool:
        """
        Check if file access is allowed

        Args:
            path: File path
            write: Whether write access is requested

        Returns:
            True if access is allowed
        """
        if write:
            return self.check_permission(PluginPermission.FILE_WRITE)
        return self.check_permission(PluginPermission.FILE_READ)

    def check_network_access(self, host: str, port: int) -> bool:
        """
        Check if network access is allowed

        Args:
            host: Target host
            port: Target port

        Returns:
            True if access is allowed
        """
        return self.check_permission(PluginPermission.NETWORK)

    def check_execution(self, command: str) -> bool:
        """
        Check if command execution is allowed

        Args:
            command: Command to execute

        Returns:
            True if execution is allowed
        """
        return self.check_permission(PluginPermission.EXECUTE)


class SandboxMonitor:
    """
    Monitors plugin execution for resource usage and violations
    """

    def __init__(self, security_config: PluginSecurityConfig):
        """
        Initialize sandbox monitor

        Args:
            security_config: Security configuration
        """
        self.security_config = security_config
        self.violations: List[Dict[str, Any]] = []
        self.resource_usage: Dict[str, Any] = {}

    def record_violation(self, plugin_id: str, violation_type: str, details: str):
        """
        Record a security violation

        Args:
            plugin_id: Plugin that caused violation
            violation_type: Type of violation
            details: Violation details
        """
        self.violations.append(
            {
                "plugin_id": plugin_id,
                "type": violation_type,
                "details": details,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

    def check_resource_usage(self, plugin_id: str) -> Dict[str, Any]:
        """
        Check current resource usage

        Args:
            plugin_id: Plugin to check

        Returns:
            Resource usage statistics
        """
        usage = resource.getrusage(resource.RUSAGE_SELF)

        return {
            "plugin_id": plugin_id,
            "memory_mb": usage.ru_maxrss / 1024,  # Max resident set size
            "cpu_time": usage.ru_utime + usage.ru_stime,  # User + system CPU time
            "io_reads": usage.ru_inblock,  # Block input operations
            "io_writes": usage.ru_oublock,  # Block output operations
        }

    def is_within_limits(self, plugin_id: str) -> bool:
        """
        Check if plugin is within resource limits

        Args:
            plugin_id: Plugin to check

        Returns:
            True if within limits
        """
        usage = self.check_resource_usage(plugin_id)

        # Check memory limit
        if usage["memory_mb"] > self.security_config.max_memory_mb:
            self.record_violation(
                plugin_id, "memory_limit", f"Memory usage: {usage['memory_mb']}MB"
            )
            return False

        # Check CPU limit (as percentage of total time)
        # Note: This is a simplified check
        if usage["cpu_time"] > self.security_config.timeout_seconds:
            self.record_violation(plugin_id, "cpu_limit", f"CPU time: {usage['cpu_time']}s")
            return False

        return True

    def get_violations(self, plugin_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recorded violations

        Args:
            plugin_id: Filter by plugin ID (optional)

        Returns:
            List of violations
        """
        if plugin_id:
            return [v for v in self.violations if v["plugin_id"] == plugin_id]
        return self.violations.copy()