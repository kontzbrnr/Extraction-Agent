from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from infra.orchestration.runtime.orchestrator import orchestrator_run


app = FastAPI(title="Research Orchestrator Runtime API")


class RunRequest(BaseModel):
    ledgerRoot: str


@app.post("/run")
def run(request: RunRequest) -> dict:
    try:
        return orchestrator_run(request.ledgerRoot)
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise HTTPException(status_code=500, detail=str(exc)) from exc
