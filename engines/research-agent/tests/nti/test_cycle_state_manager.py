"""
tests/nti/test_cycle_state_manager.py

Tests for nti/cycle_state_manager.py.

Key invariants under test:
  INV-1: all read operations re-read from disk — no caching.
  Schema gap: NTI_CYCLE_STATE-1.0 is authoritative as designed here.
  Idempotency: seal_surface is idempotent — no write on already-sealed surface.
"""

import json
import pytest

from infra.orchestration.nti.cycle_state_manager import (
    NTI_CYCLE_STATE_SCHEMA_VERSION,
    NTIStateError,
    NTIStateExistsError,
    NTIStateReadError,
    create_nti_state,
    get_exhaustion_counter,
    get_sealed_surfaces,
    increment_exhaustion_counter,
    read_nti_state,
    seal_surface,
    set_current_surface,
    write_nti_state,
)
from infra.orchestration.nti.surface_rotation_index import SURFACE_ROTATION_ORDER


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

RUN_PATH = "runs/2024_REG"


def _nti_path(tmp_path):
    return tmp_path / RUN_PATH / "nti_state.json"


def _make_run_dir(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True, exist_ok=True)


def _read_raw(tmp_path):
    return json.loads(_nti_path(tmp_path).read_text(encoding="utf-8"))


def _setup(tmp_path):
    _make_run_dir(tmp_path)
    return create_nti_state(str(tmp_path), RUN_PATH)


# ---------------------------------------------------------------------------
# create_nti_state
# ---------------------------------------------------------------------------


def test_create_nti_state_creates_file(tmp_path):
    _make_run_dir(tmp_path)
    create_nti_state(str(tmp_path), RUN_PATH)
    assert _nti_path(tmp_path).exists()


def test_create_nti_state_schema_version(tmp_path):
    _setup(tmp_path)
    assert _read_raw(tmp_path)["schemaVersion"] == NTI_CYCLE_STATE_SCHEMA_VERSION


def test_create_nti_state_current_surface_is_null(tmp_path):
    _setup(tmp_path)
    assert _read_raw(tmp_path)["currentSurface"] is None


def test_create_nti_state_all_surfaces_active(tmp_path):
    _setup(tmp_path)
    status = _read_raw(tmp_path)["surfaceSealStatus"]
    assert all(v is False for v in status.values())
    assert set(status.keys()) == set(SURFACE_ROTATION_ORDER)


def test_create_nti_state_all_exhaustion_counters_zero(tmp_path):
    _setup(tmp_path)
    counters = _read_raw(tmp_path)["exhaustionCounters"]
    assert all(v == 0 for v in counters.values())
    assert set(counters.keys()) == set(SURFACE_ROTATION_ORDER)


def test_create_nti_state_all_eight_surfaces_present(tmp_path):
    _setup(tmp_path)
    data = _read_raw(tmp_path)
    assert len(data["surfaceSealStatus"]) == 8
    assert len(data["exhaustionCounters"]) == 8


def test_create_nti_state_raises_if_exists(tmp_path):
    _setup(tmp_path)
    with pytest.raises(NTIStateExistsError) as exc_info:
        create_nti_state(str(tmp_path), RUN_PATH)
    assert exc_info.value.path != ""


def test_create_nti_state_readable_by_read_nti_state(tmp_path):
    _setup(tmp_path)
    result = read_nti_state(str(tmp_path), RUN_PATH)
    assert result["schemaVersion"] == NTI_CYCLE_STATE_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# read_nti_state
# ---------------------------------------------------------------------------


def test_read_nti_state_file_not_found(tmp_path):
    _make_run_dir(tmp_path)
    with pytest.raises(NTIStateReadError) as exc_info:
        read_nti_state(str(tmp_path), RUN_PATH)
    assert exc_info.value.path != ""


def test_read_nti_state_wrong_schema_version(tmp_path):
    _setup(tmp_path)
    data = _read_raw(tmp_path)
    data["schemaVersion"] = "WRONG-9.9"
    _nti_path(tmp_path).write_text(json.dumps(data))
    with pytest.raises(NTIStateReadError) as exc_info:
        read_nti_state(str(tmp_path), RUN_PATH)
    assert NTI_CYCLE_STATE_SCHEMA_VERSION in str(exc_info.value)


