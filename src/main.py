import asyncio
import logging
from config import (
    TWITTER_USERNAME,
    TWITTER_PASSWORD,
    OLLAMA_URL
)
from src.twitter_bot.bot import BeraBot
from src.utils.logging_config import setup_logging, DebugCategory

# Set up logging
setup_logging([DebugCategory.API, DebugCategory.PRICE, DebugCategory.TOKEN])
logger = logging.getLogger(__name__)

async def main():
    try:
        bot = BeraBot(
            username=TWITTER_USERNAME,
            password=TWITTER_PASSWORD,
            ollama_url=OLLAMA_URL
        )
        
        logger.info("Starting BeraBot with Twitter client login")
        await bot.start()
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
