"""
tests/nti/test_extraction_fingerprint_registry.py

Tests for nti/extraction_fingerprint_registry.py.

Key invariants under test:
  INV-5: Fingerprints stored sorted → byte-identical JSON for identical
         fingerprint sets regardless of registration order.
  No time encoding: registry schema contains ZERO time fields.
  Idempotency: re-registering a fingerprint returns False with no write.
  Append-only: registered fingerprints cannot be removed.
  Read-only operations: is_registered, registry_size, all_fingerprints
                        perform no disk writes.
"""

import json
import os

import pytest

from infra.orchestration.nti.extraction_fingerprint_registry import (
    EXTRACTION_FINGERPRINT_REGISTRY_SCHEMA_VERSION,
    FingerprintRegistryExistsError,
    FingerprintRegistryReadError,
    all_fingerprints,
    create_registry,
    is_registered,
    register_fingerprint,
    registry_size,
)

RUN_PATH = "runs/2024_REG"


def _reg_path(tmp_path):
    return tmp_path / RUN_PATH / "extraction_fingerprints.json"


def _setup(tmp_path):
    """Create run directory and empty registry."""
    run_dir = tmp_path / RUN_PATH
    run_dir.mkdir(parents=True, exist_ok=True)
    create_registry(str(tmp_path), RUN_PATH)


def _read_raw(tmp_path):
    with open(_reg_path(tmp_path), "r", encoding="utf-8") as fh:
        return json.load(fh)


# ── create_registry ───────────────────────────────────────────────────────────

def test_create_registry_creates_file(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True)
    create_registry(str(tmp_path), RUN_PATH)
    assert _reg_path(tmp_path).exists()


def test_create_registry_schema_version(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True)
    create_registry(str(tmp_path), RUN_PATH)
    data = _read_raw(tmp_path)
    assert data["schemaVersion"] == EXTRACTION_FINGERPRINT_REGISTRY_SCHEMA_VERSION


def test_create_registry_empty_fingerprints(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True)
    create_registry(str(tmp_path), RUN_PATH)
    data = _read_raw(tmp_path)
    assert data["fingerprints"] == []


def test_create_registry_returns_state_dict(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True)
    result = create_registry(str(tmp_path), RUN_PATH)
    assert isinstance(result, dict)
    assert result["schemaVersion"] == EXTRACTION_FINGERPRINT_REGISTRY_SCHEMA_VERSION
    assert result["fingerprints"] == []


def test_create_registry_raises_if_exists(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True)
    create_registry(str(tmp_path), RUN_PATH)
    with pytest.raises(FingerprintRegistryExistsError):
        create_registry(str(tmp_path), RUN_PATH)


def test_create_registry_exists_error_pre_io(tmp_path):
    """ExistsError is raised before any file IO (pre-IO check)."""
    (tmp_path / RUN_PATH).mkdir(parents=True)
    create_registry(str(tmp_path), RUN_PATH)
    # Second call must raise immediately — file is unchanged.
    data_before = _read_raw(tmp_path)
    with pytest.raises(FingerprintRegistryExistsError):
        create_registry(str(tmp_path), RUN_PATH)
    data_after = _read_raw(tmp_path)
    assert data_before == data_after


# ── NO TIME ENCODING — schema structure ───────────────────────────────────────

def test_schema_has_only_schema_version_and_fingerprints_keys(tmp_path):
    """
    CONFIRM NO TIME ENCODING:
    Registry JSON must have exactly two keys: schemaVersion and fingerprints.
    Zero time-related fields (season, surface, cycle, batch_id, timestamp, etc.)
    """
    _setup(tmp_path)
    data = _read_raw(tmp_path)
    assert set(data.keys()) == {"schemaVersion", "fingerprints"}


def test_register_does_not_add_time_fields(tmp_path):
    """After registration, registry still has exactly two keys."""
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "abc123")
    data = _read_raw(tmp_path)
    assert set(data.keys()) == {"schemaVersion", "fingerprints"}


