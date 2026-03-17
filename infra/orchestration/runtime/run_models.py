from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RunStatus(Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class RunRequest:
    profile: str
    entry_stage: str
    payload: dict


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    status: RunStatus
    created_at: str
    updated_at: str
    profile: str
    entry_stage: str
