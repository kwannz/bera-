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
from ..services.response_formatter import ContentType as FormatterContentType


class WebSocketHandler:
    def __init__(
        self,
        rate_limiter,
        context_manager: ContextManager,
        price_tracker,
        news_monitor,
        analytics_collector,
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

    async def handle_connection(self, websocket):
        session_id = None
        try:
            async for message in websocket:
                try:
                    if not session_id:
                        try:
                            session_data = json.loads(message)
                            session_id = session_data.get('session_id')
                            if not session_id:
                                error_msg = {"error": "Session ID is required"}
                                await websocket.send(json.dumps(error_msg))
                                continue
                        except json.JSONDecodeError:
                            await websocket.send(
                                json.dumps({"error": "Invalid JSON format"})
                            )
                            continue

                    response = await self.process_message(session_id, message)
                    await websocket.send(json.dumps(response))
                except Exception as e:
                    await websocket.send(json.dumps({"error": str(e)}))
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
            results = await asyncio.gather(*tasks, return_exceptions=True)
            price_data, news_data, sentiment = results

            # Format response with error handling
            market_data = {"error": "Unexpected error"}
            if isinstance(price_data, Exception):
                if "Rate limit exceeded" in str(price_data):
                    market_data = {"error": "Rate limit exceeded"}
                else:
                    market_data = {"error": "Unexpected error"}
            else:
                try:
                    if isinstance(price_data, dict):
                        market_data = price_data
                    else:
                        market_data = {"error": "Rate limit exceeded"}
                except (TypeError, AttributeError):
                    market_data = {"error": "Rate limit exceeded"}

            # Prepare response data with proper types
            news_list = []
            if (not isinstance(news_data, Exception) and
                    isinstance(news_data, list)):
                news_list = news_data

            sentiment_data = {
                "sentiment": "neutral",
                "confidence": 0.0
            }
            if (not isinstance(sentiment, Exception) and
                    isinstance(sentiment, dict)):
                sentiment_data = sentiment

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
            return {"error": str(e)}

    async def _get_price_data(self):
        """Get price data from price tracker service"""
        return await self.price_tracker.get_price_data()

    async def _get_latest_news(self):
        """Get latest news from news monitor service"""
        return await self.news_monitor.get_latest_news()

    async def _analyze_market_sentiment(self):
        """Get market sentiment from analytics collector service"""
        return await self.analytics_collector.analyze_market_sentiment()
