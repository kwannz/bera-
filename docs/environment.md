# Environment Variables

## API Configuration

### DEX APIs
- `PANCAKESWAP_API_KEY` - PancakeSwap API key (optional)
  - Documentation: https://docs.pancakeswap.finance/developers/api
- `UNISWAP_API_KEY` - Uniswap API key (optional)
  - Documentation: https://docs.uniswap.org/api/introduction
- `JUPITER_API_KEY` - Jupiter API key (optional)
  - Documentation: https://station.jup.ag/docs/apis/swap-api

### WebSocket APIs
- `BINANCE_WS_KEY` - Binance WebSocket API key (optional)
  - Documentation: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams

### Chart APIs
- `TRADINGVIEW_API_KEY` - TradingView API key (optional)
  - Documentation: https://www.tradingview.com/charting-library-docs/latest/api/

### Ollama API
- `OLLAMA_URL` - Ollama API endpoint URL (default: http://localhost:11434)
- `MODEL_TEMPERATURE` - Temperature setting for model responses (default: 0.7)

### BeraTrail API
- `BERATRAIL_API_KEY` - API key for authentication (optional)
- `BERATRAIL_API_URL` - BeraTrail API endpoint URL (default: https://api.beratrail.io/v1)

## Redis Configuration
- `REDIS_HOST` - Redis server hostname (default: localhost)
- `REDIS_PORT` - Redis server port (default: 6379)
- `REDIS_DB` - Redis database number (default: 0)

## Cache Configuration
- `PRICE_CACHE_TTL` - Price data cache TTL in seconds (default: 300)
- `NEWS_CACHE_TTL` - News data cache TTL in seconds (default: 86400)
- `SENTIMENT_CACHE_TTL` - Sentiment data cache TTL in seconds (default: 300)

## Rate Limiting
- `RATE_LIMIT_REQUESTS` - Maximum requests per window (default: 60)
- `RATE_LIMIT_WINDOW` - Time window in seconds (default: 60)

## Logging
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR) (default: INFO)
- `LOG_FORMAT` - Log format (default: "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
- `LOG_FILE` - Log file path (optional, logs to stdout if not set)
- `LOG_MAX_BYTES` - Maximum log file size before rotation (default: 10485760)
- `LOG_BACKUP_COUNT` - Number of backup log files to keep (default: 5)

## Service URLs
- `BERAHOME_SUBSTACK_URL` - BeraHome Substack URL (default: https://berahome.substack.com)

Never commit actual values for these environment variables. Use a secure method to manage and distribute secrets.

## Example Configuration (for development)
```bash
# Ollama API
export OLLAMA_URL=http://localhost:11434
export MODEL_TEMPERATURE=0.7

# BeraTrail API Configuration
export BERATRAIL_API_KEY=your_api_key_here  # Required for authentication
export BERATRAIL_API_URL=https://api.beratrail.io/v1  # Default API endpoint
export PRICE_CACHE_TTL=300  # Cache TTL in seconds (default: 300)

# DEX APIs Configuration
export PANCAKESWAP_API_KEY=your_key  # Optional, see https://docs.pancakeswap.finance/developers/api
export UNISWAP_API_KEY=your_key      # Optional, see https://docs.uniswap.org/api/introduction
export JUPITER_API_KEY=your_key       # Optional, see https://station.jup.ag/docs/apis/swap-api

# WebSocket APIs Configuration
export BINANCE_WS_KEY=your_key       # Optional, see https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams

# Chart APIs Configuration
export TRADINGVIEW_API_KEY=your_key   # Optional, see https://www.tradingview.com/charting-library-docs/latest/api/

# Fallback APIs Configuration
export COINGECKO_API_KEY=your_coingecko_api_key  # Optional, used as first fallback
export OKX_API_KEY=your_okx_api_key              # Optional, used as second fallback
export OKX_SECRET_KEY=your_okx_secret_key        # Required if OKX_API_KEY is set

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0

# Cache TTLs
export PRICE_CACHE_TTL=300
export NEWS_CACHE_TTL=86400
export SENTIMENT_CACHE_TTL=300

# Rate Limiting
export RATE_LIMIT_REQUESTS=60
export RATE_LIMIT_WINDOW=60

# Logging
export LOG_LEVEL=INFO
export LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
export LOG_MAX_BYTES=10485760
export LOG_BACKUP_COUNT=5

# Service URLs
export BERAHOME_SUBSTACK_URL=https://berahome.substack.com
```
