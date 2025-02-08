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
    MARKET = "market"
    NEWS = "news"

PROMPT_TEMPLATES = {
    ContentType.MARKET: """Generate a market update for BERA token.
Price: {price}
Volume: {volume}
24h Change: {change}%
Style: Professional and informative.""",

    ContentType.NEWS: """Generate a news update about recent Berachain developments.
News: {news}
Impact: {impact}
Style: Professional and informative."""
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
            return None
                
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
