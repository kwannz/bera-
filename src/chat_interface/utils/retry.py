from functools import wraps
import asyncio
from typing import (
    TypeVar, Callable, Any, Tuple, Optional,
    Union, Coroutine, TypeAlias
)

T = TypeVar('T')
ExceptionTypes = Union[Tuple[type[Exception], ...], type[Exception]]
AsyncFunc: TypeAlias = Callable[..., Coroutine[Any, Any, T]]


def async_retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Optional[ExceptionTypes] = None
) -> Callable[[AsyncFunc], AsyncFunc]:
    """异步重试装饰器

    Args:
        retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍数
        exceptions: 需要重试的异常类型，默认为所有异常

    Returns:
        装饰器函数
    """
    if exceptions is None:
        exceptions = (Exception,)
    elif isinstance(exceptions, type) and issubclass(exceptions, Exception):
        exceptions = (exceptions,)

    def decorator(func: AsyncFunc) -> AsyncFunc:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            retry_count = 0
            current_delay = delay

            while retry_count < retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1
                    if retry_count == retries:
                        raise e
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            raise RuntimeError("Should not reach here")
        return wrapper  # type: ignore
    return decorator
