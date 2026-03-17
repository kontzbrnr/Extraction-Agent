"""
pressure/psca.py

PSCA — Pressure Signal Critic Agent — Phase 7.6

Evaluates pre-critic PSAR v1.0 objects against structural sanity gates.
Appends verdict fields to a copy of each PSAR. Returns passed and rejected
records in separate lists.

Responsibilities:
    1. Malformed input exclusion (false enumComplianceFlags → no output)
    2. Step 1: Cluster size gate (clusterSize < MIN_CLUSTER_SIZE → REJECT)
    3. Step 2: Domain diversity gate (domainDiversityCount < MIN_DOMAIN_DIVERSITY → REJECT)
    4. Verdict field append (criticStatus, reasonCode, failureStage)
    5. pscaVersion population in agentVersionSnapshot
    6. Audit log emission

Does NOT:
    - Mint canonical CPS IDs (PSTA responsibility)
    - Normalize enums (2A responsibility)
    - Mutate input PSAR dicts (INV-3)
    - Apply narrative purity gates (eliminated by Ruling 2)
    - Issue COLLAPSE or RECLASSIFY verdicts (eliminated by Ruling 3)

Pipeline position: 2A → PSCA → PSTA

Contract authority:
    PRESSURE-SIGNAL-CRITIC-AGENT.md v2.0
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0
    Phase 7.6 Governing Rulings (verdict scope, input schema, gate set)

Invariant compliance:
    INV-1: Pure function. No module-level mutable state.
    INV-2: No canonical IDs minted, referenced, or precomputed.
    INV-3: Input PSAR dicts are never mutated. Post-critic objects are new dicts.
    INV-5: Deterministic. Gate order is fixed: Step 1 before Step 2.
           Identical input + constants → identical output.
"""

from __future__ import annotations

from engines.research_agent.agents.pressure.psca_schema import (
    PSCA_VERSION,
    MIN_CLUSTER_SIZE,
    MIN_DOMAIN_DIVERSITY,
    VERDICT_PASS,
    VERDICT_REJECT,
    REASON_PASS_ALL_CHECKS,
    REASON_REJECT_INSUFFICIENT_CLUSTER_SIZE,
    REASON_REJECT_INSUFFICIENT_DOMAIN_DIVERSITY,
    STAGE_1_CLUSTER_SIZE,
    STAGE_2_DOMAIN_DIVERSITY,
)
from engines.research_agent.agents.pressure.psca_audit_log import make_psca_audit_log


