"""Tests for channel module."""
import pytest
import asyncio
from rx_events import Channel, Event, BaseEvent, EventBus
from typing import Dict, Any


class TestChannel:
    """Tests for Channel class."""
    
    def test_create_channel(self):
        """Test creating a Channel."""
        channel = Channel("test_channel")
        
        assert channel.name == "test_channel"
    
    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test publishing an event to channel."""
        channel = Channel("test_channel")
        event = Event.create(event_type="test", payload={})
        
        result = await channel.publish(event)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_publish_base_event(self):
        """Test publishing a BaseEvent (custom event) to channel."""
        class CustomEvent(BaseEvent):
            data: str
            
            @property
            def event_type(self) -> str:
                return "custom_event"
            
            def to_payload(self) -> Dict[str, Any]:
                return {"data": self.data}
        
        channel = Channel("test_channel")
        custom_event = CustomEvent(data="test")
        
        result = await channel.publish(custom_event)
        assert result is True
    
    def test_get_event_stream(self):
        """Test getting event stream."""
        channel = Channel("test_channel")
        stream = channel.get_event_stream()
        
        assert stream is not None
    
    @pytest.mark.asyncio
    async def test_event_stream_subscription(self):
        """Test subscribing to event stream."""
        channel = Channel("test_channel")
        events_received = []
        
        channel.get_event_stream().subscribe(
            on_next=lambda e: events_received.append(e)
        )
        
        event1 = Event.create(event_type="test1", payload={})
        event2 = Event.create(event_type="test2", payload={})
        
        await channel.publish(event1)
        await channel.publish(event2)
        
        await asyncio.sleep(0.1)
        
        assert len(events_received) == 2
        assert events_received[0].uuid == event1.uuid
        assert events_received[1].uuid == event2.uuid
    
    def test_get_stats(self):
        """Test getting channel statistics."""
        channel = Channel("test_channel")
        
        stats = channel.get_stats()
        assert stats["name"] == "test_channel"
        assert stats["type"] == "simple"


class TestChannelWithEventBus:
    """Tests for Channel when created through EventBus."""
    
    def test_create_channel_via_event_bus(self):
        """Test creating a channel through EventBus."""
        bus = EventBus()
        channel = bus.create_channel("test_channel")
        
        assert channel.name == "test_channel"
        assert isinstance(channel, Channel)
        assert "test_channel" in bus._channels
    
    def test_create_duplicate_channel(self):
        """Test that creating duplicate channel raises error."""
        bus = EventBus()
        bus.create_channel("test_channel")
        
        with pytest.raises(ValueError, match="already exists"):
            bus.create_channel("test_channel")
    
    def test_get_channel(self):
        """Test getting a simple channel."""
        bus = EventBus()
        created = bus.create_channel("test_channel")
        retrieved = bus.get_channel("test_channel")
        
        assert retrieved is created
        assert isinstance(retrieved, Channel)
    
    @pytest.mark.asyncio
    async def test_publish_to_simple_channel(self):
        """Test publishing event to simple channel via EventBus."""
        bus = EventBus()
        bus.create_channel("test_channel")
        
        event = Event.create(
            event_type="test_event",
            payload={"key": "value"}
        )
        
        result = await bus.publish("test_channel", event)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_publish_base_event_to_simple_channel(self):
        """Test publishing BaseEvent to simple channel."""
        class CustomEvent(BaseEvent):
            data: str
            
            @property
            def event_type(self) -> str:
                return "custom_event"
            
            def to_payload(self) -> Dict[str, Any]:
                return {"data": self.data}
        
        bus = EventBus()
        bus.create_channel("test_channel")
        
        custom_event = CustomEvent(data="test")
        result = await bus.publish("test_channel", custom_event)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_acknowledge_on_simple_channel_raises_error(self):
        """Test that acknowledging on simple channel raises error."""
        from rx_events import EventAck, EventStatus
        
        bus = EventBus()
        bus.create_channel("test_channel")
        
        ack = EventAck.create(
            event_uuid="test-uuid",
            status=EventStatus.COMPLETED
        )
        
        with pytest.raises(ValueError, match="does not support acknowledgments"):
            await bus.acknowledge("test_channel", ack)
    
    @pytest.mark.asyncio
    async def test_simple_channel_vs_ack_channel(self):
        """Test that simple channels and ack channels can coexist."""
        bus = EventBus()
        simple_channel = bus.create_channel("simple_channel")
        ack_channel = bus.create_ack_channel("ack_channel")
        
        assert isinstance(simple_channel, Channel)
        assert not isinstance(simple_channel, type(ack_channel))
        
        # Both should support publishing
        event = Event.create(event_type="test", payload={})
        result1 = await bus.publish("simple_channel", event)
        result2 = await bus.publish("ack_channel", event)
        
        assert result1 is True
        assert result2 is True
