import asyncio
import logging
import asyncio
import aiohttp
import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from agent_twitter_client import TwitterScraper
from ..ai_response.model_manager import AIModelManager, ContentType
from ..utils.logging_config import get_logger, DebugCategory
from ..utils.rate_limiter import RateLimiter
from ..utils.error_handler import TwitterErrorHandler, RetryAction, TwitterError
from .session_manager import SessionManager

class AuthenticationError(Exception):
    """Raised when authentication with Twitter fails"""
    pass

# Response Templates
TWEET_TEMPLATE = "🐻 {content}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeraBot:
    def __init__(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        two_factor_secret: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        bearer_token: Optional[str] = None
    ):
        self.logger = get_logger(__name__)
        self.username = username
        self.password = password
        self.email = email
        self.two_factor_secret = two_factor_secret
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")

    def __init__(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        two_factor_secret: Optional[str] = None,
        ollama_url: str = "http://localhost:11434"
    ):
        self.logger = get_logger(__name__)
        self.username = username
        self.password = password
        self.email = email
        self.two_factor_secret = two_factor_secret
        
        # Initialize components
        self.scraper = TwitterScraper()
        self.session_manager = SessionManager()
        self.rate_limiter = RateLimiter()
        self.error_handler = TwitterErrorHandler(self.rate_limiter.strategy)
        
        # Authentication state
        self.guest_token: Optional[str] = None
        self.guest_token_created: Optional[datetime] = None
        
        self.logger.info("Initialized Twitter client with scraper, rate limiter and error handler")
        
        # Initialize AI components
        self.model_manager = AIModelManager(
            ollama_url=ollama_url
        )
        # Initialize state
        self.last_mention_id: Optional[int] = None
        self.last_price_update = datetime.now() - timedelta(minutes=15)
        self.last_news_update = datetime.now() - timedelta(hours=1)
        
    async def get_csrf_token(self) -> Optional[str]:
        """Get CSRF token from cookies"""
        cookies = await self.session_manager.load_cookies()
        for cookie in cookies:
            if cookie["name"] == "ct0":
                return cookie["value"]
        return None
        
    async def prepare_headers(self) -> Dict[str, str]:
        """Prepare headers with proper tokens"""
        headers = {
            "Authorization": f"Bearer {self.BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        
        if self.guest_token:
            headers["x-guest-token"] = self.guest_token
            
        if csrf_token := await self.get_csrf_token():
            headers["x-csrf-token"] = csrf_token
            
        return headers
        
    def should_refresh_token(self) -> bool:
        """Check if guest token needs refresh (3 hour expiration)"""
        if not self.guest_token or not self.guest_token_created:
            return True
            
        expiration = timedelta(hours=3)
        return datetime.now() - self.guest_token_created > expiration
        
    async def ensure_authenticated(self):
        """Ensure valid authentication before requests"""
        if self.should_refresh_token():
            if not await self.authenticate():
                raise AuthenticationError("Failed to refresh authentication")
                
    async def authenticate(self) -> bool:
        """Authenticate with Twitter using guest token flow"""
        try:
            headers = await self.prepare_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.twitter.com/1.1/guest/activate.json",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise AuthenticationError(f"Failed to get guest token: {response.status}")
                        
                    data = await response.json()
                    if "guest_token" not in data:
                        raise AuthenticationError("Invalid guest token response")
                        
                    self.guest_token = data["guest_token"]
                    self.guest_token_created = datetime.now()
                    
                    # Update cookies from response
                    cookies = response.cookies
                    await self.session_manager.save_cookies([
                        {"name": c.key, "value": c.value}
                        for c in cookies.values()
                    ])
                    
            return True
        except Exception as e:
            action, wait_time = await self.error_handler.handle_error(e, "authenticate")
            if action == RetryAction.WAIT_AND_RETRY:
                await asyncio.sleep(wait_time)
                return await self.authenticate()
            return False
        
    async def restore_session(self) -> bool:
        """Attempt to restore previous session from cookies
        
        Returns:
            bool: True if session restored successfully, False otherwise
        """
        try:
            cookies = await self.session_manager.load_cookies()
            if cookies:
                await self.scraper.setCookies(cookies)
                if await self.scraper.isLoggedIn():
                    self.logger.info("Successfully restored session from cookies")
                    return True
        except Exception as e:
            self.logger.error(
                f"Failed to restore session: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
        return False
        
    async def start(self):
        """Start the bot's main loop"""
        try:
            self.logger.info("Attempting to restore previous session...")
            if not await self.restore_session():
                self.logger.info("No valid session found, logging in...")
                try:
                    await self.login()
                except AuthenticationError as e:
                    self.logger.error(
                        str(e),
                        extra={"category": DebugCategory.API.value}
                    )
                    return
                
            self.logger.info("Successfully logged in to Twitter")
            
            while True:
                try:
                    await self.check_mentions()
                    await self.check_scheduled_updates()
                    await asyncio.sleep(60)
                except Exception as e:
                    self.logger.error(
                        f"Error in main loop: {str(e)}",
                        extra={"category": DebugCategory.API.value}
                    )
                    await asyncio.sleep(60)
        except Exception as e:
            self.logger.error(
                f"Error during Twitter login: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
                
    async def check_mentions(self):
        """Check and respond to mentions"""
        try:
            await self.ensure_authenticated()
            await self.rate_limiter.acquire("/api/mentions")
            mentions = await self.scraper.get_mentions(since_id=self.last_mention_id)
            for mention in mentions:
                await self.handle_mention(mention)
                self.last_mention_id = max(mention.id, self.last_mention_id or 0)
        except Exception as e:
            action = await self.error_handler.handle_error(e, "check_mentions")
            if action == RetryAction.WAIT_AND_RETRY:
                await asyncio.sleep(60)  # Wait before retry
            elif action == RetryAction.RETRY_IMMEDIATELY:
                await self.check_mentions()  # Retry immediately
            
    async def handle_mention(self, mention):
        """Handle user mentions with AI-powered responses"""
        try:
            await self.ensure_authenticated()
            await self.rate_limiter.acquire("/api/tweets")
            text = mention.text.lower()
            
            # Build context for AI response
            context = {
                "topic": "general",
                "data": {},
                "query_type": "general"
            }
            
            if "ido" in text or "upcoming" in text or "launch" in text:
                context = {
                    "topic": "IDO information",
                    "query_type": "ido"
                }
            elif "news" in text or "update" in text or "latest" in text:
                context = {
                    "topic": "ecosystem news",
                    "query_type": "news"
                }
            elif "price" in text or "bera" in text or "token" in text or "$" in text:
                context = {
                    "topic": "market data",
                    "query_type": "price"
                }
                
            # Generate AI response with context
            response = await self.model_manager.generate_content(
                ContentType.REPLY,
                {
                    "query": mention.text,
                    "context": str(context)
                }
            )
            
            if response:
                await self.scraper.send_tweet(
                    text=f"@{mention.user.screen_name} {response}"[:280],
                    reply_to=mention.id
                )
                
        except Exception as e:
            action = await self.error_handler.handle_error(e, "handle_mention")
            if action == RetryAction.WAIT_AND_RETRY:
                await asyncio.sleep(60)  # Wait before retry
                await self.handle_mention(mention)
            elif action == RetryAction.RETRY_IMMEDIATELY:
                await self.handle_mention(mention)
            
    def _format_tweet(self, content: str) -> str:
        """Format tweet with bear theme"""
        return TWEET_TEMPLATE.format(content=content)[:280]
        
    async def check_scheduled_updates(self):
        """Post scheduled updates"""
        try:
            now = datetime.now()
            
            # Price updates every 15 minutes
            if (now - self.last_price_update).total_seconds() >= 900:
                response = await self.model_manager.generate_content(
                    ContentType.MARKET,
                    {
                        "price": "10.5",
                        "volume": "1M",
                        "change": "+5.2"
                    }
                )
                if response:
                    tweet = self._format_tweet(response)
                    await self.scraper.send_tweet(text=tweet)
                    self.last_price_update = now
                    
            # News updates every hour
            if (now - self.last_news_update).total_seconds() >= 3600:
                response = await self.model_manager.generate_content(
                    ContentType.NEWS,
                    {
                        "news": "Latest ecosystem update",
                        "impact": "Growing ecosystem"
                    }
                )
                if response:
                    tweet = self._format_tweet(response)
                    await self.scraper.send_tweet(text=tweet)
                    self.last_news_update = now
                    
        except Exception as e:
            self.logger.error(
                f"Error posting scheduled update: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
