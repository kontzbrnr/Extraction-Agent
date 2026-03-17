"""
tests/ledger/test_crash_simulation.py

System-level crash simulation tests.

Validates that all ledger write operations preserve target file integrity
after OS-level crashes injected at:
  - byte 1  (crash during write, 1 byte in temp file)
  - byte N-1 (crash during write, N-1 bytes in temp file)
  - before rename (full temp file, os.replace blocked)

Key assertions:
  - Target file is either absent or byte-identical to pre-crash state
  - No partial JSON entry is visible in any target file
  - Subsequent valid writes succeed (retry-safe)
  - Lane isolation: other lanes unaffected by a crashed append (INV-4)
"""

import json
import os
import pytest

from tests.ledger.crash_harness import (
    crash_before_rename,
    crash_write_at_byte,
    payload_size,
)
from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.registry_writer import append_canonical_object, EMPTY_REGISTRY
from engines.research_engine.ledger.registry_reader import read_registry, lane_cardinality
from engines.research_engine.ledger.global_state_manager import (
    read_global_state,
    write_global_state,
    read_season_state,
    write_season_state,
)
from engines.research_engine.ledger.season_state_manager import create_season_run


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

RUN_PATH = "runs/2024_REG"

SAMPLE_DATA = {
    "schemaVersion": "CANONICAL_REGISTRY-1.0",
    "CPS": [],
    "CME": [],
    "CSN": [],
    "StructuralEnvironment": [],
    "MediaContext": [],
}

VALID_GLOBAL_STATE = {
    "schemaVersion": "GLOBAL_STATE-1.0",
    "activeSeason": "2024_REG",
    "activeRunPath": RUN_PATH,
    "systemStatus": "operational",
}


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def _registry_path(tmp_path):
    run_dir = tmp_path / RUN_PATH
    run_dir.mkdir(parents=True, exist_ok=True)
    return str(run_dir / "canonical_objects.json")


def _cps_obj(canonical_id: str) -> dict:
    return {"canonicalId": canonical_id, "lane": "CPS"}


# ---------------------------------------------------------------------------
# atomic_write_json — crash at byte 1
# ---------------------------------------------------------------------------


class TestCrashAtByte1:

    def test_target_absent_after_crash_on_first_write(self, tmp_path):
        path = str(tmp_path / "output.json")
        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                atomic_write_json(path, SAMPLE_DATA)
        assert not os.path.exists(path)

    def test_target_unchanged_after_crash_overwrite(self, tmp_path):
        path = str(tmp_path / "output.json")
        # Establish valid initial state
        atomic_write_json(path, SAMPLE_DATA)
        before_bytes = _read_bytes(path)

        new_data = {**SAMPLE_DATA, "CPS": [_cps_obj("c1")]}
        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                atomic_write_json(path, new_data)

        assert _read_bytes(path) == before_bytes

    def test_target_valid_json_after_crash(self, tmp_path):
        path = str(tmp_path / "output.json")
        atomic_write_json(path, SAMPLE_DATA)

        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                atomic_write_json(path, {**SAMPLE_DATA, "CPS": [_cps_obj("c1")]})

        # Must be valid JSON — no partial entry
        with open(path, "r", encoding="utf-8") as fh:
            result = json.load(fh)
        assert result["CPS"] == []

    def test_retry_after_crash_succeeds(self, tmp_path):
        path = str(tmp_path / "output.json")
        new_data = {**SAMPLE_DATA, "CPS": [_cps_obj("c1")]}

        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                atomic_write_json(path, new_data)

        # Retry without crash injection — must succeed
        atomic_write_json(path, new_data)
        result = json.loads(_read_bytes(path))
        assert len(result["CPS"]) == 1


# ---------------------------------------------------------------------------
# atomic_write_json — crash at byte N-1
# ---------------------------------------------------------------------------


