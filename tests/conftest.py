"""Pytest configuration and fixtures."""
import pytest
from rx_events import EventBus


@pytest.fixture
def event_bus():
    """Create a fresh EventBus for each test."""
    return EventBus()


@pytest.fixture
def test_channel(event_bus):
    """Create a test channel."""
    return event_bus.create_channel("test_channel", timeout_seconds=300)
