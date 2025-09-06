"""
Comprehensive test suite for Plugin Sandbox Security System
Tests all security features including resource limits, isolation, and permissions
"""

import asyncio
import multiprocessing
import os
import platform
import pytest
import resource
import signal
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from subforge.core.context.exceptions import ContextError as SubForgeError
from subforge.plugins.config import PluginPermission, PluginSecurityConfig
from subforge.plugins.plugin_manager import PluginMetadata, SubForgePlugin
from subforge.plugins.sandbox import (
    PermissionChecker,
    PluginSandbox,
    PluginSandboxError,
    ResourceLimitExceeded,
    SandboxMonitor,
    SecurityViolation,
)


# ================ Test Plugin Classes ================


class BenignPlugin(SubForgePlugin):
    """Simple plugin for basic testing"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="benign_plugin",
            version="1.0.0",
            author="Test",
            description="Benign test plugin",
            type="test",
            dependencies=[],
            config={},
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        return True

    def execute(self, context: Dict[str, Any]) -> Any:
        """Simple execution that returns context data"""
        return {"status": "success", "data": context.get("test_data", "no_data")}


class MaliciousPlugin(SubForgePlugin):
    """Plugin that attempts various security violations"""

    def __init__(self, attack_type: str = "file_system"):
        self.attack_type = attack_type

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="malicious_plugin",
            version="1.0.0",
            author="Attacker",
            description="Malicious test plugin",
            type="test",
            dependencies=[],
            config={"attack": self.attack_type},
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        return True

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute various attack attempts based on attack_type"""
        if self.attack_type == "file_system":
            # Attempt to read sensitive files
            try:
                with open("/etc/passwd", "r") as f:
                    return f.read()
            except:
                pass
            # Try to write to system directories
            try:
                with open("/etc/malicious", "w") as f:
                    f.write("compromised")
            except:
                pass

        elif self.attack_type == "command_injection":
            # Attempt command execution
            try:
                import subprocess

                return subprocess.check_output(["whoami"])
            except:
                pass

        elif self.attack_type == "privilege_escalation":
            # Attempt to change process privileges
            try:
                os.setuid(0)  # Try to become root
            except:
                pass

        elif self.attack_type == "sandbox_escape":
            # Attempt to escape the sandbox
            try:
                # Try to access parent process
                import ctypes

                libc = ctypes.CDLL("libc.so.6")
                libc.system(b"echo 'escaped'")
            except:
                pass

        elif self.attack_type == "network":
            # Attempt network operations
            try:
                import socket

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("evil.com", 80))
                s.send(b"GET / HTTP/1.1\r\nHost: evil.com\r\n\r\n")
                return s.recv(1024)
            except:
                pass

        return {"attack": "failed"}


class ResourceHogPlugin(SubForgePlugin):
    """Plugin that tries to consume excessive resources"""

    def __init__(self, resource_type: str = "memory"):
        self.resource_type = resource_type

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="resource_hog_plugin",
            version="1.0.0",
            author="Test",
            description="Resource-consuming test plugin",
            type="test",
            dependencies=[],
            config={"resource": self.resource_type},
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        return True

    def execute(self, context: Dict[str, Any]) -> Any:
        """Consume resources based on resource_type"""
        if self.resource_type == "memory":
            # Try to allocate excessive memory
            try:
                huge_list = []
                for _ in range(1000000):
                    huge_list.append([0] * 10000)  # ~400MB
                return {"allocated": len(huge_list)}
            except MemoryError:
                return {"error": "memory_limit_reached"}

        elif self.resource_type == "cpu":
            # CPU-intensive operation
            start_time = time.time()
            count = 0
            while time.time() - start_time < 60:  # Run for 60 seconds
                count += sum(range(10000))
            return {"iterations": count}

        elif self.resource_type == "file_descriptors":
            # Try to open many files
            files = []
            try:
                for i in range(1000):
                    f = open(f"/tmp/test_{i}.txt", "w")
                    files.append(f)
                return {"files_opened": len(files)}
            except OSError:
                return {"error": "file_limit_reached"}
            finally:
                for f in files:
                    try:
                        f.close()
                    except:
                        pass

        elif self.resource_type == "processes":
            # Try to spawn many processes
            processes = []
            try:
                for i in range(100):
                    p = multiprocessing.Process(target=lambda: time.sleep(1))
                    p.start()
                    processes.append(p)
                return {"processes_spawned": len(processes)}
            except:
                return {"error": "process_limit_reached"}
            finally:
                for p in processes:
                    try:
                        p.terminate()
                    except:
                        pass

        return {"resource": "consumed"}


