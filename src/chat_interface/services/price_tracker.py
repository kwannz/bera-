import os
import asyncio
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
        return await self._fetch_price_data()

    async def _fetch_price_data(self) -> Dict[str, Any]:

        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "berachain",
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "x_cg_api_key": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                for attempt in range(3):
                    try:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                self.cache["last_price"] = data
                                return data
                            elif attempt < 2:
                                await asyncio.sleep(1 * (attempt + 1))
                                continue
                            else:
                                return self.cache.get(
                                    "last_price",
                                    {
                                        "error": f"HTTP {response.status}"
                                    }
                                )
                    except aiohttp.ClientError:
                        if attempt < 2:
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
                        return self.cache.get(
                            "last_price",
                            {"error": "API connection error"}
                        )

                # If all attempts failed
                return self.cache.get(
                    "last_price",
                    {"error": "All attempts failed"}
                )

        except Exception:
            return self.cache.get(
                "last_price",
                {"error": "Unexpected error"}
            )
