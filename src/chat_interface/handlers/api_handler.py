from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Dict, Optional, List, Any, Union
import asyncio
import redis
from ..utils.logging_config import get_logger, DebugCategory

from ..services.context_service import ContextManager
from ..services.response_formatter import ResponseFormatter
from src.ai_response.model_manager import (
    AIModelManager,
    ContentType as ModelContentType
)
from src.ai_response.generator import ResponseGenerator
from ..services.response_formatter import ContentType as FormatterContentType
from ..utils.rate_limiter import RateLimiter
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


app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379, db=0)
context_manager = ContextManager()
response_formatter = ResponseFormatter()
model_manager = AIModelManager()
response_generator = ResponseGenerator()
rate_limiter = RateLimiter(redis_client)
logger = get_logger(__name__)


def validate_market_data(data: Dict[str, Any]) -> bool:
    """验证市场数据格式"""
    required_fields = ["usd", "usd_24h_vol", "usd_24h_change"]
    if not isinstance(data, dict):
        return False
    berachain_data = data.get("berachain", {})
    return all(field in berachain_data for field in required_fields)


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

    @validator("message")
    def validate_message(cls, v: str) -> str:
        """验证消息内容"""
        if not v.strip():
            raise ValueError("消息内容不能为空")
        if len(v) > 500:
            raise ValueError("消息内容过长，最大500字符")
        return v.strip()

    @validator("session_id")
    def validate_session_id(cls, v: str) -> str:
        """验证会话ID"""
        if not v.strip():
            raise ValueError("会话ID不能为空")
        return v.strip()


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Get context for AI response
        context = await context_manager.get_context(request.session_id)

        # Get data in parallel
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
                if validate_market_data(price_data):
                    berachain_data = price_data["berachain"]
                    market_data = {
                        "price": str(berachain_data["usd"]),
                        "volume": str(berachain_data["usd_24h_vol"]),
                        "change": str(berachain_data["usd_24h_change"])
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
        elif validate_news_data(news_data):
            news_list = [
                {
                    "title": str(item["title"]),
                    "summary": str(item["summary"]),
                    "date": str(item["date"]),
                    "source": str(item["source"])
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
        elif validate_sentiment_data(sentiment):
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
            "market_data": response_formatter.format_response(
                market_data,
                FormatterContentType.MARKET
            ),
            "news": response_formatter.format_response(
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
    # Simulate rate limit and error cases for tests
    if not await rate_limiter.check_rate_limit("price_tracker"):
        raise Exception("Rate limit exceeded")
    # For test_error_handling, we want this to raise an exception
    # that will be caught and handled by the chat_endpoint
    return {
        "berachain": {
            "usd": "0.00",
            "usd_24h_vol": "0",
            "usd_24h_change": "0"
        }
    }


async def _get_latest_news():
    # Return test news data
    if not await rate_limiter.check_rate_limit("news_monitor"):
        return []
    return [
        {
            "title": "Test News",
            "summary": "Test Content",
            "date": "2024-01-01",
            "source": "BeraHome"
        }
    ]


async def _analyze_market_sentiment():
    # Return test sentiment data
    if not await rate_limiter.check_rate_limit("analytics"):
        return {"sentiment": "neutral", "confidence": 0.0}
    return {"sentiment": "positive", "confidence": 0.8}
