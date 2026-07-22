from __future__ import annotations

from typing import Any, Optional

from pydantic import PrivateAttr

from demo.corpus import DemoCorpus


def _format_documents(documents) -> str:
    if not documents:
        return "No results found"
    return "\n".join(
        f"\n# DOCUMENT ID: {document.chunk_id}\n{document.text}" for document in documents
    )


def build_harness_tools(corpus: DemoCorpus):
    from harness.tools import (
        GREP_CORPUS_SCHEMA,
        READ_DOCUMENT_SCHEMA,
        SEARCH_CORPUS_SCHEMA,
        GrepCorpusToolCallMetadata,
        SearchCorpusToolCallMetadata,
        Tool,
    )

    class DemoSearchTool(Tool):
        _demo_corpus: DemoCorpus = PrivateAttr()

        def __init__(self):
            super().__init__(tool_schema=SEARCH_CORPUS_SCHEMA)
            self._demo_corpus = corpus

        def __call__(self, params: dict[Any, Any], overrides: Optional[dict] = None):
            query = str(params.get("query") or params.get("q") or "")
            ignored = (overrides or {}).get("ignore_ids", [])
            docs = self._demo_corpus.search(query, ignore_ids=ignored)
            return _format_documents(docs), SearchCorpusToolCallMetadata(
                returned_chunk_ids=[doc.chunk_id for doc in docs]
            )

    class DemoReadTool(Tool):
        _demo_corpus: DemoCorpus = PrivateAttr()

        def __init__(self):
            super().__init__(tool_schema=READ_DOCUMENT_SCHEMA)
            self._demo_corpus = corpus

        def __call__(self, params: dict[Any, Any], overrides: Optional[dict] = None):
            doc_id = str(params.get("doc_id") or params.get("id") or "")
            return _format_documents(self._demo_corpus.read_document(doc_id)), None

    class DemoGrepTool(Tool):
        _demo_corpus: DemoCorpus = PrivateAttr()

        def __init__(self):
            super().__init__(tool_schema=GREP_CORPUS_SCHEMA)
            self._demo_corpus = corpus

        def __call__(self, params: dict[Any, Any], overrides: Optional[dict] = None):
            docs = self._demo_corpus.grep(str(params.get("pattern") or ""))
            return _format_documents(docs), GrepCorpusToolCallMetadata(
                returned_chunk_ids=[doc.chunk_id for doc in docs]
            )

    return DemoSearchTool(), DemoReadTool(), DemoGrepTool()
