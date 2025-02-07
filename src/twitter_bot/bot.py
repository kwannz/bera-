import asyncio
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from agent_twitter_client import TwitterScraper
from ..ai_response.generator import ResponseGenerator
from ..ai_response.model_manager import AIModelManager, ModelType, ContentType
from ..price_tracking.tracker import PriceTracker
from ..news_monitoring.monitor import NewsMonitor
from .tweet_generator import TweetGenerator
from ..utils.logging_config import get_logger, DebugCategory

# Response Templates
PRICE_UPDATE_TEMPLATE = "🐻 BERA Update: ${price} | Vol: ${volume} | ${change}% 24h\n📊 {market_sentiment}"
NEWS_UPDATE_TEMPLATE = "📰 Berachain Update: {title}\n🔍 Key points: {summary}\n🌟 Impact: {relevance}"
TECHNICAL_RESPONSE_TEMPLATE = "🛠️ {explanation}\n📚 Learn more: {doc_link}\n🐼 Need help? Just ask!"
IDO_UPDATE_TEMPLATE = "🚀 New IDO Alert: {project}\n📅 Timeline: {dates}\n💡 Quick facts: {key_points}"

# Emoji Constants
BEAR_EMOJI = "🐻"
PANDA_EMOJI = "🐼"
CHART_EMOJI = "📊"
NEWS_EMOJI = "📰"
ROCKET_EMOJI = "🚀"
TOOLS_EMOJI = "🛠️"
BOOKS_EMOJI = "📚"
MAGNIFY_EMOJI = "🔍"
STAR_EMOJI = "🌟"
BULB_EMOJI = "💡"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeraBot:
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
        
        # Initialize Twitter client
        self.scraper = TwitterScraper()
        self.logger.info("Initialized Twitter client with scraper")
        
        # Initialize AI components
        self.model_manager = AIModelManager(
            ollama_url=ollama_url
        )
        self.tweet_generator = TweetGenerator(self.model_manager)
        self.response_generator = ResponseGenerator()
        
        # Initialize data components
        self.price_tracker = PriceTracker()
        self.news_monitor = NewsMonitor()
        
        # Initialize state
        self.last_mention_id: Optional[int] = None
        self.last_price_update = datetime.now() - timedelta(minutes=15)
        self.last_news_update = datetime.now() - timedelta(hours=1)
        
    async def start(self):
        """Start the bot's main loop"""
        while True:
            try:
                await self.check_mentions()
                await self.check_scheduled_updates()
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(60)
                
    async def check_mentions(self):
        """Check and respond to mentions"""
        try:
            mentions = await self.scraper.get_mentions(since_id=self.last_mention_id)
            for mention in mentions:
                await self.handle_mention(mention)
                self.last_mention_id = max(mention.id, self.last_mention_id or 0)
        except Exception as e:
            logger.error(f"Error checking mentions: {str(e)}")
            
    async def handle_mention(self, mention):
        """Handle user mentions with AI-powered responses"""
        try:
            text = mention.text.lower()
            context = {}
            
            # Build context for AI response
            if any(word in text for word in ["ido", "upcoming", "launch"]):
                idos = await self.news_monitor.fetch_upcoming_idos()
                context = {
                    "topic": "IDO information",
                    "data": idos if idos else [],
                    "query_type": "ido"
                }
                
            elif any(word in text for word in ["news", "update", "latest"]):
                news = await self.news_monitor.fetch_latest_news()
                context = {
                    "topic": "ecosystem news",
                    "data": news if news else [],
                    "query_type": "news"
                }
                
            elif any(word in text for word in ["price", "bera", "token", "$"]):
                price_data = await self.price_tracker.get_price_data()
                context = {
                    "topic": "market data",
                    "data": price_data if price_data else {},
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
            self.logger.error(
                f"Error handling mention: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            
    def _format_ido_response(self, idos: List[Dict]) -> str:
        responses = []
        for ido in idos:
            response = IDO_UPDATE_TEMPLATE.format(
                project=ido['name'],
                dates=ido['date'],
                key_points=ido['status']
            )
            responses.append(response)
        return "\n\n".join(responses)[:280]
        
    def _format_news_response(self, news: Dict) -> str:
        return NEWS_UPDATE_TEMPLATE.format(
            title=news['title'][:50] + "..." if len(news['title']) > 50 else news['title'],
            summary=news['summary'][:100] + "..." if len(news['summary']) > 100 else news['summary'],
            relevance="Growing the Berachain ecosystem! 🌱"
        )[:280]
        
    async def check_scheduled_updates(self):
        """Post scheduled updates"""
        try:
            now = datetime.now()
            
            # Price updates every 15 minutes
            if (now - self.last_price_update).total_seconds() >= 900:
                tweet = await self.tweet_generator.generate_market_update()
                if tweet:
                    await self.scraper.send_tweet(text=tweet)
                    self.last_price_update = now
                    
            # News updates every hour
            if (now - self.last_news_update).total_seconds() >= 3600:
                tweet = await self.tweet_generator.generate_news_update()
                if tweet:
                    await self.scraper.send_tweet(text=tweet)
                    self.last_news_update = now
                    
                # Also check for ecosystem updates
                tweet = await self.tweet_generator.generate_ecosystem_update()
                if tweet:
                    await self.scraper.send_tweet(text=tweet)
                    
                # Check for IDO announcements
                tweet = await self.tweet_generator.generate_ido_announcement()
                if tweet:
                    await self.scraper.send_tweet(text=tweet)
                    
        except Exception as e:
            self.logger.error(
                f"Error posting scheduled update: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
