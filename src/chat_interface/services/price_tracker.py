import os
import json
import aiohttp
from typing import Dict, Any, Optional
from ..utils.rate_limiter import RateLimiter
from ..utils.retry import async_retry
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.metrics import Metrics
from ..utils.logging_config import get_logger, DebugCategory


class PriceTracker:
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
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.cache_ttl = int(os.getenv("PRICE_CACHE_TTL", "300"))  # 5 minutes default
        self.logger = get_logger(__name__)
        
        if not self.api_key:
            self.logger.error(
                "Missing required environment variable: COINGECKO_API_KEY",
                extra={"category": DebugCategory.CONFIG.value}
            )

    async def get_price_data(self) -> Dict[str, Any]:
        """获取BERA代币价格数据"""
        if not await self.rate_limiter.check_rate_limit("price_tracker"):
            self.logger.warning(
                "Rate limit exceeded for price tracker",
                extra={"category": DebugCategory.API.value}
            )
            return self.cache.get(
                "last_price",
                {"error": "Rate limit exceeded"}
            )

        try:
            cached_data = await self.get_cached_price()
            if cached_data:
                return cached_data

            return await self.circuit_breaker.call(
                self._fetch_price_data
            )
        except Exception as e:
            self.logger.error(
                f"Error fetching price data: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            self.metrics.record_error("price_tracker")
            return self.cache.get(
                "last_price",
                {"error": str(e)}
            )

    async def get_cached_price(self) -> Optional[Dict[str, Any]]:
        """获取缓存的价格数据"""
        try:
            cached_data = await self.rate_limiter.redis_client.get("bera_price")
            if not cached_data:
                return None

            try:
                data = json.loads(cached_data)
                if not isinstance(data, dict) or "berachain" not in data:
                    self.logger.warning(
                        "Invalid cache data format",
                        extra={"category": DebugCategory.CACHE.value}
                    )
                    await self.rate_limiter.redis_client.delete("bera_price")
                    return None
                return data
            except json.JSONDecodeError:
                self.logger.error(
                    "Failed to parse cached data",
                    extra={"category": DebugCategory.CACHE.value}
                )
                await self.rate_limiter.redis_client.delete("bera_price")
                return None
        except Exception as e:
            self.logger.error(
                f"Redis cache error: {str(e)}",
                extra={"category": DebugCategory.CACHE.value}
            )
            return None

    @async_retry(retries=3, delay=1.0, exceptions=(aiohttp.ClientError,))
    async def _fetch_price_data(self) -> Dict[str, Any]:
        """获取价格数据，使用重试装饰器和断路器"""
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "berachain",
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "x_cg_api_key": self.api_key
        }

        self.metrics.start_request("price_tracker")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "berachain" in data:
                            # Cache the valid response
                            try:
                                await self.rate_limiter.redis_client.setex(
                                    "bera_price",
                                    self.cache_ttl,
                                    json.dumps(data)
                                )
                            except Exception as e:
                                self.logger.error(
                                    f"Failed to cache price data: {str(e)}",
                                    extra={"category": DebugCategory.CACHE.value}
                                )
                            self.cache["last_price"] = data
                            self.metrics.end_request("price_tracker")
                            return data
                        else:
                            self.logger.error(
                                "Invalid response format from CoinGecko API",
                                extra={"category": DebugCategory.API.value}
                            )
                            self.metrics.record_error("price_tracker")
                            return self.cache.get(
                                "last_price",
                                {"error": "Invalid response format"}
                            )
                    else:
                        self.logger.error(
                            f"CoinGecko API error: HTTP {response.status}",
                            extra={"category": DebugCategory.API.value}
                        )
                        self.metrics.record_error("price_tracker")
                        return self.cache.get(
                            "last_price",
                            {"error": f"HTTP {response.status}"}
                        )
        except Exception as e:
            self.logger.error(
                f"CoinGecko API error: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            self.metrics.record_error("price_tracker")
            return self.cache.get(
                "last_price",
                {"error": str(e)}
            )
