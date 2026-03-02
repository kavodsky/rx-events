"""Tests for events module."""
import pytest
import time
import uuid as uuid_lib
from typing import Dict, Any, Optional
from pydantic import Field, ValidationError

from rx_events import (
    EventStatus,
    BaseEvent,
    Event,
    BaseEventAck,
    EventAck,
)


class TestEventStatus:
    """Tests for EventStatus enum."""
    
    def test_event_status_values(self):
        """Test EventStatus enum values."""
        assert EventStatus.PENDING.value == "pending"
        assert EventStatus.PROCESSING.value == "processing"
        assert EventStatus.COMPLETED.value == "completed"
        assert EventStatus.FAILED.value == "failed"
        assert EventStatus.TIMEOUT.value == "timeout"


class TestEvent:
    """Tests for Event class."""
    
    def test_create_event(self):
        """Test creating an event."""
        event = Event(
            uuid="test-uuid",
            event_type="test_event",
            payload={"key": "value"},
            timestamp=time.time()
        )
        
        assert event.uuid == "test-uuid"
        assert event.event_type == "test_event"
        assert event.payload == {"key": "value"}
        assert event.correlation_id is None
    
    def test_create_event_factory(self):
        """Test Event.create factory method."""
        event = Event.create(
            event_type="test_event",
            payload={"key": "value"},
            correlation_id="corr-123"
        )
        
        assert event.event_type == "test_event"
        assert event.payload == {"key": "value"}
        assert event.correlation_id == "corr-123"
        assert event.uuid is not None
        assert isinstance(event.timestamp, float)
    
    def test_create_event_with_uuid(self):
        """Test Event.create with custom UUID."""
        custom_uuid = str(uuid_lib.uuid4())
        event = Event.create(
            event_type="test_event",
            payload={},
            uuid=custom_uuid
        )
        
        assert event.uuid == custom_uuid


