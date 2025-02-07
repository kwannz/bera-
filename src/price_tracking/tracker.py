import requests
from typing import Dict, Optional
from datetime import datetime, timedelta

from ..twitter_bot.twitter_client import TwitterClient
from ..utils.logging_config import get_logger, DebugCategory

BEAR_EMOJI = "🐻"
PRICE_UPDATE_TEMPLATE = "{emoji} BERA: ${price} | Volume: ${volume} | {change_24h}% 24h"

class PriceTracker:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.base_url = "https://beratrail.io/api/v1"
        self.previous_price = None
        self.last_update = None
        
    async def get_price_data(self):
        try:
            self.logger.debug(
                "Fetching BERA price data from beratrail.io",
                extra={"category": DebugCategory.PRICE.value}
            )
            
            response = requests.get(f"{self.base_url}/tokens/bera")
            data = response.json()
            
            self.logger.debug(
                f"Raw API response: {data}",
                extra={"category": DebugCategory.PRICE.value}
            )
            
            current_price = float(data['price'])
            current_time = datetime.now()
            
            self.logger.debug(
                f"Price data received: price={current_price}, time={current_time}",
                extra={"category": DebugCategory.PRICE.value}
            )
            
            price_change_24h = 0
            if self.previous_price and self.last_update:
                time_diff = current_time - self.last_update
                if time_diff.total_seconds() >= 86400:
                    price_change_24h = ((current_price - self.previous_price) / self.previous_price) * 100
                    self.logger.debug(
                        f"Calculated 24h price change: {price_change_24h}%",
                        extra={"category": DebugCategory.PRICE.value}
                    )
            
            self.previous_price = current_price
            self.last_update = current_time
            
            result = {
                "price": current_price,
                "volume_24h": float(data['volume_24h']),
                "price_change_24h": price_change_24h
            }
            
            self.logger.debug(
                f"Returning price data: {result}",
                extra={"category": DebugCategory.PRICE.value}
            )
            
            return result
        except Exception as e:
            self.logger.error(
                f"Error fetching BERA price data: {str(e)}",
                extra={"category": DebugCategory.PRICE.value}
            )
            return None
            
    def format_price_report(self, data: Dict) -> str:
        if not data:
            return f"{BEAR_EMOJI} Price data unavailable"
        
        volume = data['volume_24h']
        volume_str = f"${volume/1_000_000_000:.1f}B" if volume >= 1_000_000_000 else f"${volume/1_000_000:.1f}M"
        
        sentiment = "Bullish 📈" if data['price_change_24h'] > 0 else "Bearish 📉"
        
        return PRICE_UPDATE_TEMPLATE.format(
            emoji=BEAR_EMOJI,
            price=f"{data['price']:.2f}",
            volume=volume_str,
            change_24h=f"{data['price_change_24h']:+.1f}"
        )
