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
        """Authenticate with Twitter API using OAuth 1.0a"""
        try:
            # Step 1: Get request token
            # Verify API key is present
            if not self.api_key or not self.api_secret:
                self.logger.error("Missing API key or secret")
                return False
                
            # Prepare OAuth parameters
            nonce = str(uuid.uuid4()).replace('-', '')
            timestamp = str(int(time.time()))
            
            oauth_params = {
                "oauth_callback": "oob",
                "oauth_consumer_key": self.api_key,
                "oauth_nonce": nonce,
                "oauth_signature_method": "HMAC-SHA1",
                "oauth_timestamp": timestamp,
                "oauth_version": "1.0"
            }
            
            # Log OAuth parameters for debugging (excluding sensitive data)
            self.logger.debug(f"OAuth params: nonce={nonce}, timestamp={timestamp}")
            
            # Generate OAuth signature
            url = "https://api.twitter.com/oauth/request_token"
            oauth_params["oauth_signature"] = self._generate_oauth_signature(
                "POST", url, oauth_params
            )
            
            # Format OAuth header according to Twitter API spec
            auth_header = "OAuth " + ", ".join([
                f'{quote(k, safe="")}="{quote(str(v), safe="")}"'
                for k, v in sorted(oauth_params.items())
            ])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers={"Authorization": auth_header}
                ) as response:
                    response_text = await response.text()
                    if response.status != 200:
                        self.logger.error(f"OAuth error: {response.status}, Response: {response_text}")
                        self.logger.error(f"Request headers: {auth_header}")
                        return False
                        
                    try:
                        params = dict(p.split("=") for p in response_text.split("&"))
                        self.oauth_token = params.get("oauth_token")
                        self.oauth_token_secret = params.get("oauth_token_secret")
                        
                        if not self.oauth_token or not self.oauth_token_secret:
                            self.logger.error(f"Missing tokens in response: {response_text}")
                            return False
                            
                        self.logger.info("Successfully obtained OAuth tokens")
                    except Exception as e:
                        self.logger.error(f"Failed to parse response: {response_text}, Error: {str(e)}")
                        return False
                    
                    if not self.oauth_token or not self.oauth_token_secret:
                        self.logger.error("Missing OAuth tokens in response")
                        return False
                        
                    return True
                    
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False
            
    async def post_tweet(self, message: str) -> Optional[Dict]:
        """Post a tweet using OAuth 1.0a"""
        try:
            if not self.oauth_token or not self.oauth_token_secret:
                if not await self.authenticate():
                    return None
                    
            url = "https://api.twitter.com/2/tweets"
            oauth_params = {
                "oauth_consumer_key": self.api_key,
                "oauth_nonce": str(uuid.uuid4()),
                "oauth_signature_method": "HMAC-SHA1",
                "oauth_timestamp": str(int(time.time())),
                "oauth_token": self.oauth_token,
                "oauth_version": "1.0"
            }
            
            # Add message to params for signature
            params = {**oauth_params, "text": message}
            
            oauth_params["oauth_signature"] = self._generate_oauth_signature(
                "POST", url, params
            )
            
            auth_header = "OAuth " + ", ".join([
                f'{quote(k)}="{quote(str(v))}"'
                for k, v in oauth_params.items()
            ])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers={
                        "Authorization": auth_header,
                        "Content-Type": "application/json"
                    },
                    json={"text": message}
                ) as response:
                    if response.status == 201:
                        return await response.json()
                    self.logger.error(f"Tweet error: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Tweet error: {str(e)}")
            return None
