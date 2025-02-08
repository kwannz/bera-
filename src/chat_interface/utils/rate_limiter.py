import time
import asyncio
import redis.asyncio
from typing import Optional, cast
from redis.asyncio.client import Redis


class RateLimiter:
    def __init__(
        self,
        redis_client: Optional[Redis] = None
    ):
        self._redis_client = redis_client
        # Default rate limits for different APIs
        self.limits = {
            "beratrail": 60,  # requests per minute
            "coingecko": 50,  # requests per minute
            "okx": 20,  # requests per second
            "news_monitor": 30,  # requests per minute
            "analytics": 20  # requests per minute
        }
        # Time windows in seconds
        self.windows = {
            "beratrail": 60,  # seconds
            "coingecko": 60,  # seconds
            "okx": 1,  # second
            "news_monitor": 60,  # seconds
            "analytics": 60  # seconds
        }
        # Default values for unknown services
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
            try:
                self._redis_client = await redis.asyncio.Redis.from_url(
                    "redis://localhost:6379/0",
                    decode_responses=False,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0
                )
                if not self._redis_client:
                    raise RuntimeError("Failed to initialize Redis client")

                # Verify connection and clear data
                await asyncio.wait_for(self._redis_client.ping(), timeout=5.0)
                await asyncio.wait_for(
                    self._redis_client.delete("rate_limit:*"),
                    timeout=5.0
                )
            except (asyncio.TimeoutError, redis.RedisError) as e:
                raise RuntimeError(f"Redis initialization failed: {str(e)}")
            except Exception as e:
                raise RuntimeError(
                    f"Unexpected error during Redis setup: {str(e)}"
                )

    async def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> bool:
        """检查是否超出速率限制"""
        try:
            current = int(time.time())
            # Use API-specific limits if available, otherwise use provided or default values
            limit = limit or self.limits.get(key, self.default_limit)
            window = window or self.windows.get(key, self.default_window)

            key = f"rate_limit:{key}"

            # Use Redis pipeline for atomic operations with timeout
            async with self.redis_client.pipeline() as pipe:
                # Remove old entries first
                pipe.zremrangebyscore(key, 0, current - window)
                # Get current count before adding new request
                pipe.zcard(key)
                # Add new request
                pipe.zadd(key, {str(current): current})
                pipe.expire(key, window)
                # Execute pipeline with timeout
                results = await asyncio.wait_for(
                    pipe.execute(),
                    timeout=5.0
                )

            # Check count before new request was added
            request_count = cast(int, results[1])
            return request_count < limit
        except (asyncio.TimeoutError, redis.RedisError) as e:
            raise RuntimeError(f"Rate limit check failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error during rate limit check: {str(e)}"
            )
