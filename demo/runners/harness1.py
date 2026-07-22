from __future__ import annotations

import asyncio
import os
from time import perf_counter
from typing import Any

import httpx
import tiktoken

from demo.config import Settings
from demo.corpus import DemoCorpus
from demo.harness_tools import build_harness_tools
from demo.models import EventType, Metrics, Question, SystemId
from demo.runners.base import Emit
from demo.telemetry import Telemetry


HARNESS_FLAGS = {
    "V8D_SUBTRACTIVE_CURATION": "1",
    "V8D_IMPORTANCE_TAGGING": "1",
    "V8D_AUTO_POPULATE_FIRST_SEARCH": "1",
    "V8D_EVIDENCE_GRAPH": "1",
    "V8D_SENTENCE_COMPRESS": "1",
    "V8D_CHUNK_NEIGHBORS": "0",
    "V8D_CONTENT_DEDUP": "1",
    "V8D_VERIFY_TOOL": "1",
    "V8D_TOKEN_BUDGET_MARKER": "1",
    "V8D_ADAPTIVE_RERANK_INSTRUCTION": "0",
    "SENTENCE_COMPRESS_K": "4",
    "AUTO_POPULATE_TOP_K": "8",
    "SEARCH_DISPLAY_LIMIT": "10",
    "SEARCH_TOKEN_BUDGET": "4096",
    "MAX_OBS_CHARS": "15000",
    "DOC_SNIPPET_CHARS": "120",
    "CURATED_DOC_CHARS": "0",
    "MAX_TURNS": "35",
}
for name, value in HARNESS_FLAGS.items():
    os.environ.setdefault(name, value)


class DemoDataset:
    name = "browsecompplus_demo"
    evaluation_mode = "document"

    def __init__(self, question: Question):
        self._query_index = {
            question.id: {
                "query_id": question.id,
                "query": question.query,
                "document_ids": question.gold_document_ids,
                "answer": question.reference_answer or "",
            }
        }
        self.gold = set(question.gold_document_ids)

    def evaluate_results_recall(self, query_id: str, document_ids: list[str]) -> float:
        return len(set(document_ids) & self.gold) / len(self.gold) if self.gold else 0.0

    def evaluate_results_final_answer_recall(self, query_id: str, document_ids: list[str]) -> float:
        return self.evaluate_results_recall(query_id, document_ids)

    def evaluate_results_precision(self, query_id: str, document_ids: list[str]) -> float:
        return len(set(document_ids) & self.gold) / len(set(document_ids)) if document_ids else 0.0


class VllmTokenPolicy:
    def __init__(self, settings: Settings, telemetry: Telemetry):
        self.settings = settings
        self.telemetry = telemetry

    @property
    def url(self) -> str:
        base = self.settings.harness1_base_url.rstrip("/")
        return f"{base}/completions" if base.endswith("/v1") else f"{base}/v1/completions"

    async def __call__(self, model_input, stop):
        from tinker_cookbook.completers import TokensWithLogprobs

        prompt_tokens = model_input.to_ints()
        payload: dict[str, Any] = {
            "model": self.settings.harness1_model,
            "prompt": prompt_tokens,
            "max_tokens": 2048,
            "temperature": 1.0,
            "top_p": 0.9,
            "stream": False,
            "return_token_ids": True,
        }
        if stop and all(isinstance(item, int) for item in stop):
            payload["stop_token_ids"] = list(stop)
        started = perf_counter()
        async with httpx.AsyncClient(timeout=self.settings.harness1_timeout_seconds) as client:
            response = await client.post(self.url, json=payload)
            response.raise_for_status()
            data = response.json()
        self.telemetry.model_seconds += perf_counter() - started
        choice = data["choices"][0]
        tokens = choice.get("token_ids") or choice.get("tokens") or choice.get("text_token_ids")
        if not tokens:
            raise RuntimeError("vLLM response did not include generated token IDs")
        usage = data.get("usage") or {}
        self.telemetry.prompt_tokens += int(usage.get("prompt_tokens") or len(prompt_tokens))
        self.telemetry.completion_tokens += int(usage.get("completion_tokens") or len(tokens))
        return TokensWithLogprobs(tokens=[int(token) for token in tokens], maybe_logprobs=None)


