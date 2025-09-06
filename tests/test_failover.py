"""
Comprehensive failover and resilience tests for SubForge system.

Tests system resilience including:
- Graceful degradation under failure
- Circuit breaker patterns
- Retry mechanisms with backoff
- Service discovery and failover

Created: 2025-01-05 12:40 UTC-3 São Paulo
"""

import pytest
import asyncio
import time
import random
import json
import tempfile
import os
import shutil
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from contextlib import asynccontextmanager

# Import SubForge modules
try:
    from subforge.core.project_analyzer import ProjectAnalyzer
    from subforge.core.workflow_orchestrator import WorkflowOrchestrator
    from subforge.core.validation_engine import ValidationEngine
except ImportError:
    # Mock imports if modules not available
    ProjectAnalyzer = Mock
    WorkflowOrchestrator = Mock
    ValidationEngine = Mock


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3
    timeout: float = 30.0


class CircuitBreaker:
    """Circuit breaker implementation for testing."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.metrics = {"calls": 0, "failures": 0, "timeouts": 0}
    
    async def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker."""
        self.metrics["calls"] += 1
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time < self.config.recovery_timeout:
                raise Exception("Circuit breaker is OPEN - fast failing")
            else:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs), 
                    timeout=self.config.timeout
                )
            else:
                result = func(*args, **kwargs)
            
            # Success handling
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            
            return result
            
        except asyncio.TimeoutError:
            self.metrics["timeouts"] += 1
            self._record_failure()
            raise
            
        except Exception as e:
            self.metrics["failures"] += 1
            self._record_failure()
            raise
    
    def _record_failure(self):
        """Record a failure and update circuit state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN


class RetryPolicy:
    """Retry policy with exponential backoff and jitter."""
    
    def __init__(self, max_retries=3, base_delay=1.0, max_delay=60.0, jitter=True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
    
    async def execute(self, func, *args, **kwargs):
        """Execute function with retry policy."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                
                # Add jitter to prevent thundering herd
                if self.jitter:
                    delay *= (0.5 + random.random() * 0.5)
                
                await asyncio.sleep(delay)
        
        raise last_exception


class ServiceRegistry:
    """Service registry for failover testing."""
    
    def __init__(self):
        self.services: Dict[str, List[Dict]] = {}
        self.health_checks: Dict[str, bool] = {}
    
    def register_service(self, name: str, endpoint: str, metadata: Dict = None):
        """Register a service endpoint."""
        if name not in self.services:
            self.services[name] = []
        
        service_info = {
            "endpoint": endpoint,
            "metadata": metadata or {},
            "registered_at": time.time(),
            "health_check_failures": 0
        }
        
        self.services[name].append(service_info)
        self.health_checks[endpoint] = True
    
    def get_healthy_endpoints(self, service_name: str) -> List[str]:
        """Get list of healthy endpoints for a service."""
        if service_name not in self.services:
            return []
        
        healthy_endpoints = []
        for service in self.services[service_name]:
            endpoint = service["endpoint"]
            if self.health_checks.get(endpoint, False):
                healthy_endpoints.append(endpoint)
        
        return healthy_endpoints
    
    def mark_unhealthy(self, endpoint: str):
        """Mark an endpoint as unhealthy."""
        self.health_checks[endpoint] = False
    
    def mark_healthy(self, endpoint: str):
        """Mark an endpoint as healthy."""
        self.health_checks[endpoint] = True


