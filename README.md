# Berachain Ecosystem Monitor

A monitoring system for tracking and analyzing information about the Berachain ecosystem.

## Features
- Real-time BERA token price and volume tracking
- Automated news monitoring and updates
- IDO tracking and announcements
- AI-powered analysis using Ollama (deepseek-r1:1.5b)

## Prerequisites
- Python 3.8+
- Ollama with deepseek-r1:1.5b model

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kwannz/bera-.git
cd bera-
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```
OPENAI_API_KEY=your_openai_key
OLLAMA_URL=http://localhost:11434
```

## Usage

1. Start the monitor:
```bash
python src/main.py
```

2. Run tests:
```bash
python -m pytest tests/
```

## Configuration

The monitor can be configured through environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key (optional)
- `OLLAMA_URL`: URL for Ollama API (default: http://localhost:11434)

## Features

### Price Updates
The monitor tracks BERA token metrics:
- Real-time price data
- Trading volume analysis
- 24-hour price changes
- Market trend indicators

### News Monitoring
Monitors and analyzes Berachain ecosystem updates:
- BeraHome platform news
- Ecosystem developments
- IDO announcements and tracking
- Project updates

### AI Integration
Uses Ollama with deepseek-r1:1.5b for:
- Market analysis
- News summarization
- Trend identification
- Impact assessment

## Development

1. Run tests:
```bash
python -m pytest tests/
```

2. Check code style:
```bash
flake8 src/ tests/
```

3. Type checking:
```bash
mypy src/
```

## Project Structure

```
src/
├── ai_response/        # AI analysis using Ollama
├── news_monitoring/    # BeraHome ecosystem news scraping
├── price_tracking/     # BERA token price and volume tracking
├── token_analytics/    # Token validation and analytics
└── utils/             # Shared utilities and logging

tests/                 # Test suite
docs/                  # Documentation
```

## Contributing
1. Fork the repository
2. Create your feature branch
3. Run tests and ensure code quality
4. Submit a pull request

## License
MIT License```

## Prerequisites

- Python 3.12+
- Node.js 18+
- Ollama (for AI responses)

## Installation

1. Clone the repositories:
```bash
# Clone main repository
git clone https://github.com/kwannz/bera-.git
cd bera-twitter-bot

# Clone and install agent-twitter-client
git clone https://github.com/elizaOS/agent-twitter-client.git
cd agent-twitter-client
npm install
npm run build
cd ..
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
pip install -e ./agent-twitter-client  # Install Twitter client
```

4. Install and start Ollama:
```bash
# Follow instructions at https://ollama.ai/download
ollama pull deepseek-r1:1.5b  # Download model
ollama run deepseek-r1:1.5b   # Start model server
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Twitter credentials and API keys
```

## Dependencies

Key dependencies and their versions:
- eth-typing==3.5.2 (required for Web3 integration)
- web3==6.15.1
- aiohttp==3.9.3
- agent-twitter-client (from elizaOS)

## Development

### Environment Setup
1. Configure Twitter API credentials in `.env`
2. Start Ollama server for AI responses
3. Set up BeraTrail API access for price tracking

### Running Tests
```bash
python -m pytest tests/ -v
```

### API Documentation

#### Twitter Client
- Uses agent-twitter-client for Twitter API interactions
- Implements TypeScript-inspired authentication flow
- Handles rate limiting with exponential backoff

#### Price Tracking
- BeraTrail API integration for real-time BERA token data
- Automated price and volume updates
- Daily percentage change calculations

#### AI Integration
- Uses Ollama with deepseek-r1:1.5b model
- Customizable response templates
- Context-aware interactions

### Troubleshooting

1. eth-typing Dependency Issues
```bash
pip uninstall eth-typing web3 eth-utils
pip install eth-typing==3.5.2 web3==6.15.1 eth-utils==3.0.0
```

2. Twitter Client Installation
```bash
# If npm build fails, try:
cd agent-twitter-client
rm -rf node_modules
npm install --legacy-peer-deps
npm run build
```

3. Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags
# Restart Ollama if needed
sudo systemctl restart ollama
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