def test_read_nti_state_invalid_json(tmp_path):
    _make_run_dir(tmp_path)
    _nti_path(tmp_path).write_text("{bad json")
    with pytest.raises(NTIStateReadError):
        read_nti_state(str(tmp_path), RUN_PATH)


def test_read_nti_state_no_caching(tmp_path):
    _setup(tmp_path)
    r1 = read_nti_state(str(tmp_path), RUN_PATH)
    assert r1["currentSurface"] is None
    # Externally mutate
    data = _read_raw(tmp_path)
    data["currentSurface"] = "offseason"
    _nti_path(tmp_path).write_text(json.dumps(data))
    r2 = read_nti_state(str(tmp_path), RUN_PATH)
    assert r2["currentSurface"] == "offseason"


# ---------------------------------------------------------------------------
# set_current_surface
# ---------------------------------------------------------------------------


def test_set_current_surface_valid(tmp_path):
    _setup(tmp_path)
    set_current_surface(str(tmp_path), RUN_PATH, "offseason")
    assert _read_raw(tmp_path)["currentSurface"] == "offseason"


def test_set_current_surface_all_valid_surfaces(tmp_path):
    _setup(tmp_path)
    for surface in SURFACE_ROTATION_ORDER:
        set_current_surface(str(tmp_path), RUN_PATH, surface)
        assert _read_raw(tmp_path)["currentSurface"] == surface


def test_set_current_surface_unknown_raises_before_io(tmp_path):
    with pytest.raises(NTIStateError):
        set_current_surface(str(tmp_path / "nonexistent"), RUN_PATH, "INVALID")


def test_set_current_surface_does_not_mutate_seal_status(tmp_path):
    _setup(tmp_path)
    set_current_surface(str(tmp_path), RUN_PATH, "playoffs")
    status = _read_raw(tmp_path)["surfaceSealStatus"]
    assert all(v is False for v in status.values())


# ---------------------------------------------------------------------------
# seal_surface
# ---------------------------------------------------------------------------


def test_seal_surface_seals_target(tmp_path):
    _setup(tmp_path)
    seal_surface(str(tmp_path), RUN_PATH, "offseason")
    assert _read_raw(tmp_path)["surfaceSealStatus"]["offseason"] is True


def test_seal_surface_others_remain_active(tmp_path):
    _setup(tmp_path)
    seal_surface(str(tmp_path), RUN_PATH, "offseason")
    status = _read_raw(tmp_path)["surfaceSealStatus"]
    for surface, sealed in status.items():
        if surface != "offseason":
            assert sealed is False


def test_seal_surface_idempotent_no_error(tmp_path):
    _setup(tmp_path)
    seal_surface(str(tmp_path), RUN_PATH, "offseason")
    before_bytes = _nti_path(tmp_path).read_bytes()
    seal_surface(str(tmp_path), RUN_PATH, "offseason")  # second call
    after_bytes = _nti_path(tmp_path).read_bytes()
    # Idempotent — no write should occur (bytes identical)
    assert before_bytes == after_bytes


def test_seal_surface_unknown_raises_before_io(tmp_path):
    with pytest.raises(NTIStateError):
        seal_surface(str(tmp_path / "nonexistent"), RUN_PATH, "INVALID")


def test_seal_all_surfaces(tmp_path):
    _setup(tmp_path)
    for surface in SURFACE_ROTATION_ORDER:
        seal_surface(str(tmp_path), RUN_PATH, surface)
    status = _read_raw(tmp_path)["surfaceSealStatus"]
    assert all(v is True for v in status.values())


# ---------------------------------------------------------------------------
# get_sealed_surfaces
# ---------------------------------------------------------------------------


def test_get_sealed_surfaces_empty_initially(tmp_path):
    _setup(tmp_path)
    assert get_sealed_surfaces(str(tmp_path), RUN_PATH) == frozenset()