class TestGracefulDegradation:
    """Test graceful degradation under various failure scenarios."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.service_registry = ServiceRegistry()
    
    def teardown_method(self):
        """Cleanup test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_degraded_mode_activation(self):
        """Test activation of degraded mode when critical services fail."""
        
        class SystemManager:
            def __init__(self):
                self.mode = "normal"
                self.available_features = {
                    "advanced_analysis": True,
                    "real_time_monitoring": True,
                    "auto_optimization": True,
                    "basic_functionality": True,
                }
                self.service_status = {
                    "database": True,
                    "cache": True,
                    "analytics": True,
                    "monitoring": True,
                }
            
            def check_system_health(self):
                """Check overall system health and adjust mode."""
                critical_services = ["database"]
                important_services = ["cache", "analytics"]
                
                # Check critical services
                critical_failures = [
                    service for service in critical_services
                    if not self.service_status.get(service, False)
                ]
                
                # Check important services
                important_failures = [
                    service for service in important_services
                    if not self.service_status.get(service, False)
                ]
                
                if critical_failures:
                    self.mode = "emergency"
                    self.available_features = {"basic_functionality": True}
                elif len(important_failures) >= 2:
                    self.mode = "degraded"
                    self.available_features = {
                        "basic_functionality": True,
                        "real_time_monitoring": True,
                    }
                elif important_failures:
                    self.mode = "limited"
                    self.available_features = {
                        "basic_functionality": True,
                        "real_time_monitoring": True,
                        "advanced_analysis": True,
                    }
                else:
                    self.mode = "normal"
                    self.available_features = {
                        "advanced_analysis": True,
                        "real_time_monitoring": True,
                        "auto_optimization": True,
                        "basic_functionality": True,
                    }
                
                return self.mode
        
        system = SystemManager()
        
        # Test normal mode
        assert system.mode == "normal"
        assert system.check_system_health() == "normal"
        assert system.available_features["advanced_analysis"] is True
        
        # Simulate cache failure
        system.service_status["cache"] = False
        assert system.check_system_health() == "limited"
        assert system.available_features["advanced_analysis"] is True
        assert system.available_features["auto_optimization"] is False
        
        # Simulate additional analytics failure
        system.service_status["analytics"] = False
        assert system.check_system_health() == "degraded"
        assert system.available_features["advanced_analysis"] is False
        
        # Simulate critical database failure
        system.service_status["database"] = False
        assert system.check_system_health() == "emergency"
        assert len(system.available_features) == 1
        assert system.available_features["basic_functionality"] is True
    
    def test_feature_toggling(self):
        """Test dynamic feature toggling based on system state."""
        
        class FeatureManager:
            def __init__(self):
                self.features = {
                    "ai_analysis": {"enabled": True, "cpu_intensive": True},
                    "real_time_sync": {"enabled": True, "network_intensive": True},
                    "batch_processing": {"enabled": True, "memory_intensive": True},
                    "basic_crud": {"enabled": True, "essential": True},
                    "notifications": {"enabled": True, "optional": True},
                }
                self.system_resources = {
                    "cpu_usage": 30,
                    "memory_usage": 40,
                    "network_latency": 100,
                    "disk_io": 20,
                }
            
            def update_system_resources(self, resources):
                """Update current system resource usage."""
                self.system_resources.update(resources)
                self.adjust_features()
            
            def adjust_features(self):
                """Adjust features based on system resources."""
                cpu_threshold = 80
                memory_threshold = 85
                network_threshold = 1000  # ms
                
                # Disable CPU intensive features if CPU is high
                if self.system_resources["cpu_usage"] > cpu_threshold:
                    for feature, config in self.features.items():
                        if config.get("cpu_intensive", False):
                            self.features[feature]["enabled"] = False
                
                # Disable memory intensive features if memory is high
                if self.system_resources["memory_usage"] > memory_threshold:
                    for feature, config in self.features.items():
                        if config.get("memory_intensive", False):
                            self.features[feature]["enabled"] = False
                
                # Disable network intensive features if network is slow
                if self.system_resources["network_latency"] > network_threshold:
                    for feature, config in self.features.items():
                        if config.get("network_intensive", False):
                            self.features[feature]["enabled"] = False
                
                # Always keep essential features enabled
                for feature, config in self.features.items():
                    if config.get("essential", False):
                        self.features[feature]["enabled"] = True
        
        feature_manager = FeatureManager()
        
        # Test normal operation
        assert feature_manager.features["ai_analysis"]["enabled"] is True
        assert feature_manager.features["basic_crud"]["enabled"] is True
        
        # Test high CPU usage
        feature_manager.update_system_resources({"cpu_usage": 90})
        assert feature_manager.features["ai_analysis"]["enabled"] is False
        assert feature_manager.features["basic_crud"]["enabled"] is True
        
        # Reset and test high memory usage
        feature_manager.features["ai_analysis"]["enabled"] = True
        feature_manager.features["batch_processing"]["enabled"] = True
        feature_manager.update_system_resources({"cpu_usage": 30, "memory_usage": 90})
        
        assert feature_manager.features["batch_processing"]["enabled"] is False
        assert feature_manager.features["basic_crud"]["enabled"] is True
        
        # Test high network latency
        feature_manager.update_system_resources({"memory_usage": 40, "network_latency": 2000})
        assert feature_manager.features["real_time_sync"]["enabled"] is False
        assert feature_manager.features["basic_crud"]["enabled"] is True


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,  # Short timeout for testing
            success_threshold=2
        )
        self.circuit_breaker = CircuitBreaker(self.config)
    
    async def test_circuit_breaker_open(self):
        """Test circuit breaker opening after threshold failures."""
        
        async def failing_service():
            """Service that always fails."""
            raise Exception("Service unavailable")
        
        # Test that circuit breaker starts closed
        assert self.circuit_breaker.state == CircuitState.CLOSED
        
        # Generate failures to reach threshold
        for i in range(self.config.failure_threshold):
            with pytest.raises(Exception):
                await self.circuit_breaker.call(failing_service)
        
        # Circuit should now be open
        assert self.circuit_breaker.state == CircuitState.OPEN
        
        # Next call should fast-fail
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await self.circuit_breaker.call(failing_service)
    
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery to closed state."""
        
        self.service_working = False
        
        async def intermittent_service():
            """Service that fails then succeeds."""
            if not self.service_working:
                raise Exception("Service temporarily down")
            return "Service response"
        
        # Force circuit to open
        for i in range(self.config.failure_threshold):
            with pytest.raises(Exception):
                await self.circuit_breaker.call(intermittent_service)
        
        assert self.circuit_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(self.config.recovery_timeout + 0.1)
        
        # Fix the service
        self.service_working = True
        
        # First call after timeout should transition to half-open
        result = await self.circuit_breaker.call(intermittent_service)
        assert result == "Service response"
        assert self.circuit_breaker.state == CircuitState.HALF_OPEN
        
        # Successful calls should close the circuit
        for i in range(self.config.success_threshold - 1):
            await self.circuit_breaker.call(intermittent_service)
        
        assert self.circuit_breaker.state == CircuitState.CLOSED
    
    async def test_circuit_breaker_timeout_handling(self):
        """Test circuit breaker handling of timeouts."""
        
        async def slow_service(delay=0.1):
            """Service with configurable delay."""
            await asyncio.sleep(delay)
            return "Slow response"
        
        # Configure short timeout
        self.circuit_breaker.config.timeout = 0.05
        
        # Test successful fast call
        result = await self.circuit_breaker.call(slow_service, 0.01)
        assert result == "Slow response"
        
        # Test timeout
        with pytest.raises(asyncio.TimeoutError):
            await self.circuit_breaker.call(slow_service, 0.1)
        
        assert self.circuit_breaker.metrics["timeouts"] == 1
    
    async def test_circuit_breaker_metrics(self):
        """Test circuit breaker metrics collection."""
        
        async def test_service(should_fail=False):
            """Service for testing metrics."""
            if should_fail:
                raise Exception("Test failure")
            return "Success"
        
        # Make successful calls
        for i in range(5):
            await self.circuit_breaker.call(test_service, should_fail=False)
        
        # Make failing calls
        for i in range(2):
            with pytest.raises(Exception):
                await self.circuit_breaker.call(test_service, should_fail=True)
        
        metrics = self.circuit_breaker.metrics
        assert metrics["calls"] == 7
        assert metrics["failures"] == 2


class TestRetryMechanisms:
    """Test retry mechanisms with various strategies."""
    
    async def test_exponential_backoff(self):
        """Test exponential backoff retry strategy."""
        
        self.attempt_count = 0
        
        async def flaky_service():
            """Service that fails first few times."""
            self.attempt_count += 1
            if self.attempt_count < 3:
                raise Exception(f"Failure attempt {self.attempt_count}")
            return f"Success after {self.attempt_count} attempts"
        
        retry_policy = RetryPolicy(max_retries=3, base_delay=0.01, jitter=False)
        
        start_time = time.time()
        result = await retry_policy.execute(flaky_service)
        end_time = time.time()
        
        assert result == "Success after 3 attempts"
        assert self.attempt_count == 3
        
        # Check that delays were applied (should take at least base_delay * 3)
        expected_min_time = 0.01 + 0.02  # First two delays
        assert end_time - start_time >= expected_min_time
    
    async def test_retry_with_jitter(self):
        """Test retry with jitter to prevent thundering herd."""
        
        delays = []
        original_sleep = asyncio.sleep
        
        async def mock_sleep(delay):
            delays.append(delay)
            await original_sleep(0.001)  # Very short actual delay for testing
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            retry_policy = RetryPolicy(max_retries=3, base_delay=1.0, jitter=True)
            
            async def always_failing_service():
                raise Exception("Always fails")
            
            with pytest.raises(Exception):
                await retry_policy.execute(always_failing_service)
        
        # Should have 3 delays (for 3 retries)
        assert len(delays) == 3
        
        # With jitter, delays should vary
        base_delays = [1.0, 2.0, 4.0]  # Expected base delays
        for i, actual_delay in enumerate(delays):
            expected_base = base_delays[i]
            # Jitter should make delay between 50% and 100% of base
            assert expected_base * 0.5 <= actual_delay <= expected_base
    
    async def test_retry_max_attempts(self):
        """Test that retry respects maximum attempt limits."""
        
        self.call_count = 0
        
        async def always_failing_service():
            """Service that always fails."""
            self.call_count += 1
            raise Exception(f"Failure {self.call_count}")
        
        retry_policy = RetryPolicy(max_retries=2, base_delay=0.001)
        
        with pytest.raises(Exception, match="Failure 3"):
            await retry_policy.execute(always_failing_service)
        
        # Should have been called 3 times (1 initial + 2 retries)
        assert self.call_count == 3
    
    async def test_retry_immediate_success(self):
        """Test that successful operations don't retry."""
        
        self.call_count = 0
        
        async def successful_service():
            """Service that succeeds immediately."""
            self.call_count += 1
            return f"Success on call {self.call_count}"
        
        retry_policy = RetryPolicy(max_retries=3, base_delay=0.1)
        
        start_time = time.time()
        result = await retry_policy.execute(successful_service)
        end_time = time.time()
        
        assert result == "Success on call 1"
        assert self.call_count == 1
        # Should complete quickly without delays
        assert end_time - start_time < 0.05


