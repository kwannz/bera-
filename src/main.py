import asyncio
import logging
from config import (
    TWITTER_USERNAME,
    TWITTER_PASSWORD,
    TWITTER_EMAIL,
    TWITTER_2FA_SECRET,
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET,
    OLLAMA_URL
)
from src.twitter_bot.bot import BeraBot
from src.utils.logging_config import setup_logging, DebugCategory

# Set up logging
setup_logging([DebugCategory.API, DebugCategory.PRICE, DebugCategory.TOKEN])
logger = logging.getLogger(__name__)

async def main():
    try:
        # Try API key authentication first
        if all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
            bot = BeraBot(
                api_key=TWITTER_API_KEY,
                api_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_secret=TWITTER_ACCESS_SECRET,
                ollama_url=OLLAMA_URL
            )
        # Fall back to username/password authentication
        elif all([TWITTER_USERNAME, TWITTER_PASSWORD]):
            bot = BeraBot(
                username=TWITTER_USERNAME,
                password=TWITTER_PASSWORD,
                email=TWITTER_EMAIL,
                two_factor_secret=TWITTER_2FA_SECRET,
                ollama_url=OLLAMA_URL
            )
        else:
            logger.error("Missing required Twitter credentials")
            return
            
        logger.info("Starting BeraBot")
        await bot.start()
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