def test_same_fingerprint_is_duplicate_regardless_of_context(tmp_path):
    """
    CONFIRM NO TIME ENCODING:
    Same fingerprint string registered under any 'context' (simulating different
    surfaces) is always a duplicate. Registry has no concept of surface/season.
    """
    _setup(tmp_path)
    fp = "sha256:deadbeef" * 8  # opaque structural fingerprint
    # First registration — simulating Offseason context
    result1 = register_fingerprint(str(tmp_path), RUN_PATH, fp)
    assert result1 is True
    # Second registration — simulating Regular Season context (same structural content)
    result2 = register_fingerprint(str(tmp_path), RUN_PATH, fp)
    assert result2 is False  # Duplicate — registry has no time context


# ── register_fingerprint — happy path ────────────────────────────────────────

def test_register_returns_true_for_new_fingerprint(tmp_path):
    _setup(tmp_path)
    assert register_fingerprint(str(tmp_path), RUN_PATH, "fp_a") is True


def test_register_persists_fingerprint(tmp_path):
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_a")
    assert is_registered(str(tmp_path), RUN_PATH, "fp_a") is True


def test_register_returns_false_for_duplicate(tmp_path):
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_a")
    result = register_fingerprint(str(tmp_path), RUN_PATH, "fp_a")
    assert result is False


def test_register_duplicate_no_disk_write(tmp_path):
    """Duplicate registration must not write to disk (idempotent)."""
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_a")
    data_before = _read_raw(tmp_path)
    mtime_before = os.path.getmtime(_reg_path(tmp_path))

    register_fingerprint(str(tmp_path), RUN_PATH, "fp_a")
    data_after = _read_raw(tmp_path)
    mtime_after = os.path.getmtime(_reg_path(tmp_path))

    assert data_before == data_after
    assert mtime_before == mtime_after


def test_register_multiple_fingerprints(tmp_path):
    _setup(tmp_path)
    fps = [f"fp_{i:04d}" for i in range(10)]
    for fp in fps:
        result = register_fingerprint(str(tmp_path), RUN_PATH, fp)
        assert result is True
    assert registry_size(str(tmp_path), RUN_PATH) == 10


def test_register_all_fingerprints_persist(tmp_path):
    _setup(tmp_path)
    fps = ["fp_alpha", "fp_beta", "fp_gamma"]
    for fp in fps:
        register_fingerprint(str(tmp_path), RUN_PATH, fp)
    result = all_fingerprints(str(tmp_path), RUN_PATH)
    assert result == frozenset(fps)


# ── INV-5 — sorted storage ────────────────────────────────────────────────────

def test_fingerprints_stored_sorted_ascending(tmp_path):
    """INV-5: fingerprints list in JSON must be sorted ascending."""
    _setup(tmp_path)
    # Register in non-alphabetical order
    register_fingerprint(str(tmp_path), RUN_PATH, "zzz")
    register_fingerprint(str(tmp_path), RUN_PATH, "aaa")
    register_fingerprint(str(tmp_path), RUN_PATH, "mmm")
    data = _read_raw(tmp_path)
    assert data["fingerprints"] == sorted(data["fingerprints"])


def test_registration_order_does_not_affect_json_content(tmp_path):
    """
    INV-5: two registries with same fingerprints in different order
    must produce byte-identical JSON files.
    """
    fps = ["fp_c", "fp_a", "fp_b"]

    # Registry 1: register in order c, a, b
    run1 = "runs/run1"
    (tmp_path / run1).mkdir(parents=True)
    create_registry(str(tmp_path), run1)
    for fp in fps:
        register_fingerprint(str(tmp_path), run1, fp)

    # Registry 2: register in order a, b, c
    run2 = "runs/run2"
    (tmp_path / run2).mkdir(parents=True)
    create_registry(str(tmp_path), run2)
    for fp in sorted(fps):
        register_fingerprint(str(tmp_path), run2, fp)

    with open(tmp_path / run1 / "extraction_fingerprints.json", "rb") as f1:
        bytes1 = f1.read()
    with open(tmp_path / run2 / "extraction_fingerprints.json", "rb") as f2:
        bytes2 = f2.read()

    assert bytes1 == bytes2


# ── Pre-IO validation ─────────────────────────────────────────────────────────

def test_empty_fingerprint_raises_value_error(tmp_path):
    _setup(tmp_path)
    with pytest.raises(ValueError):
        register_fingerprint(str(tmp_path), RUN_PATH, "")


def test_non_string_fingerprint_raises_value_error(tmp_path):
    _setup(tmp_path)
    with pytest.raises(ValueError):
        register_fingerprint(str(tmp_path), RUN_PATH, 12345)  # type: ignore


