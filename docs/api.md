# Berachain Twitter Bot API Documentation

## Authentication Endpoints

### API Key Authentication
```http
POST /api/auth/token
Content-Type: application/json

{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "access_token": "your_access_token",
    "access_secret": "your_access_secret"
}
```

### Username/Password Authentication
```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password",
    "email": "your_email"
}
```

## Rate Limiting

The API implements rate limiting with exponential backoff:
- Default: 25 requests per 2-hour window
- Guest token refresh: Every 3 hours
- Failed requests: Exponential backoff (base_delay * 2^retry_count)
- Maximum wait time: 1 hour

Rate limit headers:
```http
X-Rate-Limit-Limit: 25
X-Rate-Limit-Remaining: 24
X-Rate-Limit-Reset: 1738926030
```

## Error Responses

### Rate Limit Error
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60

{
    "error": "rate_limit_exceeded",
    "message": "Too many requests",
    "retry_after": 60
}
```

### Authentication Error
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
    "error": "authentication_failed",
    "message": "Invalid credentials"
}
```

### Network Error
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
    "error": "network_error",
    "message": "Connection failed"
}
```

## Price Tracking Endpoints

### Get BERA Token Price
```http
GET /api/price/bera
Content-Type: application/json
Authorization: Bearer ${token}

Response:
{
    "price": "8.5",
    "volume": "10000000",
    "change_24h": "+10.5"
}
```

## News Monitoring Endpoints

### Get Latest News
```http
GET /api/news/latest
Content-Type: application/json
Authorization: Bearer ${token}

Response:
{
    "news": [
        {
            "title": "New BeraHome Feature",
            "content": "BeraHome launches new staking feature",
            "timestamp": "2024-02-07T12:00:00Z"
        }
    ]
}
```

## AI Response Endpoints

### Generate Response
```http
POST /api/ai/generate
Content-Type: application/json
Authorization: Bearer ${token}

{
    "prompt": "What is the current BERA price?",
    "context": {
        "price": "8.5",
        "volume": "10M",
        "change": "+10%"
    }
}

Response:
{
    "response": "🐻 BERA is currently trading at $8.5 with a 24h volume of $10M, up 10% in the last 24 hours!"
}
```

## Best Practices

1. Always include proper authentication headers
2. Handle rate limits with exponential backoff
3. Implement proper error handling
4. Use CSRF tokens for all POST requests
5. Monitor rate limit headers and adjust accordingly

## Development Guidelines

1. Use environment variables for sensitive data
2. Implement proper logging
3. Follow TypeScript-inspired patterns
4. Add comprehensive test coverage
5. Document all API changes
