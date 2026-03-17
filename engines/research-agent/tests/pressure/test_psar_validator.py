"""Tests for pressure.psar_validator — Phase 7.5"""

import unittest
from copy import deepcopy

from engines.research_agent.agents.pressure.psar_validator import PSARSchemaValidationError, validate_psar


# ── Shared fixture ─────────────────────────────────────────────────────────────
# All values are valid per PSAR_v1.0 schema, registry.json, and derived-field rules.

_VALID_PSAR = {
    "proposalID": "PROP_2025_REG_003_0001",
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
    "domainSet": ["authority_distribution", "timing_horizon"],
    "clusterSignature": "SIG_" + "a" * 64,
    "structuralSourceIDs": ["PLO2_" + "a" * 64, "PLO2_" + "b" * 64],
    "clusterSize": 2,
    "domainDiversityCount": 2,
    "enumComplianceFlags": {
        "actorGroupResolved": True,
        "actionTypeResolved": True,
        "objectRoleResolved": True,
        "domainSetResolved": True,
        "registryVersionMatched": True,
    },
}


def _psar(**overrides) -> dict:
    """Return a deep copy of _VALID_PSAR with field overrides applied."""
    p = deepcopy(_VALID_PSAR)
    p.update(overrides)
    return p


class TestPSARValidator(unittest.TestCase):

    # ── Stage 1: JSON schema ───────────────────────────────────────────────────

    def test_valid_psar_passes(self):
        assert validate_psar(deepcopy(_VALID_PSAR)) is None

    def test_missing_proposal_id_fails(self):
        p = deepcopy(_VALID_PSAR)
        del p["proposalID"]
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(p)

    def test_wrong_audit_schema_version_fails(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(auditSchemaVersion="PSAR_v2.0"))

    def test_missing_agent_version_snapshot_fails(self):
        p = deepcopy(_VALID_PSAR)
        del p["agentVersionSnapshot"]
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(p)

    def test_incomplete_agent_version_snapshot_fails(self):
        p = deepcopy(_VALID_PSAR)
        del p["agentVersionSnapshot"]["pscaVersion"]
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(p)

    def test_proposal_id_pattern_valid(self):
        # All valid cycle-scoped formats
        for pid in ["PROP_2025_REG_001_0001", "PROP_2025_PRE_012_9999", "PROP_2026_POST_000_0001"]:
            assert validate_psar(_psar(proposalID=pid)) is None

    def test_proposal_id_wrong_pattern_fails(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(proposalID="PSPROPOSAL_abc123"))

    def test_cluster_signature_valid_64_hex(self):
        assert validate_psar(_psar(clusterSignature="SIG_" + "f" * 64)) is None

    def test_cluster_signature_truncated_fails(self):
        # 8-char suffix — old [:8] bug format must be rejected
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(clusterSignature="SIG_" + "a" * 8))

    def test_cluster_signature_wrong_prefix_fails(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(clusterSignature="HASH_" + "a" * 64))

    def test_cluster_size_zero_fails(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(clusterSize=0))

    def test_domain_diversity_count_zero_fails(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(domainDiversityCount=0))

    def test_empty_domain_set_fails(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(domainSet=[]))

    def test_empty_structural_source_ids_fails(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(structuralSourceIDs=[]))

    def test_additional_property_fails(self):
        p = deepcopy(_VALID_PSAR)
        p["unknownField"] = "value"
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(p)

    # ── Stage 2: Enum membership (INV-4) ──────────────────────────────────────

    def test_all_valid_cast_requirement_tokens_pass(self):
        valid_actors = [
            "individual_player", "position_group", "coach", "front_office",
            "ownership", "franchise", "league", "group", "unspecified",
        ]
        for actor in valid_actors:
            assert validate_psar(_psar(actorGroup=actor)) is None

    def test_actor_group_not_in_registry_fails(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(actorGroup="media_personality"))

    def test_actor_group_raw_value_fails(self):
        # Raw NLP span — not normalized
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(actorGroup="coaching staff"))

    def test_valid_domain_set_tokens_pass(self):
        for domain in ["authority_distribution", "timing_horizon", "availability_status",
                       "structural_configuration", "resource_allocation"]:
            assert validate_psar(_psar(domainSet=[domain], domainDiversityCount=1,
                                       structuralSourceIDs=["PLO2_" + "a" * 64],
                                       clusterSize=1)) is None

    def test_domain_not_in_registry_fails(self):
        p = _psar(domainSet=["authority_distribution", "nonexistent_domain"],
                  domainDiversityCount=2)
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(p)

    def test_domain_prose_label_fails(self):
        # Raw PLO-E domain label — not normalized
        p = _psar(domainSet=["Authority Distribution", "Timing & Horizon"],
                  domainDiversityCount=2)
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(p)

    # ── Stage 3: Derived-field consistency (INV-5) ────────────────────────────

    def test_cluster_size_matches_structural_source_ids(self):
        # 3 IDs, clusterSize=3 → valid
        ids = ["PLO2_" + c * 64 for c in "abc"]
        assert validate_psar(_psar(structuralSourceIDs=ids, clusterSize=3)) is None

    def test_cluster_size_mismatch_fails(self):
        ids = ["PLO2_" + "a" * 64, "PLO2_" + "b" * 64]
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(structuralSourceIDs=ids, clusterSize=5))

    def test_domain_diversity_count_matches_domain_set(self):
        # Domains must be sorted (INV-5). Sorted order: authority < resource < timing.
        domains = sorted(["authority_distribution", "timing_horizon", "resource_allocation"])
        assert validate_psar(_psar(domainSet=domains, domainDiversityCount=3)) is None

    def test_domain_diversity_count_mismatch_fails(self):
        domains = ["authority_distribution", "timing_horizon"]
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(domainSet=domains, domainDiversityCount=99))

    def test_sorted_domain_set_passes(self):
        # Lexicographic ascending
        domains = sorted(["timing_horizon", "authority_distribution"])
        assert validate_psar(_psar(domainSet=domains, domainDiversityCount=2)) is None

    def test_unsorted_domain_set_fails(self):
        # Reverse lexicographic — violates INV-5 sort contract
        domains = ["timing_horizon", "authority_distribution"]  # reverse of sorted
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(domainSet=domains, domainDiversityCount=2))

    # ── Exception type ─────────────────────────────────────────────────────────

    def test_raises_psar_schema_validation_error_not_base_exception(self):
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(_psar(actorGroup="invalid_actor"))

    def test_error_message_is_non_empty(self):
        with self.assertRaises(PSARSchemaValidationError) as cm:
            validate_psar(_psar(actorGroup="invalid_actor"))
        assert str(cm.exception) != ""

    # ── No timestamp (INV-5) ───────────────────────────────────────────────────

    def test_valid_psar_contains_no_timestamp(self):
        # validate_psar returns None — output has no timestamp to check.
        # Verify the validator does not inject fields into the input.
        p = deepcopy(_VALID_PSAR)
        original_keys = set(p.keys())
        validate_psar(p)
        assert set(p.keys()) == original_keys

    def test_input_not_mutated_on_pass(self):
        p = deepcopy(_VALID_PSAR)
        original = deepcopy(p)
        validate_psar(p)
        assert p == original

    def test_input_not_mutated_on_fail(self):
        p = _psar(actorGroup="invalid_actor")
        original = deepcopy(p)
        with self.assertRaises(PSARSchemaValidationError):
            validate_psar(p)
        # Only actorGroup was changed — rest unchanged
        assert p["proposalID"] == original["proposalID"]


if __name__ == "__main__":
    unittest.main()
