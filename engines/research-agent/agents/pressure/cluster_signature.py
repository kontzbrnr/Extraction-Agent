"""
pressure/cluster_signature.py

Cluster Signature Construction — Phase 7.4

Pure function for deriving the deterministic SHA-256 cluster signature
from normalized PSAR structural fields.

No canonical IDs. No registry access. No state.

Contract authority:
    Structural Assembler Contract v1.1 §IV.3 (signature construction)
    Investigation Report 2026-03-07

Invariant compliance:
    INV-1: Pure function. No module-level mutable state.
    INV-2: No canonical CPS ID usage. proposalID is assigned by assembler_2a.py,
           not here. clusterSignature is a content-derived structural fingerprint.
    INV-5: Deterministic. domainSet must be sorted before passing.
           Full SHA-256 hexdigest (64 hex chars). No truncation.
"""

from __future__ import annotations
import hashlib


CLUSTER_SIGNATURE_PREFIX: str = "SIG_"


def derive_cluster_signature(
    actor_group: str,
    action_type: str,
    object_role: str,
    domain_set: list[str],
) -> str:
    """
    Derive a deterministic SHA-256 cluster signature.

    Input fields are joined with "|" in order:
        actor_group | action_type | object_role | domain[0] | domain[1] | ...

    domain_set MUST be sorted by the caller before passing.
    This function does not re-sort — sorting responsibility stays with
    the caller to keep this function's contract explicit.

    Args:
        actor_group : Normalized cast_requirement enum token (e.g., "coach")
        action_type : Normalized snake_case action string (e.g., "retained_control")
        object_role : Normalized snake_case object string (e.g., "play_calling")
        domain_set  : Sorted list of normalized pressure_signal_domain tokens
                      (e.g., ["authority_distribution", "timing_horizon"])

    Returns:
        "SIG_" + full 64-character SHA-256 hexdigest (no truncation).

    Example:
        derive_cluster_signature(
            "coach", "retained_control", "play_calling",
            ["authority_distribution"]
        )
        → "SIG_<64 hex chars>"

    Invariant:
        INV-5: Given identical inputs in identical order, always returns
        identical output. No randomness. No entropy sources.
    """
    sig_raw = "|".join([actor_group, action_type, object_role] + domain_set)
    return CLUSTER_SIGNATURE_PREFIX + hashlib.sha256(
        sig_raw.encode("utf-8")
    ).hexdigest()
