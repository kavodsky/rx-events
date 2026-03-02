"""
Example: Creating Custom Event Classes with Pydantic

This example demonstrates how to extend BaseEvent to create custom event types
with type-safe properties and validation using Pydantic.
"""

import time
import uuid as uuid_lib
from typing import Dict, Any, Optional
from rx_events import BaseEvent, EventBus, EventStatus, EventAck
from pydantic import Field, field_validator


# Example 1: Simple Custom Event
class UserBehaviorEvent(BaseEvent):
    """Custom event for user behavior analysis with typed fields."""
    
    user_id: str
    behavior_data: Dict[str, Any]
    session_data: Dict[str, Any]
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    correlation_id: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "user_behavior_analysis"
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "behavior_data": self.behavior_data,
            "session_data": self.session_data
        }
    
    @classmethod
    def from_event(cls, event):
        """Custom parsing from standard Event."""
        return cls(
            uuid=event.uuid,
            timestamp=event.timestamp,
            correlation_id=event.correlation_id,
            user_id=event.payload["user_id"],
            behavior_data=event.payload.get("behavior_data", {}),
            session_data=event.payload.get("session_data", {})
        )


# Example 2: Event with Validation
class RecommendationEvent(BaseEvent):
    """Custom event for recommendations with validation."""
    
    user_id: str
    context: Dict[str, Any]
    user_history: list
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    correlation_id: Optional[str] = None
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user_id is not empty."""
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v
    
    @field_validator('user_history')
    @classmethod
    def validate_user_history(cls, v: list) -> list:
        """Validate user_history is a list."""
        if not isinstance(v, list):
            raise ValueError("user_history must be a list")
        return v
    
    @property
    def event_type(self) -> str:
        return "recommendation_request"
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "context": self.context,
            "user_history": self.user_history
        }
    
    @classmethod
    def from_event(cls, event):
        return cls(
            uuid=event.uuid,
            timestamp=event.timestamp,
            correlation_id=event.correlation_id,
            user_id=event.payload["user_id"],
            context=event.payload.get("context", {}),
            user_history=event.payload.get("user_history", [])
        )


# Example 3: Event with Helper Methods
class AnalyticsEvent(BaseEvent):
    """Custom event with helper methods for analytics processing."""
    
    metrics: Dict[str, float]
    dimensions: Dict[str, Any]
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    correlation_id: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "analytics_processing"
    
    def to_payload(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics,
            "dimensions": self.dimensions
        }
    
    def get_metric(self, key: str, default: float = 0.0) -> float:
        """Helper method to safely get a metric value."""
        return self.metrics.get(key, default)
    
    def has_dimension(self, key: str) -> bool:
        """Helper method to check if a dimension exists."""
        return key in self.dimensions
    
    @classmethod
    def from_event(cls, event):
        return cls(
            uuid=event.uuid,
            timestamp=event.timestamp,
            correlation_id=event.correlation_id,
            metrics=event.payload.get("metrics", {}),
            dimensions=event.payload.get("dimensions", {})
        )


# Example Usage
async def example_usage():
    """Example of how to use custom events."""
    
    # Create event bus and channel
    bus = EventBus()
    bus.create_ack_channel("user_analysis", timeout_seconds=180)
    
    # Create custom event instances
    user_event = UserBehaviorEvent(
        user_id="user_123",
        behavior_data={"page_views": 10, "clicks": 5},
        session_data={"duration": 3600, "time_on_site": 1800},
        correlation_id="corr_123"
    )
    
    # Publish custom event (automatically converts to Event internally)
    await bus.publish("user_analysis", user_event)
    
    # Create recommendation event
    rec_event = RecommendationEvent(
        user_id="user_456",
        context={"page": "homepage", "device": "mobile"},
        user_history=["item_1", "item_2", "item_3"]
    )
    
    await bus.publish("recommendations", rec_event)
    
    # Access typed properties
    print(f"User ID: {user_event.user_id}")
    print(f"Event Type: {user_event.event_type}")
    print(f"UUID: {user_event.uuid}")
    
    # Pydantic models have built-in serialization
    print(f"Event as dict: {user_event.model_dump()}")
    print(f"Event as JSON: {user_event.model_dump_json()}")
    
    # Convert back from standard Event if needed
    channel = bus.get_channel("user_analysis")
    # When receiving events, you can convert them back:
    # received_event = UserBehaviorEvent.from_event(standard_event)


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