def test_get_sealed_surfaces_after_seal(tmp_path):
    _setup(tmp_path)
    seal_surface(str(tmp_path), RUN_PATH, "offseason")
    seal_surface(str(tmp_path), RUN_PATH, "playoffs")
    result = get_sealed_surfaces(str(tmp_path), RUN_PATH)
    assert result == frozenset({"offseason", "playoffs"})


def test_get_sealed_surfaces_returns_frozenset(tmp_path):
    _setup(tmp_path)
    result = get_sealed_surfaces(str(tmp_path), RUN_PATH)
    assert isinstance(result, frozenset)


def test_get_sealed_surfaces_all_sealed(tmp_path):
    _setup(tmp_path)
    for surface in SURFACE_ROTATION_ORDER:
        seal_surface(str(tmp_path), RUN_PATH, surface)
    result = get_sealed_surfaces(str(tmp_path), RUN_PATH)
    assert result == frozenset(SURFACE_ROTATION_ORDER)


# ---------------------------------------------------------------------------
# increment_exhaustion_counter
# ---------------------------------------------------------------------------


def test_increment_exhaustion_counter_starts_zero(tmp_path):
    _setup(tmp_path)
    new_count = increment_exhaustion_counter(str(tmp_path), RUN_PATH, "offseason")
    assert new_count == 1


def test_increment_exhaustion_counter_returns_new_count(tmp_path):
    _setup(tmp_path)
    assert increment_exhaustion_counter(str(tmp_path), RUN_PATH, "offseason") == 1
    assert increment_exhaustion_counter(str(tmp_path), RUN_PATH, "offseason") == 2
    assert increment_exhaustion_counter(str(tmp_path), RUN_PATH, "offseason") == 3


def test_increment_exhaustion_counter_persisted(tmp_path):
    _setup(tmp_path)
    increment_exhaustion_counter(str(tmp_path), RUN_PATH, "regular_season")
    increment_exhaustion_counter(str(tmp_path), RUN_PATH, "regular_season")
    assert _read_raw(tmp_path)["exhaustionCounters"]["regular_season"] == 2


def test_increment_exhaustion_counter_isolation(tmp_path):
    """Incrementing one surface must not affect other surfaces."""
    _setup(tmp_path)
    increment_exhaustion_counter(str(tmp_path), RUN_PATH, "playoffs")
    counters = _read_raw(tmp_path)["exhaustionCounters"]
    for surface, count in counters.items():
        if surface != "playoffs":
            assert count == 0


def test_increment_exhaustion_counter_unknown_raises_before_io(tmp_path):
    with pytest.raises(NTIStateError):
        increment_exhaustion_counter(
            str(tmp_path / "nonexistent"), RUN_PATH, "INVALID"
        )


def test_increment_reads_disk_each_call(tmp_path):
    """INV-1: each increment re-reads from disk."""
    _setup(tmp_path)
    # Externally set counter to 10
    data = _read_raw(tmp_path)
    data["exhaustionCounters"]["offseason"] = 10
    _nti_path(tmp_path).write_text(json.dumps(data))
    new_count = increment_exhaustion_counter(str(tmp_path), RUN_PATH, "offseason")
    assert new_count == 11


# ---------------------------------------------------------------------------
# get_exhaustion_counter
# ---------------------------------------------------------------------------


def test_get_exhaustion_counter_initial_zero(tmp_path):
    _setup(tmp_path)
    assert get_exhaustion_counter(str(tmp_path), RUN_PATH, "offseason") == 0


def test_get_exhaustion_counter_after_increments(tmp_path):
    _setup(tmp_path)
    increment_exhaustion_counter(str(tmp_path), RUN_PATH, "training_camp")
    increment_exhaustion_counter(str(tmp_path), RUN_PATH, "training_camp")
    assert get_exhaustion_counter(str(tmp_path), RUN_PATH, "training_camp") == 2


def test_get_exhaustion_counter_unknown_raises(tmp_path):
    _setup(tmp_path)
    with pytest.raises(NTIStateError):
        get_exhaustion_counter(str(tmp_path), RUN_PATH, "INVALID")
