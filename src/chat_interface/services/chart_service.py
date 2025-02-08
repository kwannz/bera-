import os
import json
from typing import Dict, Any, Optional
from ..utils.rate_limiter import RateLimiter
from ..utils.metrics import Metrics
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