class TestCrashAtByteNMinus1:

    def test_target_absent_after_crash_on_first_write(self, tmp_path):
        path = str(tmp_path / "output.json")
        n = payload_size(SAMPLE_DATA)
        with crash_write_at_byte(n - 1):
            with pytest.raises(OSError):
                atomic_write_json(path, SAMPLE_DATA)
        assert not os.path.exists(path)

    def test_target_unchanged_after_crash_overwrite(self, tmp_path):
        path = str(tmp_path / "output.json")
        atomic_write_json(path, SAMPLE_DATA)
        before_bytes = _read_bytes(path)

        new_data = {**SAMPLE_DATA, "CME": [{"id": "m1"}]}
        n = payload_size(new_data)
        with crash_write_at_byte(n - 1):
            with pytest.raises(OSError):
                atomic_write_json(path, new_data)

        assert _read_bytes(path) == before_bytes

    def test_no_partial_entry_visible(self, tmp_path):
        path = str(tmp_path / "output.json")
        atomic_write_json(path, SAMPLE_DATA)

        new_data = {**SAMPLE_DATA, "CSN": [{"id": "n1"}, {"id": "n2"}]}
        n = payload_size(new_data)
        with crash_write_at_byte(n - 1):
            with pytest.raises(OSError):
                atomic_write_json(path, new_data)

        result = json.loads(_read_bytes(path))
        assert result["CSN"] == []  # new data not visible

    def test_retry_after_crash_succeeds(self, tmp_path):
        path = str(tmp_path / "output.json")
        data = {**SAMPLE_DATA, "CPS": [_cps_obj("c1")]}
        n = payload_size(data)

        with crash_write_at_byte(n - 1):
            with pytest.raises(OSError):
                atomic_write_json(path, data)

        atomic_write_json(path, data)
        assert json.loads(_read_bytes(path))["CPS"][0]["canonicalId"] == "c1"


# ---------------------------------------------------------------------------
# atomic_write_json — crash before rename (os.replace blocked)
# ---------------------------------------------------------------------------


class TestCrashBeforeRename:

    def test_target_absent_on_first_write(self, tmp_path):
        path = str(tmp_path / "output.json")
        with crash_before_rename():
            with pytest.raises(OSError):
                atomic_write_json(path, SAMPLE_DATA)
        assert not os.path.exists(path)

    def test_target_unchanged_on_overwrite(self, tmp_path):
        path = str(tmp_path / "output.json")
        atomic_write_json(path, SAMPLE_DATA)
        before_bytes = _read_bytes(path)

        with crash_before_rename():
            with pytest.raises(OSError):
                atomic_write_json(path, {**SAMPLE_DATA, "CPS": [_cps_obj("x")]})

        assert _read_bytes(path) == before_bytes

    def test_retry_after_crash_succeeds(self, tmp_path):
        path = str(tmp_path / "output.json")
        data = {**SAMPLE_DATA, "CPS": [_cps_obj("retry_obj")]}

        with crash_before_rename():
            with pytest.raises(OSError):
                atomic_write_json(path, data)

        atomic_write_json(path, data)
        assert json.loads(_read_bytes(path))["CPS"][0]["canonicalId"] == "retry_obj"


# ---------------------------------------------------------------------------
# append_canonical_object — no partial entry after crash (INV-3)
# ---------------------------------------------------------------------------


class TestRegistryAppendCrash:

    def test_no_partial_entry_after_crash_at_byte_1(self, tmp_path):
        reg_path = _registry_path(tmp_path)
        atomic_write_json(reg_path, EMPTY_REGISTRY)

        obj = _cps_obj("cps_crash_001")
        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                append_canonical_object(reg_path, "CPS", obj)

        registry = read_registry(reg_path)
        assert len(registry["CPS"]) == 0

    def test_no_partial_entry_after_crash_before_rename(self, tmp_path):
        reg_path = _registry_path(tmp_path)
        atomic_write_json(reg_path, EMPTY_REGISTRY)

        obj = _cps_obj("cps_crash_002")
        with crash_before_rename():
            with pytest.raises(OSError):
                append_canonical_object(reg_path, "CPS", obj)

        assert lane_cardinality(reg_path, "CPS") == 0

    def test_committed_objects_survive_crash(self, tmp_path):
        """Objects committed before the crash must remain after it."""
        reg_path = _registry_path(tmp_path)
        atomic_write_json(reg_path, EMPTY_REGISTRY)

        # Commit first object successfully
        append_canonical_object(reg_path, "CPS", _cps_obj("cps_pre_crash"))
        assert lane_cardinality(reg_path, "CPS") == 1

        # Crash during second append
        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                append_canonical_object(reg_path, "CPS", _cps_obj("cps_lost"))

        # First object is still there; second is not
        registry = read_registry(reg_path)
        assert len(registry["CPS"]) == 1
        assert registry["CPS"][0]["canonicalId"] == "cps_pre_crash"

    def test_lane_isolation_after_crash(self, tmp_path):
        """Crash during CPS append must not corrupt other lane arrays (INV-4)."""
        reg_path = _registry_path(tmp_path)
        initial = {
            **EMPTY_REGISTRY,
            "CSN": [{"id": "csn_001"}],
            "CME": [{"id": "cme_001"}],
        }
        atomic_write_json(reg_path, initial)
        before_csn = read_registry(reg_path)["CSN"]
        before_cme = read_registry(reg_path)["CME"]

        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                append_canonical_object(reg_path, "CPS", _cps_obj("cps_crash"))

        registry = read_registry(reg_path)
        assert registry["CSN"] == before_csn
        assert registry["CME"] == before_cme

    def test_retry_append_after_crash_succeeds(self, tmp_path):
        """After a crashed append, the same object can be appended successfully."""
        reg_path = _registry_path(tmp_path)
        atomic_write_json(reg_path, EMPTY_REGISTRY)
        obj = _cps_obj("cps_retry")

        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                append_canonical_object(reg_path, "CPS", obj)

        append_canonical_object(reg_path, "CPS", obj)
        assert lane_cardinality(reg_path, "CPS") == 1


