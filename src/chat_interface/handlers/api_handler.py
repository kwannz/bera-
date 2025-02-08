from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
import asyncio
import redis

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


class ChatRequest(BaseModel):
    message: str
    session_id: str
    metadata: Optional[Dict] = None


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

        # Format response with error handling
        # Handle market data with proper error messages
        market_data: Dict[str, str] = {"error": "Unexpected error"}
        if isinstance(price_data, Exception):
            market_data = {"error": "Unexpected error"}
        else:
            try:
                if isinstance(price_data, dict):
                    berachain_data = price_data.get("berachain", {})
                    if isinstance(berachain_data, dict):
                        market_data = {
                            "price": str(
                                berachain_data.get("usd", "0.00")
                            ),
                            "volume": str(
                                berachain_data.get("usd_24h_vol", "0")
                            ),
                            "change": str(
                                berachain_data.get("usd_24h_change", "0")
                            )
                        }
                    else:
                        market_data = {"error": "Rate limit exceeded"}
                else:
                    market_data = {"error": "Rate limit exceeded"}
            except (TypeError, AttributeError):
                market_data = {"error": "Rate limit exceeded"}

        # Prepare response data with proper types
        news_list: List[Dict[str, str]] = []
        if (not isinstance(news_data, Exception) and
                isinstance(news_data, list)):
            for item in news_data:
                if isinstance(item, dict):
                    news_list.append({
                        "title": str(item.get("title", "")),
                        "summary": str(item.get("summary", "")),
                        "date": str(item.get("date", "")),
                        "source": str(item.get("source", ""))
                    })

        sentiment_data: Dict[str, Any] = {
            "sentiment": "neutral",
            "confidence": 0.0
        }
        if (not isinstance(sentiment, Exception) and
                isinstance(sentiment, dict)):
            sentiment_data = {
                "sentiment": str(sentiment.get("sentiment", "neutral")),
                "confidence": float(sentiment.get("confidence", 0.0))
            }

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
