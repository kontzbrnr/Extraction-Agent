"""Tests for pressure.psca — Phase 7.6"""

import unittest
from copy import deepcopy

from engines.research_agent.agents.pressure.psca import enforce_psca
from engines.research_agent.agents.pressure.psca_schema import (
    MIN_CLUSTER_SIZE,
    MIN_DOMAIN_DIVERSITY,
    PSCA_VERSION,
    REASON_PASS_ALL_CHECKS,
    REASON_REJECT_INSUFFICIENT_CLUSTER_SIZE,
    REASON_REJECT_INSUFFICIENT_DOMAIN_DIVERSITY,
    STAGE_1_CLUSTER_SIZE,
    STAGE_2_DOMAIN_DIVERSITY,
    VERDICT_PASS,
    VERDICT_REJECT,
)


# ── Shared fixtures ────────────────────────────────────────────────────────────

def _make_psar(cluster_size: int = 2, domain_diversity: int = 2,
               all_flags_true: bool = True) -> dict:
    """Minimal valid pre-critic PSAR for gate testing."""
    flags = {
        "actorGroupResolved": True,
        "actionTypeResolved": True,
        "objectRoleResolved": True,
        "domainSetResolved": True,
        "registryVersionMatched": True,
    }
    if not all_flags_true:
        flags["actorGroupResolved"] = False

    return {
        "proposalID": f"PROP_2025_REG_001_0001",
        "auditSchemaVersion": "PSAR_v1.0",
        "enumRegistryVersion": "ENUM_v1.0",
        "agentVersionSnapshot": {
            "ploEVersion": "1.0",
            "assembler2AVersion": "2A-1.0",
            "pscaVersion": "unknown",
        },
        "actorGroup": "coach",
        "actionType": "retained_control",
        "objectRole": "play_calling",
        "domainSet": ["authority_distribution", "timing_horizon"][:domain_diversity],
        "clusterSignature": "SIG_" + "a" * 64,
        "structuralSourceIDs": ["PLO2_" + c * 64 for c in "ab"[:cluster_size]],
        "clusterSize": cluster_size,
        "domainDiversityCount": domain_diversity,
        "enumComplianceFlags": flags,
    }


_PASSING_PSAR = _make_psar(cluster_size=2, domain_diversity=2)


