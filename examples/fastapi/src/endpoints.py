from fastapi import APIRouter, HTTPException, Query, Body
import uuid
import time
from rx_events import event_bus, Event, EventStatus, EventAck

from src.schema import EventResponse, EventRequest, EventStatusResponse, AcknowledgeRequest

router = APIRouter()


@router.post("/api/user/behavior", response_model=EventResponse)
async def analyze_user_behavior(request: EventRequest):
    """Trigger user behavior analysis"""
    event = Event(
        uuid=str(uuid.uuid4()),
        event_type="user_behavior_analysis",
        payload=request.payload,
        timestamp=time.time(),
        correlation_id=request.correlation_id
    )

    try:
        await event_bus.publish("user_analysis", event)
        return EventResponse(
            event_uuid=event.uuid,
            status="accepted",
            message="Event published, processing will be tracked"
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/api/events/{event_uuid}/status", response_model=EventStatusResponse)
async def get_event_status(event_uuid: str):
    """Get status of a specific event"""

    # Check all channels for this event
    for channel_name, channel in event_bus._channels.items():
        status = await channel.get_event_status(event_uuid)
        if status:
            return EventStatusResponse(**status)

    raise HTTPException(status_code=404, detail="Event not found")


@router.post("/api/events/acknowledge")
async def acknowledge_event(
        event_uuid: str = Query(..., description="UUID of the event being acknowledged"),
        channel_name: str = Query(..., description="Name of the channel"),
        status: str = Query(..., description="Status of the event processing"),
        body: AcknowledgeRequest = Body(...)
):
    """DS code calls this to acknowledge event processing"""

    try:
        event_status = EventStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    ack = EventAck(
        event_uuid=event_uuid,
        status=event_status,
        result=body.result,
        error=body.error,
        processing_time=body.processing_time
    )

    try:
        success = await event_bus.acknowledge(channel_name, ack)
        if success:
            return {"message": "Acknowledgment received"}
        else:
            raise HTTPException(status_code=404, detail="Event not found for acknowledgment")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/channels/stats")
async def get_channel_stats():
    """Get statistics for all channels"""
    return {
        channel_name: channel.get_stats()
        for channel_name, channel in event_bus._channels.items()
    }