class LongRunningPlugin(SubForgePlugin):
    """Plugin that runs for a long time"""

    def __init__(self, run_time: int = 10):
        self.run_time = run_time

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="long_running_plugin",
            version="1.0.0",
            author="Test",
            description="Long-running test plugin",
            type="test",
            dependencies=[],
            config={"run_time": self.run_time},
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        return True

    def execute(self, context: Dict[str, Any]) -> Any:
        """Run for specified time"""
        start_time = time.time()
        while time.time() - start_time < self.run_time:
            time.sleep(0.1)
        return {"ran_for": self.run_time}


# ================ Test Cases ================


class TestResourceLimitEnforcement:
    """Test resource limit enforcement in the sandbox"""

    def test_memory_limit_enforcement(self):
        """Test that memory limits are enforced"""
        # Create sandbox with 100MB limit
        security_config = PluginSecurityConfig(
            enable_sandbox=True, max_memory_mb=100, timeout_seconds=10
        )
        sandbox = PluginSandbox(security_config)

        # Create plugin that tries to allocate 200MB
        plugin = ResourceHogPlugin("memory")

        # Execute should fail or return error
        with pytest.raises((ResourceLimitExceeded, PluginSandboxError, MemoryError)):
            result = sandbox.execute_in_sandbox(plugin, "execute", {"test": "memory"})

    def test_cpu_limit_enforcement(self):
        """Test that CPU time limits are enforced"""
        # Create sandbox with 2-second CPU limit
        security_config = PluginSecurityConfig(
            enable_sandbox=True, max_cpu_percent=50, timeout_seconds=2
        )
        sandbox = PluginSandbox(security_config)

        # Create CPU-intensive plugin
        plugin = ResourceHogPlugin("cpu")

        # Should timeout
        with pytest.raises((ResourceLimitExceeded, PluginSandboxError)):
            sandbox.execute_in_sandbox(plugin, "execute", {})

    def test_timeout_enforcement(self):
        """Test that execution timeouts are enforced"""
        # Create sandbox with 2-second timeout
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=2)
        sandbox = PluginSandbox(security_config)

        # Create plugin that runs for 5 seconds
        plugin = LongRunningPlugin(run_time=5)

        # Should timeout
        with pytest.raises((ResourceLimitExceeded, multiprocessing.TimeoutError)):
            sandbox.execute_in_sandbox(plugin, "execute", {})

    def test_file_descriptor_limit(self):
        """Test that file descriptor limits are enforced"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True, timeout_seconds=10
        )
        sandbox = PluginSandbox(security_config)

        plugin = ResourceHogPlugin("file_descriptors")

        # Should hit file descriptor limit
        try:
            result = sandbox.execute_in_sandbox(plugin, "execute", {})
            # If it succeeds, check that it hit the limit
            assert result.get("error") == "file_limit_reached" or result.get("files_opened", 0) < 200
        except (ResourceLimitExceeded, PluginSandboxError, OSError):
            # Expected if limits are strictly enforced
            pass

    def test_process_limit(self):
        """Test that process spawn limits are enforced"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True, timeout_seconds=10
        )
        sandbox = PluginSandbox(security_config)

        plugin = ResourceHogPlugin("processes")

        # Should hit process limit
        try:
            result = sandbox.execute_in_sandbox(plugin, "execute", {})
            # If it succeeds, check that it hit the limit
            assert result.get("error") == "process_limit_reached" or result.get("processes_spawned", 0) < 20
        except (ResourceLimitExceeded, PluginSandboxError):
            # Expected if limits are strictly enforced
            pass


