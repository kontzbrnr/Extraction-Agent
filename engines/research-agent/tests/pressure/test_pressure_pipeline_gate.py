"""Tests for pressure.pressure_pipeline_gate — Phase 7.7

SSI calls spaCy at import time. A sys.modules stub is installed before any
pressure imports to satisfy the import-time version assertion and model load
in pressure.ssi_extractor, allowing full isolation of the gate's routing
logic via @patch mocks.
"""

# ── spaCy stub (must be first, before any pressure imports) ───────────────────
# pressure.pressure_pipeline_gate → pressure.ssi → pressure.ssi_extractor
# imports spacy and asserts __version__.startswith("3.7"), then calls
# spacy.load("en_core_web_sm"). Both are satisfied by a lightweight Mock.
import sys
from unittest.mock import MagicMock

_spacy_stub = MagicMock()
_spacy_stub.__version__ = "3.7.0"   # satisfies SPACY_MODEL_VERSION_PREFIX == "3.7"
_spacy_stub.load.return_value = MagicMock()  # satisfies _NLP = spacy.load(...)
sys.modules.setdefault("spacy", _spacy_stub)

# ── Standard library ──────────────────────────────────────────────────────────
import unittest
from copy import deepcopy
from unittest.mock import call, patch

# ── Module under test and supporting imports ──────────────────────────────────
from engines.research_agent.agents.pressure.pressure_pipeline_gate import enforce_pressure_pipeline
from engines.research_agent.agents.pressure.pressure_pipeline_schema import (
    PRESSURE_PIPELINE_GATE_VERSION,
    REJECT_PSAR_GATE_SCHEMA_INVALID,
    PSAR_GATE_VALIDATION_SCHEMA_VERSION,
)
from engines.research_agent.agents.pressure.psar_validator import PSARSchemaValidationError


# ── Shared fixtures ────────────────────────────────────────────────────────────

_PLO = {
    "sourceSeedId": "SEED_001",
    "sourceSeedText": "The coaching staff retained control of play calling.",
    "schemaVersion": "PLO-1.0",
    "observations": [
        {"domain": "Authority Distribution", "observation": "obs 1"},
        {"domain": "Timing & Horizon", "observation": "obs 2"},
        {"domain": "Structural Configuration", "observation": "obs 3"},
        {"domain": "Preparation & Installation", "observation": "obs 4"},
    ],
}

_CYCLE = {"season": "2025", "phase": "REG", "week": 3}

_PLO2_RECORD = {
    "ploID": "PLO2_" + "a" * 64,
    "actorGroup_raw": "coaching staff",
    "action_raw": "retained control",
    "objectRole_raw": "play calling",
    "domain": "Authority Distribution",
    "sourceSeedId": "SEED_001",
    "cycleMetadata": _CYCLE,
}

_PSAR_RECORD = {
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
    "structuralSourceIDs": ["PLO2_" + "a" * 64],
    "clusterSize": 1,
    "domainDiversityCount": 2,
    "enumComplianceFlags": {
        "actorGroupResolved": True,
        "actionTypeResolved": True,
        "objectRoleResolved": True,
        "domainSetResolved": True,
        "registryVersionMatched": True,
    },
}

_PASSED_PSAR = {**_PSAR_RECORD, "criticStatus": "PASS", "reasonCode": "PASS_ALL_CHECKS", "failureStage": None}
_REJECTED_PSAR = {**_PSAR_RECORD, "criticStatus": "REJECT",
                  "reasonCode": "REJECT_INSUFFICIENT_CLUSTER_SIZE",
                  "failureStage": "1_CLUSTER_SIZE_GATE"}

_SSI_AUDIT = {"decision": "PASS", "auditSchemaVersion": "SSI_AUDIT-1.0"}
_2A_AUDIT = {"decision": "PASS", "auditSchemaVersion": "2A_AUDIT-1.0"}
_PSCA_AUDIT = {"decision": "PASS", "auditSchemaVersion": "PSCA_AUDIT-1.0"}


