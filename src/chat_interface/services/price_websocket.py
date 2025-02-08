import os
import json
import asyncio
import websockets
from typing import Dict, Any, Optional, List, Set
from ..utils.rate_limiter import RateLimiter
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.metrics import Metrics
from ..utils.logging_config import get_logger, DebugCategory


class BinanceWebSocket:
    """Binance WebSocket client for real-time price updates"""
    WS_URL = "wss://stream.binance.com:9443/ws"

    def __init__(
        self,
        rate_limiter: RateLimiter,
        metrics: Metrics,
        circuit_breaker: CircuitBreaker
    ):
        self.rate_limiter = rate_limiter
        self.metrics = metrics
        self.circuit_breaker = circuit_breaker
        self.logger = get_logger(__name__)
        self.subscribed_symbols: Set[str] = set()
        self.ws = None
        self._initialized = False
        self._running = False
        self._callbacks: List[callable] = []

    async def initialize(self) -> None:
        """Initialize the WebSocket client"""
        if self._initialized and self.ws and self._running:
            return

        try:
            # Set flags to initial state
            self._initialized = False
            self._running = False

            # Cancel existing message task if any
            if hasattr(self, '_message_task') and self._message_task:
                self._message_task.cancel()
                try:
                    await self._message_task
                except asyncio.CancelledError:
                    pass
                self._message_task = None

            # Close existing WebSocket if any
            if self.ws:
                await self.ws.close()
                self.ws = None

            # Initialize new WebSocket
            self.ws = await websockets.connect(self.WS_URL)
            
            # Start message handler task
            self._message_task = asyncio.create_task(self._message_handler())
            
            # Set flags after successful initialization
            self._running = True
            self._initialized = True
            
            self.logger.info(
                "WebSocket initialized successfully",
                extra={"category": DebugCategory.API.value}
            )
        except Exception as e:
            # Reset state on failure
            self._running = False
            self._initialized = False
            
            if self.ws:
                await self.ws.close()
                self.ws = None
                
            if hasattr(self, '_message_task') and self._message_task:
                self._message_task.cancel()
                try:
                    await self._message_task
                except asyncio.CancelledError:
                    pass
                self._message_task = None
                
            self.logger.error(
                f"Error initializing WebSocket: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            raise

    async def subscribe_price_updates(
        self,
        symbol: str,
        callback: Optional[callable] = None
    ) -> None:
        """Subscribe to price updates for a symbol"""
        try:
            # Initialize WebSocket if not already initialized
            if not self._initialized or not self.ws:
                await self.initialize()

            # Add callback first if provided
            if callback and callback not in self._callbacks:
                self._callbacks.append(callback)

            # Check rate limit before allowing subscription
            if len(self.subscribed_symbols) >= 5 or not await self.rate_limiter.check_rate_limit("binance_ws", limit=5, window=60):
                self.logger.warning(
                    "Rate limit exceeded for Binance WebSocket",
                    extra={"category": DebugCategory.API.value}
                )
                return

            symbol_lower = symbol.lower()
            if symbol_lower in self.subscribed_symbols:
                return

            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [f"{symbol_lower}@ticker"],
                "id": len(self.subscribed_symbols) + 1
            }

            await self.ws.send(json.dumps(subscribe_msg))
            self.subscribed_symbols.add(symbol_lower)
            
            # Wait a bit for subscription to take effect
            await asyncio.sleep(0.1)

            self.logger.info(
                f"Subscribed to {symbol} price updates",
                extra={"category": DebugCategory.API.value}
            )

        except Exception as e:
            self.logger.error(
                f"Error subscribing to price updates: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            await self._handle_connection_error()

    async def unsubscribe_price_updates(self, symbol: str) -> None:
        """Unsubscribe from price updates for a symbol"""
        if not self.ws:
            return

        try:
            symbol_lower = symbol.lower()
            if symbol_lower not in self.subscribed_symbols:
                return

            unsubscribe_msg = {
                "method": "UNSUBSCRIBE",
                "params": [f"{symbol_lower}@ticker"],
                "id": len(self.subscribed_symbols)
            }

            await self.ws.send(json.dumps(unsubscribe_msg))
            self.subscribed_symbols.remove(symbol_lower)

            self.logger.info(
                f"Unsubscribed from {symbol} price updates",
                extra={"category": DebugCategory.API.value}
            )

        except Exception as e:
            self.logger.error(
                f"Error unsubscribing from price updates: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )

    async def _message_handler(self) -> None:
        """Handle incoming WebSocket messages"""
        try:
            while self._running and self._initialized and self.ws:
                try:
                    message = await self.ws.recv()
                    data = json.loads(message)

                    # Process ticker data
                    if "e" in data and data["e"] == "24hrTicker":
                        try:
                            symbol = data["s"]
                            symbol_lower = symbol.lower()
                            
                            # Only process data for subscribed symbols
                            if symbol_lower in self.subscribed_symbols:
                                price_data = {
                                    "symbol": symbol,
                                    "price": float(data["c"]),
                                    "price_change": float(data["p"]),
                                    "price_change_percent": float(data["P"]),
                                    "volume": float(data["v"]),
                                    "timestamp": data["E"]
                                }

                                # Execute callbacks with timeout protection
                                callback_tasks = []
                                for callback in self._callbacks:
                                    task = asyncio.create_task(
                                        self._execute_callback(callback, price_data)
                                    )
                                    callback_tasks.append(task)
                                
                                if callback_tasks:
                                    try:
                                        await asyncio.wait_for(
                                            asyncio.gather(*callback_tasks),
                                            timeout=1.0
                                        )
                                    except asyncio.TimeoutError:
                                        self.logger.warning(
                                            f"Callback execution timed out for {symbol}",
                                            extra={"category": DebugCategory.API.value}
                                        )
                                    except Exception as e:
                                        self.logger.error(
                                            f"Error executing callbacks for {symbol}: {str(e)}",
                                            extra={"category": DebugCategory.API.value}
                                        )
                                
                        except (KeyError, ValueError) as e:
                            self.logger.error(
                                f"Error processing ticker data: {str(e)}",
                                extra={"category": DebugCategory.API.value}
                            )

                except websockets.ConnectionClosed:
                    self.logger.warning(
                        "WebSocket connection closed",
                        extra={"category": DebugCategory.API.value}
                    )
                    await self._handle_connection_error()
                    break
                except Exception as e:
                    self.logger.error(
                        f"Error handling WebSocket message: {str(e)}",
                        extra={"category": DebugCategory.API.value}
                    )
                    if not self._running or not self._initialized or not self.ws:
                        break
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            self.logger.info(
                "Message handler task cancelled",
                extra={"category": DebugCategory.API.value}
            )
            raise
        finally:
            self.logger.info(
                "Message handler stopped",
                extra={"category": DebugCategory.API.value}
            )

    async def _handle_connection_error(self) -> None:
        """Handle WebSocket connection errors"""
        self.logger.warning(
            "WebSocket connection lost, attempting to reconnect",
            extra={"category": DebugCategory.API.value}
        )

        try:
            # Save current state
            current_subscriptions = set(self.subscribed_symbols)
            current_callbacks = list(self._callbacks)

            # Reset state
            self._initialized = False
            self._running = False
            self.subscribed_symbols.clear()
            self._callbacks.clear()

            # Close existing connection and tasks
            if self.ws:
                try:
                    await self.ws.close()
                except Exception:
                    pass
            self.ws = None

            if hasattr(self, '_message_task') and self._message_task:
                self._message_task.cancel()
                try:
                    await self._message_task
                except asyncio.CancelledError:
                    pass
                self._message_task = None

            # Wait a bit before reconnecting
            await asyncio.sleep(1)

            # Reinitialize connection
            await self.initialize()

            if self.ws and self._initialized and self._running:
                # Restore state only if initialization succeeded
                self._callbacks.extend(current_callbacks)
                for symbol in current_subscriptions:
                    try:
                        await self.subscribe_price_updates(symbol)
                        await asyncio.sleep(0.1)  # Small delay between subscriptions
                    except Exception as e:
                        self.logger.error(
                            f"Failed to resubscribe to {symbol}: {str(e)}",
                            extra={"category": DebugCategory.API.value}
                        )

        except Exception as e:
            self.logger.error(
                f"Error reconnecting WebSocket: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            # Reset state on failure
            self._initialized = False
            self._running = False
            if self.ws:
                try:
                    await self.ws.close()
                except Exception:
                    pass
            self.ws = None
            await asyncio.sleep(5)  # Longer wait before next retry

    async def _execute_callback(self, callback: callable, price_data: Dict[str, Any]) -> None:
        """Execute a callback with price data"""
        try:
            await callback(price_data)
            self.logger.debug(
                f"Price update callback executed: {price_data}",
                extra={"category": DebugCategory.API.value}
            )
        except Exception as e:
            self.logger.error(
                f"Error in price update callback: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )

    async def close(self) -> None:
        """Close the WebSocket connection"""
        # Set flags first to prevent new operations
        self._running = False
        self._initialized = False
        
        try:
            # Cancel message handler task first
            if hasattr(self, '_message_task') and self._message_task:
                self._message_task.cancel()
                try:
                    await self._message_task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass
                finally:
                    self._message_task = None

            if self.ws:
                try:
                    # Unsubscribe from all symbols
                    symbols = list(self.subscribed_symbols)
                    for symbol in symbols:
                        try:
                            await self.unsubscribe_price_updates(symbol)
                        except Exception:
                            pass
                    
                    # Close WebSocket connection
                    await self.ws.close()
                except Exception as e:
                    self.logger.error(
                        f"Error closing WebSocket: {str(e)}",
                        extra={"category": DebugCategory.API.value}
                    )
                finally:
                    self.ws = None
        finally:
            # Clear all state
            self.subscribed_symbols.clear()
            self._callbacks.clear()
            # Wait a bit to ensure cleanup
            await asyncio.sleep(0.1)