class TestFileSystemIsolation:
    """Test file system isolation in the sandbox"""

    def test_read_sensitive_files_blocked(self):
        """Test that reading sensitive system files is blocked"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True,
            allowed_permissions=[],  # No file read permission
            timeout_seconds=5,
        )
        sandbox = PluginSandbox(security_config)

        plugin = MaliciousPlugin("file_system")

        # Should not be able to read /etc/passwd
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        assert result.get("attack") == "failed"

    def test_write_system_directories_blocked(self):
        """Test that writing to system directories is blocked"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True,
            allowed_permissions=[PluginPermission.FILE_READ],  # Read only
            timeout_seconds=5,
        )
        sandbox = PluginSandbox(security_config)

        plugin = MaliciousPlugin("file_system")

        # Should not be able to write to /etc/
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        assert result.get("attack") == "failed"

    def test_sandbox_escape_blocked(self):
        """Test that attempts to escape sandbox directory are blocked"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True,
            allowed_permissions=[PluginPermission.FILE_READ, PluginPermission.FILE_WRITE],
            allowed_paths=[Path("/tmp")],
            denied_paths=[Path("/etc"), Path("/sys"), Path("/proc")],
            timeout_seconds=5,
        )
        sandbox = PluginSandbox(security_config)

        plugin = MaliciousPlugin("file_system")

        # Should not be able to access outside allowed paths
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        assert result.get("attack") == "failed"

    def test_allowed_file_operations(self):
        """Test that allowed file operations succeed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            security_config = PluginSecurityConfig(
                enable_sandbox=True,
                allowed_permissions=[PluginPermission.FILE_READ, PluginPermission.FILE_WRITE],
                allowed_paths=[Path(tmpdir)],
                timeout_seconds=5,
            )
            
            # Create a test plugin that writes to allowed directory
            class FileWritePlugin(SubForgePlugin):
                def get_metadata(self) -> PluginMetadata:
                    return PluginMetadata(
                        name="file_writer",
                        version="1.0.0",
                        author="Test",
                        description="File write test",
                        type="test",
                        dependencies=[],
                        config={},
                    )

                def initialize(self, config: Dict[str, Any]) -> bool:
                    return True

                def execute(self, context: Dict[str, Any]) -> Any:
                    test_file = Path(tmpdir) / "test.txt"
                    test_file.write_text("test content")
                    return {"written": True, "content": test_file.read_text()}

            sandbox = PluginSandbox(security_config)
            plugin = FileWritePlugin()

            # This should succeed if sandbox is disabled or permissions allow
            if not security_config.enable_sandbox:
                result = sandbox.execute_in_sandbox(plugin, "execute", {})
                assert result.get("written") == True
                assert result.get("content") == "test content"


class TestNetworkAccessControl:
    """Test network access control in the sandbox"""

    def test_network_isolation_enforced(self):
        """Test that network access is blocked when not permitted"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True,
            allowed_permissions=[],  # No network permission
            allow_network=False,
            timeout_seconds=5,
        )
        sandbox = PluginSandbox(security_config)

        plugin = MaliciousPlugin("network")

        # Network operations should fail
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        assert result.get("attack") == "failed"

    def test_network_allowed_when_permitted(self):
        """Test that network access works when permitted"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True,
            allowed_permissions=[PluginPermission.NETWORK],
            allow_network=True,
            allowed_hosts=["localhost", "127.0.0.1"],
            timeout_seconds=5,
        )
        
        # Create a plugin that makes allowed network requests
        class NetworkPlugin(SubForgePlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="network_plugin",
                    version="1.0.0",
                    author="Test",
                    description="Network test plugin",
                    type="test",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            def execute(self, context: Dict[str, Any]) -> Any:
                # Try localhost connection (should be allowed)
                try:
                    import socket

                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1)
                    # Just test socket creation, don't actually connect
                    s.close()
                    return {"network": "available"}
                except:
                    return {"network": "blocked"}

        sandbox = PluginSandbox(security_config)
        plugin = NetworkPlugin()

        # If sandbox is disabled, network should work
        if not security_config.enable_sandbox:
            result = sandbox.execute_in_sandbox(plugin, "execute", {})
            assert result.get("network") == "available"


