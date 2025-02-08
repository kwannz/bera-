import os
import aiohttp
from typing import Dict, Any
from ..utils.rate_limiter import RateLimiter


class PriceTracker:
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
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
            async with aiohttp.ClientSession() as session:
                # Using CoinGecko API
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": "berachain",
                    "vs_currencies": "usd",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "x_cg_api_key": self.api_key
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.cache["last_price"] = data
                        return data
                    return self.cache.get(
                        "last_price",
                        {"error": "API request failed"}
                    )

        except Exception as e:
            return self.cache.get(
                "last_price",
                {"error": str(e)}
            )
