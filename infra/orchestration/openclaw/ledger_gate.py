"""
openclaw/ledger_gate.py

Ledger path accessibility gate for OpenClaw.

Contract authority: contracts_md/OPENCLAW-RUNTIME-CONTRACT.md v1.0 §V

Enforces ledger-first startup by verifying the ledger directory and
global_state.json are reachable before the orchestrator is invoked.

This gate operates at the path level only:
    - It checks existence, not content.
    - It does not read or parse any ledger file.
    - It does not cache any state.

The orchestrator's preflight_read() remains the authoritative source
for ledger state validation. This gate exists to fail loudly at the
OpenClaw boundary rather than deep inside the orchestrator.

Layers:
    Layer 1 — InvocationParams: parameter shape validation (Step 4)
    Layer 2 — assert_ledger_reachable: path accessibility (this file)
    Layer 3 — orchestrator.preflight_read: ledger state validation
"""

from __future__ import annotations

from pathlib import Path


class LedgerNotReachableError(RuntimeError):
    """Raised when the ledger is not accessible at the OpenClaw boundary.

    Indicates that ledger_root does not exist as a directory, or that
    global_state.json is not present inside it. The orchestrator will
    not be invoked.

    This error is raised before orchestrator_run() is called.
    It does not indicate a ledger state error — only a path
    accessibility failure.
    """


def assert_ledger_reachable(ledger_root: str) -> None:
    """Verify the ledger directory and global_state.json are reachable.

    Performs path-level existence checks only. Does not open, read, or
    parse any file. Does not cache any state (INV-1).

    Called after InvocationParams validation and before orchestrator_run.
    Fails loudly at the OpenClaw boundary rather than deep inside the
    orchestrator's preflight sequence.

    Args:
        ledger_root: Absolute path to the ledger root directory.
                     Must be a non-empty string (already validated by
                     InvocationParams before this is called).

    Raises:
        LedgerNotReachableError: ledger_root is not an existing directory.
        LedgerNotReachableError: global_state.json is not present in
            ledger_root.

    Contract: this function does not read file contents. It checks
    path existence only (§V: OpenClaw must not pre-read ledger state).
    """
    root = Path(ledger_root)

    if not root.is_dir():
        raise LedgerNotReachableError(
            f"ledger_root is not an existing directory: '{ledger_root}'. "
            "The orchestrator cannot be invoked without a reachable ledger. "
            "Verify the path and ensure the ledger has been initialized."
        )

    global_state_path = root / "global_state.json"
    if not global_state_path.exists():
        raise LedgerNotReachableError(
            f"global_state.json not found in ledger_root: '{ledger_root}'. "
            "The orchestrator requires global_state.json to be present. "
            "Verify the ledger has been initialized before invoking OpenClaw."
        )
