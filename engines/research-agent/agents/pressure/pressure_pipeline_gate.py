"""
pressure/pressure_pipeline_gate.py

Pressure Lane Pipeline Gate — Phase 7.7

Single-entry runner that chains the pressure lane stages in mandatory
contract order:

    PLO-1.0 → SSI → 2A → [PSAR Validation] → PSCA → passed PSARs

The gate enforces stage ordering (INV-4), collects all rejections and
audit logs, and short-circuits cleanly at each stage boundary if no
records survive to the next stage.

Does NOT:
    - Mint canonical IDs (PSTA responsibility)
    - Transform or modify stage outputs
    - Call PSTA, CIV, or Registry Commit (orchestrator responsibilities)
    - Maintain state across calls

Pipeline position:
    PLO-E output → this gate → PSTA (for PASS PSARs)

Contract authority:
    ORCHESTRATOR-EXECUTION-CONTRACT.md §XIV (canonical pressure lane order)
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0 §II (pipeline position)
    PRESSURE-SIGNAL-CRITIC-AGENT.md v2.0 §X (placement rules)
    STRUCTURAL-ASSEMBLER-CONTRACT.md v1.1 §II (position in pipeline)

Invariant compliance:
    INV-1: Pure function. No module-level mutable state.
    INV-2: No canonical IDs computed or referenced.
    INV-3: Input PLO dict never mutated. Stage outputs forwarded as-is.
    INV-4: Stage call order is fixed and enforced. PSCA never receives
           unvalidated PSARs. Downstream stages not called if inputs
           are empty.
    INV-5: Deterministic. Identical input always produces identical output.
           No timestamps, UUIDs, or runtime-derived values introduced.
"""

from __future__ import annotations

from engines.research_agent.agents.pressure.pressure_pipeline_schema import (
    PRESSURE_PIPELINE_GATE_VERSION,
    PSAR_GATE_VALIDATION_SCHEMA_VERSION,
    REJECT_PSAR_GATE_SCHEMA_INVALID,
)
from engines.research_agent.agents.pressure.ssi import enforce_ssi
from engines.research_agent.agents.pressure.assembler_2a import enforce_assembler_2a
from engines.research_agent.agents.pressure.psar_validator import validate_psar, PSARSchemaValidationError
from engines.research_agent.agents.pressure.psca import enforce_psca
from engines.research_engine.agent_runtime.agent_packet import AgentRunPacket
from engines.research_engine.agent_runtime.agent_registry import get_agent, register_default_agents


def enforce_pressure_pipeline(
    plo: dict,
    cycle_metadata: dict,
) -> tuple[list[dict], list[dict], dict]:
    register_default_agents()
    packet = AgentRunPacket(
        run_id=str(plo.get("sourceSeedId", "")) if isinstance(plo, dict) else "",
        stage="pressure_pipeline",
        agent_name="pressure",
        payload={
            "plo": plo,
            "cycle_metadata": cycle_metadata,
        },
        metadata={},
    )
    packet.validate()
    result = get_agent(packet.agent_name).run(packet)
    return (
        list(result.output.get("passed_psars", [])),
        list(result.output.get("all_rejections", [])),
        dict(result.output.get("composite_audit", {})),
    )


