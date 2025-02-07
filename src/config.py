import os
from dotenv import load_dotenv

load_dotenv()

TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
