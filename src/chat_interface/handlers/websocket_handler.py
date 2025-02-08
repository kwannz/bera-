import asyncio
import json
import websockets
from typing import Dict, Any
from ..services.context_service import ContextManager
from ..services.response_formatter import ResponseFormatter
from src.ai_response.model_manager import (
    AIModelManager,
    ContentType as ModelContentType
)
from src.ai_response.generator import ResponseGenerator
from ..services.response_formatter import ContentType as FormatterContentType


class WebSocketHandler:
    def __init__(self):
        self.context_manager = ContextManager()
        self.response_formatter = ResponseFormatter()
        self.model_manager = AIModelManager()
        self.response_generator = ResponseGenerator()

    async def handle_connection(self, websocket):
        session_id = None
        try:
            async for message in websocket:
                if not session_id:
                    session_data = json.loads(message)
                    session_id = session_data.get('session_id')
                    if not session_id:
                        await websocket.send(
                            json.dumps({"error": "Session ID is required"})
                        )
                        continue

                response = await self.process_message(session_id, message)
                await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            pass

    async def process_message(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """处理接收到的消息"""
        try:
            # Get context for AI response
            context = await self.context_manager.get_context(session_id)

            # Generate AI response
            ai_response = await self.model_manager.generate_content(
                ModelContentType.MARKET,
                {"message": message, "context": context},
                max_length=280
            )

            # Get additional data in parallel
            tasks = [
                self._get_price_data(),
                self._get_latest_news(),
                self._analyze_market_sentiment()
            ]
            price_data, news_data, sentiment = await asyncio.gather(*tasks)

            # Format response
            response = {
                "ai_response": ai_response,
                "market_data": self.response_formatter.format_response(
                    json.dumps(price_data),
                    FormatterContentType.MARKET
                ),
                "news": self.response_formatter.format_response(
                    json.dumps(news_data),
                    FormatterContentType.NEWS
                ),
                "sentiment": sentiment
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
            return {"error": str(e)}

    async def _get_price_data(self):
        # TODO: Implement price data fetching
        return {"price": "0.00", "volume": "0"}

    async def _get_latest_news(self):
        # TODO: Implement news fetching
        return {"title": "", "content": ""}

    async def _analyze_market_sentiment(self):
        # TODO: Implement sentiment analysis
        return "neutral"