def enforce_psca(
    psar_records: list[dict],
) -> tuple[list[dict], list[dict], dict]:
    """
    PSCA structural sanity gate function.

    Evaluates each PSAR v1.0 record against cluster size and domain diversity
    thresholds. Appends verdict fields to a copy of each evaluable record.
    Malformed records (false enumComplianceFlags) are silently excluded per
    PSAR contract v1.0 §VII.

    Args:
        psar_records: List of pre-critic PSAR v1.0 dicts from assembler_2a.

    Returns:
        3-tuple:
            passed_psars  : list[dict] — Post-critic PSARs with criticStatus=PASS.
                            Ready for PSTA canonicalization.
            rejected_psars: list[dict] — Post-critic PSARs with criticStatus=REJECT.
                            Routed to PQG audit storage only.
            audit_log     : dict       — PSCA gate audit record (PSCA_AUDIT-1.0).

    Outcomes:
        EMPTY_INPUT — no PSAR records provided.
        PASS        — all evaluable records passed both gates.
        PARTIAL     — mixed pass/reject among evaluable records.
        REJECT_ALL  — all evaluable records rejected.

    Invariant (INV-5):
        Given identical psar_records and threshold constants, produces:
        - Identical verdict per record
        - Identical passed_psars and rejected_psars
        - Identical audit_log
    """
    # ── Stage 0: Empty input guard ─────────────────────────────────────────────
    if not psar_records:
        return [], [], make_psca_audit_log(
            input_count=0,
            malformed_count=0,
            pass_count=0,
            reject_count=0,
            decision="EMPTY_INPUT",
        )

    passed_psars:   list[dict] = []
    rejected_psars: list[dict] = []
    malformed_count: int = 0

    for psar in psar_records:

        # ── Stage 1: Malformed input exclusion ────────────────────────────────
        # PSAR contract v1.0 §VII: PSCA must treat PSARs with false
        # enumComplianceFlags as malformed — produce no output for these records.
        compliance_flags: dict = psar.get("enumComplianceFlags", {})
        if not all(compliance_flags.values()):
            malformed_count += 1
            continue

        cluster_size:          int = psar["clusterSize"]
        domain_diversity_count: int = psar["domainDiversityCount"]

        # ── Stage 2: Gate evaluation (fixed order — INV-5) ────────────────────

        # Step 1 — Cluster size gate
        # PSCA contract v2.0 §V.1️⃣
        if cluster_size < MIN_CLUSTER_SIZE:
            post_critic = _append_verdict(
                psar=psar,
                verdict=VERDICT_REJECT,
                reason_code=REASON_REJECT_INSUFFICIENT_CLUSTER_SIZE,
                failure_stage=STAGE_1_CLUSTER_SIZE,
            )
            rejected_psars.append(post_critic)
            continue

        # Step 2 — Domain diversity gate
        # PSCA contract v2.0 §V.2️⃣
        if domain_diversity_count < MIN_DOMAIN_DIVERSITY:
            post_critic = _append_verdict(
                psar=psar,
                verdict=VERDICT_REJECT,
                reason_code=REASON_REJECT_INSUFFICIENT_DOMAIN_DIVERSITY,
                failure_stage=STAGE_2_DOMAIN_DIVERSITY,
            )
            rejected_psars.append(post_critic)
            continue

        # All gates passed
        post_critic = _append_verdict(
            psar=psar,
            verdict=VERDICT_PASS,
            reason_code=REASON_PASS_ALL_CHECKS,
            failure_stage=None,
        )
        passed_psars.append(post_critic)

    # ── Stage 3: Audit log ─────────────────────────────────────────────────────
    pass_count   = len(passed_psars)
    reject_count = len(rejected_psars)
    evaluable    = pass_count + reject_count

    if evaluable == 0:
        decision = "REJECT_ALL"   # all inputs were malformed
    elif pass_count == 0:
        decision = "REJECT_ALL"
    elif reject_count == 0 and malformed_count == 0:
        decision = "PASS"
    else:
        decision = "PARTIAL"

    audit = make_psca_audit_log(
        input_count=len(psar_records),
        malformed_count=malformed_count,
        pass_count=pass_count,
        reject_count=reject_count,
        decision=decision,
    )

    return passed_psars, rejected_psars, audit


# ── Internal helpers ───────────────────────────────────────────────────────────

def _append_verdict(
    psar: dict,
    verdict: str,
    reason_code: str,
    failure_stage: str | None,
) -> dict:
    """
    Return a new dict containing all original PSAR fields plus verdict fields.

    The original psar dict is never mutated (INV-3).
    pscaVersion in agentVersionSnapshot is updated from "unknown" to PSCA_VERSION
    per PSAR contract v1.0 §VI (pscaVersion must be set post-critic).

    Verdict fields appended (PSAR contract v1.0 §IX):
        criticStatus  : PASS | REJECT
        reasonCode    : deterministic reason code
        failureStage  : which gate triggered verdict (None for PASS)
    """
    # Build updated agentVersionSnapshot with pscaVersion resolved
    original_snapshot: dict = psar.get("agentVersionSnapshot", {})
    updated_snapshot: dict = {**original_snapshot, "pscaVersion": PSCA_VERSION}

    # Construct post-critic PSAR as a new dict (INV-3 — no mutation)
    post_critic: dict = {
        **psar,
        "agentVersionSnapshot": updated_snapshot,
        "criticStatus":  verdict,
        "reasonCode":    reason_code,
        "failureStage":  failure_stage,
    }

    return post_critic
