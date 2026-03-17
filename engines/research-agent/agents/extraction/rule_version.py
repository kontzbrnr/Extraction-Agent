"""
extraction/rule_version.py

Extraction rule version lock.

Contract authority:
  - GLOBAL-SPLIT-DOCTRINE.md (GSD) Section X: Determinism Lock
    "Given identical input REC text and identical rule version,
    Atomicity Enforcement must produce identical: AU set (order + content),
    PCR retention decision, rejection decisions + reason codes."
  - CREATIVE-LIBRARY-EXTRACTION-AGENT.md Section XII:
    "Given identical source material and identical rule version:"

EXTRACTION_RULE_VERSION is the single source of truth for the extraction rule
set version. It must be imported by ExtractionAuditLog (Phase 3.6) to satisfy
the GSD Section X Determinism Lock requirement.

This constant is distinct from:
  - Schema versions (e.g., "REC-1.0" in rec.schema.json schemaVersion field)
  - Per-rule constants (e.g., COMPOSITE_DETECTION_RULE_VERSION in composite_marker.py)

Increment EXTRACTION_RULE_VERSION when any extraction rule changes such that
identical source material could produce different output under the new rules.

INV-1: No module-level mutable state.
INV-5: Constant value. Identical across all runs. Replay-safe.
"""

# Extraction rule set version.
# Anchors replay determinism per GSD Section X and CREATIVE-LIBRARY-EXTRACTION-AGENT.md XII.
# Must never be derived from environment variables, config files, or any runtime source.
EXTRACTION_RULE_VERSION: str = "1.0"
