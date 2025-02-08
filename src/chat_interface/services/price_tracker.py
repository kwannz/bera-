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
        
        # BeraTrail API configuration
        self.api_key = os.getenv("BERATRAIL_API_KEY")
        self.api_url = os.getenv(
            "BERATRAIL_API_URL",
            "https://beratrail.io/api/v1"  # Default API URL
        )
        
        # Rate limiting configuration
        self.rate_limit = int(os.getenv("BERATRAIL_RATE_LIMIT", "100"))
        self.rate_window = int(os.getenv("BERATRAIL_RATE_WINDOW", "60"))
        
        # Cache configuration
        self.cache_ttl = int(os.getenv("PRICE_CACHE_TTL", "300"))
        self.logger = get_logger(__name__)
        self._initialized = False
        self._last_successful_price: Optional[Dict[str, Any]] = None
        
        # BeraTrail API can be used without API key in free tier
        if not self.api_url:
            self.logger.warning(
                "BERATRAIL_API_URL not set, using default",
                extra={"category": DebugCategory.CONFIG.value}
            )

    async def initialize(self) -> None:
        """Initialize the price tracker service"""
        if self._initialized:
            return
        # Clear any existing cache
        try:
            # Ensure rate_limiter is initialized
            if not hasattr(self.rate_limiter, '_redis_client'):
                await self.rate_limiter.initialize()
            # Clear cache
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
        if not await self.rate_limiter.check_rate_limit(
            "beratrail",
            limit=self.rate_limit,
            window=self.rate_window
        ):
            self.logger.warning(
                "Rate limit exceeded for BeraTrail API",
                extra={"category": DebugCategory.API.value}
            )
            # Return last successful price if available
            if self._last_successful_price:
                return self._last_successful_price
            return {"error": "Rate limit exceeded"}

        try:
            data = await self._fetch_beratrail_price()
            if "error" not in data:
                self._last_successful_price = data
                return data
            
            self.logger.error(
                f"BeraTrail API error: {data.get('error')}",
                extra={"category": DebugCategory.API.value}
            )
            # Return last successful price if available
            if self._last_successful_price:
                return self._last_successful_price
            return data
        except Exception as e:
            self.logger.error(
                f"BeraTrail API failed: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            # Return last successful price if available
            if self._last_successful_price:
                return self._last_successful_price
            return {"error": str(e)}

    async def _fetch_beratrail_price(self) -> Dict[str, Any]:
        """从BeraTrail API获取价格数据"""
        url = f"{self.api_url}/tokens/bera/price"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BeraMonitor/1.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.metrics.start_request("beratrail")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 429:
                        self.logger.warning(
                            "BeraTrail API rate limit exceeded",
                            extra={"category": DebugCategory.API.value}
                        )
                        return {"error": "Rate limit exceeded"}
                        
                    if response.status == 200:
                        data = await response.json()
                        required_fields = ["price", "volume_24h", "price_change_24h"]
                        if all(k in data for k in required_fields):
                            try:
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
                            except (ValueError, TypeError) as e:
                                return await self._handle_api_error(
                                    e,
                                    "BeraTrail",
                                    "Invalid numeric data in response"
                                )

                        return await self._handle_api_error(
                            ValueError("Invalid response format"),
                            "BeraTrail",
                            str(data)
                        )
                    else:
                        response_text = await response.text()
                        return await self._handle_api_error(
                            Exception(f"HTTP {response.status}"),
                            "BeraTrail",
                            response_text
                        )
        except aiohttp.ClientError as e:
            self.logger.error(
                f"BeraTrail API connection error: {str(e)}",
                extra={
                    "category": DebugCategory.API.value,
                    "error_type": "connection"
                }
            )
            return {"error": "Connection error"}
        except Exception as e:
            return await self._handle_api_error(e, "BeraTrail")

    async def _handle_api_error(
        self,
        error: Exception,
        response_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """统一处理BeraTrail API错误"""
        error_msg = str(error)
        if response_text:
            error_msg = f"{error_msg} - Response: {response_text}"
            
        self.logger.error(
            f"BeraTrail API error: {error_msg}",
            extra={
                "category": DebugCategory.API.value,
                "error_type": "api_error"
            }
        )
        self.metrics.record_error("price_tracker_beratrail")
        return {"error": error_msg}

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
