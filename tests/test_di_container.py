#!/usr/bin/env python3
"""
Tests for the Dependency Injection Container
"""

import pytest
from typing import Optional

from subforge.core.di_container import (
    DIContainer,
    DIContainerError,
    ServiceLifecycle,
    get_container,
)


# Test classes for dependency injection
class IDatabase:
    """Database interface"""
    def connect(self) -> bool:
        raise NotImplementedError


class MockDatabase(IDatabase):
    """Mock database implementation"""
    def __init__(self):
        self.connected = False
    
    def connect(self) -> bool:
        self.connected = True
        return True


class ICache:
    """Cache interface"""
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError


class MockCache(ICache):
    """Mock cache implementation"""
    def __init__(self):
        self.data = {}
    
    def get(self, key: str) -> Optional[str]:
        return self.data.get(key)


class UserService:
    """Service with dependencies"""
    def __init__(self, database: IDatabase, cache: ICache):
        self.database = database
        self.cache = cache
    
    def get_user(self, user_id: str) -> dict:
        # Check cache first
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return {"id": user_id, "from_cache": True}
        
        # Get from database
        if self.database.connect():
            return {"id": user_id, "from_db": True}
        
        return {}


class TestDIContainer:
    """Test cases for DI Container"""
    
    def test_register_and_resolve_simple(self):
        """Test basic registration and resolution"""
        container = DIContainer()
        
        # Register service
        container.register(MockDatabase)
        
        # Resolve service
        db = container.resolve(MockDatabase)
        
        assert isinstance(db, MockDatabase)
        assert db.connect() is True
    
    def test_register_interface_with_implementation(self):
        """Test registering interface with implementation"""
        container = DIContainer()
        
        # Register interface with implementation
        container.register(IDatabase, MockDatabase)
        
        # Resolve by interface
        db = container.resolve(IDatabase)
        
        assert isinstance(db, MockDatabase)
        assert isinstance(db, IDatabase)
    
    def test_singleton_lifecycle(self):
        """Test singleton lifecycle"""
        container = DIContainer()
        
        # Register as singleton
        container.register(MockDatabase, lifecycle=ServiceLifecycle.SINGLETON)
        
        # Resolve multiple times
        db1 = container.resolve(MockDatabase)
        db2 = container.resolve(MockDatabase)
        
        # Should be same instance
        assert db1 is db2
    
    def test_transient_lifecycle(self):
        """Test transient lifecycle"""
        container = DIContainer()
        
        # Register as transient (default)
        container.register(MockDatabase, lifecycle=ServiceLifecycle.TRANSIENT)
        
        # Resolve multiple times
        db1 = container.resolve(MockDatabase)
        db2 = container.resolve(MockDatabase)
        
        # Should be different instances
        assert db1 is not db2
    
    def test_scoped_lifecycle(self):
        """Test scoped lifecycle"""
        container = DIContainer()
        
        # Register as scoped
        container.register(MockCache, lifecycle=ServiceLifecycle.SCOPED)
        
        # Within same scope
        cache1 = container.resolve(MockCache)
        cache2 = container.resolve(MockCache)
        assert cache1 is cache2
        
        # Clear scope
        container.clear_scoped_instances()
        
        # New scope
        cache3 = container.resolve(MockCache)
        assert cache3 is not cache1
    
    def test_register_factory(self):
        """Test factory registration"""
        container = DIContainer()
        
        # Counter to track factory calls
        call_count = [0]
        
        def database_factory() -> IDatabase:
            call_count[0] += 1
            return MockDatabase()
        
        # Register factory
        container.register_factory(IDatabase, database_factory)
        
        # Resolve using factory
        db1 = container.resolve(IDatabase)
        db2 = container.resolve(IDatabase)
        
        assert isinstance(db1, MockDatabase)
        assert isinstance(db2, MockDatabase)
        assert db1 is not db2
        assert call_count[0] == 2
    
    def test_register_instance(self):
        """Test instance registration"""
        container = DIContainer()
        
        # Create instance
        cache_instance = MockCache()
        cache_instance.data["test"] = "value"
        
        # Register instance
        container.register_instance(ICache, cache_instance)
        
        # Resolve should return same instance
        cache1 = container.resolve(ICache)
        cache2 = container.resolve(ICache)
        
        assert cache1 is cache_instance
        assert cache2 is cache_instance
        assert cache1.get("test") == "value"
    
    def test_constructor_injection(self):
        """Test automatic constructor injection"""
        container = DIContainer()
        
        # Register dependencies
        container.register(IDatabase, MockDatabase)
        container.register(ICache, MockCache)
        container.register(UserService)
        
        # Resolve service with dependencies
        user_service = container.resolve(UserService)
        
        assert isinstance(user_service, UserService)
        assert isinstance(user_service.database, MockDatabase)
        assert isinstance(user_service.cache, MockCache)
        
        # Test service works
        user = user_service.get_user("123")
        assert user["id"] == "123"
        assert user["from_db"] is True
    
    def test_circular_dependency_prevention(self):
        """Test that circular dependencies are handled"""
        container = DIContainer()
        
        class ServiceA:
            def __init__(self, service_b: "ServiceB"):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        container.register(ServiceA)
        container.register(ServiceB)
        
        # Should raise error for circular dependency
        with pytest.raises(DIContainerError):
            container.resolve(ServiceA)
    
    def test_missing_dependency_error(self):
        """Test error when dependency is not registered"""
        container = DIContainer()
        
        class ServiceWithMissingDep:
            def __init__(self, unknown_service: "UnknownService"):
                self.unknown = unknown_service
        
        container.register(ServiceWithMissingDep)
        
        # Should raise error for missing dependency
        with pytest.raises(DIContainerError) as exc_info:
            container.resolve(ServiceWithMissingDep)
        
        assert "Cannot resolve dependency" in str(exc_info.value)
    
    def test_optional_dependency(self):
        """Test optional dependencies"""
        container = DIContainer()
        
        class ServiceWithOptional:
            def __init__(self, database: Optional[IDatabase] = None):
                self.database = database
        
        container.register(ServiceWithOptional)
        
        # Should resolve without optional dependency
        service = container.resolve(ServiceWithOptional)
        assert service.database is None
        
        # Register optional dependency
        container.register(IDatabase, MockDatabase)
        
        # Now should resolve with dependency
        service2 = container.resolve(ServiceWithOptional)
        assert isinstance(service2.database, MockDatabase)
    
    def test_inject_decorator(self):
        """Test inject decorator"""
        container = DIContainer()
        container.register(IDatabase, MockDatabase)
        container.register(ICache, MockCache)
        
        @container.inject
        def process_data(database: IDatabase, cache: ICache) -> str:
            if database.connect():
                return "Connected"
            return "Failed"
        
        # Call function without providing dependencies
        result = process_data()
        assert result == "Connected"
    
    def test_scope_context_manager(self):
        """Test scope context manager"""
        container = DIContainer()
        container.register(MockCache, lifecycle=ServiceLifecycle.SCOPED)
        
        # First scope
        with container.create_scope():
            cache1 = container.resolve(MockCache)
            cache2 = container.resolve(MockCache)
            assert cache1 is cache2
        
        # Second scope (automatic cleanup)
        with container.create_scope():
            cache3 = container.resolve(MockCache)
            assert cache3 is not cache1
    
    def test_is_registered(self):
        """Test checking if service is registered"""
        container = DIContainer()
        
        assert not container.is_registered(MockDatabase)
        
        container.register(MockDatabase)
        
        assert container.is_registered(MockDatabase)
    
    def test_get_all_services(self):
        """Test getting all registered services"""
        container = DIContainer()
        
        container.register(IDatabase, MockDatabase)
        container.register(ICache, MockCache)
        container.register(UserService)
        
        services = container.get_all_services()
        
        assert "IDatabase" in services
        assert "ICache" in services
        assert "UserService" in services
    
    def test_global_container(self):
        """Test global container instance"""
        container1 = get_container()
        container2 = get_container()
        
        # Should be same instance
        assert container1 is container2
    
    def test_fluent_interface(self):
        """Test fluent interface for registration"""
        container = DIContainer()
        
        # Chain registrations
        result = (
            container
            .register(IDatabase, MockDatabase, lifecycle=ServiceLifecycle.SINGLETON)
            .register(ICache, MockCache)
            .register(UserService)
        )
        
        # Should return container for chaining
        assert result is container
        
        # All services should be registered
        assert container.is_registered(IDatabase)
        assert container.is_registered(ICache)
        assert container.is_registered(UserService)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])