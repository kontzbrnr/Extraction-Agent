"""Tests for pressure.assembler_2a — Phase 7.2–7.4"""

import re
import unittest
from copy import deepcopy

from engines.research_agent.agents.pressure.assembler_2a import enforce_assembler_2a
from engines.research_agent.agents.pressure.assembler_2a_schema import PSAR_SCHEMA_VERSION


# ── Shared fixtures ────────────────────────────────────────────────────────────

_CYCLE = {"season": "2025", "phase": "REG", "week": 3}

def _plo2(ploID_suffix: str = "a" * 64,
          actorGroup_raw: str = "coaching staff",
          action_raw: str = "retained control",
          objectRole_raw: str = "play calling",
          domain: str = "Authority Distribution",
          sourceSeedId: str = "SEED_001") -> dict:
    """Minimal PLO-2.0 record using known-good normalization table entries."""
    return {
        "ploID": f"PLO2_{ploID_suffix}",
        "actorGroup_raw": actorGroup_raw,
        "action_raw": action_raw,
        "objectRole_raw": objectRole_raw,
        "domain": domain,
        "sourceSeedId": sourceSeedId,
        "cycleMetadata": deepcopy(_CYCLE),
    }


_TWO_DOMAIN_RECORDS = [
    _plo2(ploID_suffix="a" * 64, domain="Authority Distribution"),
    _plo2(ploID_suffix="b" * 64, domain="Timing & Horizon"),
]


_PROPOSAL_ID_PATTERN = re.compile(r"^PROP_[A-Za-z0-9]+_[A-Za-z0-9]+_\d{3}_\d{4}$")


