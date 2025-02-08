from enum import Enum
from typing import Dict, Any, Union, List


class ContentType(Enum):
    MARKET = "market"
    NEWS = "news"
    GENERAL = "general"


class ResponseFormatter:
    @staticmethod
    def format_response(
        raw_response: Union[Dict[str, Any], List[Dict[str, Any]]],
        data_type: ContentType
    ) -> str:
        """应用模板格式化响应"""
        if data_type == ContentType.MARKET:
            assert isinstance(raw_response, dict)
            return ResponseFormatter._apply_market_template(raw_response)
        elif data_type == ContentType.NEWS:
            if isinstance(raw_response, list):
                return ResponseFormatter._apply_news_template(raw_response)
            return ""
        return str(raw_response)

    @staticmethod
    def _apply_market_template(data: Dict[str, Any]) -> str:
        """使用PRICE_UPDATE_TEMPLATE模板"""
        if "error" in data:
            return f"❌ 错误：{data['error']}"
        return (
            f"📈 当前价格：${data['price']}\n"
            f"💰 24小时交易量：${data['volume']}\n"
            f"📊 价格变动：{data['change']}%"
        )

    @staticmethod
    def _apply_news_template(
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """使用NEWS_UPDATE_TEMPLATE模板"""
        if isinstance(data, list):
            result = []
            for item in data:
                result.append(
                    f"📰 标题：{item['title']}\n"
                    f"🔍 来源：{item['source']}\n"
                    f"⏰ 时间：{item['date']}\n"
                    f"{item['summary']}\n"
                )
            return "\n".join(result)
        return str(data)
