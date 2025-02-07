import os
import pytest
import logging
from src.twitter_bot.twitter_client import TwitterClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_twitter_api_connection():
    """Test Twitter API connection and posting"""
    # Get environment variables directly from secure storage
    api_key = os.environ.get("APIKey")
    api_secret = os.environ.get("APIKeySecret")
    bearer_token = os.environ.get("BearerToken")
    
    # Print environment variable status for debugging
    logger.debug(f"API Key present: {bool(api_key)}")
    logger.debug(f"API Secret present: {bool(api_secret)}")
    logger.debug(f"Bearer Token present: {bool(bearer_token)}")
    
    # Verify required environment variables
    if not all([api_key, api_secret, bearer_token]):
        pytest.skip("Missing required Twitter API credentials")
    
    # Log environment variable status (first 5 chars only)
    if api_key and api_secret and bearer_token:
        logger.info(f"Using API key: {api_key[:5]}...")
    else:
        logger.error("Missing Twitter API credentials")
    
    # Verify credentials are present
    assert api_key, "APIKey environment variable is missing"
    assert api_secret, "APIKeySecret environment variable is missing"
    assert bearer_token, "BearerToken environment variable is missing"
    
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
