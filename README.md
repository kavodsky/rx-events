# Rx-Events

A flexible event-driven system with acknowledgment tracking using Pydantic and ReactiveX.

## Features

- ✅ **Extensible Event Classes** - Create custom event types with Pydantic BaseModel
- ✅ **Acknowledgment Tracking** - Built-in support for event processing acknowledgments
- ✅ **Reactive Streams** - Powered by ReactiveX (RxPY) for reactive event processing
- ✅ **Type Safety** - Full type hints and Pydantic validation
- ✅ **Event Bus Pattern** - Centralized event management with channels
- ✅ **Timeout Handling** - Automatic timeout detection and handling

## Installation

```bash
# Install from local directory (development)
pip install -e /path/to/rx-events

# Or install from source
cd /path/to/rx-events
pip install .
```

## Quick Start

### Basic Usage

```python
from rx_events import EventBus, BaseEvent, EventStatus, EventAck
from pydantic import Field
import time
import uuid as uuid_lib
from typing import Dict, Any, Optional

# Create a custom event
class MyEvent(BaseEvent):
    user_id: str
    data: Dict[str, Any]
    
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    correlation_id: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "my_event"
    
    def to_payload(self) -> Dict[str, Any]:
        return {"user_id": self.user_id, "data": self.data}

# Create event bus and channel
bus = EventBus()
bus.create_channel("my_channel", timeout_seconds=180)

# Publish event
event = MyEvent(user_id="123", data={"key": "value"})
await bus.publish("my_channel", event)

# Subscribe to events
channel = bus.get_channel("my_channel")
channel.get_event_stream().subscribe(
    on_next=lambda event: print(f"Received: {event.event_type}"),
    on_error=lambda error: print(f"Error: {error}")
)

# Send acknowledgment
ack = EventAck.create(
    event_uuid=event.uuid,
    status=EventStatus.COMPLETED,
    result={"processed": True}
)
await bus.acknowledge("my_channel", ack)
```

### Custom Event with Validation

```python
from pydantic import Field, field_validator

class UserEvent(BaseEvent):
    user_id: str
    email: str
    
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    correlation_id: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError("Invalid email")
        return v
    
    @property
    def event_type(self) -> str:
        return "user_event"
    
    def to_payload(self) -> Dict[str, Any]:
        return {"user_id": self.user_id, "email": self.email}
```

## Testing

Run tests with pytest:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=rx_events --cov-report=html
```

## API Reference

### Core Classes

- **`BaseEvent`** - Abstract base class for custom events
- **`Event`** - Standard event class for general-purpose events
- **`BaseEventAck`** - Abstract base class for custom acknowledgments
- **`EventAck`** - Standard acknowledgment class
- **`EventStatus`** - Enum for event statuses (PENDING, PROCESSING, COMPLETED, FAILED, TIMEOUT)
- **`EventBus`** - Central event bus for managing channels
- **`AckChannel`** - Channel for event publishing and acknowledgment tracking

### EventBus Methods

- `create_channel(name, allow_duplicates=False, timeout_seconds=300)` - Create a new channel
- `get_channel(name)` - Get an existing channel
- `publish(channel_name, event)` - Publish an event to a channel
- `acknowledge(channel_name, ack)` - Send an acknowledgment

### AckChannel Methods

- `publish(event)` - Publish an event
- `acknowledge(ack)` - Receive an acknowledgment
- `get_event_stream()` - Get ReactiveX Observable for events
- `get_ack_stream()` - Get ReactiveX Observable for acknowledgments
- `get_stats()` - Get channel statistics
- `get_event_status(event_uuid)` - Get status of a specific event

## Examples

See the `tests/` directory for comprehensive examples.

## License

MIT
