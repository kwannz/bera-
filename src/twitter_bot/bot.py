import tweepy
import asyncio
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from ..ai_response.generator import ResponseGenerator
from ..price_tracking.tracker import PriceTracker
from ..news_monitoring.monitor import NewsMonitor

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
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_secret: str):
        self.auth = tweepy.OAuthHandler(api_key, api_secret)
        self.auth.set_access_token(access_token, access_secret)
        self.api = tweepy.API(self.auth)
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        self.price_tracker = PriceTracker()
        self.news_monitor = NewsMonitor()
        self.response_generator = ResponseGenerator()
        self.last_mention_id: Optional[int] = None
        self.last_price_update = datetime.now() - timedelta(minutes=15)
        
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
            mentions = self.api.mentions_timeline(since_id=self.last_mention_id)
            for mention in mentions:
                await self.handle_mention(mention)
                self.last_mention_id = max(mention.id, self.last_mention_id or 0)
        except Exception as e:
            logger.error(f"Error checking mentions: {str(e)}")
            
    async def handle_mention(self, mention):
        """Handle user mentions with Eliza-style responses"""
        try:
            text = mention.text.lower()
            response = ""
            
            if any(word in text for word in ["ido", "upcoming", "launch"]):
                idos = await self.news_monitor.fetch_upcoming_idos()
                if idos:
                    response = self._format_ido_response(idos[:3])
                else:
                    response = "No upcoming IDOs found at the moment. I'll keep you updated!"
                    
            elif any(word in text for word in ["news", "update", "latest"]):
                news = await self.news_monitor.fetch_latest_news()
                if news:
                    response = self._format_news_response(news[0])
                else:
                    response = "No recent news updates available. Check back soon!"
                    
            elif any(word in text for word in ["price", "bera", "token", "$"]):
                price_data = await self.price_tracker.get_price_data()
                response = self.price_tracker.format_price_report(price_data)
                
            else:
                response = await self.response_generator.generate_response(mention.text)
                
            if response:
                self.client.create_tweet(
                    text=f"@{mention.user.screen_name} {response}"[:280],
                    in_reply_to_tweet_id=mention.id
                )
        except Exception as e:
            logger.error(f"Error handling mention: {str(e)}")
            
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
        """Post scheduled updates (price updates every 15 minutes)"""
        try:
            now = datetime.now()
            if (now - self.last_price_update).total_seconds() >= 900:  # 15 minutes
                price_data = await self.price_tracker.get_price_data()
                if price_data:
                    tweet = self.price_tracker.format_price_report(price_data)
                    self.client.create_tweet(text=tweet)
                    self.last_price_update = now
        except Exception as e:
            logger.error(f"Error posting scheduled update: {str(e)}")
