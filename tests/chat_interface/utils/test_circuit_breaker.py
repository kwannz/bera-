import pytest
import asyncio
from unittest.mock import AsyncMock
from src.chat_interface.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError
)


@pytest.mark.asyncio
async def test_circuit_breaker_success():
    """Test successful execution"""
    cb = CircuitBreaker(name="test")
    mock_func = AsyncMock(return_value="success")

    result = await cb.call(mock_func, "arg1", kwarg1="value1")
    assert result == "success"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    mock_func.assert_called_once_with("arg1", kwarg1="value1")


@pytest.mark.asyncio
async def test_circuit_breaker_failure_threshold():
    """Test circuit opens after failure threshold"""
    cb = CircuitBreaker(failure_threshold=2, name="test")
    mock_func = AsyncMock(side_effect=ValueError("test error"))

    # First failure
    with pytest.raises(ValueError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    # Second failure - should open circuit
    with pytest.raises(ValueError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 2

    # Circuit is open - should raise CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        await cb.call(mock_func)


@pytest.mark.asyncio
async def test_circuit_breaker_reset_timeout():
    """Test circuit transitions to half-open after timeout"""
    cb = CircuitBreaker(
        failure_threshold=1,
        reset_timeout=0.1,
        name="test-timeout"
    )
    mock_func = AsyncMock(side_effect=[ValueError("error"), "success"])

    # Fail once to open circuit
    with pytest.raises(ValueError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.OPEN

    # Wait for timeout
    await asyncio.sleep(0.2)

    # Should transition to half-open and succeed
    result = await cb.call(mock_func)
    assert result == "success"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure():
    """Test circuit reopens on failure in half-open state"""
    cb = CircuitBreaker(
        failure_threshold=1,
        reset_timeout=0.1,
        name="test-half-open"
    )
    mock_func = AsyncMock(side_effect=[
        ValueError("error1"),
        ValueError("error2")
    ])

    # Fail once to open circuit
    with pytest.raises(ValueError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.OPEN

    # Wait for timeout
    await asyncio.sleep(0.2)

    # Should transition to half-open and fail
    with pytest.raises(ValueError):
        await cb.call(mock_func)
    assert cb.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_success_reset():
    """Test success resets failure count"""
    cb = CircuitBreaker(failure_threshold=2, name="test")
    mock_func = AsyncMock(side_effect=[
        ValueError("error"),
        "success",
        "success"
    ])

    # First failure
    with pytest.raises(ValueError):
        await cb.call(mock_func)
    assert cb.failure_count == 1

    # Success should reset failure count
    result = await cb.call(mock_func)
    assert result == "success"
    assert cb.failure_count == 0

    # Another success
    result = await cb.call(mock_func)
    assert result == "success"
    assert cb.state == CircuitState.CLOSED
