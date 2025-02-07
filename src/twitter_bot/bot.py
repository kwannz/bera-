import tweepy
import tweepy
from typing import Optional

from ..ai_response.generator import ResponseGenerator
from ..price_tracking.tracker import PriceTracker
from ..news_monitoring.monitor import NewsMonitor

class BeraBot:
    def __init__(self, api_key, api_secret, access_token, access_secret):
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_secret)
        self.api = tweepy.API(auth)
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        self.price_tracker = PriceTracker()
        self.news_monitor = NewsMonitor()
        self.response_generator = ResponseGenerator()
        
    async def handle_mention(self, mention):
        response = await self.response_generator.generate_response(mention.text)
        self.client.create_tweet(
            text=response,
            in_reply_to_tweet_id=mention.id
        )
        
    async def post_price_update(self):
        price_data = await self.price_tracker.get_price_data()
        tweet = self.price_tracker.format_price_report(price_data)
        self.client.create_tweet(text=tweet)
