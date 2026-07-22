from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from demo.models import Metrics, SystemId


@dataclass
class Telemetry:
    system: SystemId
    brev_hourly_usd: float = 0
    gpt4o_input_per_million: float = 2.50
    gpt4o_output_per_million: float = 10.00
    pricing_effective_date: str = "2026-07-21"
    started_at: float = 0
    first_action_at: float | None = None
    model_seconds: float = 0
    retrieval_seconds: float = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    action_count: int = 0

    def start(self) -> None:
        self.started_at = perf_counter()

    def action_completed(self) -> None:
        self.action_count += 1
        if self.first_action_at is None:
            self.first_action_at = perf_counter()

    def finish(self) -> Metrics:
        now = perf_counter()
        total = max(0.0, now - self.started_at)
        ttfa = None if self.first_action_at is None else self.first_action_at - self.started_at
        throughput = (
            self.completion_tokens / self.model_seconds if self.model_seconds > 0 else None
        )
        if self.system == SystemId.GPT4O:
            cost = (
                self.prompt_tokens * self.gpt4o_input_per_million
                + self.completion_tokens * self.gpt4o_output_per_million
            ) / 1_000_000
            basis = f"GPT-4o standard token rates configured {self.pricing_effective_date}."
        else:
            cost = self.brev_hourly_usd * self.model_seconds / 3600
            basis = (
                f"Brev rate configured {self.pricing_effective_date}, allocated to model inference; "
                "excludes idle/warm-up/storage."
            )
        return Metrics(
            total_seconds=round(total, 3),
            time_to_first_action_seconds=None if ttfa is None else round(ttfa, 3),
            model_inference_seconds=round(self.model_seconds, 3),
            retrieval_seconds=round(self.retrieval_seconds, 3),
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            completion_tokens_per_second=None if throughput is None else round(throughput, 2),
            action_count=self.action_count,
            estimated_cost_usd=round(cost, 6),
            cost_basis=basis,
        )
