from demo.corpus import _trajectory_documents, tokenize


def test_trajectory_documents_are_deduplicated_and_tagged():
    payload = {"doc_store": {"source_1": {"full_text": "Alpha evidence"}}}
    rows = [
        {"payload_json": __import__("json").dumps(payload), "query_id": 7},
        {"payload_json": __import__("json").dumps(payload), "query_id": 8},
    ]

    documents = _trajectory_documents(rows)

    assert list(documents) == ["source_1"]
    assert documents["source_1"].metadata["origin"] == "published_trajectory"
    assert tokenize("Alpha's 42nd result") == ["alpha", "s", "42nd", "result"]
