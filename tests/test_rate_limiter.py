import pytest
import time
import asyncio
from src.utils.rate_limiter import RateLimiter, RateLimit

@pytest.fixture
def rate_limiter():
    return RateLimiter(default_max_requests=2, default_window=1)

async def test_rate_limiting(rate_limiter):
    """Test basic rate limiting functionality"""
    start_time = time.time()
    
    # First two requests should be immediate
    await rate_limiter.acquire()
    await rate_limiter.acquire()
    
    # Third request should wait
    await rate_limiter.acquire()
    
    elapsed = time.time() - start_time
    assert elapsed >= 1.0, "Rate limit not enforced"

async def test_update_limits(rate_limiter):
    """Test updating rate limits from headers"""
    headers = {
        "x-rate-limit-remaining": "50",
        "x-rate-limit-reset": str(int(time.time()) + 3600),
        "x-rate-limit-limit": "100"
    }
    
    rate_limiter.update_limits(headers)
    assert rate_limiter.default_limit.max_requests == 100
    assert rate_limiter.default_limit.remaining == 50

async def test_handle_429(rate_limiter):
    """Test handling 429 responses"""
    wait_time = rate_limiter.handle_429(retry_after="30")
    assert wait_time == 30.0
    
    # Test default wait time
    wait_time = rate_limiter.handle_429()
    assert wait_time == 60.0

async def test_endpoint_specific_limits(rate_limiter):
    """Test endpoint-specific rate limits"""
    headers = {
        "x-rate-limit-remaining": "10",
        "x-rate-limit-reset": str(int(time.time()) + 3600),
        "x-rate-limit-limit": "20"
    }
    
    rate_limiter.update_limits(headers, endpoint="/api/tweets")
    assert "/api/tweets" in rate_limiter.endpoints
    assert rate_limiter.endpoints["/api/tweets"].max_requests == 20
    assert rate_limiter.endpoints["/api/tweets"].remaining == 10
