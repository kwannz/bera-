from typing import Optional, Tuple
from .logging_config import get_logger, DebugCategory
from .rate_limiter import RateLimitStrategy, RateLimit
from .errors import RetryAction, RateLimitError, NetworkError, AuthenticationError

class ErrorHandler:
    def __init__(self, rate_limit_strategy: RateLimitStrategy):
        self.rate_limit_strategy = rate_limit_strategy
        self.logger = get_logger(__name__)
        
    async def handle_error(
        self,
        error: Exception,
        context: str,
        retry_count: int = 0
    ) -> tuple[RetryAction, float]:
        """Handle Twitter API errors with proper retry strategy
        
        Args:
            error: The exception that occurred
            context: Description of where the error occurred
            retry_count: Number of retries attempted
            
        Returns:
            tuple[RetryAction, float]: Action to take and wait time in seconds
        """
        if isinstance(error, RateLimitError):
            try:
                wait_time = await self.rate_limit_strategy.handle_rate_limit(
                    retry_count
                )
                self.logger.warning(
                    f"Rate limit hit in {context}, waiting {wait_time}s",
                    extra={"category": DebugCategory.API.value}
                )
                return RetryAction.WAIT_AND_RETRY, wait_time
            except RateLimitError:
                self.logger.error(
                    f"Max retries exceeded in {context}",
                    extra={"category": DebugCategory.API.value}
                )
                return RetryAction.ABORT, 0
            
        if isinstance(error, NetworkError):
            self.logger.error(
                f"Network error in {context}: {str(error)}",
                extra={"category": DebugCategory.API.value}
            )
            return RetryAction.RETRY_IMMEDIATELY, 0
            
        if isinstance(error, AuthenticationError):
            self.logger.error(
                f"Authentication error in {context}",
                extra={"category": DebugCategory.API.value}
            )
            return RetryAction.ABORT, 0
            
        # Unknown errors
        self.logger.error(
            f"Unexpected error in {context}: {error.__class__.__name__}",
            extra={"category": DebugCategory.API.value}
        )
        return RetryAction.ABORT, 0
