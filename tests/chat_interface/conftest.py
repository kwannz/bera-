import pytest
import redis
from typing import Generator
from src.chat_interface.utils.rate_limiter import RateLimiter
from src.chat_interface.utils.metrics import Metrics
from src.chat_interface.utils.circuit_breaker import CircuitBreaker
from src.chat_interface.services.context_service import ContextManager
from src.chat_interface.services.response_formatter import ResponseFormatter
from src.chat_interface.handlers.api_handler import ChatHandler
from src.chat_interface.services.price_tracker import PriceTracker
from src.chat_interface.services.news_monitor import NewsMonitor
from src.chat_interface.services.analytics_collector import AnalyticsCollector
from src.ai_response.model_manager import AIModelManager


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


@pytest.fixture
def metrics() -> Metrics:
    return Metrics()


@pytest.fixture
def circuit_breaker() -> CircuitBreaker:
    return CircuitBreaker()


@pytest.fixture
def response_formatter() -> ResponseFormatter:
    return ResponseFormatter()


@pytest.fixture
def chat_handler(
    redis_client: redis.Redis,
    rate_limiter: RateLimiter,
    context_manager: ContextManager,
    metrics: Metrics,
    circuit_breaker: CircuitBreaker,
    response_formatter: ResponseFormatter
) -> ChatHandler:
    """创建测试用的聊天处理器"""
    price_tracker = PriceTracker(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    news_monitor = NewsMonitor(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    analytics_collector = AnalyticsCollector(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    model_manager = AIModelManager()

    handler = ChatHandler(
        rate_limiter=rate_limiter,
        context_manager=context_manager,
        price_tracker=price_tracker,
        news_monitor=news_monitor,
        analytics_collector=analytics_collector,
        model_manager=model_manager,
        response_formatter=response_formatter
    )
    return handler
