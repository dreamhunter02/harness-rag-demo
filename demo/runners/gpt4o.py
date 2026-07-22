from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from openai import AsyncOpenAI

from demo.config import Settings
from demo.corpus import DemoCorpus
from demo.models import EventType, Metrics, Question, SystemId
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
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for GPT-4o live mode")
        corpus = DemoCorpus(self.settings)
        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        telemetry = Telemetry(SystemId.GPT4O)
        telemetry.start()
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "Answer the user's question using the local evidence tools. Search from multiple "
                    "angles, read promising documents, then give a concise answer and cite document IDs. "
                    "Do not reveal private reasoning. You have at most eight search turns."
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
                final_text = message.content or "No final answer returned."
                break

            calls_payload = []
            observations = []
            tool_started = perf_counter()
            for call in message.tool_calls:
                params = json.loads(call.function.arguments or "{}")
                calls_payload.append({"tool": call.function.name, "parameters": params})
                if call.function.name == "search_corpus":
                    docs = corpus.search(str(params.get("query") or ""))
                elif call.function.name == "read_document":
                    docs = corpus.read_document(str(params.get("doc_id") or ""))
                else:
                    docs = []
                cited_ids.update(document.chunk_id for document in docs)
                output = _format_documents(docs)
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
        else:
            final_text = "Search turn limit reached before a final answer was produced."

        metrics = telemetry.finish()
        return (
            {
                "answer": final_text,
                "answer_kind": "generated",
                "retrieved_document_ids": sorted(cited_ids),
                "disclosure": "Results use the BrowseComp+ Demo Slice, not the full benchmark index.",
            },
            metrics,
        )
