# Event-Driven API with Acknowledgments

An event-driven system built with FastAPI that enables asynchronous processing of events with acknowledgment tracking. The system uses an event bus pattern where API endpoints publish events, and data science processors consume them, sending acknowledgments back through the event bus.

## Architecture

The system consists of three main components:

1. **Event Bus** - Manages event channels and acknowledgment tracking
2. **API Endpoints** - Publish events and track their status
3. **Data Science Processors** - Subscribe to events, process them, and send acknowledgments

### Event Flow

```
API Endpoint → Event Bus → DS Processor → Event Bus → Status Tracking
     ↓            ↓            ↓              ↓              ↓
  Publish    Channel      Process       Acknowledge    Query Status
```

## Features

- ✅ Event-driven architecture with reactive streams (RxPY)
- ✅ Acknowledgment tracking for event processing
- ✅ Multiple event channels with configurable timeouts
- ✅ Real-time event status monitoring
- ✅ Automatic timeout handling
- ✅ Channel statistics and monitoring
- ✅ **Extensible event classes** - Create custom event types with type safety

## Setup

### Prerequisites

- Python 3.12+
- `uv` package manager (or pip)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
# Using uv
uv sync

# Or using pip
pip install -r requirements.txt
```

### Running the Application

```bash
# Using uvicorn directly
python -m src.main

# Or using uvicorn command
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI) is available at `http://localhost:8000/docs`

## API Endpoints

### 1. User Behavior Analysis

**POST** `/api/user/behavior`

Triggers user behavior analysis processing.

**Request Body:**
```json
{
  "event_type": "user_behavior_analysis",
  "payload": {
    "user_id": "user_12345",
    "behavior_data": {
      "page_views": 15,
      "clicks": 8
    },
    "session_data": {
      "duration": 4200,
      "time_on_site": 2100
    }
  },
  "correlation_id": "optional-correlation-id"
}
```

**Response:**
```json
{
  "event_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Event published, processing will be tracked"
}
```

**Payload Fields:**
- `user_id` (required): User identifier
- `behavior_data` (optional): Object containing:
  - `page_views`: Number of pages viewed
  - `clicks`: Number of clicks
- `session_data` (optional): Object containing:
  - `duration`: Session duration in seconds
  - `time_on_site`: Time on site in seconds

### 2. Get Event Status

**GET** `/api/events/{event_uuid}/status`

Retrieves the current status and processing details of an event.

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "published_at": 1234567890.123,
  "processing_started_at": 1234567891.456,
  "completed_at": 1234567895.789,
  "age_seconds": 5.666,
  "processing_time": 4.333,
  "result": {
    "user_id": "user_12345",
    "risk_score": 0.75,
    "behavior_pattern": "suspicious",
    "anomaly_score": 0.85,
    "predictions": {
      "churn_probability": 0.3,
      "lifetime_value_estimate": 2500.0,
      "next_best_action": "offer_discount"
    }
  },
  "error": null
}
```

**Status Values:**
- `pending`: Event published, waiting for processing
- `processing`: Event is being processed
- `completed`: Processing completed successfully
- `failed`: Processing failed
- `timeout`: Event timed out

### 3. Channel Statistics

**GET** `/api/channels/stats`

Returns statistics for all event channels.

**Response:**
```json
{
  "user_analysis": {
    "name": "user_analysis",
    "allow_duplicates": false,
    "timeout_seconds": 180,
    "active_events": 2,
    "pending_acks": 1,
    "completed_events": 15,
    "active_event_details": [
      {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "event_type": "user_behavior_analysis",
        "status": "processing",
        "age_seconds": 45.2
      }
    ]
  },
  "recommendations": { ... },
  "analytics": { ... }
}
```

## Event Channels

The system uses three event channels, each configured for different use cases:

### 1. `user_analysis`
- **Purpose**: User behavior analysis and ML predictions
- **Timeout**: 180 seconds (3 minutes)
- **Duplicates**: Not allowed
- **Event Type**: `user_behavior_analysis`

### 2. `recommendations`
- **Purpose**: Recommendation engine processing
- **Timeout**: 300 seconds (5 minutes)
- **Duplicates**: Not allowed
- **Event Type**: `recommendation_request`

### 3. `analytics`
- **Purpose**: Quick analytics processing
- **Timeout**: 60 seconds (1 minute)
- **Duplicates**: Allowed
- **Event Type**: `analytics_processing`

## Event Processing

### How It Works

1. **Event Publication**: API endpoint publishes an event to a channel
2. **Event Subscription**: Data science processors subscribe to channel event streams
3. **Processing**: Processors receive events and perform analysis
4. **Acknowledgment**: Processors send acknowledgments back through the event bus:
   - `PROCESSING`: When processing starts
   - `COMPLETED`: When processing succeeds (with result)
   - `FAILED`: When processing fails (with error)
5. **Status Tracking**: Event status is tracked and can be queried via API

### Data Science Processors

The processors automatically:
- Subscribe to their respective event channels
- Process events asynchronously
- Send acknowledgments at each stage
- Handle errors gracefully

**User Behavior Processor** processes:
- Risk scoring
- Behavior pattern detection
- Anomaly detection
- Churn prediction
- Lifetime value estimation
- Next best action recommendations

## Example Usage

### Using cURL

```bash
# 1. Publish a user behavior analysis event
curl -X POST "http://localhost:8000/api/user/behavior" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user_behavior_analysis",
    "payload": {
      "user_id": "user_12345",
      "behavior_data": {
        "page_views": 15,
        "clicks": 8
      },
      "session_data": {
        "duration": 4200,
        "time_on_site": 2100
      }
    }
  }'

