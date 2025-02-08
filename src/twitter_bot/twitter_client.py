import os
import json
import hmac
import base64
import hashlib
import aiohttp
import logging
import time
import uuid
from typing import Optional, Dict
from urllib.parse import quote

class TwitterClient:
    def __init__(self, api_key: str, api_secret: str, bearer_token: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.bearer_token = bearer_token
        self.logger = logging.getLogger(__name__)
        self.oauth_token = None
        self.oauth_token_secret = None
        
    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str]) -> str:
        """Generate OAuth 1.0a signature according to Twitter's specifications"""
        # Verify required parameters
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret are required for signature generation")
            
        # Sort parameters and encode values
        sorted_params = sorted(params.items())
        param_str = "&".join([
            f"{quote(str(k), safe='')}={quote(str(v), safe='')}"
            for k, v in sorted_params
        ])
        
        # Create signature base string
        base_str = "&".join([
            method.upper(),
            quote(url, safe=""),
            quote(param_str, safe="")
        ])
        
        self.logger.debug(f"Base string: {base_str}")
        
        # Create signing key
        signing_key = f"{quote(self.api_secret, safe='')}&{quote(self.oauth_token_secret or '', safe='')}"
        
        # Generate HMAC-SHA1 signature
        signature = hmac.new(
            signing_key.encode('ascii'),
            base_str.encode('ascii'),
            hashlib.sha1
        ).digest()
        
        # Encode signature in base64
        encoded_signature = base64.b64encode(signature).decode('ascii')
        self.logger.debug(f"Generated signature: {encoded_signature}")
        
        return encoded_signature
        
    async def authenticate(self) -> bool:
        """Authenticate with Twitter API v2"""
        try:
            if not self.bearer_token:
                self.logger.error("Missing bearer token")
                return False
                
            # Test authentication with a simple API call
            url = "https://api.twitter.com/2/users/me"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"Authorization": f"Bearer {self.bearer_token}"}
                ) as response:
                    response_json = await response.json()
                    if response.status != 200:
                        self.logger.error(f"Authentication error: {response.status}")
                        self.logger.error(f"Response details: {response_json}")
                        return False
                        
                    self.logger.info("Successfully authenticated with Twitter API v2")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False
            
    async def post_tweet(self, message: str) -> Optional[Dict]:
        """Post a tweet using Twitter API v2"""
        try:
            if not self.bearer_token:
                if not await self.authenticate():
                    return None
                    
            url = "https://api.twitter.com/2/tweets"
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.bearer_token}",
                        "Content-Type": "application/json"
                    },
                    json={"text": message}
                ) as response:
                    response_json = await response.json()
                    if response.status == 201:
                        return response_json
                    self.logger.error(f"Tweet error: {response.status}")
                    self.logger.error(f"Response details: {response_json}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Tweet error: {str(e)}")
            return None
