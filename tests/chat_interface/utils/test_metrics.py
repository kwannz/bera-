import pytest
import asyncio
from src.chat_interface.utils.metrics import Metrics


def test_metrics_initialization():
    """Test metrics initialization with empty dictionaries"""
    metrics = Metrics()
    assert metrics.api_latency == {}
    assert metrics.error_count == {}
    assert metrics.request_count == {}


def test_record_latency():
    """Test recording API latency"""
    metrics = Metrics()
    metrics.record_latency("test_endpoint", 0.5)
    assert metrics.api_latency["test_endpoint"] == 0.5


def test_record_error():
    """Test recording errors"""
    metrics = Metrics()
    metrics.record_error("test_endpoint")
    assert metrics.error_count["test_endpoint"] == 1
    metrics.record_error("test_endpoint")
    assert metrics.error_count["test_endpoint"] == 2


def test_record_request():
    """Test recording requests"""
    metrics = Metrics()
    metrics.record_request("test_endpoint")
    assert metrics.request_count["test_endpoint"] == 1
    metrics.record_request("test_endpoint")
    assert metrics.request_count["test_endpoint"] == 2


@pytest.mark.asyncio
async def test_request_timing():
    """Test request timing functionality"""
    metrics = Metrics()
    metrics.start_request("test_endpoint")
    await asyncio.sleep(0.1)  # Simulate some work
    metrics.end_request("test_endpoint")
    assert "test_endpoint" in metrics.api_latency
    assert metrics.api_latency["test_endpoint"] > 0
    assert metrics.request_count["test_endpoint"] == 1


def test_get_metrics():
    """Test getting all metrics"""
    metrics = Metrics()
    metrics.record_latency("endpoint1", 0.5)
    metrics.record_error("endpoint2")
    metrics.record_request("endpoint3")

    all_metrics = metrics.get_metrics()
    assert all_metrics["api_latency"]["endpoint1"] == 0.5
    assert all_metrics["error_count"]["endpoint2"] == 1
    assert all_metrics["request_count"]["endpoint3"] == 1


def test_multiple_endpoints():
    """Test handling multiple endpoints"""
    metrics = Metrics()
    # Record data for multiple endpoints
    metrics.record_latency("endpoint1", 0.5)
    metrics.record_latency("endpoint2", 0.7)
    metrics.record_error("endpoint1")
    metrics.record_error("endpoint2")
    metrics.record_request("endpoint1")
    metrics.record_request("endpoint2")

    # Verify each endpoint's data
    all_metrics = metrics.get_metrics()
    assert all_metrics["api_latency"]["endpoint1"] == 0.5
    assert all_metrics["api_latency"]["endpoint2"] == 0.7
    assert all_metrics["error_count"]["endpoint1"] == 1
    assert all_metrics["error_count"]["endpoint2"] == 1
    assert all_metrics["request_count"]["endpoint1"] == 1
    assert all_metrics["request_count"]["endpoint2"] == 1
