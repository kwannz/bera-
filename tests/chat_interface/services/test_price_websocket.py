import pytest
import json
import asyncio
from typing import Dict, Any
import websockets
from src.chat_interface.services.price_websocket import BinanceWebSocket
from src.chat_interface.utils.rate_limiter import RateLimiter
from src.chat_interface.utils.circuit_breaker import CircuitBreaker
from src.chat_interface.utils.metrics import Metrics
from tests.chat_interface.services.mock_websocket import MockWebSocket


@pytest.fixture
def metrics():
    """Create a metrics instance for testing"""
    return Metrics()


@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker instance for testing"""
    return CircuitBreaker()


@pytest.fixture
async def websocket_client(
    rate_limiter,
    metrics,
    circuit_breaker,
    monkeypatch,
    event_loop
) -> BinanceWebSocket:
    """Create a WebSocket client instance for testing"""
    client = BinanceWebSocket(rate_limiter, metrics, circuit_breaker)
    mock_ws = None

    # Mock websockets.connect to return our MockWebSocket
    async def mock_connect(url):
        nonlocal mock_ws
        mock_ws = MockWebSocket(url, rate_limiter=rate_limiter)
        await mock_ws.connect()
        return mock_ws

    monkeypatch.setattr(websockets, "connect", mock_connect)

    # Initialize client with longer timeout
    await asyncio.wait_for(client.initialize(), timeout=10.0)

    # Verify initialization
    assert client._initialized is True, "WebSocket should be initialized"
    assert client._running is True, "WebSocket should be running"
    assert client.ws is not None, "WebSocket connection should be established"

    try:
        yield client
    finally:
        # Clean up in reverse order
        if client:
            await client.close()
        if mock_ws:
            await mock_ws.close()
        # Wait for cleanup
        await asyncio.sleep(0.2)


@pytest.mark.asyncio
async def test_websocket_initialization(websocket_client):
    """Test WebSocket client initialization"""
    async with asyncio.timeout(5.0):
        client = await anext(websocket_client)
        # Initialize should already be called by fixture
        assert client._initialized is True, "WebSocket should be initialized"
        assert client._running is True, "WebSocket should be running"
        assert len(client.subscribed_symbols) == 0, "No symbols should be subscribed initially"
        
        # Test re-initialization (should be idempotent)
        await client.initialize()
        assert client._initialized is True, "WebSocket should remain initialized"
    assert client._running is True, "WebSocket should remain running"


@pytest.mark.asyncio
async def test_price_subscription(websocket_client):
    """Test price update subscription"""
    client = await anext(websocket_client)
    received_data = None

    async def price_callback(data: Dict[str, Any]):
        nonlocal received_data
        received_data = data

    # Subscribe to price updates
    await client.subscribe_price_updates(
        "BERAUSDT",
        callback=price_callback
    )

    # Wait a bit for subscription to complete
    await asyncio.sleep(0.1)

    assert "BERAUSDT".lower() in client.subscribed_symbols
    assert client.ws is not None
    assert len(client._callbacks) == 1


@pytest.mark.asyncio
async def test_websocket_reconnection(websocket_client):
    """Test WebSocket reconnection logic"""
    client = await anext(websocket_client)
    
    async def verify_connection():
        """Helper to verify connection state"""
        assert client.ws is not None, "WebSocket connection should exist"
        assert client._initialized is True, "WebSocket should be initialized"
        assert client._running is True, "WebSocket should be running"
        await asyncio.sleep(0.1)  # Give time for internal state to update
    
    async def _test_reconnection():
        try:
            # First establish a connection
            await client.subscribe_price_updates("BERAUSDT")
            await verify_connection()
            
            # Force connection close
            old_ws = client.ws
            if old_ws:
                await old_ws.close()
                client.ws = None
                await asyncio.sleep(0.1)  # Wait for cleanup
                
                # Verify disconnected state
                assert client.ws is None, "WebSocket should be None after close"
                assert not client._running, "WebSocket should not be running after close"

            # Try to subscribe after connection loss
            await client.subscribe_price_updates("BERAUSDT")
            await verify_connection()
            
            # Verify new connection
            assert client.ws is not None, "New WebSocket connection should exist"
            assert client.ws is not old_ws, "Should have new WebSocket instance"
            assert "BERAUSDT".lower() in client.subscribed_symbols, "Symbol should be subscribed"
            
        except AssertionError:
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error during reconnection test: {str(e)}")
    
    try:
        await asyncio.wait_for(_test_reconnection(), timeout=5.0)
    except asyncio.TimeoutError:
        raise TimeoutError("WebSocket reconnection test timed out")
    finally:
        # Ensure cleanup
        if client.ws:
            await client.ws.close()


@pytest.mark.asyncio
async def test_unsubscribe_price_updates(websocket_client):
    """Test unsubscribing from price updates"""
    client = await anext(websocket_client)
    symbol = "BERAUSDT"
    
    async def verify_state(expected_subscribed: bool):
        """Helper to verify connection and subscription state"""
        assert client.ws is not None, "WebSocket connection should exist"
        assert client._initialized is True, "WebSocket should be initialized"
        assert client._running is True, "WebSocket should be running"
        
        if expected_subscribed:
            assert symbol.lower() in client.subscribed_symbols, "Symbol should be in subscribed symbols"
        else:
            assert symbol.lower() not in client.subscribed_symbols, "Symbol should not be in subscribed symbols"
    
    try:
        # First verify initial state
        await verify_state(expected_subscribed=False)
        
        # Subscribe
        await client.subscribe_price_updates(symbol)
        await verify_state(expected_subscribed=True)
        
        # Small delay to ensure subscription is processed
        await asyncio.sleep(0.1)
        
        # Unsubscribe
        await client.unsubscribe_price_updates(symbol)
        await verify_state(expected_subscribed=False)
        
    except Exception as e:
        raise RuntimeError(f"Test failed: {str(e)}")
    finally:
        # Ensure cleanup
        if client.ws:
            await client.ws.close()


@pytest.mark.asyncio
async def test_rate_limit_handling(websocket_client):
    """Test rate limit handling for WebSocket connections"""
    client = await anext(websocket_client)
    
    async def verify_subscription(symbol: str, should_succeed: bool):
        """Helper to verify subscription attempt"""
        try:
            await asyncio.wait_for(client.subscribe_price_updates(symbol), timeout=0.5)
            assert should_succeed, f"Subscription to {symbol} should have failed"
            assert symbol.lower() in client.subscribed_symbols
        except (websockets.exceptions.InvalidStatusCode, asyncio.TimeoutError):
            assert not should_succeed, f"Subscription to {symbol} should have succeeded"
            assert symbol.lower() not in client.subscribed_symbols
    
    try:
        # Try to make multiple connections quickly
        subscription_count = 0
        for i in range(6):  # Try 6 subscriptions (5 should succeed)
            symbol = f"PAIR{i}USDT"
            should_succeed = i < 5  # First 5 should succeed
            await verify_subscription(symbol, should_succeed)
            if should_succeed:
                subscription_count += 1
            await asyncio.sleep(0.01)  # Small delay between attempts
        
        # Verify we hit the rate limit
        assert subscription_count == 5, f"Made {subscription_count} subscriptions when limit is 5"
        
    except Exception as e:
        raise RuntimeError(f"Rate limit test failed: {str(e)}")
    finally:
        # Ensure cleanup
        if client.ws:
            try:
                await asyncio.wait_for(client.ws.close(), timeout=0.1)
            except (asyncio.TimeoutError, Exception):
                pass


@pytest.mark.asyncio
async def test_message_handler(websocket_client):
    """Test WebSocket message handling"""
    client = await anext(websocket_client)
    received_data = None
    callback_executed = asyncio.Event()

    async def price_callback(data: Dict[str, Any]):
        nonlocal received_data
        received_data = data
        callback_executed.set()

    async def verify_message_data():
        """Helper to verify received message data"""
        assert received_data is not None, "No data received from callback"
        assert received_data["symbol"] == "BERAUSDT", "Wrong symbol in callback data"
        assert isinstance(received_data["price"], (int, float)), "Invalid price type"
        assert isinstance(received_data["volume"], (int, float)), "Invalid volume type"
    
    try:
        async with asyncio.timeout(1.0):  # Overall timeout
            # Subscribe to price updates
            await client.subscribe_price_updates("BERAUSDT", callback=price_callback)
            
            # Wait for callback execution with shorter timeout
            await callback_executed.wait()
            
            # Verify received data
            await verify_message_data()
            
            # Verify subscription state
            assert client.ws is not None, "WebSocket connection should exist"
            assert client._initialized is True, "WebSocket should be initialized"
            assert client._running is True, "WebSocket should be running"
            assert "BERAUSDT".lower() in client.subscribed_symbols, "Symbol should be subscribed"
            
    except asyncio.TimeoutError:
        raise TimeoutError("Message handling test timed out")
    except Exception as e:
        raise RuntimeError(f"Message handling test failed: {str(e)}")
    finally:
        # Ensure cleanup
        if client.ws:
            try:
                await client.unsubscribe_price_updates("BERAUSDT")
                await asyncio.wait_for(client.ws.close(), timeout=0.2)
            except (asyncio.TimeoutError, Exception):
                pass
