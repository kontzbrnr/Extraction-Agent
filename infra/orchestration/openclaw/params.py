"""
openclaw/params.py

Formal validated input model for OpenClaw invocations.

Contract authority: contracts_md/OPENCLAW-RUNTIME-CONTRACT.md v1.0 §IV

Defines the minimum runtime input surface. No per-agent tuning is
exposed. No additional parameters are accepted beyond the five defined
here.

InvocationParams is the sole validated gate for all OpenClaw inputs.
It is constructed as the first operation inside run_research_agent.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvocationParams:
    """Validated, immutable model of the OpenClaw minimum input surface.

    Fields (§IV):
        ledger_root: Absolute path to the ledger root directory.
                     Must not be empty. The orchestrator reads all state
                     from this path unconditionally (§V). Not pre-read here.
        env_path:    Path to environment / repo root. Must not be empty.
                     Accepted for runtime context; not forwarded to the
                     orchestrator (orchestrator is ledger-driven).
        mode:        Execution mode. Must be "deterministic". Enforced at
                     construction. Any other value raises ValueError.
        run_id:      Optional season run identifier. Not forwarded to the
                     orchestrator (ledger-derived). May be None.
        seed:        Optional fixed seed for deterministic seeding.
                     Reserved for future use. Not forwarded to orchestrator.
                     May be None.

    This model is closed. No additional fields may be added without a
    contract amendment to OPENCLAW-RUNTIME-CONTRACT.md §IV.

    Raises:
        ValueError: ledger_root is empty.
        ValueError: env_path is empty.
        ValueError: mode is not "deterministic".
    """

    ledger_root: str
    env_path:    str
    mode:        str       = "deterministic"
    run_id:      str | None = None
    seed:        int | None = None

    # Sole permitted mode value — owned here, not in entrypoint.
    _PERMITTED_MODE: str = "deterministic"

    def __post_init__(self) -> None:
        if not self.ledger_root:
            raise ValueError(
                "ledger_root must not be empty. "
                "Provide the absolute path to the ledger root directory."
            )
        if not self.env_path:
            raise ValueError(
                "env_path must not be empty. "
                "Provide the path to the environment / repo root."
            )
        if self.mode != self._PERMITTED_MODE:
            raise ValueError(
                f"mode must be 'deterministic', got '{self.mode}'. "
                "Non-deterministic invocations are prohibited by "
                "OPENCLAW-RUNTIME-CONTRACT.md §IV."
            )