# ---------------------------------------------------------------------------
# Season state write — crash scenarios
# ---------------------------------------------------------------------------


class TestSeasonStateCrash:

    def _season_path(self, tmp_path):
        run_dir = tmp_path / RUN_PATH
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir / "state.json"

    def test_season_state_unchanged_after_crash_at_byte_1(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        before_bytes = self._season_path(tmp_path).read_bytes()

        updated = {**json.loads(before_bytes), "microBatchCount": 99}
        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                write_season_state(str(tmp_path), RUN_PATH, updated)

        assert self._season_path(tmp_path).read_bytes() == before_bytes

    def test_season_state_unchanged_after_crash_before_rename(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        before_bytes = self._season_path(tmp_path).read_bytes()

        updated = {**json.loads(before_bytes), "microBatchCount": 99}
        with crash_before_rename():
            with pytest.raises(OSError):
                write_season_state(str(tmp_path), RUN_PATH, updated)

        assert self._season_path(tmp_path).read_bytes() == before_bytes

    def test_season_state_valid_after_crash(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)

        updated = {**json.loads(self._season_path(tmp_path).read_bytes()),
                   "microBatchCount": 5}
        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                write_season_state(str(tmp_path), RUN_PATH, updated)

        # Must be readable and schema-valid
        result = read_season_state(str(tmp_path), RUN_PATH)
        assert result["microBatchCount"] == 0  # original value


# ---------------------------------------------------------------------------
# Global state write — crash scenarios
# ---------------------------------------------------------------------------


class TestGlobalStateCrash:

    def test_global_state_unchanged_after_crash_at_byte_1(self, tmp_path):
        write_global_state(str(tmp_path), VALID_GLOBAL_STATE)
        before_bytes = (tmp_path / "global_state.json").read_bytes()

        updated = {**VALID_GLOBAL_STATE, "activeSeason": "2025_PRE"}
        with crash_write_at_byte(1):
            with pytest.raises(OSError):
                write_global_state(str(tmp_path), updated)

        assert (tmp_path / "global_state.json").read_bytes() == before_bytes

    def test_global_state_valid_after_crash(self, tmp_path):
        write_global_state(str(tmp_path), VALID_GLOBAL_STATE)

        updated = {**VALID_GLOBAL_STATE, "systemStatus": "halted"}
        n = payload_size(updated)
        with crash_write_at_byte(n - 1):
            with pytest.raises(OSError):
                write_global_state(str(tmp_path), updated)

        result = read_global_state(str(tmp_path))
        assert result["systemStatus"] == "operational"  # original value

    def test_retry_global_state_write_after_crash(self, tmp_path):
        write_global_state(str(tmp_path), VALID_GLOBAL_STATE)
        updated = {**VALID_GLOBAL_STATE, "activeSeason": "2025_PRE"}

        with crash_before_rename():
            with pytest.raises(OSError):
                write_global_state(str(tmp_path), updated)

        write_global_state(str(tmp_path), updated)
        assert read_global_state(str(tmp_path))["activeSeason"] == "2025_PRE"
