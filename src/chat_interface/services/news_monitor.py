import aiohttp
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, cast
from ..utils.rate_limiter import RateLimiter


class NewsMonitor:
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.cache: Dict[str, List[Dict[str, Any]]] = {}

    async def get_latest_news(self) -> List[Dict[str, Any]]:
        """获取最新的Berachain生态新闻"""
        if not await self.rate_limiter.check_rate_limit("news_monitor"):
            return self.cache.get("latest_news", [])

        try:
            news = []
            async with aiohttp.ClientSession() as session:
                # BeraHome news
                url = "https://berahome.com/news"
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        news_items = soup.find_all(
                            'article',
                            class_='news-item'
                        )

                        # Get latest 5 news
                        for item in news_items[:5]:
                            item_tag = cast(Tag, item)
                            title_tag = cast(Tag, item_tag.find('h2'))
                            summary_tag = cast(Tag, item_tag.find('p'))
                            date_tag = cast(Tag, item_tag.find('time'))
                            news.append({
                                "title": title_tag.text.strip(),
                                "summary": summary_tag.text.strip(),
                                "date": date_tag.text.strip(),
                                "source": "BeraHome"
                            })

            self.cache["latest_news"] = news
            return news

        except Exception:
            return self.cache.get("latest_news", [])
