import redis.asyncio
from typing import List, Dict, Optional
import json
from redis.asyncio.client import Redis


class ContextManager:
    def __init__(
        self,
        redis_client: Optional[Redis] = None
    ):
        self._redis_client = redis_client
        self.max_context_rounds = 5

    @property
    def redis_client(self) -> Redis:
        """Get the Redis client instance"""
        if not self._redis_client:
            raise RuntimeError("Redis client not initialized")
        return self._redis_client

    async def initialize(self) -> None:
        """Initialize the context manager"""
        if not self._redis_client:
            self._redis_client = await redis.asyncio.Redis.from_url(
                "redis://localhost:6379/0",
                decode_responses=False
            )
            if not self._redis_client:
                raise RuntimeError("Failed to initialize Redis client")
            # Verify Redis connection
            await self._redis_client.ping()
            # Clear any existing context data
            await self._redis_client.delete("chat:context:*")

    def _compress_context(self, context: List[Dict]) -> List[Dict]:
        """压缩对话上下文，保留关键信息

        压缩策略:
        1. 如果消息数量少于等于2条，保留所有消息
        2. 保留第一条用户消息作为初始上下文
        3. 保留最后2轮对话（4条消息）作为即时上下文
        """
        if len(context) <= 2:
            return context

        # Keep first user message for context
        compressed = []
        for msg in context[:2]:  # Look in first 2 messages
            if msg.get("role") == "user":
                compressed.append(msg)
                break

        # Keep last 2 rounds (4 messages) for immediate context
        compressed.extend(context[-4:])

        return compressed

    async def get_context(self, session_id: str) -> List[Dict]:
        """获取压缩后的对话上下文"""
        context_key = f"chat:context:{session_id}"
        raw_context = await self.redis_client.get(context_key)
        if raw_context:
            try:
                context = json.loads(raw_context)
                return self._compress_context(context)
            except json.JSONDecodeError:
                await self.redis_client.delete(context_key)
        return []

    async def add_message(self, session_id: str, message: Dict):
        """添加新消息到上下文"""
        context_key = f"chat:context:{session_id}"
        context = await self.get_context(session_id)
        context.append(message)

        # 保持最近5轮对话
        if len(context) > self.max_context_rounds * 2:
            context = context[-self.max_context_rounds * 2:]

        await self.redis_client.setex(
            context_key,
            3600,  # 1小时过期
            json.dumps(context)
        )
