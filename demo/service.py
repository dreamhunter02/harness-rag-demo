from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import httpx

from demo.config import Settings
from demo.models import (
    DemoEvent,
    EventType,
    RunMode,
    RunRecord,
    RunRequest,
    RunStatus,
    SystemId,
)
from demo.questions import get_question
from demo.runners.gpt4o import GPT4ORunner
from demo.runners.harness1 import Harness1Runner
from demo.runners.replay import ReplayRunner
from demo.security import sanitize_payload


TERMINAL = {RunStatus.COMPLETED, RunStatus.ERROR, RunStatus.CANCELLED}


class RunConflict(RuntimeError):
    pass


class RunManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.records: dict[str, RunRecord] = {}
        self.tasks: dict[str, asyncio.Task] = {}
        self.conditions: dict[str, asyncio.Condition] = {}
        self._lock = asyncio.Lock()

    async def create(self, request: RunRequest) -> RunRecord:
        get_question(request.question_id)
        async with self._lock:
            if request.mode == RunMode.LIVE and any(
                record.mode == RunMode.LIVE and record.status in {RunStatus.QUEUED, RunStatus.RUNNING}
                for record in self.records.values()
            ):
                raise RunConflict("Only one live run may be active")
            record = RunRecord(
                question_id=request.question_id,
                system=request.system,
                mode=request.mode,
            )
            self.records[record.id] = record
            self.conditions[record.id] = asyncio.Condition()
            self.tasks[record.id] = asyncio.create_task(self._execute(record))
            return record

    async def _emit(
        self,
        record: RunRecord,
        event_type: EventType,
        phase: str,
        payload: dict[str, Any],
    ) -> None:
        event = DemoEvent.make(
            record.id,
            len(record.events) + 1,
            event_type,
            phase,
            sanitize_payload(payload),
        )
        record.events.append(event)
        record.updated_at = event.timestamp
        async with self.conditions[record.id]:
            self.conditions[record.id].notify_all()

    async def _execute(self, record: RunRecord) -> None:
        question = get_question(record.question_id)
        record.status = RunStatus.RUNNING
        await self._emit(
            record,
            EventType.STATUS,
            "starting",
            {"status": "running", "mode": record.mode, "system": record.system},
        )

        async def emit(event_type: EventType, phase: str, payload: dict[str, Any]) -> None:
            await self._emit(record, event_type, phase, payload)

        if record.mode == RunMode.REPLAY:
            runner = ReplayRunner(self.settings, record.system)
        elif record.system == SystemId.HARNESS1:
            runner = Harness1Runner(self.settings)
        else:
            runner = GPT4ORunner(self.settings)
        try:
            result, metrics = await asyncio.wait_for(
                runner.run(question, emit), timeout=self.settings.run_timeout_seconds
            )
            record.result = sanitize_payload(result)
            record.metrics = metrics
            await self._emit(record, EventType.RESULT, "completed", record.result)
            await self._emit(record, EventType.METRICS, "completed", metrics.model_dump())
            record.status = RunStatus.COMPLETED
            await self._emit(record, EventType.STATUS, "completed", {"status": "completed"})
            if record.mode == RunMode.LIVE:
                self._save_replay(record)
        except asyncio.CancelledError:
            record.status = RunStatus.CANCELLED
            await self._emit(record, EventType.STATUS, "cancelled", {"status": "cancelled"})
        except TimeoutError:
            record.status = RunStatus.ERROR
            record.error = f"Run exceeded the {self.settings.run_timeout_seconds}s timeout"
            await self._emit(
                record,
                EventType.ERROR,
                "error",
                {"message": record.error, "replay_available": self.replay_exists(record)},
            )
            await self._emit(record, EventType.STATUS, "error", {"status": "error"})
        except Exception as exc:
            record.status = RunStatus.ERROR
            record.error = str(exc)[:500]
            await self._emit(
                record,
                EventType.ERROR,
                "error",
                {"message": record.error, "replay_available": self.replay_exists(record)},
            )
            await self._emit(record, EventType.STATUS, "error", {"status": "error"})

    def _save_replay(self, record: RunRecord) -> None:
        self.settings.demo_replay_dir.mkdir(parents=True, exist_ok=True)
        path = self.settings.demo_replay_dir / f"{record.question_id}-{record.system.value}.jsonl"
        with path.open("w", encoding="utf-8") as output:
            for event in record.events:
                output.write(event.model_dump_json() + "\n")

    def replay_exists(self, record: RunRecord) -> bool:
        return (self.settings.demo_replay_dir / f"{record.question_id}-{record.system.value}.jsonl").exists()

    def get(self, run_id: str) -> RunRecord:
        if run_id not in self.records:
            raise KeyError(run_id)
        return self.records[run_id]

    async def cancel(self, run_id: str) -> RunRecord:
        record = self.get(run_id)
        task = self.tasks.get(run_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return record

    async def stream(self, run_id: str, after: int = 0) -> AsyncIterator[DemoEvent]:
        record = self.get(run_id)
        cursor = after
        while True:
            while cursor < len(record.events):
                event = record.events[cursor]
                cursor += 1
                yield event
            if record.status in TERMINAL:
                return
            async with self.conditions[run_id]:
                await self.conditions[run_id].wait()

    async def health(self) -> dict[str, Any]:
        root_url = self.settings.harness1_base_url.removesuffix("/v1")
        harness_ready = False
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                response = await client.get(f"{root_url}/health")
                harness_ready = response.is_success
        except Exception:
            pass
        corpus_ready = (self.settings.corpus_dir / "documents.jsonl").exists()
        replays = len(list(self.settings.demo_replay_dir.glob("*.jsonl")))
        return {
            "status": "ready" if corpus_ready and replays >= 6 else "degraded",
            "components": {
                "corpus": {"ready": corpus_ready},
                "harness1_vllm": {"ready": harness_ready, "url": root_url},
                "gpt4o": {"ready": bool(self.settings.openai_api_key)},
                "replays": {"ready": replays >= 6, "count": replays},
            },
        }
