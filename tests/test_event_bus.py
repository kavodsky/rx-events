"""Tests for event_bus module."""
import pytest
import asyncio
from rx_events import EventBus, Event, EventStatus, BaseEvent, EventAck
from pydantic import Field


class TestEventBus:
    """Tests for EventBus class."""
    
    def test_create_event_bus(self):
        """Test creating an EventBus."""
        bus = EventBus()
        assert bus is not None
        assert len(bus._channels) == 0
    
    def test_create_channel(self):
        """Test creating a channel."""
        bus = EventBus()
        channel = bus.create_channel("test_channel", timeout_seconds=60)
        
        assert channel.name == "test_channel"
        assert channel.timeout_seconds == 60
        assert "test_channel" in bus._channels
    
    def test_create_duplicate_channel(self):
        """Test that creating duplicate channel raises error."""
        bus = EventBus()
        bus.create_channel("test_channel")
        
        with pytest.raises(ValueError, match="already exists"):
            bus.create_channel("test_channel")
    
    def test_get_channel(self):
        """Test getting an existing channel."""
        bus = EventBus()
        created = bus.create_channel("test_channel")
        retrieved = bus.get_channel("test_channel")
        
        assert retrieved is created
    
    def test_get_nonexistent_channel(self):
        """Test getting a non-existent channel raises error."""
        bus = EventBus()
        
        with pytest.raises(ValueError, match="not found"):
            bus.get_channel("nonexistent")
    
    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test publishing an event."""
        bus = EventBus()
        bus.create_channel("test_channel")
        
        event = Event.create(
            event_type="test_event",
            payload={"key": "value"}
        )
        
        result = await bus.publish("test_channel", event)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_publish_base_event(self):
        """Test publishing a BaseEvent (custom event)."""
        class CustomEvent(BaseEvent):
            data: str
            
            @property
            def event_type(self) -> str:
                return "custom_event"
            
            def to_payload(self) -> dict:
                return {"data": self.data}
        
        bus = EventBus()
        bus.create_channel("test_channel")
        
        custom_event = CustomEvent(data="test")
        result = await bus.publish("test_channel", custom_event)
        
        assert result is True
        
        # Verify it was converted to Event
        channel = bus.get_channel("test_channel")
        # The event should be in the channel's active events
        assert custom_event.uuid in channel._active_events
    
    @pytest.mark.asyncio
    async def test_acknowledge_event(self):
        """Test acknowledging an event."""
        bus = EventBus()
        bus.create_channel("test_channel")
        
        event = Event.create(
            event_type="test_event",
            payload={}
        )
        
        await bus.publish("test_channel", event)
        
        ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.COMPLETED,
            result={"processed": True}
        )
        
        result = await bus.acknowledge("test_channel", ack)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_acknowledge_nonexistent_event(self):
        """Test acknowledging a non-existent event."""
        bus = EventBus()
        bus.create_channel("test_channel")
        
        ack = EventAck.create(
            event_uuid="nonexistent-uuid",
            status=EventStatus.COMPLETED
        )
        
        result = await bus.acknowledge("test_channel", ack)
        assert result is False


class TestEventBusIntegration:
    """Integration tests for EventBus."""
    
    @pytest.mark.asyncio
    async def test_full_event_lifecycle(self):
        """Test complete event lifecycle: publish -> process -> acknowledge."""
        bus = EventBus()
        bus.create_channel("test_channel", timeout_seconds=300)
        
        # Publish event
        event = Event.create(
            event_type="test_event",
            payload={"data": "test"}
        )
        await bus.publish("test_channel", event)
        
        # Get channel and verify event is tracked
        channel = bus.get_channel("test_channel")
        status = await channel.get_event_status(event.uuid)
        assert status is not None
        assert status["status"] == "pending"
        
        # Acknowledge processing
        processing_ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.PROCESSING
        )
        await bus.acknowledge("test_channel", processing_ack)
        
        status = await channel.get_event_status(event.uuid)
        assert status["status"] == "processing"
        
        # Acknowledge completion
        completed_ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.COMPLETED,
            result={"success": True},
            processing_time=1.5
        )
        await bus.acknowledge("test_channel", completed_ack)
        
        status = await channel.get_event_status(event.uuid)
        assert status["status"] == "completed"
        assert status["result"] == {"success": True}
        assert status["processing_time"] == 1.5
    
    @pytest.mark.asyncio
    async def test_multiple_channels(self):
        """Test using multiple channels."""
        bus = EventBus()
        bus.create_channel("channel1")
        bus.create_channel("channel2")
        
        event1 = Event.create(event_type="event1", payload={})
        event2 = Event.create(event_type="event2", payload={})
        
        await bus.publish("channel1", event1)
        await bus.publish("channel2", event2)
        
        channel1 = bus.get_channel("channel1")
        channel2 = bus.get_channel("channel2")
        
        assert event1.uuid in channel1._active_events
        assert event2.uuid in channel2._active_events
        assert event1.uuid not in channel2._active_events
        assert event2.uuid not in channel1._active_events
