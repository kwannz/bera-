import asyncio
import logging
from .config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET
)
from .twitter_bot.bot import BeraBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        logger.error("Missing required Twitter API credentials")
        return
        
    bot = BeraBot(
        TWITTER_API_KEY,
        TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_SECRET
    )
    
    try:
        await bot.start()
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
