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
        self.api_key = os.getenv("BERATRAIL_API_KEY")
        # 5 minutes default
        self.cache_ttl = int(os.getenv("PRICE_CACHE_TTL", "300"))
        self.api_url = os.getenv(
            "BERATRAIL_API_URL",
            "https://api.beratrail.io/v1"  # Default API URL
        )
        self.logger = get_logger(__name__)
        self._initialized = False
        
        # Validate required configuration
        missing_vars = []
        if not self.api_key:
            missing_vars.append("BERATRAIL_API_KEY")
        if not self.api_url:
            missing_vars.append("BERATRAIL_API_URL")
            
        if missing_vars:
            self.logger.error(
                "Missing required environment variables: " +
                ", ".join(missing_vars),
                extra={"category": DebugCategory.CONFIG.value}
            )

    async def initialize(self) -> None:
        """Initialize the price tracker service"""
        if self._initialized:
            return
        # Clear any existing cache
        try:
            await self.rate_limiter.redis_client.delete("bera_price")
        except Exception as e:
            self.logger.error(
                f"Failed to clear cache during initialization: {str(e)}",
                extra={"category": DebugCategory.CACHE.value}
            )
        self._initialized = True

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
            cached_data = await self.rate_limiter.redis_client.get(
                "bera_price"
            )
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
        # Try BeraTrail API first
        try:
            data = await self._fetch_beratrail_price()
            if "error" not in data:
                return data
        except Exception as e:
            self.logger.warning(
                f"BeraTrail API failed, falling back to CoinGecko: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
        
        # Fallback to CoinGecko
        return await self._fetch_coingecko_price()

    async def _fetch_beratrail_price(self) -> Dict[str, Any]:
        """从BeraTrail API获取价格数据"""
        url = f"{self.api_url}/tokens/bera"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        self.metrics.start_request("beratrail")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        required_fields = ["price", "volume_24h", "price_change_24h"]
                        if all(k in data for k in required_fields):
                            price_data = {
                                "berachain": {
                                    "usd": float(data["price"]),
                                    "usd_24h_vol": float(data["volume_24h"]),
                                    "usd_24h_change": float(data["price_change_24h"])
                                }
                            }
                            await self._cache_price_data(price_data)
                            self.metrics.end_request("beratrail")
                            return price_data

                        self.logger.error(
                            "Invalid response format from BeraTrail API",
                            extra={
                                "category": DebugCategory.API.value,
                                "response": str(data)
                            }
                        )
                        self.metrics.record_error("beratrail")
                        return {"error": "Invalid response format"}
                    else:
                        self.logger.error(
                            f"BeraTrail API error: HTTP {response.status}",
                            extra={
                                "category": DebugCategory.API.value,
                                "response": await response.text()
                            }
                        )
                        self.metrics.record_error("beratrail")
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(
                f"BeraTrail API error: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            self.metrics.record_error("beratrail")
            return {"error": str(e)}

    async def _fetch_coingecko_price(self) -> Dict[str, Any]:
        """从CoinGecko API获取价格数据作为备用"""
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "berachain",
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        headers = {
            "X-CG-API-KEY": os.getenv("COINGECKO_API_KEY")
        }

        self.metrics.start_request("coingecko")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "berachain" in data:
                            bera_data = data["berachain"]
                            price_data = {
                                "berachain": {
                                    "usd": float(bera_data["usd"]),
                                    "usd_24h_vol": float(bera_data.get("usd_24h_vol", 0)),
                                    "usd_24h_change": float(bera_data.get("usd_24h_change", 0))
                                }
                            }
                            await self._cache_price_data(price_data)
                            self.metrics.end_request("coingecko")
                            return price_data

                        self.logger.error(
                            "Invalid response format from CoinGecko API",
                            extra={
                                "category": DebugCategory.API.value,
                                "response": str(data)
                            }
                        )
                        self.metrics.record_error("coingecko")
                        return {"error": "Invalid response format"}
                    else:
                        self.logger.error(
                            f"CoinGecko API error: HTTP {response.status}",
                            extra={
                                "category": DebugCategory.API.value,
                                "response": await response.text()
                            }
                        )
                        self.metrics.record_error("coingecko")
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(
                f"CoinGecko API error: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            self.metrics.record_error("coingecko")
            return {"error": str(e)}

    async def _cache_price_data(self, price_data: Dict[str, Any]) -> None:
        """缓存价格数据到Redis"""
        try:
            await self.rate_limiter.redis_client.setex(
                "bera_price",
                self.cache_ttl,
                json.dumps(price_data)
            )
            self.cache["last_price"] = price_data
        except Exception as e:
            self.logger.error(
                f"Failed to cache price data: {str(e)}",
                extra={"category": DebugCategory.CACHE.value}
            )
