"""Tests for ack_channel module."""
import pytest
import asyncio
import time
from rx_events import AckChannel, Event, EventAck, EventStatus
from reactivex import operators as ops


class TestAckChannel:
    """Tests for AckChannel class."""
    
    def test_create_channel(self):
        """Test creating an AckChannel."""
        channel = AckChannel("test_channel", allow_duplicates=False, timeout_seconds=60)
        
        assert channel.name == "test_channel"
        assert channel.allow_duplicates is False
        assert channel.timeout_seconds == 60
    
    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test publishing an event to channel."""
        channel = AckChannel("test_channel")
        event = Event.create(event_type="test", payload={})
        
        result = await channel.publish(event)
        assert result is True
        assert event.uuid in channel._active_events
        assert event.uuid in channel._pending_acks
    
    @pytest.mark.asyncio
    async def test_publish_duplicate_event(self):
        """Test that duplicate events are rejected when duplicates not allowed."""
        channel = AckChannel("test_channel", allow_duplicates=False)
        event = Event.create(event_type="test", payload={})
        
        await channel.publish(event)
        
        # Try to publish same event again
        with pytest.raises(ValueError, match="Duplicate UUID"):
            await channel.publish(event)
    
    @pytest.mark.asyncio
    async def test_publish_duplicate_allowed(self):
        """Test that duplicates are allowed when configured."""
        channel = AckChannel("test_channel", allow_duplicates=True)
        event = Event.create(event_type="test", payload={})
        
        await channel.publish(event)
        # Should not raise error
        result = await channel.publish(event)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_acknowledge_event(self):
        """Test acknowledging an event."""
        channel = AckChannel("test_channel")
        event = Event.create(event_type="test", payload={})
        
        await channel.publish(event)
        
        ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.COMPLETED
        )
        
        result = await channel.acknowledge(ack)
        assert result is True
        assert event.uuid not in channel._pending_acks
        assert event.uuid not in channel._active_events
        assert event.uuid in channel._completed_events
    
    @pytest.mark.asyncio
    async def test_acknowledge_processing_status(self):
        """Test acknowledging with PROCESSING status."""
        channel = AckChannel("test_channel")
        event = Event.create(event_type="test", payload={})
        
        await channel.publish(event)
        
        ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.PROCESSING
        )
        
        await channel.acknowledge(ack)
        
        status = await channel.get_event_status(event.uuid)
        assert status["status"] == "processing"
        assert status["processing_started_at"] is not None
    
    @pytest.mark.asyncio
    async def test_acknowledge_nonexistent_event(self):
        """Test acknowledging a non-existent event."""
        channel = AckChannel("test_channel")
        
        ack = EventAck.create(
            event_uuid="nonexistent",
            status=EventStatus.COMPLETED
        )
        
        result = await channel.acknowledge(ack)
        assert result is False
    
    def test_get_event_stream(self):
        """Test getting event stream."""
        channel = AckChannel("test_channel")
        stream = channel.get_event_stream()
        
        assert stream is not None
    
    def test_get_ack_stream(self):
        """Test getting acknowledgment stream."""
        channel = AckChannel("test_channel")
        stream = channel.get_ack_stream()
        
        assert stream is not None
    
    @pytest.mark.asyncio
    async def test_event_stream_subscription(self):
        """Test subscribing to event stream."""
        channel = AckChannel("test_channel")
        events_received = []
        
        def on_next(event):
            events_received.append(event)
        
        channel.get_event_stream().subscribe(on_next=on_next)
        
        event1 = Event.create(event_type="test1", payload={})
        event2 = Event.create(event_type="test2", payload={})
        
        await channel.publish(event1)
        await asyncio.sleep(0.1)  # Give time for async processing
        await channel.publish(event2)
        await asyncio.sleep(0.1)
        
        assert len(events_received) == 2
        assert events_received[0].event_type == "test1"
        assert events_received[1].event_type == "test2"
    
    @pytest.mark.asyncio
    async def test_ack_stream_subscription(self):
        """Test subscribing to acknowledgment stream."""
        channel = AckChannel("test_channel")
        acks_received = []
        
        def on_next(ack):
            acks_received.append(ack)
        
        channel.get_ack_stream().subscribe(on_next=on_next)
        
        event = Event.create(event_type="test", payload={})
        await channel.publish(event)
        
        ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.COMPLETED
        )
        
        await channel.acknowledge(ack)
        await asyncio.sleep(0.1)
        
        assert len(acks_received) == 1
        assert acks_received[0].status == EventStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_get_event_status_pending(self):
        """Test getting status of pending event."""
        channel = AckChannel("test_channel")
        event = Event.create(event_type="test", payload={})
        
        await channel.publish(event)
        
        status = await channel.get_event_status(event.uuid)
        assert status is not None
        assert status["status"] == "pending"
        assert status["uuid"] == event.uuid
        assert "published_at" in status
    
    @pytest.mark.asyncio
    async def test_get_event_status_completed(self):
        """Test getting status of completed event."""
        channel = AckChannel("test_channel")
        event = Event.create(event_type="test", payload={})
        
        await channel.publish(event)
        
        ack = EventAck.create(
            event_uuid=event.uuid,
            status=EventStatus.COMPLETED,
            result={"success": True},
            processing_time=1.5
        )
        
        await channel.acknowledge(ack)
        
        status = await channel.get_event_status(event.uuid)
        assert status is not None
        assert status["status"] == "completed"
        assert status["result"] == {"success": True}
        assert status["processing_time"] == 1.5
    
    @pytest.mark.asyncio
    async def test_get_event_status_nonexistent(self):
        """Test getting status of non-existent event."""
        channel = AckChannel("test_channel")
        
        status = await channel.get_event_status("nonexistent")
        assert status is None
    
    def test_get_stats(self):
        """Test getting channel statistics."""
        channel = AckChannel("test_channel", timeout_seconds=120)
        
        stats = channel.get_stats()
        assert stats["name"] == "test_channel"
        assert stats["timeout_seconds"] == 120
        assert stats["allow_duplicates"] is False
        assert stats["active_events"] == 0
        assert stats["pending_acks"] == 0
        assert stats["completed_events"] == 0
    
    @pytest.mark.asyncio
    async def test_get_stats_with_events(self):
        """Test getting stats with active events."""
        channel = AckChannel("test_channel")
        event = Event.create(event_type="test", payload={})
        
        await channel.publish(event)
        
        stats = channel.get_stats()
        assert stats["active_events"] == 1
        assert stats["pending_acks"] == 1
        assert len(stats["active_event_details"]) == 1
        assert stats["active_event_details"][0]["uuid"] == event.uuid
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that events timeout after specified time."""
        channel = AckChannel("test_channel", timeout_seconds=1)  # 1 second timeout
        event = Event.create(event_type="test", payload={})
        
        await channel.publish(event)
        
        # Wait for timeout
        await asyncio.sleep(1.5)
        
        # Check that timeout was handled
        status = await channel.get_event_status(event.uuid)
        assert status is not None
        assert status["status"] == "timeout"
        assert "timed out" in status.get("error", "").lower()
