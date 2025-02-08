import os
import json
from typing import Dict, Any, Optional
from ..utils.rate_limiter import RateLimiter
from ..utils.metrics import Metrics

from typing import Dict, Any, Optional
 
from ..utils.logging_config import get_logger, DebugCategory


class TradingViewChart:
    """TradingView chart integration for BERA token"""
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        metrics: Optional[Metrics] = None
    ):
        self.rate_limiter = rate_limiter
        self.metrics = metrics
        self.logger = get_logger(__name__)
        self.cache_ttl = int(os.getenv("CHART_CACHE_TTL", "900"))  # 15 minutes
        self.widget_config = {
            "symbol": "BERAUSDT",
            "interval": "D",  # Default to daily
            "theme": "dark",
            "locale": "zh_CN",  # Default to Chinese
            "enable_publishing": False,
            "hide_top_toolbar": False,
            "hide_legend": False,
            "save_image": True,
            "container_id": "tradingview_chart",
            "studies": ["RSI", "MASimple@tv-basicstudies"],
            "style": "1",  # Candlestick
            "timezone": "Asia/Shanghai",
            "width": "100%",
            "height": "500"
    """TradingView chart integration service"""
    def __init__(self):
        self.logger = get_logger(__name__)
        self.widget_config = {
            "width": 980,
            "height": 610,
            "symbol": "BERAUSDT",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": False,
            "allow_symbol_change": True,
            "container_id": "tradingview_chart",
            "studies": [
                "MASimple@tv-basicstudies",
                "RSI@tv-basicstudies"
            ],
            "show_popup_button": False,
            "popup_width": "1000",
            "popup_height": "650",
            "hide_side_toolbar": False,
            "hide_legend": False,
            "save_image": True,
            "enable_publishing": False,
            "withdateranges": True,
            "hide_volume": False,
            "scaleshistory": True
        }

    def get_widget_config(
        self,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        theme: Optional[str] = None,
        studies: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get TradingView widget configuration with overrides"""
        theme: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get widget configuration with optional overrides"""
        config = self.widget_config.copy()
        
        if symbol:
            config["symbol"] = symbol
        if interval:
            config["interval"] = interval
        if theme:
            config["theme"] = theme
        if studies:
            config["studies"] = studies
            
        # Update with any additional kwargs
        config.update(kwargs)
        return config

    def get_widget_html(self, **kwargs) -> str:
        """Generate TradingView widget HTML code"""
        config = self.get_widget_config(**kwargs)
        container_id = config["container_id"]
        
        return f"""
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div id="{container_id}" style="height:calc(100% - 32px);width:100%"></div>
  <div class="tradingview-widget-copyright">
    <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
      <span class="blue-text">Track BERA on TradingView</span>
    </a>
  </div>
</div>
<script type="text/javascript">
new TradingView.widget({
    {self._format_config_for_js(config)}
});
</script>
<!-- TradingView Widget END -->
"""

    def get_chart_url(

        return config

    def get_widget_html(
        self,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        theme: Optional[str] = None
    ) -> str:
        """Generate TradingView chart URL"""
        config = self.get_widget_config(symbol, interval, theme)
        symbol = config["symbol"]
        interval = config["interval"]
        theme = config["theme"]
        
        return (
            f"https://www.tradingview.com/chart/"
            f"?symbol={symbol}"
            f"&interval={interval}"
            f"&theme={theme}"
        )

    def _format_config_for_js(self, config: Dict[str, Any]) -> str:
        """Format configuration dictionary as JavaScript object"""
        js_items = []
        for key, value in config.items():
            if isinstance(value, bool):
                js_items.append(f'    "{key}": {str(value).lower()}')
            elif isinstance(value, (int, float)):
                js_items.append(f'    "{key}": {value}')
            elif isinstance(value, list):
                values = [f'"{v}"' for v in value]
                js_items.append(f'    "{key}": [{",".join(values)}]')
            else:
                js_items.append(f'    "{key}": "{value}"')
        
        return ",\n".join(js_items)
=======
        """Get HTML code for embedding TradingView chart"""
        config = self.get_widget_config(symbol, interval, theme)
        
        try:
            html = f"""
            <!-- TradingView Widget BEGIN -->
            <div class="tradingview-widget-container">
                <div id="{config['container_id']}"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({self._format_config_for_js(config)});
                </script>
            </div>
            <!-- TradingView Widget END -->
            """
            return html
        except Exception as e:
            self.logger.error(
                f"Error generating widget HTML: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return ""

    def _format_config_for_js(self, config: Dict[str, Any]) -> str:
        """Format configuration dictionary for JavaScript"""
        try:
            # Convert Python dict to JavaScript object notation
            js_items = []
            for key, value in config.items():
                if isinstance(value, bool):
                    js_value = str(value).lower()
                elif isinstance(value, (int, float)):
                    js_value = str(value)
                elif isinstance(value, list):
                    js_value = f"[{','.join(repr(v) for v in value)}]"
                else:
                    js_value = f'"{value}"'
                js_items.append(f'"{key}": {js_value}')
            
            return "{" + ",\n".join(js_items) + "}"
        except Exception as e:
            self.logger.error(
                f"Error formatting config for JS: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return "{}"

    def get_chart_url(
        self,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        theme: Optional[str] = None
    ) -> str:
        """Get TradingView chart URL for direct linking"""
        config = self.get_widget_config(symbol, interval, theme)
        symbol = config["symbol"].replace("USDT", "")
        
        try:
            url = (
                f"https://www.tradingview.com/chart/"
                f"?symbol={symbol}&interval={config['interval']}"
                f"&theme={config['theme']}"
            )
            return url
        except Exception as e:
            self.logger.error(
                f"Error generating chart URL: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return ""
