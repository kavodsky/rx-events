import logging
from typing import Dict, Any

import reactivex as rx
from reactivex import Subject

from .events import Event, BaseEvent


class Channel:
    """Simple channel abstraction for event publishing and subscribing."""
    
    def __init__(self, name: str):
        self.name = name
        self._event_stream: Subject[Event] = Subject()
        self._logger = logging.getLogger(f"channel.{name}")
    
    async def publish(self, event: Event) -> bool:
        """Publish event to channel."""
        # Convert BaseEvent to Event if needed
        if isinstance(event, BaseEvent) and not isinstance(event, Event):
            event = event.to_event()
        
        self._event_stream.on_next(event)
        self._logger.info(f"Published {event.event_type} with UUID {event.uuid}")
        return True
    
    def get_event_stream(self) -> rx.Observable:
        """Get observable stream for subscribing to events."""
        return self._event_stream
    
    def get_stats(self) -> Dict[str, Any]:
        """Get channel statistics."""
        return {
            "name": self.name,
            "type": "simple"
        }