def _run_pressure_pipeline_impl(
    plo: dict,
    cycle_metadata: dict,
) -> tuple[list[dict], list[dict], dict]:
    """
    Run a PLO-1.0 object through the full pressure lane pipeline.

    Executes stages in mandatory contract order:
        SSI → 2A → PSAR Validation → PSCA

    Short-circuits at each stage boundary if no records survive to pass
    to the next stage. Collects all rejections and audit logs across all
    reached stages.

    Args:
        plo:            A validated PLO-1.0 dict from PLO-E.
                        Must contain: sourceSeedId, schemaVersion, observations.
                        Never mutated (INV-3).
        cycle_metadata: Orchestrator-provided cycle context.
                        Must contain: season, phase, week.

    Returns:
        3-tuple:
            passed_psars   : list[dict] — Post-critic PSARs with
                             criticStatus="PASS". Ready for PSTA.
            all_rejections : list[dict] — All rejection records from
                             all reached stages, in pipeline order:
                               [ssi_rejections,
                                assembler_rejections,
                                psar_validation_rejections,
                                psca_rejected_psars]
            composite_audit: dict — Stage-keyed audit logs.
                             Keys present only for stages that were reached:
                               "ssi"         → SSI audit log
                               "assembler_2a" → 2A audit log
                               "psca"         → PSCA audit log

    Short-circuit conditions:
        - SSI produces no plo2_records → return before 2A
        - 2A produces no psar_records  → return before PSAR validation
        - PSAR validation passes no PSARs → return before PSCA

    Determinism (INV-5):
        Given identical (plo, cycle_metadata), produces identical output.
        All stage functions are deterministic.
    """
    composite_audit: dict = {}
    all_rejections:  list[dict] = []

    # ── Stage 1: Structural Signal Interpreter (SSI) ───────────────────────────
    # Extracts (actorGroup_raw, action_raw, objectRole_raw) from each
    # PLO-1.0 observation and emits PLO-2.0 records.
    plo2_records, ssi_rejections, ssi_audit = enforce_ssi(plo, cycle_metadata)
    composite_audit["ssi"] = ssi_audit
    all_rejections.extend(ssi_rejections)

    if not plo2_records:
        return [], all_rejections, composite_audit

    # ── Stage 2: 2A PSAR Assembler ─────────────────────────────────────────────
    # Normalizes enums, clusters by (actorGroup, actionType, objectRole),
    # derives cluster signatures, and emits pre-critic PSAR v1.0 records.
    psar_records, assembler_rejections, assembler_audit = enforce_assembler_2a(
        plo2_records, cycle_metadata
    )
    composite_audit["assembler_2a"] = assembler_audit
    all_rejections.extend(assembler_rejections)

    if not psar_records:
        return [], all_rejections, composite_audit

    # ── Stage 3: PSAR Schema Validation ───────────────────────────────────────
    # Validates each PSAR against schema, enum membership, and derived-field
    # consistency before it reaches PSCA.
    # PSARs that fail validation are excluded from PSCA input and logged here.
    # PSCA must never receive a structurally invalid PSAR.
    valid_psars:      list[dict] = []
    validation_rejections: list[dict] = []

    for psar in psar_records:
        try:
            validate_psar(psar)
            valid_psars.append(psar)
        except PSARSchemaValidationError as exc:
            validation_rejections.append(_make_psar_gate_rejection(psar, str(exc)))

    all_rejections.extend(validation_rejections)

    if not valid_psars:
        return [], all_rejections, composite_audit

    # ── Stage 4: PSCA Critic Agent ─────────────────────────────────────────────
    # Evaluates each valid PSAR against structural sanity gates:
    #   Step 1: clusterSize >= MIN_CLUSTER_SIZE
    #   Step 2: domainDiversityCount >= MIN_DOMAIN_DIVERSITY
    # Returns passed PSARs (criticStatus=PASS) and rejected PSARs separately.
    passed_psars, psca_rejected_psars, psca_audit = enforce_psca(valid_psars)
    composite_audit["psca"] = psca_audit
    all_rejections.extend(psca_rejected_psars)

    return passed_psars, all_rejections, composite_audit


# ── Internal helpers ───────────────────────────────────────────────────────────

def _make_psar_gate_rejection(psar: dict, reason: str) -> dict:
    """
    Construct a gate-level rejection record for a PSAR that failed
    validate_psar before reaching PSCA.

    The PSAR dict is included by reference (shallow copy not required —
    PSARs are already post-2A dicts not held by the caller at this point).

    Args:
        psar:   The PSAR dict that failed validation.
        reason: The PSARSchemaValidationError message.

    Returns:
        Gate rejection record dict.
    """
    return {
        "schemaVersion":  PSAR_GATE_VALIDATION_SCHEMA_VERSION,
        "reasonCode":     REJECT_PSAR_GATE_SCHEMA_INVALID,
        "reason":         reason,
        "proposalID":     psar.get("proposalID"),
        "pipelineGateVersion": PRESSURE_PIPELINE_GATE_VERSION,
    }
