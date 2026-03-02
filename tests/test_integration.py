"""Integration tests for rx-events package."""
import pytest
import asyncio
from rx_events import EventBus, Event, EventStatus, EventAck, BaseEvent
from pydantic import Field
from typing import Dict, Any


class TestIntegration:
    """Integration tests for the complete event system."""
    
    @pytest.mark.asyncio
    async def test_complete_event_workflow(self):
        """Test complete workflow: publish -> subscribe -> process -> acknowledge."""
        bus = EventBus()
        bus.create_channel("test_channel", timeout_seconds=300)
        
        events_received = []
        acks_received = []
        
        # Subscribe to events
        channel = bus.get_channel("test_channel")
        channel.get_event_stream().subscribe(
            on_next=lambda e: events_received.append(e)
        )
        
        channel.get_ack_stream().subscribe(
            on_next=lambda a: acks_received.append(a)
        )
        
        # Publish event
        event = Event.create(
            event_type="test_event",
            payload={"data": "test"}
        )
        await bus.publish("test_channel", event)
        
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(events_received) == 1
        assert events_received[0].uuid == event.uuid
        
        # Acknowledge processing
        processing_ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.PROCESSING
        )
        await bus.acknowledge("test_channel", processing_ack)
        
        await asyncio.sleep(0.1)
        
        # Verify processing ack was received
        assert len(acks_received) >= 1
        assert acks_received[0].status == EventStatus.PROCESSING
        
        # Acknowledge completion
        completed_ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.COMPLETED,
            result={"success": True},
            processing_time=1.5
        )
        await bus.acknowledge("test_channel", completed_ack)
        
        await asyncio.sleep(0.1)
        
        # Verify completion ack was received
        assert len(acks_received) >= 2
        assert any(a.status == EventStatus.COMPLETED for a in acks_received)
        
        # Verify final status
        status = await channel.get_event_status(event.uuid)
        assert status["status"] == "completed"
        assert status["result"] == {"success": True}
    
    @pytest.mark.asyncio
    async def test_custom_event_workflow(self):
        """Test workflow with custom event types."""
        class CustomEvent(BaseEvent):
            user_id: str
            action: str
            
            @property
            def event_type(self) -> str:
                return "custom_event"
            
            def to_payload(self) -> Dict[str, Any]:
                return {"user_id": self.user_id, "action": self.action}
        
        bus = EventBus()
        bus.create_channel("test_channel")
        
        custom_event = CustomEvent(user_id="123", action="login")
        
        # Publish custom event (should be converted to Event)
        await bus.publish("test_channel", custom_event)
        
        # Verify it was published
        channel = bus.get_channel("test_channel")
        status = await channel.get_event_status(custom_event.uuid)
        assert status is not None
        assert status["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_multiple_events_processing(self):
        """Test processing multiple events."""
        bus = EventBus()
        bus.create_channel("test_channel")
        
        events = [
            Event.create(event_type="event1", payload={"id": i})
            for i in range(5)
        ]
        
        # Publish all events
        for event in events:
            await bus.publish("test_channel", event)
        
        # Verify all are tracked
        channel = bus.get_channel("test_channel")
        stats = channel.get_stats()
        assert stats["active_events"] == 5
        assert stats["pending_acks"] == 5
        
        # Acknowledge all
        for event in events:
            ack = EventAck.create(
                event_uuid=event.uuid,
                status=EventStatus.COMPLETED
            )
            await bus.acknowledge("test_channel", ack)
        
        # Verify all are completed
        stats = channel.get_stats()
        assert stats["active_events"] == 0
        assert stats["pending_acks"] == 0
        assert stats["completed_events"] == 5