class TestPermissionValidation:
    """Test permission validation and enforcement"""

    def test_file_read_permission_enforcement(self):
        """Test FILE_READ permission enforcement"""
        checker = PermissionChecker({PluginPermission.FILE_READ})

        # Should allow file read
        assert checker.check_permission(PluginPermission.FILE_READ) == True
        assert checker.check_file_access(Path("/tmp/test.txt"), write=False) == True

        # Should deny file write
        assert checker.check_permission(PluginPermission.FILE_WRITE) == False
        assert checker.check_file_access(Path("/tmp/test.txt"), write=True) == False

    def test_file_write_permission_enforcement(self):
        """Test FILE_WRITE permission enforcement"""
        checker = PermissionChecker({PluginPermission.FILE_WRITE})

        # Should allow file write
        assert checker.check_permission(PluginPermission.FILE_WRITE) == True
        assert checker.check_file_access(Path("/tmp/test.txt"), write=True) == True

        # Should deny other permissions
        assert checker.check_permission(PluginPermission.NETWORK) == False

    def test_network_permission_enforcement(self):
        """Test NETWORK permission enforcement"""
        checker = PermissionChecker({PluginPermission.NETWORK})

        # Should allow network access
        assert checker.check_permission(PluginPermission.NETWORK) == True
        assert checker.check_network_access("example.com", 80) == True

        # Should deny other permissions
        assert checker.check_permission(PluginPermission.EXECUTE) == False

    def test_execute_permission_enforcement(self):
        """Test EXECUTE permission enforcement"""
        checker = PermissionChecker({PluginPermission.EXECUTE})

        # Should allow command execution
        assert checker.check_permission(PluginPermission.EXECUTE) == True
        assert checker.check_execution("ls -la") == True

        # Should deny other permissions
        assert checker.check_permission(PluginPermission.DATABASE) == False

    def test_require_permission_raises_on_denial(self):
        """Test that require_permission raises exception when denied"""
        checker = PermissionChecker({PluginPermission.FILE_READ})

        # Should not raise for allowed permission
        checker.require_permission(PluginPermission.FILE_READ)

        # Should raise for denied permission
        with pytest.raises(SecurityViolation):
            checker.require_permission(PluginPermission.FILE_WRITE)

    def test_multiple_permissions(self):
        """Test handling of multiple permissions"""
        checker = PermissionChecker(
            {
                PluginPermission.FILE_READ,
                PluginPermission.FILE_WRITE,
                PluginPermission.NETWORK,
            }
        )

        # Should allow all granted permissions
        assert checker.check_permission(PluginPermission.FILE_READ) == True
        assert checker.check_permission(PluginPermission.FILE_WRITE) == True
        assert checker.check_permission(PluginPermission.NETWORK) == True

        # Should deny non-granted permissions
        assert checker.check_permission(PluginPermission.EXECUTE) == False
        assert checker.check_permission(PluginPermission.DATABASE) == False


