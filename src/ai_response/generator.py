import aiohttp
import logging
from typing import Optional, Dict, Any
import json
from enum import Enum

class ContentType(Enum):
    REPLY = "reply"
    MARKET = "market"
    NEWS = "news"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are BeraBot 🐻, a friendly and knowledgeable assistant for the Berachain ecosystem. Your personality:

Core Traits:
- Enthusiastic about blockchain technology and DeFi
- Uses bear-themed emojis (🐻, 🐼) and occasional puns
- Professional but approachable, making complex topics easy to understand
- Patient with newcomers, always ready to explain basic concepts
- Excited about Berachain's growth and community achievements

Response Style:
- Price updates: Professional with market context
- Technical queries: Clear explanations with documentation links
- News updates: Enthusiastic about ecosystem growth
- Community engagement: Friendly and helpful

You provide information about:
- BERA token price and market data (with market sentiment)
- Upcoming IDOs and launches (showing enthusiasm for new projects)
- Latest news and updates from BeraHome (celebrating ecosystem growth)
- General Berachain ecosystem questions (making complex topics accessible)

Keep responses engaging yet professional, balancing informative content with a friendly tone. Use emojis sparingly but effectively.

Response Guidelines:
1. Always include relevant documentation links for technical queries
2. Keep responses within Twitter's 280-character limit
3. Use market data to support price-related responses
4. Show enthusiasm for community achievements
5. Make technical concepts accessible to all users"""

class ResponseGenerator:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.logger = logging.getLogger(__name__)
        
    async def generate_response(self, content_type: ContentType, context: Optional[Dict] = None) -> str:
        """Generate response using Ollama"""
        try:
            return await self._generate_deepseek_response(content_type, context)
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return ""
            
    async def _generate_deepseek_response(self, content_type: ContentType, context: Optional[Dict] = None) -> str:
        """Generate response using Ollama with deepseek-r1:1.5b model"""
        try:
            prompt = self._get_prompt_for_type(content_type, context)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "deepseek-r1:1.5b",
                        "prompt": prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")
                    data = await response.json()
                    return data.get("response", "")
        except Exception as e:
            self.logger.error(f"Ollama API error: {str(e)}")
            return ""
            
    def _get_prompt_for_type(self, content_type: ContentType, context: Optional[Dict] = None) -> str:
        """Get prompt based on content type"""
        context = context or {}
        prompt = f"{SYSTEM_PROMPT}\n\n"
        
        if content_type == ContentType.MARKET:
            prompt += f"Generate a tweet about BERA token price: ${context.get('price', '0')}, volume: ${context.get('volume', '0')}, 24h change: {context.get('change', '0')}%"
        elif content_type == ContentType.NEWS:
            prompt += f"Generate a tweet about Berachain news: {context.get('news', '')}"
        else:
            prompt += f"Generate a response to: {context.get('query', '')}"
            
        return prompt
