import pytest
from src.chat_interface.services.chart_service import TradingViewChart


def test_tradingview_config():
    """Test TradingView widget configuration"""
    chart = TradingViewChart()
    config = chart.widget_config
    assert "symbol" in config
    assert config["symbol"] == "BERAUSDT"
    assert "interval" in config
    assert "theme" in config
    assert "container_id" in config


def test_widget_config_overrides():
    """Test widget configuration overrides"""
    chart = TradingViewChart()
    config = chart.get_widget_config(
        symbol="BERABTC",
        interval="1H",
        theme="light"
    )
    assert config["symbol"] == "BERABTC"
    assert config["interval"] == "1H"
    assert config["theme"] == "light"


def test_widget_html_generation():
    """Test widget HTML code generation"""
    chart = TradingViewChart()
    html = chart.get_widget_html()
    assert "TradingView Widget" in html
    assert "tradingview-widget-container" in html
    assert "tradingview_chart" in html
    assert "TradingView.widget" in html


def test_widget_html_with_overrides():
    """Test widget HTML generation with overrides"""
    chart = TradingViewChart()
    html = chart.get_widget_html(
        symbol="BERABTC",
        interval="1H",
        theme="light"
    )
    assert "BERABTC" in html
    assert "light" in html


def test_chart_url_generation():
    """Test chart URL generation"""
    chart = TradingViewChart()
    url = chart.get_chart_url()
    assert "tradingview.com/chart" in url
    assert "BERA" in url
    assert "interval" in url
    assert "theme" in url


def test_chart_url_with_overrides():
    """Test chart URL generation with overrides"""
    chart = TradingViewChart()
    url = chart.get_chart_url(
        symbol="BERABTC",
        interval="1H",
        theme="light"
    )
    assert "BERA" in url
    assert "interval=1H" in url
    assert "theme=light" in url


def test_config_js_formatting():
    """Test JavaScript configuration formatting"""
    chart = TradingViewChart()
    config = {
        "symbol": "BERAUSDT",
        "interval": "D",
        "enable_publishing": False,
        "studies": ["RSI", "MASimple"]
    }
    js_config = chart._format_config_for_js(config)
    assert '"symbol": "BERAUSDT"' in js_config
    assert '"interval": "D"' in js_config
    assert '"enable_publishing": false' in js_config
    # Check studies array content regardless of quote style
    assert any(f'studies": [{q}RSI{q},{q}MASimple{q}]' in js_config for q in ['"', "'"])
