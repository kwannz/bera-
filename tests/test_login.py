import asyncio
from src.twitter_bot.bot import BeraBot

async def test_twitter_login():
    bot = BeraBot(
        username="myjoi_ai",
        password="joiapp1278!",
        email="joiweb3@gmail.com"
    )
    
    try:
        await bot.start()
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False
    return True

if __name__ == "__main__":
    asyncio.run(test_twitter_login())
