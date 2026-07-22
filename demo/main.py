from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from demo.config import ROOT, settings
from demo.models import RunRequest
from demo.questions import load_questions
from demo.service import RunConflict, RunManager


app = FastAPI(title="Harness-1 Live Demo", version="0.1.0")
manager = RunManager(settings)


@app.get("/api/health")
async def health():
    return await manager.health()


@app.get("/api/questions")
async def questions():
    return [question.model_dump() for question in load_questions()]


@app.post("/api/runs", status_code=202)
async def create_run(request: RunRequest):
    try:
        record = await manager.create(request)
        return record.public_summary()
    except KeyError:
        raise HTTPException(404, "Unknown question") from None
    except RunConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    try:
        return manager.get(run_id).public_summary()
    except KeyError:
        raise HTTPException(404, "Unknown run") from None


@app.get("/api/runs/{run_id}/events")
async def run_events(request: Request, run_id: str, after: int = Query(0, ge=0)):
    try:
        manager.get(run_id)
    except KeyError:
        raise HTTPException(404, "Unknown run") from None

    async def events():
        async for event in manager.stream(run_id, after):
            if await request.is_disconnected():
                break
            yield {
                "id": str(event.sequence),
                "event": event.type.value,
                "data": event.model_dump_json(),
            }

    return EventSourceResponse(events(), ping=10)


@app.post("/api/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    try:
        return (await manager.cancel(run_id)).public_summary()
    except KeyError:
        raise HTTPException(404, "Unknown run") from None


frontend = ROOT / "frontend" / "dist"
if frontend.exists():
    app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")

    @app.get("/{path:path}")
    async def frontend_app(path: str):
        target = frontend / path
        if path and target.is_file():
            return FileResponse(target)
        return FileResponse(frontend / "index.html")
