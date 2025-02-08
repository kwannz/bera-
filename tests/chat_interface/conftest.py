import pytest
import redis
from typing import Generator
from src.chat_interface.utils.rate_limiter import RateLimiter
from src.chat_interface.services.context_service import ContextManager


@pytest.fixture
def redis_client() -> Generator[redis.Redis, None, None]:
    client = redis.Redis(host='localhost', port=6379, db=0)
    yield client
    client.flushdb()
    client.close()


@pytest.fixture
def rate_limiter(redis_client: redis.Redis) -> RateLimiter:
    return RateLimiter(redis_client)


@pytest.fixture
def context_manager(redis_client: redis.Redis) -> ContextManager:
    manager = ContextManager()
    manager.redis_client = redis_client
    return manager
