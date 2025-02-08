import time
from enum import Enum
from typing import Optional, Callable, Any, TypeVar, Coroutine, TypeAlias

T = TypeVar('T')
AsyncFunc: TypeAlias = Callable[..., Coroutine[Any, Any, T]]


class CircuitState(Enum):
    """断路器状态"""
    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 断开状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """断路器实现，用于防止系统级联失败"""

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        name: str = "default"
    ):
        """初始化断路器

        Args:
            failure_threshold: 失败阈值，达到此值后断路器打开
            reset_timeout: 重置超时时间（秒），超过此时间后尝试半开状态
            name: 断路器名称，用于标识不同的服务
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None

    def _should_allow_request(self) -> bool:
        """检查是否允许请求通过"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if (self.last_failure_time and
                    time.time() - self.last_failure_time > self.reset_timeout):
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN state
        return True

    def _on_success(self) -> None:
        """处理成功请求"""
        self.failure_count = 0
        self.last_success_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        """处理失败请求"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if (self.failure_count >= self.failure_threshold or
                self.state == CircuitState.HALF_OPEN):
            self.state = CircuitState.OPEN

    async def call(self, func: AsyncFunc, *args: Any, **kwargs: Any) -> T:
        """调用目标函数并应用断路器逻辑

        Args:
            func: 异步目标函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            目标函数的返回值

        Raises:
            CircuitBreakerError: 断路器打开时抛出
            Exception: 目标函数抛出的异常
        """
        if not self._should_allow_request():
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is {self.state.value}"
            )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e


class CircuitBreakerError(Exception):
    """断路器错误，当断路器打开时抛出"""
    pass
