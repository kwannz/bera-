import redis
from typing import List, Dict, Set
import json
import re


class ContextManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0
        )
        self.max_context_rounds = 5

    def _compress_context(self, context: List[Dict]) -> List[Dict]:
        """使用实体识别算法压缩上下文"""
        compressed = []
        entities: Set[str] = set()

        for msg in context:
            # Extract entities (keywords, numbers, symbols)
            content = str(msg.get("content", ""))
            pattern = r'\b\w+\b|\$\d+\.?\d*|\d+%'
            msg_entities = set(re.findall(pattern, content))

            # Only keep messages with new entities
            if msg_entities - entities:
                compressed.append(msg)
                entities.update(msg_entities)

        return compressed

    async def get_context(self, session_id: str) -> List[Dict]:
        """获取压缩后的对话上下文"""
        context_key = f"chat:context:{session_id}"
        raw_context = self.redis_client.get(context_key)
        if raw_context:
            context = json.loads(raw_context)
            return self._compress_context(context)
        return []

    async def add_message(self, session_id: str, message: Dict):
        """添加新消息到上下文"""
        context_key = f"chat:context:{session_id}"
        context = await self.get_context(session_id)
        context.append(message)

        # 保持最近5轮对话
        if len(context) > self.max_context_rounds * 2:
            context = context[-self.max_context_rounds * 2:]

        self.redis_client.setex(
            context_key,
            3600,  # 1小时过期
            json.dumps(context)
        )
