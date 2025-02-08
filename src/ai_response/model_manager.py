import os
import json
import aiohttp
import asyncio
from typing import Optional, Dict, List
from enum import Enum
from ..utils.logging_config import get_logger, DebugCategory

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

class ModelType(Enum):
    OLLAMA = "ollama"

class ContentType(Enum):
    MARKET = "market"
    NEWS = "news"
    POL = "pol"
    MINING = "mining"
    MEME = "meme"
    PRICE_ANALYSIS = "price_analysis"
    BGT_HOLDING = "bgt_holding"
    BGT_DELEGATION = "bgt_delegation"
    NFT = "nft"
    LENDING = "lending"
    BERAWAR = "berawar"
    AI_PROJECTS = "ai_projects"

PROMPT_TEMPLATES = {
    ContentType.MARKET: """生成BERA代币市场更新：
当前价格: {price} USD
24小时交易量: {volume} USD
价格变动: {change}%
分析风格：专业、信息丰富""",

    ContentType.NEWS: """生成Berachain最新动态：
新闻: {news}
影响: {impact}
分析风格：专业、信息丰富""",

    ContentType.POL: """解释POL（Protocol Owned Liquidity）：
定义：{definition}
参与方式：{participation}
风险提示：{risks}
分析风格：通俗易懂""",

    ContentType.MINING: """BGT挖矿策略分析：
当前收益率：{apy}%
挖矿池状态：{pool_status}
建议策略：{strategy}
风险提示：{risks}
分析风格：实用、详细""",

    ContentType.MEME: """Meme Token分析：
代币名称：{token_name}
市值：{market_cap}
交易量：{volume}
风险评级：{risk_level}
分析风格：客观、谨慎""",

    ContentType.PRICE_ANALYSIS: """BERA价格分析：
技术分析：{technical_analysis}
基本面：{fundamentals}
市场情绪：{sentiment}
预测建议：{recommendation}
分析风格：专业、全面""",

    ContentType.BGT_HOLDING: """BGT持有策略：
当前价格：{price}
市场趋势：{trend}
收益分析：{yield_analysis}
建议：{recommendation}
分析风格：理性、客观""",

    ContentType.BGT_DELEGATION: """BGT委托节点分析：
节点名称：{node_name}
委托收益率：{apy}%
节点表现：{performance}
风险评估：{risk_assessment}
分析风格：详细、客观""",

    ContentType.NFT: """NFT项目分析：
项目名称：{project_name}
市场表现：{market_performance}
独特优势：{unique_features}
投资建议：{investment_advice}
分析风格：专业、深入""",

    ContentType.LENDING: """借贷池分析：
池名称：{pool_name}
存款利率：{deposit_rate}%
借款利率：{borrow_rate}%
资金利用率：{utilization_rate}%
风险评估：{risk_assessment}
分析风格：专业、谨慎""",

    ContentType.BERAWAR: """BeraWar项目介绍：
项目概述：{overview}
游戏机制：{mechanics}
收益模式：{earning_model}
参与指南：{participation_guide}
分析风格：详细、易懂""",

    ContentType.AI_PROJECTS: """AI项目分析：
项目名称：{project_name}
技术创新：{innovation}
市场潜力：{market_potential}
投资建议：{investment_advice}
分析风格：专业、前瞻"""
}

class AIModelManager:
    def __init__(
        self,
        ollama_url: Optional[str] = None
    ):
        self.logger = get_logger(__name__)
        self.model_type = ModelType.OLLAMA
        self.ollama_url = ollama_url or os.getenv(
            "OLLAMA_URL",
            "http://localhost:11434"
        )
        
    async def generate_content(
        self,
        content_type: ContentType,
        params: Dict,
        max_length: int = 280,
        retries: int = MAX_RETRIES
    ) -> Optional[str]:
        try:
            prompt = PROMPT_TEMPLATES[content_type].format(**params)
            
            self.logger.debug(
                f"Generating {content_type.value} content",
                extra={"category": DebugCategory.API.value}
            )
            
            for attempt in range(retries):
                try:
                    content = await self._generate_ollama_content(prompt, max_length)
                    if content:
                        return content[:max_length]
                    
                    if attempt < retries - 1:
                        self.logger.warning(
                            f"Retrying content generation (attempt {attempt + 1}/{retries})",
                            extra={"category": DebugCategory.API.value}
                        )
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                except Exception as e:
                    if attempt < retries - 1:
                        self.logger.warning(
                            f"Error in content generation (attempt {attempt + 1}/{retries}): {str(e)}",
                            extra={"category": DebugCategory.API.value}
                        )
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        raise
            return None
                
        except Exception as e:
            self.logger.error(
                f"Error generating content: {str(e)}",
                extra={"category": DebugCategory.API.value}
            )
            return None
            
    async def _generate_ollama_content(self, prompt: str, max_length: int) -> Optional[str]:
        """生成AI响应内容"""
        try:
            # Ollama configuration
            model = "deepseek-r1:1.5b"
            temp = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
            
            # Prepare payload for Ollama API
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_predict": max_length,
                    "stop": ["</s>", "\n\n"]
                }
            }
            
            self.logger.debug(
                "Sending request to Ollama API",
                extra={
                    "category": DebugCategory.API.value,
                    "prompt_length": len(prompt),
                    "max_length": max_length,
                    "model": model
                }
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload,
                    timeout=10.0  # 10 second timeout
                ) as response:
                    if response.status == 200:
                        try:
                            result = await response.json()
                            if (isinstance(result, dict) and
                                    "response" in result and
                                    isinstance(result["response"], str)):
                                return result["response"][:max_length]
                            else:
                                self.logger.error(
                                    "Invalid response format from Ollama API",
                                    extra={
                                        "category": DebugCategory.API.value,
                                        "response": str(result)
                                    }
                                )
                        except json.JSONDecodeError as e:
                            self.logger.error(
                                f"Failed to parse Ollama response: {str(e)}",
                                extra={
                                    "category": DebugCategory.API.value,
                                    "response": await response.text()
                                }
                            )
                    else:
                        self.logger.error(
                            f"Ollama API error (status {response.status})",
                            extra={
                                "category": DebugCategory.API.value,
                                "response": await response.text()
                            }
                        )
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(
                "Ollama API request timed out",
                extra={"category": DebugCategory.API.value}
            )
            return None
        except Exception as e:
            self.logger.error(
                f"Unexpected error in Ollama API call: {str(e)}",
                extra={
                    "category": DebugCategory.API.value,
                    "error_type": type(e).__name__
                }
            )
            return None
