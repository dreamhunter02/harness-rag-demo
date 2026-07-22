from unittest.mock import patch

import pytest

from demo.models import SystemId
from demo.telemetry import Telemetry


def test_gpt_cost_and_metrics_are_aggregated():
    telemetry = Telemetry(SystemId.GPT4O)
    with patch("demo.telemetry.perf_counter", side_effect=[10.0, 11.25, 15.0]):
        telemetry.start()
        telemetry.action_completed()
        telemetry.model_seconds = 2
        telemetry.retrieval_seconds = 1.5
        telemetry.prompt_tokens = 1_000_000
        telemetry.completion_tokens = 100_000
        metrics = telemetry.finish()

    assert metrics.total_seconds == 5
    assert metrics.time_to_first_action_seconds == 1.25
    assert metrics.completion_tokens_per_second == 50_000
    assert metrics.estimated_cost_usd == pytest.approx(3.5)


def test_harness_cost_uses_only_measured_inference_allocation():
    telemetry = Telemetry(SystemId.HARNESS1, brev_hourly_usd=3.0)
    with patch("demo.telemetry.perf_counter", side_effect=[1.0, 121.0]):
        telemetry.start()
        telemetry.model_seconds = 120
        metrics = telemetry.finish()

    assert metrics.estimated_cost_usd == pytest.approx(0.1)
    assert "excludes idle/warm-up/storage" in metrics.cost_basis
