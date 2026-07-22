from __future__ import annotations

import re
from dataclasses import dataclass


_ANSWER_RE = re.compile(r"^ANSWER:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_EVIDENCE_RE = re.compile(r"^EVIDENCE:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class SynthesizedAnswer:
    answer: str
    evidence_document_ids: list[str]
    verified: bool


def answer_matches_reference(answer: str, reference: str | None) -> bool:
    if not reference:
        return True

    def normalize(value: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))

    actual = normalize(answer)
    expected = normalize(reference)
    return expected in actual or actual in expected


def synthesis_prompt(question: str, evidence: str) -> str:
    return f"""You are the final answer stage of a retrieval harness. Solve the multi-hop question
using only the supplied evidence. Connect facts across documents when needed. Prefer a short named
entity stated in the documents. Return exactly two lines and no private reasoning:
ANSWER: <short answer, or INSUFFICIENT EVIDENCE>
EVIDENCE: <at least two comma-separated document IDs that jointly support the answer>

QUESTION:
{question}

EVIDENCE:
{evidence}
"""


def parse_synthesized_answer(text: str, available_ids: set[str]) -> SynthesizedAnswer:
    answer_match = _ANSWER_RE.search(text)
    evidence_match = _EVIDENCE_RE.search(text)
    answer = answer_match.group(1).strip() if answer_match else "INSUFFICIENT EVIDENCE"
    raw_ids = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", evidence_match.group(1)) if evidence_match else []
    normalized_available = {item.split("_", 1)[0]: item for item in available_ids}
    cited: list[str] = []
    for raw_id in raw_ids:
        resolved = raw_id if raw_id in available_ids else normalized_available.get(raw_id.split("_", 1)[0])
        if resolved and resolved not in cited:
            cited.append(resolved)
    verified = answer.casefold() != "insufficient evidence" and len(cited) >= 2
    return SynthesizedAnswer(answer=answer, evidence_document_ids=cited, verified=verified)
