import os
import pytest
import logging
from src.twitter_bot.twitter_client import TwitterClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_twitter_api_connection():
    """Test Twitter API connection and posting"""
    # Get environment variables
    api_key = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
    
    # Verify credentials are present
    assert api_key, "TWITTER_API_KEY environment variable is missing"
    assert api_secret, "TWITTER_API_SECRET environment variable is missing"
    assert bearer_token, "TWITTER_BEARER_TOKEN environment variable is missing"
    
    logger.info(f"Using API key: {api_key[:5]}...")
    
    client = TwitterClient(
        api_key=api_key,
        api_secret=api_secret,
        bearer_token=bearer_token
    )
    
    # Test authentication
    auth_result = await client.authenticate()
    assert auth_result is True
    
    # Test posting
    test_message = "🐻 Testing Berachain Twitter Bot - Price Update\nBERA: $8.5 | Volume: $10M | +5% 24h\n#Berachain #DeFi"
    post_result = await client.post_tweet(test_message)
    assert post_result is not None
