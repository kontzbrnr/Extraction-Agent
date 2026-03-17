"""
tests/gsd/test_gsd_determinism_harness.py

GSD-Layer Determinism Verification Harness — Phase 4.6

Runs each GSD-layer function _RUNS times on fixed inputs and asserts
that every output is identical across all runs.

Covers INV-5 (replay determinism) and INV-1 (no accumulated state)
for the following GSD-layer components:
  - gsd.composite_ruleset.is_composite
  - gsd.split_mechanics.split_rec (AU ids, PCR, schemaVersion)
  - gsd.au_validator.validate_au
  - gsd.rejection_handler.make_atomicity_rejection
  - gsd.split_mechanics.AU_ID_VERSION (constant stability)
  - gsd.composite_ruleset.GSD_COMPOSITE_RULESET_VERSION (constant stability)

AtomicityEnforcer is excluded: enforce() raises NotImplementedError
and will be covered by its own harness in a later phase.
"""

from gsd.au_validator import validate_au
from gsd.composite_ruleset import GSD_COMPOSITE_RULESET_VERSION, is_composite
from gsd.rejection_handler import make_atomicity_rejection
from gsd.split_mechanics import AU_ID_VERSION, split_rec

# ── Harness configuration ─────────────────────────────────────────────────────

_RUNS: int = 5
_SOURCE_REF: str = "article://harness/gsd-test-001"

# ── Fixed REC inputs (hardcoded — never derived from env or runtime) ───────────

_COMPOSITE_REC = {
    "id": "REC_" + "b" * 64,
    "text": "Coach fired OC and promoted QB coach.",
    "isComposite": True,
    "schemaVersion": "REC-1.0",
}

_NON_COMPOSITE_REC = {
    "id": "REC_" + "a" * 64,
    "text": "Head coach announced a quarterback change.",
    "isComposite": False,
    "schemaVersion": "REC-1.0",
}

_TRIPLE_COMPOSITE_REC = {
    "id": "REC_" + "c" * 64,
    "text": "Team won Monday and lost Tuesday and benched the starter.",
    "isComposite": True,
    "schemaVersion": "REC-1.0",
}

# Fixed text inputs for is_composite determinism
_TEXT_INPUTS = [
    "Coach fired OC and promoted QB coach.",
    "Head coach announced a quarterback change.",
    "Team won Monday and lost Tuesday and benched the starter.",
    "Analysts described the defense as undisciplined.",
    "Owner approved deal and GM signed contract but coach resigned.",
]

# Fixed valid AU for validate_au determinism
_VALID_AU = {
    "schemaVersion": "AU-1.0",
    "id": "AU_" + "a" * 64,
    "text": "Coach fired the offensive coordinator.",
    "parentSourceID": "REC_" + "b" * 64,
    "sourceReference": _SOURCE_REF,
    "splitIndex": 0,
}


# ── Helper ────────────────────────────────────────────────────────────────────

def _all_equal(results: list) -> bool:
    """Return True if all elements in results are equal (value equality)."""
    return all(r == results[0] for r in results)


# ── Helper self-tests ─────────────────────────────────────────────────────────

def test_all_equal_true_for_identical():
    assert _all_equal([1, 1, 1, 1, 1]) is True


def test_all_equal_false_for_divergent():
    assert _all_equal([1, 1, 2, 1, 1]) is False


# ── is_composite determinism ──────────────────────────────────────────────────

def test_is_composite_determinism_all_inputs():
    """is_composite must return the same bool for each input across _RUNS."""
    for text in _TEXT_INPUTS:
        results = [is_composite(text) for _ in range(_RUNS)]
        assert _all_equal(results), (
            f"is_composite diverged across {_RUNS} runs for input: {text!r}"
        )


# ── split_rec composite — AU id determinism ───────────────────────────────────

def test_split_rec_composite_au_ids_determinism():
    """split_rec on composite REC must produce identical AU id list each run."""
    results = []
    for _ in range(_RUNS):
        aus, _pcrs, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
        results.append([au["id"] for au in aus])
    assert _all_equal(results)


def test_split_rec_triple_composite_au_ids_determinism():
    """split_rec on 3-clause composite must produce identical AU ids each run."""
    results = []
    for _ in range(_RUNS):
        aus, _pcrs, _rejs = split_rec(_TRIPLE_COMPOSITE_REC, _SOURCE_REF)
        results.append([au["id"] for au in aus])
    assert _all_equal(results)


# ── split_rec composite — AU count determinism ────────────────────────────────

def test_split_rec_composite_au_count_determinism():
    """split_rec must produce the same number of AUs each run."""
    results = [
        len(split_rec(_COMPOSITE_REC, _SOURCE_REF)[0])
        for _ in range(_RUNS)
    ]
    assert _all_equal(results)


# ── split_rec composite — PCR determinism ─────────────────────────────────────

def test_split_rec_composite_pcr_determinism():
    """split_rec must produce an identical PCR dict each run."""
    results = []
    for _ in range(_RUNS):
        _aus, pcrs, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
        results.append(pcrs[0])
    assert _all_equal(results)


# ── split_rec composite — AU schemaVersion stability ─────────────────────────

def test_split_rec_composite_au_schema_version_determinism():
    """AU schemaVersion must be identical across all runs."""
    results = []
    for _ in range(_RUNS):
        aus, _pcrs, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
        results.append([au["schemaVersion"] for au in aus])
    assert _all_equal(results)


# ── split_rec non-composite — AU id determinism ───────────────────────────────

def test_split_rec_non_composite_au_id_determinism():
    """split_rec on non-composite REC must produce identical AU id each run."""
    results = []
    for _ in range(_RUNS):
        aus, _pcrs, _rejs = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
        results.append(aus[0]["id"])
    assert _all_equal(results)


# ── validate_au determinism ───────────────────────────────────────────────────

def test_validate_au_determinism_valid_input():
    """validate_au must return None on every run for a valid AU."""
    results = [validate_au(_VALID_AU) for _ in range(_RUNS)]
    assert all(r is None for r in results)


# ── make_atomicity_rejection determinism ──────────────────────────────────────

def test_make_atomicity_rejection_determinism():
    """make_atomicity_rejection must produce identical dicts each run."""
    results = [make_atomicity_rejection(_COMPOSITE_REC) for _ in range(_RUNS)]
    assert _all_equal(results)


def test_make_atomicity_rejection_reason_code_stability():
    """reasonCode in rejection record must be identical across all runs."""
    results = [
        make_atomicity_rejection(_COMPOSITE_REC)["reasonCode"]
        for _ in range(_RUNS)
    ]
    assert _all_equal(results)


# ── Version constant stability ────────────────────────────────────────────────

def test_au_id_version_stability():
    """AU_ID_VERSION must be identical across _RUNS reads (pinned literal)."""
    results = [AU_ID_VERSION for _ in range(_RUNS)]
    assert _all_equal(results)


def test_gsd_composite_ruleset_version_stability():
    """GSD_COMPOSITE_RULESET_VERSION must be identical across _RUNS reads."""
    results = [GSD_COMPOSITE_RULESET_VERSION for _ in range(_RUNS)]
    assert _all_equal(results)
