import os
import json
import aiohttp
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Set
from ..utils.logging_config import get_logger, DebugCategory
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
        self.logger = get_logger(__name__)
        self.cache_ttl = int(os.getenv("NEWS_CACHE_TTL", "86400"))  # 24 hours default
        self.substack_url = os.getenv(
            "BERAHOME_SUBSTACK_URL",
            "https://berahome.substack.com"
        )

    async def get_latest_news(self) -> List[Dict[str, Any]]:
        """获取最新的Berachain生态新闻"""
        if not await self.rate_limiter.check_rate_limit("news_monitor"):
            self.logger.warning(
                "Rate limit exceeded for news monitor",
                extra={"category": DebugCategory.API.value}
            )
            return await self._get_cached_articles() or []

        try:
            # Check cache first
            cached_articles = await self._get_cached_articles()
            if cached_articles:
                return cached_articles

            # Fetch and process articles
            articles = await self.circuit_breaker.call(
                self._fetch_and_process_articles
            )

            if articles:
                # Update cache and index
                await self._update_cache_and_index(articles)
                return articles

            return []
        except Exception as e:
            self.logger.error(
                f"Error fetching news data: {str(e)}",
                extra={
                    "category": DebugCategory.API.value,
                    "error_type": type(e).__name__
                }
            )
            self.metrics.record_error("news_monitor")
            return []

    async def _get_cached_articles(self) -> Optional[List[Dict[str, Any]]]:
        """从Redis获取缓存的文章数据"""
        try:
            # Get article IDs from index
            article_ids = await self.rate_limiter.redis_client.smembers("bera_articles:index")
            if not article_ids:
                return None

            # Get articles from cache
            articles = []
            for article_id in article_ids:
                article_data = await self.rate_limiter.redis_client.get(f"bera_articles:{article_id}")
                if article_data:
                    try:
                        article = json.loads(article_data)
                        if self._validate_article(article):
                            articles.append(article)
                    except json.JSONDecodeError:
                        self.logger.error(
                            f"Failed to parse article data for ID: {article_id}",
                            extra={"category": DebugCategory.CACHE.value}
                        )
                        continue

            if not articles:
                self.logger.warning(
                    "No valid articles in cache",
                    extra={"category": DebugCategory.CACHE.value}
                )
                return None

            return sorted(
                articles,
                key=lambda x: datetime.fromisoformat(x["date"]),
                reverse=True
            )
        except Exception as e:
            self.logger.error(
                f"Redis cache error: {str(e)}",
                extra={"category": DebugCategory.CACHE.value}
            )
            return None

    def _validate_article(self, article: Dict[str, Any]) -> bool:
        """验证文章数据格式"""
        required_fields = ["title", "content", "date", "url", "summary"]
        return all(
            isinstance(article.get(field), str) and article.get(field)
            for field in required_fields
        )

    @async_retry(retries=3, delay=1.0, exceptions=(aiohttp.ClientError,))
    async def _fetch_and_process_articles(self) -> List[Dict[str, Any]]:
        """获取并处理文章内容"""
        self.metrics.start_request("news_monitor")
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch main page to get article links
                async with session.get(self.substack_url) as response:
                    if response.status != 200:
                        self.logger.error(
                            f"Failed to fetch BeraHome main page: {response.status}",
                            extra={"category": DebugCategory.SCRAPING.value}
                        )
                        self.metrics.record_error("news_monitor")
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    article_links = self._extract_article_links(soup)

                    # Fetch and process articles
                    articles = []
                    for url in article_links[:10]:  # Process latest 10 articles
                        try:
                            article = await self._fetch_article(session, url)
                            if article:
                                articles.append(article)
                        except Exception as e:
                            self.logger.error(
                                f"Error processing article {url}: {str(e)}",
                                extra={
                                    "category": DebugCategory.SCRAPING.value,
                                    "url": url
                                }
                            )
                            continue

                    self.metrics.end_request("news_monitor")
                    return articles

        except Exception as e:
            self.logger.error(
                f"Error in article scraping: {str(e)}",
                extra={
                    "category": DebugCategory.SCRAPING.value,
                    "error_type": type(e).__name__
                }
            )
            self.metrics.record_error("news_monitor")
            return []

    def _extract_article_links(self, soup: BeautifulSoup) -> Set[str]:
        """从页面提取文章链接"""
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/p/' in href and href.startswith(('http://berahome.substack.com', 'https://berahome.substack.com')):
                links.add(href)
        return links

    async def _fetch_article(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict[str, Any]]:
        """获取并解析单篇文章"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.error(
                        f"Failed to fetch article {url}: {response.status}",
                        extra={"category": DebugCategory.SCRAPING.value}
                    )
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract article data
                title = soup.find('h1').get_text().strip() if soup.find('h1') else None
                content = soup.find('article').get_text().strip() if soup.find('article') else None
                date_elem = soup.find('time')
                date = date_elem.get('datetime') if date_elem else None

                if not all([title, content, date]):
                    self.logger.warning(
                        f"Missing required fields for article {url}",
                        extra={"category": DebugCategory.SCRAPING.value}
                    )
                    return None

                # Generate article ID
                article_id = hashlib.sha256(url.encode()).hexdigest()[:16]

                # Create article object
                article = {
                    "id": article_id,
                    "title": title,
                    "content": content,
                    "summary": content[:200] + "..." if len(content) > 200 else content,
                    "date": date,
                    "url": url
                }

                return article

        except Exception as e:
            self.logger.error(
                f"Error processing article {url}: {str(e)}",
                extra={
                    "category": DebugCategory.SCRAPING.value,
                    "error_type": type(e).__name__
                }
            )
            return None

    async def _update_cache_and_index(self, articles: List[Dict[str, Any]]) -> None:
        """更新Redis缓存和索引"""
        try:
            pipeline = self.rate_limiter.redis_client.pipeline()

            # Update article index
            article_ids = set()
            for article in articles:
                article_id = article["id"]
                article_ids.add(article_id)

                # Store article
                pipeline.setex(
                    f"bera_articles:{article_id}",
                    self.cache_ttl,
                    json.dumps(article)
                )

                # Update date index
                date = datetime.fromisoformat(article["date"])
                date_key = date.strftime("%Y-%m")
                pipeline.sadd(f"bera_articles:dates:{date_key}", article_id)

                # Update keyword index (simple word-based)
                keywords = set(
                    word.lower()
                    for word in f"{article['title']} {article['summary']}".split()
                    if len(word) > 3
                )
                for keyword in keywords:
                    pipeline.sadd(f"bera_articles:keywords:{keyword}", article_id)

            # Update main index
            pipeline.delete("bera_articles:index")
            pipeline.sadd("bera_articles:index", *article_ids)

            # Execute pipeline
            await pipeline.execute()

        except Exception as e:
            self.logger.error(
                f"Error updating cache and index: {str(e)}",
                extra={
                    "category": DebugCategory.CACHE.value,
                    "error_type": type(e).__name__
                }
            )
            self.metrics.record_error("news_monitor")
