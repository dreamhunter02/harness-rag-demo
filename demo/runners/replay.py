from __future__ import annotations

import asyncio
import json
from typing import Any

from demo.config import Settings
from demo.models import EventType, Metrics, Question, SystemId
from demo.runners.base import Emit


class ReplayRunner:
    def __init__(self, settings: Settings, system: SystemId):
        self.settings = settings
        self.system = system

    async def run(self, question: Question, emit: Emit) -> tuple[dict[str, Any], Metrics]:
        path = self.settings.demo_replay_dir / f"{question.id}-{self.system.value}.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Replay fixture is missing: {path}")
        result: dict[str, Any] | None = None
        metrics: Metrics | None = None
        for line in path.read_text().splitlines():
            stored = json.loads(line)
            event_type = EventType(stored["type"])
            if event_type == EventType.RESULT:
                result = stored["payload"]
                continue
            if event_type == EventType.METRICS:
                metrics = Metrics.model_validate(stored["payload"])
                continue
            if event_type == EventType.STATUS:
                continue
            await asyncio.sleep(float(stored.get("delay_ms", 180)) / 1000)
            await emit(event_type, stored.get("phase", "replay"), stored.get("payload", {}))
        if result is None or metrics is None:
            raise ValueError(f"Replay fixture is incomplete: {path}")
        return result, metrics
