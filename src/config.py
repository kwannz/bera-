import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Twitter Authentication
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_EMAIL: Optional[str] = os.getenv("TWITTER_EMAIL")
TWITTER_2FA_SECRET: Optional[str] = os.getenv("TWITTER_2FA_SECRET")

# AI Model Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
