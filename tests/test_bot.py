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
async def test_market_content():
    """Test market update content generation"""
    model_manager = AIModelManager(ollama_url="http://localhost:11434")
    
    content = await model_manager.generate_content(
        ContentType.MARKET,
        {
            "price": "10.5",
            "volume": "1M",
            "change": "+5.2"
        }
    )
    assert content is not None
    assert any(keyword in content.lower() for keyword in ["price", "volume", "bera"])

@pytest.mark.asyncio
async def test_news_content():
    """Test news content generation"""
    model_manager = AIModelManager(ollama_url="http://localhost:11434")
    
    content = await model_manager.generate_content(
        ContentType.NEWS,
        {
            "news": "New partnership announcement",
            "impact": "Growing ecosystem"
        }
    )
    assert content is not None
    assert any(keyword in content.lower() for keyword in ["news", "partnership", "ecosystem"])
