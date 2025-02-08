# Berachain Ecosystem Monitor

A comprehensive monitoring and analysis system for the Berachain ecosystem, featuring real-time price tracking, multi-DEX integration, and AI-powered insights.

## Features
- Real-time BERA token price tracking across multiple DEXs:
  - PancakeSwap integration
  - Uniswap integration
  - Jupiter (Solana) integration
- WebSocket-based live price updates
- TradingView chart integration
- BeraTrail API integration with fallback sources
- AI-powered analysis using Ollama (deepseek-r1:1.5b)
- Automated news monitoring and BeraHome updates
- IDO tracking and announcements
- Advanced error handling with circuit breakers
- Rate limiting and request throttling

## Prerequisites
- Python 3.12+
- Redis server
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
pip install -r tests/requirements-test.txt  # For running tests
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```
# AI Model Configuration
OLLAMA_URL=http://localhost:11434
DEEPSEEK_API_KEY=your_deepseek_key

# Price API Keys
BERATRAIL_API_KEY=your_beratrail_key
COINGECKO_API_KEY=your_coingecko_key
OKX_API_KEY=your_okx_key
OKX_SECRET_KEY=your_okx_secret

# Redis Configuration
REDIS_URL=redis://localhost:6379
PRICE_CACHE_TTL=300  # Cache TTL in seconds
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
├── ai_response/           # AI analysis using Ollama/Deepseek
│   ├── model_manager.py   # AI model integration
│   └── generator.py       # Response generation
├── chat_interface/        # Main chat interface
│   ├── handlers/          # API and WebSocket handlers
│   ├── models/           # Data models
│   ├── services/         # Core services
│   │   ├── price_tracker.py      # BeraTrail price tracking
│   │   ├── dex_price_tracker.py  # Multi-DEX integration
│   │   ├── price_websocket.py    # WebSocket price updates
│   │   ├── chart_service.py      # TradingView integration
│   │   ├── news_monitor.py       # BeraHome news scraping
│   │   └── analytics_collector.py # Market analytics
│   └── utils/            # Shared utilities
│       ├── circuit_breaker.py    # Error handling
│       ├── rate_limiter.py       # Request throttling
│       ├── metrics.py            # Performance tracking
│       └── retry.py              # Retry mechanisms
└── utils/                # Global utilities
    └── logging_config.py # Logging configuration

tests/                   # Test suite
├── chat_interface/      # Interface tests
│   ├── services/        # Service tests
│   └── utils/          # Utility tests
└── conftest.py         # Test fixtures

docs/                   # Documentation
└── environment.md      # Environment setup guide
```

## Development

### Environment Setup
1. Start Redis server:
```bash
sudo service redis-server start
```

2. Set up API keys in `.env`:
```bash
# Required API keys
export BERATRAIL_API_KEY="your_key"
export DEEPSEEK_API_KEY="your_key"
export COINGECKO_API_KEY="your_key"
export OKX_API_KEY="your_key"
export OKX_SECRET_KEY="your_key"
```

3. Start Ollama server:
```bash
ollama run deepseek-r1:1.5b
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
pytest tests/chat_interface/services/test_dex_price_tracker.py -v
pytest tests/chat_interface/services/test_price_websocket.py -v
pytest tests/chat_interface/services/test_chart_service.py -v

# Run with debug logging
pytest tests/ -v --log-cli-level=DEBUG
```

### Code Quality
```bash
# Style checking
flake8 src/ tests/

# Type checking
mypy src/

# Format code
black src/ tests/
```

## Contributing
1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b devin/$(date +%s)-feature-name
```
3. Run tests and ensure code quality:
```bash
python -m pytest tests/
flake8 src/ tests/
mypy src/
```
4. Submit a pull request with:
- Clear description of changes
- Test coverage for new features
- Documentation updates
- Link to related issues

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
