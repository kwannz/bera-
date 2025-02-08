import os
import aiohttp
from typing import Dict, Any, Optional
import json
from ..utils.rate_limiter import RateLimiter
from ..utils.retry import async_retry
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.metrics import Metrics
from ..utils.logging_config import get_logger, DebugCategory


class AnalyticsCollector:
    def __init__(
        self,
        rate_limiter: RateLimiter,
        metrics: Metrics,
        circuit_breaker: CircuitBreaker
    ):
        self.rate_limiter = rate_limiter
        self.metrics = metrics
        self.circuit_breaker = circuit_breaker
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.logger = get_logger(__name__)
        self.cache_ttl = int(os.getenv("SENTIMENT_CACHE_TTL", "300"))  # 5 minutes default
        self.api_key = os.getenv("DEEPSEEK_API_KEY")

    @async_retry(retries=3, delay=1.0, exceptions=(aiohttp.ClientError,))
    async def _get_price_change(self) -> Dict[str, float]:
        """获取价格变化数据"""
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "berachain",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_7d_change": "true",
            "x_cg_api_key": self.api_key
        }

        self.metrics.start_request("analytics_price")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = {
                            "24h": data["berachain"]["usd_24h_change"],
                            "7d": data["berachain"]["usd_7d_change"]
                        }
                        self.metrics.end_request("analytics_price")
                        return result
                    self.metrics.record_error("analytics_price")
        except Exception:
            self.metrics.record_error("analytics_price")
        return {"24h": 0.0, "7d": 0.0}

    @async_retry(retries=3, delay=1.0, exceptions=(aiohttp.ClientError,))
    async def _get_social_metrics(self) -> Dict[str, int]:
        """获取社交媒体指标"""
        url = "https://api.coingecko.com/api/v3/coins/berachain"
        params = {"x_cg_api_key": self.api_key}

        self.metrics.start_request("analytics_social")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = {
                            "mentions": (
                                data["community_data"]["twitter_followers"]
                            ),
                            "sentiment_score": (
                                data["sentiment_votes_up_percentage"]
                            )
                        }
                        self.metrics.end_request("analytics_social")
                        return result
                    self.metrics.record_error("analytics_social")
        except Exception:
            self.metrics.record_error("analytics_social")
        return {"mentions": 0, "sentiment_score": 0}

    async def get_cached_sentiment(self) -> Optional[Dict[str, Any]]:
        """获取缓存的情绪数据"""
        try:
            cached_data = await self.rate_limiter.redis_client.get("bera_sentiment")
            if not cached_data:
                return None

            try:
                data = json.loads(cached_data)
                if not isinstance(data, dict) or "sentiment" not in data:
                    self.logger.warning(
                        "Invalid sentiment cache data format",
                        extra={"category": DebugCategory.CACHE.value}
                    )
                    await self.rate_limiter.redis_client.delete("bera_sentiment")
                    return None
                return data
            except json.JSONDecodeError:
                self.logger.error(
                    "Failed to parse cached sentiment data",
                    extra={"category": DebugCategory.CACHE.value}
                )
                await self.rate_limiter.redis_client.delete("bera_sentiment")
                return None
        except Exception as e:
            self.logger.error(
                f"Redis cache error: {str(e)}",
                extra={"category": DebugCategory.CACHE.value}
            )
            return None

    async def analyze_market_sentiment(self) -> Dict[str, Any]:
        """分析市场情绪"""
        if not await self.rate_limiter.check_rate_limit("analytics"):
            self.logger.warning(
                "Rate limit exceeded for sentiment analysis",
                extra={"category": DebugCategory.API.value}
            )
            return self.cache.get("sentiment", {"sentiment": "neutral"})

        try:
            cached_data = await self.get_cached_sentiment()
            if cached_data:
                return cached_data

            return await self.circuit_breaker.call(
                self._analyze_sentiment
            )
        except Exception as e:
            self.logger.error(
                f"Error analyzing sentiment: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            self.metrics.record_error("analytics")
            return self.cache.get(
                "sentiment",
                {"sentiment": "neutral"}
            )

    @async_retry(retries=3, delay=1.0, exceptions=(aiohttp.ClientError,))
    async def _analyze_sentiment(self) -> Dict[str, Any]:
        """使用Deepseek API分析市场情绪"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Collect data points for analysis
        price_change = await self._get_price_change()
        social_metrics = await self._get_social_metrics()

        url = "https://api.deepseek.com/api/v3/chat/completions"
        data = {
            "model": "deepseek-r1:1.5b",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Analyze market sentiment based on "
                        "price and social metrics."
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "price_change": price_change,
                        "social_metrics": social_metrics
                    })
                }
            ]
        }

        self.metrics.start_request("analytics")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        analysis = {
                            "sentiment": (
                                result["choices"][0]["message"]
                                ["content"]
                            ),
                            "confidence": 0.8,
                            "timestamp": "now"
                        }
                        try:
                            await self.rate_limiter.redis_client.setex(
                                "bera_sentiment",
                                self.cache_ttl,
                                json.dumps(analysis)
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Failed to cache sentiment data: {str(e)}",
                                extra={"category": DebugCategory.CACHE.value}
                            )
                        self.cache["sentiment"] = analysis
                        self.metrics.end_request("analytics")
                        return analysis
                    self.metrics.record_error("analytics")
                    return self.cache.get(
                        "sentiment",
                        {"sentiment": "neutral"}
                    )
        except Exception:
            self.metrics.record_error("analytics")
            return self.cache.get(
                "sentiment",
                {"sentiment": "neutral"}
            )
