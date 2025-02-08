from enum import Enum


class ContentType(Enum):
    MARKET = "market"
    NEWS = "news"
    GENERAL = "general"


class ResponseFormatter:
    @staticmethod
    def format_response(raw_response: str, data_type: ContentType) -> str:
        """应用模板格式化响应"""
        if data_type == ContentType.MARKET:
            return ResponseFormatter._apply_market_template(raw_response)
        elif data_type == ContentType.NEWS:
            return ResponseFormatter._apply_news_template(raw_response)
        return raw_response

    @staticmethod
    def _apply_market_template(text: str) -> str:
        """使用PRICE_UPDATE_TEMPLATE模板"""
        return (
            text.replace("Price:", "📈 当前价格：")
                .replace("Volume:", "💰 24小时交易量：")
                .replace("Change:", "📊 价格变动：")
        )

    @staticmethod
    def _apply_news_template(text: str) -> str:
        """使用NEWS_UPDATE_TEMPLATE模板"""
        return (
            text.replace("Title:", "📰 标题：")
                .replace("Source:", "🔍 来源：")
                .replace("Time:", "⏰ 时间：")
        )
