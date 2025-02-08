from enum import Enum, auto

class RetryAction(Enum):
    RETRY_IMMEDIATELY = auto()
    WAIT_AND_RETRY = auto()
    ABORT = auto()

class APIError(Exception):
    """Base class for API-related errors"""
    pass

class RateLimitError(APIError):
    """Raised when rate limits are hit"""
    pass

class NetworkError(APIError):
    """Raised when network issues occur"""
    pass

class AuthenticationError(APIError):
    """Raised when authentication fails"""
    pass