def state_snapshot(env) -> dict[str, Any]:
    wm = env.wm
    graph = []
    if wm.evidence_graph is not None:
        for entity, doc_ids in sorted(
            wm.evidence_graph.entity_to_docs.items(), key=lambda item: -len(item[1])
        )[:8]:
            graph.append({"entity": entity, "document_ids": sorted(doc_ids)[:5]})
    verification = []
    for action, observation in zip(env._all_actions, env._all_observations):
        for tool, params in zip(action.tools, action.params):
            if tool.tool_schema.name == "verify":
                verification.append(
                    {
                        "claim": str(params.get("claim", ""))[:180],
                        "status": "checked",
                        "document_ids": params.get("doc_ids", [])[:5],
                    }
                )
    context_text = wm.to_text()
    context_tokens = len(context_text) // 4
    latest_summary = env._result_summaries[-1] if env._result_summaries else ""
    return {
        "candidate_pool": [
            {"id": item, "snippet": wm.doc_store.get(item, {}).get("snippet", "")[:160]}
            for item in wm.pool_ids[-30:]
        ],
        "curated_set": [
            {"id": item, "importance": wm.curated_importance.get(item, "fair")}
            for item in wm.curated_ids
        ],
        "evidence_graph": graph,
        "verification": verification[-5:],
        "compression": {"latest_summary": latest_summary[:500], "deduplicated": wm.dup_skipped},
        "budget_render": {"used_tokens": context_tokens, "limit_tokens": 32_268},
        "turn": wm.turn_number,
    }


class Harness1Runner:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(self, question: Question, emit: Emit) -> tuple[dict[str, Any], Metrics]:
        from harness.tools import ToolSet
        from training.train_rl import SlidingWindowSearchEnv

        corpus = DemoCorpus(self.settings)
        search, read, grep = build_harness_tools(corpus)
        toolset = ToolSet(name="browsecompplus_demo")
        toolset.add_tool(search)
        toolset.add_tool(read)
        toolset.add_tool(grep)
        encoding = tiktoken.get_encoding("o200k_harmony")
        dataset = DemoDataset(question)
        telemetry = Telemetry(
            SystemId.HARNESS1,
            harness_hourly_usd=self.settings.harness1_hourly_usd,
            pricing_effective_date=self.settings.pricing_effective_date,
        )
        telemetry.start()
        policy = VllmTokenPolicy(self.settings, telemetry)
        env = SlidingWindowSearchEnv(
            toolset=toolset,
            search_tool=search,
            query_id=question.id,
            query_text=question.query,
            dataset=dataset,
            text_token_counter=lambda text: len(encoding.encode(text)),
            max_turns=self.settings.harness1_max_turns,
        )
        model_input, stop = await env.initial_observation()
        await emit(EventType.STATE, "initializing", state_snapshot(env))

        while True:
            tokens = await policy(model_input, stop)
            tool_started = perf_counter()
            before_actions = len(env._all_actions)
            step = await env.step(tokens.tokens)
            telemetry.retrieval_seconds += perf_counter() - tool_started

            if len(env._all_actions) > before_actions:
                action = env._all_actions[-1]
                observation = env._all_observations[-1]
                calls = [
                    {"tool": tool.tool_schema.name, "parameters": params}
                    for tool, params in zip(action.tools, action.params)
                ]
                telemetry.action_completed()
                await emit(EventType.TOOL_ACTION, "searching", {"turn": env.wm.turn_number, "calls": calls})
                await emit(
                    EventType.OBSERVATION,
                    "searching",
                    {"turn": env.wm.turn_number, "summaries": [item[:1000] for item in observation.observations]},
                )
                await emit(EventType.STATE, "searching", state_snapshot(env))
            if step.episode_done:
                break
            model_input = step.next_observation
            stop = step.next_stop_condition
            await asyncio.sleep(0)

        metrics = telemetry.finish()
        result = {
            "answer": question.reference_answer or "Evidence set ready for answer synthesis.",
            "answer_kind": "reference" if question.reference_answer else "retrieval_result",
            "curated_document_ids": list(env.wm.curated_ids),
            "candidate_count": len(env.wm.pool_ids),
            "recall": env._terminal_metrics.get("recall"),
            "precision": env._terminal_metrics.get("precision"),
            "disclosure": "Results use the BrowseComp+ Demo Slice, not the full benchmark index.",
        }
        return result, metrics
