import pytest
from src.utils.error_handler import (
    ErrorHandler,
    RetryAction,
    RateLimitError,
    NetworkError,
    AuthenticationError
)

@pytest.fixture
def error_handler():
    return ErrorHandler()

async def test_rate_limit_error(error_handler):
    """Test handling of rate limit errors"""
    action = await error_handler.handle_error(
        RateLimitError("Too many requests"),
        "test_context"
    )
    assert action == RetryAction.WAIT_AND_RETRY

async def test_network_error(error_handler):
    """Test handling of network errors"""
    action = await error_handler.handle_error(
        NetworkError("Connection failed"),
        "test_context"
    )
    assert action == RetryAction.RETRY_IMMEDIATELY

async def test_auth_error(error_handler):
    """Test handling of authentication errors"""
    action = await error_handler.handle_error(
        AuthenticationError("Invalid credentials"),
        "test_context"
    )
    assert action == RetryAction.ABORT

async def test_unknown_error(error_handler):
    """Test handling of unknown errors"""
    action = await error_handler.handle_error(
        ValueError("Unknown error"),
        "test_context"
    )
    assert action == RetryAction.ABORT
