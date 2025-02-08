from websockets.legacy.server import serve
from typing import Optional, Any
from src.chat_interface.handlers.websocket_handler import WebSocketHandler


class TestWebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server: Optional[Any] = None
        # Initialize handler with required dependencies
        import redis.asyncio
        from src.chat_interface.utils.rate_limiter import RateLimiter
        from src.chat_interface.services.context_service import ContextManager
        from src.chat_interface.utils.metrics import Metrics
        from src.chat_interface.utils.circuit_breaker import CircuitBreaker
        from src.chat_interface.services.response_formatter import (
            ResponseFormatter
        )
        from src.chat_interface.services.price_tracker import PriceTracker
        from src.chat_interface.services.news_monitor import NewsMonitor
        from src.chat_interface.services.analytics_collector import (
            AnalyticsCollector
        )
        from src.ai_response.model_manager import AIModelManager

        # Create Redis client
        self.redis_client = redis.asyncio.Redis.from_url(
            "redis://localhost:6379/0",
            decode_responses=False
        )
        # Initialize services
        self.rate_limiter = RateLimiter(self.redis_client)
        self.context_manager = ContextManager(self.redis_client)
        self.metrics = Metrics()
        self.circuit_breaker = CircuitBreaker()
        self.response_formatter = ResponseFormatter()
        self.price_tracker = PriceTracker(
            self.rate_limiter, self.metrics, self.circuit_breaker
        )
        self.news_monitor = NewsMonitor(
            self.rate_limiter, self.metrics, self.circuit_breaker
        )
        self.analytics_collector = AnalyticsCollector(
            self.rate_limiter, self.metrics, self.circuit_breaker
        )
        self.model_manager = AIModelManager()
        # Create handler with all dependencies
        self.handler = WebSocketHandler(
            rate_limiter=self.rate_limiter,
            context_manager=self.context_manager,
            price_tracker=self.price_tracker,
            news_monitor=self.news_monitor,
            analytics_collector=self.analytics_collector,
            model_manager=self.model_manager,
            response_formatter=self.response_formatter
        )

    async def start(self) -> None:
        """启动测试服务器"""
        # Initialize all services
        await self.rate_limiter.initialize()
        await self.context_manager.initialize()
        await self.price_tracker.initialize()
        await self.news_monitor.initialize()
        await self.analytics_collector.initialize()
        await self.model_manager.initialize()

        # Start WebSocket server
        self.server = await serve(
            self.handler.handle_connection,
            self.host,
            self.port
        )

    async def stop(self) -> None:
        """停止测试服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # Cleanup services
        try:
            await self.redis_client.aclose()
            await self.rate_limiter.redis_client.aclose()
            await self.context_manager.redis_client.aclose()
        except Exception as e:
            print(f"Warning: Error during cleanup: {str(e)}")

    @property
    def url(self) -> str:
        """获取服务器URL"""
        return f"ws://{self.host}:{self.port}"
