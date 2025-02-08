import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from src.twitter_bot.bot import BeraBot, AuthenticationError
from src.utils.error_handler import TwitterError, NetworkError, RateLimitError
from src.utils.rate_limiter import RateLimitStrategy

@pytest.mark.asyncio
async def test_api_key_authentication():
    """Test API key-based authentication"""
    bot = BeraBot(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_secret="test_secret"
    )
    
    with patch.object(bot.scraper, 'authenticate') as mock_auth:
        mock_auth.return_value = True
        await bot.authenticate()
        mock_auth.assert_called_once_with(
            api_key="test_key",
            api_secret="test_secret",
            access_token="test_token",
            access_secret="test_secret"
        )

@pytest.mark.asyncio
async def test_username_password_authentication():
    """Test username/password authentication"""
    bot = BeraBot(
        username="test_user",
        password="test_pass",
        email="test@email.com"
    )
    
    with patch.object(bot.scraper, 'login') as mock_login:
        mock_login.return_value = True
        await bot.authenticate()
        mock_login.assert_called_once_with(
            username="test_user",
            password="test_pass",
            email="test@email.com"
        )

@pytest.mark.asyncio
async def test_rate_limit_handling():
    """Test rate limit handling with exponential backoff"""
    bot = BeraBot(username="test_user", password="test_pass")
    
    # Mock rate limit error
    with patch.object(bot.scraper, 'authenticate') as mock_auth:
        mock_auth.side_effect = RateLimitError("Too many requests")
        
        start_time = datetime.now()
        try:
            await bot.authenticate()
        except AuthenticationError:
            pass
            
        # Verify exponential backoff
        elapsed = (datetime.now() - start_time).total_seconds()
        assert elapsed >= 60, "Rate limit backoff not enforced"

@pytest.mark.asyncio
async def test_ollama_integration():
    """Test Ollama model integration"""
    bot = BeraBot(
        username="test_user",
        password="test_pass",
        ollama_url="http://test-ollama:11434"
    )
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"response": "Test response"}
        )
        
        response = await bot.model_manager.generate_content(
            "test_prompt",
            {"context": "test"}
        )
        
        assert response == "Test response"
        mock_post.assert_called_once()
        
@pytest.mark.asyncio
async def test_csrf_token_handling():
    """Test CSRF token extraction and header preparation"""
    bot = BeraBot(
        username="test_user",
        password="test_pass"
    )
    
    # Mock cookie with CSRF token
    test_cookies = [{"name": "ct0", "value": "test_csrf_token"}]
    with patch.object(bot.session_manager, 'load_cookies') as mock_load:
        mock_load.return_value = test_cookies
        
        # Verify CSRF token extraction
        csrf_token = await bot.get_csrf_token()
        assert csrf_token == "test_csrf_token"
        
        # Verify headers include CSRF token
        bot.guest_token = "test_guest_token"
        headers = await bot.prepare_headers()
        assert headers["x-csrf-token"] == "test_csrf_token"
        assert headers["x-guest-token"] == "test_guest_token"
        
@pytest.mark.asyncio
async def test_login_with_retries():
    """Test login retry mechanism"""
    bot = BeraBot(
        username="test_user",
        password="test_pass",
        email="test@email.com"
    )
    
    # Mock failed login attempts
    with patch.object(bot.scraper, 'login') as mock_login:
        mock_login.side_effect = [
            NetworkError("Connection failed"),
            RateLimitError("Too many requests"),
            None  # Success on third try
        ]
        
        with patch.object(bot.scraper, 'isLoggedIn') as mock_is_logged_in:
            mock_is_logged_in.side_effect = [False, False, True]
            
            await bot.login()
            assert mock_login.call_count == 3
            
@pytest.mark.asyncio
async def test_session_restoration():
    """Test session restoration from cookies"""
    bot = BeraBot(
        username="test_user",
        password="test_pass",
        email="test@email.com"
    )
    
    # Mock successful cookie restoration
    with patch.object(bot.session_manager, 'load_cookies') as mock_load:
        mock_load.return_value = [{"name": "test_cookie", "value": "test_value"}]
        
        with patch.object(bot.scraper, 'setCookies') as mock_set_cookies:
            with patch.object(bot.scraper, 'isLoggedIn') as mock_is_logged_in:
                mock_is_logged_in.return_value = True
                
                assert await bot.restore_session() is True
                mock_load.assert_called_once()
                mock_set_cookies.assert_called_once()
                
@pytest.mark.asyncio
async def test_network_failure():
    """Test handling of network failures"""
    bot = BeraBot(username="test_user", password="test_pass")
    
    with patch.object(bot.scraper, 'login') as mock_login:
        mock_login.side_effect = NetworkError("Connection failed")
        
        with pytest.raises(AuthenticationError):
            await bot.login()
            
        assert mock_login.call_count == 3  # Should try 3 times before giving up

@pytest.mark.asyncio
async def test_token_expiration():
    """Test handling of token expiration"""
    bot = BeraBot(username="test_user", password="test_pass")
    
    # Set expired token
    bot.guest_token = "expired_token"
    bot.guest_token_created = datetime.now() - timedelta(hours=4)
    
    with patch.object(bot, 'authenticate') as mock_auth:
        mock_auth.return_value = True
        await bot.ensure_authenticated()
        mock_auth.assert_called_once()  # Should refresh token

@pytest.mark.asyncio
async def test_authentication_failure():
    """Test handling of authentication failures"""
    bot = BeraBot(username="test_user", password="test_pass")
    
    with patch.object(bot.scraper, 'login') as mock_login:
        mock_login.side_effect = AuthenticationError("Invalid credentials")
        
        with pytest.raises(AuthenticationError):
            await bot.login()
            
        assert mock_login.call_count == 1  # Should not retry on auth failure
