import redis
from typing import List, Dict
import json


class ContextManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0
        )
        self.max_context_rounds = 5

    async def get_context(self, session_id: str) -> List[Dict]:
        """获取压缩后的对话上下文"""
        context_key = f"chat:context:{session_id}"
        raw_context = self.redis_client.get(context_key)
        if raw_context:
            return json.loads(raw_context)
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
