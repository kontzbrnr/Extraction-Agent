from __future__ import annotations

import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.orchestration.runtime.run_models import RunRecord, RunStatus


os.makedirs("runtime/runs", exist_ok=True)

_RUNS_ROOT = Path("runtime") / "runs"


class DuplicateRunError(Exception):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_run_dir(run_id: str) -> Path:
    run_dir = _RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _write_json(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(content, file, indent=2, sort_keys=True)


def create_run_directory(run_id: str) -> None:
    run_dir = _RUNS_ROOT / run_id
    if run_dir.exists():
        raise DuplicateRunError(f"Run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)


def write_packet(run_id: str, packet) -> None:
    run_dir = _ensure_run_dir(run_id)
    _write_json(run_dir / "packet.json", packet.to_dict())


def _run_record_to_dict(run_record: Any) -> dict[str, Any]:
    if isinstance(run_record, RunRecord):
        data = {
            "run_id": run_record.run_id,
            "status": run_record.status.value,
            "created_at": run_record.created_at,
            "updated_at": run_record.updated_at,
            "profile": run_record.profile,
            "entry_stage": run_record.entry_stage,
        }
    elif isinstance(run_record, dict):
        data = dict(run_record)
    else:
        raise TypeError("run_record must be a dataclass or dict")

    status = data.get("status")
    if isinstance(status, RunStatus):
        data["status"] = status.value
    elif not isinstance(status, str):
        raise TypeError("run_record.status must be RunStatus or str")

    return data


def create_run_record(run_record) -> None:
    record = _run_record_to_dict(run_record)
    run_id = record["run_id"]
    run_dir = _ensure_run_dir(run_id)
    _write_json(run_dir / "run_record.json", record)


def update_run_status(run_id: str, status: RunStatus) -> None:
    run_dir = _ensure_run_dir(run_id)
    record_path = run_dir / "run_record.json"
    if not record_path.exists():
        raise FileNotFoundError(f"Run record missing: {record_path}")

    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["status"] = status.value
    record["updated_at"] = _utc_now_iso()
    _write_json(record_path, record)


def write_run_result(run_id: str, result: dict[str, Any]) -> None:
    run_dir = _ensure_run_dir(run_id)
    _write_json(run_dir / "result.json", result)


def write_run_error(run_id: str, error: Exception) -> None:
    run_dir = _ensure_run_dir(run_id)
    _write_json(
        run_dir / "error.json",
        {
            "message": str(error),
            "type": error.__class__.__name__,
            "traceback": traceback.format_exc(),
        },
    )
