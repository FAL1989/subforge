"""
Context Engineering Module - Modular components for context management
"""

from .types import (
    ProjectContext,
    TechnicalContext,
    Example,
    Pattern,
    ValidationGate,
    PreviousOutput,
    ContextPackageDict,
)

from .exceptions import (
    ContextError,
    InvalidProfileError,
    TemplateNotFoundError,
    ValidationError,
    ContextGenerationError,
)

from .validators import (
    validate_project_profile,
    validate_context_package_data,
)

from .builder import ContextBuilder, ContextPackage
from .repository import ExampleRepository
from .patterns import PatternExtractor, ContextLevel
from .enricher import ContextEnricher
from .cache import CachedContextManager

__all__ = [
    # Types
    "ProjectContext",
    "TechnicalContext",
    "Example",
    "Pattern",
    "ValidationGate",
    "PreviousOutput",
    "ContextPackageDict",
    # Exceptions
    "ContextError",
    "InvalidProfileError",
    "TemplateNotFoundError",
    "ValidationError",
    "ContextGenerationError",
    # Validators
    "validate_project_profile",
    "validate_context_package_data",
    # Core Classes
    "ContextBuilder",
    "ContextPackage",
    "ExampleRepository",
    "PatternExtractor",
    "ContextLevel",
    "ContextEnricher",
    "CachedContextManager",
]