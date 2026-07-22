import asyncio
import json

import pytest

from demo.config import Settings
from demo.models import EventType, RunRequest, RunStatus
from demo.service import RunManager


def write_replay(path):
    rows = [
        {"type": "tool_action", "phase": "acting", "delay_ms": 0, "payload": {"turn": 1, "calls": [{"tool": "search", "parameters": {}}]}},
        {"type": "state_snapshot", "phase": "state", "delay_ms": 0, "payload": {"turn": 1}},
        {"type": "result", "phase": "completed", "payload": {"answer": "fixture"}},
        {"type": "metrics", "phase": "completed", "payload": {"total_seconds": 1, "action_count": 1}},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


async def test_replay_event_order_and_sse_reconnect_cursor(tmp_path):
    replay_dir = tmp_path / "replays"
    replay_dir.mkdir()
    write_replay(replay_dir / "bcplus-100-harness1.jsonl")
    manager = RunManager(Settings(demo_replay_dir=replay_dir, run_timeout_seconds=5))

    record = await manager.create(RunRequest(question_id="bcplus-100", system="harness1", mode="replay"))
    await manager.tasks[record.id]

    assert record.status == RunStatus.COMPLETED
    assert [event.sequence for event in record.events] == list(range(1, len(record.events) + 1))
    assert record.events[-1].type == EventType.STATUS
    assert record.events[-1].payload["status"] == "completed"
    reconnected = [event async for event in manager.stream(record.id, after=2)]
    assert all(event.sequence > 2 for event in reconnected)


async def test_cancellation_sets_terminal_state(monkeypatch, tmp_path):
    async def slow_run(self, question, emit):
        await asyncio.sleep(60)

    monkeypatch.setattr("demo.runners.replay.ReplayRunner.run", slow_run)
    manager = RunManager(Settings(demo_replay_dir=tmp_path, run_timeout_seconds=120))
    record = await manager.create(RunRequest(question_id="bcplus-100", system="harness1", mode="replay"))
    await asyncio.sleep(0)
    await manager.cancel(record.id)

    assert record.status == RunStatus.CANCELLED
    assert record.events[-1].payload["status"] == "cancelled"


@pytest.mark.parametrize("question_id", ["bcplus-100", "bcplus-1023", "bcplus-1068"])
@pytest.mark.parametrize("system", ["harness1", "gpt4o"])
async def test_all_checked_in_stage_replays_complete(monkeypatch, question_id, system):
    async def no_delay(_seconds):
        return None

    monkeypatch.setattr("demo.runners.replay.asyncio.sleep", no_delay)
    manager = RunManager(Settings())
    record = await manager.create(RunRequest(question_id=question_id, system=system, mode="replay"))
    await manager.tasks[record.id]

    assert record.status == RunStatus.COMPLETED
    assert record.result["answer_kind"] == "seed_replay"
    assert "not a live model result" in record.result["disclosure"]
