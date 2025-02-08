import json
import aiohttp
from typing import List, Dict, Any, Optional
from ..utils.logging_config import get_logger, DebugCategory
from ..utils.rate_limiter import RateLimiter
from ..utils.retry import async_retry
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.metrics import Metrics


class NewsMonitor:
    def __init__(
        self,
        rate_limiter: RateLimiter,
        metrics: Metrics,
        circuit_breaker: CircuitBreaker
    ):
        self.rate_limiter = rate_limiter
        self.metrics = metrics
        self.circuit_breaker = circuit_breaker
        self.cache: Dict[str, List[Dict[str, Any]]] = {}
        self.logger = get_logger(__name__)

    async def get_latest_news(self) -> List[Dict[str, Any]]:
        """获取最新的Berachain生态新闻"""
        if not await self.rate_limiter.check_rate_limit("news_monitor"):
            self.logger.warning(
                "Rate limit exceeded for news monitor",
                extra={"category": DebugCategory.API.value}
            )
            return self.cache.get("latest_news", [])

        try:
            cached_data = await self.get_cached_news()
            if cached_data:
                return cached_data

            return await self.circuit_breaker.call(
                self._fetch_news
            )
        except Exception as e:
            self.logger.error(
                f"Error fetching news data: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            self.metrics.record_error("news_monitor")
            return self.cache.get(
                "latest_news",
                []
            )

    async def get_cached_news(self) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的新闻数据"""
        try:
            cached_data = await self.rate_limiter.redis_client.get("bera_news")
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            self.logger.error(
                f"Redis cache error: {str(e)}",
                extra={"category": DebugCategory.CACHE.value}
            )
            return None

    def _validate_news_item(self, item: Dict[str, Any]) -> bool:
        """验证新闻数据格式"""
        required_fields = ["title", "summary", "date", "source"]
        return all(
            isinstance(item.get(field), str) and item.get(field)
            for field in required_fields
        )

    @async_retry(retries=3, delay=1.0, exceptions=(aiohttp.ClientError,))
    async def _fetch_news(self) -> List[Dict[str, Any]]:
        """获取新闻数据，使用重试装饰器和断路器"""
        url = "https://berahome.com/api/v1/news"
        self.metrics.start_request("news_monitor")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            # Filter and validate news items
                            news = [
                                item for item in data[:10]  # Get latest 10 news
                                if isinstance(item, dict) and
                                self._validate_news_item(item)
                            ]
                            if news:
                                # Cache valid news data
                                await self.rate_limiter.redis_client.setex(
                                    "bera_news",
                                    600,  # Cache for 10 minutes
                                    json.dumps(news)
                                )
                                self.cache["latest_news"] = news
                                self.metrics.end_request("news_monitor")
                                return news
                            else:
                                self.logger.error(
                                    "No valid news items in response",
                                    extra={"category": DebugCategory.API.value}
                                )
                        else:
                            self.logger.error(
                                "Invalid response format from BeraHome API",
                                extra={"category": DebugCategory.API.value}
                            )
                    else:
                        self.logger.error(
                            f"BeraHome API error: HTTP {response.status}",
                            extra={"category": DebugCategory.API.value}
                        )
                    
                    self.metrics.record_error("news_monitor")
                    return self.cache.get("latest_news", [])

        except Exception as e:
            self.logger.error(
                f"BeraHome API error: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            self.metrics.record_error("news_monitor")
            return self.cache.get("latest_news", [])
