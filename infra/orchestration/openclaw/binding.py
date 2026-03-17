"""
openclaw/binding.py

Explicit authority chain binding for the OpenClaw execution shell.

Contract authority: contracts_md/OPENCLAW-RUNTIME-CONTRACT.md v1.0 §III

OpenClaw's sole permitted downstream call is orchestrator_run().
All pipeline agents remain under orchestrator authority exclusively.
"""

from __future__ import annotations

# §III — The sole permitted downstream call from OpenClaw.
PERMITTED_ORCHESTRATOR_CALL: str = "orchestrator_run"

# §III — Agents that OpenClaw must never call directly.
# These remain exclusively under orchestrator authority.
FORBIDDEN_DIRECT_CALLS: frozenset[str] = frozenset({
    "plo_e",          # PLO-E — Pressure-Legible Observation Expansion
    "iav",            # IAV   — Identity Abstraction Validator
    "psta",           # PSTA  — Pressure Signal Transformation Agent
    "emi",            # EMI   — Event Material Identifier
    "media_mint",     # media mint
    "civ",            # CIV   — Canonical Integrity Validator
    "pressure",       # pressure pipeline (any module)
    "extraction",     # extraction agents
    "narrative",      # narrative agents
    "classification", # classification agents
})


class BindingViolationError(RuntimeError):
    """Raised when the openclaw namespace contains a forbidden downstream import.

    Indicates that a pipeline agent has been imported directly into the
    openclaw package, violating OPENCLAW-RUNTIME-CONTRACT.md §III.
    """


def verify_binding_integrity() -> None:
    """Verify that the openclaw package contains no forbidden direct imports.

    Inspects sys.modules for all openclaw-prefixed modules and checks
    that no attribute name in those modules matches a forbidden call target.

    This is a read-only check. It does not modify any state.

    Raises:
        BindingViolationError: A forbidden module name is found as an
            attribute in any openclaw module's namespace.

    Note: This check operates on attribute *names*, not values.
    Orchestrator result dicts containing lane-name strings as values
    are not in module namespaces and will not trigger this check.
    """
    import sys

    openclaw_modules = {
        name: mod
        for name, mod in sys.modules.items()
        if name.startswith("openclaw") and mod is not None
    }

    for module_name, module in openclaw_modules.items():
        module_dict = getattr(module, "__dict__", {})
        for attr_name in module_dict:
            attr_lower = attr_name.lower()
            for forbidden in FORBIDDEN_DIRECT_CALLS:
                if forbidden in attr_lower:
                    raise BindingViolationError(
                        f"Forbidden binding '{attr_name}' found in openclaw "
                        f"module '{module_name}'. Direct calls to "
                        f"'{forbidden}' are prohibited by "
                        f"OPENCLAW-RUNTIME-CONTRACT.md §III. "
                        f"These agents remain under orchestrator authority."
                    )
