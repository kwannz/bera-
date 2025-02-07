import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional

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
            if news_section:
                for article in news_section.find_all('article'):
                    title = article.find('h2').text.strip()
                    date = article.find('time').text.strip()
                    link = article.find('a')['href']
                    news_items.append({
                        'title': title,
                        'date': date,
                        'link': link if link.startswith('http') else f"{self.bera_home_url}{link}"
                    })
            
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
            if ido_section:
                for ido in ido_section.find_all('div', {'class': 'ido-card'}):
                    name = ido.find('h3').text.strip()
                    date = ido.find('time').text.strip()
                    status = ido.find('span', {'class': 'status'}).text.strip()
                    ido_items.append({
                        'name': name,
                        'date': date,
                        'status': status
                    })
            
            self.latest_idos_cache = ido_items
            return ido_items
        except Exception as e:
            logging.error(f"Error fetching upcoming IDOs: {str(e)}")
            return self.latest_idos_cache
            
    def format_news_update(self, news_item: Dict) -> str:
        return f"📰 {news_item['title']}\n📅 {news_item['date']}\n🔗 {news_item['link']}"
        
    def format_ido_update(self, ido: Dict) -> str:
        return f"🚀 Upcoming IDO: {ido['name']}\n📅 {ido['date']}\n📊 Status: {ido['status']}"
