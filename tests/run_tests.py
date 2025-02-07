import asyncio
import aiohttp
import sys
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ai_response.model_manager import AIModelManager, ContentType

async def test_ollama_server():
    """Test if Ollama server is running and accessible"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                assert response.status == 200
                data = await response.json()
                assert any(model["name"] == "deepseek-r1:1.5b" for model in data["models"])
        print("✓ Ollama server test passed")
        return True
    except Exception as e:
        print(f"✗ Ollama server test failed: {str(e)}")
        return False

async def test_content_generation():
    """Test content generation with Ollama"""
    try:
        model_manager = AIModelManager()
        
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
        print("✓ Tweet generation test passed")
        
        # Test market update
        market = await model_manager.generate_content(
            ContentType.MARKET,
            {
                "price": "10.5",
                "volume": "1M",
                "change": "+5.2"
            }
        )
        assert market is not None
        assert len(market) <= 280
        print("✓ Market update test passed")
        return True
    except Exception as e:
        print(f"✗ Content generation test failed: {str(e)}")
        return False

async def main():
    tests = [
        test_ollama_server(),
        test_content_generation()
    ]
    results = await asyncio.gather(*tests)
    if all(results):
        print("\nAll tests passed! ✨")
        sys.exit(0)
    else:
        print("\nSome tests failed! ❌")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
