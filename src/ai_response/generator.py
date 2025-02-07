import openai
import aiohttp
import logging
from typing import Optional, Dict, Any
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant for the Berachain ecosystem. You provide information about:
- BERA token price and market data
- Upcoming IDOs and launches
- Latest news and updates from BeraHome
- General Berachain ecosystem questions

Keep responses concise and informative, focusing on providing accurate information."""

class ResponseGenerator:
    def __init__(self, model: str = "deepseek-r1:1.5b", deepseek_api_key: Optional[str] = None):
        self.model = model
        self.openai_client = openai.Client()
        self.deepseek_api_key = deepseek_api_key
        self.deepseek_api_url = "https://api.deepseek.com/v3/chat/completions"
        
    async def generate_response(self, query: str) -> str:
        try:
            if self.model == "deepseek-r1:1.5b":
                return await self._generate_deepseek_response(query)
            else:
                return await self._generate_openai_response(query)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request at the moment. Please try again later."
            
    async def _generate_openai_response(self, query: str) -> str:
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
            
    async def _generate_deepseek_response(self, query: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-r1:1.5b",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.deepseek_api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        logger.error(f"Deepseek API error: {error_text}")
                        raise Exception(f"Deepseek API error: {response.status}")
        except Exception as e:
            logger.error(f"Deepseek API error: {str(e)}")
            raise
