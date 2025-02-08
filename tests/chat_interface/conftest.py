import os
from typing import AsyncGenerator
import pytest
import redis.asyncio

from src.ai_response.model_manager import AIModelManager
from src.chat_interface.handlers.api_handler import ChatHandler
from src.chat_interface.services.analytics_collector import AnalyticsCollector
from src.chat_interface.services.context_service import ContextManager
from src.chat_interface.services.news_monitor import NewsMonitor
from src.chat_interface.services.price_tracker import PriceTracker
from src.chat_interface.services.response_formatter import ResponseFormatter
from src.chat_interface.utils.circuit_breaker import CircuitBreaker
from src.chat_interface.utils.metrics import Metrics
from src.chat_interface.utils.rate_limiter import RateLimiter


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for testing"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield loop
    if loop.is_running():
        loop.stop()
    if not loop.is_closed():
        loop.close()


@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator[redis.asyncio.Redis, None]:
    """Create a Redis client for testing"""
    # Set test environment variables
    os.environ["BERATRAIL_API_KEY"] = "test_key"
    os.environ["OLLAMA_API_URL"] = "http://localhost:11434"
    os.environ["DEEPSEEK_API_KEY"] = "test_key"

    client = await redis.asyncio.Redis.from_url(
        "redis://localhost:6379/0",
        decode_responses=False,
        encoding='utf-8'
    )
    if not client:
        raise RuntimeError("Failed to initialize Redis client")

    await client.ping()  # Ensure connection is established
    await client.flushdb()  # Clear any existing data
    try:
        yield client
    finally:
        if client:
            try:
                await client.aclose()
            except Exception:
                pass


@pytest.fixture(scope="function")
async def rate_limiter(redis_client: redis.asyncio.Redis) -> RateLimiter:
    """Create a rate limiter instance for testing"""
    limiter = RateLimiter(redis_client)
    await limiter.initialize()
    return limiter


@pytest.fixture(scope="function")
async def context_manager(redis_client: redis.asyncio.Redis) -> ContextManager:
    """Create a context manager instance for testing"""
    manager = ContextManager(redis_client)
    await manager.initialize()
    return manager


@pytest.fixture
def metrics() -> Metrics:
    return Metrics()


@pytest.fixture
def circuit_breaker() -> CircuitBreaker:
    return CircuitBreaker()


@pytest.fixture
def response_formatter() -> ResponseFormatter:
    return ResponseFormatter()


@pytest.fixture(scope="function")
async def chat_handler(
    redis_client: redis.asyncio.Redis,
    rate_limiter: RateLimiter,
    context_manager: ContextManager,
    metrics: Metrics,
    circuit_breaker: CircuitBreaker,
    response_formatter: ResponseFormatter,
    monkeypatch
) -> ChatHandler:
    """创建测试用的聊天处理器"""
    # Mock responses
    async def mock_get_price_data():
        return {
            "berachain": {
                "usd": 1.23,
                "usd_24h_vol": 1000000,
                "usd_24h_change": 5.67
            }
        }

    async def mock_get_latest_news():
        return [{
            "title": "Test News",
            "content": "Test Content",
            "date": "2024-02-08"
        }]

    async def mock_analyze_sentiment():
        return {
            "sentiment": "positive",
            "confidence": 0.8
        }

    async def mock_generate_content(*args, **kwargs):
        return "AI generated response for testing"

    # Initialize model manager with mock
    model_manager = AIModelManager()
    await model_manager.initialize()
    monkeypatch.setattr(
        model_manager, "generate_content", mock_generate_content
    )

    # Initialize services with dependencies and mocks
    price_tracker = PriceTracker(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    await price_tracker.initialize()
    monkeypatch.setattr(price_tracker, "get_price_data", mock_get_price_data)

    news_monitor = NewsMonitor(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    await news_monitor.initialize()
    monkeypatch.setattr(news_monitor, "get_latest_news", mock_get_latest_news)

    analytics_collector = AnalyticsCollector(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    await analytics_collector.initialize()
    monkeypatch.setattr(
        analytics_collector, "analyze_market_sentiment", mock_analyze_sentiment
    )

    # Create and initialize handler
    handler = ChatHandler(
        rate_limiter=rate_limiter,
        context_manager=context_manager,
        price_tracker=price_tracker,
        news_monitor=news_monitor,
        analytics_collector=analytics_collector,
        model_manager=model_manager,
        response_formatter=response_formatter
    )
    await handler.initialize()
    return handler
