import aiohttp
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, cast
from ..utils.rate_limiter import RateLimiter
from ..utils.retry import async_retry
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.metrics import Metrics


class NewsMonitor:
    def __init__(
        self,
        rate_limiter: RateLimiter,
        metrics: Metrics,
        circuit_breaker: CircuitBreaker
    ):
        self.rate_limiter = rate_limiter
        self.metrics = metrics
        self.circuit_breaker = circuit_breaker
        self.cache: Dict[str, List[Dict[str, Any]]] = {}

    async def get_latest_news(self) -> List[Dict[str, Any]]:
        """获取最新的Berachain生态新闻"""
        if not await self.rate_limiter.check_rate_limit("news_monitor"):
            return self.cache.get("latest_news", [])

        try:
            return await self.circuit_breaker.call(
                self._fetch_news
            )
        except Exception:
            self.metrics.record_error("news_monitor")
            return self.cache.get(
                "latest_news",
                []
            )

    @async_retry(
        retries=3,
        delay=1.0,
        exceptions=(aiohttp.ClientError, AttributeError)
    )
    async def _fetch_news(self) -> List[Dict[str, Any]]:
        """获取新闻数据，使用重试装饰器和断路器"""
        url = "https://berahome.com/news"
        self.metrics.start_request("news_monitor")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        news_items = soup.find_all(
                            'article',
                            class_='news-item'
                        )

                        news = []
                        # Get latest 5 news
                        for item in news_items[:5]:
                            item_tag = cast(Tag, item)
                            title_tag = cast(Tag, item_tag.find('h2'))
                            summary_tag = cast(Tag, item_tag.find('p'))
                            date_tag = cast(Tag, item_tag.find('time'))
                            required_tags = [
                                title_tag, summary_tag, date_tag
                            ]
                            if all(required_tags):
                                news.append({
                                    "title": title_tag.text.strip(),
                                    "summary": summary_tag.text.strip(),
                                    "date": date_tag.text.strip(),
                                    "source": "BeraHome"
                                })

                        if news:  # Only cache if we got valid news
                            self.cache["latest_news"] = news
                            self.metrics.end_request("news_monitor")
                            return news

                    self.metrics.record_error("news_monitor")
                    return self.cache.get("latest_news", [])

        except Exception:
            self.metrics.record_error("news_monitor")
            return self.cache.get("latest_news", [])
