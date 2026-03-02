from typing import Dict, Any, Optional

from pydantic import BaseModel


class EventRequest(BaseModel):
    event_type: str
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None


class EventResponse(BaseModel):
    event_uuid: str
    status: str
    message: str


class EventStatusResponse(BaseModel):
    uuid: str
    status: str
    published_at: Optional[float] = None
    processing_started_at: Optional[float] = None
    completed_at: Optional[float] = None
    age_seconds: Optional[float] = None
    processing_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None