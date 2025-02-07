from typing import Dict, Optional
from datetime import datetime
from ..utils.logging_config import get_logger, DebugCategory
from ..ai_response.model_manager import AIModelManager, ContentType
from ..price_tracking.tracker import PriceTracker
from ..utils.templates import TWEET_TEMPLATE, BEAR_EMOJI
from ..token_analytics.analytics_collector import AnalyticsCollector

class TweetGenerator:
    def __init__(self, model_manager: AIModelManager):
        self.logger = get_logger(__name__)
        self.model_manager = model_manager
        self.price_tracker = PriceTracker()
        self.logger = get_logger(__name__)
        self.analytics_collector = AnalyticsCollector()
        
    async def generate_market_update(self) -> Optional[str]:
        try:
            self.logger.debug(
                "Generating market update tweet",
                extra={"category": DebugCategory.API.value}
            )
            
            price_data = await self.price_tracker.get_price_data()
            if not price_data:
                return None
                
            params = {
                "price": f"${price_data['price']:.2f}",
                "volume": f"${price_data['volume_24h']/1_000_000:.1f}M",
                "change": f"{price_data['price_change_24h']:+.1f}%"
            }
            
            return await self.model_manager.generate_content(
                ContentType.MARKET,
                params
            )
            
        except Exception as e:
            self.logger.error(
                f"Error generating market update: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
            
    async def generate_news_update(self) -> Optional[str]:
        try:
            self.logger.debug(
                "Generating news update tweet",
                extra={"category": DebugCategory.API.value}
            )
            
            news_items = await self.news_monitor.fetch_latest_news()
            if not news_items:
                return None
                
            latest_news = news_items[0]
            params = {
                "news": latest_news['title'],
                "impact": "Growing the Berachain ecosystem"
            }
            
            return await self.model_manager.generate_content(
                ContentType.NEWS,
                params
            )
            
        except Exception as e:
            self.logger.error(
                f"Error generating news update: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
            
    async def generate_ecosystem_update(self) -> Optional[str]:
        try:
            self.logger.debug(
                "Generating ecosystem update tweet",
                extra={"category": DebugCategory.API.value}
            )
            
            # Combine price and news data for ecosystem context
            price_data = await self.price_tracker.get_price_data()
            news_items = await self.news_monitor.fetch_latest_news()
            idos = await self.news_monitor.fetch_upcoming_idos()
            
            if not price_data or not news_items:
                return None
                
            params = {
                "topic": "ecosystem growth",
                "focus": "community and development",
                "points": f"Price: ${price_data['price']:.2f}, "
                         f"News: {news_items[0]['title']}, "
                         f"Upcoming IDOs: {len(idos)}"
            }
            
            return await self.model_manager.generate_content(
                ContentType.TWEET,
                params
            )
            
        except Exception as e:
            self.logger.error(
                f"Error generating ecosystem update: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
            
    async def generate_ido_announcement(self) -> Optional[str]:
        try:
            self.logger.debug(
                "Generating IDO announcement tweet",
                extra={"category": DebugCategory.API.value}
            )
            
            idos = await self.news_monitor.fetch_upcoming_idos()
            if not idos:
                return None
                
            latest_ido = idos[0]
            params = {
                "topic": "upcoming IDO",
                "focus": "project launch",
                "points": f"Project: {latest_ido['name']}, "
                         f"Date: {latest_ido['date']}, "
                         f"Status: {latest_ido['status']}"
            }
            
            return await self.model_manager.generate_content(
                ContentType.TWEET,
                params
            )
            
        except Exception as e:
            self.logger.error(
                f"Error generating IDO announcement: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
