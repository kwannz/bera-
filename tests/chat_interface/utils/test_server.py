from websockets.legacy.server import serve
from typing import Optional, Any
from src.chat_interface.handlers.websocket_handler import WebSocketHandler


class TestWebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server: Optional[Any] = None
        self.handler = WebSocketHandler()

    async def start(self) -> None:
        """启动测试服务器"""
        self.server = await serve(
            self.handler.handle_connection,
            self.host,
            self.port
        )

    async def stop(self) -> None:
        """停止测试服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    @property
    def url(self) -> str:
        """获取服务器URL"""
        return f"ws://{self.host}:{self.port}"
