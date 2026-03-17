"""
pressure/ssi.py

Structural Signal Interpreter — Phase 7.2

Transforms PLO-1.0 objects into PLO-2.0 records.
One PLO-2.0 record emitted per observation.
Deterministic. Stateless. INV-1, INV-2, INV-5 compliant.

cycleMetadata is orchestrator-supplied run context. SSI forwards it
opaquely without validation. Schema: {season, phase, week, cycleID}.

Pipeline position:
    PLO-E → SSI (this gate) → 2A (PSAR Assembly + Enum Normalization)

Contract authority:
    STRUCTURAL-SIGNAL-INTERPRETER.md

Invariant compliance:
    INV-1: No module-level mutable state. No instance state.
    INV-2: ploID = "PLO2_" + sha256hex. Not a CPS ID. No canonical logic.
    INV-5: SHA-256 is deterministic. spaCy dep parsing is deterministic for
           pinned model. hashlib is stdlib. No timestamps, UUIDs, randomness.
"""

from __future__ import annotations

import hashlib

from engines.research_agent.agents.pressure.ssi_audit_log import make_ssi_audit_log
from engines.research_agent.agents.pressure.ssi_extractor import extract_structural_fields
from engines.research_agent.agents.pressure.ssi_rejection_handler import make_ssi_rejection
from engines.research_agent.agents.pressure.ssi_schema import (
    PLO2_SCHEMA_VERSION,
    REJECT_PLO2_EXTRACTION_FAILED,
    REJECT_PLO2_INVALID_INPUT,
)


# ── Gate function ──────────────────────────────────────────────────────────────

def enforce_ssi(
    plo: dict,
    cycle_metadata: dict,
) -> tuple[list[dict], list[dict], dict]:
    """Apply SSI transformation to a single PLO-1.0 object.

    Produces zero or more PLO-2.0 records (one per successfully extracted
    observation) and zero or more rejection records.

    Args:
        plo:            A PLO-1.0 conformant dict. Must contain "sourceSeedId"
                        and "observations" (list).
        cycle_metadata: Opaque orchestrator-supplied run context dict.
                        Shallow-copied into each PLO-2.0 record. Not validated.

    Returns:
        A 3-tuple (plo2_records, rejections, audit_log) where:

        plo2_records : list[dict]  — PLO-2.0 records (may be empty)
        rejections   : list[dict]  — rejection records (may be empty)
        audit_log    : dict        — SSI_AUDIT-1.0 dict

        Outcomes:
            PASS    — all observations extracted; rejections is []
            PARTIAL — some extracted, some rejected
            REJECT  — nothing extracted (invalid input or all observations failed)

    INV-1: No state mutation. cycle_metadata is shallow-copied (INV-3).
    INV-2: ploID computed as "PLO2_" + SHA-256 hex. Not a canonical ID.
    INV-5: Deterministic. Identical (plo, cycle_metadata) always produces
           identical output. No timestamps, UUIDs, or randomness.
    """
    source_seed_id = plo.get("sourceSeedId")
    observations = plo.get("observations")

    # Stage 1: Input pre-check
    if (
        not source_seed_id
        or not isinstance(observations, list)
        or len(observations) == 0
    ):
        label = source_seed_id or "UNKNOWN"
        rejection = make_ssi_rejection(
            REJECT_PLO2_INVALID_INPUT,
            "PLO-1.0 missing required fields: sourceSeedId or observations",
            label,
        )
        audit = make_ssi_audit_log(
            source_seed_id=label,
            total_observations=0,
            extracted_count=0,
            rejected_count=1,
            decision="REJECT",
        )
        return [], [rejection], audit

    plo2_records: list[dict] = []
    rejections: list[dict] = []

    for obs in observations:
        domain: str | None = obs.get("domain")
        observation_text: str | None = obs.get("observation")

        if not domain or not observation_text:
            rejections.append(
                make_ssi_rejection(
                    REJECT_PLO2_EXTRACTION_FAILED,
                    "Observation entry missing domain or observation text",
                    source_seed_id,
                    domain=domain,
                )
            )
            continue

        # Stage 2: ploID — content-derived, replay-stable (INV-5)
        raw = f"{source_seed_id}|{domain}|{observation_text}"
        plo_id = "PLO2_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()

        # Stage 3: Deterministic extraction
        actor_group_raw, action_raw, object_role_raw = extract_structural_fields(
            observation_text
        )

        if actor_group_raw is None or action_raw is None or object_role_raw is None:
            rejections.append(
                make_ssi_rejection(
                    REJECT_PLO2_EXTRACTION_FAILED,
                    (
                        f"Extraction incomplete: "
                        f"actorGroup_raw={actor_group_raw!r}, "
                        f"action_raw={action_raw!r}, "
                        f"objectRole_raw={object_role_raw!r}"
                    ),
                    source_seed_id,
                    domain=domain,
                )
            )
            continue

        plo2_records.append(
            {
                "ploID": plo_id,
                "actorGroup_raw": actor_group_raw,
                "action_raw": action_raw,
                "objectRole_raw": object_role_raw,
                "domain": domain,
                "sourceSeedId": source_seed_id,
                "cycleMetadata": dict(cycle_metadata),  # shallow copy; INV-1
                "schemaVersion": PLO2_SCHEMA_VERSION,
            }
        )

    total = len(observations)
    extracted = len(plo2_records)
    rejected = len(rejections)

    if extracted == 0:
        decision = "REJECT"
    elif rejected > 0:
        decision = "PARTIAL"
    else:
        decision = "PASS"

    audit = make_ssi_audit_log(
        source_seed_id=source_seed_id,
        total_observations=total,
        extracted_count=extracted,
        rejected_count=rejected,
        decision=decision,
    )

    return plo2_records, rejections, audit
