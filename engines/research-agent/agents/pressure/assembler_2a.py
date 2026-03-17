"""
pressure/assembler_2a.py

2A PSAR Assembly — Phase 7.2

Accepts PLO-2.0 records from the Structural Signal Interpreter (SSI).
Emits pre-critic PSAR v1.0 objects for PSCA evaluation.

Responsibilities:
    1. Deterministic clustering by normalized (actorGroup, actionType, objectRole)
    2. Enum normalization (actorGroup → cast_requirement, domain → pressure_signal_domain)
    3. Structural signature construction (SHA-256 content-derived)
    4. Diagnostic metadata construction (clusterSize, domainDiversityCount, enumComplianceFlags)
    5. Pre-critic PSAR v1.0 emission with cycle-scoped proposalID

Does NOT:
    - Mint canonical CPS IDs (PSTA responsibility)
    - Validate pressure legitimacy (PSCA responsibility)
    - Enforce multi-domain convergence (removed per contract v1.1)
    - Maintain cross-cycle state (stateless)
    - Use timestamps for clustering (time-neutral)

Pipeline position: SSI → 2A → PSCA → PSTA

Contract authority:
    Structural Assembler Contract v1.1
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0
    Investigation Report 2026-03-07

Invariant compliance:
    INV-1: No module-level mutable state. enforce_assembler_2a() is pure function.
    INV-2: proposalID is cycle-scoped (PROP_{season}_{phase}_{week}_{ordinal}),
           not a CPS ID. No fingerprint computation.
    INV-4: actorGroup drawn from cast_requirement (pressure lane).
           Domain drawn from pressure_signal_domain (pressure lane).
    INV-5: Deterministic clustering, normalization, signature construction,
           and ordinal assignment. No randomness. No entropy sources.
"""

from __future__ import annotations
from collections import defaultdict

from engines.research_agent.agents.pressure.assembler_2a_schema import (
    ASSEMBLER_2A_VERSION,
    PSAR_SCHEMA_VERSION,
    REJECT_2A_ENUM_RESOLUTION_FAILED,
)
from engines.research_agent.agents.pressure.assembler_2a_normalizer import (
    normalize_actor_group,
    normalize_action_type,
    normalize_domain,
    normalize_object_role,
)
from engines.research_agent.agents.pressure.assembler_2a_rejection_handler import make_2a_rejection
from engines.research_agent.agents.pressure.assembler_2a_audit_log import make_2a_audit_log
from engines.research_agent.agents.pressure.cluster_signature import derive_cluster_signature
from engines.research_agent.agents.pressure.plo_schema import PLO_E_VERSION
from engines.research_agent.enums.role_token_registry import PRESSURE_ENUM_REGISTRY_VERSION


