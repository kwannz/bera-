import requests
from datetime import datetime, timedelta

class PriceTracker:
    def __init__(self):
        self.base_url = "https://beratrail.io/api"
        
    async def get_price_data(self):
        try:
            response = requests.get(f"{self.base_url}/price")
            data = response.json()
            return {
                "price": data["price"],
                "volume_24h": data["volume"],
                "price_change_24h": data["price_change_percentage"]
            }
        except Exception as e:
            return None
            
    def format_price_report(self, data):
        if not data:
            return "Price data unavailable"
        return f"BERA: ${data['price']:.2f} | Volume: ${data['volume_24h']:.1f}B | {data['price_change_24h']:+.1f}% 24h"
