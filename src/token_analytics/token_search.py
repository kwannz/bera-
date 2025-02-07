import logging
from typing import List, Optional, Dict
from .token_validator import TokenMetadata, TokenValidator
from ..utils.logging_config import get_logger, DebugCategory

class TokenSearch:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.validator = TokenValidator()
        self._search_cache: Dict[str, TokenMetadata] = {}
        
    async def search_by_address(self, address: str) -> Optional[TokenMetadata]:
        try:
            self.logger.debug(
                f"Searching for token by address: {address}",
                extra={"category": DebugCategory.SEARCH.value}
            )
            
            # Check cache first
            if address in self._search_cache:
                self.logger.debug(
                    f"Token found in cache: {address}",
                    extra={"category": DebugCategory.SEARCH.value}
                )
                return self._search_cache[address]
            
            # Validate address format
            if not self.validator.validate_address(address):
                self.logger.warning(
                    f"Invalid token address format: {address}",
                    extra={"category": DebugCategory.SEARCH.value}
                )
                return None
            
            # Get token metadata
            metadata = await self.validator.get_token_metadata(address)
            if metadata:
                self._search_cache[address] = metadata
                self.logger.debug(
                    f"Token metadata retrieved and cached: {metadata}",
                    extra={"category": DebugCategory.SEARCH.value}
                )
                return metadata
            
            self.logger.info(
                f"No token found for address: {address}",
                extra={"category": DebugCategory.SEARCH.value}
            )
            return None
            
        except Exception as e:
            self.logger.error(
                f"Error searching for token: {str(e)}",
                extra={"category": DebugCategory.SEARCH.value}
            )
            return None
            
    async def search_by_symbol(self, symbol: str) -> List[TokenMetadata]:
        try:
            self.logger.debug(
                f"Searching for tokens by symbol: {symbol}",
                extra={"category": DebugCategory.SEARCH.value}
            )
            
            # For now, just search through cache
            results = [
                token for token in self._search_cache.values()
                if token.symbol.lower() == symbol.lower()
            ]
            
            self.logger.debug(
                f"Found {len(results)} tokens for symbol {symbol}",
                extra={"category": DebugCategory.SEARCH.value}
            )
            
            return results
            
        except Exception as e:
            self.logger.error(
                f"Error searching by symbol: {str(e)}",
                extra={"category": DebugCategory.SEARCH.value}
            )
            return []
