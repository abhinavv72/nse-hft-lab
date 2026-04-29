from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable


EventHandler = Callable[[dict], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event_type: str, payload: dict) -> None:
        handlers = list(self._subscribers.get(event_type, []))
        if not handlers:
            return
        await asyncio.gather(*(handler(payload) for handler in handlers), return_exceptions=True)

