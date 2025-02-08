import time
import redis.asyncio
from typing import Optional, cast
from redis.asyncio.client import Redis


class RateLimiter:
    def __init__(
        self,
        redis_client: Optional[Redis] = None
    ):
        self._redis_client = redis_client
        self.default_limit = 60  # requests per minute
        self.default_window = 60  # window in seconds

    @property
    def redis_client(self) -> Redis:
        """Get the Redis client instance"""
        if not self._redis_client:
            raise RuntimeError("Redis client not initialized")
        return self._redis_client

    async def initialize(self) -> None:
        """Initialize the rate limiter"""
        if not self._redis_client:
            self._redis_client = await redis.asyncio.Redis.from_url(
                "redis://localhost:6379/0",
                decode_responses=False
            )
            if not self._redis_client:
                raise RuntimeError("Failed to initialize Redis client")
            # Verify Redis connection
            await self._redis_client.ping()
            # Clear any existing rate limit data
            await self._redis_client.delete("rate_limit:*")

    async def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> bool:
        """检查是否超出速率限制"""
        # Check rate limit
        current = int(time.time())
        limit = limit or self.default_limit
        window = window or self.default_window

        key = f"rate_limit:{key}"

        # Use Redis pipeline for atomic operations
        async with self.redis_client.pipeline() as pipe:
            # Remove old entries first
            pipe.zremrangebyscore(key, 0, current - window)
            # Get current count before adding new request
            pipe.zcard(key)
            # Add new request
            pipe.zadd(key, {str(current): current})
            pipe.expire(key, window)
            results = await pipe.execute()

        # Check count before new request was added
        request_count = cast(int, results[1])
        return request_count < limit
