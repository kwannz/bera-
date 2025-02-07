import requests
import logging
from datetime import datetime, timedelta

class PriceTracker:
    def __init__(self):
        self.base_url = "https://beratrail.io/api/v1"
        self.previous_price = None
        self.last_update = None
        
    async def get_price_data(self):
        try:
            response = requests.get(f"{self.base_url}/tokens/bera")
            data = response.json()
            
            current_price = float(data['price'])
            current_time = datetime.now()
            
            price_change_24h = 0
            if self.previous_price and self.last_update:
                time_diff = current_time - self.last_update
                if time_diff.total_seconds() >= 86400:
                    price_change_24h = ((current_price - self.previous_price) / self.previous_price) * 100
            
            self.previous_price = current_price
            self.last_update = current_time
            
            return {
                "price": current_price,
                "volume_24h": float(data['volume_24h']),
                "price_change_24h": price_change_24h
            }
        except Exception as e:
            logging.error(f"Error fetching BERA price data: {str(e)}")
            return None
            
    def format_price_report(self, data):
        if not data:
            return "Price data unavailable"
        
        volume = data['volume_24h']
        if volume >= 1_000_000_000:  # Billions
            volume_str = f"${volume/1_000_000_000:.1f}B"
        else:  # Millions
            volume_str = f"${volume/1_000_000:.1f}M"
            
        return f"BERA: ${data['price']:.2f} | Volume: {volume_str} | {data['price_change_24h']:+.1f}% 24h"
