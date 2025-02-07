import asyncio
from config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET
)
from src.twitter_bot.bot import BeraBot

async def main():
    bot = BeraBot(
        TWITTER_API_KEY,
        TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_SECRET
    )
    
    while True:
        await bot.post_price_update()
        await asyncio.sleep(900)  # 15 minutes

if __name__ == "__main__":
    asyncio.run(main())