class TestPressurePipelineGate(unittest.TestCase):

    # ── Return type ────────────────────────────────────────────────────────────

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_returns_tuple(self, mock_ssi):
        result = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert isinstance(result, tuple)

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_returns_three_elements(self, mock_ssi):
        assert len(enforce_pressure_pipeline(_PLO, _CYCLE)) == 3

    # ── Short-circuit: SSI produces no records ────────────────────────────────

    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a")
    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_ssi_empty_skips_assembler(self, mock_ssi, mock_2a):
        enforce_pressure_pipeline(_PLO, _CYCLE)
        mock_2a.assert_not_called()

    @patch("pressure.pressure_pipeline_gate.enforce_psca")
    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_ssi_empty_skips_psca(self, mock_ssi, mock_psca):
        enforce_pressure_pipeline(_PLO, _CYCLE)
        mock_psca.assert_not_called()

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_ssi_empty_returns_empty_passed(self, mock_ssi):
        passed, _, _ = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert passed == []

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], ["ssi_rejection"], _SSI_AUDIT))
    def test_ssi_rejections_forwarded(self, mock_ssi):
        _, all_rejections, _ = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "ssi_rejection" in all_rejections

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_ssi_empty_audit_has_ssi_key(self, mock_ssi):
        _, _, audit = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "ssi" in audit

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_ssi_empty_audit_has_no_assembler_key(self, mock_ssi):
        _, _, audit = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "assembler_2a" not in audit

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_ssi_empty_audit_has_no_psca_key(self, mock_ssi):
        _, _, audit = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "psca" not in audit

    # ── Short-circuit: 2A produces no PSAR records ────────────────────────────

    @patch("pressure.pressure_pipeline_gate.enforce_psca")
    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([], [], _2A_AUDIT))
    def test_assembler_empty_skips_psca(self, mock_2a, mock_ssi, mock_psca):
        enforce_pressure_pipeline(_PLO, _CYCLE)
        mock_psca.assert_not_called()

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([], ["2a_rejection"], _2A_AUDIT))
    def test_assembler_empty_rejections_forwarded(self, mock_2a, mock_ssi):
        _, all_rejections, _ = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "2a_rejection" in all_rejections

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([], [], _2A_AUDIT))
    def test_assembler_empty_audit_has_assembler_key(self, mock_2a, mock_ssi):
        _, _, audit = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "assembler_2a" in audit

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([], [], _2A_AUDIT))
    def test_assembler_empty_audit_no_psca_key(self, mock_2a, mock_ssi):
        _, _, audit = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "psca" not in audit

    # ── PSAR validation gate ───────────────────────────────────────────────────

    @patch("pressure.pressure_pipeline_gate.enforce_psca")
    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], [], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar",
           side_effect=PSARSchemaValidationError("bad psar"))
    def test_invalid_psar_excluded_from_psca(self, mock_validate, mock_2a, mock_ssi, mock_psca):
        enforce_pressure_pipeline(_PLO, _CYCLE)
        mock_psca.assert_not_called()

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], [], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar",
           side_effect=PSARSchemaValidationError("bad psar"))
    def test_invalid_psar_produces_gate_rejection(self, mock_validate, mock_2a, mock_ssi):
        _, all_rejections, _ = enforce_pressure_pipeline(_PLO, _CYCLE)
        gate_rejections = [r for r in all_rejections
                           if r.get("schemaVersion") == PSAR_GATE_VALIDATION_SCHEMA_VERSION]
        assert len(gate_rejections) == 1

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], [], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar",
           side_effect=PSARSchemaValidationError("bad psar"))
    def test_invalid_psar_gate_rejection_reason_code(self, mock_validate, mock_2a, mock_ssi):
        _, all_rejections, _ = enforce_pressure_pipeline(_PLO, _CYCLE)
        gate_rejection = next(r for r in all_rejections
                              if r.get("schemaVersion") == PSAR_GATE_VALIDATION_SCHEMA_VERSION)
        assert gate_rejection["reasonCode"] == REJECT_PSAR_GATE_SCHEMA_INVALID

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], [], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_psca",
           return_value=([deepcopy(_PASSED_PSAR)], [], _PSCA_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar", return_value=None)
    def test_valid_psar_reaches_psca(self, mock_validate, mock_psca, mock_2a, mock_ssi):
        enforce_pressure_pipeline(_PLO, _CYCLE)
        mock_psca.assert_called_once()

    # ── Full pass-through ─────────────────────────────────────────────────────

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], [], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_psca",
           return_value=([deepcopy(_PASSED_PSAR)], [], _PSCA_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar", return_value=None)
    def test_full_pass_returns_passed_psars(self, mock_validate, mock_psca, mock_2a, mock_ssi):
        passed, _, _ = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert len(passed) == 1
        assert passed[0]["criticStatus"] == "PASS"

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], [], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_psca",
           return_value=([deepcopy(_PASSED_PSAR)], [], _PSCA_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar", return_value=None)
    def test_full_pass_composite_audit_has_all_keys(self, mock_validate, mock_psca, mock_2a, mock_ssi):
        _, _, audit = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "ssi" in audit
        assert "assembler_2a" in audit
        assert "psca" in audit

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], [], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_psca",
           return_value=([], [deepcopy(_REJECTED_PSAR)], _PSCA_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar", return_value=None)
    def test_psca_rejected_psars_in_all_rejections(self, mock_validate, mock_psca, mock_2a, mock_ssi):
        _, all_rejections, _ = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert any(r.get("criticStatus") == "REJECT" for r in all_rejections)

    # ── Rejection ordering (audit trail completeness) ────────────────────────

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], ["ssi_rej"], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], ["2a_rej"], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar",
           side_effect=PSARSchemaValidationError("bad"))
    def test_rejection_order_ssi_then_2a_then_validation(self, mock_validate, mock_2a, mock_ssi):
        _, all_rejections, _ = enforce_pressure_pipeline(_PLO, _CYCLE)
        # SSI rejection first, 2A rejection second, gate rejection third
        assert all_rejections[0] == "ssi_rej"
        assert all_rejections[1] == "2a_rej"
        assert all_rejections[2]["reasonCode"] == REJECT_PSAR_GATE_SCHEMA_INVALID

    # ── Input immutability (INV-3) ────────────────────────────────────────────

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([], [], _SSI_AUDIT))
    def test_input_plo_not_mutated(self, mock_ssi):
        plo = deepcopy(_PLO)
        original = deepcopy(plo)
        enforce_pressure_pipeline(plo, _CYCLE)
        assert plo == original

    # ── Version constant ───────────────────────────────────────────────────────

    def test_gate_version_constant(self):
        assert PRESSURE_PIPELINE_GATE_VERSION == "1.0"

    # ── No timestamp (INV-5) ───────────────────────────────────────────────────

    @patch("pressure.pressure_pipeline_gate.enforce_ssi",
           return_value=([_PLO2_RECORD], [], _SSI_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_assembler_2a",
           return_value=([deepcopy(_PSAR_RECORD)], [], _2A_AUDIT))
    @patch("pressure.pressure_pipeline_gate.enforce_psca",
           return_value=([deepcopy(_PASSED_PSAR)], [], _PSCA_AUDIT))
    @patch("pressure.pressure_pipeline_gate.validate_psar", return_value=None)
    def test_no_timestamp_in_composite_audit(self, mock_validate, mock_psca, mock_2a, mock_ssi):
        _, _, audit = enforce_pressure_pipeline(_PLO, _CYCLE)
        assert "timestamp" not in audit


if __name__ == "__main__":
    unittest.main()
