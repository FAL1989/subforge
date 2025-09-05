#!/usr/bin/env python3
"""
Exception definitions for Context Engineering module
Provides specific exception types for better error handling
"""


class ContextError(Exception):
    """Base exception for context engineering errors"""
    pass


class InvalidProfileError(ContextError):
    """Raised when project profile is invalid or incomplete"""
    pass


class TemplateNotFoundError(ContextError):
    """Raised when a required template is not found"""
    pass


class ValidationError(ContextError):
    """Raised when context validation fails"""
    pass


class ContextGenerationError(ContextError):
    """Raised when context generation fails"""
    pass


class InvalidContextLevelError(ContextError):
    """Raised when an invalid context level is specified"""
    pass


class PatternExtractionError(ContextError):
    """Raised when pattern extraction fails"""
    pass


class ExampleNotFoundError(ContextError):
    """Raised when no suitable examples are found"""
    pass