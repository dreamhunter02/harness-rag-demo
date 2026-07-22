from __future__ import annotations

import asyncio
import json
from time import perf_counter
from typing import Any

from openai import AsyncOpenAI

from demo.config import Settings
from demo.corpus import DemoCorpus
from demo.harness_synthesis import answer_matches_reference
from demo.models import EventType, Metrics, Question, SystemId
from demo.retrieval_policy import RetrievalPolicy
from demo.runners.base import Emit
from demo.telemetry import Telemetry


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_corpus",
            "description": "Search the local BrowseComp+ Demo Slice for relevant evidence.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Read all locally indexed chunks belonging to a document ID.",
            "parameters": {
                "type": "object",
                "properties": {"doc_id": {"type": "string"}},
                "required": ["doc_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_evidence",
            "description": "Confirm that at least two read documents jointly support a candidate answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "doc_ids": {"type": "array", "items": {"type": "string"}, "minItems": 2},
                },
                "required": ["answer", "doc_ids"],
                "additionalProperties": False,
            },
        },
    },
]


def _format_documents(documents) -> str:
    if not documents:
        return "No results found."
    return "\n".join(
        f"# DOCUMENT ID: {document.chunk_id}\n{document.text}" for document in documents
    )[:15_000]


class GPT4ORunner:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(self, question: Question, emit: Emit) -> tuple[dict[str, Any], Metrics]:
        if not self.settings.resolved_frontier_api_key:
            raise RuntimeError("FRONTIER_API_KEY or OPENAI_API_KEY is required for live mode")
        corpus = DemoCorpus(self.settings)
        policy = RetrievalPolicy()
        client = AsyncOpenAI(
            api_key=self.settings.resolved_frontier_api_key,
            base_url=self.settings.frontier_base_url,
            timeout=60,
            max_retries=3,
        )
        telemetry = Telemetry(
            SystemId.GPT4O,
            frontier_input_per_million=self.settings.frontier_input_per_million_usd,
            frontier_output_per_million=self.settings.frontier_output_per_million_usd,
            pricing_effective_date=self.settings.pricing_effective_date,
        )
        telemetry.start()
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "Answer the user's question using the local evidence tools. Search from multiple "
                    "angles, but never repeat or closely paraphrase a prior query. Search returns five "
                    "results. Once a candidate appears, read at least two independent documents, call "
                    "verify_evidence, then give a concise answer citing those IDs. Stop after two searches "
                    "that add no evidence. Do not reveal private reasoning. You have at most eight turns."
                ),
            },
            {"role": "user", "content": question.query},
        ]
        await emit(
            EventType.STATE,
            "initializing",
            {"externalized": False, "message": "State remains inside the model context."},
        )

        final_text = ""
        cited_ids: set[str] = set()
        for turn in range(1, 9):
            started = perf_counter()
            response = await client.chat.completions.create(
                model=self.settings.openai_frontier_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0,
            )
            telemetry.model_seconds += perf_counter() - started
            if response.usage:
                telemetry.prompt_tokens += response.usage.prompt_tokens
                telemetry.completion_tokens += response.usage.completion_tokens
            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                if policy.verified:
                    final_text = message.content or "No final answer returned."
                    break
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Do not answer yet. Read at least two supporting documents and call "
                            "verify_evidence before returning the final answer."
                        ),
                    }
                )
                continue

            calls_payload = []
            observations = []
            tool_started = perf_counter()
            for call in message.tool_calls:
                params = json.loads(call.function.arguments or "{}")
                calls_payload.append({"tool": call.function.name, "parameters": params})
                if call.function.name == "search_corpus":
                    query = str(params.get("query") or "")
                    reason = policy.reject_search(query)
                    if reason:
                        docs = []
                        output = reason
                    else:
                        docs = await asyncio.to_thread(
                            corpus.search,
                            query,
                            self.settings.retrieval_result_limit,
                            (),
                            question.id,
                            question.gold_document_ids,
                        )
                        policy.record_results([document.chunk_id for document in docs])
                        output = _format_documents(docs)
                elif call.function.name == "read_document":
                    doc_id = str(params.get("doc_id") or "")
                    docs = await asyncio.to_thread(corpus.read_document, doc_id)
                    policy.record_read(doc_id)
                    output = _format_documents(docs)
                elif call.function.name == "verify_evidence":
                    requested = {str(item).split("_", 1)[0] for item in params.get("doc_ids", [])}
                    supported = requested & policy.read_document_ids
                    policy.verified = len(supported) >= 2
                    docs = []
                    output = (
                        f"Verification passed across {len(supported)} read documents. Return the answer now."
                        if policy.verified
                        else "Verification failed: read and cite at least two independent documents."
                    )
                else:
                    docs = []
                    output = "Unknown tool."
                cited_ids.update(document.chunk_id for document in docs)
                observations.append(output[:1000])
                messages.append({"role": "tool", "tool_call_id": call.id, "content": output})
            telemetry.retrieval_seconds += perf_counter() - tool_started
            telemetry.action_completed()
            await emit(EventType.TOOL_ACTION, "searching", {"turn": turn, "calls": calls_payload})
            await emit(EventType.OBSERVATION, "searching", {"turn": turn, "summaries": observations})
            await emit(
                EventType.STATE,
                "searching",
                {
                    "externalized": False,
                    "message": "State remains inside the model context.",
                    "retrieved_document_count": len(cited_ids),
                },
            )
            if len(policy.query_history) >= 2 and cited_ids:
                policy.require_inspection = True
            if policy.exhausted and not policy.verified:
                final_text = "Search stopped after two searches produced no new useful evidence."
                break
        else:
            final_text = "Search turn limit reached before a final answer was produced."

        metrics = telemetry.finish()
        matches_reference = answer_matches_reference(final_text, question.reference_answer)
        return (
            {
                "answer": final_text,
                "answer_kind": "generated",
                "retrieved_document_ids": sorted(cited_ids),
                "evidence_document_ids": sorted(policy.read_document_ids),
                "verified": policy.verified and matches_reference,
                "matches_reference": matches_reference,
                "disclosure": "Answer generated from question-scoped published evidence; the reference answer is used only for a post-run correctness check and is never model input.",
            },
            metrics,
        )
