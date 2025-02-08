import json
import time
import asyncio
import websockets
from typing import Dict, Any, List


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self, url: str = "", rate_limiter=None):
        self.url = url
        self.connected = False  # Start disconnected
        self.messages: List[Dict[str, Any]] = []
        self.subscriptions: List[str] = []
        self.rate_limiter = rate_limiter
        self.message_queue = asyncio.Queue()
        self._message_task = None
        self._initialized = False
        self._running = False

    async def connect(self) -> None:
        """Simulate connection"""
        try:
            # Check rate limit before allowing connection
            if not await self.rate_limiter.check_rate_limit(
                "binance_ws", limit=5, window=60
            ):
                # Use 429 for rate limit
                raise websockets.exceptions.InvalidStatusCode(None, 429)

            # Cancel existing task if any
            if hasattr(self, '_message_task') and self._message_task:
                try:
                    self._message_task.cancel()
                    try:
                        await asyncio.wait_for(self._message_task, timeout=0.1)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                except Exception:
                    pass
                finally:
                    self._message_task = None
                
            # Clear message queue
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            # Set flags before starting task
            self._initialized = True
            self._running = True
            self.connected = True

            # Start message sending task
            self._message_task = asyncio.create_task(self._send_messages())
            
            # Wait for task to start and verify it's running
            try:
                # Overall timeout for initialization
                async with asyncio.timeout(0.5):
                    # Try up to 5 times
                    for _ in range(5):
                        if self._message_task and not self._message_task.done():
                            break
                        await asyncio.sleep(0.1)
                    else:
                        raise RuntimeError("Failed to start message task")
            except Exception as e:
                self._initialized = False
                self._running = False
                self.connected = False
                if hasattr(self, '_message_task') and self._message_task:
                    self._message_task.cancel()
                    try:
                        await asyncio.wait_for(self._message_task, timeout=0.1)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                    self._message_task = None
                raise RuntimeError(f"Failed to initialize WebSocket: {str(e)}")
                
        except Exception:
            self._initialized = False
            self._running = False
            self.connected = False
            if hasattr(self, '_message_task') and self._message_task:
                self._message_task.cancel()
                try:
                    await asyncio.wait_for(
                        self._message_task, timeout=0.1
                    )
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
                self._message_task = None
            raise

    async def send(self, message: str) -> None:
        """Handle subscription messages"""
        if not self.connected:
            raise websockets.exceptions.ConnectionClosed(None, None)
            
        try:
            data = json.loads(message)
            if data["method"] == "SUBSCRIBE":
                # Check rate limit before allowing subscription
                if not await self.rate_limiter.check_rate_limit(
                    "binance_ws", limit=5, window=60
                ):
                    raise websockets.exceptions.InvalidStatusCode(None, 429)
                    
                # Add new subscriptions
                for param in data["params"]:
                    if param not in self.subscriptions:
                        self.subscriptions.append(param)
                        
            elif data["method"] == "UNSUBSCRIBE":
                # Remove subscriptions
                for param in data["params"]:
                    if param in self.subscriptions:
                        self.subscriptions.remove(param)
                        
            if not self.connected:  # Check connection after operation
                raise websockets.exceptions.ConnectionClosed(None, None)
                
        except json.JSONDecodeError:
            raise websockets.exceptions.InvalidMessage("Invalid message format")
        except KeyError:
            raise websockets.exceptions.InvalidMessage("Missing required fields")
        except Exception as e:
            if not self.connected:
                raise websockets.exceptions.ConnectionClosed(None, None)
            raise

    async def recv(self) -> str:
        """Return mock price update"""
        if not (self.connected and self._running and self._initialized):
            raise websockets.exceptions.ConnectionClosed(None, None)
            
        if not self.subscriptions:
            await asyncio.sleep(0.05)  # Small network delay
            return json.dumps({"e": "error", "m": "No subscriptions"})

        try:
            # Get next message from queue with timeout
            try:
                message = self.message_queue.get_nowait()
            except asyncio.QueueEmpty:
                # If queue is empty, return error immediately
                return json.dumps({"e": "error", "m": "No messages available"})
            
            if not (
                self.connected and self._running and self._initialized
            ):
                raise websockets.exceptions.ConnectionClosed(None, None)
            
            # Parse message and update timestamp
            try:
                data = json.loads(message)
                data["E"] = int(time.time() * 1000)
                
                # Only queue another message if we're still connected
                if (
                    self.connected and self._running and self._initialized
                ):
                    try:
                        self.message_queue.put_nowait(json.dumps(data))
                    except asyncio.QueueFull:
                        pass  # Ignore if queue is full
            except Exception:
                pass  # Ignore any parsing errors
                
            return message
            
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"Error receiving message: {str(exc)}")
            if not (
                self.connected and
                self._running and
                self._initialized
            ):
                raise websockets.exceptions.ConnectionClosed(None, None)
            return json.dumps({
                "e": "error",
                "m": "Error receiving message"
            })

    async def _send_messages(self) -> None:
        """Continuously send messages in the background"""
        try:
            while self.connected and self._running and self._initialized:
                if not self.subscriptions:
                    await asyncio.sleep(0.001)
                    continue

                for subscription in list(self.subscriptions):
                    if not (
                        self.connected and self._running and self._initialized
                    ):
                        return

                    symbol = subscription.split("@")[0].upper()

                    # Send subscription confirmation
                    sub_confirm = {
                        "result": None,
                        "id": len(self.subscriptions)
                    }
                    try:
                        self.message_queue.put_nowait(json.dumps(sub_confirm))
                    except (asyncio.QueueFull, Exception):
                        continue

                    # Send one price update immediately
                    if not (
                        self.connected and self._running and self._initialized
                    ):
                        return

                    data = {
                        "e": "24hrTicker",
                        "s": symbol,
                        "c": "1.23",
                        "p": "0.05",
                        "P": "4.23",
                        "v": "1000000",
                        "E": int(time.time() * 1000)
                    }
                    try:
                        self.message_queue.put_nowait(json.dumps(data))
                    except (asyncio.QueueFull, Exception):
                        continue

                    await asyncio.sleep(0.0001)

                if not (self.connected and self._running and self._initialized):
                    return

                await asyncio.sleep(0.0001)
        except asyncio.CancelledError:
            print("Message task cancelled")
        finally:
            self._initialized = False
            self._running = False
            self.connected = False
            try:
                while not self.message_queue.empty():
                    try:
                        self.message_queue.get_nowait()
                    except (asyncio.QueueEmpty, Exception):
                        break
            except Exception:
                pass

    async def close(self) -> None:
        """Close connection"""
        # Set flags first to prevent new operations
        self._initialized = False
        self._running = False
        self.connected = False
        
        # Cancel message task immediately
        if hasattr(self, '_message_task') and self._message_task:
            try:
                self._message_task.cancel()
                try:
                    await asyncio.wait_for(self._message_task, timeout=0.1)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
            except Exception:
                pass
            finally:
                self._message_task = None
                
        # Clear message queue immediately
        try:
            while True:
                try:
                    self.message_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                except Exception:
                    break
        except Exception:
            pass
                
        # Clear subscriptions immediately
        try:
            self.subscriptions.clear()
        except Exception:
            pass
