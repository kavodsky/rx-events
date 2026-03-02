from typing import Dict, Union
import logging

from .ack_channel import AckChannel
from .channel import Channel
from .events import Event, EventAck, BaseEvent


class EventBus:
    def __init__(self):
        self._channels: Dict[str, Union[Channel, AckChannel]] = {}
        self._logger = logging.getLogger(__name__)

    def create_channel(self, name: str) -> Channel:
        """Create a simple channel without acknowledgment tracking."""
        if name in self._channels:
            raise ValueError(f"Channel {name} already exists")

        channel = Channel(name)
        self._channels[name] = channel
        self._logger.info("Created simple channel: %s", name)
        return channel

    def create_ack_channel(self, name: str, allow_duplicates: bool = False,
                           timeout_seconds: int = 300) -> AckChannel:
        """Create a channel with acknowledgment tracking."""
        if name in self._channels:
            raise ValueError(f"Channel {name} already exists")

        channel = AckChannel(name, allow_duplicates, timeout_seconds)
        self._channels[name] = channel
        self._logger.info("Created ack channel: %s (timeout: %ds)", name, timeout_seconds)
        return channel

    def get_channel(self, name: str) -> Union[Channel, AckChannel]:
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
        """Send acknowledgment to channel. Only works with AckChannel instances."""
        channel = self.get_channel(channel_name)
        if not isinstance(channel, AckChannel):
            raise ValueError(f"Channel {channel_name} does not support acknowledgments. Use create_ack_channel() instead.")
        return await channel.acknowledge(ack)


# Global event bus
event_bus = EventBus()
