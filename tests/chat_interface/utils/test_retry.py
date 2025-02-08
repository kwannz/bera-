import pytest
from unittest.mock import AsyncMock
from src.chat_interface.utils.retry import async_retry


@pytest.mark.asyncio
async def test_retry_success():
    """Test successful execution without retries"""
    mock_func = AsyncMock(return_value="success")
    decorated = async_retry()(mock_func)

    result = await decorated()
    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_with_temporary_failure():
    """Test retry with temporary failure"""
    mock_func = AsyncMock(side_effect=[ValueError, ValueError, "success"])
    decorated = async_retry(retries=3, delay=0.1)(mock_func)

    result = await decorated()
    assert result == "success"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retry_max_retries_exceeded():
    """Test max retries exceeded"""
    mock_func = AsyncMock(side_effect=ValueError("test error"))
    decorated = async_retry(retries=2, delay=0.1)(mock_func)

    with pytest.raises(ValueError, match="test error"):
        await decorated()
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_retry_with_specific_exception():
    """Test retry with specific exception type"""
    mock_func = AsyncMock(side_effect=[ValueError, "success"])
    decorated = async_retry(
        retries=2,
        delay=0.1,
        exceptions=ValueError
    )(mock_func)

    result = await decorated()
    assert result == "success"
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_retry_with_unhandled_exception():
    """Test retry with unhandled exception type"""
    mock_func = AsyncMock(side_effect=KeyError("test error"))
    decorated = async_retry(
        retries=2,
        delay=0.1,
        exceptions=ValueError
    )(mock_func)

    with pytest.raises(KeyError, match="test error"):
        await decorated()
    assert mock_func.call_count == 1
