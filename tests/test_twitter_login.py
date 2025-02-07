import asyncio
import pytest
from unittest.mock import patch, MagicMock
from src.twitter_bot.bot import BeraBot, AuthenticationError
from src.utils.error_handler import TwitterError, NetworkError, RateLimitError

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
async def test_login_failure():
    """Test handling of login failures"""
    bot = BeraBot(
        username="test_user",
        password="test_pass",
        email="test@email.com"
    )
    
    # Mock persistent login failures
    with patch.object(bot.scraper, 'login') as mock_login:
        mock_login.side_effect = NetworkError("Connection failed")
        
        with pytest.raises(AuthenticationError):
            await bot.login()
            
        assert mock_login.call_count == 3  # Should try 3 times before giving up
    credentials = {
        "username": "myjoi_ai",
        "password": "joiapp1278!",
        "email": "joiweb3@gmail.com"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'X-Twitter-Active-User': 'yes',
        'X-Twitter-Auth-Type': 'OAuth2Session',
        'X-Twitter-Client-Language': 'en'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # Step 1: Get initial auth tokens
            logger.info("Getting auth tokens...")
            async with session.get("https://twitter.com/i/flow/login") as response:
                if response.status != 200:
                    logger.error(f"Failed to get auth page: {response.status}")
                    return False
                auth_page = await response.text()
                logger.info("Successfully got auth page")
                
            # Step 2: Get guest token
            logger.info("Getting guest token...")
            async with session.post(
                "https://api.twitter.com/1.1/guest/activate.json",
                headers={
                    "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
                    "Content-Type": "application/json"
                }
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to get guest token: {response.status}")
                    return False
                    
                guest_data = await response.json()
                if not guest_data or "guest_token" not in guest_data:
                    logger.error(f"Invalid guest token response: {guest_data}")
                    return False
                    
                guest_token = guest_data["guest_token"]
                headers["x-guest-token"] = guest_token
                logger.info(f"Got guest token: {guest_token}")

            # Step 3: Submit login flow
            logger.info("Submitting login flow...")
            headers["Authorization"] = f"Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
            flow_token = None
            async with session.post(
                "https://api.twitter.com/1.1/onboarding/task.json?flow_name=login",
                json={
                    "input_flow_data": {
                        "flow_context": {
                            "debug_overrides": {},
                            "start_location": {"location": "unknown"}
                        }
                    },
                    "subtask_versions": {}
                },
                headers=headers
            ) as response:
                flow_data = await response.json()
                flow_token = flow_data.get("flow_token")
                logger.info(f"Got flow token: {flow_token}")
                
                if not flow_token:
                    logger.error("Failed to get flow token")
                    return False
                    
            # Step 4: Submit username
            logger.info("Submitting username...")
            async with session.post(
                "https://api.twitter.com/1.1/onboarding/task.json",
                json={
                    "flow_token": flow_token,
                    "subtask_inputs": [{
                        "subtask_id": "LoginEnterUserIdentifierSSO",
                        "settings_list": {
                            "setting_responses": [{
                                "key": "user_identifier",
                                "response_data": {"text_data": {"result": credentials["username"]}}
                            }],
                            "link": "next_link"
                        }
                    }]
                },
                headers=headers
            ) as response:
                data = await response.json()
                logger.info(f"Username submission response: {json.dumps(data, indent=2)}")
                flow_token = data.get("flow_token")
                
            # Step 5: Submit password
            logger.info("Submitting password...")
            async with session.post(
                "https://api.twitter.com/1.1/onboarding/task.json",
                json={
                    "flow_token": flow_token,
                    "subtask_inputs": [{
                        "subtask_id": "LoginEnterPassword",
                        "enter_password": {
                            "password": credentials["password"],
                            "link": "next_link"
                        }
                    }]
                },
                headers=headers
            ) as response:
                data = await response.json()
                logger.info(f"Password submission response: {json.dumps(data, indent=2)}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False

if __name__ == "__main__":
    asyncio.run(test_twitter_login())
