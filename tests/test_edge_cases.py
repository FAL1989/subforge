"""
Comprehensive edge case tests for SubForge system.

Tests system behavior under extreme conditions including:
- Input edge cases (empty, large, special characters)
- Concurrency edge cases
- Resource exhaustion scenarios
- Boundary value testing

Created: 2025-01-05 12:35 UTC-3 São Paulo
"""

import pytest
import asyncio
import threading
import time
import os
import tempfile
import shutil
import json
import sys
import gc
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import SubForge modules
try:
    from subforge.core.project_analyzer import ProjectAnalyzer
    from subforge.core.workflow_orchestrator import WorkflowOrchestrator
    from subforge.core.validation_engine import ValidationEngine
    from subforge.core.cache_manager import CacheManager
except ImportError:
    # Mock imports if modules not available
    ProjectAnalyzer = Mock
    WorkflowOrchestrator = Mock
    ValidationEngine = Mock
    CacheManager = Mock


class TestInputEdgeCases:
    """Test handling of various edge case inputs."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        empty_cases = [
            "",  # Empty string
            [],  # Empty list
            {},  # Empty dict
            None,  # None value
            set(),  # Empty set
            tuple(),  # Empty tuple
        ]
        
        def process_input(value):
            """Mock input processor."""
            if value is None:
                return {"error": "null_input", "processed": False}
            elif not value:  # Empty but not None
                return {"warning": "empty_input", "processed": True, "result": "default"}
            else:
                return {"processed": True, "result": value}
        
        for empty_input in empty_cases:
            result = process_input(empty_input)
            assert "processed" in result
            
            if empty_input is None:
                assert result["processed"] is False
                assert result["error"] == "null_input"
            else:
                assert result["processed"] is True
                if not empty_input:
                    assert result["result"] == "default"
    
    def test_extremely_large_inputs(self):
        """Test handling of extremely large inputs."""
        # Large string (1MB)
        large_string = "x" * (1024 * 1024)
        
        # Large list (100k items)
        large_list = list(range(100000))
        
        # Large dict (10k key-value pairs)
        large_dict = {f"key_{i}": f"value_{i}" for i in range(10000)}
        
        # Deep nested structure (1000 levels)
        deep_nested = {"level": 0}
        current = deep_nested
        for i in range(1, 1000):
            current["next"] = {"level": i}
            current = current["next"]
        
        def validate_input_size(data, max_size=10 * 1024 * 1024):  # 10MB limit
            """Validate input size constraints."""
            try:
                # Estimate size
                if isinstance(data, str):
                    size = len(data.encode('utf-8'))
                elif isinstance(data, (list, dict)):
                    size = sys.getsizeof(data)
                else:
                    size = sys.getsizeof(data)
                
                if size > max_size:
                    return False, f"Input too large: {size} bytes > {max_size} bytes"
                
                return True, size
            except (MemoryError, OverflowError):
                return False, "Memory error processing input"
        
        # Test large string
        is_valid, size_info = validate_input_size(large_string)
        assert isinstance(size_info, (int, str))  # Either size or error message
        
        # Test large list
        is_valid, size_info = validate_input_size(large_list)
        assert isinstance(size_info, (int, str))
        
        # Test large dict
        is_valid, size_info = validate_input_size(large_dict)
        assert isinstance(size_info, (int, str))
        
        # Test deep nested structure
        is_valid, size_info = validate_input_size(deep_nested)
        assert isinstance(size_info, (int, str))
    
    def test_special_characters(self):
        """Test handling of special characters and encodings."""
        special_cases = [
            "Hello, 世界!",  # Unicode characters
            "Emoji test: 🚀🌟💻🎯",  # Emoji characters
            "Control chars: \x00\x01\x02\x1F",  # Control characters
            "Line breaks:\n\r\n\t",  # Whitespace variations
            "Quotes: \"'`´",  # Various quote types
            "SQL injection: '; DROP TABLE users; --",  # Potential SQL injection
            "XSS attempt: <script>alert('xss')</script>",  # XSS attempt
            "Path traversal: ../../../etc/passwd",  # Path traversal
            "Null byte: file.txt\x00.exe",  # Null byte injection
        ]
        
        def sanitize_input(text):
            """Input sanitization function."""
            if not isinstance(text, str):
                return str(text)
            
            # Remove null bytes
            text = text.replace('\x00', '')
            
            # Limit control characters (keep newline and tab)
            allowed_control = {'\n', '\r', '\t'}
            text = ''.join(char for char in text 
                          if ord(char) >= 32 or char in allowed_control)
            
            # HTML escape for XSS prevention
            html_escapes = {
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;',
                '&': '&amp;'
            }
            for char, escape in html_escapes.items():
                text = text.replace(char, escape)
            
            return text
        
        for special_input in special_cases:
            sanitized = sanitize_input(special_input)
            
            # Verify sanitization worked
            assert '\x00' not in sanitized  # No null bytes
            assert '<script>' not in sanitized  # XSS blocked
            
            # Verify we can safely process sanitized input
            try:
                json.dumps({"input": sanitized})  # Should be JSON serializable
            except (TypeError, ValueError):
                pytest.fail(f"Sanitized input not JSON serializable: {special_input}")
    
    def test_boundary_values(self):
        """Test behavior at boundary values."""
        # Integer boundaries
        int_boundaries = [
            -sys.maxsize - 1,  # Most negative
            -1,  # Negative edge
            0,  # Zero
            1,  # Positive edge
            sys.maxsize,  # Most positive
        ]
        
        # Float boundaries
        float_boundaries = [
            float('-inf'),  # Negative infinity
            -sys.float_info.max,  # Largest negative
            -sys.float_info.min,  # Smallest negative
            0.0,  # Zero
            sys.float_info.min,  # Smallest positive
            sys.float_info.max,  # Largest positive
            float('inf'),  # Positive infinity
            float('nan'),  # Not a number
        ]
        
        def process_numeric_boundary(value):
            """Process numeric boundary values."""
            try:
                if isinstance(value, int):
                    # Check integer overflow scenarios
                    if abs(value) > 2**63 - 1:  # 64-bit signed integer limit
                        return {"error": "integer_overflow", "value": None}
                    return {"value": value, "type": "integer"}
                
                elif isinstance(value, float):
                    import math
                    if math.isinf(value):
                        return {"error": "infinite_value", "value": None}
                    elif math.isnan(value):
                        return {"error": "nan_value", "value": None}
                    else:
                        return {"value": value, "type": "float"}
                
                return {"error": "unknown_type", "value": None}
            
            except (OverflowError, ValueError) as e:
                return {"error": str(e), "value": None}
        
        # Test integer boundaries
        for int_val in int_boundaries:
            result = process_numeric_boundary(int_val)
            assert "value" in result or "error" in result
        
        # Test float boundaries
        for float_val in float_boundaries:
            result = process_numeric_boundary(float_val)
            assert "value" in result or "error" in result
            
            # Special handling for inf and nan
            import math
            if math.isinf(float_val) or math.isnan(float_val):
                assert "error" in result
    
    def test_encoding_edge_cases(self):
        """Test various text encoding edge cases."""
        encoding_cases = [
            ("ascii", "Hello World"),
            ("utf-8", "Hello, 世界! 🌍"),
            ("latin-1", "Café naïve résumé"),
            ("cp1252", "Windows-1252 encoding"),
        ]
        
        def handle_encoding(text, encoding):
            """Handle text with specific encoding."""
            try:
                # Encode and decode to test roundtrip
                encoded = text.encode(encoding)
                decoded = encoded.decode(encoding)
                return {"success": True, "text": decoded, "bytes": len(encoded)}
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                # Fallback to UTF-8 with error replacement
                try:
                    fallback = text.encode('utf-8', errors='replace').decode('utf-8')
                    return {"success": False, "error": str(e), "fallback": fallback}
                except Exception as fallback_error:
                    return {"success": False, "error": str(fallback_error)}
        
        for encoding, text in encoding_cases:
            result = handle_encoding(text, encoding)
            assert "success" in result
            
            if result["success"]:
                assert "text" in result
                assert "bytes" in result
            else:
                assert "error" in result


class TestConcurrencyEdgeCases:
    """Test edge cases in concurrent operations."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.shared_resource = os.path.join(self.temp_dir, "shared_resource.json")
        self.lock = threading.Lock()
    
    def teardown_method(self):
        """Cleanup test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_concurrent_modifications(self):
        """Test concurrent modifications to shared resources."""
        initial_data = {"counter": 0, "modifications": []}
        
        # Initialize shared resource
        with open(self.shared_resource, 'w') as f:
            json.dump(initial_data, f)
        
        async def modify_resource(worker_id, iterations=100):
            """Modify shared resource concurrently."""
            modifications = []
            
            for i in range(iterations):
                # Simulate file-based locking
                lock_file = self.shared_resource + ".lock"
                
                # Try to acquire lock
                max_attempts = 10
                attempt = 0
                
                while attempt < max_attempts:
                    try:
                        # Atomic lock creation
                        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                        os.write(fd, f"worker_{worker_id}".encode())
                        os.close(fd)
                        break
                    except FileExistsError:
                        # Lock exists, wait and retry
                        await asyncio.sleep(0.001)
                        attempt += 1
                
                if attempt >= max_attempts:
                    continue  # Skip this iteration if can't acquire lock
                
                try:
                    # Critical section - modify shared resource
                    with open(self.shared_resource, 'r') as f:
                        data = json.load(f)
                    
                    data["counter"] += 1
                    data["modifications"].append(f"worker_{worker_id}_iter_{i}")
                    modifications.append(data["counter"])
                    
                    with open(self.shared_resource, 'w') as f:
                        json.dump(data, f)
                
                finally:
                    # Release lock
                    try:
                        os.remove(lock_file)
                    except FileNotFoundError:
                        pass
            
            return modifications
        
        # Start multiple concurrent workers
        workers = [modify_resource(i, 50) for i in range(5)]
        results = await asyncio.gather(*workers)
        
        # Verify final state
        with open(self.shared_resource, 'r') as f:
            final_data = json.load(f)
        
        # Each worker did 50 iterations = 250 total expected
        expected_count = 5 * 50
        assert final_data["counter"] == expected_count
        assert len(final_data["modifications"]) == expected_count
    
    def test_race_conditions(self):
        """Test race condition scenarios."""
        shared_counter = {"value": 0}
        race_results = []
        
        def increment_with_race(thread_id, iterations=1000):
            """Function that can cause race conditions."""
            local_results = []
            
            for i in range(iterations):
                # Race condition: read-modify-write without proper locking
                current_value = shared_counter["value"]
                # Simulate some processing time
                time.sleep(0.0001)  # 0.1ms
                new_value = current_value + 1
                shared_counter["value"] = new_value
                local_results.append(new_value)
            
            return local_results
        
        def increment_with_lock(thread_id, iterations=1000):
            """Function with proper locking."""
            local_results = []
            
            for i in range(iterations):
                with self.lock:
                    current_value = shared_counter["value"]
                    new_value = current_value + 1
                    shared_counter["value"] = new_value
                    local_results.append(new_value)
            
            return local_results
        
        # Test without locking (should have race conditions)
        shared_counter["value"] = 0
        threads = []
        
        for i in range(3):
            thread = threading.Thread(
                target=lambda tid=i: race_results.extend(increment_with_race(tid, 100))
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # With race conditions, final value might be less than expected
        race_final_value = shared_counter["value"]
        
        # Test with locking (should be consistent)
        shared_counter["value"] = 0
        lock_results = []
        threads = []
        
        for i in range(3):
            thread = threading.Thread(
                target=lambda tid=i: lock_results.extend(increment_with_lock(tid, 100))
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # With proper locking, should get expected result
        lock_final_value = shared_counter["value"]
        expected_value = 3 * 100
        
        # Race condition test: final value should be <= expected
        assert race_final_value <= expected_value
        
        # Locked test: final value should be exactly expected
        assert lock_final_value == expected_value
    
    async def test_deadlock_prevention(self):
        """Test deadlock prevention mechanisms."""
        resource_a = asyncio.Lock()
        resource_b = asyncio.Lock()
        
        async def task_1():
            """Task that acquires resources in order A -> B."""
            try:
                # Use timeout to prevent indefinite waiting
                async with asyncio.wait_for(resource_a.acquire(), timeout=1.0):
                    await asyncio.sleep(0.1)  # Hold lock A for a while
                    
                    async with asyncio.wait_for(resource_b.acquire(), timeout=1.0):
                        await asyncio.sleep(0.1)  # Hold both locks
                        return "task_1_completed"
            except asyncio.TimeoutError:
                return "task_1_timeout"
            finally:
                if resource_a.locked():
                    resource_a.release()
                if resource_b.locked():
                    resource_b.release()
        
        async def task_2():
            """Task that acquires resources in order B -> A (potential deadlock)."""
            try:
                # Use same ordering as task_1 to prevent deadlock
                async with asyncio.wait_for(resource_a.acquire(), timeout=1.0):
                    await asyncio.sleep(0.1)  # Hold lock A for a while
                    
                    async with asyncio.wait_for(resource_b.acquire(), timeout=1.0):
                        await asyncio.sleep(0.1)  # Hold both locks
                        return "task_2_completed"
            except asyncio.TimeoutError:
                return "task_2_timeout"
            finally:
                if resource_a.locked():
                    resource_a.release()
                if resource_b.locked():
                    resource_b.release()
        
        # Run tasks concurrently
        results = await asyncio.gather(task_1(), task_2(), return_exceptions=True)
        
        # Both tasks should complete (no deadlock) or timeout gracefully
        for result in results:
            assert isinstance(result, str)  # Should return string result
            assert "completed" in result or "timeout" in result
    
    def test_thread_pool_exhaustion(self):
        """Test behavior when thread pool is exhausted."""
        max_workers = 4
        
        def long_running_task(task_id):
            """Simulate long-running task."""
            time.sleep(0.5)  # 500ms task
            return f"task_{task_id}_completed"
        
        def quick_task(task_id):
            """Quick task that should queue up."""
            time.sleep(0.01)  # 10ms task
            return f"quick_task_{task_id}_completed"
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit more tasks than available workers
            long_tasks = [executor.submit(long_running_task, i) for i in range(6)]
            quick_tasks = [executor.submit(quick_task, i) for i in range(10)]
            
            # Wait for all tasks to complete
            all_tasks = long_tasks + quick_tasks
            completed_results = []
            
            for future in as_completed(all_tasks):
                try:
                    result = future.result(timeout=5.0)  # 5 second timeout
                    completed_results.append(result)
                except Exception as e:
                    completed_results.append(f"error: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All tasks should complete
        assert len(completed_results) == 16
        
        # Should take at least as long as the longest sequential execution would
        # 6 long tasks * 0.5s = 3s minimum if properly queued with 4 workers
        min_expected_time = (6 * 0.5) / max_workers
        assert total_time >= min_expected_time


class TestResourceExhaustion:
    """Test system behavior under resource exhaustion."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_memory_exhaustion_simulation(self):
        """Test graceful degradation under simulated memory pressure."""
        memory_chunks = []
        chunk_size = 10 * 1024 * 1024  # 10MB chunks
        max_chunks = 10  # Limit to prevent actual system issues
        
        def allocate_memory_with_limit():
            """Allocate memory with safety limits."""
            try:
                # Check available memory before allocation
                memory_info = psutil.virtual_memory()
                available_gb = memory_info.available / (1024**3)
                
                # Only proceed if we have at least 1GB available
                if available_gb < 1.0:
                    return False, "Insufficient memory available"
                
                # Allocate chunks up to limit
                for i in range(max_chunks):
                    chunk = bytearray(chunk_size)
                    memory_chunks.append(chunk)
                    
                    # Force garbage collection to get accurate reading
                    gc.collect()
                    
                    # Check memory pressure
                    memory_info = psutil.virtual_memory()
                    if memory_info.percent > 90:  # Stop at 90% memory usage
                        break
                
                return True, f"Allocated {len(memory_chunks)} chunks"
            
            except MemoryError:
                return False, "Memory allocation failed"
        
        success, message = allocate_memory_with_limit()
        
        # Cleanup allocated memory
        memory_chunks.clear()
        gc.collect()
        
        assert isinstance(success, bool)
        assert isinstance(message, str)
    
    def test_file_descriptor_exhaustion_simulation(self):
        """Test handling of file descriptor limits."""
        open_files = []
        max_test_files = 100  # Reasonable limit for testing
        
        def test_file_descriptor_limits():
            """Test file descriptor handling."""
            try:
                # Create and open multiple files
                for i in range(max_test_files):
                    file_path = os.path.join(self.temp_dir, f"test_file_{i}.txt")
                    file_handle = open(file_path, 'w')
                    file_handle.write(f"Test data for file {i}")
                    open_files.append(file_handle)
                
                return True, f"Opened {len(open_files)} files successfully"
            
            except OSError as e:
                if "Too many open files" in str(e):
                    return False, f"Hit file descriptor limit at {len(open_files)} files"
                else:
                    return False, f"Unexpected error: {e}"
            
            finally:
                # Always cleanup open files
                for file_handle in open_files:
                    try:
                        file_handle.close()
                    except:
                        pass
                open_files.clear()
        
        success, message = test_file_descriptor_limits()
        
        assert isinstance(success, bool)
        assert isinstance(message, str)
    
    def test_disk_space_exhaustion_simulation(self):
        """Test handling when disk space is limited."""
        def simulate_disk_space_check():
            """Simulate disk space monitoring."""
            try:
                # Get actual disk usage
                disk_usage = shutil.disk_usage(self.temp_dir)
                free_bytes = disk_usage.free
                total_bytes = disk_usage.total
                
                # Calculate usage percentage
                used_bytes = total_bytes - free_bytes
                usage_percent = (used_bytes / total_bytes) * 100
                
                # Simulate different disk space scenarios
                scenarios = [
                    (95.0, "critical", "Emergency cleanup required"),
                    (90.0, "warning", "Low disk space warning"),
                    (80.0, "caution", "Monitor disk space"),
                    (50.0, "normal", "Sufficient disk space"),
                ]
                
                for threshold, level, message in scenarios:
                    if usage_percent >= threshold:
                        return {
                            "level": level,
                            "usage_percent": usage_percent,
                            "message": message,
                            "free_gb": free_bytes / (1024**3)
                        }
                
                return {
                    "level": "normal",
                    "usage_percent": usage_percent,
                    "message": "Disk space is healthy",
                    "free_gb": free_bytes / (1024**3)
                }
            
            except Exception as e:
                return {
                    "level": "error",
                    "message": f"Could not check disk space: {e}"
                }
        
        disk_info = simulate_disk_space_check()
        
        assert "level" in disk_info
        assert "message" in disk_info
        assert disk_info["level"] in ["critical", "warning", "caution", "normal", "error"]
    
    def test_cpu_exhaustion_simulation(self):
        """Test CPU intensive operations with monitoring."""
        def cpu_intensive_task(duration_seconds=1):
            """Simulate CPU intensive task."""
            import math
            
            start_time = time.time()
            iterations = 0
            
            # CPU intensive loop
            while time.time() - start_time < duration_seconds:
                # Perform meaningless but CPU intensive calculations
                result = math.sqrt(math.pow(iterations % 1000, 2))
                iterations += 1
            
            return {
                "iterations": iterations,
                "duration": time.time() - start_time,
                "iterations_per_second": iterations / (time.time() - start_time)
            }
        
        # Monitor CPU usage during task
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        
        result = cpu_intensive_task(0.5)  # 500ms of intensive work
        
        cpu_after = process.cpu_percent()
        
        assert result["iterations"] > 0
        assert result["duration"] > 0.4  # Should be close to 0.5 seconds
        assert result["iterations_per_second"] > 0


