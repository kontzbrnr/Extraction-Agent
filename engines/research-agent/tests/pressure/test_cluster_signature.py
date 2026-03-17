"""Tests for pressure.cluster_signature — Phase 7.4"""

import hashlib
import unittest

from engines.research_agent.agents.pressure.cluster_signature import (
    CLUSTER_SIGNATURE_PREFIX,
    derive_cluster_signature,
)


class TestClusterSignature(unittest.TestCase):

    # ── Constants ──────────────────────────────────────────────────────────────

    def test_prefix_constant(self):
        assert CLUSTER_SIGNATURE_PREFIX == "SIG_"

    # ── Return shape ───────────────────────────────────────────────────────────

    def test_returns_string(self):
        result = derive_cluster_signature("coach", "retained_control", "play_calling", ["authority_distribution"])
        assert isinstance(result, str)

    def test_total_length(self):
        # "SIG_" (4) + sha256 hexdigest (64) = 68
        result = derive_cluster_signature("coach", "retained_control", "play_calling", ["authority_distribution"])
        assert len(result) == 68

    def test_starts_with_sig_prefix(self):
        result = derive_cluster_signature("coach", "retained_control", "play_calling", ["authority_distribution"])
        assert result.startswith("SIG_")

    def test_hex_suffix_is_lowercase_hex(self):
        result = derive_cluster_signature("coach", "retained_control", "play_calling", ["authority_distribution"])
        hex_part = result[4:]
        assert len(hex_part) == 64
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_no_truncation(self):
        # Full hexdigest must be 64 chars — not the 8-char [:8] bug.
        result = derive_cluster_signature("coach", "retained_control", "play_calling", ["authority_distribution"])
        hex_part = result[4:]
        assert len(hex_part) == 64

    # ── Correctness ────────────────────────────────────────────────────────────

    def test_matches_manual_sha256(self):
        actor_group  = "coach"
        action_type  = "retained_control"
        object_role  = "play_calling"
        domain_set   = ["authority_distribution", "timing_horizon"]
        sig_raw = "|".join([actor_group, action_type, object_role] + domain_set)
        expected = "SIG_" + hashlib.sha256(sig_raw.encode("utf-8")).hexdigest()
        result = derive_cluster_signature(actor_group, action_type, object_role, domain_set)
        assert result == expected

    # ── Determinism (INV-5) ────────────────────────────────────────────────────

    def test_determinism_single_domain(self):
        args = ("coach", "retained_control", "play_calling", ["authority_distribution"])
        assert derive_cluster_signature(*args) == derive_cluster_signature(*args)

    def test_determinism_multi_domain(self):
        args = ("front_office", "released", "starter", ["authority_distribution", "timing_horizon"])
        assert derive_cluster_signature(*args) == derive_cluster_signature(*args)

    # ── Collision resistance (INV-5) ───────────────────────────────────────────

    def test_different_actor_group_produces_different_signature(self):
        domains = ["authority_distribution"]
        sig1 = derive_cluster_signature("coach", "retained_control", "play_calling", domains)
        sig2 = derive_cluster_signature("front_office", "retained_control", "play_calling", domains)
        assert sig1 != sig2

    def test_different_action_type_produces_different_signature(self):
        domains = ["authority_distribution"]
        sig1 = derive_cluster_signature("coach", "retained_control", "play_calling", domains)
        sig2 = derive_cluster_signature("coach", "relinquished_control", "play_calling", domains)
        assert sig1 != sig2

    def test_different_object_role_produces_different_signature(self):
        domains = ["authority_distribution"]
        sig1 = derive_cluster_signature("coach", "retained_control", "play_calling", domains)
        sig2 = derive_cluster_signature("coach", "retained_control", "clock_management", domains)
        assert sig1 != sig2

    def test_different_domain_set_produces_different_signature(self):
        sig1 = derive_cluster_signature("coach", "retained_control", "play_calling", ["authority_distribution"])
        sig2 = derive_cluster_signature("coach", "retained_control", "play_calling", ["timing_horizon"])
        assert sig1 != sig2

    def test_domain_sort_order_sensitivity(self):
        # Function does NOT sort — caller must pre-sort.
        # Different order → different hash (caller contract violation, but deterministic).
        sig_ab = derive_cluster_signature("coach", "retained_control", "play_calling",
                                          ["authority_distribution", "timing_horizon"])
        sig_ba = derive_cluster_signature("coach", "retained_control", "play_calling",
                                          ["timing_horizon", "authority_distribution"])
        assert sig_ab != sig_ba

    def test_presorted_domains_stable(self):
        domains = sorted(["timing_horizon", "authority_distribution"])
        sig1 = derive_cluster_signature("coach", "retained_control", "play_calling", domains)
        sig2 = derive_cluster_signature("coach", "retained_control", "play_calling", domains)
        assert sig1 == sig2

    def test_single_domain_vs_two_domains_differ(self):
        sig1 = derive_cluster_signature("coach", "retained_control", "play_calling",
                                        ["authority_distribution"])
        sig2 = derive_cluster_signature("coach", "retained_control", "play_calling",
                                        ["authority_distribution", "timing_horizon"])
        assert sig1 != sig2

    # ── No runtime fields (INV-5) ──────────────────────────────────────────────

    def test_no_uuid_or_timestamp_in_output(self):
        result = derive_cluster_signature("coach", "retained_control", "play_calling", ["authority_distribution"])
        # Output is deterministic hex — no UUIDs or timestamps possible
        assert result.startswith("SIG_")
        assert len(result) == 68


if __name__ == "__main__":
    unittest.main()
