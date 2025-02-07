import openai
from typing import Optional

class ResponseGenerator:
    def __init__(self, model: str = "deepseek-r1:1.5b"):
        self.model = model
        self.openai_client = openai.Client()
        
    async def generate_response(self, query: str) -> str:
        try:
            if self.model == "deepseek-r1:1.5b":
                return await self._generate_ollama_response(query)
            else:
                return await self._generate_openai_response(query)
        except Exception as e:
            return "Sorry, I couldn't process your request at the moment."
            
    async def _generate_openai_response(self, query: str) -> str:
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for the Berachain ecosystem."},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content
        
    async def _generate_ollama_response(self, query: str) -> str:
        # TODO: Implement Ollama integration
        return "I'm processing your request using the Ollama model."
