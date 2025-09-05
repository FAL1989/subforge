#!/usr/bin/env python3
"""
Strategy Registry for PRP Generation
Manages registration and retrieval of PRP generation strategies
"""

from pathlib import Path
from typing import Dict, Optional, Type

from ..prp_template_loader import PRPTemplateLoader
from .base import IPRPStrategy, PRPType
from .factory_strategy import FactoryAnalysisStrategy
from .generation_strategy import GenerationStrategy
from .validation_strategy import ValidationStrategy


class PRPStrategyRegistry:
    """
    Registry for managing PRP generation strategies
    
    This class provides a centralized location for registering and retrieving
    different PRP generation strategies based on PRP type.
    """
    
    def __init__(self, workspace_dir: Path, template_loader: Optional[PRPTemplateLoader] = None):
        """
        Initialize the strategy registry
        
        Args:
            workspace_dir: Path to workspace directory
            template_loader: Optional template loader for strategies
        """
        self.workspace_dir = workspace_dir
        self.template_loader = template_loader
        self._strategies: Dict[PRPType, IPRPStrategy] = {}
        self._strategy_classes: Dict[PRPType, Type[IPRPStrategy]] = {}
        
        # Register default strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register the default set of strategies"""
        # Register strategy classes
        self._strategy_classes[PRPType.FACTORY_ANALYSIS] = FactoryAnalysisStrategy
        self._strategy_classes[PRPType.FACTORY_GENERATION] = GenerationStrategy
        self._strategy_classes[PRPType.VALIDATION_COMPREHENSIVE] = ValidationStrategy
        
        # Note: We'll instantiate strategies lazily to avoid unnecessary resource allocation
    
    def register(self, prp_type: PRPType, strategy: IPRPStrategy):
        """
        Register a strategy for a specific PRP type
        
        Args:
            prp_type: Type of PRP this strategy generates
            strategy: Strategy instance to register
        """
        self._strategies[prp_type] = strategy
    
    def register_class(self, prp_type: PRPType, strategy_class: Type[IPRPStrategy]):
        """
        Register a strategy class for lazy instantiation
        
        Args:
            prp_type: Type of PRP this strategy generates
            strategy_class: Strategy class to register
        """
        self._strategy_classes[prp_type] = strategy_class
    
    def get_strategy(self, prp_type: PRPType) -> IPRPStrategy:
        """
        Get strategy for a specific PRP type
        
        Args:
            prp_type: Type of PRP to get strategy for
            
        Returns:
            Strategy instance for the given type
            
        Raises:
            ValueError: If no strategy registered for the type
        """
        # Check if strategy is already instantiated
        if prp_type in self._strategies:
            return self._strategies[prp_type]
        
        # Check if we have a class registered for lazy instantiation
        if prp_type in self._strategy_classes:
            strategy_class = self._strategy_classes[prp_type]
            strategy = strategy_class(self.workspace_dir, self.template_loader)
            self._strategies[prp_type] = strategy
            return strategy
        
        raise ValueError(f"No strategy registered for PRP type: {prp_type.value}")
    
    def has_strategy(self, prp_type: PRPType) -> bool:
        """
        Check if a strategy is registered for a PRP type
        
        Args:
            prp_type: Type to check
            
        Returns:
            True if strategy is registered
        """
        return prp_type in self._strategies or prp_type in self._strategy_classes
    
    def list_registered_types(self) -> list[PRPType]:
        """
        List all registered PRP types
        
        Returns:
            List of registered PRP types
        """
        registered = set(self._strategies.keys()) | set(self._strategy_classes.keys())
        return sorted(registered, key=lambda x: x.value)
    
    def unregister(self, prp_type: PRPType):
        """
        Unregister a strategy
        
        Args:
            prp_type: Type to unregister
        """
        self._strategies.pop(prp_type, None)
        self._strategy_classes.pop(prp_type, None)
    
    def clear(self):
        """Clear all registered strategies"""
        self._strategies.clear()
        self._strategy_classes.clear()
    
    def reload_defaults(self):
        """Reload default strategies (useful for testing)"""
        self.clear()
        self._register_default_strategies()


def create_strategy_registry(
    workspace_dir: Path,
    template_loader: Optional[PRPTemplateLoader] = None
) -> PRPStrategyRegistry:
    """
    Factory function to create a configured strategy registry
    
    Args:
        workspace_dir: Path to workspace directory
        template_loader: Optional template loader
        
    Returns:
        Configured strategy registry
    """
    return PRPStrategyRegistry(workspace_dir, template_loader)