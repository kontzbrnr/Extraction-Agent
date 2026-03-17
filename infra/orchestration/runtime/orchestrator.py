"""
orchestrator/orchestrator.py

Orchestrator — ledger-driven, stateless invocation controller.

Contract authority:
    contracts_md/ORCHESTRATOR-EXECUTION-CONTRACT.md v1.0
    contracts_md/ORCHESTRATOR-FINAL-REPORT-CONTRACT.md v1.0

Role (§I):
    Controller only. Reads ledger state, dispatches agents, commits
    canonical objects, checkpoints state, evaluates termination. Exits.

Prohibited (§I, §VIII):
    - Canonical ID derivation or fingerprint computation
    - Deduplication logic
    - Modification of worker outputs
    - Long-running loops or internal timers
    - Skipping ledger writes

Invocation model (§III, §X):
    One discrete invocation per trigger. Each invocation executes the
    full micro-batch flow (Steps 1–5) exactly once then exits.
    External scheduler drives the next invocation.

Implementation status:
    Step 1  (Preflight read)         — Phase 13.1 ✓
    Step 2  (Determine action)       — Phase 13.1 ✓
    Step 3  (Canonical pipeline)     — Phase 13.1 stub; commit wrapper Phase 13.4 ✓;
                                       retry envelope Phase 13.8 ✓
    Step 4  (End-of-batch boundary)  — Phase 13.1 ✓; Phase 13.5 checkpoint complete ✓
    Step 5  (Termination evaluation) — Phase 13.6 ✓ (NTI wired; exhaustion stub)

Invariant compliance:
    INV-1: No module-level mutable state. Ledger re-read unconditionally
           on every invocation and after every mutating operation.
    INV-2: No fingerprint computation. No canonical ID construction.
    INV-3: Canonical objects passed to commit layer exactly as emitted.
    INV-4: Lane isolation enforced at registry_writer layer.
    INV-5: sorted_lanes() called before first append_canonical_object()
           call — byte-identical JSON for identical input guaranteed.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from engines.research_agent.agents.civ.civ_schema import VALID_CIV_LANES
from engines.research_engine.agent_runtime.agent_packet import AgentRunPacket
from engines.research_engine.agent_runtime.agent_registry import get_agent, register_default_agents
from engines.research_engine.ledger.batch_collector import make_batch_collector
from engines.research_engine.ledger.global_state_manager import (
    LedgerState,
    PreflightError,
    preflight_read,
    read_season_state,
)
from engines.research_engine.ledger.registry_writer import RegistryAppendError, append_canonical_object
from engines.research_engine.ledger.rollback_handler import CrashRecoveryResult, handle_crash_recovery
from engines.research_agent.agents.pressure.psta_schema import STATUS_DUPLICATE
from infra.orchestration.nti.cycle_state_manager import NTIStateReadError
from infra.orchestration.nti.termination_evaluator import evaluate_termination
from infra.orchestration.runtime.run_packet import RunPacket
from engines.research_engine.ledger.season_state_manager import (
    BatchAlreadyInProgressError,
    clear_incomplete_batch_flag,
    increment_audit_cycle_count,
    increment_micro_batch_count,
    increment_retry_failure_count,
    mark_batch_start,
    set_termination_status,
    update_exhaustion_counters,
    update_subcategory_counts,
)


# ── Version ───────────────────────────────────────────────────────────────────

ORCHESTRATOR_VERSION: str = "ORCHESTRATOR-1.0"

# ── Termination status tokens (§V, §VII) ─────────────────────────────────────

_STATUS_SEALED:         str = "sealed"
_STATUS_EXHAUSTED:      str = "exhausted"
_STATUS_SYSTEM_FAILURE: str = "system_failure"

# Audit cycle interval — number of micro-batches between NTI audit cycles.
# Governance gap: no contract defines this value. Default: 1 (every batch).
# Pending governance ruling to introduce a non-unit interval.
AUDIT_CYCLE_INTERVAL: int = 1

# Valid action tokens (§III) — exhaustive set. Guard enforced after Step 2.
_VALID_ACTIONS: frozenset[str] = frozenset({"new_batch", "crash_recovery"})


register_default_agents()


# ── Public entry point ────────────────────────────────────────────────────────

def execute(packet: RunPacket):
    agent = get_agent(packet.agent_name)
    result = agent.run(packet)
    return result


def orchestrator_run(ledger_root: str) -> dict:
    """Execute one complete orchestrator invocation.

    Implements ORCHESTRATOR-EXECUTION-CONTRACT.md §IV (Micro-Batch
    Execution Flow), Steps 1–5.

    Args:
        ledger_root: Absolute path to the ledger root directory.
                     Must contain global_state.json.

    Returns:
        Status dict:
            {
                "orchestratorVersion": str,
                "action":              str,   # "new_batch" | "crash_recovery" | "halted"
                "terminationStatus":   str,
                "microBatchCount":     int | None,
                "canonicalizedCount":  int,
                "rejectedCount":       int,
            }
        On preflight failure:
            {
                "orchestratorVersion": str,
                "action":              "halted",
                "terminationStatus":   "blocked",
                "reasonCode":          str,
                "microBatchCount":     None,
                "canonicalizedCount":  0,
                "rejectedCount":       0,
            }

    Raises:
        BatchAlreadyInProgressError: mark_batch_start found flag already
            set after crash recovery — indicates recovery failure.
        RegistryAppendError:         duplicate canonical ID on commit.
        LedgerWriteMismatchError:    ledger write read-back mismatch.
        GlobalStateReadError:        global_state.json unreadable.
        SeasonStateReadError:        season state.json unreadable.

    INV-1: preflight_read() and every post-mutate read_season_state()
           issue unconditional disk reads. No cached state used.
    INV-2: No hashlib, no fingerprint call, no canonical ID construction.
    INV-3: Objects reach append_canonical_object() without mutation.
    INV-5: sorted_lanes() called before first append in _commit_batch().
    """
    # ── Step 1: Preflight read ────────────────────────────────────────────────
    try:
        ledger_state: LedgerState = preflight_read(ledger_root)
    except PreflightError as exc:
        return _build_halted_status(exc.reason_code)

    global_state    = ledger_state.global_state
    season_state    = ledger_state.season_state
    active_run_path = global_state["activeRunPath"]
    season          = season_state["season"]
    registry_path   = _registry_path(ledger_root, active_run_path)

    # ── Step 2: Determine action ──────────────────────────────────────────────
    # §VIII Hard fail on ambiguity: incompleteBatchFlag must be an exact bool.
    # Never guess: an else/default branch would silently treat None, strings,
    # or any unexpected value as "new_batch" — a canonical write on a guessed
    # action violates INV-3 and INV-5. Explicit three-way check enforces this.
    incomplete_flag = season_state.get("incompleteBatchFlag")

    if incomplete_flag is True:
        # §VI: Crash recovery — discard entire incomplete batch, reset flag.
        # INV-3: handle_crash_recovery never opens, reads, or writes
        # canonical_objects.json. Canonical objects committed before the
        # crash are valid and remain untouched in the registry.
        _crash_result: CrashRecoveryResult = handle_crash_recovery(
            ledger_root, active_run_path
        )
        action = "crash_recovery"

        # §VII: Retry envelope — each detected crash increments the failure count.
        # If this is the second crash (retryFailureCount reaches 2), transition
        # to system_failure and exit without starting a new batch.
        # Re-read after write (INV-1: pre-increment value is stale).
        increment_retry_failure_count(ledger_root, active_run_path)
        season_state = read_season_state(ledger_root, active_run_path)

        if season_state.get("retryFailureCount", 0) >= 2:
            # Terminal transition. Do NOT call mark_batch_start — the
            # incompleteBatchFlag is already False (cleared by crash recovery).
            set_termination_status(ledger_root, active_run_path, _STATUS_SYSTEM_FAILURE)
            season_state = read_season_state(ledger_root, active_run_path)
            return _build_run_status(
                action=action,
                season_state=season_state,
                canonical_count=0,
                rejected_count=0,
                batch_id=None,
            )
        # retryFailureCount < 2 — proceed with new batch (§VI: resume).

    elif incomplete_flag is False:
        action = "new_batch"

    else:
        # §VIII: incompleteBatchFlag is neither True nor False.
        # State is ambiguous — halt without writing any canonical state.
        # mark_batch_start is NOT called from this path.
        return _build_halted_status("AMBIGUOUS_LEDGER_STATE")

    # ── §III Single-action guard ──────────────────────────────────────────────
    # Contract: each invocation performs exactly one valid action.
    # Defensive check — action is always set above; this fires only if a future
    # code change introduces an unrecognized action token.
    if action not in _VALID_ACTIONS:
        return _build_halted_status("INVALID_ACTION")

    # Build cycle_snapshot for enforce_civ (keys: schemaVersion, enumVersion,
    # contractVersion — per civ/civ_schema.py REQUIRED_CYCLE_SNAPSHOT_KEYS).
    cycle_snapshot = _build_cycle_snapshot(global_state)

    # Derive deterministic batch_id from current ledger state.
    batch_id = _derive_batch_id(season, season_state["microBatchCount"])

    # Mark batch start BEFORE cluster processing — crash detection contract.
    # §IV Step 2: "Flag is persisted BEFORE any cluster processing begins."
    try:
        mark_batch_start(ledger_root, active_run_path, batch_id)
    except BatchAlreadyInProgressError:
        raise  # Do NOT swallow — indicates recovery failure.

    # Fresh batch collector — in-memory only, never cached at module level.
    collector = make_batch_collector(batch_id)

    # ── Step 3: Canonical pipeline processing ────────────────────────────────
    # §VII Retry Envelope: retry once on first exception; on second exception
    # increment retryFailureCount. If >= 2, transition to system_failure and
    # exit — _commit_batch and _end_of_batch_boundary are NOT called.
    # incompleteBatchFlag remains True on early exit so that crash recovery
    # detects the incomplete batch on the next invocation.
    try:
        _run_canonical_pipeline(
            ledger_root=ledger_root,
            active_run_path=active_run_path,
            season=season,
            batch_id=batch_id,
            cycle_snapshot=cycle_snapshot,
            collector=collector,
        )
    except Exception:
        # §VII: First failure — retry with fresh collector (INV-3: discard
        # any partial state accumulated in the failed collector).
        collector = make_batch_collector(batch_id)
        try:
            _run_canonical_pipeline(
                ledger_root=ledger_root,
                active_run_path=active_run_path,
                season=season,
                batch_id=batch_id,
                cycle_snapshot=cycle_snapshot,
                collector=collector,
            )
        except Exception:
            # §VII: Second failure — increment retryFailureCount and exit.
            # Re-read after write (INV-1: pre-increment value is stale).
            increment_retry_failure_count(ledger_root, active_run_path)
            season_state = read_season_state(ledger_root, active_run_path)
            if season_state.get("retryFailureCount", 0) >= 2:
                set_termination_status(
                    ledger_root, active_run_path, _STATUS_SYSTEM_FAILURE
                )
                season_state = read_season_state(ledger_root, active_run_path)
            # Exit without commit or end-of-batch boundary (§VII).
            # incompleteBatchFlag stays True — crash recovery handles next run.
            return _build_run_status(
                action=action,
                season_state=season_state,
                canonical_count=0,
                rejected_count=0,
                batch_id=batch_id,
            )

    # ── Step 4: End-of-batch boundary ────────────────────────────────────────
    committed_count, commit_rejected_count = _commit_batch(
        registry_path=registry_path,
        collector=collector,
        cycle_snapshot=cycle_snapshot,
    )
    _end_of_batch_boundary(ledger_root=ledger_root, active_run_path=active_run_path)

    # Re-read state after mutations (INV-1: never trust cached state).
    season_state = read_season_state(ledger_root, active_run_path)

    # ── Step 5: Termination evaluation ───────────────────────────────────────
    nti_skipped: bool = _evaluate_termination(
        ledger_root=ledger_root,
        active_run_path=active_run_path,
        season_state=season_state,
    )

    # Final re-read for accurate status report.
    season_state = read_season_state(ledger_root, active_run_path)

    return _build_run_status(
        action=action,
        season_state=season_state,
        canonical_count=committed_count,
        rejected_count=commit_rejected_count,
        nti_evaluation_skipped=nti_skipped,
        batch_id=batch_id,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _registry_path(ledger_root: str, active_run_path: str) -> Path:
    """Derive canonical_objects.json path from ledger structure (§IX)."""
    normalized = active_run_path.rstrip("/").rstrip("\\")
    return Path(ledger_root) / normalized / "canonical_objects.json"


def _derive_batch_id(season: str, micro_batch_count: int) -> str:
    """Derive batch_id per ORCHESTRATOR_INTEGRATION_GUIDE.md §1a.

    Format: BATCH_{season}_{microBatchCount:04d}
    Example: BATCH_2024_REG_0001

    INV-5: Deterministic — identical (season, micro_batch_count)
           always produces identical batch_id.
    """
    return f"BATCH_{season}_{micro_batch_count:04d}"


def _build_cycle_snapshot(global_state: dict) -> dict:
    """Construct the cycle_snapshot dict required by enforce_civ.

    Required keys (civ/civ_schema.py REQUIRED_CYCLE_SNAPSHOT_KEYS):
        schemaVersion, enumVersion, contractVersion

    Phase 13.1 stub resolved: fields are sourced directly from global_state.
    Missing fields raise KeyError — silent version substitution is prohibited
    (Audit 13.10 item 3: enum namespace collision).

    INV-5: Values must be stable for identical global_state input.
    """
    # KeyError is intentional: a missing version field must fail loudly.
    # Silent fallback substitution would cause CIV to validate against the
    # wrong enum namespace with no observable error (Audit 13.10 item 3).
    return {
        "schemaVersion":   global_state["schemaVersion"],
        "enumVersion":     global_state["enumVersion"],
        "contractVersion": global_state["contractVersion"],
    }


def _run_canonical_pipeline(
    ledger_root: str,
    active_run_path: str,
    season: str,
    batch_id: str,
    cycle_snapshot: dict,
    collector: object,
) -> None:
    """Run all canonical pipeline stages for one micro-batch.

    Stub — Phase 13.1 skeleton only. No-op.

    Full pipeline order per §XIV (Global Pipeline Ordering):
        1.  Extraction Agent
        2.  GSD — Global Split Doctrine
        3.  Seed Typing
        4.  PLO-E — Pressure-Legible Observation Expansion (pressure only)
        5.  2A — PSAR Assembly + Enum Normalization
        6.  PSCA — Pressure Signal Critic
        7.  PSTA — Canonical Mint + Dedup Resolution
        8.  CIV — enforce_civ() (validate, do not modify)
        9.  Registry Commit — via collector → _commit_batch()
        10. Cluster Engine
        11. PQG — Pipeline Quality Governor

    Contract prohibitions at this layer (§IV, §VIII):
        - No canonical ID generation or fingerprint computation (INV-2)
        - No deduplication logic (PSTA sole authority)
        - No modification of worker outputs (INV-3)
        - No ordering-dependent canonical identity (INV-5)

    Args:
        collector: BatchCollector instance. Call collector.add(lane, obj)
                   for each pipeline-output canonical object.
    """
    packets_path = Path(active_run_path) / "shared-corpus" / season
    packet_files = list(packets_path.glob("*.json"))

    for packet_file in packet_files:
        with open(packet_file, "r", encoding="utf-8") as handle:
            nti_doc = json.load(handle)

        result = subprocess.run(
            ["node", "dist/extraction/runExtraction.js"],
            input=json.dumps(nti_doc),
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            print("Extraction failed:", result.stderr)
            continue

        extraction_result = json.loads(result.stdout)

        for obj in extraction_result.get("pressureLane", {}).get("cpsObjects", []):
            collector.add("CPS", obj)

        for obj in extraction_result.get("narrativeLane", {}).get("csnObjects", []):
            collector.add("CSN", obj)


def _commit_canonical_object(
    obj: dict,
    lane: str,
    registry_path: Path,
    cycle_snapshot: dict,
) -> tuple[bool, dict | None]:
    """Sequence dedup → CIV → append for one canonical object.

    Pipeline order per §XIV (Global Pipeline Ordering):
        1. CPS dedup check    (CPS lane only — detect_cps_duplicate)
        2. CIV validation     (all CIV lanes — enforce_civ)
        3. Registry append    (append_canonical_object — only if steps pass)

    StructuralEnvironment lane:
        Skips both dedup check and CIV (not in VALID_CIV_LANES).
        append_canonical_object called directly.

    Args:
        obj:            Canonical object dict as emitted by transformation
                        agent. Never mutated (INV-3).
        lane:           Registry lane key. One of VALID_LANES.
        registry_path:  Path to canonical_objects.json.
        cycle_snapshot: Orchestrator cycle version snapshot dict.
                        Required keys: schemaVersion, enumVersion,
                        contractVersion.

    Returns:
        (True, None)            — object committed to registry.
        (False, rejection_dict) — object rejected at dedup or CIV stage.

    Raises:
        RegistryAppendError:      Duplicate ID that passed dedup check
                                  (contract violation — do NOT swallow).
        LedgerWriteMismatchError: Atomic write read-back failure.

    INV-2: No canonical ID derivation. detect_cps_duplicate receives
           canonical_id extracted from obj; this module does not compute it.
    INV-3: obj is never mutated before or after enforce_civ.
    INV-4: StructuralEnvironment bypasses CIV (not in VALID_CIV_LANES).
    INV-5: Fixed stage order — dedup before CIV before append.
    """
    # ── Step 1: CPS cross-run dedup gate ─────────────────────────────────
    # Only CPS lane has a registry-backed dedup module (Phase 8.3).
    # Other lanes rely on append_canonical_object RegistryAppendError
    # for duplicate detection.
    if lane == "CPS":
        canonical_id = obj.get("canonicalId", "")
        dedup_packet = AgentRunPacket(
            run_id=str(obj.get("batchId", "")),
            stage="cps_dedup",
            agent_name="pressure",
            payload={
                "canonical_id": canonical_id,
                "registry_path": str(registry_path),
            },
            metadata={"lane": lane},
        )
        dedup_packet.validate()
        dedup_result = get_agent(dedup_packet.agent_name).run(dedup_packet)
        dedup_status = dedup_result.output.get("status")
        if dedup_status == STATUS_DUPLICATE:
            return (False, {
                "rejected":    True,
                "reasonCode":  STATUS_DUPLICATE,
                "lane":        lane,
                "canonicalId": canonical_id,
                "stage":       "CPS_DEDUP",
            })

    # ── Step 2: CIV validation ────────────────────────────────────────────
    # StructuralEnvironment is not in VALID_CIV_LANES — skip CIV for it.
    if lane in VALID_CIV_LANES:
        packet = AgentRunPacket(
            run_id=str(obj.get("batchId", "")),
            stage="civ_validation",
            agent_name="civ",
            payload={
                "obj": obj,
                "lane": lane,
                "cycle_snapshot": cycle_snapshot,
            },
            metadata={"lane": lane},
        )
        packet.validate()
        agent = get_agent(packet.agent_name)
        result = agent.run(packet)
        passed = bool(result.output.get("passed", False))
        rejection = result.output.get("rejection")
        if not passed:
            return (False, rejection)

    # ── Step 3: Registry commit ───────────────────────────────────────────
    # RegistryAppendError propagates — indicates a contract violation
    # (duplicate that evaded dedup gate). Do NOT swallow.
    append_canonical_object(registry_path, lane, obj)
    return (True, None)


def _commit_batch(
    registry_path: Path,
    collector: object,
    cycle_snapshot: dict,
) -> tuple[int, int]:
    """Commit all CIV-validated objects from collector to canonical registry.

    Implements ORCHESTRATOR_INTEGRATION_GUIDE.md §2 (At Batch Boundary).

    Order of operations:
        1. collector.sorted_lanes() — sort by lane name (INV-5)
        2. _commit_canonical_object() per object — dedup → CIV → append

    Returns:
        (committed_count, rejected_count)

    INV-3: Objects passed through without mutation.
    INV-4: Lane isolation enforced at append_canonical_object() layer.
    INV-5: sorted_lanes() before first write ensures byte-identical JSON.

    Raises:
        RegistryAppendError: Duplicate canonical ID (contract violation).
        LedgerWriteMismatchError: Read-back mismatch after atomic write.
    """
    committed: int = 0
    rejected:  int = 0
    sorted_results = collector.sorted_lanes()
    for lane, objects in sorted_results.items():
        for obj in objects:
            ok, _ = _commit_canonical_object(obj, lane, registry_path, cycle_snapshot)
            if ok:
                committed += 1
            else:
                rejected += 1
    return committed, rejected


def _end_of_batch_boundary(ledger_root: str, active_run_path: str) -> None:
    """Perform end-of-batch checkpoint.

    Implements §IV Step 4 (complete):
        1. Increment microBatchCount
        2. If audit interval reached → increment auditCycleCount
        3. Update subcategoryCounts       (stub: {} until NTI wired)
        4. Update exhaustionCounters      (stub: {} until NTI wired)
        5. Clear incompleteBatchFlag      (MUST be last — crash safety)

    Contract: checkpoint MUST occur before termination evaluation (§IV).

    INV-1: read_season_state called after increment_micro_batch_count to
           get the post-increment microBatchCount for the interval check.
           No cached state used across calls.
    INV-5: clear_incomplete_batch_flag is unconditionally last — ordering
           is fixed. A crash between any earlier write and this call is
           detectable on the next invocation.

    Stubs (Phase 13.x — NTI wiring):
        auditCycleCount fires every batch (AUDIT_CYCLE_INTERVAL == 1).
        NTI audit result (exhaustion_triggered) deferred.
        subcategoryCounts and exhaustionCounters deltas deferred.
    """
    # Step 1 — Increment microBatchCount.
    increment_micro_batch_count(ledger_root, active_run_path)

    # Re-read after increment (INV-1: post-increment count required for
    # interval check; cached pre-increment value would be off-by-one).
    season_state = read_season_state(ledger_root, active_run_path)

    # Step 2 — Audit interval gate.
    if season_state["microBatchCount"] % AUDIT_CYCLE_INTERVAL == 0:
        increment_audit_cycle_count(ledger_root, active_run_path)

    # Step 3 — Update subcategoryCounts.
    # Stub: NTI-produced surface coverage delta is {} until NTI wired.
    update_subcategory_counts(ledger_root, active_run_path, {})

    # Step 4 — Update exhaustionCounters.
    # Stub: NTI-produced exhaustion delta is {} until NTI wired.
    update_exhaustion_counters(ledger_root, active_run_path, {})

    # Step 5 — Clear incompleteBatchFlag (MUST be last — crash safety).
    # This is the crash-detection sentinel. Any failure before this line
    # leaves the flag set, and the next invocation detects incomplete batch.
    clear_incomplete_batch_flag(ledger_root, active_run_path)


def _evaluate_termination(
    ledger_root: str,
    active_run_path: str,
    season_state: dict,
) -> bool:
    """Evaluate termination conditions and transition status if met.

    Implements §V (Termination Evaluation) and §VII (Retry Envelope).

    Evaluation order (priority):
        1. §VII Retry gate: retryFailureCount >= 2 → "system_failure" → return
           (Early return required: evaluate_termination must NOT be called
           after set_termination_status — terminal→terminal transition raises
           InvalidTerminationTransitionError.)
        2. §V NTI evaluation: evaluate_termination(exhaustion_triggered=False)
           (exhaustion_triggered stub — Phase 13.x when NTI audit wired.)

    NTI state fallback:
        If nti_state.json is absent (NTIStateReadError), NTI evaluation is
        silently skipped. terminationStatus remains "running". This is the
        correct stub behavior pending NTI state initialization (Phase 13.x).

    Returns:
        False — NTI evaluation was called (regardless of outcome).
        True  — NTIStateReadError was raised; evaluation was skipped.
                Caller must surface this via the returned status dict so
                that downstream consumers can distinguish "NTI confirmed
                running" from "NTI state absent" (Audit 13.10 items 4, 6).

    Args:
        season_state: Season state dict as read from disk AFTER checkpoint.
                      Must be a fresh disk read (INV-1). Used only for the
                      retry gate — evaluate_termination re-reads ledger
                      internally (INV-1).

    INV-1: evaluate_termination calls preflight_read and get_sealed_surfaces
           unconditionally. No cached state is introduced here.
    INV-5: Retry gate checked before NTI evaluation — order is fixed.
    """
    # §VII — Retry failure gate (checked first; early return on terminal write).
    if season_state.get("retryFailureCount", 0) >= 2:
        set_termination_status(ledger_root, active_run_path, _STATUS_SYSTEM_FAILURE)
        return False

    # §V — NTI-driven termination evaluation.
    # evaluate_termination writes terminationStatus internally when sealed
    # or exhausted — orchestrator must not call set_termination_status after.
    # exhaustion_triggered=False until NTI audit is wired (Phase 13.x).
    try:
        evaluate_termination(
            ledger_root,
            active_run_path,
            exhaustion_triggered=False,
        )
    except NTIStateReadError:
        # nti_state.json not yet initialized — NTI termination evaluation
        # deferred. terminationStatus remains "running". Stub behavior
        # pending NTI state initialization (Phase 13.x).
        # Return True to signal skip — caller must surface this
        # (Audit 13.10 items 4, 6: replay determinism + inference creep).
        return True
    return False


def _build_run_status(
    action: str,
    season_state: dict,
    canonical_count: int,
    rejected_count: int,
    nti_evaluation_skipped: bool = False,
    batch_id: str | None = None,
) -> dict:
    """Build the structured status dict returned by orchestrator_run.

    Fields required by §XI (Output Discipline):
        - active surface (stub — None until NTI wired)
        - micro-batch count
        - canonical objects produced this cycle
        - termination status
        - "batchId":             str | None,
        - "ntiEvaluationSkipped": bool,  # True if NTIStateReadError — eval skipped
    """
    return {
        "orchestratorVersion":  ORCHESTRATOR_VERSION,
        "action":               action,
        "terminationStatus":    season_state.get("terminationStatus"),
        "activeSurface":        season_state.get("activeSurface"),   # None until NTI wired
        "microBatchCount":      season_state.get("microBatchCount"),
        "canonicalizedCount":   canonical_count,
        "rejectedCount":        rejected_count,
        "batchId":              batch_id,
        "ntiEvaluationSkipped": nti_evaluation_skipped,
    }


def _build_halted_status(reason_code: str) -> dict:
    """Return status dict for early exit on preflight failure.

    Preflight failures (PreflightError.reason_code):
        SYSTEM_HALTED         — global_state.systemStatus == "halted"
        TERMINATION_BLOCKED   — season_state.terminationStatus != "running"

    Action guard:
        INVALID_ACTION        — action token not in _VALID_ACTIONS

    State ambiguity:
        AMBIGUOUS_LEDGER_STATE — incompleteBatchFlag is neither True nor False
    """
    return {
        "orchestratorVersion": ORCHESTRATOR_VERSION,
        "action":              "halted",
        "terminationStatus":   "blocked",
        "reasonCode":          reason_code,
        "activeSurface":       None,
        "microBatchCount":     None,
        "canonicalizedCount":  0,
        "rejectedCount":       0,
        "batchId":             None,
    }
