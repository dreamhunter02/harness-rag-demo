from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class SystemId(StrEnum):
    HARNESS1 = "harness1"
    GPT4O = "gpt4o"


class RunMode(StrEnum):
    LIVE = "live"
    REPLAY = "replay"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class EventType(StrEnum):
    STATUS = "status"
    TOOL_ACTION = "tool_action"
    OBSERVATION = "observation"
    STATE = "state_snapshot"
    METRICS = "metrics"
    RESULT = "result"
    ERROR = "error"


class Question(BaseModel):
    id: str
    label: str
    query: str
    benchmark: str = "BrowseComp+ Demo Slice"
    reference_answer: str | None = None
    gold_document_ids: list[str] = Field(default_factory=list)


class RunRequest(BaseModel):
    question_id: str
    system: SystemId
    mode: RunMode = RunMode.LIVE


class DemoEvent(BaseModel):
    run_id: str
    sequence: int
    timestamp: datetime
    type: EventType
    phase: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def make(
        cls,
        run_id: str,
        sequence: int,
        event_type: EventType,
        phase: str,
        payload: dict[str, Any] | None = None,
    ) -> "DemoEvent":
        return cls(
            run_id=run_id,
            sequence=sequence,
            timestamp=datetime.now(timezone.utc),
            type=event_type,
            phase=phase,
            payload=payload or {},
        )


class Metrics(BaseModel):
    total_seconds: float = 0
    time_to_first_action_seconds: float | None = None
    model_inference_seconds: float = 0
    retrieval_seconds: float = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    completion_tokens_per_second: float | None = None
    action_count: int = 0
    estimated_cost_usd: float = 0
    cost_basis: str = ""


class RunRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    question_id: str
    system: SystemId
    mode: RunMode
    status: RunStatus = RunStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    events: list[DemoEvent] = Field(default_factory=list)
    metrics: Metrics | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    def public_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "system": self.system,
            "mode": self.mode,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metrics": self.metrics,
            "result": self.result,
            "error": self.error,
        }


HealthStatus = Literal["ready", "degraded", "unavailable"]
