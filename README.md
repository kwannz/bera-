# Berachain Twitter Bot

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kwannz/bera-.git
cd bera-twitter-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r tests/requirements-test.txt  # For running tests
```

4. Install and start Ollama:
```bash
# Follow instructions at https://ollama.ai/download
ollama run deepseek-r1:1.5b
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Twitter credentials and API keys
```

## Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Running the Bot
```bash
python src/main.py
```

## Features

- Real-time BERA token price tracking
- AI-powered responses using deepseek-r1:1.5b
- Automated news monitoring
- Interactive user queries
- Token analytics and validation

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
