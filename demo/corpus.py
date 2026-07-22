from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any, Iterable

import chromadb
from openai import OpenAI
from rank_bm25 import BM25Okapi

from demo.config import Settings


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
COLLECTION_NAME = "browsecomp_plus_demo"


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


@dataclass(slots=True)
class CorpusDocument:
    chunk_id: str
    source: str
    text: str
    metadata: dict[str, Any]


class DemoCorpus:
    """Hybrid dense/BM25 retrieval over a persistent local Chroma collection."""

    def __init__(self, settings: Settings):
        manifest = settings.corpus_dir / "documents.jsonl"
        if not manifest.exists():
            raise FileNotFoundError(
                f"Demo corpus is missing at {manifest}. Run `python -m demo.build_corpus`."
            )
        self.settings = settings
        self.documents = [
            CorpusDocument(**json.loads(line))
            for line in manifest.read_text().splitlines()
            if line.strip()
        ]
        self.by_id = {doc.chunk_id: doc for doc in self.documents}
        self.by_source: dict[str, list[CorpusDocument]] = {}
        for doc in self.documents:
            self.by_source.setdefault(doc.source, []).append(doc)
        self.bm25 = BM25Okapi([tokenize(doc.text) for doc in self.documents])
        self.chroma = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self.collection = self.chroma.get_collection(COLLECTION_NAME)
        self.openai = OpenAI(api_key=settings.openai_api_key)

    def search(self, query: str, limit: int = 10, ignore_ids: Iterable[str] = ()) -> list[CorpusDocument]:
        ignored = set(ignore_ids)
        embedding = self.openai.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=[query],
            encoding_format="float",
        ).data[0].embedding
        dense = self.collection.query(query_embeddings=[embedding], n_results=min(50, len(self.documents)))
        dense_ids = list(dense.get("ids", [[]])[0])
        lexical_scores = self.bm25.get_scores(tokenize(query))
        lexical_order = sorted(range(len(lexical_scores)), key=lexical_scores.__getitem__, reverse=True)[:50]
        lexical_ids = [self.documents[index].chunk_id for index in lexical_order]

        scores: dict[str, float] = {}
        for rank, chunk_id in enumerate(dense_ids):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (60 + rank)
        for rank, chunk_id in enumerate(lexical_ids):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (60 + rank)
        ranked = sorted(scores, key=scores.__getitem__, reverse=True)
        return [self.by_id[item] for item in ranked if item not in ignored][:limit]

    def read_document(self, doc_id: str) -> list[CorpusDocument]:
        normalized = doc_id.split("_", 1)[0]
        return self.by_source.get(normalized, []) or ([self.by_id[doc_id]] if doc_id in self.by_id else [])

    def grep(self, pattern: str, limit: int = 5) -> list[CorpusDocument]:
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            regex = re.compile(re.escape(pattern), re.IGNORECASE)
        return [doc for doc in self.documents if regex.search(doc.text)][:limit]


def _fetch_sft_rows(limit: int = 12) -> list[dict[str, Any]]:
    import urllib.parse
    import urllib.request

    selected: list[dict[str, Any]] = []
    offset = 0
    while len(selected) < limit and offset < 900:
        params = urllib.parse.urlencode(
            {
                "dataset": "pat-jj/harness-1-train-data",
                "config": "default",
                "split": "train",
                "offset": offset,
                "length": 100,
            }
        )
        with urllib.request.urlopen(
            f"https://datasets-server.huggingface.co/rows?{params}", timeout=180
        ) as response:
            page = json.load(response)
        for item in page.get("rows", []):
            row = item["row"]
            if row.get("stage") == "sft" and row.get("dataset_name") == "browsecompplus":
                selected.append(row)
                if len(selected) == limit:
                    break
        offset += 100
    if len(selected) < limit:
        raise RuntimeError(f"Only found {len(selected)} public BrowseComp+ SFT rows")
    return selected


def _trajectory_documents(rows: list[dict[str, Any]]) -> dict[str, CorpusDocument]:
    documents: dict[str, CorpusDocument] = {}
    for row in rows:
        payload = json.loads(row["payload_json"])
        for source, stored in payload.get("doc_store", {}).items():
            text = stored.get("full_text") or stored.get("snippet") or ""
            if not text.strip():
                continue
            chunk_id = str(source)
            documents.setdefault(
                chunk_id,
                CorpusDocument(
                    chunk_id=chunk_id,
                    source=chunk_id.split("_", 1)[0],
                    text=text,
                    metadata={"origin": "published_trajectory", "query_id": str(row["query_id"])},
                ),
            )
    return documents


def _stream_distractors(limit: int, seed: int) -> Iterable[CorpusDocument]:
    from datasets import load_dataset

    files = "hf://datasets/pat-jj/harness-1-train-data/corpora/browsecompplus/test/*.parquet"
    stream = load_dataset("parquet", data_files=files, split="train", streaming=True)
    shuffled = stream.shuffle(seed=seed, buffer_size=50_000)
    for row in shuffled.take(limit):
        chunk_id = str(row["chunk_id"])
        metadata = json.loads(row.get("metadata_json") or "{}")
        source = str(metadata.get("source") or chunk_id.split("_", 1)[0])
        yield CorpusDocument(
            chunk_id=chunk_id,
            source=source,
            text=str(row["document_text"]),
            metadata={"origin": "deterministic_distractor", **metadata},
        )


def build_corpus(settings: Settings, distractor_count: int = 20_000, seed: int = 42) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to build dense embeddings")
    rows = _fetch_sft_rows(12)
    documents = _trajectory_documents(rows)
    for document in _stream_distractors(distractor_count, seed):
        documents.setdefault(document.chunk_id, document)

    settings.corpus_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    manifest = settings.corpus_dir / "documents.jsonl"
    ordered = [documents[key] for key in sorted(documents)]
    with manifest.open("w", encoding="utf-8") as output:
        for document in ordered:
            output.write(json.dumps(asdict(document), ensure_ascii=False, default=str) + "\n")

    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)
    openai = OpenAI(api_key=settings.openai_api_key)
    batch_size = 128
    started = perf_counter()
    for start in range(0, len(ordered), batch_size):
        batch = ordered[start : start + batch_size]
        response = openai.embeddings.create(
            model=settings.openai_embedding_model,
            input=[item.text for item in batch],
            encoding_format="float",
        )
        collection.add(
            ids=[item.chunk_id for item in batch],
            documents=[item.text for item in batch],
            metadatas=[{"source": item.source, **item.metadata} for item in batch],
            embeddings=[item.embedding for item in response.data],
        )

    candidates = settings.corpus_dir / "candidate_questions.json"
    candidates.write_text(
        json.dumps(
            [
                {
                    "id": str(row["query_id"]),
                    "query": row["query"],
                    "gold_document_ids": json.loads(row.get("document_ids_json") or "[]"),
                }
                for row in rows
            ],
            indent=2,
        )
    )
    return {
        "documents": len(ordered),
        "candidate_questions": len(rows),
        "seed": seed,
        "seconds": round(perf_counter() - started, 1),
    }
