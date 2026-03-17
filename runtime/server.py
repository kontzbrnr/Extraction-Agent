"""
bridge/server.py

Mission Control bridge server.

Exposes the research-agent pipeline to the Mission Control Next.js
dashboard (http://localhost:3000) via a local REST API on port 8000.

Sole Python entry point: openclaw.run_research_agent
Nothing in this server calls orchestrator_run, pipeline agents, or
any sub-agent directly. OpenClaw handles parameter validation, ledger
gate, concurrency lock, orchestrator call, and invocation logging.

Endpoints:
    GET  /health        — liveness check
    POST /run           — trigger one orchestrator invocation via OpenClaw
    GET  /runs          — return invocation history from openclaw_invocation_log.jsonl

Run from the research-agent project root:
    uvicorn runtime.server:app --port 8000 --reload

Or:
    python -m uvicorn runtime.server:app --port 8000 --reload
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Optional

# ── Path bootstrap ────────────────────────────────────────────────────────────
# Add research-agent root to sys.path so openclaw and all sub-packages resolve.
# Mirrors the approach in conftest.py.
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ── Imports ───────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from infra.orchestration.openclaw import (
    run_research_agent,
    LedgerNotReachableError,
    ConcurrencyViolationError,
    BindingViolationError,
)
from infra.orchestration.openclaw.invocation_logger import LOG_FILENAME

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Research Agent Bridge",
    description="Mission Control → OpenClaw bridge server",
    version="1.0.0",
)

# Allow Mission Control (localhost:3000) to call this server cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Request / response models ─────────────────────────────────────────────────

class RunRequest(BaseModel):
    """Parameters accepted by POST /run.

    Maps directly to run_research_agent's parameter surface.
    Only ledger_root and env_path are required.
    mode is always 'deterministic' — no other mode is permitted.
    """
    ledger_root: str
    env_path: str
    mode: str = "deterministic"
    run_id: Optional[str] = None
    seed: Optional[int] = None


class RunResponse(BaseModel):
    status: str           # "success" | "error"
    result: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    """Liveness check. Returns 200 if server is reachable."""
    return {"status": "ok", "server": "research-agent-bridge"}


@app.post("/run", response_model=RunResponse)
def trigger_run(request: RunRequest) -> RunResponse:
    """Trigger one orchestrator invocation via OpenClaw.

    Calls run_research_agent with the provided parameters.
    OpenClaw handles:
        - InvocationParams validation (shape)
        - assert_ledger_reachable (path)
        - acquire_run_lock (concurrency guard)
        - orchestrator_run (pipeline execution)
        - write_invocation_log (execution logging)

    Returns:
        200 — run completed (success or halted with reason code)
        409 — concurrent invocation already in progress
        422 — ledger path not reachable
        500 — binding violation or unhandled internal error

    Note: A halted result (action == "halted") is returned as HTTP 200
    with the full orchestrator result dict. The caller reads
    result["action"] and result["reasonCode"] to determine outcome.
    Halted is a valid terminal state, not an error.
    """
    try:
        result = run_research_agent(
            ledger_root=request.ledger_root,
            env_path=request.env_path,
            mode=request.mode,
            run_id=request.run_id,
            seed=request.seed,
        )
        return RunResponse(status="success", result=result)

    except ConcurrencyViolationError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "ConcurrencyViolationError",
                "message": str(exc),
            },
        )

    except LedgerNotReachableError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "LedgerNotReachableError",
                "message": str(exc),
            },
        )

    except BindingViolationError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "BindingViolationError",
                "message": str(exc),
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": type(exc).__name__,
                "message": str(exc),
            },
        )


@app.get("/runs")
def get_runs(
    ledger_root: str = Query(..., description="Absolute path to ledger root directory"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries to return"),
) -> dict:
    """Return invocation history from openclaw_invocation_log.jsonl.

    Reads the append-only JSONL log written by OpenClaw on every
    invocation. Returns entries in reverse chronological order
    (most recent first).

    Args:
        ledger_root: Absolute path to ledger root directory.
        limit:       Maximum number of entries to return (default 100).

    Returns:
        {
            "ledger_root": str,
            "total": int,
            "runs": list[dict]  — entries newest-first
        }

    Returns 404 if ledger_root does not exist.
    Returns empty runs list if log file does not exist yet
    (no invocations have been run).
    """
    root = Path(ledger_root)
    if not root.is_dir():
        raise HTTPException(
            status_code=404,
            detail={
                "error": "LedgerNotFound",
                "message": f"ledger_root does not exist: {ledger_root}",
            },
        )

    log_path = root / LOG_FILENAME
    if not log_path.exists():
        return {"ledger_root": ledger_root, "total": 0, "runs": []}

    entries: list[dict] = []
    raw_lines = log_path.read_text(encoding="utf-8").splitlines()
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            # Skip malformed lines — never crash on log read
            continue

    # Reverse so newest entry is first
    entries.reverse()

    return {
        "ledger_root": ledger_root,
        "total": len(entries),
        "runs": entries[:limit],
    }


# ── Harvest runner ────────────────────────────────────────────────────────────

def run_harvest_process(run_id: str) -> None:
    """Spawn the TypeScript harvest engine in a background thread.

    Runs `npx tsx engines/deep-search/corpus-harvester/runHarvest.ts`
    from the project root. DEEPSEARCH_BASE_URL is forwarded so the
    harvest engine can reach the DeepSearch API on port 8001.
    """
    cmd = ["npx", "tsx", "engines/deep-search/corpus-harvester/runHarvest.ts"]

    env = os.environ.copy()
    env["DEEPSEARCH_BASE_URL"] = "http://localhost:8001"

    subprocess.run(
        cmd,
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
    )


@app.post("/run-harvest")
def run_harvest() -> dict:
    """Trigger the TypeScript harvest engine asynchronously.

    Starts a background thread that runs:
        npx tsx engines/deep-search/corpus-harvester/runHarvest.ts

    Returns immediately with a run_id and status 'running'.
    The harvest cycle executes in the background and writes packets
    to the NTI corpus without blocking the API server.

    Returns:
        {"run_id": str, "status": "running"}
    """
    run_id = str(uuid.uuid4())

    thread = threading.Thread(
        target=run_harvest_process,
        args=(run_id,),
        daemon=True,
    )
    thread.start()

    return {"run_id": run_id, "status": "running"}
