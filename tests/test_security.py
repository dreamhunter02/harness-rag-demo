from demo.security import sanitize_payload


def test_reasoning_fields_are_removed_recursively():
    payload = {
        "tool": "search",
        "reasoning": "private",
        "nested": [{"analysis": "private", "summary": "safe"}],
        "system_prompt": "private",
    }

    assert sanitize_payload(payload) == {
        "tool": "search",
        "nested": [{"summary": "safe"}],
    }


def test_long_streamed_strings_are_bounded():
    assert len(sanitize_payload("x" * 20_000)) == 12_000