class TestBaseEvent:
    """Tests for BaseEvent base class."""
    
    def test_base_event_abstract(self):
        """Test that BaseEvent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseEvent()
    
    def test_custom_event_implementation(self):
        """Test creating a custom event."""
        class CustomEvent(BaseEvent):
            user_id: str
            data: Dict[str, Any]
            
            @property
            def event_type(self) -> str:
                return "custom_event"
            
            def to_payload(self) -> Dict[str, Any]:
                return {"user_id": self.user_id, "data": self.data}
        
        event = CustomEvent(user_id="123", data={"key": "value"})
        assert event.user_id == "123"
        assert event.data == {"key": "value"}
        assert event.event_type == "custom_event"
        assert event.uuid is not None
        assert isinstance(event.timestamp, float)
    
    def test_custom_event_to_event(self):
        """Test converting custom event to standard Event."""
        class CustomEvent(BaseEvent):
            user_id: str
            
            @property
            def event_type(self) -> str:
                return "custom_event"
            
            def to_payload(self) -> Dict[str, Any]:
                return {"user_id": self.user_id}
        
        custom = CustomEvent(user_id="123")
        standard = custom.to_event()
        
        assert isinstance(standard, Event)
        assert standard.event_type == "custom_event"
        assert standard.payload == {"user_id": "123"}
        assert standard.uuid == custom.uuid
    
    def test_custom_event_from_event(self):
        """Test creating custom event from standard Event."""
        class CustomEvent(BaseEvent):
            user_id: str
            
            @property
            def event_type(self) -> str:
                return "custom_event"
            
            def to_payload(self) -> Dict[str, Any]:
                return {"user_id": self.user_id}
            
            @classmethod
            def from_event(cls, event: Event):
                return cls(
                    uuid=event.uuid,
                    timestamp=event.timestamp,
                    correlation_id=event.correlation_id,
                    user_id=event.payload["user_id"]
                )
        
        standard = Event.create(
            event_type="custom_event",
            payload={"user_id": "123"}
        )
        
        custom = CustomEvent.from_event(standard)
        assert custom.user_id == "123"
        assert custom.uuid == standard.uuid


class TestEventAck:
    """Tests for EventAck class."""
    
    def test_create_event_ack(self):
        """Test creating an EventAck."""
        ack = EventAck(
            event_uuid="test-uuid",
            status=EventStatus.COMPLETED,
            result={"processed": True}
        )
        
        assert ack.event_uuid == "test-uuid"
        assert ack.status == EventStatus.COMPLETED
        assert ack.result == {"processed": True}
        assert ack.error is None
        assert isinstance(ack.timestamp, float)
    
    def test_create_event_ack_factory(self):
        """Test EventAck.create factory method."""
        ack = EventAck.create(
            event_uuid="test-uuid",
            status=EventStatus.FAILED,
            error="Something went wrong",
            processing_time=1.5
        )
        
        assert ack.event_uuid == "test-uuid"
        assert ack.status == EventStatus.FAILED
        assert ack.error == "Something went wrong"
        assert ack.processing_time == 1.5
        assert isinstance(ack.timestamp, float)
    
    def test_event_ack_all_statuses(self):
        """Test EventAck with all status types."""
        for status in EventStatus:
            ack = EventAck.create(
                event_uuid="test-uuid",
                status=status
            )
            assert ack.status == status


class TestBaseEventAck:
    """Tests for BaseEventAck base class."""
    
    def test_base_event_ack_abstract(self):
        """Test that BaseEventAck cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseEventAck(
                event_uuid="test",
                status=EventStatus.PENDING
            )
    
    def test_custom_ack_implementation(self):
        """Test creating a custom acknowledgment."""
        class CustomAck(BaseEventAck):
            user_id: str
            score: float
            
            def get_ack_type(self) -> str:
                return "custom_ack"
            
            def to_event_ack(self) -> EventAck:
                return EventAck(
                    event_uuid=self.event_uuid,
                    status=self.status,
                    result={
                        "user_id": self.user_id,
                        "score": self.score,
                        **(self.result or {})
                    },
                    error=self.error,
                    processing_time=self.processing_time,
                    timestamp=self.timestamp
                )
        
        ack = CustomAck(
            event_uuid="test-uuid",
            status=EventStatus.COMPLETED,
            user_id="123",
            score=0.95
        )
        
        assert ack.user_id == "123"
        assert ack.score == 0.95
        assert ack.status == EventStatus.COMPLETED
        
        standard = ack.to_event_ack()
        assert isinstance(standard, EventAck)
        assert standard.result["user_id"] == "123"
        assert standard.result["score"] == 0.95


class TestEventValidation:
    """Tests for event validation."""
    
    def test_event_pydantic_validation(self):
        """Test that Pydantic validation works on events."""
        # Valid event
        event = Event.create(
            event_type="test",
            payload={"key": "value"}
        )
        assert event is not None
        
        # Invalid - missing required fields
        with pytest.raises(ValidationError):
            Event(uuid="test")  # Missing required fields
    
    def test_custom_event_validation(self):
        """Test validation on custom events."""
        from pydantic import field_validator
        
        class ValidatedEvent(BaseEvent):
            email: str
            age: int
            
            @field_validator('email')
            @classmethod
            def validate_email(cls, v: str) -> str:
                if '@' not in v:
                    raise ValueError("Invalid email")
                return v
            
            @field_validator('age')
            @classmethod
            def validate_age(cls, v: int) -> int:
                if v < 0:
                    raise ValueError("Age must be positive")
                return v
            
            @property
            def event_type(self) -> str:
                return "validated_event"
            
            def to_payload(self) -> Dict[str, Any]:
                return {"email": self.email, "age": self.age}
        
        # Valid
        event = ValidatedEvent(email="test@example.com", age=25)
        assert event.email == "test@example.com"
        
        # Invalid email
        with pytest.raises(ValidationError):
            ValidatedEvent(email="invalid", age=25)
        
        # Invalid age
        with pytest.raises(ValidationError):
            ValidatedEvent(email="test@example.com", age=-1)
