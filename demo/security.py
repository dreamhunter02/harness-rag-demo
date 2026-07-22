from __future__ import annotations

from typing import Any


SENSITIVE_KEYS = {
    "reasoning",
    "analysis",
    "chain_of_thought",
    "chain-of-thought",
    "system_prompt",
    "prompt_tokens_raw",
}


def sanitize_payload(value: Any) -> Any:
    """Recursively remove private-reasoning fields before persistence or streaming."""
    if isinstance(value, dict):
        return {
            key: sanitize_payload(item)
            for key, item in value.items()
            if key.lower() not in SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return value[:12_000]
    return value
