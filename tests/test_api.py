from fastapi.testclient import TestClient

from demo.main import app


client = TestClient(app)


def test_health_and_questions_contracts():
    health = client.get("/api/health")
    questions = client.get("/api/questions")

    assert health.status_code == 200
    assert set(health.json()["components"]) == {"corpus", "harness1_vllm", "gpt4o", "replays"}
    assert questions.status_code == 200
    assert len(questions.json()) == 2
    assert all(item["benchmark"] == "BrowseComp+ Demo Slice" for item in questions.json())


def test_unknown_run_and_question_return_404():
    assert client.get("/api/runs/missing").status_code == 404
    response = client.post(
        "/api/runs",
        json={"question_id": "missing", "system": "harness1", "mode": "live"},
    )
    assert response.status_code == 404
