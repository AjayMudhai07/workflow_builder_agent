"""
Custom exceptions for IRA Workflow Builder.

This module defines all custom exception classes used throughout the application.
"""


class IRAException(Exception):
    """Base exception for all IRA Workflow Builder errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class WorkflowException(IRAException):
    """Exception raised for workflow execution errors."""

    pass


class AgentException(IRAException):
    """Exception raised for agent-related errors."""

    pass


class StorageException(IRAException):
    """Exception raised for storage operation errors."""

    pass


class ValidationException(IRAException):
    """Exception raised for validation errors."""

    pass


class ExecutionException(IRAException):
    """Exception raised for code execution errors."""

    pass


class ConfigurationException(IRAException):
    """Exception raised for configuration errors."""

    pass


class AuthenticationException(IRAException):
    """Exception raised for authentication errors."""

    pass


class RateLimitException(IRAException):
    """Exception raised when rate limits are exceeded."""

    pass
