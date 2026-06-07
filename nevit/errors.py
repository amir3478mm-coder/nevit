"""Custom exceptions for Nevit library."""


class NevitError(Exception):
    """Base exception for all Nevit errors."""
    pass


class TokenInvalidError(NevitError):
    """Raised when the bot token is invalid."""
    pass


class ChatNotFoundError(NevitError):
    """Raised when a chat is not found."""
    pass


class UserNotFoundError(NevitError):
    """Raised when a user is not found."""
    pass


class PermissionDeniedError(NevitError):
    """Raised when the bot doesn't have permission."""
    pass


class RateLimitError(NevitError):
    """Raised when rate limit is exceeded."""
    pass


class InvalidParameterError(NevitError):
    """Raised when a parameter is invalid."""
    pass


class NetworkError(NevitError):
    """Raised when a network error occurs."""
    pass