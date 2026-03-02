from typing import Dict, Union
import logging

from .ack_channel import AckChannel
from .events import Event, EventAck, BaseEvent


class EventBus:
    def __init__(self):
        self._channels: Dict[str, AckChannel] = {}
        self._logger = logging.getLogger(__name__)

    def create_channel(self, name: str, allow_duplicates: bool = False,
                       timeout_seconds: int = 300) -> AckChannel:
        if name in self._channels:
            raise ValueError(f"Channel {name} already exists")

        channel = AckChannel(name, allow_duplicates, timeout_seconds)
        self._channels[name] = channel
        self._logger.info(f"Created ack channel: {name} (timeout: {timeout_seconds}s)")
        return channel

    def get_channel(self, name: str) -> AckChannel:
        if name not in self._channels:
            raise ValueError(f"Channel {name} not found")
        return self._channels[name]

    async def publish(self, channel_name: str, event: Union[Event, BaseEvent]) -> bool:
        """Publish event to channel. Accepts both Event and BaseEvent instances."""
        channel = self.get_channel(channel_name)
        # Convert BaseEvent to Event if needed
        if isinstance(event, BaseEvent) and not isinstance(event, Event):
            event = event.to_event()
        return await channel.publish(event)

    async def acknowledge(self, channel_name: str, ack: EventAck) -> bool:
        """Send acknowledgment to channel"""
        channel = self.get_channel(channel_name)
        return await channel.acknowledge(ack)


# Global event bus
event_bus = EventBus()
