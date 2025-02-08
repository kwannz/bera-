import os
import asyncio
import aiohttp
from typing import Dict, Any
import json
from ..utils.rate_limiter import RateLimiter


class AnalyticsCollector:
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.api_key = os.getenv("DEEPSEEK_API_KEY")

    async def _get_price_change(self) -> Dict[str, float]:
        """获取价格变化数据"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": "berachain",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_7d_change": "true",
                    "x_cg_api_key": self.api_key
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "24h": data["berachain"]["usd_24h_change"],
                            "7d": data["berachain"]["usd_7d_change"]
                        }
        except Exception:
            pass
        return {"24h": 0.0, "7d": 0.0}

    async def _get_social_metrics(self) -> Dict[str, int]:
        """获取社交媒体指标"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.coingecko.com/api/v3/coins/berachain"
                params = {"x_cg_api_key": self.api_key}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "mentions": (
                                data["community_data"]["twitter_followers"]
                            ),
                            "sentiment_score": (
                                data["sentiment_votes_up_percentage"]
                            )
                        }
        except Exception:
            pass
        return {"mentions": 0, "sentiment_score": 0}

    async def analyze_market_sentiment(self) -> Dict[str, Any]:
        """分析市场情绪"""
        if not await self.rate_limiter.check_rate_limit("analytics"):
            return self.cache.get("sentiment", {"sentiment": "neutral"})

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Collect data points for analysis
            price_change = await self._get_price_change()
            social_metrics = await self._get_social_metrics()

            # Use Deepseek API for sentiment analysis
            async with aiohttp.ClientSession() as session:
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

                for attempt in range(3):
                    try:
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
                                self.cache["sentiment"] = analysis
                                return analysis
                            elif attempt < 2:
                                await asyncio.sleep(1 * (attempt + 1))
                                continue
                            else:
                                return self.cache.get(
                                    "sentiment",
                                    {"sentiment": "neutral"}
                                )
                    except aiohttp.ClientError:
                        if attempt < 2:
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
                        return self.cache.get(
                            "sentiment",
                            {"sentiment": "neutral"}
                        )

            return self.cache.get("sentiment", {"sentiment": "neutral"})

        except Exception:
            return self.cache.get(
                "sentiment",
                {"sentiment": "neutral"}
            )
