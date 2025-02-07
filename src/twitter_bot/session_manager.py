import json
import logging
from typing import Dict, List, Optional
from ..utils.logging_config import get_logger, DebugCategory

class SessionManager:
    def __init__(self):
        self.cookie_store: Dict[str, str] = {}
        self.logger = get_logger(__name__)
        
    async def save_cookies(self, cookies: List[Dict[str, str]]) -> None:
        """Save session cookies securely
        
        Args:
            cookies: List of cookie dictionaries with 'name' and 'value' keys
        """
        try:
            self.cookie_store = {
                cookie["name"]: cookie["value"]
                for cookie in cookies
                if "name" in cookie and "value" in cookie
            }
            self.logger.debug(
                f"Saved {len(self.cookie_store)} cookies",
                extra={"category": DebugCategory.API.value}
            )
        except Exception as e:
            self.logger.error(
                f"Failed to save cookies: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            raise
            
    async def load_cookies(self) -> List[Dict[str, str]]:
        """Load saved cookies
        
        Returns:
            List of cookie dictionaries with 'name' and 'value' keys
        """
        try:
            cookies = [
                {"name": name, "value": value}
                for name, value in self.cookie_store.items()
            ]
            self.logger.debug(
                f"Loaded {len(cookies)} cookies",
                extra={"category": DebugCategory.API.value}
            )
            return cookies
        except Exception as e:
            self.logger.error(
                f"Failed to load cookies: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return []
            
    def clear_cookies(self) -> None:
        """Clear all stored cookies"""
        self.cookie_store.clear()
        self.logger.debug(
            "Cleared all cookies",
            extra={"category": DebugCategory.API.value}
        )
