import time
import redis
from typing import Optional


class RateLimiter:
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None
    ):
        self.redis = redis_client or redis.Redis(
            host='localhost',
            port=6379,
            db=0
        )
        self.default_limit = 60  # requests per minute
        self.default_window = 60  # window in seconds

    async def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> bool:
        """检查是否超出速率限制"""
        current = int(time.time())
        limit = limit or self.default_limit
        window = window or self.default_window

        key = f"rate_limit:{key}"

        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(current): current})
        pipe.zremrangebyscore(key, 0, current - window)
        pipe.zcard(key)
        pipe.expire(key, window)
        results = pipe.execute()

        request_count = results[2]
        return request_count <= limit
