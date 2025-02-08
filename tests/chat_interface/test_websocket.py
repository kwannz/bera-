import pytest
import json
import asyncio
from unittest.mock import patch, AsyncMock
import pytest_asyncio
from .utils.test_server import TestWebSocketServer
from websockets.legacy.client import connect
from websockets.exceptions import ConnectionClosed


@pytest_asyncio.fixture(scope="function")
async def server():
    """创建并启动测试服务器"""
    server = TestWebSocketServer()
    await server.start()
    await asyncio.sleep(0.1)  # Give server time to start
    try:
        yield server
    finally:
        await server.stop()
        await asyncio.sleep(0.1)  # Give server time to stop


@pytest.mark.asyncio
async def test_websocket_connection(server):
    """Test WebSocket connection and session initialization"""
    async with connect(server.url) as websocket:
        # Test session initialization
        await websocket.send(json.dumps({
            "session_id": "test_session"
        }))

        # Test message handling
        await websocket.send(json.dumps({
            "message": "Test message"
        }))

        response = json.loads(await websocket.recv())
        assert "ai_response" in response
        assert "market_data" in response
        assert "news" in response
        assert "sentiment" in response


@pytest.mark.asyncio
async def test_websocket_error_handling(server):
    """Test error handling for invalid messages"""
    async with connect(server.url) as websocket:
        # Test missing session_id
        await websocket.send(json.dumps({
            "message": "Test message"
        }))
        response = json.loads(await websocket.recv())
        assert "error" in response
        assert "Session ID is required" in response["error"]

        # Test invalid JSON
        await websocket.send("invalid json")
        response = json.loads(await websocket.recv())
        assert "error" in response


@pytest.mark.asyncio
async def test_websocket_rate_limit(server):
    """Test rate limit error handling"""
    async with connect(server.url) as websocket:
        # Initialize session
        await websocket.send(json.dumps({
            "session_id": "test_session"
        }))

        # Mock rate limiter to simulate rate limit exceeded
        with patch(
            'src.chat_interface.utils.rate_limiter.RateLimiter.'
            'check_rate_limit',
            return_value=False
        ):
            await websocket.send(json.dumps({
                "message": "Test message"
            }))
            response = json.loads(await websocket.recv())
            assert "market_data" in response
            assert "Rate limit exceeded" in response["market_data"]


@pytest.mark.asyncio
async def test_websocket_response_structure(server):
    """Test detailed response structure"""
    async with connect(server.url) as websocket:
        # Initialize session
        await websocket.send(json.dumps({
            "session_id": "test_session"
        }))

        # Mock services for consistent response
        price_data = {
            "price": "1.23",
            "volume": "1000000",
            "change": "5.67"
        }
        news_data = [{
            "title": "Test News",
            "summary": "Test Content",
            "date": "2024-01-01",
            "source": "BeraHome"
        }]
        sentiment_data = {
            "sentiment": "positive",
            "confidence": 0.8
        }

        with patch(
            'src.chat_interface.handlers.websocket_handler.WebSocketHandler._get_price_data',  # noqa: E501
            new_callable=AsyncMock,
            return_value=price_data
        ), patch(
            'src.chat_interface.handlers.websocket_handler.WebSocketHandler._get_latest_news',  # noqa: E501
            new_callable=AsyncMock,
            return_value=news_data
        ), patch(
            'src.chat_interface.handlers.websocket_handler.WebSocketHandler._analyze_market_sentiment',  # noqa: E501
            new_callable=AsyncMock,
            return_value=sentiment_data
        ):
            await websocket.send(json.dumps({
                "message": "Test message"
            }))
            response = json.loads(await websocket.recv())

            # Verify response structure
            assert isinstance(response["ai_response"], str)
            assert "📈 当前价格" in response["market_data"]
            assert "💰 24小时交易量" in response["market_data"]
            assert "📊 价格变动" in response["market_data"]
            assert "📰 标题" in response["news"]
            assert "Test News" in response["news"]
            assert response["sentiment"]["sentiment"] == "positive"
            assert response["sentiment"]["confidence"] == 0.8


@pytest.mark.asyncio
async def test_websocket_connection_closed(server):
    """Test handling of closed connections"""
    async with connect(server.url) as websocket:
        # Initialize session
        await websocket.send(json.dumps({
            "session_id": "test_session"
        }))

        # Close connection abruptly
        await websocket.close()

        # Try to send message after close
        with pytest.raises(ConnectionClosed):
            await websocket.send(json.dumps({
                "message": "Test message"
            }))
