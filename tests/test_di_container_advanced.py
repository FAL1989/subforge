"""
Advanced DI Container Tests for SubForge
Tests complex scenarios including scoped services, circular dependencies,
factory registration, performance, thread safety, and complex dependency graphs
"""

import asyncio
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest

from subforge.core.di_container import (
    DIContainer,
    DIContainerError,
    DIScope,
    ServiceDescriptor,
    ServiceLifecycle,
    get_container,
    register_services,
)


# Test fixtures and mock classes
class IDatabase(ABC):
    """Database interface"""

    @abstractmethod
    def connect(self) -> bool:
        pass


class ICache(ABC):
    """Cache interface"""

    @abstractmethod
    def get(self, key: str) -> Any:
        pass


class ILogger(ABC):
    """Logger interface"""

    @abstractmethod
    def log(self, message: str):
        pass


class MockDatabase(IDatabase):
    """Mock database implementation"""

    def __init__(self):
        self.connected = False
        self.connection_count = 0

    def connect(self) -> bool:
        self.connected = True
        self.connection_count += 1
        return True


class MockCache(ICache):
    """Mock cache implementation"""

    def __init__(self, database: IDatabase):
        self.database = database
        self.data = {}

    def get(self, key: str) -> Any:
        return self.data.get(key)


class MockLogger(ILogger):
    """Mock logger implementation"""

    def __init__(self, name: str = "default"):
        self.name = name
        self.messages = []

    def log(self, message: str):
        self.messages.append(f"[{self.name}] {message}")


@dataclass
class ServiceWithMultipleDeps:
    """Service with multiple dependencies"""

    database: IDatabase
    cache: ICache
    logger: ILogger
    config: Optional[Dict[str, Any]] = None


class CircularDepA:
    """Class A for circular dependency testing"""

    def __init__(self, b: "CircularDepB"):
        self.b = b


class CircularDepB:
    """Class B for circular dependency testing"""

    def __init__(self, a: CircularDepA):
        self.a = a


class SelfDependent:
    """Class that depends on itself"""

    def __init__(self, self_dep: "SelfDependent"):
        self.self_dep = self_dep


