from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from demo.models import EventType, Metrics, Question


Emit = Callable[[EventType, str, dict[str, Any]], Awaitable[None]]


class Runner(Protocol):
    async def run(self, question: Question, emit: Emit) -> tuple[dict[str, Any], Metrics]: ...
