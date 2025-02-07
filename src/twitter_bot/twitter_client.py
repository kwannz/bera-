import os
import json
import aiohttp
import logging
from typing import Optional, Dict

class TwitterClient:
    def __init__(self, api_key: str, api_secret: str, bearer_token: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.bearer_token = bearer_token
        self.logger = logging.getLogger(__name__)
        
    async def authenticate(self) -> bool:
        """Authenticate with Twitter API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.twitter.com/2/tweets",
                    headers=headers,
                    params={"max_results": 1}
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False
            
    async def post_tweet(self, message: str) -> Optional[Dict]:
        """Post a tweet"""
        try:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.twitter.com/2/tweets",
                    headers=headers,
                    json={"text": message}
                ) as response:
                    if response.status == 201:
                        return await response.json()
                    return None
                    
        except Exception as e:
            self.logger.error(f"Tweet error: {str(e)}")
            return None
