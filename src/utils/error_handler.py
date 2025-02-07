from enum import Enum, auto
from typing import Optional
from .logging_config import get_logger, DebugCategory

class RetryAction(Enum):
    RETRY_IMMEDIATELY = auto()
    WAIT_AND_RETRY = auto()
    ABORT = auto()

class TwitterError(Exception):
    """Base class for Twitter-related errors"""
    pass

class RateLimitError(TwitterError):
    """Raised when rate limits are hit"""
    pass

class NetworkError(TwitterError):
    """Raised when network issues occur"""
    pass

class AuthenticationError(TwitterError):
    """Raised when authentication fails"""
    pass

class ErrorHandler:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def handle_error(self, error: Exception, context: str) -> RetryAction:
        """Handle different types of errors with proper logging
        
        Args:
            error: The exception that occurred
            context: Description of where the error occurred
            
        Returns:
            RetryAction: Recommended action to take
        """
        if isinstance(error, RateLimitError):
            self.logger.warning(
                f"Rate limit hit in {context}: {str(error)}",
                extra={"category": DebugCategory.API.value}
            )
            return RetryAction.WAIT_AND_RETRY
            
        if isinstance(error, NetworkError):
            self.logger.error(
                f"Network error in {context}: {str(error)}",
                extra={"category": DebugCategory.API.value}
            )
            return RetryAction.RETRY_IMMEDIATELY
            
        if isinstance(error, AuthenticationError):
            self.logger.error(
                f"Authentication error in {context}",
                extra={"category": DebugCategory.API.value}
            )
            return RetryAction.ABORT
            
        # Unknown errors
        self.logger.error(
            f"Unexpected error in {context}: {error.__class__.__name__}",
            extra={"category": DebugCategory.API.value}
        )
        return RetryAction.ABORT
