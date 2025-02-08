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
            f"📈 当前价格：${data.get('price', '0.00')}\n"
            f"💰 24小时交易量：${data.get('volume', '0')}\n"
            f"📊 价格变动：{data.get('change', '0')}%"
        )

    @staticmethod
    def _apply_news_template(
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """使用NEWS_UPDATE_TEMPLATE模板"""
        if isinstance(data, list) and data:
            result = []
            for item in data:
                if isinstance(item, dict):
                    result.append(
                        f"📰 标题：{item.get('title', '')}\n"
                        f"🔍 来源：{item.get('source', '')}\n"
                        f"⏰ 时间：{item.get('date', '')}\n"
                        f"{item.get('summary', '')}\n"
                    )
            return "\n".join(result) if result else ""
        return ""