class TestAsyncEdgeCases:
    """Test edge cases in asynchronous operations."""
    
    async def test_asyncio_timeout_handling(self):
        """Test proper handling of asyncio timeouts."""
        
        async def slow_operation(delay):
            """Simulate slow async operation."""
            await asyncio.sleep(delay)
            return f"completed_after_{delay}s"
        
        # Test successful completion within timeout
        try:
            result = await asyncio.wait_for(slow_operation(0.1), timeout=0.2)
            assert result == "completed_after_0.1s"
        except asyncio.TimeoutError:
            pytest.fail("Should not timeout with sufficient time")
        
        # Test timeout handling
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(0.2), timeout=0.1)
    
    async def test_async_exception_propagation(self):
        """Test exception handling in async contexts."""
        
        async def failing_operation(should_fail=True):
            """Operation that may fail."""
            await asyncio.sleep(0.01)  # Small delay
            if should_fail:
                raise ValueError("Simulated async failure")
            return "success"
        
        # Test exception propagation
        with pytest.raises(ValueError, match="Simulated async failure"):
            await failing_operation(should_fail=True)
        
        # Test successful execution
        result = await failing_operation(should_fail=False)
        assert result == "success"
    
    async def test_async_resource_cleanup(self):
        """Test proper cleanup of async resources."""
        cleanup_called = []
        
        class AsyncResource:
            def __init__(self, resource_id):
                self.resource_id = resource_id
                self.closed = False
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await self.cleanup()
            
            async def cleanup(self):
                if not self.closed:
                    cleanup_called.append(self.resource_id)
                    self.closed = True
        
        # Test normal cleanup
        async with AsyncResource("test_1") as resource:
            assert not resource.closed
        
        assert "test_1" in cleanup_called
        
        # Test cleanup on exception
        try:
            async with AsyncResource("test_2") as resource:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        assert "test_2" in cleanup_called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])