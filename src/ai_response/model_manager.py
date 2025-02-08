import aiohttp
import asyncio
from typing import Optional, Dict, List
from enum import Enum
from ..utils.logging_config import get_logger, DebugCategory

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

class ModelType(Enum):
    OLLAMA = "ollama"

class ContentType(Enum):
    TWEET = "tweet"
    REPLY = "reply"
    NEWS = "news"
    MARKET = "market"

PROMPT_TEMPLATES = {
    ContentType.TWEET: """Generate an engaging tweet about {topic} in the Berachain ecosystem.
Focus on: {focus}
Key points: {points}
Style: Professional yet friendly, using bear-themed elements sparingly.""",
    
    ContentType.REPLY: """Generate a helpful reply to a user query about Berachain.
Query: {query}
Context: {context}
Style: Friendly and informative, using bear-themed elements when appropriate.

Guidelines:
1. For price queries: Include current price, volume, and market sentiment
2. For IDO queries: List upcoming IDOs with dates and status
3. For news queries: Summarize latest updates and their impact
4. For technical queries: Provide clear explanations with documentation links
5. Always maintain a helpful and enthusiastic tone
6. Use bear-themed elements (🐻, 🐼) sparingly
7. Keep responses under 280 characters""",
    
    ContentType.NEWS: """Generate a tweet about recent Berachain news.
News: {news}
Impact: {impact}
Style: Enthusiastic and informative, highlighting ecosystem growth.""",
    
    ContentType.MARKET: """Generate a market update tweet for BERA token.
Price: {price}
Volume: {volume}
Change: {change}
Style: Professional with market insights, using bear-themed elements."""
}

class AIModelManager:
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434"
    ):
        self.logger = get_logger(__name__)
        self.model_type = ModelType.OLLAMA
        self.ollama_url = ollama_url
        
    async def generate_content(
        self,
        content_type: ContentType,
        params: Dict,
        max_length: int = 280,
        retries: int = MAX_RETRIES
    ) -> Optional[str]:
        try:
            prompt = PROMPT_TEMPLATES[content_type].format(**params)
            
            self.logger.debug(
                f"Generating {content_type.value} content",
                extra={"category": DebugCategory.API.value}
            )
            
            for attempt in range(retries):
                try:
                    content = await self._generate_ollama_content(prompt, max_length)
                    if content:
                        return content[:max_length]
                    
                    if attempt < retries - 1:
                        self.logger.warning(
                            f"Retrying content generation (attempt {attempt + 1}/{retries})",
                            extra={"category": DebugCategory.API.value}
                        )
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                except Exception as e:
                    if attempt < retries - 1:
                        self.logger.warning(
                            f"Error in content generation (attempt {attempt + 1}/{retries}): {str(e)}",
                            extra={"category": DebugCategory.API.value}
                        )
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        raise
                
        except Exception as e:
            self.logger.error(
                f"Error generating content: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
            
    async def _generate_ollama_content(self, prompt: str, max_length: int) -> Optional[str]:
        try:
            payload = {
                "model": "deepseek-r1:1.5b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": max_length
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["message"]["content"]
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Ollama API error: {error_text}",
                            extra={"category": DebugCategory.API.value}
                        )
                        return None
        except Exception as e:
            self.logger.error(
                f"Ollama API error: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
