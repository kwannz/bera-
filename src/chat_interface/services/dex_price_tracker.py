import os
import json
import aiohttp
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from ..utils.rate_limiter import RateLimiter
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.metrics import Metrics
from ..utils.logging_config import get_logger, DebugCategory


class DexPriceTracker(ABC):
    """Base class for DEX price tracking"""
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

    @abstractmethod
    async def get_price_data(self) -> Dict[str, Any]:
        """Get price data from DEX"""
        pass


class PancakeSwapTracker(DexPriceTracker):
    """PancakeSwap price tracker implementation"""
    API_URL = "https://api.pancakeswap.finance/api/v2"

    async def get_price_data(self) -> Dict[str, Any]:
        """Get price data from PancakeSwap"""
        if not await self.rate_limiter.check_rate_limit("pancakeswap", limit=100, window=60):
            self.logger.warning(
                "Rate limit exceeded for PancakeSwap",
                extra={"category": DebugCategory.API.value}
            )
            return {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_URL}/tokens/bera"
                ) as response:
                    if response.status == 429:  # Rate limited
                        await self.rate_limiter.check_rate_limit("pancakeswap", limit=100, window=60)  # Consume a token
                        self.logger.warning(
                            "Rate limit exceeded for PancakeSwap",
                            extra={"category": DebugCategory.API.value}
                        )
                        return {}
                    elif response.status == 200:
                        data = await response.json()
                        return self._format_response(data)
                    self.logger.error(
                        f"PancakeSwap API error: {response.status}",
                        extra={"category": DebugCategory.API.value}
                    )
                    return {}
        except Exception as e:
            self.logger.error(
                f"Error fetching PancakeSwap data: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return {}

    def _format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format PancakeSwap response"""
        try:
            return {
                "price": float(data.get("price", 0)),
                "volume_24h": float(data.get("volume24h", 0)),
                "price_change_24h": float(data.get("priceChange24h", 0))
            }
        except (ValueError, TypeError) as e:
            self.logger.error(
                f"Error formatting PancakeSwap data: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return {}


class UniswapTracker(DexPriceTracker):
    """Uniswap price tracker implementation"""
    API_URL = "https://api.uniswap.org/v2"

    async def get_price_data(self) -> Dict[str, Any]:
        """Get price data from Uniswap"""
        if not await self.rate_limiter.check_rate_limit("uniswap", limit=100, window=60):
            self.logger.warning(
                "Rate limit exceeded for Uniswap",
                extra={"category": DebugCategory.API.value}
            )
            return {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_URL}/tokens/bera"
                ) as response:
                    if response.status == 429:  # Rate limited
                        self.logger.warning(
                            "Rate limit exceeded for Uniswap",
                            extra={"category": DebugCategory.API.value}
                        )
                        return {}
                    elif response.status == 200:
                        data = await response.json()
                        return self._format_response(data)
                    self.logger.error(
                        f"Uniswap API error: {response.status}",
                        extra={"category": DebugCategory.API.value}
                    )
                    return {}
        except Exception as e:
            self.logger.error(
                f"Error fetching Uniswap data: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return {}

    def _format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Uniswap response"""
        try:
            return {
                "price": float(data.get("price", 0)),
                "volume_24h": float(data.get("volume24h", 0)),
                "price_change_24h": float(data.get("priceChange24h", 0))
            }
        except (ValueError, TypeError) as e:
            self.logger.error(
                f"Error formatting Uniswap data: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return {}


class JupiterTracker(DexPriceTracker):
    """Jupiter price tracker implementation"""
    API_URL = "https://price.jup.ag/v4"

    async def get_price_data(self) -> Dict[str, Any]:
        """Get price data from Jupiter"""
        if not await self.rate_limiter.check_rate_limit("jupiter", limit=60, window=60):
            self.logger.warning(
                "Rate limit exceeded for Jupiter",
                extra={"category": DebugCategory.API.value}
            )
            return {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_URL}/price?id=bera"
                ) as response:
                    if response.status == 429:  # Rate limited
                        self.logger.warning(
                            "Rate limit exceeded for Jupiter",
                            extra={"category": DebugCategory.API.value}
                        )
                        return {}
                    elif response.status == 200:
                        data = await response.json()
                        return self._format_response(data)
                    self.logger.error(
                        f"Jupiter API error: {response.status}",
                        extra={"category": DebugCategory.API.value}
                    )
                    return {}
        except Exception as e:
            self.logger.error(
                f"Error fetching Jupiter data: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return {}

    def _format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Jupiter response"""
        try:
            return {
                "price": float(data.get("price", 0)),
                "volume_24h": float(data.get("volume24h", 0)),
                "price_change_24h": float(data.get("priceChange24h", 0))
            }
        except (ValueError, TypeError) as e:
            self.logger.error(
                f"Error formatting Jupiter data: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return {}
