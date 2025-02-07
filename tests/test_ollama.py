import asyncio
import aiohttp
import json
import sys

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
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "deepseek-r1:1.5b",
                "messages": [{
                    "role": "user", 
                    "content": "Generate a tweet about Berachain ecosystem growth"
                }],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 280
                }
            }
            
            print("Sending request to Ollama...")
            async with session.post(
                "http://localhost:11434/api/chat",
                json=payload
            ) as response:
                print(f"Response status: {response.status}")
                response_text = await response.text()
                print(f"Raw response: {response_text[:200]}...")
                
                assert response.status == 200, f"Expected status 200, got {response.status}"
                result = json.loads(response_text)
                assert "message" in result, "No 'message' in response"
                assert "content" in result["message"], "No 'content' in message"
                
                content = result["message"]["content"]
                assert content is not None, "Content is None"
                assert len(content) <= 280, f"Content too long: {len(content)} chars"
                
                print("✓ Content generation test passed")
                print(f"Sample response: {content[:100]}...")
                return True
    except Exception as e:
        print(f"✗ Content generation test failed:")
        if isinstance(e, aiohttp.ClientError):
            print(f"  Network error: {str(e)}")
        elif isinstance(e, json.JSONDecodeError):
            print(f"  Invalid JSON response: {str(e)}")
        elif isinstance(e, AssertionError):
            print(f"  Assertion failed: {str(e)}")
        else:
            print(f"  Unexpected error: {str(e)}")
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