class TestAssembler2A(unittest.TestCase):

    # ── Return type ────────────────────────────────────────────────────────────

    def test_returns_tuple(self):
        result = enforce_assembler_2a([], _CYCLE)
        assert isinstance(result, tuple)

    def test_returns_three_elements(self):
        assert len(enforce_assembler_2a([], _CYCLE)) == 3

    # ── Empty input ────────────────────────────────────────────────────────────

    def test_empty_input_empty_psar_list(self):
        psars, _, _ = enforce_assembler_2a([], _CYCLE)
        assert psars == []

    def test_empty_input_empty_rejection_list(self):
        _, rejections, _ = enforce_assembler_2a([], _CYCLE)
        assert rejections == []

    def test_empty_input_decision(self):
        _, _, audit = enforce_assembler_2a([], _CYCLE)
        assert audit["decision"] == "EMPTY_INPUT"

    # ── Normalization failure → rejection ─────────────────────────────────────

    def test_unknown_actor_group_produces_rejection(self):
        record = _plo2(actorGroup_raw="alien entity")
        _, rejections, _ = enforce_assembler_2a([record], _CYCLE)
        assert len(rejections) == 1

    def test_unknown_actor_group_empty_psars(self):
        record = _plo2(actorGroup_raw="alien entity")
        psars, _, _ = enforce_assembler_2a([record], _CYCLE)
        assert psars == []

    def test_unknown_domain_produces_rejection(self):
        record = _plo2(domain="Completely Unknown Domain")
        _, rejections, _ = enforce_assembler_2a([record], _CYCLE)
        assert len(rejections) == 1

    def test_rejection_decision_all_fail(self):
        record = _plo2(actorGroup_raw="alien entity")
        _, _, audit = enforce_assembler_2a([record], _CYCLE)
        assert audit["decision"] == "REJECT"

    # ── Successful PSAR emission ───────────────────────────────────────────────

    def test_known_actor_group_produces_psar(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        assert len(psars) == 1

    def test_psar_schema_version(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        assert psars[0]["auditSchemaVersion"] == PSAR_SCHEMA_VERSION

    def test_actor_group_normalized(self):
        psars, _, _ = enforce_assembler_2a([_plo2(actorGroup_raw="coaching staff")], _CYCLE)
        assert psars[0]["actorGroup"] == "coach"

    def test_action_type_snake_case(self):
        psars, _, _ = enforce_assembler_2a([_plo2(action_raw="retained control")], _CYCLE)
        assert psars[0]["actionType"] == "retained_control"

    def test_object_role_snake_case(self):
        psars, _, _ = enforce_assembler_2a([_plo2(objectRole_raw="play calling")], _CYCLE)
        assert psars[0]["objectRole"] == "play_calling"

    def test_domain_normalized(self):
        psars, _, _ = enforce_assembler_2a([_plo2(domain="Authority Distribution")], _CYCLE)
        assert "authority_distribution" in psars[0]["domainSet"]

    def test_all_enum_compliance_flags_true(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        flags = psars[0]["enumComplianceFlags"]
        assert all(flags.values())

    # ── proposalID format (INV-5) ─────────────────────────────────────────────

    def test_proposal_id_matches_pattern(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        assert _PROPOSAL_ID_PATTERN.match(psars[0]["proposalID"])

    def test_proposal_id_contains_season(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        assert "2025" in psars[0]["proposalID"]

    def test_proposal_id_contains_phase(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        assert "REG" in psars[0]["proposalID"]

    def test_proposal_id_week_zero_padded(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        # week=3 → "003"
        assert "_003_" in psars[0]["proposalID"]

    # ── clusterSignature (INV-5) ──────────────────────────────────────────────

    def test_cluster_signature_has_sig_prefix(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        assert psars[0]["clusterSignature"].startswith("SIG_")

    def test_cluster_signature_full_64_hex(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        hex_part = psars[0]["clusterSignature"][4:]
        assert len(hex_part) == 64
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_cluster_signature_not_truncated(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        # Must be 68 chars total ("SIG_" + 64 hex) — not 12 from old [:8] bug
        assert len(psars[0]["clusterSignature"]) == 68

    # ── Derived field consistency ─────────────────────────────────────────────

    def test_cluster_size_equals_source_id_count(self):
        psars, _, _ = enforce_assembler_2a(_TWO_DOMAIN_RECORDS, _CYCLE)
        psar = psars[0]
        assert psar["clusterSize"] == len(psar["structuralSourceIDs"])

    def test_domain_diversity_count_equals_domain_set_length(self):
        psars, _, _ = enforce_assembler_2a(_TWO_DOMAIN_RECORDS, _CYCLE)
        psar = psars[0]
        assert psar["domainDiversityCount"] == len(psar["domainSet"])

    def test_domain_set_is_sorted(self):
        psars, _, _ = enforce_assembler_2a(_TWO_DOMAIN_RECORDS, _CYCLE)
        domain_set = psars[0]["domainSet"]
        assert domain_set == sorted(domain_set)

    def test_structural_source_ids_are_sorted(self):
        psars, _, _ = enforce_assembler_2a(_TWO_DOMAIN_RECORDS, _CYCLE)
        ids = psars[0]["structuralSourceIDs"]
        assert ids == sorted(ids)

    def test_two_domain_records_produce_one_cluster(self):
        # Both records have same actorGroup_raw/action_raw/objectRole_raw → one cluster
        psars, _, _ = enforce_assembler_2a(_TWO_DOMAIN_RECORDS, _CYCLE)
        assert len(psars) == 1

    def test_two_domain_records_domain_diversity_is_two(self):
        psars, _, _ = enforce_assembler_2a(_TWO_DOMAIN_RECORDS, _CYCLE)
        assert psars[0]["domainDiversityCount"] == 2

    # ── Clustering by normalized key ──────────────────────────────────────────

    def test_different_actor_groups_produce_separate_clusters(self):
        record_coach = _plo2(actorGroup_raw="coaching staff", ploID_suffix="a" * 64)
        record_fo = _plo2(actorGroup_raw="general manager", ploID_suffix="b" * 64)
        psars, _, _ = enforce_assembler_2a([record_coach, record_fo], _CYCLE)
        assert len(psars) == 2

    def test_cluster_ordinal_sorted_by_signature(self):
        # Two clusters — ordinals assigned by sorted clusterSignature
        record_a = _plo2(actorGroup_raw="coaching staff", ploID_suffix="a" * 64)
        record_b = _plo2(actorGroup_raw="general manager", ploID_suffix="b" * 64)
        psars, _, _ = enforce_assembler_2a([record_a, record_b], _CYCLE)
        sigs = [p["clusterSignature"] for p in psars]
        assert sigs == sorted(sigs)

    # ── Deduplication (INV-5) ─────────────────────────────────────────────────

    def test_duplicate_plo_id_deduplicated(self):
        record = _plo2(ploID_suffix="a" * 64)
        duplicate = deepcopy(record)
        psars, _, _ = enforce_assembler_2a([record, duplicate], _CYCLE)
        assert psars[0]["clusterSize"] == 1

    # ── Determinism (INV-5) ───────────────────────────────────────────────────

    def test_determinism_single_record(self):
        records1 = [_plo2()]
        records2 = [_plo2()]
        result1 = enforce_assembler_2a(records1, deepcopy(_CYCLE))
        result2 = enforce_assembler_2a(records2, deepcopy(_CYCLE))
        assert result1 == result2

    def test_determinism_two_domain_records(self):
        r1 = deepcopy(_TWO_DOMAIN_RECORDS)
        r2 = deepcopy(_TWO_DOMAIN_RECORDS)
        result1 = enforce_assembler_2a(r1, deepcopy(_CYCLE))
        result2 = enforce_assembler_2a(r2, deepcopy(_CYCLE))
        assert result1 == result2

    # ── No canonical IDs (INV-2) ──────────────────────────────────────────────

    def test_no_canonical_cps_id_in_psar(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        assert "canonicalCpsID" not in psars[0]

    # ── No timestamp (INV-5) ───────────────────────────────────────────────────

    def test_no_timestamp_in_psar(self):
        psars, _, _ = enforce_assembler_2a([_plo2()], _CYCLE)
        assert "timestamp" not in psars[0]

    def test_no_timestamp_in_audit(self):
        _, _, audit = enforce_assembler_2a([_plo2()], _CYCLE)
        assert "timestamp" not in audit

    # ── Audit log ─────────────────────────────────────────────────────────────

    def test_audit_pass_decision(self):
        _, _, audit = enforce_assembler_2a([_plo2()], _CYCLE)
        assert audit["decision"] == "PASS"

    def test_audit_partial_decision(self):
        good = _plo2(ploID_suffix="a" * 64)
        bad = _plo2(ploID_suffix="b" * 64, actorGroup_raw="alien entity")
        _, _, audit = enforce_assembler_2a([good, bad], _CYCLE)
        assert audit["decision"] == "PARTIAL"


if __name__ == "__main__":
    unittest.main()
