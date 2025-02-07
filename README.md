# Berachain Twitter Bot

A Twitter bot for tracking and sharing information about the Berachain ecosystem.

## Features
- Price tracking for BERA token
- Trading volume monitoring
- Daily price change calculations
- Interactive user query responses
- BeraHome news monitoring

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with required credentials:
```
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
OPENAI_API_KEY=
```

## Components
- `src/price_tracking/` - BERA token price and volume tracking
- `src/news_monitoring/` - BeraHome ecosystem news scraping
- `src/twitter_bot/` - Twitter bot core using Eliza client
- `src/ai_response/` - AI response generation using OpenAI and Ollama