class TestServiceDiscovery:
    """Test service discovery and failover mechanisms."""
    
    def setup_method(self):
        """Setup test environment."""
        self.registry = ServiceRegistry()
    
    def test_service_registration_and_discovery(self):
        """Test basic service registration and discovery."""
        
        # Register multiple endpoints for same service
        self.registry.register_service("api", "http://api1.example.com")
        self.registry.register_service("api", "http://api2.example.com")
        self.registry.register_service("api", "http://api3.example.com")
        
        # Get healthy endpoints
        endpoints = self.registry.get_healthy_endpoints("api")
        assert len(endpoints) == 3
        assert "http://api1.example.com" in endpoints
        
        # Mark one as unhealthy
        self.registry.mark_unhealthy("http://api1.example.com")
        healthy_endpoints = self.registry.get_healthy_endpoints("api")
        assert len(healthy_endpoints) == 2
        assert "http://api1.example.com" not in healthy_endpoints
    
    async def test_load_balancing_with_failover(self):
        """Test load balancing with automatic failover."""
        
        # Setup services
        services = [
            "http://service1.example.com",
            "http://service2.example.com", 
            "http://service3.example.com"
        ]
        
        for service in services:
            self.registry.register_service("compute", service)
        
        class LoadBalancer:
            def __init__(self, registry):
                self.registry = registry
                self.current_index = 0
            
            def get_next_endpoint(self, service_name):
                """Round-robin load balancing."""
                endpoints = self.registry.get_healthy_endpoints(service_name)
                if not endpoints:
                    return None
                
                endpoint = endpoints[self.current_index % len(endpoints)]
                self.current_index += 1
                return endpoint
            
            async def call_service(self, service_name, operation):
                """Call service with automatic failover."""
                max_attempts = 3
                
                for attempt in range(max_attempts):
                    endpoint = self.get_next_endpoint(service_name)
                    if not endpoint:
                        raise Exception("No healthy endpoints available")
                    
                    try:
                        # Simulate service call
                        return await self._simulate_service_call(endpoint, operation)
                    except Exception:
                        # Mark endpoint as unhealthy and try next
                        self.registry.mark_unhealthy(endpoint)
                        continue
                
                raise Exception("All failover attempts exhausted")
            
            async def _simulate_service_call(self, endpoint, operation):
                """Simulate calling a service endpoint."""
                # Simulate different service behaviors
                if endpoint == "http://service1.example.com":
                    if operation == "test_failure":
                        raise Exception("Service 1 is down")
                    return f"Response from service 1: {operation}"
                elif endpoint == "http://service2.example.com":
                    return f"Response from service 2: {operation}"
                else:
                    return f"Response from service 3: {operation}"
        
        load_balancer = LoadBalancer(self.registry)
        
        # Test normal operation
        result = await load_balancer.call_service("compute", "normal_request")
        assert "Response from service" in result
        
        # Test failover when service 1 fails
        result = await load_balancer.call_service("compute", "test_failure")
        assert "service 2" in result or "service 3" in result
        
        # Verify service 1 is marked unhealthy
        healthy_endpoints = self.registry.get_healthy_endpoints("compute")
        assert "http://service1.example.com" not in healthy_endpoints
    
    def test_health_check_recovery(self):
        """Test service health check and recovery."""
        
        # Register service
        self.registry.register_service("database", "http://db1.example.com")
        
        # Service should be healthy initially
        endpoints = self.registry.get_healthy_endpoints("database")
        assert len(endpoints) == 1
        
        # Mark as unhealthy
        self.registry.mark_unhealthy("http://db1.example.com")
        endpoints = self.registry.get_healthy_endpoints("database")
        assert len(endpoints) == 0
        
        # Recover service
        self.registry.mark_healthy("http://db1.example.com")
        endpoints = self.registry.get_healthy_endpoints("database")
        assert len(endpoints) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])