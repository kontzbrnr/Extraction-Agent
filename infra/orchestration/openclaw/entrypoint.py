"""
openclaw/entrypoint.py

Single callable entrypoint for the research agent runtime.

Contract authority: contracts_md/OPENCLAW-RUNTIME-CONTRACT.md v1.0

Invocation rule (§II):
    run_research_agent() calls orchestrator_run() exactly once.
    No loops. No chaining. No internal retry.

Authority chain (§III):
    Only downstream call: orchestrator_run(ledger_root).
    No direct calls to PLO-E, IAV, PSTA, EMI, media mint, or CIV.

Input surface (§IV):
    ledger_root  — required
    env_path     — required
    mode         — required, must be "deterministic"
    run_id       — optional
    seed         — optional, reserved for future deterministic seeding

Ledger-first (§V):
    ledger_root is passed to orchestrator_run. The orchestrator reads
    all state from ledger unconditionally. No state is pre-read or
    passed here.
"""

from __future__ import annotations

import datetime

from infra.orchestration.openclaw.concurrency_guard import acquire_run_lock
from infra.orchestration.openclaw.invocation_logger import (
    compute_ledger_state_hash,
    make_failure_entry,
    make_success_entry,
    write_invocation_log,
)
from infra.orchestration.openclaw.ledger_gate import assert_ledger_reachable
from infra.orchestration.openclaw.params import InvocationParams
from infra.orchestration.runtime.orchestrator import orchestrator_run


def run_research_agent(
    ledger_root: str,
    env_path: str,
    mode: str = "deterministic",
    run_id: str | None = None,
    seed: int | None = None,
) -> dict:
    """Invoke one orchestrator action and return the execution result.

    This is the sole callable entrypoint for the research agent runtime.
    It enforces the OpenClaw runtime contract boundary:

        OpenClaw does not interpret.
        OpenClaw does not make ontology decisions.
        OpenClaw only triggers orchestrator actions.

    Args:
        ledger_root: Absolute path to the ledger root directory.
                     Passed directly to orchestrator_run. The orchestrator
                     reads all state from ledger unconditionally (§V).
        env_path:    Path to environment / repo root. Accepted for
                     runtime context but not forwarded to orchestrator
                     (orchestrator is ledger-driven, not env-driven).
        mode:        Execution mode. Must be "deterministic". Any other
                     value raises ValueError immediately (§IV).
        run_id:      Optional season run identifier. Reserved — not
                     forwarded to orchestrator_run (ledger-derived).
        seed:        Optional fixed seed. Reserved — not forwarded to
                     orchestrator_run (ledger-derived).

    Returns:
        The orchestrator result dict exactly as returned by
        orchestrator_run. Not modified, not filtered, not interpreted.

    Raises:
        ValueError: ledger_root is empty, env_path is empty, or mode is
            not "deterministic". Raised by InvocationParams (Step 4).
        LedgerNotReachableError: ledger_root directory or global_state.json
            not found. Raised by assert_ledger_reachable (Step 5).
        OSError: compute_ledger_state_hash cannot read global_state.json.
            Raised after assert_ledger_reachable, before orchestrator call.
        Any exception raised by orchestrator_run propagates unmodified.

    Contract: this function calls orchestrator_run() exactly once.
    No loop. No retry. No chaining (§II).
    """
    # §IV — Validate and freeze invocation parameters.
    # InvocationParams raises ValueError on empty paths or non-deterministic
    # mode. Construction is the first operation — no orchestrator call is
    # made before parameters are validated.
    params = InvocationParams(
        ledger_root=ledger_root,
        env_path=env_path,
        mode=mode,
        run_id=run_id,
        seed=seed,
    )

    # §V — Ledger-first gate.
    # Verify ledger_root directory and global_state.json are reachable
    # before invoking the orchestrator. Path check only — no content read.
    # Raises LedgerNotReachableError if the ledger cannot be reached.
    assert_ledger_reachable(params.ledger_root)

    # §VI — Single-writer enforcement.
    # Lock is acquired after path verification and held for the entire
    # orchestrator boundary: timestamp capture → orchestrator call →
    # log write → return. Raises ConcurrencyViolationError immediately
    # if another invocation is in progress.
    with acquire_run_lock(params.ledger_root):

        # §VI — Pre-invocation log capture.
        invocation_timestamp: str = (
            datetime.datetime.utcnow().isoformat() + "Z"
        )
        ledger_state_hash: str = compute_ledger_state_hash(params.ledger_root)

        # §III — Sole downstream call.
        try:
            execution_summary: dict = orchestrator_run(params.ledger_root)
        except Exception as exc:
            try:
                write_invocation_log(
                    params.ledger_root,
                    make_failure_entry(invocation_timestamp, ledger_state_hash, exc),
                )
            except OSError:
                pass
            raise

        # §VI — Log success.
        log_write_error: str | None = None
        try:
            write_invocation_log(
                params.ledger_root,
                make_success_entry(invocation_timestamp, ledger_state_hash, execution_summary),
            )
        except OSError as log_exc:
            log_write_error = str(log_exc)

        if log_write_error is not None:
            execution_summary = {**execution_summary, "logWriteError": log_write_error}

        return execution_summary