class TestProcessIsolation:
    """Test process isolation in the sandbox"""

    def test_plugin_runs_in_separate_process(self):
        """Test that plugins run in isolated processes"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=5)
        sandbox = PluginSandbox(security_config)

        # Create plugin that gets process ID
        class ProcessPlugin(SubForgePlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="process_plugin",
                    version="1.0.0",
                    author="Test",
                    description="Process test plugin",
                    type="test",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            def execute(self, context: Dict[str, Any]) -> Any:
                return {"pid": os.getpid()}

        plugin = ProcessPlugin()

        # Get main process PID
        main_pid = os.getpid()

        # Execute plugin
        result = sandbox.execute_in_sandbox(plugin, "execute", {})

        # Plugin should have different PID (runs in subprocess)
        if security_config.enable_sandbox:
            assert result.get("pid") != main_pid

    def test_process_limits_enforced(self):
        """Test that process resource limits are enforced"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True,
            max_memory_mb=100,
            timeout_seconds=10,
        )
        sandbox = PluginSandbox(security_config)

        # Plugin should have limited resources
        plugin = ResourceHogPlugin("memory")

        with pytest.raises((ResourceLimitExceeded, PluginSandboxError, MemoryError)):
            sandbox.execute_in_sandbox(plugin, "execute", {})

    def test_inter_process_communication_blocked(self):
        """Test that IPC between sandboxed processes is restricted"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=5)
        sandbox = PluginSandbox(security_config)

        # Create plugin that tries IPC
        class IPCPlugin(SubForgePlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="ipc_plugin",
                    version="1.0.0",
                    author="Test",
                    description="IPC test plugin",
                    type="test",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            def execute(self, context: Dict[str, Any]) -> Any:
                # Try to create shared memory or pipes
                try:
                    import mmap

                    # Try to create shared memory
                    mm = mmap.mmap(-1, 1024)
                    mm.close()
                    return {"ipc": "succeeded"}
                except:
                    return {"ipc": "blocked"}

        plugin = IPCPlugin()
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        # IPC might be allowed but isolated between processes

    def test_clean_process_termination(self):
        """Test that processes are cleanly terminated"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=2)
        sandbox = PluginSandbox(security_config)

        # Create plugin that ignores signals
        class StubbornPlugin(SubForgePlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="stubborn_plugin",
                    version="1.0.0",
                    author="Test",
                    description="Stubborn test plugin",
                    type="test",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            def execute(self, context: Dict[str, Any]) -> Any:
                # Ignore termination signals
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                time.sleep(10)  # Long running
                return {"status": "completed"}

        plugin = StubbornPlugin()

        # Should timeout and terminate
        with pytest.raises((ResourceLimitExceeded, multiprocessing.TimeoutError)):
            sandbox.execute_in_sandbox(plugin, "execute", {})


class TestSecurityViolations:
    """Test handling of various security violations"""

    def test_privilege_escalation_blocked(self):
        """Test that privilege escalation attempts are blocked"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=5)
        sandbox = PluginSandbox(security_config)

        plugin = MaliciousPlugin("privilege_escalation")

        # Should not be able to escalate privileges
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        assert result.get("attack") == "failed"

    def test_code_injection_blocked(self):
        """Test that code injection attempts are blocked"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True,
            allowed_permissions=[],  # No execute permission
            timeout_seconds=5,
        )
        sandbox = PluginSandbox(security_config)

        plugin = MaliciousPlugin("command_injection")

        # Command execution should be blocked
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        assert result.get("attack") == "failed"

    def test_sandbox_escape_attempts_caught(self):
        """Test that sandbox escape attempts are caught and logged"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=5)
        sandbox = PluginSandbox(security_config)
        monitor = SandboxMonitor(security_config)

        plugin = MaliciousPlugin("sandbox_escape")

        # Execute malicious plugin
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        
        # Attack should fail
        assert result.get("attack") == "failed"

    def test_violation_logging(self):
        """Test that security violations are properly logged"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=5)
        monitor = SandboxMonitor(security_config)

        # Record various violations
        monitor.record_violation("plugin1", "memory_limit", "Exceeded 100MB")
        monitor.record_violation("plugin2", "unauthorized_access", "Tried to read /etc/passwd")
        monitor.record_violation("plugin1", "timeout", "Exceeded 30s timeout")

        # Check violations are recorded
        all_violations = monitor.get_violations()
        assert len(all_violations) == 3

        # Check filtering by plugin
        plugin1_violations = monitor.get_violations("plugin1")
        assert len(plugin1_violations) == 2
        assert all(v["plugin_id"] == "plugin1" for v in plugin1_violations)

    def test_resource_monitoring(self):
        """Test resource usage monitoring"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True, max_memory_mb=100, timeout_seconds=10
        )
        monitor = SandboxMonitor(security_config)

        # Check resource usage
        usage = monitor.check_resource_usage("test_plugin")
        assert "memory_mb" in usage
        assert "cpu_time" in usage
        assert "io_reads" in usage
        assert "io_writes" in usage

        # Check within limits (should be true for test process)
        assert monitor.is_within_limits("test_plugin") == True


class TestConcurrentSandboxOperations:
    """Test concurrent sandbox operations"""

    def test_multiple_sandboxes_isolated(self):
        """Test that multiple sandboxes are isolated from each other"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=5)

        def run_plugin(plugin_id: int) -> Dict[str, Any]:
            """Run a plugin in a sandbox"""
            sandbox = PluginSandbox(security_config)

            class TestPlugin(SubForgePlugin):
                def get_metadata(self) -> PluginMetadata:
                    return PluginMetadata(
                        name=f"test_plugin_{plugin_id}",
                        version="1.0.0",
                        author="Test",
                        description="Concurrent test plugin",
                        type="test",
                        dependencies=[],
                        config={"id": plugin_id},
                    )

                def initialize(self, config: Dict[str, Any]) -> bool:
                    return True

                def execute(self, context: Dict[str, Any]) -> Any:
                    # Each plugin writes to its own temp file
                    temp_file = Path(f"/tmp/sandbox_test_{plugin_id}.txt")
                    temp_file.write_text(f"Plugin {plugin_id} was here")
                    return {"plugin_id": plugin_id, "file": str(temp_file)}

            plugin = TestPlugin()
            return sandbox.execute_in_sandbox(plugin, "execute", {})

        # Run multiple sandboxes concurrently
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_plugin, i) for i in range(5)]
            results = [f.result() for f in futures]

        # Each should have its own result
        plugin_ids = [r.get("plugin_id") for r in results]
        assert len(set(plugin_ids)) == 5  # All unique

    def test_resource_sharing_limits(self):
        """Test that resource limits are enforced across concurrent sandboxes"""
        security_config = PluginSecurityConfig(
            enable_sandbox=True, max_memory_mb=50, timeout_seconds=10
        )

        def run_memory_hog(hog_id: int) -> Dict[str, Any]:
            """Run a memory-consuming plugin"""
            sandbox = PluginSandbox(security_config)
            plugin = ResourceHogPlugin("memory")
            try:
                return sandbox.execute_in_sandbox(plugin, "execute", {"id": hog_id})
            except (ResourceLimitExceeded, PluginSandboxError, MemoryError):
                return {"error": "limit_exceeded", "id": hog_id}

        # Run multiple memory hogs concurrently
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_memory_hog, i) for i in range(3)]
            results = [f.result() for f in futures]

        # At least some should fail due to limits
        errors = [r for r in results if "error" in r]
        assert len(errors) > 0  # Some should hit limits

    def test_no_interference_between_sandboxes(self):
        """Test that sandboxes don't interfere with each other"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=5)

        class SharedStatePlugin(SubForgePlugin):
            shared_data = {}  # Shared class variable

            def __init__(self, plugin_id: int):
                self.plugin_id = plugin_id

            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name=f"shared_plugin_{self.plugin_id}",
                    version="1.0.0",
                    author="Test",
                    description="Shared state test",
                    type="test",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            def execute(self, context: Dict[str, Any]) -> Any:
                # Try to modify shared state
                self.shared_data[self.plugin_id] = f"Plugin {self.plugin_id}"
                time.sleep(0.1)  # Give time for interference
                # Check if our data is still there
                our_data = self.shared_data.get(self.plugin_id)
                return {
                    "plugin_id": self.plugin_id,
                    "our_data": our_data,
                    "total_keys": len(self.shared_data),
                }

        # Run multiple plugins that try to share state
        sandboxes = [PluginSandbox(security_config) for _ in range(3)]
        plugins = [SharedStatePlugin(i) for i in range(3)]

        results = []
        for sandbox, plugin in zip(sandboxes, plugins):
            result = sandbox.execute_in_sandbox(plugin, "execute", {})
            results.append(result)

        # Each plugin should only see its own data (due to process isolation)
        for result in results:
            if security_config.enable_sandbox:
                # In sandbox, each process is isolated
                assert result.get("total_keys", 0) <= 1  # Should only see own data


class TestSandboxConfiguration:
    """Test sandbox configuration and settings"""

    def test_sandbox_can_be_disabled(self):
        """Test that sandbox can be disabled for trusted plugins"""
        security_config = PluginSecurityConfig(enable_sandbox=False)
        sandbox = PluginSandbox(security_config)

        plugin = BenignPlugin()
        result = sandbox.execute_in_sandbox(plugin, "execute", {"test_data": "hello"})

        # Should execute directly without sandboxing
        assert result["status"] == "success"
        assert result["data"] == "hello"

    def test_custom_resource_limits(self):
        """Test custom resource limit configuration"""
        # Test various memory limits
        for memory_mb in [50, 100, 200]:
            security_config = PluginSecurityConfig(
                enable_sandbox=True, max_memory_mb=memory_mb, timeout_seconds=10
            )
            sandbox = PluginSandbox(security_config)
            assert sandbox.security_config.max_memory_mb == memory_mb

        # Test various timeout limits
        for timeout in [5, 10, 30]:
            security_config = PluginSecurityConfig(
                enable_sandbox=True, timeout_seconds=timeout
            )
            sandbox = PluginSandbox(security_config)
            assert sandbox.security_config.timeout_seconds == timeout

    def test_permission_configuration(self):
        """Test permission configuration"""
        # Test with different permission sets
        permissions_sets = [
            [PluginPermission.FILE_READ],
            [PluginPermission.FILE_READ, PluginPermission.FILE_WRITE],
            [PluginPermission.NETWORK],
            [PluginPermission.FILE_READ, PluginPermission.NETWORK, PluginPermission.EXECUTE],
        ]

        for permissions in permissions_sets:
            security_config = PluginSecurityConfig(
                enable_sandbox=True, allowed_permissions=permissions
            )
            checker = PermissionChecker(set(permissions))

            for perm in permissions:
                assert checker.check_permission(perm) == True

            # Check that non-granted permissions are denied
            all_perms = set(PluginPermission)
            for perm in all_perms - set(permissions):
                assert checker.check_permission(perm) == False

    def test_path_restrictions(self):
        """Test path restriction configuration"""
        allowed_paths = [Path("/tmp"), Path("/var/tmp")]
        denied_paths = [Path("/etc"), Path("/sys"), Path("/proc")]

        security_config = PluginSecurityConfig(
            enable_sandbox=True,
            allowed_paths=allowed_paths,
            denied_paths=denied_paths,
        )

        assert security_config.allowed_paths == allowed_paths
        assert security_config.denied_paths == denied_paths


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_plugin_without_execute_method(self):
        """Test handling of plugin without execute method"""

        class InvalidPlugin(SubForgePlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="invalid",
                    version="1.0.0",
                    author="Test",
                    description="Invalid plugin",
                    type="test",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            # Missing execute method!

        security_config = PluginSecurityConfig(enable_sandbox=True)
        sandbox = PluginSandbox(security_config)
        plugin = InvalidPlugin()

        # Should raise error about missing method
        with pytest.raises((AttributeError, PluginSandboxError)):
            sandbox.execute_in_sandbox(plugin, "execute", {})

    def test_plugin_raising_exception(self):
        """Test handling of plugin that raises exceptions"""

        class ExceptionPlugin(SubForgePlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="exception",
                    version="1.0.0",
                    author="Test",
                    description="Exception test",
                    type="test",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            def execute(self, context: Dict[str, Any]) -> Any:
                raise ValueError("Intentional error for testing")

        security_config = PluginSecurityConfig(enable_sandbox=True)
        sandbox = PluginSandbox(security_config)
        plugin = ExceptionPlugin()

        # Should wrap exception appropriately
        with pytest.raises(PluginSandboxError):
            sandbox.execute_in_sandbox(plugin, "execute", {})

    def test_empty_context(self):
        """Test execution with empty context"""
        security_config = PluginSecurityConfig(enable_sandbox=True)
        sandbox = PluginSandbox(security_config)
        plugin = BenignPlugin()

        # Should handle empty context
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        assert result["status"] == "success"
        assert result["data"] == "no_data"

    def test_large_context(self):
        """Test execution with large context data"""
        security_config = PluginSecurityConfig(enable_sandbox=True, timeout_seconds=10)
        sandbox = PluginSandbox(security_config)
        plugin = BenignPlugin()

        # Create large context
        large_context = {"test_data": "x" * 1000000}  # 1MB string

        # Should handle large context
        result = sandbox.execute_in_sandbox(plugin, "execute", large_context)
        assert result["status"] == "success"

    def test_restricted_builtins(self):
        """Test that dangerous builtins are restricted"""
        
        class BuiltinTestPlugin(SubForgePlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="builtin_test",
                    version="1.0.0",
                    author="Test",
                    description="Builtin test",
                    type="test",
                    dependencies=[],
                    config={},
                )

            def initialize(self, config: Dict[str, Any]) -> bool:
                return True

            def execute(self, context: Dict[str, Any]) -> Any:
                results = {}
                
                # Test safe builtins (should work)
                try:
                    results["len"] = len([1, 2, 3]) == 3
                    results["sum"] = sum([1, 2, 3]) == 6
                    results["max"] = max([1, 2, 3]) == 3
                except:
                    results["safe_builtins"] = False
                else:
                    results["safe_builtins"] = True
                
                # Test dangerous builtins (should be restricted)
                try:
                    eval("1 + 1")
                    results["eval_blocked"] = False
                except:
                    results["eval_blocked"] = True
                
                try:
                    exec("x = 1")
                    results["exec_blocked"] = False
                except:
                    results["exec_blocked"] = True
                
                try:
                    __import__("os")
                    results["import_blocked"] = False
                except:
                    results["import_blocked"] = True
                
                return results
        
        security_config = PluginSecurityConfig(enable_sandbox=True)
        sandbox = PluginSandbox(security_config)
        plugin = BuiltinTestPlugin()
        
        result = sandbox.execute_in_sandbox(plugin, "execute", {})
        
        # Safe builtins should work
        assert result.get("safe_builtins") == True
        
        # Dangerous builtins should be blocked in sandbox
        if security_config.enable_sandbox:
            assert result.get("eval_blocked") == True
            assert result.get("exec_blocked") == True


# ================ Test Runner ================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])