class TestPSCA(unittest.TestCase):

    # ── Return type ────────────────────────────────────────────────────────────

    def test_returns_tuple(self):
        assert isinstance(enforce_psca([]), tuple)

    def test_returns_three_elements(self):
        assert len(enforce_psca([])) == 3

    def test_first_element_is_list(self):
        passed, _, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert isinstance(passed, list)

    def test_second_element_is_list(self):
        _, rejected, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert isinstance(rejected, list)

    def test_third_element_is_dict(self):
        _, _, audit = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert isinstance(audit, dict)

    # ── Empty input ────────────────────────────────────────────────────────────

    def test_empty_input_returns_empty_passed(self):
        passed, _, _ = enforce_psca([])
        assert passed == []

    def test_empty_input_returns_empty_rejected(self):
        _, rejected, _ = enforce_psca([])
        assert rejected == []

    def test_empty_input_decision(self):
        _, _, audit = enforce_psca([])
        assert audit["decision"] == "EMPTY_INPUT"

    def test_empty_input_counts(self):
        _, _, audit = enforce_psca([])
        assert audit["inputCount"] == 0
        assert audit["passCount"] == 0
        assert audit["rejectCount"] == 0
        assert audit["malformedCount"] == 0

    # ── Malformed input (false enumComplianceFlags) ───────────────────────────

    def test_malformed_excluded_from_passed(self):
        malformed = _make_psar(cluster_size=2, domain_diversity=2, all_flags_true=False)
        passed, _, _ = enforce_psca([malformed])
        assert passed == []

    def test_malformed_excluded_from_rejected(self):
        malformed = _make_psar(cluster_size=2, domain_diversity=2, all_flags_true=False)
        _, rejected, _ = enforce_psca([malformed])
        assert rejected == []

    def test_malformed_counted_in_audit(self):
        malformed = _make_psar(cluster_size=2, domain_diversity=2, all_flags_true=False)
        _, _, audit = enforce_psca([malformed])
        assert audit["malformedCount"] == 1

    def test_malformed_produces_reject_all_decision(self):
        malformed = _make_psar(cluster_size=2, domain_diversity=2, all_flags_true=False)
        _, _, audit = enforce_psca([malformed])
        assert audit["decision"] == "REJECT_ALL"

    # ── Gate Step 1: Cluster size ──────────────────────────────────────────────

    def test_cluster_size_below_minimum_rejected(self):
        psar = _make_psar(cluster_size=MIN_CLUSTER_SIZE - 1, domain_diversity=2)
        _, rejected, _ = enforce_psca([psar])
        assert len(rejected) == 1

    def test_cluster_size_below_minimum_reason_code(self):
        psar = _make_psar(cluster_size=MIN_CLUSTER_SIZE - 1, domain_diversity=2)
        _, rejected, _ = enforce_psca([psar])
        assert rejected[0]["reasonCode"] == REASON_REJECT_INSUFFICIENT_CLUSTER_SIZE

    def test_cluster_size_below_minimum_failure_stage(self):
        psar = _make_psar(cluster_size=MIN_CLUSTER_SIZE - 1, domain_diversity=2)
        _, rejected, _ = enforce_psca([psar])
        assert rejected[0]["failureStage"] == STAGE_1_CLUSTER_SIZE

    def test_cluster_size_below_minimum_verdict(self):
        psar = _make_psar(cluster_size=MIN_CLUSTER_SIZE - 1, domain_diversity=2)
        _, rejected, _ = enforce_psca([psar])
        assert rejected[0]["criticStatus"] == VERDICT_REJECT

    def test_cluster_size_at_minimum_passes_gate_1(self):
        psar = _make_psar(cluster_size=MIN_CLUSTER_SIZE, domain_diversity=2)
        passed, _, _ = enforce_psca([psar])
        # clusterSize == MIN passes step 1. domainDiversity == 2 passes step 2.
        assert len(passed) == 1

    # ── Gate Step 2: Domain diversity ─────────────────────────────────────────

    def test_domain_diversity_below_minimum_rejected(self):
        psar = _make_psar(cluster_size=2, domain_diversity=MIN_DOMAIN_DIVERSITY - 1)
        _, rejected, _ = enforce_psca([psar])
        assert len(rejected) == 1

    def test_domain_diversity_below_minimum_reason_code(self):
        psar = _make_psar(cluster_size=2, domain_diversity=MIN_DOMAIN_DIVERSITY - 1)
        _, rejected, _ = enforce_psca([psar])
        assert rejected[0]["reasonCode"] == REASON_REJECT_INSUFFICIENT_DOMAIN_DIVERSITY

    def test_domain_diversity_below_minimum_failure_stage(self):
        psar = _make_psar(cluster_size=2, domain_diversity=MIN_DOMAIN_DIVERSITY - 1)
        _, rejected, _ = enforce_psca([psar])
        assert rejected[0]["failureStage"] == STAGE_2_DOMAIN_DIVERSITY

    def test_domain_diversity_at_minimum_passes_gate_2(self):
        psar = _make_psar(cluster_size=2, domain_diversity=MIN_DOMAIN_DIVERSITY)
        passed, _, _ = enforce_psca([psar])
        assert len(passed) == 1

    # ── Gate ordering (INV-5): Step 1 before Step 2 ───────────────────────────

    def test_step_1_evaluated_before_step_2(self):
        # Both gates would fail — reasonCode must come from step 1
        psar = _make_psar(cluster_size=MIN_CLUSTER_SIZE - 1, domain_diversity=MIN_DOMAIN_DIVERSITY - 1)
        _, rejected, _ = enforce_psca([psar])
        assert rejected[0]["reasonCode"] == REASON_REJECT_INSUFFICIENT_CLUSTER_SIZE
        assert rejected[0]["failureStage"] == STAGE_1_CLUSTER_SIZE

    # ── PASS path ──────────────────────────────────────────────────────────────

    def test_pass_verdict(self):
        passed, _, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert passed[0]["criticStatus"] == VERDICT_PASS

    def test_pass_reason_code(self):
        passed, _, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert passed[0]["reasonCode"] == REASON_PASS_ALL_CHECKS

    def test_pass_failure_stage_is_none(self):
        passed, _, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert passed[0]["failureStage"] is None

    def test_pass_not_in_rejected(self):
        passed, rejected, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert len(passed) == 1
        assert len(rejected) == 0

    def test_pass_decision_all_pass(self):
        _, _, audit = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert audit["decision"] == "PASS"

    # ── pscaVersion updated (PSAR contract v1.0 §VI) ──────────────────────────

    def test_psca_version_set_in_passed_psar(self):
        passed, _, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert passed[0]["agentVersionSnapshot"]["pscaVersion"] == PSCA_VERSION

    def test_psca_version_set_in_rejected_psar(self):
        psar = _make_psar(cluster_size=1, domain_diversity=2)
        _, rejected, _ = enforce_psca([psar])
        assert rejected[0]["agentVersionSnapshot"]["pscaVersion"] == PSCA_VERSION

    def test_psca_version_was_unknown_before(self):
        assert _PASSING_PSAR["agentVersionSnapshot"]["pscaVersion"] == "unknown"

    def test_psca_version_not_unknown_after(self):
        passed, _, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert passed[0]["agentVersionSnapshot"]["pscaVersion"] != "unknown"

    # ── Input immutability (INV-3) ────────────────────────────────────────────

    def test_input_psar_not_mutated_on_pass(self):
        psar = deepcopy(_PASSING_PSAR)
        original = deepcopy(psar)
        enforce_psca([psar])
        assert psar == original

    def test_input_psar_not_mutated_on_reject(self):
        psar = _make_psar(cluster_size=1, domain_diversity=2)
        original = deepcopy(psar)
        enforce_psca([psar])
        assert psar == original

    def test_passed_psar_is_new_object(self):
        psar = deepcopy(_PASSING_PSAR)
        passed, _, _ = enforce_psca([psar])
        assert passed[0] is not psar

    def test_rejected_psar_is_new_object(self):
        psar = _make_psar(cluster_size=1, domain_diversity=2)
        _, rejected, _ = enforce_psca([psar])
        assert rejected[0] is not psar

    # ── Audit log ─────────────────────────────────────────────────────────────

    def test_audit_pass_counts(self):
        _, _, audit = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert audit["passCount"] == 1
        assert audit["rejectCount"] == 0
        assert audit["inputCount"] == 1

    def test_audit_reject_counts(self):
        psar = _make_psar(cluster_size=1, domain_diversity=2)
        _, _, audit = enforce_psca([psar])
        assert audit["passCount"] == 0
        assert audit["rejectCount"] == 1
        assert audit["inputCount"] == 1

    def test_audit_partial_decision(self):
        passing = deepcopy(_PASSING_PSAR)
        failing = _make_psar(cluster_size=1, domain_diversity=2)
        _, _, audit = enforce_psca([passing, failing])
        assert audit["decision"] == "PARTIAL"

    def test_audit_reject_all_decision(self):
        failing = _make_psar(cluster_size=1, domain_diversity=2)
        _, _, audit = enforce_psca([failing])
        assert audit["decision"] == "REJECT_ALL"

    def test_audit_psca_version(self):
        _, _, audit = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert audit["pscaVersion"] == PSCA_VERSION

    # ── No canonical IDs (INV-2) ──────────────────────────────────────────────

    def test_no_canonical_cps_id_in_passed(self):
        passed, _, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert "canonicalCpsID" not in passed[0]

    def test_no_canonical_cps_id_in_rejected(self):
        psar = _make_psar(cluster_size=1, domain_diversity=2)
        _, rejected, _ = enforce_psca([psar])
        assert "canonicalCpsID" not in rejected[0]

    # ── No timestamp (INV-5) ───────────────────────────────────────────────────

    def test_no_timestamp_in_passed(self):
        passed, _, _ = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert "timestamp" not in passed[0]

    def test_no_timestamp_in_audit(self):
        _, _, audit = enforce_psca([deepcopy(_PASSING_PSAR)])
        assert "timestamp" not in audit

    # ── Determinism (INV-5) ───────────────────────────────────────────────────

    def test_determinism_pass(self):
        psar1 = deepcopy(_PASSING_PSAR)
        psar2 = deepcopy(_PASSING_PSAR)
        result1 = enforce_psca([psar1])
        result2 = enforce_psca([psar2])
        assert result1 == result2

    def test_determinism_reject(self):
        psar1 = _make_psar(cluster_size=1, domain_diversity=2)
        psar2 = _make_psar(cluster_size=1, domain_diversity=2)
        result1 = enforce_psca([psar1])
        result2 = enforce_psca([psar2])
        assert result1 == result2

    # ── Threshold constants ────────────────────────────────────────────────────

    def test_min_cluster_size_constant(self):
        assert MIN_CLUSTER_SIZE == 2

    def test_min_domain_diversity_constant(self):
        assert MIN_DOMAIN_DIVERSITY == 2


if __name__ == "__main__":
    unittest.main()
