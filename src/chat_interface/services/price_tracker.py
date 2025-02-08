import os
import aiohttp
from typing import Dict, Any
from ..utils.rate_limiter import RateLimiter
from ..utils.retry import async_retry
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.metrics import Metrics


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

    async def get_price_data(self) -> Dict[str, Any]:
        """获取BERA代币价格数据"""
        if not await self.rate_limiter.check_rate_limit("price_tracker"):
            return self.cache.get(
                "last_price",
                {"error": "Rate limit exceeded"}
            )
        try:
            return await self.circuit_breaker.call(
                self._fetch_price_data
            )
        except Exception as e:
            self.metrics.record_error("price_tracker")
            return self.cache.get(
                "last_price",
                {"error": str(e)}
            )

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
                        self.cache["last_price"] = data
                        self.metrics.end_request("price_tracker")
                        return data
                    else:
                        self.metrics.record_error("price_tracker")
                        return self.cache.get(
                            "last_price",
                            {"error": f"HTTP {response.status}"}
                        )
        except Exception as e:
            self.metrics.record_error("price_tracker")
            return self.cache.get(
                "last_price",
                {"error": str(e)}
            )
