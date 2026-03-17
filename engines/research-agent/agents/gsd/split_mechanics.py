"""
gsd/split_mechanics.py

Split Mechanics Engine — Phase 4.3

Transforms individual RECs into AU sets and PCR records
under the Global Split Doctrine.

Design decision — AU id formula (no authoritative spec recoverable):
  sha256((AU_ID_VERSION + "|" + parent_source_id + "|"
          + str(split_index) + "|" + text.strip()).encode("utf-8"))

  Rationale:
    - parent_source_id included: INV-4 lane isolation
      (same text from different parents yields different AU id)
    - split_index included: prevents sibling collision
      (same text at different positions yields different id)
    - AU_ID_VERSION pinned to "1.0": INV-5 replay determinism
    - text.strip() applied consistently before hashing

Invariant compliance:
  INV-1: No module-level mutable state.
  INV-2: No REC or PCR fingerprint computation. AU ids are GSD-layer only.
  INV-3: Input REC dicts are never mutated. All outputs are new dicts.
  INV-4: AU id formula includes parentSourceID — lane-isolated.
  INV-5: AU_ID_VERSION is a pinned literal. Formula is fully deterministic.
"""

from __future__ import annotations

import hashlib

from engines.research_agent.agents.extraction.composite_marker import (
    _CLAUSE_SPLIT_PATTERN,
    ERR_COMPOSITE_BOUNDARY_UNCLEAR,
)
from gsd.composite_ruleset import is_composite
from gsd.rejection_handler import make_atomicity_rejection

_AU_SCHEMA_VERSION: str = "AU-1.0"
_PCR_SCHEMA_VERSION: str = "PCR-1.0"
_SEP: str = "|"

# Pinned version for AU id computation. Never derive from env or config.
# INV-5: changing this value changes all AU ids — treat as a breaking change.
AU_ID_VERSION: str = "1.0"


def _au_id(parent_source_id: str, split_index: int, text: str) -> str:
    """Compute a deterministic, lane-isolated AU id.

    Hash input: AU_ID_VERSION | parent_source_id | split_index | text.strip()
    Prefix: "AU_"
    """
    payload = (
        AU_ID_VERSION
        + _SEP
        + parent_source_id
        + _SEP
        + str(split_index)
        + _SEP
        + text.strip()
    )
    return "AU_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def split_rec(rec: dict, source_reference: str) -> tuple[list[dict], list[dict], list[dict]]:
    """Split a single REC into AUs, PCRs, and (if boundary unclear) rejections.

    Three paths per GSD doctrine:
      1. isComposite False  → ([au], [], [])
      2. isComposite True, separable → ([au, ...], [pcr], [])
      3. isComposite True, boundary unclear → ([], [], [rejection_dict])

    Args:
        rec: A REC-1.0 conformant dict. Never mutated.
        source_reference: Caller-supplied article or cluster pointer.
                          Applied to every AU produced.
                          Never derived from REC content (INV-2).

    Returns:
        (aus, pcrs, rejections) where each element is a list.
        Exactly one of: aus non-empty, or rejections non-empty.
        Never raises on boundary-unclear input (INV-5 / GSD Section VI).
    """
    text: str = rec["text"]
    parent_source_id: str = rec["id"]

    if not is_composite(text):
        au = {
            "id": _au_id(parent_source_id, 0, text),
            "text": text,
            "parentSourceID": parent_source_id,
            "sourceReference": source_reference,
            "splitIndex": 0,
            "schemaVersion": _AU_SCHEMA_VERSION,
        }
        return [au], [], []

    # Composite path: split on conjunction boundary.
    raw_segments = _CLAUSE_SPLIT_PATTERN.split(text)
    segments = [s.strip() for s in raw_segments if s.strip()]

    if len(segments) < 2:
        return [], [], [make_atomicity_rejection(rec)]

    aus = [
        {
            "id": _au_id(parent_source_id, idx, segment),
            "text": segment,
            "parentSourceID": parent_source_id,
            "sourceReference": source_reference,
            "splitIndex": idx,
            "schemaVersion": _AU_SCHEMA_VERSION,
        }
        for idx, segment in enumerate(segments)
    ]

    pcr = {
        "parentSourceId": parent_source_id,
        "originalText": text,
        "splitCount": len(segments),
        "schemaVersion": _PCR_SCHEMA_VERSION,
    }

    return aus, [pcr], []
