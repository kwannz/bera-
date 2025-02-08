# Environment Variables

## API Configuration

### Ollama API
- `OLLAMA_URL` - Ollama API endpoint URL (default: http://localhost:11434)
- `MODEL_TEMPERATURE` - Temperature setting for model responses (default: 0.7)

### BeraTrail API
- `BERATRAIL_API_KEY` - API key for authentication (required)
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

# BeraTrail API
export BERATRAIL_API_KEY=your_api_key_here
export BERATRAIL_API_URL=https://api.beratrail.io/v1

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
