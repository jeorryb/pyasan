"""Custom exceptions for PyASAN."""


class PyASANError(Exception):
    """Base exception for PyASAN."""
    pass


class APIError(PyASANError):
    """Raised when the NASA API returns an error."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(APIError):
    """Raised when API key is invalid or missing."""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass


class ValidationError(PyASANError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(PyASANError):
    """Raised when configuration is invalid or missing."""
    pass
