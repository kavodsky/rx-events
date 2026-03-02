import asyncio
import logging
import time
from typing import Dict, Any, Optional

import reactivex as rx
from reactivex import Subject

from .events import Event, EventAck, EventStatus


class AckChannel:
    def __init__(self, name: str, allow_duplicates: bool = False, timeout_seconds: int = 300):
        self.name = name
        self.allow_duplicates = allow_duplicates
        self.timeout_seconds = timeout_seconds

        # Event tracking
        self._active_events: Dict[str, Dict[str, Any]] = {}  # uuid -> event info
        self._event_stream: Subject[Event] = Subject()  # For DS to subscribe
        self._ack_stream: Subject[EventAck] = Subject()  # For DS to send acks

        # Acknowledgment tracking
        self._pending_acks: Dict[str, Event] = {}  # uuid -> original event
        self._completed_events: Dict[str, EventAck] = {}  # uuid -> ack

        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"channel.{name}")

        # Start timeout monitoring (only if event loop is running)
        self._monitor_task: Optional[asyncio.Task] = None
        try:
            loop = asyncio.get_running_loop()
            self._monitor_task = asyncio.create_task(self._monitor_timeouts())
        except RuntimeError:
            # No running event loop, task will be created when first async method is called
            pass

        # Setup ack processing
        self._setup_ack_processing()

    async def publish(self, event: Event) -> bool:
        """Publish event and wait for acknowledgment tracking"""
        # Start monitor task if not already started
        if self._monitor_task is None:
            try:
                self._monitor_task = asyncio.create_task(self._monitor_timeouts())
            except RuntimeError:
                # Still no event loop, this shouldn't happen in async context
                pass
        
        async with self._lock:
            if not self.allow_duplicates and event.uuid in self._active_events:
                raise ValueError(f"Duplicate UUID {event.uuid}")

            # Track event
            event_info = {
                'event': event,
                'status': EventStatus.PENDING,
                'published_at': time.time(),
                'processing_started_at': None
            }

            self._active_events[event.uuid] = event_info
            self._pending_acks[event.uuid] = event

            # Publish to DS subscribers
            self._event_stream.on_next(event)
            self._logger.info(f"Published {event.event_type} with UUID {event.uuid}")

            return True

    async def acknowledge(self, ack: EventAck) -> bool:
        """Receive acknowledgment from DS code"""
        async with self._lock:
            if ack.event_uuid not in self._pending_acks:
                self._logger.warning(f"Received ack for unknown UUID {ack.event_uuid}")
                return False

            # Update event status
            if ack.event_uuid in self._active_events:
                self._active_events[ack.event_uuid]['status'] = ack.status

                if ack.status == EventStatus.PROCESSING:
                    self._active_events[ack.event_uuid]['processing_started_at'] = time.time()

            # Store completion
            if ack.status in [EventStatus.COMPLETED, EventStatus.FAILED]:
                self._completed_events[ack.event_uuid] = ack

                # Clean up tracking
                self._pending_acks.pop(ack.event_uuid, None)
                self._active_events.pop(ack.event_uuid, None)

                self._logger.info(f"Event {ack.event_uuid} {ack.status.value}")

            # Emit ack to monitoring
            self._ack_stream.on_next(ack)
            return True

    def get_event_stream(self) -> rx.Observable:
        """DS code subscribes to this for events"""
        return self._event_stream

    def get_ack_stream(self) -> rx.Observable:
        """Your code can monitor acknowledgments"""
        return self._ack_stream

    def _setup_ack_processing(self):
        """Setup acknowledgment stream processing"""
        self._ack_stream.subscribe(
            on_next=self._handle_ack_received,
            on_error=lambda e: self._logger.error(f"Ack stream error: {e}")
        )

    def _handle_ack_received(self, ack: EventAck):
        """Handle received acknowledgment"""
        self._logger.debug(f"Received ack: {ack.event_uuid} -> {ack.status.value}")

        # You can add custom logic here:
        # - Update databases
        # - Send notifications
        # - Trigger other events
        # - Update metrics

    async def _monitor_timeouts(self):
        """Monitor for timed out events"""
        # Check interval: use 1 second or 1/10th of timeout, whichever is smaller
        # This ensures timeouts are detected promptly
        check_interval = min(1.0, self.timeout_seconds / 10.0)
        
        while True:
            await asyncio.sleep(check_interval)

            current_time = time.time()
            timed_out_events = []

            async with self._lock:
                for uuid, event_info in self._active_events.items():
                    published_at = event_info['published_at']

                    if current_time - published_at > self.timeout_seconds:
                        timed_out_events.append(uuid)

            # Handle timeouts
            for uuid in timed_out_events:
                await self._handle_timeout(uuid)

    async def _handle_timeout(self, event_uuid: str):
        """Handle event timeout"""
        async with self._lock:
            if event_uuid in self._active_events:
                event_info = self._active_events[event_uuid]

                # Create timeout ack
                timeout_ack = EventAck(
                    event_uuid=event_uuid,
                    status=EventStatus.TIMEOUT,
                    error=f"Event timed out after {self.timeout_seconds} seconds"
                )

                # Store and clean up
                self._completed_events[event_uuid] = timeout_ack
                self._active_events.pop(event_uuid, None)
                self._pending_acks.pop(event_uuid, None)

                self._logger.warning(f"Event {event_uuid} timed out")
                self._ack_stream.on_next(timeout_ack)

    def get_stats(self) -> Dict[str, Any]:
        """Get channel statistics"""
        return {
            "name": self.name,
            "allow_duplicates": self.allow_duplicates,
            "timeout_seconds": self.timeout_seconds,
            "active_events": len(self._active_events),
            "pending_acks": len(self._pending_acks),
            "completed_events": len(self._completed_events),
            "active_event_details": [
                {
                    "uuid": uuid,
                    "event_type": info['event'].event_type,
                    "status": info['status'].value,
                    "age_seconds": time.time() - info['published_at']
                }
                for uuid, info in self._active_events.items()
            ]
        }

    async def get_event_status(self, event_uuid: str) -> Optional[Dict[str, Any]]:
        """Get status of specific event"""
        async with self._lock:
            # Check active events
            if event_uuid in self._active_events:
                info = self._active_events[event_uuid]
                return {
                    "uuid": event_uuid,
                    "status": info['status'].value,
                    "published_at": info['published_at'],
                    "processing_started_at": info.get('processing_started_at'),
                    "age_seconds": time.time() - info['published_at']
                }

            # Check completed events
            if event_uuid in self._completed_events:
                ack = self._completed_events[event_uuid]
                return {
                    "uuid": event_uuid,
                    "status": ack.status.value,
                    "result": ack.result,
                    "error": ack.error,
                    "processing_time": ack.processing_time,
                    "completed_at": ack.timestamp
                }

            return None
