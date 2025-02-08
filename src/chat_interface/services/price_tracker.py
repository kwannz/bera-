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
        url = f"{self.api_url}/tokens/bera"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        self.metrics.start_request("price_tracker")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        required_fields = ["price", "volume_24h", "price_change_24h"]
                        if all(k in data for k in required_fields):
                            # Transform to match expected format
                            price_data = {
                                "berachain": {
                                    "usd": float(data["price"]),
                                    "usd_24h_vol": float(data["volume_24h"]),
                                    "usd_24h_change": float(data["price_change_24h"])
                                }
                            }
                            # Cache the valid response
                            try:
                                await self.rate_limiter.redis_client.setex(
                                    "bera_price",
                                    self.cache_ttl,
                                    json.dumps(price_data)
                                )
                            except Exception as e:
                                self.logger.error(
                                    "Failed to cache price data: "
                                    f"{str(e)}",
                                    extra={
                                        "category": DebugCategory.CACHE.value
                                    }
                                )
                            self.cache["last_price"] = price_data
                            self.metrics.end_request("price_tracker")
                            return price_data

                        self.logger.error(
                            "Invalid response format from BeraTrail API",
                            extra={
                                "category": DebugCategory.API.value,
                                "response": str(data)
                            }
                        )
                        self.metrics.record_error("price_tracker")
                        return {"error": "Invalid response format"}
                    else:
                        self.logger.error(
                            f"BeraTrail API error: HTTP {response.status}",
                            extra={
                                "category": DebugCategory.API.value,
                                "response": await response.text()
                            }
                        )
                        self.metrics.record_error("price_tracker")
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(
                f"BeraTrail API error: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            self.metrics.record_error("price_tracker")
            return {"error": str(e)}
