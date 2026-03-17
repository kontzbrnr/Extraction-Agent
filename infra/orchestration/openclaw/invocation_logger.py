"""
openclaw/invocation_logger.py

Execution logging for the OpenClaw invocation boundary.

Contract authority: contracts_md/OPENCLAW-RUNTIME-CONTRACT.md v1.0

For each OpenClaw invocation, logs:
    - invocation timestamp (UTC ISO-8601)
    - ledger state snapshot hash (SHA-256 of global_state.json bytes)
    - action selected (from orchestrator result)
    - batch id if created
    - result summary
    - error code if failure

Log destination: {ledger_root}/openclaw_invocation_log.jsonl
Format: one JSON object per line (JSON Lines).

The ledger state hash is computed from global_state.json bytes before
the orchestrator is called. It is for replay evidence only — it is
never passed to the orchestrator and does not substitute for the
orchestrator's own ledger reads (§V).

hashlib is used here for a logging hash at the OpenClaw boundary.
This is not canonical identity computation. The INV-2 prohibition
applies to the orchestrator layer, not to OpenClaw logging.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

LOG_FILENAME: str = "openclaw_invocation_log.jsonl"


def compute_ledger_state_hash(ledger_root: str) -> str:
    """Compute SHA-256 hash of global_state.json bytes for replay evidence.

    Reads the raw bytes of global_state.json. Does not parse or
    interpret the JSON content. The hash is a deterministic snapshot
    identifier for the ledger state at the moment of invocation.

    Args:
        ledger_root: Absolute path to the ledger root directory.
                     global_state.json must exist (confirmed by
                     assert_ledger_reachable before this is called).

    Returns:
        "sha256:<64-char-hex-digest>"

    Raises:
        OSError: global_state.json cannot be read.
    """
    path = Path(ledger_root) / "global_state.json"
    raw_bytes = path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    return f"sha256:{digest}"


def write_invocation_log(ledger_root: str, entry: dict) -> None:
    """Append one invocation log entry to openclaw_invocation_log.jsonl.

    Appends a single JSON line to the log file. Creates the file if it
    does not exist. Uses open("a") — not atomic_write_json, which
    overwrites rather than appends.

    Args:
        ledger_root: Absolute path to the ledger root directory.
        entry:       Log entry dict. Must be JSON-serialisable.

    Raises:
        OSError: Log file cannot be opened or written.
    """
    log_path = Path(ledger_root) / LOG_FILENAME
    line = json.dumps(entry, sort_keys=True, default=str) + "\n"
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()


def make_success_entry(
    timestamp: str,
    ledger_state_hash: str,
    execution_summary: dict,
) -> dict:
    """Build a success log entry from an orchestrator execution summary.

    Does not interpret the result — extracts named fields only.

    Args:
        timestamp:          UTC ISO-8601 string captured before invocation.
        ledger_state_hash:  SHA-256 of global_state.json pre-invocation.
        execution_summary:  Dict returned by orchestrator_run (unmodified).

    Returns:
        Log entry dict with fields:
            timestamp, ledgerStateHash, actionSelected, batchId,
            resultSummary, errorCode, invocationSuccess.
    """
    return {
        "timestamp":        timestamp,
        "ledgerStateHash":  ledger_state_hash,
        "status":           "success",
        "actionSelected":   execution_summary.get("action"),
        "batchId":          execution_summary.get("batchId"),
        "resultSummary": {
            "terminationStatus":    execution_summary.get("terminationStatus"),
            "microBatchCount":      execution_summary.get("microBatchCount"),
            "canonicalizedCount":   execution_summary.get("canonicalizedCount"),
            "rejectedCount":        execution_summary.get("rejectedCount"),
            "ntiEvaluationSkipped": execution_summary.get("ntiEvaluationSkipped"),
        },
        "errorCode":        execution_summary.get("reasonCode"),
        "invocationSuccess": execution_summary.get("action") != "halted",
    }


def make_failure_entry(
    timestamp: str,
    ledger_state_hash: str,
    exc: BaseException,
) -> dict:
    """Build a failure log entry from an unhandled orchestrator exception.

    Args:
        timestamp:         UTC ISO-8601 string captured before invocation.
        ledger_state_hash: SHA-256 of global_state.json pre-invocation.
        exc:               Exception raised by orchestrator_run.

    Returns:
        Log entry dict with invocationSuccess=False and errorCode set to
        the exception class name.
    """
    return {
        "timestamp":        timestamp,
        "ledgerStateHash":  ledger_state_hash,
        "status":           "failure",
        "actionSelected":   None,
        "batchId":          None,
        "resultSummary":    None,
        "errorCode":        type(exc).__name__,
        "invocationSuccess": False,
    }
