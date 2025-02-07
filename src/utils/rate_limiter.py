import time
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from .logging_config import get_logger, DebugCategory

@dataclass
class RateLimit:
    max_requests: int
    time_window: int
    remaining: int
    reset_time: float

class RateLimiter:
    def __init__(self, default_max_requests: int = 25, default_window: int = 7200):
        self.logger = get_logger(__name__)
        self.default_limit = RateLimit(
            max_requests=default_max_requests,
            time_window=default_window,
            remaining=default_max_requests,
            reset_time=time.time() + default_window
        )
        self.endpoints: Dict[str, RateLimit] = {}
        self.requests: List[float] = []
        
    async def acquire(self, endpoint: Optional[str] = None) -> None:
        """Check rate limit and wait if necessary
        
        Args:
            endpoint: Optional endpoint-specific rate limit to check
        """
        now = time.time()
        limit = self.endpoints.get(endpoint, self.default_limit)
        
        # Clean old requests
        self.requests = [t for t in self.requests if now - t < limit.time_window]
        
        if len(self.requests) >= limit.max_requests:
            wait_time = self.requests[0] + limit.time_window - now
            self.logger.warning(
                f"Rate limit reached, waiting {wait_time:.2f}s",
                extra={"category": DebugCategory.API.value}
            )
            await asyncio.sleep(wait_time)
            
        self.requests.append(now)
        
    def update_limits(self, headers: Dict[str, str], endpoint: Optional[str] = None) -> None:
        """Update rate limits from response headers
        
        Args:
            headers: Response headers containing rate limit information
            endpoint: Optional endpoint to update limits for
        """
        try:
            remaining = int(headers.get("x-rate-limit-remaining", "0"))
            reset_time = float(headers.get("x-rate-limit-reset", "0"))
            max_requests = int(headers.get("x-rate-limit-limit", "0"))
            
            if max_requests > 0:
                limit = RateLimit(
                    max_requests=max_requests,
                    time_window=int(reset_time - time.time()),
                    remaining=remaining,
                    reset_time=reset_time
                )
                
                if endpoint:
                    self.endpoints[endpoint] = limit
                else:
                    self.default_limit = limit
                    
                self.logger.debug(
                    f"Updated rate limits: {remaining}/{max_requests} requests remaining",
                    extra={"category": DebugCategory.API.value}
                )
                
        except (ValueError, KeyError) as e:
            self.logger.error(
                f"Failed to parse rate limit headers: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            
    def handle_429(self, retry_after: Optional[str] = None) -> float:
        """Handle 429 Too Many Requests response
        
        Args:
            retry_after: Optional Retry-After header value
            
        Returns:
            float: Number of seconds to wait before retrying
        """
        try:
            if retry_after:
                wait_time = float(retry_after)
            else:
                wait_time = 60  # Default to 60 seconds
                
            self.logger.warning(
                f"Rate limit exceeded, waiting {wait_time}s",
                extra={"category": DebugCategory.API.value}
            )
            return wait_time
            
        except ValueError as e:
            self.logger.error(
                f"Failed to parse Retry-After header: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return 60  # Default to 60 seconds
