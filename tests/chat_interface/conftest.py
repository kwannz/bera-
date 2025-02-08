import os
import asyncio
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


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for testing"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator[redis.asyncio.Redis, None]:
    """Create a Redis client for testing"""
    # Set test environment variables
    os.environ["BERATRAIL_API_KEY"] = "test_key"
    os.environ["OLLAMA_API_URL"] = "http://localhost:11434"
    os.environ["DEEPSEEK_API_KEY"] = "test_key"

    client = None
    try:
        client = await redis.asyncio.Redis.from_url(
            "redis://localhost:6379/0",
            decode_responses=False,
            encoding='utf-8',
            socket_timeout=5.0,
            socket_connect_timeout=5.0
        )
        if not client:
            raise RuntimeError("Failed to initialize Redis client")

        # Verify connection and clear data with timeouts
        try:
            await asyncio.wait_for(client.ping(), timeout=5.0)
            await asyncio.wait_for(client.flushdb(), timeout=5.0)
        except asyncio.TimeoutError as e:
            raise RuntimeError(f"Redis operation timed out: {str(e)}")

        yield client

    except redis.RedisError as e:
        raise RuntimeError(f"Redis initialization failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during Redis setup: {str(e)}")
    finally:
        if client:
            try:
                await asyncio.wait_for(client.aclose(), timeout=5.0)
            except Exception as e:
                print(f"Warning: Error during Redis cleanup: {str(e)}")


@pytest.fixture(scope="function")
async def rate_limiter(
    redis_client: redis.asyncio.Redis
) -> AsyncGenerator[RateLimiter, None]:
    """Create a rate limiter instance for testing"""
    limiter = RateLimiter(redis_client)
    try:
        await asyncio.wait_for(limiter.initialize(), timeout=5.0)
        yield limiter
    except asyncio.TimeoutError as e:
        raise RuntimeError(f"Rate limiter initialization timed out: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Rate limiter initialization failed: {str(e)}")


@pytest.fixture(scope="function")
async def context_manager(
    redis_client: redis.asyncio.Redis
) -> AsyncGenerator[ContextManager, None]:
    """Create a context manager instance for testing"""
    manager = ContextManager(redis_client)
    try:
        await asyncio.wait_for(manager.initialize(), timeout=5.0)
        yield manager
    except asyncio.TimeoutError as e:
        raise RuntimeError(
            f"Context manager initialization timed out: {str(e)}"
        )
    except Exception as e:
        raise RuntimeError(f"Context manager initialization failed: {str(e)}")


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
) -> AsyncGenerator[ChatHandler, None]:
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
    try:
        await asyncio.wait_for(handler.initialize(), timeout=5.0)
        yield handler
    except asyncio.TimeoutError as e:
        raise RuntimeError(f"Chat handler initialization timed out: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Chat handler initialization failed: {str(e)}")
