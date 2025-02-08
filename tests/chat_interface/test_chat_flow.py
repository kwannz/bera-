import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.chat_interface.handlers.api_handler import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_full_chat_flow():
    """Test complete chat flow with all components"""
    # Mock external service responses
    price_data = {
        "berachain": {
            "usd": "1.23",
            "usd_24h_vol": "1000000",
            "usd_24h_change": "5.67"
        }
    }
    news_data = [dict(
        title="Test News",
        summary="Test Content",
        date="2024-01-01",
        source="BeraHome"
    )]
    sentiment_data = dict(
        sentiment="positive",
        confidence=0.8
    )

    price_patch = (
        'src.chat_interface.services.price_tracker'
        '.PriceTracker.get_price_data'
    )
    news_patch = (
        'src.chat_interface.services.news_monitor'
        '.NewsMonitor.get_latest_news'
    )
    sentiment_patch = (
        'src.chat_interface.services.analytics_collector'
        '.AnalyticsCollector.analyze_market_sentiment'
    )
    ai_patch = 'src.ai_response.model_manager.AIModelManager.generate_content'

    with patch(price_patch) as mock_price, \
         patch(news_patch) as mock_news, \
         patch(sentiment_patch) as mock_sentiment, \
         patch(ai_patch) as mock_ai:

        mock_price.return_value = price_data
        mock_news.return_value = news_data
        mock_sentiment.return_value = sentiment_data
        mock_ai.return_value = "BERA price analysis response"

        # Test chat request
        response = client.post(
            "/api/chat",
            json={
                "message": "What's the current BERA price?",
                "session_id": "test_session"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "ai_response" in data
        assert "market_data" in data
        assert "news" in data
        assert "sentiment" in data

        # Verify AI response
        assert data["ai_response"] == "BERA price analysis response"

        # Verify market data formatting
        assert "📈 当前价格" in data["market_data"]
        assert "💰 24小时交易量" in data["market_data"]
        assert "📊 价格变动" in data["market_data"]

        # Verify news data
        assert "📰 标题" in data["news"]
        assert "Test News" in data["news"]
        assert "Test Content" in data["news"]

        # Verify sentiment data
        assert data["sentiment"]["sentiment"] == "positive"
        assert data["sentiment"]["confidence"] == 0.8


@pytest.mark.asyncio
async def test_rate_limit_handling():
    """Test rate limit handling in chat flow"""
    rate_limit_patch = (
        'src.chat_interface.utils.rate_limiter'
        '.RateLimiter.check_rate_limit'
    )
    with patch(rate_limit_patch) as mock_rate_limit:
        mock_rate_limit.return_value = False

        response = client.post(
            "/api/chat",
            json={
                "message": "Test message",
                "session_id": "test_session"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "❌ 错误" in data["market_data"]
        assert "Rate limit exceeded" in data["market_data"]


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in chat flow"""
    price_patch = (
        'src.chat_interface.services.price_tracker'
        '.PriceTracker.get_price_data'
    )
    with patch(price_patch) as mock_price:
        mock_price.side_effect = Exception("Test error")

        response = client.post(
            "/api/chat",
            json={
                "message": "Test message",
                "session_id": "test_session"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "❌ 错误" in data["market_data"]
        assert "Unexpected error" in data["market_data"]
