import logging
import requests
from bs4 import BeautifulSoup, Tag as BeautifulSoupTag
from datetime import datetime
from typing import List, Dict, Optional

from ..twitter_bot.bot import NEWS_UPDATE_TEMPLATE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class NewsMonitor:
    def __init__(self):
        self.bera_home_url = "https://home.berachain.com"
        self.ido_url = "https://home.berachain.com/ido"
        self.latest_news_cache = []
        self.latest_idos_cache = []
        self.last_update = None
        
    async def fetch_latest_news(self) -> List[Dict]:
        try:
            response = requests.get(self.bera_home_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = []
            news_section = soup.find('section', {'class': 'news-section'})
            if news_section and isinstance(news_section, BeautifulSoupTag):
                articles = news_section.find_all('article')
                for article in articles:
                    if not isinstance(article, BeautifulSoupTag):
                        continue
                    title_elem = article.find('h2')
                    date_elem = article.find('time')
                    link_elem = article.find('a')
                    
                    if title_elem and date_elem and link_elem and isinstance(title_elem, BeautifulSoupTag) and isinstance(date_elem, BeautifulSoupTag) and isinstance(link_elem, BeautifulSoupTag):
                        try:
                            title = title_elem.text.strip()
                            date = date_elem.text.strip()
                            link = link_elem.get('href', '')
                            if title and date and link:
                                # Extract summary from article content
                                summary_elem = article.find('p', {'class': 'summary'}) or article.find('p')
                                summary = summary_elem.text.strip() if summary_elem and isinstance(summary_elem, BeautifulSoupTag) else ""
                                
                                news_items.append({
                                    'title': title,
                                    'date': date,
                                    'link': link if isinstance(link, str) and link.startswith('http') else f"{self.bera_home_url}{link}",
                                    'summary': summary
                                })
                        except (AttributeError, TypeError) as e:
                            logging.warning(f"Error parsing news item: {str(e)}")
            
            self.latest_news_cache = news_items
            self.last_update = datetime.now()
            return news_items
        except Exception as e:
            logging.error(f"Error fetching BeraHome news: {str(e)}")
            return self.latest_news_cache
            
    async def fetch_upcoming_idos(self) -> List[Dict]:
        try:
            response = requests.get(self.ido_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            ido_items = []
            ido_section = soup.find('section', {'class': 'ido-section'})
            if ido_section and isinstance(ido_section, BeautifulSoupTag):
                idos = ido_section.find_all('div', {'class': 'ido-card'})
                for ido in idos:
                    if not isinstance(ido, BeautifulSoupTag):
                        continue
                    name_elem = ido.find('h3')
                    date_elem = ido.find('time')
                    status_elem = ido.find('span', {'class': 'status'})
                    
                    if name_elem and date_elem and status_elem and isinstance(name_elem, BeautifulSoupTag) and isinstance(date_elem, BeautifulSoupTag) and isinstance(status_elem, BeautifulSoupTag):
                        try:
                            name = name_elem.text.strip()
                            date = date_elem.text.strip()
                            status = status_elem.text.strip()
                            if name and date and status:
                                ido_items.append({
                                    'name': name,
                                    'date': date,
                                    'status': status
                                })
                        except (AttributeError, TypeError) as e:
                            logging.warning(f"Error parsing IDO item: {str(e)}")
            
            self.latest_idos_cache = ido_items
            return ido_items
        except Exception as e:
            logging.error(f"Error fetching upcoming IDOs: {str(e)}")
            return self.latest_idos_cache
            
    def format_news_update(self, news_item: Dict) -> str:
        return NEWS_UPDATE_TEMPLATE.format(
            title=news_item['title'][:50] + "..." if len(news_item['title']) > 50 else news_item['title'],
            summary=news_item['summary'][:100] + "..." if len(news_item['summary']) > 100 else news_item['summary'],
            relevance="Growing the Berachain ecosystem! 🌱"
        )
        
    def format_ido_update(self, ido: Dict) -> str:
        return f"🚀 Upcoming IDO: {ido['name']}\n📅 {ido['date']}\n📊 Status: {ido['status']}"
