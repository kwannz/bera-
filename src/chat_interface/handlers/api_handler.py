from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from typing import Dict, Optional, List, Any, Union
import asyncio
import redis.asyncio
from redis.asyncio.client import Redis
from ..utils.logging_config import get_logger, DebugCategory
from ..services.price_tracker import PriceTracker
from ..services.news_monitor import NewsMonitor
from ..services.analytics_collector import AnalyticsCollector
from ..services.context_service import ContextManager
from ...ai_response.model_manager import (
    AIModelManager,
    ContentType as ModelContentType
)
from ..utils.rate_limiter import RateLimiter
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.metrics import Metrics
from ..services.response_formatter import (
    ContentType as FormatterContentType,
    ResponseFormatter
)
from typing_extensions import TypedDict


class MarketData(TypedDict, total=False):
    price: str
    volume: str
    change: str
    error: str


class NewsItem(TypedDict):
    title: str
    summary: str
    date: str
    source: str


NewsData = List[NewsItem]


class SentimentData(TypedDict):
    sentiment: str
    confidence: float


class ChatHandler:
    """聊天处理器，处理所有聊天相关的请求"""
    def __init__(
        self,
        rate_limiter: RateLimiter,
        context_manager: ContextManager,
        price_tracker: PriceTracker,
        news_monitor: NewsMonitor,
        analytics_collector: AnalyticsCollector,
        model_manager: AIModelManager,
        response_formatter: ResponseFormatter
    ):
        self.rate_limiter = rate_limiter
        self.context_manager = context_manager
        self.price_tracker = price_tracker
        self.news_monitor = news_monitor
        self.analytics_collector = analytics_collector
        self.model_manager = model_manager
        self.response_formatter = response_formatter
        self.logger = get_logger(__name__)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the chat handler and verify all dependencies"""
        if self._initialized:
            return
        # Verify all dependencies are properly initialized
        if not self.rate_limiter or not self.context_manager:
            raise RuntimeError("Required dependencies not provided")
        self._initialized = True

    async def process_message(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """处理用户消息"""
        try:
            # Check rate limit
            rate_limit_key = f"chat_{session_id}"
            if not await self.rate_limiter.check_rate_limit(rate_limit_key):
                self.logger.warning(
                    "Rate limit exceeded for session",
                    extra={
                        "category": DebugCategory.API.value,
                        "session_id": session_id
                    }
                )
                return {
                    "error": "Rate limit exceeded",
                    "retry_after": self.rate_limiter.default_window
                }

            # Get context for AI response
            context = await self.context_manager.get_context(session_id)

            # Get data in parallel
            tasks = [
                self.price_tracker.get_price_data(),
                self.news_monitor.get_latest_news(),
                self.analytics_collector.analyze_market_sentiment()  # noqa
            ]
            # Get all data in parallel
            results = await asyncio.gather(*tasks)
            market_data = results[0]
            news_data = results[1]
            sentiment_data = results[2]

            # Generate AI response
            prompt_data = {
                "market_data": self._format_market_data(market_data),
                "news": self._format_news_data(news_data),
                "sentiment": self._format_sentiment_data(sentiment_data),
                "context": context,
                "message": message
            }

            ai_response = await self.model_manager.generate_content(
                ModelContentType.MARKET,
                prompt_data,
                max_length=500
            )

            # Format response
            response = {
                "ai_response": ai_response,
                "market_data": self._format_market_data(market_data),
                "news": self._format_news_data(news_data),
                "sentiment": self._format_sentiment_data(sentiment_data)
            }

            # Update context
            await self.context_manager.add_message(
                session_id,
                {"role": "user", "content": message}
            )
            await self.context_manager.add_message(
                session_id,
                {"role": "assistant", "content": str(ai_response)}
            )

            return response
        except Exception as e:
            self.logger.error(
                f"Error processing message: {str(e)}",
                extra={
                    "category": DebugCategory.API.value,
                    "session_id": session_id
                }
            )
            return {
                "error": "Internal server error",
                "message": "服务器内部错误，请稍后再试"
            }

            # Get data in parallel
            tasks = [
                self.model_manager.generate_content(
                    ModelContentType.MARKET,
                    {"message": message, "context": context},
                    max_length=280
                ),
                self.price_tracker.get_price_data(),
                self.news_monitor.get_latest_news(),
                self.analytics_collector.analyze_market_sentiment()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            ai_response, price_data, news_data, sentiment = results

            # Format response with validation and error handling
            market_data = self._format_market_data(price_data)
            news_list = self._format_news_data(news_data)
            sentiment_data = self._format_sentiment_data(sentiment)

            response = {
                "ai_response": (
                    "Unable to generate response"
                    if isinstance(ai_response, Exception)
                    else str(ai_response)
                ),
                "market_data": self.response_formatter.format_response(
                    market_data,
                    FormatterContentType.MARKET
                ),
                "news": self.response_formatter.format_response(
                    news_list,
                    FormatterContentType.NEWS
                ),
                "sentiment": sentiment_data
            }

            # Update context
            await self.context_manager.add_message(
                session_id,
                {"role": "user", "content": message}
            )
            await self.context_manager.add_message(
                session_id,
                {"role": "assistant", "content": response}
            )

            return response

        except Exception as e:
            self.logger.error(
                f"Error processing message: {str(e)}",
                extra={
                    "category": DebugCategory.API.value,
                    "session_id": session_id
                }
            )
            return {
                "error": "Internal server error",
                "message": "服务器内部错误，请稍后再试"
            }

    def _format_market_data(self, price_data: Any) -> Dict[str, str]:
        """格式化市场数据"""
        market_data: Dict[str, str] = {"error": "Unexpected error"}
        if isinstance(price_data, Exception):
            error_msg = str(price_data)
            self.logger.error(
                f"Price data error: {error_msg}",
                extra={"category": DebugCategory.API.value}
            )
            if "Rate limit exceeded" in error_msg:
                market_data = {"error": "Rate limit exceeded"}
            else:
                market_data = {"error": "Unexpected error"}
        else:
            try:
                if (not isinstance(price_data, BaseException) and
                        isinstance(price_data, dict) and
                        "berachain" in price_data):
                    berachain_data = price_data["berachain"]
                    market_data = {
                        "📈 当前价格": f"${berachain_data['usd']}",
                        "💰 24小时交易量": f"${berachain_data['usd_24h_vol']:,}",
                        "📊 24小时涨跌": f"{berachain_data['usd_24h_change']:+}%"
                    }
                else:
                    self.logger.error(
                        "Invalid market data format",
                        extra={"category": DebugCategory.VALIDATION.value}
                    )
                    market_data = {"error": "Invalid data format"}
            except Exception as e:
                self.logger.error(
                    f"Market data processing error: {str(e)}",
                    extra={"category": DebugCategory.API.value}
                )
                market_data = {"error": "Data processing error"}
        return market_data

    def _format_news_data(self, news_data: Any) -> List[Dict[str, str]]:
        """格式化新闻数据"""
        news_list: List[Dict[str, str]] = []
        if isinstance(news_data, Exception):
            self.logger.error(
                f"News data error: {str(news_data)}",
                extra={"category": DebugCategory.API.value}
            )
        elif (not isinstance(news_data, BaseException) and
              validate_news_data(news_data)):
            news_list = [
                {
                    "title": str(item["title"]),
                    "summary": str(
                        item["summary"]
                    ),
                    "date": str(item["date"]),
                    "source": str(
                        item["source"]
                    )
                }
                for item in news_data
            ]
        else:
            self.logger.error(
                "Invalid news data format",
                extra={"category": DebugCategory.VALIDATION.value}
            )
        return news_list

    def _format_sentiment_data(
        self,
        sentiment: Any
    ) -> Dict[str, Union[str, float]]:
        """格式化情绪数据"""
        sentiment_data: Dict[str, Union[str, float]] = {
            "sentiment": "neutral",
            "confidence": 0.0
        }
        if isinstance(sentiment, Exception):
            self.logger.error(
                f"Sentiment data error: {str(sentiment)}",
                extra={"category": DebugCategory.API.value}
            )
        elif (not isinstance(sentiment, BaseException) and
              validate_sentiment_data(sentiment)):
            sentiment_data = {
                "sentiment": str(sentiment["sentiment"]),
                "confidence": float(sentiment["confidence"])
            }
        else:
            self.logger.error(
                "Invalid sentiment data format",
                extra={"category": DebugCategory.VALIDATION.value}
            )
        return sentiment_data


# Initialize global variables
price_tracker: Optional[PriceTracker] = None
news_monitor: Optional[NewsMonitor] = None
analytics_collector: Optional[AnalyticsCollector] = None
model_manager: Optional[AIModelManager] = None
response_formatter: Optional[ResponseFormatter] = None
chat_handler: Optional[ChatHandler] = None

# Initialize FastAPI app
app = FastAPI()

# Initialize base services
redis_client: Optional[Redis] = None
rate_limiter = RateLimiter()
logger = get_logger(__name__)
context_manager = ContextManager()
metrics = Metrics()
circuit_breaker = CircuitBreaker()


# Initialize Redis client
async def initialize_redis():
    """Initialize Redis client"""
    global redis_client
    redis_client = await redis.asyncio.Redis.from_url(
        "redis://localhost:6379/0",
        decode_responses=False
    )
    if not redis_client:
        raise RuntimeError("Failed to initialize Redis client")
    return redis_client


async def initialize_services():
    """Initialize all services required for the chat interface"""
    await rate_limiter.initialize()
    await context_manager.initialize()

    price_tracker = PriceTracker(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    await price_tracker.initialize()

    news_monitor = NewsMonitor(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    await news_monitor.initialize()

    analytics_collector = AnalyticsCollector(
        rate_limiter=rate_limiter,
        metrics=metrics,
        circuit_breaker=circuit_breaker
    )
    await analytics_collector.initialize()

    model_manager = AIModelManager()
    await model_manager.initialize()

    return (
        price_tracker,
        news_monitor,
        analytics_collector,
        model_manager,
        ResponseFormatter()
    )


@app.on_event("startup")
async def startup_event():
    """Initialize services on FastAPI startup"""
    global redis_client, price_tracker, news_monitor
    global analytics_collector, model_manager, response_formatter, chat_handler

    # Initialize Redis first
    redis_client = await initialize_redis()

    # Update services with Redis client
    rate_limiter._redis_client = redis_client
    context_manager._redis_client = redis_client

    # Initialize all services
    await rate_limiter.initialize()
    await context_manager.initialize()

    # Initialize remaining services
    (
        price_tracker,
        news_monitor,
        analytics_collector,
        model_manager,
        response_formatter
    ) = await initialize_services()
    chat_handler = await initialize_chat_handler()


# Initialize chat handler after services are ready
async def initialize_chat_handler():
    """Initialize chat handler with all required services"""
    global chat_handler
    chat_handler = ChatHandler(
        rate_limiter=rate_limiter,
        context_manager=context_manager,
        price_tracker=price_tracker,
        news_monitor=news_monitor,
        analytics_collector=analytics_collector,
        model_manager=model_manager,
        response_formatter=response_formatter
    )
    await chat_handler.initialize()
    return chat_handler


def validate_market_data(data: Dict[str, Any]) -> bool:
    """验证市场数据格式"""
    if not isinstance(data, dict):
        return False
    market_data = data.get("market_data", {})
    required_fields = ["📈 当前价格", "💰 24小时交易量", "📊 24小时涨跌"]
    return all(field in market_data for field in required_fields)


def validate_news_data(data: List[Dict[str, Any]]) -> bool:
    """验证新闻数据格式"""
    required_fields = ["title", "summary", "date", "source"]
    if not isinstance(data, list):
        return False
    return all(
        isinstance(item, dict) and
        all(field in item for field in required_fields)
        for item in data
    )


def validate_sentiment_data(data: Dict[str, Any]) -> bool:
    """验证情绪数据格式"""
    required_fields = ["sentiment", "confidence"]
    if not isinstance(data, dict):
        return False
    return all(
        field in data and
        isinstance(data[field], (str, float))
        for field in required_fields
    )


class ChatRequest(BaseModel):
    message: str
    session_id: str
    metadata: Optional[Dict] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """验证消息内容"""
        if not v.strip():
            raise ValueError("消息内容不能为空")
        if len(v) > 500:
            raise ValueError("消息内容过长，最大500字符")
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """验证会话ID"""
        if not v.strip():
            raise ValueError("会话ID不能为空")
        return v.strip()


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Initialize services if needed
        global model_manager, price_tracker, news_monitor
        global analytics_collector, response_formatter

        if not all([
            model_manager,
            price_tracker,
            news_monitor,
            analytics_collector,
            response_formatter
        ]):
            try:
                (
                    price_tracker,
                    news_monitor,
                    analytics_collector,
                    model_manager,
                    response_formatter
                ) = await initialize_services()
            except Exception as e:
                logger.error(
                    f"Failed to initialize services: {str(e)}",
                    extra={"category": DebugCategory.CONFIG.value}
                )
                return {
                    "error": "Service unavailable",
                    "message": "服务初始化失败，请稍后再试"
                }

        # Get context for AI response
        context = await context_manager.get_context(request.session_id)

        # Get data in parallel
        # Type assertions for mypy
        assert model_manager is not None, "Model manager not initialized"
        assert price_tracker is not None, "Price tracker not initialized"
        assert news_monitor is not None, "News monitor not initialized"
        assert analytics_collector is not None, "Analytics collector not ready"
        assert response_formatter is not None, "Response formatter not ready"

        tasks = [
            model_manager.generate_content(
                ModelContentType.MARKET,
                {"message": request.message, "context": context},
                max_length=280
            ),
            _get_price_data(),
            _get_latest_news(),
            _analyze_market_sentiment()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        ai_response, price_data, news_data, sentiment = results

        # Format response with validation and error handling
        market_data: Dict[str, str] = {"error": "Unexpected error"}
        if isinstance(price_data, Exception):
            error_msg = str(price_data)
            logger.error(
                f"Price data error: {error_msg}",
                extra={"category": DebugCategory.API.value}
            )
            if "Rate limit exceeded" in error_msg:
                market_data = {"error": "Rate limit exceeded"}
            else:
                market_data = {"error": "Unexpected error"}
        else:
            try:
                if (not isinstance(price_data, BaseException) and
                        isinstance(price_data, dict) and
                        "berachain" in price_data):
                    berachain_data = price_data["berachain"]
                    market_data = {
                        "📈 当前价格": f"${berachain_data['usd']}",
                        "💰 24小时交易量": f"${berachain_data['usd_24h_vol']:,}",
                        "📊 24小时涨跌": f"{berachain_data['usd_24h_change']:+}%"
                    }
                else:
                    logger.error(
                        "Invalid market data format",
                        extra={"category": DebugCategory.VALIDATION.value}
                    )
                    market_data = {"error": "Invalid data format"}
            except Exception as e:
                logger.error(
                    f"Market data processing error: {str(e)}",
                    extra={"category": DebugCategory.API.value}
                )
                market_data = {"error": "Data processing error"}

        # Validate and prepare news data
        news_list: List[Dict[str, str]] = []
        if isinstance(news_data, Exception):
            logger.error(
                f"News data error: {str(news_data)}",
                extra={"category": DebugCategory.API.value}
            )
        elif (not isinstance(news_data, BaseException) and
              validate_news_data(news_data)):
            news_list = [
                {
                    "title": str(item["title"]),
                    "summary": str(
                        item["summary"]
                    ),
                    "date": str(item["date"]),
                    "source": str(
                        item["source"]
                    )
                }
                for item in news_data
            ]
        else:
            logger.error(
                "Invalid news data format",
                extra={"category": DebugCategory.VALIDATION.value}
            )

        # Validate and prepare sentiment data
        sentiment_data: Dict[str, Union[str, float]] = {
            "sentiment": "neutral",
            "confidence": 0.0
        }
        if isinstance(sentiment, Exception):
            logger.error(
                f"Sentiment data error: {str(sentiment)}",
                extra={"category": DebugCategory.API.value}
            )
        elif (not isinstance(sentiment, BaseException) and
              validate_sentiment_data(sentiment)):
            sentiment_data = {
                "sentiment": str(sentiment["sentiment"]),
                "confidence": float(sentiment["confidence"])
            }
        else:
            logger.error(
                "Invalid sentiment data format",
                extra={"category": DebugCategory.VALIDATION.value}
            )

        response = {
            "ai_response": (
                "Unable to generate response"
                if isinstance(ai_response, Exception)
                else str(ai_response)
            ),
            "market_data": response_formatter.format_response(  # type: ignore
                market_data,
                FormatterContentType.MARKET
            ),
            "news": response_formatter.format_response(  # type: ignore
                news_list,
                FormatterContentType.NEWS
            ),
            "sentiment": sentiment_data
        }

        # Update context
        await context_manager.add_message(
            request.session_id,
            {"role": "user", "content": request.message}
        )
        await context_manager.add_message(
            request.session_id,
            {"role": "assistant", "content": response}
        )

        return response

    except Exception:
        # Log the error but return a graceful response
        return {
            "ai_response": "Unable to process request",
            "market_data": {"error": "Service unavailable"},
            "news": [],
            "sentiment": {"sentiment": "neutral"}
        }


async def _get_price_data():
    """Get price data from price tracker service"""
    global price_tracker
    if not price_tracker:
        raise RuntimeError("Price tracker service not initialized")
    return await price_tracker.get_price_data()


async def _get_latest_news():
    """Get latest news from news monitor service"""
    global news_monitor
    if not news_monitor:
        raise RuntimeError("News monitor service not initialized")
    return await news_monitor.get_latest_news()


async def _analyze_market_sentiment():
    """Get market sentiment from analytics collector service"""
    global analytics_collector
    if not analytics_collector:
        raise RuntimeError("Analytics collector service not initialized")
    return await analytics_collector.analyze_market_sentiment()