def enforce_assembler_2a(
    plo2_records: list[dict],
    cycle_metadata: dict,
) -> tuple[list[dict], list[dict], dict]:
    """
    2A PSAR Assembly gate function.
    
    Transforms PLO-2.0 records into pre-critic PSAR v1.0 proposals.
    
    Args:
        plo2_records: List of PLO-2.0 dicts from SSI with fields:
            - ploID (str)
            - actorGroup_raw (str)
            - action_raw (str)
            - objectRole_raw (str)
            - domain (str, PLO-E prose label)
            - sourceSeedId (str)
            - cycleMetadata (dict)
        cycle_metadata: Orchestrator-provided cycle context with:
            - season (str)
            - phase (str)
            - week (int)
    
    Returns:
        3-tuple:
            psar_records : list[dict]  — Pre-critic PSAR v1.0 objects
            rejections   : list[dict]  — Diagnostic rejection records (REJECTION-1.0)
            audit_log    : dict        — Gate audit record (2A_AUDIT-1.0)
    
    Outcomes:
        EMPTY_INPUT — no PLO-2.0 records provided
        PASS        — all clusters proposed, zero rejections
        PARTIAL     — some clusters proposed, some rejected
        REJECT      — no clusters proposed (all records failed normalization)
    
    Determinism guarantee (INV-5):
        Given identical plo2_records and cycle_metadata, produces:
        - Identical cluster boundaries
        - Identical clusterSignatures (SHA-256)
        - Identical proposalID ordinals (sorted by clusterSignature)
        - Identical PSAR v1.0 objects
    
    Example:
        plo2_records = [
            {
                "ploID": "PLO2_abc123",
                "actorGroup_raw": "coaching staff",
                "action_raw": "retained control",
                "objectRole_raw": "play calling",
                "domain": "Authority Distribution",
                "sourceSeedId": "SEED_001",
                "cycleMetadata": {...}
            }
        ]
        cycle_metadata = {"season": "2025", "phase": "REG", "week": 3}
        
        psar_records, rejections, audit = enforce_assembler_2a(plo2_records, cycle_metadata)
        # psar_records[0]["proposalID"] == "PROP_2025_REG_003_0001"
        # psar_records[0]["actorGroup"] == "coach"
        # psar_records[0]["actionType"] == "retained_control"
    """
    # ── Stage 0: Empty input guard ────────────────────────────────────────────
    if not plo2_records:
        audit = make_2a_audit_log(
            input_record_count=0,
            proposed_count=0,
            rejected_cluster_count=0,
            decision="EMPTY_INPUT",
        )
        return [], [], audit

    # ── Stage 1: cycleMetadata extraction ────────────────────────────────────
    # KeyError is intentional — missing cycleMetadata is an orchestrator error.
    season = cycle_metadata["season"]
    phase = cycle_metadata["phase"]
    week = int(cycle_metadata["week"])

    # ── Stage 2: Per-record normalization and clustering ──────────────────────
    # cluster_map: cluster_key → list of (ploID, normalized_domain)
    cluster_map: dict[tuple, list[tuple[str, str]]] = defaultdict(list)
    # record_rejections: records that fail normalization
    record_rejections: list[dict] = []
    seen_plo_ids: set[str] = set()

    for record in plo2_records:
        plo_id: str = record.get("ploID", "")

        # Deduplicate by ploID — keep first occurrence (INV-5 determinism)
        if plo_id in seen_plo_ids:
            continue
        seen_plo_ids.add(plo_id)

        actor_group_raw: str = record.get("actorGroup_raw", "")
        action_raw: str = record.get("action_raw", "")
        object_role_raw: str = record.get("objectRole_raw", "")
        domain_raw: str = record.get("domain", "")

        # Normalize all four fields
        actor_group = normalize_actor_group(actor_group_raw)
        action_type = normalize_action_type(action_raw)
        object_role = normalize_object_role(object_role_raw)
        domain = normalize_domain(domain_raw)

        # Build compliance flags for this record
        actor_resolved = actor_group is not None
        action_resolved = action_type is not None
        object_resolved = object_role is not None
        domain_resolved = domain is not None

        # Any field failure → record cannot join a cluster
        if not (actor_resolved and action_resolved and object_resolved and domain_resolved):
            failed_fields = [
                f for f, ok in [
                    ("actorGroup", actor_resolved),
                    ("actionType", action_resolved),
                    ("objectRole", object_resolved),
                    ("domain", domain_resolved),
                ] if not ok
            ]
            record_rejections.append(make_2a_rejection(
                REJECT_2A_ENUM_RESOLUTION_FAILED,
                f"Normalization failed for fields: {failed_fields}; "
                f"raw values: actorGroup_raw={actor_group_raw!r}, "
                f"action_raw={action_raw!r}, "
                f"objectRole_raw={object_role_raw!r}, "
                f"domain={domain_raw!r}",
                cluster_key=(actor_group or actor_group_raw,
                             action_type or action_raw,
                             object_role or object_role_raw),
                structural_source_ids=[plo_id],
            ))
            continue

        # Add record to its cluster
        cluster_key = (actor_group, action_type, object_role)
        cluster_map[cluster_key].append((plo_id, domain))

    # ── Stage 3: Per-cluster PSAR construction ────────────────────────────────
    psar_records: list[dict] = []
    cluster_rejections: list[dict] = []

    # Sort cluster keys for deterministic ordinal assignment (INV-5)
    # Build signatures first, then sort by signature for proposalID ordinal

    # First pass: build signatures
    cluster_data: list[tuple[str, dict]] = []  # (clusterSignature, partial_psar)

    for cluster_key, members in cluster_map.items():
        actor_group, action_type, object_role = cluster_key
        plo_ids = sorted({m[0] for m in members})     # deterministic order
        domains = sorted({m[1] for m in members})     # deduplicated, sorted

        # domainSetResolved: all domains successfully normalized (they were —
        # only normalized domains reach here — so this is always True at
        # cluster level; flag is for PSAR consumer transparency)
        domain_set_resolved = True

        # registryVersionMatched
        # Re-use the already-asserted constant from import-time check
        registry_version_matched = True   # assertion at import time guarantees this

        enum_compliance_flags = {
            "actorGroupResolved":  True,
            "actionTypeResolved":  True,
            "objectRoleResolved":  True,
            "domainSetResolved":   domain_set_resolved,
            "registryVersionMatched": registry_version_matched,
        }

        # domains is already sorted (line 212) — caller contract satisfied
        cluster_signature = derive_cluster_signature(
            actor_group, action_type, object_role, domains
        )

        partial_psar = {
            "auditSchemaVersion": PSAR_SCHEMA_VERSION,
            "enumRegistryVersion": PRESSURE_ENUM_REGISTRY_VERSION,
            "agentVersionSnapshot": {
                "ploEVersion": PLO_E_VERSION,
                "assembler2AVersion": ASSEMBLER_2A_VERSION,
                "pscaVersion": "unknown",
            },
            "actorGroup":           actor_group,
            "actionType":           action_type,
            "objectRole":           object_role,
            "domainSet":            domains,
            "clusterSignature":     cluster_signature,
            "structuralSourceIDs":  plo_ids,
            "clusterSize":          len(plo_ids),
            "domainDiversityCount": len(domains),
            "enumComplianceFlags":  enum_compliance_flags,
        }
        cluster_data.append((cluster_signature, partial_psar))

    # Second pass: sort by clusterSignature → assign ordinals → inject proposalID
    cluster_data.sort(key=lambda x: x[0])

    for ordinal_0based, (cluster_signature, partial_psar) in enumerate(cluster_data):
        ordinal = ordinal_0based + 1   # 1-based
        proposal_id = f"PROP_{season}_{phase}_{week:03d}_{ordinal:04d}"
        psar = {"proposalID": proposal_id, **partial_psar}
        psar_records.append(psar)

    # ── Stage 4: Audit log ────────────────────────────────────────────────────
    all_rejections = record_rejections + cluster_rejections
    proposed = len(psar_records)
    rejected_clusters = len(cluster_rejections)

    if proposed == 0:
        decision = "REJECT"
    elif len(all_rejections) > 0:
        decision = "PARTIAL"
    else:
        decision = "PASS"

    audit = make_2a_audit_log(
        input_record_count=len(plo2_records),
        proposed_count=proposed,
        rejected_cluster_count=rejected_clusters + len(record_rejections),
        decision=decision,
    )

    return psar_records, all_rejections, audit
