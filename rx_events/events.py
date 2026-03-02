import time
import uuid as uuid_lib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class BaseEvent(BaseModel, ABC):
    """
    Base class for all events. Extend this class to create custom event types.
    
    Subclasses should inherit from BaseModel and implement event_type and to_payload.
    
    Example:
        class UserBehaviorEvent(BaseEvent):
            user_id: str
            behavior_data: Dict[str, Any]
            uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
            timestamp: float = Field(default_factory=time.time)
            correlation_id: Optional[str] = None
            
            @property
            def event_type(self) -> str:
                return "user_behavior_analysis"
            
            def to_payload(self) -> Dict[str, Any]:
                return {
                    "user_id": self.user_id,
                    "behavior_data": self.behavior_data
                }
    """
    
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    correlation_id: Optional[str] = None
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type identifier. Must be implemented by subclasses."""
        ...
    
    @abstractmethod
    def to_payload(self) -> Dict[str, Any]:
        """Convert event to payload dictionary. Must be implemented by subclasses."""
        ...
    
    def to_event(self) -> 'Event':
        """Convert to the standard Event format for compatibility."""
        return Event(
            uuid=self.uuid,
            event_type=self.event_type,
            payload=self.to_payload(),
            timestamp=self.timestamp,
            correlation_id=self.correlation_id
        )
    
    @classmethod
    def from_event(cls, event: 'Event') -> 'BaseEvent':
        """Create an instance from a standard Event. Override in subclasses for custom parsing."""
        # This is a fallback - subclasses should override this
        raise NotImplementedError("Subclasses must implement from_event")
    
    model_config = {"arbitrary_types_allowed": True}


class Event(BaseModel):
    """
    Standard event class for general-purpose event publishing.
    For custom event types, extend BaseEvent instead.
    """
    uuid: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: float
    correlation_id: Optional[str] = None
    
    @classmethod
    def create(cls, event_type: str, payload: Dict[str, Any], 
               correlation_id: Optional[str] = None, uuid: Optional[str] = None) -> 'Event':
        """Factory method to create an event with auto-generated UUID and timestamp."""
        return cls(
            uuid=uuid or str(uuid_lib.uuid4()),
            event_type=event_type,
            payload=payload,
            timestamp=time.time(),
            correlation_id=correlation_id
        )
    
    def to_base_event(self, event_class: type[BaseEvent]) -> BaseEvent:
        """Convert to a BaseEvent subclass if possible."""
        return event_class.from_event(self)
    
    model_config = {"arbitrary_types_allowed": True}


class BaseEventAck(BaseModel, ABC):
    """
    Base class for event acknowledgments. Extend this to create custom acknowledgment types.
    """
    event_uuid: str
    status: EventStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    timestamp: float = Field(default_factory=time.time)
    
    @abstractmethod
    def get_ack_type(self) -> str:
        """Return the acknowledgment type identifier. Must be implemented by subclasses."""
        ...
    
    def to_event_ack(self) -> 'EventAck':
        """Convert to standard EventAck format."""
        return EventAck(
            event_uuid=self.event_uuid,
            status=self.status,
            result=self.result,
            error=self.error,
            processing_time=self.processing_time,
            timestamp=self.timestamp
        )
    
    model_config = {"arbitrary_types_allowed": True}


class EventAck(BaseModel):
    """
    Standard event acknowledgment class.
    For custom acknowledgment types, extend BaseEventAck instead.
    """
    event_uuid: str
    status: EventStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    timestamp: float = Field(default_factory=time.time)
    
    @classmethod
    def create(cls, event_uuid: str, status: EventStatus,
               result: Optional[Dict[str, Any]] = None,
               error: Optional[str] = None,
               processing_time: Optional[float] = None) -> 'EventAck':
        """Factory method to create an acknowledgment."""
        return cls(
            event_uuid=event_uuid,
            status=status,
            result=result,
            error=error,
            processing_time=processing_time
        )
    
    model_config = {"arbitrary_types_allowed": True}
