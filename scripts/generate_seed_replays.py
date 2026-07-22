"""Generate deterministic, visibly disclosed stage-recovery fixtures.

These fixtures make failure recovery testable before credentials and a remote GPU are
available. A successful live run replaces its matching fixture automatically.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = json.loads((ROOT / "fixtures/questions.json").read_text())
OUTPUT = ROOT / "fixtures/replays"


def event(event_type: str, phase: str, payload: dict, delay_ms: int = 90) -> dict:
    return {"type": event_type, "phase": phase, "payload": payload, "delay_ms": delay_ms}


def harness_events(question: dict, index: int) -> list[dict]:
    docs = [f"bcplus-{question['id'].split('-')[-1]}-evidence-{n}" for n in range(1, 5)]
    snapshots = [
        {
            "turn": 1,
            "candidate_pool": [{"id": doc} for doc in docs],
            "curated_set": [],
            "evidence_graph": [],
            "verification": [],
            "compression": {},
            "budget_render": {"used_tokens": 1880, "limit_tokens": 32268},
        },
        {
            "turn": 2,
            "candidate_pool": [{"id": doc} for doc in docs],
            "curated_set": [{"id": docs[0], "importance": "high"}, {"id": docs[1], "importance": "fair"}],
            "evidence_graph": [{"entity": "primary subject", "document_ids": docs[:2]}],
            "verification": [],
            "compression": {},
            "budget_render": {"used_tokens": 3910, "limit_tokens": 32268},
        },
        {
            "turn": 3,
            "candidate_pool": [{"id": doc} for doc in docs],
            "curated_set": [{"id": docs[0], "importance": "high"}, {"id": docs[1], "importance": "high"}, {"id": docs[2], "importance": "fair"}],
            "evidence_graph": [
                {"entity": "primary subject", "document_ids": docs[:2]},
                {"entity": "publication and date", "document_ids": docs[1:3]},
            ],
            "verification": [{"claim": "Identity and date constraints align", "status": "supported", "document_ids": docs[:2]}],
            "compression": {},
            "budget_render": {"used_tokens": 6120, "limit_tokens": 32268},
        },
        {
            "turn": 4,
            "candidate_pool": [{"id": doc} for doc in docs],
            "curated_set": [{"id": docs[0], "importance": "high"}, {"id": docs[1], "importance": "high"}, {"id": docs[2], "importance": "fair"}],
            "evidence_graph": [
                {"entity": "primary subject", "document_ids": docs[:2]},
                {"entity": "publication and date", "document_ids": docs[1:3]},
                {"entity": "answer evidence", "document_ids": docs[2:]},
            ],
            "verification": [
                {"claim": "Identity and date constraints align", "status": "supported", "document_ids": docs[:2]},
                {"claim": "Answer is supported by disclosed evidence", "status": "supported", "document_ids": docs[2:]},
            ],
            "compression": {"latest_summary": "The evidence chain links the subject, publication window, and requested identifying detail.", "deduplicated": 2},
            "budget_render": {"used_tokens": 7890, "limit_tokens": 32268},
        },
    ]
    tool_specs = [
        ("search_corpus", {"query": question["query"][:110]}, "Retrieved a ranked candidate set from the local demo slice."),
        ("read_document", {"document_id": docs[0]}, "Inspected the leading evidence document and extracted its relevant passage."),
        ("curate_evidence", {"document_ids": docs[:3]}, "Promoted mutually supporting documents into the curated evidence set."),
        ("verify_claim", {"document_ids": docs[1:]}, "Checked the candidate answer against independent evidence and compressed the result."),
    ]
    items: list[dict] = []
    for turn, ((tool, parameters, summary), snapshot) in enumerate(zip(tool_specs, snapshots, strict=True), 1):
        items.extend(
            [
                event("tool_action", "acting", {"turn": turn, "calls": [{"tool": tool, "parameters": parameters}]}),
                event("observation", "observing", {"turn": turn, "summaries": [summary]}),
                event("state_snapshot", "updating_state", snapshot),
            ]
        )
    answer = question.get("reference_answer") or "Evidence set prepared; run live to synthesize the final answer."
    items.extend(
        [
            event("result", "completed", {"answer": answer, "answer_kind": "seed_replay", "disclosure": "Deterministic stage-recovery fixture—not a live model result or benchmark measurement.", "curated_document_ids": docs[:3]}),
            event("metrics", "completed", {"total_seconds": 18.4 + index, "time_to_first_action_seconds": 1.2 + index / 10, "model_inference_seconds": 14.1 + index, "retrieval_seconds": 2.3, "prompt_tokens": 6810 + index * 210, "completion_tokens": 1240 + index * 80, "completion_tokens_per_second": 88.0, "action_count": 4, "estimated_cost_usd": 0.018 + index / 1000, "cost_basis": "Illustrative fixture—not live measured"}),
        ]
    )
    return items


def gpt_events(question: dict, index: int) -> list[dict]:
    doc = f"bcplus-{question['id'].split('-')[-1]}-evidence-1"
    answer = question.get("reference_answer") or "Run live to synthesize the final answer from retrieved evidence."
    return [
        event("state_snapshot", "starting", {"externalized": False, "message": "State remains inside the model context.", "retrieved_document_count": 0}),
        event("tool_action", "acting", {"turn": 1, "calls": [{"tool": "search_corpus", "parameters": {"query": question["query"][:110]}}]}),
        event("observation", "observing", {"turn": 1, "summaries": ["Retrieved a ranked candidate set from the same local demo slice."]}),
        event("state_snapshot", "updating_state", {"externalized": False, "message": "State remains inside the model context.", "retrieved_document_count": 10}),
        event("tool_action", "acting", {"turn": 2, "calls": [{"tool": "read_document", "parameters": {"document_id": doc}}]}),
        event("observation", "observing", {"turn": 2, "summaries": ["Read the top evidence document inside the bounded tool loop."]}),
        event("state_snapshot", "updating_state", {"externalized": False, "message": "State remains inside the model context.", "retrieved_document_count": 10}),
        event("result", "completed", {"answer": answer, "answer_kind": "seed_replay", "disclosure": "Deterministic stage-recovery fixture—not a live model result or benchmark measurement.", "retrieved_document_ids": [doc]}),
        event("metrics", "completed", {"total_seconds": 7.8 + index, "time_to_first_action_seconds": 0.9 + index / 10, "model_inference_seconds": 5.6 + index, "retrieval_seconds": 1.4, "prompt_tokens": 4920 + index * 180, "completion_tokens": 510 + index * 40, "completion_tokens_per_second": 91.1, "action_count": 2, "estimated_cost_usd": 0.020 + index / 1000, "cost_basis": "Illustrative fixture—not live measured"}),
    ]


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for index, question in enumerate(QUESTIONS):
        for system, factory in (("harness1", harness_events), ("gpt4o", gpt_events)):
            path = OUTPUT / f"{question['id']}-{system}.jsonl"
            path.write_text("".join(json.dumps(item, separators=(",", ":")) + "\n" for item in factory(question, index)))
    print(f"Wrote {len(QUESTIONS) * 2} deterministic replay fixtures to {OUTPUT}")


if __name__ == "__main__":
    main()
