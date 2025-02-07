from typing import Optional, Dict, List
from enum import Enum
import openai
import aiohttp
import logging
from ..utils.logging_config import get_logger, DebugCategory

class ModelType(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

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
        model_type: ModelType = ModelType.DEEPSEEK,
        openai_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None
    ):
        self.logger = get_logger(__name__)
        self.model_type = model_type
        self.openai_client = openai.Client(api_key=openai_api_key) if openai_api_key else None
        self.deepseek_api_key = deepseek_api_key
        self.deepseek_api_url = "https://api.deepseek.com/v3/chat/completions"
        
    async def generate_content(
        self,
        content_type: ContentType,
        params: Dict,
        max_length: int = 280
    ) -> Optional[str]:
        try:
            prompt = PROMPT_TEMPLATES[content_type].format(**params)
            
            self.logger.debug(
                f"Generating {content_type.value} content",
                extra={"category": DebugCategory.API.value}
            )
            
            if self.model_type == ModelType.OPENAI:
                return await self._generate_openai_content(prompt, max_length)
            else:
                return await self._generate_deepseek_content(prompt, max_length)
                
        except Exception as e:
            self.logger.error(
                f"Error generating content: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
            
    async def _generate_openai_content(self, prompt: str, max_length: int) -> Optional[str]:
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(
                f"OpenAI API error: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
            
    async def _generate_deepseek_content(self, prompt: str, max_length: int) -> Optional[str]:
        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-r1:1.5b",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_length,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.deepseek_api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Deepseek API error: {error_text}",
                            extra={"category": DebugCategory.API.value}
                        )
                        return None
        except Exception as e:
            self.logger.error(
                f"Deepseek API error: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