# Response: {"event_uuid": "550e8400-...", "status": "accepted", ...}

# 2. Check event status
curl "http://localhost:8000/api/events/550e8400-e29b-41d4-a716-446655440000/status"

# 3. Get channel statistics
curl "http://localhost:8000/api/channels/stats"
```

### Using Python

```python
import requests

# Publish event
response = requests.post(
    "http://localhost:8000/api/user/behavior",
    json={
        "event_type": "user_behavior_analysis",
        "payload": {
            "user_id": "user_12345",
            "behavior_data": {
                "page_views": 15,
                "clicks": 8
            },
            "session_data": {
                "duration": 4200,
                "time_on_site": 2100
            }
        }
    }
)

event_uuid = response.json()["event_uuid"]

# Poll for status
import time
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/events/{event_uuid}/status"
    )
    status_data = status_response.json()
    
    if status_data["status"] in ["completed", "failed", "timeout"]:
        print(f"Processing finished: {status_data['status']}")
        if status_data.get("result"):
            print(f"Result: {status_data['result']}")
        break
    
    time.sleep(1)
```

## Project Structure

```
event-driven/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── endpoints.py            # API endpoints
│   ├── data_science/
│   │   └── processors.py       # Event processors
│   └── events/
│       ├── event_bus.py        # Event bus implementation
│       ├── ack_channel.py      # Acknowledgment channel
│       └── events.py           # Event and EventAck models
├── pyproject.toml              # Project dependencies
└── README.md                   # This file
```

## Dependencies

- **FastAPI**: Web framework
- **ReactiveX (RxPY)**: Reactive programming for event streams
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

## Extending Events

The events package is designed to be extensible. You can create custom event classes with type safety and validation.

### Quick Example

```python
import time
import uuid as uuid_lib
from typing import Dict, Any, Optional
from pydantic import Field
from rx_events import BaseEvent, EventBus

class MyCustomEvent(BaseEvent):
    """Your custom event with typed fields using Pydantic."""
    
    # Your custom fields
    user_id: str
    data: Dict[str, Any]
    
    # Required base fields
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    correlation_id: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "my_custom_event"
    
    def to_payload(self) -> Dict[str, Any]:
        return {"user_id": self.user_id, "data": self.data}
    
    @classmethod
    def from_event(cls, event):
        return cls(
            uuid=event.uuid,
            timestamp=event.timestamp,
            correlation_id=event.correlation_id,
            user_id=event.payload["user_id"],
            data=event.payload["data"]
        )

# Use it
bus = EventBus()
bus.create_channel("my_channel")
event = MyCustomEvent(user_id="123", data={"key": "value"})
# Pydantic provides built-in serialization
print(event.model_dump())  # Convert to dict
await bus.publish("my_channel", event)
```

For detailed documentation, see [docs/EXTENDING_EVENTS.md](docs/EXTENDING_EVENTS.md).

## Development

### Adding New Event Types

1. Create a new channel in `src/main.py`:
```python
event_bus.create_channel(
    "new_channel",
    allow_duplicates=False,
    timeout_seconds=120
)
```

2. Add processor subscription in `src/data_science/processors.py`:
```python
new_channel = event_bus.get_channel("new_channel")
new_channel.get_event_stream().pipe(
    ops.filter(lambda event: event.event_type == "new_event_type"),
    ops.flat_map(lambda event: self._process_with_acks(
        event, "new_channel", self._process_new_event
    ))
).subscribe(...)
```

3. Add API endpoint in `src/endpoints.py`:
```python
@router.post("/api/new-endpoint")
async def new_endpoint(request: EventRequest):
    event = Event(
        uuid=str(uuid.uuid4()),
        event_type="new_event_type",
        payload=request.payload,
        timestamp=time.time(),
        correlation_id=request.correlation_id
    )
    await event_bus.publish("new_channel", event)
    return EventResponse(...)
```

## License

**MIT**
