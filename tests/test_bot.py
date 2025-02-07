import pytest
import aiohttp
from src.ai_response.model_manager import AIModelManager, ContentType

async def test_ollama_server():
    """Test if Ollama server is running and accessible"""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:11434/api/tags") as response:
            assert response.status == 200
            data = await response.json()
            assert any(model["name"] == "deepseek-r1:1.5b" for model in data["models"])

@pytest.mark.asyncio
async def test_ollama_integration():
    """Test Ollama integration for content generation"""
    model_manager = AIModelManager(ollama_url="http://localhost:11434")
    
    # Test tweet generation
    tweet = await model_manager.generate_content(
        ContentType.TWEET,
        {
            "topic": "Berachain ecosystem",
            "focus": "community growth",
            "points": "Active development, growing community"
        }
    )
    assert tweet is not None
    assert len(tweet) <= 280
    
    # Test reply generation
    reply = await model_manager.generate_content(
        ContentType.REPLY,
        {
            "query": "What's the latest on Berachain?",
            "context": "Latest updates and ecosystem growth"
        }
    )
    assert reply is not None
    assert len(reply) <= 280

@pytest.mark.asyncio
async def test_market_content():
    """Test market update content generation"""
    model_manager = AIModelManager()
    
    tweet = await model_manager.generate_content(
        ContentType.MARKET,
        {
            "price": "10.5",
            "volume": "1M",
            "change": "+5.2"
        }
    )
    assert tweet is not None
    assert len(tweet) <= 280
    assert any(keyword in tweet.lower() for keyword in ["price", "volume", "bera"])

@pytest.mark.asyncio
async def test_news_content():
    """Test news content generation"""
    model_manager = AIModelManager()
    
    tweet = await model_manager.generate_content(
        ContentType.NEWS,
        {
            "news": "New partnership announcement",
            "impact": "Growing ecosystem"
        }
    )
    assert tweet is not None
    assert len(tweet) <= 280
    assert any(keyword in tweet.lower() for keyword in ["news", "partnership", "ecosystem"])
