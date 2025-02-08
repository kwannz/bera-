from dataclasses import dataclass, field
from typing import Dict, Any
import time


@dataclass
class Metrics:
    """性能指标收集器"""
    api_latency: Dict[str, float] = field(default_factory=dict)
    error_count: Dict[str, int] = field(default_factory=dict)
    request_count: Dict[str, int] = field(default_factory=dict)
    _start_times: Dict[str, float] = field(default_factory=dict)

    def start_request(self, endpoint: str) -> None:
        """开始记录请求时间"""
        self._start_times[endpoint] = time.monotonic()
        self.record_request(endpoint)

    def end_request(self, endpoint: str) -> None:
        """结束记录请求时间并计算延迟"""
        if endpoint in self._start_times:
            duration = time.monotonic() - self._start_times[endpoint]
            self.record_latency(endpoint, duration)
            del self._start_times[endpoint]

    def record_latency(self, endpoint: str, duration: float) -> None:
        """记录API延迟"""
        self.api_latency[endpoint] = duration

    def record_error(self, endpoint: str) -> None:
        """记录错误次数"""
        self.error_count[endpoint] = self.error_count.get(endpoint, 0) + 1

    def record_request(self, endpoint: str) -> None:
        """记录请求次数"""
        self.request_count[endpoint] = self.request_count.get(endpoint, 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return {
            "api_latency": self.api_latency,
            "error_count": self.error_count,
            "request_count": self.request_count
        }