class TestDIContainerAdvanced:
    """Advanced DI Container test suite"""

    @pytest.fixture
    def container(self):
        """Create fresh DI container for each test"""
        return DIContainer()

    def test_scoped_services_same_scope(self, container):
        """Test that scoped services return same instance within scope"""
        # Register scoped service
        container.register(MockLogger, lifecycle=ServiceLifecycle.SCOPED)

        # Create scope and resolve multiple times
        with container.create_scope():
            logger1 = container.resolve(MockLogger)
            logger2 = container.resolve(MockLogger)

            # Should be same instance within scope
            assert logger1 is logger2
            assert id(logger1) == id(logger2)

            # Test that instance retains state
            logger1.log("test message")
            assert len(logger2.messages) == 1
            # Logger name is initialized in constructor, check if message is there
            assert "test message" in logger2.messages[0]

    def test_scoped_services_different_scopes(self, container):
        """Test that scoped services return different instances in different scopes"""
        # Register scoped service
        container.register(MockLogger, lifecycle=ServiceLifecycle.SCOPED)

        logger_ids = []

        # Create first scope
        with container.create_scope():
            logger1 = container.resolve(MockLogger)
            logger_ids.append(id(logger1))
            logger1.log("scope 1")

        # Create second scope
        with container.create_scope():
            logger2 = container.resolve(MockLogger)
            logger_ids.append(id(logger2))
            logger2.log("scope 2")

            # Should be different instance
            assert id(logger1) != id(logger2)
            # Logger2 should not have logger1's messages
            assert len(logger2.messages) == 1
            assert "scope 2" in logger2.messages[0]

        # Verify different instances were created
        assert logger_ids[0] != logger_ids[1]

    def test_scoped_services_cleanup(self, container):
        """Test that scoped instances are cleaned up after scope exit"""
        container.register(MockDatabase, lifecycle=ServiceLifecycle.SCOPED)

        # Create scope and resolve
        with container.create_scope():
            db = container.resolve(MockDatabase)
            db.connect()
            assert db.connected

        # After scope, should get new instance
        with container.create_scope():
            db2 = container.resolve(MockDatabase)
            # Should be new instance, not connected
            assert not db2.connected
            assert db2.connection_count == 0

    def test_circular_dependency_detection_direct(self, container):
        """Test detection of direct circular dependencies (A -> B -> A)"""
        container.register(CircularDepA)
        container.register(CircularDepB)

        # Should raise error when trying to resolve circular dependency
        with pytest.raises(DIContainerError) as exc_info:
            container.resolve(CircularDepA)

        assert "Cannot resolve dependency" in str(exc_info.value)

    def test_self_dependency_detection(self, container):
        """Test detection of self-dependency"""
        container.register(SelfDependent)

        # Should raise error for self-dependency
        with pytest.raises(DIContainerError) as exc_info:
            container.resolve(SelfDependent)

        assert "Cannot resolve dependency" in str(exc_info.value)

    def test_factory_registration_basic(self, container):
        """Test basic factory function registration"""
        call_count = 0

        def create_logger() -> MockLogger:
            nonlocal call_count
            call_count += 1
            return MockLogger(f"factory-{call_count}")

        # Register factory
        container.register_factory(ILogger, create_logger)

        # Resolve using factory
        logger1 = container.resolve(ILogger)
        logger2 = container.resolve(ILogger)

        # Should create new instances (transient by default)
        assert logger1 is not logger2
        assert logger1.name == "factory-1"
        assert logger2.name == "factory-2"
        assert call_count == 2

    def test_factory_registration_with_singleton(self, container):
        """Test factory registration with singleton lifecycle"""
        creation_count = 0

        def create_database() -> MockDatabase:
            nonlocal creation_count
            creation_count += 1
            db = MockDatabase()
            db.connect()
            return db

        # Register factory as singleton
        container.register_factory(IDatabase, create_database, lifecycle=ServiceLifecycle.SINGLETON)

        # Resolve multiple times
        db1 = container.resolve(IDatabase)
        db2 = container.resolve(IDatabase)
        db3 = container.resolve(IDatabase)

        # Should be same instance
        assert db1 is db2 is db3
        assert creation_count == 1  # Factory called only once
        assert db1.connected

    def test_factory_with_parameters(self, container):
        """Test factory functions that require parameters"""
        # Register dependencies
        container.register(IDatabase, MockDatabase, lifecycle=ServiceLifecycle.SINGLETON)

        def create_cache() -> ICache:
            # Factory can resolve dependencies from container
            db = container.resolve(IDatabase)
            return MockCache(db)

        container.register_factory(ICache, create_cache)

        # Resolve cache
        cache = container.resolve(ICache)
        assert isinstance(cache, MockCache)
        assert isinstance(cache.database, MockDatabase)

    def test_async_factory_registration(self, container):
        """Test registration and resolution of async factories"""

        async def create_async_service() -> MockLogger:
            await asyncio.sleep(0.01)  # Simulate async operation
            return MockLogger("async-logger")

        # For async factories, we need a wrapper
        def async_factory_wrapper():
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(create_async_service())

        container.register_factory(MockLogger, async_factory_wrapper)

        logger = container.resolve(MockLogger)
        assert logger.name == "async-logger"

    def test_performance_benchmarks(self, container):
        """Benchmark service resolution performance"""
        # Register many services
        num_services = 100

        # Register services with dependencies
        for i in range(num_services):

            class TempService:
                def __init__(self, index=i):
                    self.index = index

            # Create closure to capture index
            def make_factory(idx):
                return lambda: TempService(idx)

            container.register_factory(TempService, make_factory(i))

        # Benchmark resolution
        start_time = time.time()
        resolutions = []

        for _ in range(1000):  # Resolve 1000 times
            service = container.resolve(TempService)
            resolutions.append(service)

        elapsed = time.time() - start_time

        # Should be fast (less than 1 second for 1000 resolutions)
        assert elapsed < 1.0
        print(f"\nPerformance: 1000 resolutions in {elapsed:.3f}s ({1000/elapsed:.0f} res/sec)")

    def test_performance_with_complex_dependencies(self, container):
        """Test performance with complex dependency graphs"""
        # Register hierarchy of dependencies
        container.register(MockDatabase, IDatabase, lifecycle=ServiceLifecycle.SINGLETON)
        container.register(MockCache, ICache)
        container.register(MockLogger, ILogger)
        container.register(ServiceWithMultipleDeps)

        start_time = time.time()

        for _ in range(100):
            service = container.resolve(ServiceWithMultipleDeps)
            assert service.database is not None
            assert service.cache is not None
            assert service.logger is not None

        elapsed = time.time() - start_time
        assert elapsed < 0.5  # Should be fast even with dependencies
        print(f"\nComplex dependency resolution: 100 in {elapsed:.3f}s")

    def test_thread_safety_concurrent_registration(self, container):
        """Test thread-safe concurrent service registration"""
        errors = []
        registration_count = 0
        lock = threading.Lock()

        def register_service(index):
            nonlocal registration_count
            try:

                class ThreadService:
                    def __init__(self):
                        self.id = index

                container.register(ThreadService)
                with lock:
                    registration_count += 1
            except Exception as e:
                errors.append(e)

        # Register services from multiple threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_service, i) for i in range(50)]
            for future in futures:
                future.result()

        assert len(errors) == 0
        assert registration_count == 50

    def test_thread_safety_concurrent_resolution(self, container):
        """Test thread-safe concurrent service resolution"""
        container.register(MockDatabase, IDatabase, lifecycle=ServiceLifecycle.SINGLETON)
        container.register(MockCache, ICache)

        resolved_services = []
        errors = []
        lock = threading.Lock()

        def resolve_services():
            try:
                db = container.resolve(IDatabase)
                cache = container.resolve(ICache)
                with lock:
                    resolved_services.append((db, cache))
            except Exception as e:
                errors.append(e)

        # Resolve from multiple threads
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(resolve_services) for _ in range(100)]
            for future in futures:
                future.result()

        assert len(errors) == 0
        assert len(resolved_services) == 100

        # All singleton instances should be the same
        databases = [s[0] for s in resolved_services]
        assert all(db is databases[0] for db in databases)

    def test_thread_safety_singleton_creation(self, container):
        """Test that singleton creation is thread-safe"""
        creation_count = 0
        lock = threading.Lock()

        class CountedService:
            def __init__(self):
                nonlocal creation_count
                with lock:
                    creation_count += 1
                # Simulate some work
                time.sleep(0.001)
                self.id = creation_count

        container.register(CountedService, lifecycle=ServiceLifecycle.SINGLETON)

        instances = []

        def get_instance():
            instances.append(container.resolve(CountedService))

        # Try to create singleton from multiple threads simultaneously
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_instance) for _ in range(50)]
            for future in futures:
                future.result()

        # Should only create one instance
        assert creation_count == 1
        # All instances should be the same
        assert all(inst is instances[0] for inst in instances)
        assert all(inst.id == 1 for inst in instances)

    def test_complex_dependency_graph_deep_chain(self, container):
        """Test resolution of deep dependency chains"""

        # Create chain of dependencies A -> B -> C -> D -> E
        class ServiceE:
            def __init__(self):
                self.name = "E"

        class ServiceD:
            def __init__(self, e: ServiceE):
                self.e = e
                self.name = "D"

        class ServiceC:
            def __init__(self, d: ServiceD):
                self.d = d
                self.name = "C"

        class ServiceB:
            def __init__(self, c: ServiceC):
                self.c = c
                self.name = "B"

        class ServiceA:
            def __init__(self, b: ServiceB):
                self.b = b
                self.name = "A"

        # Register all services
        container.register(ServiceE)
        container.register(ServiceD)
        container.register(ServiceC)
        container.register(ServiceB)
        container.register(ServiceA)

        # Resolve top-level service
        service_a = container.resolve(ServiceA)

        # Verify entire chain is resolved
        assert service_a.name == "A"
        assert service_a.b.name == "B"
        assert service_a.b.c.name == "C"
        assert service_a.b.c.d.name == "D"
        assert service_a.b.c.d.e.name == "E"

    def test_complex_dependency_graph_diamond(self, container):
        """Test resolution of diamond dependency pattern"""

        # Diamond pattern: A depends on B and C, both B and C depend on D
        class ServiceD:
            def __init__(self):
                self.name = "D"
                self.access_count = 0

        class ServiceB:
            def __init__(self, d: ServiceD):
                self.d = d
                self.name = "B"

        class ServiceC:
            def __init__(self, d: ServiceD):
                self.d = d
                self.name = "C"

        class ServiceA:
            def __init__(self, b: ServiceB, c: ServiceC):
                self.b = b
                self.c = c
                self.name = "A"

        # Register D as singleton to ensure same instance
        container.register(ServiceD, lifecycle=ServiceLifecycle.SINGLETON)
        container.register(ServiceB)
        container.register(ServiceC)
        container.register(ServiceA)

        service_a = container.resolve(ServiceA)

        # Both B and C should have the same D instance
        assert service_a.b.d is service_a.c.d

    def test_lazy_initialization_singleton(self, container):
        """Test that singletons are created lazily (only when needed)"""
        creation_log = []

        class LazyService:
            def __init__(self):
                creation_log.append("LazyService created")
                self.initialized = True

        # Register but don't resolve yet
        container.register(LazyService, lifecycle=ServiceLifecycle.SINGLETON)

        # Should not be created yet
        assert len(creation_log) == 0

        # Now resolve
        service = container.resolve(LazyService)
        assert len(creation_log) == 1
        assert service.initialized

        # Resolve again - should not create new instance
        service2 = container.resolve(LazyService)
        assert len(creation_log) == 1  # Still only one creation
        assert service is service2

    def test_service_disposal_pattern(self, container):
        """Test service disposal/cleanup pattern"""

        class DisposableService:
            def __init__(self):
                self.is_disposed = False
                self.resources_allocated = True

            def dispose(self):
                self.resources_allocated = False
                self.is_disposed = True

        # Register service
        container.register(DisposableService, lifecycle=ServiceLifecycle.SINGLETON)

        service = container.resolve(DisposableService)
        assert service.resources_allocated
        assert not service.is_disposed

        # Manual disposal (since Python doesn't have IDisposable)
        service.dispose()
        assert service.is_disposed
        assert not service.resources_allocated

    def test_scope_cleanup_on_exception(self, container):
        """Test that scope cleanup happens even on exception"""
        container.register(MockLogger, lifecycle=ServiceLifecycle.SCOPED)

        logger_in_scope = None

        try:
            with container.create_scope():
                logger_in_scope = container.resolve(MockLogger)
                logger_in_scope.log("in scope")
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # New scope should have fresh instance
        with container.create_scope():
            new_logger = container.resolve(MockLogger)
            assert new_logger is not logger_in_scope
            assert len(new_logger.messages) == 0  # Fresh instance

    def test_container_disposal(self, container):
        """Test container disposal and cleanup"""
        # Register services
        container.register(MockDatabase, IDatabase, lifecycle=ServiceLifecycle.SINGLETON)
        container.register(MockCache, ICache, lifecycle=ServiceLifecycle.SCOPED)

        # Resolve to create instances
        db = container.resolve(IDatabase)
        with container.create_scope():
            cache = container.resolve(ICache)

        # Clear all scoped instances
        container.clear_scoped_instances()

        # New scope should have fresh instances
        with container.create_scope():
            new_cache = container.resolve(ICache)
            assert new_cache is not cache

    def test_optional_dependency_injection(self, container):
        """Test injection of optional dependencies"""
        from typing import Optional

        class ServiceWithOptional:
            def __init__(self, logger: Optional[ILogger] = None):
                self.logger = logger

        # Register service but not its optional dependency
        container.register(ServiceWithOptional)

        # Should resolve with None for optional dependency
        service = container.resolve(ServiceWithOptional)
        assert service.logger is None

        # Now register the optional dependency
        container.register(MockLogger, ILogger)

        # Should resolve with the dependency
        service2 = container.resolve(ServiceWithOptional)
        assert service2.logger is not None
        assert isinstance(service2.logger, MockLogger)

    def test_get_all_services(self, container):
        """Test retrieving all registered services"""
        # Register multiple services
        container.register(MockDatabase, IDatabase)
        container.register(MockCache, ICache)
        container.register(MockLogger, ILogger, lifecycle=ServiceLifecycle.SINGLETON)

        all_services = container.get_all_services()

        assert len(all_services) == 3
        assert "IDatabase" in all_services
        assert "ICache" in all_services
        assert "ILogger" in all_services

        # Check service descriptors
        db_descriptor = all_services["IDatabase"]
        assert db_descriptor.interface == IDatabase
        assert db_descriptor.implementation == MockDatabase
        assert db_descriptor.lifecycle == ServiceLifecycle.TRANSIENT

        logger_descriptor = all_services["ILogger"]
        assert logger_descriptor.lifecycle == ServiceLifecycle.SINGLETON

    def test_is_registered(self, container):
        """Test checking if service is registered"""
        assert not container.is_registered(IDatabase)

        container.register(MockDatabase, IDatabase)
        assert container.is_registered(IDatabase)
        assert not container.is_registered(ICache)

        container.register(MockCache, ICache)
        assert container.is_registered(ICache)

    def test_inject_decorator(self, container):
        """Test dependency injection decorator"""
        container.register(MockLogger, ILogger)
        container.register(MockDatabase, IDatabase)

        @container.inject
        def process_data(data: str, logger: ILogger, database: IDatabase) -> str:
            logger.log(f"Processing: {data}")
            database.connect()
            return f"Processed: {data}"

        # Call without providing injected dependencies
        result = process_data("test data")
        assert result == "Processed: test data"

    def test_global_container(self):
        """Test global container functionality"""
        global_container = get_container()
        assert isinstance(global_container, DIContainer)

        # Register services in global container
        register_services()

        # Should have core services registered
        from subforge.core.cache_manager import CacheManager

        assert global_container.is_registered(CacheManager)

    def test_register_instance(self, container):
        """Test registering an existing instance"""
        # Create instance manually
        logger = MockLogger("manual-instance")
        logger.log("pre-registration message")

        # Register the instance
        container.register_instance(ILogger, logger)

        # Resolve should return same instance
        resolved = container.resolve(ILogger)
        assert resolved is logger
        assert len(resolved.messages) == 1
        assert "pre-registration message" in resolved.messages[0]

        # Multiple resolutions return same instance (singleton behavior)
        resolved2 = container.resolve(ILogger)
        assert resolved2 is logger

    def test_invalid_factory_registration(self, container):
        """Test error handling for invalid factory registration"""
        # Non-callable factory
        with pytest.raises(DIContainerError) as exc_info:
            container.register_factory(ILogger, "not a callable")

        assert "Factory must be callable" in str(exc_info.value)

    def test_abstract_class_registration_error(self, container):
        """Test that abstract classes cannot be registered as implementation"""
        with pytest.raises(DIContainerError) as exc_info:
            container.register(IDatabase)  # IDatabase is abstract

        assert "Cannot register abstract class" in str(exc_info.value)

    def test_invalid_implementation_error(self, container):
        """Test error when implementation doesn't implement interface"""

        class UnrelatedClass:
            pass

        with pytest.raises(DIContainerError) as exc_info:
            container.register(IDatabase, UnrelatedClass)

        assert "does not implement" in str(exc_info.value)

    def test_invalid_instance_registration(self, container):
        """Test error when registering instance of wrong type"""
        logger = MockLogger()

        with pytest.raises(DIContainerError) as exc_info:
            container.register_instance(IDatabase, logger)  # Wrong type

        assert "is not of type" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])