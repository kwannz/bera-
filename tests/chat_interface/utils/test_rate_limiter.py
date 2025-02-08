import pytest
from src.chat_interface.utils.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_init(rate_limiter: RateLimiter):
    assert rate_limiter.default_limit == 60
    assert rate_limiter.default_window == 60


@pytest.mark.asyncio
async def test_rate_limit_not_exceeded(rate_limiter: RateLimiter):
    # First request should be allowed
    assert await rate_limiter.check_rate_limit("test") is True


@pytest.mark.asyncio
async def test_rate_limit_exceeded(rate_limiter: RateLimiter):
    # Set a very low limit
    limit = 1
    window = 60

    # First request should be allowed
    assert await rate_limiter.check_rate_limit("test", limit, window) is True

    # Second request should be blocked
    assert await rate_limiter.check_rate_limit("test", limit, window) is False


@pytest.mark.asyncio
async def test_rate_limit_different_keys(rate_limiter: RateLimiter):
    limit = 1
    window = 60

    # Both requests should be allowed as they use different keys
    assert await rate_limiter.check_rate_limit("test1", limit, window) is True
    assert await rate_limiter.check_rate_limit("test2", limit, window) is True