def test_empty_fingerprint_no_io_performed(tmp_path):
    """ValueError raised before any IO."""
    _setup(tmp_path)
    data_before = _read_raw(tmp_path)
    with pytest.raises(ValueError):
        register_fingerprint(str(tmp_path), RUN_PATH, "")
    data_after = _read_raw(tmp_path)
    assert data_before == data_after


# ── is_registered ─────────────────────────────────────────────────────────────

def test_is_registered_false_before_registration(tmp_path):
    _setup(tmp_path)
    assert is_registered(str(tmp_path), RUN_PATH, "fp_x") is False


def test_is_registered_true_after_registration(tmp_path):
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_x")
    assert is_registered(str(tmp_path), RUN_PATH, "fp_x") is True


def test_is_registered_does_not_write(tmp_path):
    _setup(tmp_path)
    data_before = _read_raw(tmp_path)
    is_registered(str(tmp_path), RUN_PATH, "fp_x")
    data_after = _read_raw(tmp_path)
    assert data_before == data_after


def test_is_registered_reflects_disk(tmp_path):
    """is_registered reads fresh from disk — no caching."""
    _setup(tmp_path)
    assert is_registered(str(tmp_path), RUN_PATH, "fp_new") is False
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_new")
    assert is_registered(str(tmp_path), RUN_PATH, "fp_new") is True


# ── registry_size ─────────────────────────────────────────────────────────────

def test_registry_size_zero_on_empty(tmp_path):
    _setup(tmp_path)
    assert registry_size(str(tmp_path), RUN_PATH) == 0


def test_registry_size_increments(tmp_path):
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_1")
    assert registry_size(str(tmp_path), RUN_PATH) == 1
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_2")
    assert registry_size(str(tmp_path), RUN_PATH) == 2


def test_registry_size_unaffected_by_duplicate(tmp_path):
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_1")
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_1")  # duplicate
    assert registry_size(str(tmp_path), RUN_PATH) == 1


# ── all_fingerprints ──────────────────────────────────────────────────────────

def test_all_fingerprints_empty(tmp_path):
    _setup(tmp_path)
    assert all_fingerprints(str(tmp_path), RUN_PATH) == frozenset()


def test_all_fingerprints_returns_frozenset(tmp_path):
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_a")
    result = all_fingerprints(str(tmp_path), RUN_PATH)
    assert isinstance(result, frozenset)


def test_all_fingerprints_reflects_disk(tmp_path):
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_a")
    result = all_fingerprints(str(tmp_path), RUN_PATH)
    assert "fp_a" in result


def test_all_fingerprints_count_matches_registry_size(tmp_path):
    _setup(tmp_path)
    fps = ["fp_a", "fp_b", "fp_c", "fp_d"]
    for fp in fps:
        register_fingerprint(str(tmp_path), RUN_PATH, fp)
    assert len(all_fingerprints(str(tmp_path), RUN_PATH)) == registry_size(str(tmp_path), RUN_PATH)


# ── Read errors ───────────────────────────────────────────────────────────────

def test_read_raises_on_missing_file(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True)
    with pytest.raises(FingerprintRegistryReadError):
        is_registered(str(tmp_path), RUN_PATH, "fp")


def test_read_raises_on_wrong_schema_version(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True)
    path = _reg_path(tmp_path)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"schemaVersion": "WRONG-1.0", "fingerprints": []}, fh)
    with pytest.raises(FingerprintRegistryReadError):
        is_registered(str(tmp_path), RUN_PATH, "fp")


def test_read_raises_on_invalid_json(tmp_path):
    (tmp_path / RUN_PATH).mkdir(parents=True)
    path = _reg_path(tmp_path)
    path.write_text("not valid json", encoding="utf-8")
    with pytest.raises(FingerprintRegistryReadError):
        registry_size(str(tmp_path), RUN_PATH)


# ── Append-only — no mutation ─────────────────────────────────────────────────

def test_registered_fingerprints_present_after_more_registrations(tmp_path):
    """Existing fingerprints survive subsequent registrations."""
    _setup(tmp_path)
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_original")
    register_fingerprint(str(tmp_path), RUN_PATH, "fp_new")
    result = all_fingerprints(str(tmp_path), RUN_PATH)
    assert "fp_original" in result
    assert "fp_new" in result
