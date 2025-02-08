import pytest
from src.chat_interface.services.dex_price_tracker import (
    PancakeSwapTracker,
    UniswapTracker,
    JupiterTracker
)
from src.chat_interface.utils.rate_limiter import RateLimiter
from src.chat_interface.utils.circuit_breaker import CircuitBreaker
from src.chat_interface.utils.metrics import Metrics


# Using rate_limiter fixture from conftest.py


@pytest.fixture
def metrics():
    """Create a metrics instance for testing"""
    return Metrics()


@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker instance for testing"""
    return CircuitBreaker()


class MockResponse:
    def __init__(self, data=None, status=None):
        self._data = data or {"price": 1.23, "volume24h": 1000000, "priceChange24h": 5.67}
        self._status = status or 200

    async def json(self):
        if self._status == 429:  # Rate limited
            return {}
        return self._data

    @property
    def status(self):
        return self._status

class MockClientSession:
    def __init__(self):
        self._response = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, *args, **kwargs):
        class AsyncResponse:
            async def __aenter__(self_):
                return MockResponse()
            async def __aexit__(self_, exc_type, exc_val, exc_tb):
                pass
        return AsyncResponse()

@pytest.mark.asyncio
async def test_pancakeswap_price(
    rate_limiter,
    metrics,
    circuit_breaker,
    monkeypatch
):
    """Test PancakeSwap price data retrieval"""
    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", MockClientSession)
    
    tracker = PancakeSwapTracker(rate_limiter, metrics, circuit_breaker)
    data = await tracker.get_price_data()
    
    assert isinstance(data, dict)
    assert "price" in data
    assert isinstance(data["price"], (int, float))
    assert data["price"] == 1.23
    assert isinstance(data["price"], (int, float))
    assert "volume_24h" in data
    assert isinstance(data["volume_24h"], (int, float))
    assert "price_change_24h" in data
    assert isinstance(data["price_change_24h"], (int, float))


@pytest.mark.asyncio
async def test_uniswap_price(
    rate_limiter,
    metrics,
    circuit_breaker,
    monkeypatch
):
    """Test Uniswap price data retrieval"""
    class UniswapMockResponse(MockResponse):
        async def json(self):
            return {"price": 1.45, "volume24h": 2000000, "priceChange24h": 3.21}

    class UniswapMockClientSession(MockClientSession):
        def get(self, *args, **kwargs):
            class AsyncResponse:
                async def __aenter__(self_):
                    return UniswapMockResponse()
                async def __aexit__(self_, exc_type, exc_val, exc_tb):
                    pass
            return AsyncResponse()

    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", UniswapMockClientSession)
    
    tracker = UniswapTracker(rate_limiter, metrics, circuit_breaker)
    data = await tracker.get_price_data()
    
    assert isinstance(data, dict)
    assert "price" in data
    assert isinstance(data["price"], (int, float))
    assert data["price"] == 1.45
    assert isinstance(data["price"], (int, float))
    assert "volume_24h" in data
    assert isinstance(data["volume_24h"], (int, float))
    assert "price_change_24h" in data
    assert isinstance(data["price_change_24h"], (int, float))


@pytest.mark.asyncio
async def test_jupiter_price(
    rate_limiter,
    metrics,
    circuit_breaker,
    monkeypatch
):
    """Test Jupiter price data retrieval"""
    class JupiterMockResponse(MockResponse):
        async def json(self):
            return {"price": 1.67, "volume24h": 3000000, "priceChange24h": 2.34}

    class JupiterMockClientSession(MockClientSession):
        def get(self, *args, **kwargs):
            class AsyncResponse:
                async def __aenter__(self_):
                    return JupiterMockResponse()
                async def __aexit__(self_, exc_type, exc_val, exc_tb):
                    pass
            return AsyncResponse()

    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", JupiterMockClientSession)
    
    tracker = JupiterTracker(rate_limiter, metrics, circuit_breaker)
    data = await tracker.get_price_data()
    
    assert isinstance(data, dict)
    assert "price" in data
    assert isinstance(data["price"], (int, float))
    assert data["price"] == 1.67
    assert isinstance(data["price"], (int, float))
    assert "volume_24h" in data
    assert isinstance(data["volume_24h"], (int, float))
    assert "price_change_24h" in data
    assert isinstance(data["price_change_24h"], (int, float))


@pytest.mark.asyncio
async def test_rate_limit_handling(
    rate_limiter,
    metrics,
    circuit_breaker,
    monkeypatch
):
    """Test rate limit handling"""
    class RateLimitMockResponse(MockResponse):
        def __init__(self, rate_limited=False):
            super().__init__(
                data={} if rate_limited else {"price": 1.23, "volume24h": 1000000, "priceChange24h": 5.67},
                status=429 if rate_limited else 200
            )

    class RateLimitMockClientSession(MockClientSession):
        _request_count = 0  # Class variable to track requests across instances

        def __init__(self, rate_limiter):
            super().__init__()
            self.rate_limiter = rate_limiter

        def get(self, *args, **kwargs):
            class AsyncResponse:
                def __init__(self_, rate_limiter):
                    self_.rate_limiter = rate_limiter

                async def __aenter__(self_):
                    # Check rate limit before returning response
                    if not await self_.rate_limiter.check_rate_limit("pancakeswap", limit=100, window=60):
                        # Ensure we consume a token even when rate limited
                        await self_.rate_limiter.check_rate_limit("pancakeswap", limit=100, window=60)
                        return RateLimitMockResponse(rate_limited=True)
                    RateLimitMockClientSession._request_count += 1
                    if RateLimitMockClientSession._request_count > 100:
                        return RateLimitMockResponse(rate_limited=True)
                    return RateLimitMockResponse(rate_limited=False)

                async def __aexit__(self_, exc_type, exc_val, exc_tb):
                    pass
            return AsyncResponse(self.rate_limiter)

    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: RateLimitMockClientSession(rate_limiter))
    
    tracker = PancakeSwapTracker(rate_limiter, metrics, circuit_breaker)
    
    # Make multiple requests to trigger rate limit
    request_count = 0
    for _ in range(110):  # Over the 100 requests/minute limit
        data = await tracker.get_price_data()
        if data:  # Only count successful requests
            request_count += 1
    
    # Verify we hit the rate limit
    assert request_count <= 100, f"Made {request_count} requests when limit is 100"
    
    # Next request should return empty dict due to rate limit
    data = await tracker.get_price_data()
    assert data == {}, "Rate limited request should return empty dict"


@pytest.mark.asyncio
async def test_error_handling(
    rate_limiter,
    metrics,
    circuit_breaker,
    monkeypatch
):
    """Test error handling"""
    class ErrorMockResponse(MockResponse):
        async def json(self):
            raise aiohttp.ClientError("Mock error")
        @property
        def status(self):
            return 500

    class ErrorMockClientSession(MockClientSession):
        def get(self, *args, **kwargs):
            class AsyncResponse:
                async def __aenter__(self_):
                    return ErrorMockResponse()
                async def __aexit__(self_, exc_type, exc_val, exc_tb):
                    pass
            return AsyncResponse()

    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", ErrorMockClientSession)
    
    tracker = PancakeSwapTracker(rate_limiter, metrics, circuit_breaker)
    data = await tracker.get_price_data()
    
    assert data == {}
