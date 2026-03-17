r"""
REC Producer — Phase 3.2

Produces Raw Extraction Candidate (REC) dicts from caller-supplied text.

Schema:
  REC: schemas/rec.schema.json  (schemaVersion REC-1.0)

Fingerprinting (design decision — not contract-specified):
  norm(x): strip → lowercase → collapse \s+ to _ → remove [^a-z0-9_]
           None → ""
  REC id:  SHA-256("REC-1.0 | " + norm(text))      → "REC_<hex>"

INV-1: No disk reads. All values derived from call-time arguments only.
INV-2: Identity authority — extraction layer computes REC content hashes only.
       AU id computation belongs to Phase 4 (GSD — Global Split Doctrine).
INV-5: norm() uses re.sub with ASCII [^a-z0-9_]. UTF-8 encoding is
       mandatory. Separator " | " is locked. Do not change.
"""

from __future__ import annotations

import hashlib
import re

_SEP = " | "
_REC_VERSION = "REC-1.0"


def _norm(x: str | None) -> str:
    """
    Normalization pipeline (INV-5):
      None → ""
      trim → lowercase → collapse whitespace to _ → remove [^a-z0-9_]
    """
    if x is None:
        return ""
    s = x.strip()
    s = s.lower()
    s = re.sub(r'\s+', '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    return s


def _rec_id(text: str) -> str:
    """Compute REC id from text using locked formula."""
    payload = _REC_VERSION + _SEP + _norm(text)
    return "REC_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def produce_rec(text: str, is_composite: bool = False) -> dict:
    """
    Construct a REC dict from raw extracted text.

    Args:
        text:         Raw extracted text. Stored verbatim. No mutation.
        is_composite: Set True by atomicity enforcer only. Default False.

    Returns:
        Dict conforming to schemas/rec.schema.json.

    Raises:
        ValueError: text is empty or whitespace-only.
        TypeError:  text is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    if not text.strip():
        raise ValueError("text must be a non-empty, non-whitespace string")
    return {
        "schemaVersion": _REC_VERSION,
        "id": _rec_id(text),
        "text": text,
        "isComposite": is_composite,
    }


# ---------------------------------------------------------------------------
# EXTRACTION LAYER IDENTITY BOUNDARY (INV-2)
# _rec_id() and _norm() are the ONLY permitted identity operations in this
# file. They produce a content hash labelled "design decision — not
# contract-specified" in rec.schema.json. No other fingerprint or ID
# computation may be added to this module.
#
# AU production and AU id computation belong to Phase 4 (GSD).
# See gsd/ module — to be implemented in Phase 4.
# ---------------------------------------------------------------------------
