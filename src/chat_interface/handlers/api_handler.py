from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import asyncio

from ..services.context_service import ContextManager
from ..services.response_formatter import ResponseFormatter, ContentType


app = FastAPI()
context_manager = ContextManager()
response_formatter = ResponseFormatter()


class ChatRequest(BaseModel):
    message: str
    session_id: str
    metadata: Optional[Dict] = None


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # 并行获取数据
        data_tasks = [
            _get_price_data(),
            _get_latest_news(),
            _analyze_market_sentiment()
        ]
        price_data, news_data, sentiment = await asyncio.gather(*data_tasks)

        # 格式化响应
        response = {
            "market_data": response_formatter.format_response(
                str(price_data),
                ContentType.MARKET
            ),
            "news": response_formatter.format_response(
                str(news_data),
                ContentType.NEWS
            ),
            "sentiment": sentiment
        }

        # 更新上下文
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
