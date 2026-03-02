"""
Rx-Events Package

A flexible event-driven system with acknowledgment tracking using Pydantic and ReactiveX.

Usage:
    from rx_events import EventBus, BaseEvent, EventStatus
    from pydantic import Field
    
    class MyEvent(BaseEvent):
        data: str
        
        @property
        def event_type(self) -> str:
            return "my_event"
        
        def to_payload(self) -> Dict[str, Any]:
            return {"data": self.data}
"""

from .events import (
    EventStatus,
    BaseEvent,
    Event,
    BaseEventAck,
    EventAck,
)
from .event_bus import EventBus, event_bus
from .ack_channel import AckChannel

__all__ = [
    # Enums
    "EventStatus",
    # Base Classes
    "BaseEvent",
    "BaseEventAck",
    # Standard Classes
    "Event",
    "EventAck",
    # Event Bus
    "EventBus",
    "event_bus",
    # Channels
    "AckChannel",
]

__version__ = "0.1.0"
