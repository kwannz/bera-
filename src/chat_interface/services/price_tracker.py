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
        
        # OKX API configuration
        self.okx_api_key = os.getenv("OKX_API_KEY")
        self.okx_secret_key = os.getenv("OKX_SECRET_KEY")
        self.okx_url = "https://www.okx.com/api/v5"
        
        # Cache configuration
        self.cache_ttl = int(os.getenv("PRICE_CACHE_TTL", "300"))
        self.logger = get_logger(__name__)
        self._initialized = False
        
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
        
        # Try CoinGecko as first fallback
        try:
            data = await self._fetch_coingecko_price()
            if "error" not in data:
                return data
        except Exception as e:
            self.logger.warning(
                f"CoinGecko API failed, falling back to OKX: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
        
        # Try OKX as second fallback
        return await self._fetch_okx_price()

    async def _fetch_beratrail_price(self) -> Dict[str, Any]:
        """从BeraTrail API获取价格数据"""
        url = f"{self.api_url}/tokens/bera/price"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

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
        except Exception as e:
            return await self._handle_api_error(e, "BeraTrail")

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

                        return await self._handle_api_error(
                            ValueError("Invalid response format"),
                            "CoinGecko",
                            str(data)
                        )
                    else:
                        response_text = await response.text()
                        return await self._handle_api_error(
                            Exception(f"HTTP {response.status}"),
                            "CoinGecko",
                            response_text
                        )
        except Exception as e:
            return await self._handle_api_error(e, "CoinGecko")

    async def _handle_api_error(
        self,
        error: Exception,
        api_name: str,
        response_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """统一处理API错误"""
        error_msg = str(error)
        if response_text:
            error_msg = f"{error_msg} - Response: {response_text}"
            
        self.logger.error(
            f"{api_name} API error: {error_msg}",
            extra={
                "category": DebugCategory.API.value,
                "api": api_name
            }
        )
        self.metrics.record_error(f"price_tracker_{api_name.lower()}")
        return {"error": error_msg}

    async def _fetch_okx_price(self) -> Dict[str, Any]:
        """从OKX API获取价格数据作为第二备用"""
        url = f"{self.okx_url}/market/ticker"
        params = {"instId": "BERA-USDT"}
        headers = {
            "OK-ACCESS-KEY": self.okx_api_key,
            "OK-ACCESS-SIGN": self.okx_secret_key,
            "Content-Type": "application/json"
        }

        self.metrics.start_request("okx")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data") and len(data["data"]) > 0:
                            ticker = data["data"][0]
                            price_data = {
                                "berachain": {
                                    "usd": float(ticker["last"]),
                                    "usd_24h_vol": float(ticker["vol24h"]),
                                    "usd_24h_change": float(ticker.get("volCcy24h", 0))
                                }
                            }
                            await self._cache_price_data(price_data)
                            self.metrics.end_request("okx")
                            return price_data

                        return await self._handle_api_error(
                            ValueError("Invalid response format"),
                            "OKX",
                            str(data)
                        )
                    else:
                        response_text = await response.text()
                        return await self._handle_api_error(
                            Exception(f"HTTP {response.status}"),
                            "OKX",
                            response_text
                        )
        except Exception as e:
            return await self._handle_api_error(e, "OKX")

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
