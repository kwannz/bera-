# Environment Variables

## API Configuration
- `DEEPSEEK_API_URL` - Deepseek API endpoint URL
- `DEEPSEEK_API_KEY` - API key for authentication (required)
- `DEEPSEEK_MODEL` - Model name to use (optional)
- `MODEL_TEMPERATURE` - Temperature setting for model responses (optional)

## Redis Configuration
- `REDIS_HOST` - Redis server hostname
- `REDIS_PORT` - Redis server port
- `REDIS_DB` - Redis database number

## Rate Limiting
- `RATE_LIMIT_REQUESTS` - Maximum requests per window
- `RATE_LIMIT_WINDOW` - Time window in seconds

## Logging
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

Never commit actual values for these environment variables. Use a secure method to manage and distribute secrets.
