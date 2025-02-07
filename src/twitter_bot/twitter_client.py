import os
import json
import base64
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
        """Authenticate with Twitter API using OAuth 2.0"""
        try:
            # First, get OAuth 2.0 token
            auth_str = f"{self.api_key}:{self.api_secret}"
            auth_bytes = auth_str.encode('ascii')
            b64_auth = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with aiohttp.ClientSession() as session:
                # Get OAuth 2.0 token
                async with session.post(
                    "https://api.twitter.com/oauth2/token",
                    headers=headers,
                    data={"grant_type": "client_credentials"}
                ) as response:
                    if response.status != 200:
                        self.logger.error(f"OAuth error: {response.status}")
                        return False
                        
                    data = await response.json()
                    self.bearer_token = data.get("access_token")
                    
                    if not self.bearer_token:
                        self.logger.error("No access token in response")
                        return False
                        
                    # Test the token
                    headers = {
                        "Authorization": f"Bearer {self.bearer_token}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.get(
                        "https://api.twitter.com/2/users/me",
                        headers=headers
                    ) as test_response:
                        return test_response.status == 200
                        
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
