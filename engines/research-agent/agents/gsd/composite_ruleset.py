"""
gsd/composite_ruleset.py

GSD-layer canonical composite detection façade.

This module is the single import point for composite detection within the
atomicity enforcement layer (GSD). It re-exports the detection function and
rule version from extraction.composite_marker, which is the authoritative
implementation, and adds a GSD-layer version pin.

Design decision:
  Logic lives exclusively in extraction/composite_marker.py.
  This module does NOT reimplement detection. It exists to:
    1. Formalize the GSD-layer / extraction-layer boundary.
    2. Provide a stable import surface for AtomicityEnforcer.
    3. Version the GSD-layer composite contract independently of the
       extraction-layer rule version.

Invariant compliance:
  INV-1: No module-level mutable state.
  INV-2: No fingerprint or canonical ID computation.
  INV-5: GSD_COMPOSITE_RULESET_VERSION is a pinned constant.
         Identical input to is_composite always produces identical output.
"""

from engines.research_agent.agents.extraction.composite_marker import (  # noqa: F401
    COMPOSITE_DETECTION_RULE_VERSION,
    ERR_COMPOSITE_BOUNDARY_UNCLEAR,
    is_composite,
)

# GSD-layer version pin for the composite detection contract.
# Increment only when the GSD-layer contract changes independently of the
# extraction-layer detection rule (e.g., new dispatch logic is added here).
# Must never be derived from environment variables or runtime sources.
GSD_COMPOSITE_RULESET_VERSION: str = "1.0"
