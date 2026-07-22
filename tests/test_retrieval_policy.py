from demo.harness_synthesis import parse_synthesized_answer
from demo.config import Settings
from demo.retrieval_policy import RetrievalPolicy, queries_are_near_duplicates


def test_near_duplicate_queries_are_rejected():
    policy = RetrievalPolicy()
    assert policy.reject_search("Phoenix desert dream interview publication") is None
    assert "near-duplicate" in (
        policy.reject_search("publication interview Phoenix desert dream") or ""
    )
    assert queries_are_near_duplicates("alpha beta gamma delta", "delta gamma beta alpha")


def test_search_stops_after_two_no_new_results():
    policy = RetrievalPolicy()
    policy.record_results(["doc-1"])
    policy.record_results(["doc-1"])
    policy.record_results(["doc-1"])
    assert policy.exhausted
    assert "two searches" in (policy.reject_search("a new angle") or "")


def test_synthesis_requires_two_available_documents():
    valid = parse_synthesized_answer(
        "ANSWER: Phoenix New Times\nEVIDENCE: 10, 20", {"10", "20", "30"}
    )
    invalid = parse_synthesized_answer("ANSWER: Guess\nEVIDENCE: 10", {"10", "20"})
    assert valid.verified
    assert valid.evidence_document_ids == ["10", "20"]
    assert not invalid.verified


def test_stage_policy_limits_are_locked():
    settings = Settings()
    assert settings.harness1_max_turns == 12
    assert settings.harness1_max_generation_tokens == 768
    assert settings.curated_document_limit == 12
    assert settings.retrieval_result_limit == 5
