import os
from typing import Dict, Any, Optional
from ..utils.logging_config import get_logger, DebugCategory


class TradingViewChart:
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

        return config

    def get_widget_html(
        self,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        theme: Optional[str] = None
    ) -> str:
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
