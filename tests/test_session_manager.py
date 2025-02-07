import pytest
from src.twitter_bot.session_manager import SessionManager

@pytest.fixture
def session_manager():
    return SessionManager()

@pytest.fixture
def sample_cookies():
    return [
        {"name": "auth_token", "value": "test_token"},
        {"name": "ct0", "value": "test_csrf"}
    ]

async def test_save_and_load_cookies(session_manager, sample_cookies):
    """Test saving and loading cookies"""
    await session_manager.save_cookies(sample_cookies)
    loaded_cookies = await session_manager.load_cookies()
    
    assert len(loaded_cookies) == len(sample_cookies)
    for cookie in loaded_cookies:
        matching = next(c for c in sample_cookies if c["name"] == cookie["name"])
        assert cookie["value"] == matching["value"]

async def test_clear_cookies(session_manager, sample_cookies):
    """Test clearing cookies"""
    await session_manager.save_cookies(sample_cookies)
    session_manager.clear_cookies()
    loaded_cookies = await session_manager.load_cookies()
    assert len(loaded_cookies) == 0

async def test_save_cookies_invalid_format(session_manager):
    """Test handling invalid cookie format"""
    invalid_cookies = [{"invalid": "format"}]
    await session_manager.save_cookies(invalid_cookies)
    loaded_cookies = await session_manager.load_cookies()
    assert len(loaded_cookies) == 0

async def test_load_cookies_empty(session_manager):
    """Test loading cookies when none are stored"""
    loaded_cookies = await session_manager.load_cookies()
    assert len(loaded_cookies) == 0
