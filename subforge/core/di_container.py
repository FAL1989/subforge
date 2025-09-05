"""
SubForge Dependency Injection Container
Manages service registration, resolution, and lifecycle
"""

import inspect
from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Type, get_type_hints

from subforge.core.context.exceptions import SubForgeError


class DIContainerError(SubForgeError):
    """Raised for DI container related errors"""


class ServiceLifecycle:
    """Service lifecycle management"""

    TRANSIENT = "transient"  # New instance every time
    SINGLETON = "singleton"  # Single instance throughout application
    SCOPED = "scoped"  # Single instance per scope/request


@dataclass
class ServiceDescriptor:
    """Describes a registered service"""

    interface: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable] = None
    lifecycle: str = ServiceLifecycle.TRANSIENT
    instance: Optional[Any] = None  # For singleton instances


class DIContainer:
    """
    Dependency Injection Container for SubForge
    Manages service registration, resolution, and lifecycle
    """

    def __init__(self):
        """Initialize the DI container"""
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._scoped_instances: Dict[Type, Any] = {}

    def register(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        lifecycle: str = ServiceLifecycle.TRANSIENT,
    ) -> "DIContainer":
        """
        Register a service

        Args:
            interface: Service interface/abstract class
            implementation: Concrete implementation (defaults to interface)
            lifecycle: Service lifecycle (transient, singleton, scoped)

        Returns:
            Self for fluent interface

        Raises:
            DIContainerError: If registration fails
        """
        if implementation is None:
            implementation = interface

        # Validate implementation
        if inspect.isabstract(implementation):
            raise DIContainerError(
                f"Cannot register abstract class {implementation.__name__} as implementation"
            )

        # Validate that implementation implements interface
        if interface != implementation and not issubclass(implementation, interface):
            raise DIContainerError(
                f"{implementation.__name__} does not implement {interface.__name__}"
            )

        descriptor = ServiceDescriptor(
            interface=interface, implementation=implementation, lifecycle=lifecycle
        )

        self._services[interface] = descriptor
        return self

    def register_factory(
        self, interface: Type, factory: Callable[[], Any], lifecycle: str = ServiceLifecycle.TRANSIENT
    ) -> "DIContainer":
        """
        Register a factory function for service creation

        Args:
            interface: Service interface
            factory: Factory function that creates instances
            lifecycle: Service lifecycle

        Returns:
            Self for fluent interface
        """
        if not callable(factory):
            raise DIContainerError(f"Factory must be callable, got {type(factory)}")

        descriptor = ServiceDescriptor(interface=interface, factory=factory, lifecycle=lifecycle)

        self._services[interface] = descriptor
        return self

    def register_instance(self, interface: Type, instance: Any) -> "DIContainer":
        """
        Register an existing instance as a singleton

        Args:
            interface: Service interface
            instance: Existing instance

        Returns:
            Self for fluent interface
        """
        if not isinstance(instance, interface):
            raise DIContainerError(
                f"Instance {instance} is not of type {interface.__name__}"
            )

        descriptor = ServiceDescriptor(
            interface=interface, lifecycle=ServiceLifecycle.SINGLETON, instance=instance
        )

        self._services[interface] = descriptor
        return self

    def resolve(self, interface: Type) -> Any:
        """
        Resolve and instantiate a service

        Args:
            interface: Service interface to resolve

        Returns:
            Service instance

        Raises:
            DIContainerError: If service cannot be resolved
        """
        if interface not in self._services:
            # Try to auto-register if it's a concrete class
            if not inspect.isabstract(interface):
                self.register(interface)
            else:
                raise DIContainerError(f"Service {interface.__name__} not registered")

        descriptor = self._services[interface]

        # Handle different lifecycles
        if descriptor.lifecycle == ServiceLifecycle.SINGLETON:
            if descriptor.instance is None:
                descriptor.instance = self._create_instance(descriptor)
            return descriptor.instance

        elif descriptor.lifecycle == ServiceLifecycle.SCOPED:
            if interface not in self._scoped_instances:
                self._scoped_instances[interface] = self._create_instance(descriptor)
            return self._scoped_instances[interface]

        else:  # TRANSIENT
            return self._create_instance(descriptor)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """
        Create an instance of a service

        Args:
            descriptor: Service descriptor

        Returns:
            Service instance
        """
        # Use factory if available
        if descriptor.factory:
            return descriptor.factory()

        # Use implementation class
        if descriptor.implementation:
            return self._inject_constructor(descriptor.implementation)

        raise DIContainerError(f"Cannot create instance for {descriptor.interface.__name__}")

    def _inject_constructor(self, cls: Type) -> Any:
        """
        Create instance with constructor injection

        Args:
            cls: Class to instantiate

        Returns:
            Instance with dependencies injected
        """
        # Get constructor signature
        signature = inspect.signature(cls.__init__)
        params = signature.parameters

        # Prepare constructor arguments
        kwargs = {}

        for param_name, param in params.items():
            if param_name == "self":
                continue

            # Get parameter type hint
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation

                # Try to resolve the dependency
                try:
                    # Handle Optional types
                    if hasattr(param_type, "__origin__") and param_type.__origin__ is Optional:
                        param_type = param_type.__args__[0]

                    kwargs[param_name] = self.resolve(param_type)
                except DIContainerError:
                    # Use default value if available
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise DIContainerError(
                            f"Cannot resolve dependency {param_name}: {param_type} "
                            f"for {cls.__name__}"
                        )

        return cls(**kwargs)

    def inject(self, func: Callable) -> Callable:
        """
        Decorator for dependency injection into functions

        Args:
            func: Function to inject dependencies into

        Returns:
            Wrapped function with injected dependencies
        """

        def wrapper(*args, **kwargs):
            # Get function signature
            signature = inspect.signature(func)
            type_hints = get_type_hints(func)

            # Inject missing parameters
            for param_name, param_type in type_hints.items():
                if param_name not in kwargs:
                    try:
                        kwargs[param_name] = self.resolve(param_type)
                    except DIContainerError:
                        pass  # Let the function handle missing parameters

            return func(*args, **kwargs)

        return wrapper

    def create_scope(self) -> "DIScope":
        """
        Create a new scope for scoped services

        Returns:
            New scope instance
        """
        return DIScope(self)

    def clear_scoped_instances(self):
        """Clear all scoped instances"""
        self._scoped_instances.clear()

    def is_registered(self, interface: Type) -> bool:
        """
        Check if a service is registered

        Args:
            interface: Service interface

        Returns:
            True if registered
        """
        return interface in self._services

    def get_all_services(self) -> Dict[str, ServiceDescriptor]:
        """
        Get all registered services

        Returns:
            Dictionary of service names and descriptors
        """
        return {
            interface.__name__: descriptor for interface, descriptor in self._services.items()
        }


class DIScope:
    """
    Represents a scope for scoped services
    """

    def __init__(self, container: DIContainer):
        """
        Initialize scope

        Args:
            container: Parent DI container
        """
        self.container = container
        self._original_scoped = container._scoped_instances.copy()

    def __enter__(self):
        """Enter scope context"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit scope context and restore original scoped instances"""
        self.container._scoped_instances = self._original_scoped


# Global container instance
_global_container = DIContainer()


def get_container() -> DIContainer:
    """Get global DI container instance"""
    return _global_container


def register_services(container: Optional[DIContainer] = None):
    """
    Register common SubForge services

    Args:
        container: DI container (uses global if not provided)
    """
    if container is None:
        container = get_container()

    # Register core services
    from subforge.core.cache_manager import CacheManager
    from subforge.core.project_analyzer import ProjectAnalyzer
    from subforge.plugins.plugin_manager import PluginManager

    container.register(CacheManager, lifecycle=ServiceLifecycle.SINGLETON)
    container.register(ProjectAnalyzer, lifecycle=ServiceLifecycle.SINGLETON)
    container.register(PluginManager, lifecycle=ServiceLifecycle.SINGLETON)