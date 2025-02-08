from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import asyncio

from ..services.context_service import ContextManager
from ..services.response_formatter import ResponseFormatter
from src.ai_response.model_manager import (
    AIModelManager,
    ContentType as ModelContentType
)
from src.ai_response.generator import ResponseGenerator
from ..services.response_formatter import ContentType as FormatterContentType


app = FastAPI()
context_manager = ContextManager()
response_formatter = ResponseFormatter()
model_manager = AIModelManager()
response_generator = ResponseGenerator()


class ChatRequest(BaseModel):
    message: str
    session_id: str
    metadata: Optional[Dict] = None


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Get context for AI response
        context = await context_manager.get_context(request.session_id)

        # Generate AI response
        ai_response = await model_manager.generate_content(
            ModelContentType.MARKET,
            {"message": request.message, "context": context},
            max_length=280
        )

        # Get additional data in parallel
        data_tasks = [
            _get_price_data(),
            _get_latest_news(),
            _analyze_market_sentiment()
        ]
        price_data, news_data, sentiment = await asyncio.gather(*data_tasks)

        # Format response
        market_data = {
            "price": price_data["berachain"]["usd"],
            "volume": price_data["berachain"]["usd_24h_vol"],
            "change": price_data["berachain"]["usd_24h_change"]
        }
        response = {
            "ai_response": ai_response,
            "market_data": response_formatter.format_response(
                market_data,
                FormatterContentType.MARKET
            ),
            "news": response_formatter.format_response(
                news_data,
                FormatterContentType.NEWS
            ),
            "sentiment": sentiment
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _get_price_data():
    # TODO: Implement price data fetching
    return {"price": "0.00", "volume": "0"}


async def _get_latest_news():
    # TODO: Implement news fetching
    return {"title": "", "content": ""}


async def _analyze_market_sentiment():
    # TODO: Implement sentiment analysis
    return "neutral"
