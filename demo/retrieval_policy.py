from __future__ import annotations

import re
from dataclasses import dataclass, field


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def query_tokens(query: str) -> frozenset[str]:
    return frozenset(_TOKEN_RE.findall(query.casefold()))


def queries_are_near_duplicates(left: str, right: str, threshold: float = 0.8) -> bool:
    left_tokens = query_tokens(left)
    right_tokens = query_tokens(right)
    if not left_tokens or not right_tokens:
        return left.strip().casefold() == right.strip().casefold()
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens) >= threshold


@dataclass
class RetrievalPolicy:
    """Deterministic retrieval guard shared by both demo systems."""

    no_new_limit: int = 2
    query_history: list[str] = field(default_factory=list)
    seen_document_ids: set[str] = field(default_factory=set)
    consecutive_no_new: int = 0
    require_inspection: bool = False
    read_document_ids: set[str] = field(default_factory=set)
    verified: bool = False

    def reject_search(self, query: str) -> str | None:
        if self.consecutive_no_new >= self.no_new_limit:
            return "Search stopped: two searches produced no new evidence. Inspect and verify existing documents."
        if self.require_inspection and not self.read_document_ids:
            return "Search paused: a candidate evidence set exists. Call read_document before searching again."
        if self.require_inspection and self.read_document_ids and not self.verified:
            return "Search paused: read_document completed. Verify the candidate before searching again."
        if any(queries_are_near_duplicates(query, prior) for prior in self.query_history):
            return "Search rejected: duplicate or near-duplicate query. Inspect existing evidence or substantially change the query."
        self.query_history.append(query)
        return None

    def record_results(self, document_ids: list[str]) -> int:
        new_ids = set(document_ids) - self.seen_document_ids
        self.seen_document_ids.update(document_ids)
        self.consecutive_no_new = 0 if new_ids else self.consecutive_no_new + 1
        return len(new_ids)

    def record_read(self, document_id: str) -> None:
        if document_id:
            self.read_document_ids.add(document_id.split("_", 1)[0])

    @property
    def exhausted(self) -> bool:
        return self.consecutive_no_new >= self.no_new_limit

