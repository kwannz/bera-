import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from ..utils.logging_config import get_logger, DebugCategory

@dataclass
class TokenAnalytics:
    price: float
    volume_24h: float
    price_change_24h: float
    timestamp: datetime
    trades_count: int
    high_24h: float
    low_24h: float
    market_cap: Optional[float] = None
    
class AnalyticsCollector:
    def __init__(self):
        self.logger = get_logger(__name__)
        self._analytics_cache: Dict[str, List[TokenAnalytics]] = {}
        self._cache_limit = 1000  # Store last 1000 data points per token
        
    async def collect_analytics(self, token_address: str) -> Optional[TokenAnalytics]:
        try:
            self.logger.debug(
                f"Collecting analytics for {token_address}",
                extra={"category": DebugCategory.ANALYTICS.value}
            )
            
            # Get current price data
            from ..price_tracking.tracker import PriceTracker
            price_tracker = PriceTracker()
            price_data = await price_tracker.get_price_data()
            
            if not price_data:
                self.logger.error(
                    f"Failed to get price data for {token_address}",
                    extra={"category": DebugCategory.ANALYTICS.value}
                )
                return None
                
            analytics = TokenAnalytics(
                price=price_data['price'],
                volume_24h=price_data['volume_24h'],
                price_change_24h=price_data['price_change_24h'],
                timestamp=datetime.now(),
                trades_count=0,  # TODO: Implement trades tracking
                high_24h=price_data.get('high_24h', price_data['price']),
                low_24h=price_data.get('low_24h', price_data['price']),
                market_cap=None  # TODO: Implement market cap calculation
            )
            
            # Update cache
            if token_address not in self._analytics_cache:
                self._analytics_cache[token_address] = []
            
            self._analytics_cache[token_address].append(analytics)
            
            # Maintain cache size limit
            if len(self._analytics_cache[token_address]) > self._cache_limit:
                self._analytics_cache[token_address] = self._analytics_cache[token_address][-self._cache_limit:]
            
            self.logger.debug(
                f"Analytics collected successfully: {analytics}",
                extra={"category": DebugCategory.ANALYTICS.value}
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(
                f"Error collecting analytics: {str(e)}",
                extra={"category": DebugCategory.ANALYTICS.value}
            )
            return None
            
    def get_cached_analytics(self, token_address: str, limit: int = 100) -> List[TokenAnalytics]:
        try:
            self.logger.debug(
                f"Retrieving cached analytics for {token_address}",
                extra={"category": DebugCategory.ANALYTICS.value}
            )
            return self._analytics_cache.get(token_address, [])[-limit:]
        except Exception as e:
            self.logger.error(
                f"Error retrieving cached analytics: {str(e)}",
                extra={"category": DebugCategory.ANALYTICS.value}
            )
            return []
