"""
nca/nca_ontology.py
NCA Subclass Ontology — Phase 9.2.1
Versioned, frozen taxonomy. No runtime expansion permitted.
Contract authority: NARRATIVE-CLASSIFICATION-AGENT.md v1.0 §VII
Registry authority: enums/narrative/registry.json (ENUM_v1.0)
Governance ruling: 2026-03-08 (narrative_singularity reserved — not
                   assignable by NCA v1.0; context-agnostic constraint)
Invariants: INV-1 (no mutable state), INV-5 (frozen taxonomy)
"""

NCA_VERSION: str = "NCA-1.0"
NCA_SUBCLASS_TAXONOMY_VERSION: str = "NCA_SUBCLASS_TAXONOMY-1.0"
NCA_RULE_LOGIC_VERSION: str = "NCA_RULE_LOGIC-1.0"

NCA_CLASSIFICATION_CME: str = "CME"
NCA_CLASSIFICATION_CSN: str = "CSN"

REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION: str = (
    "REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION"
)

NCA_SUBCLASS_NARRATIVE_SINGULARITY: str = "narrative_singularity"
NCA_SUBCLASS_CROWD_EVENT: str = "crowd_event"
NCA_SUBCLASS_RITUAL_MOMENT: str = "ritual_moment"
NCA_SUBCLASS_ANECDOTAL_BEAT: str = "anecdotal_beat"
NCA_SUBCLASS_PROCEDURAL_CURIOSITY: str = "procedural_curiosity"
NCA_SUBCLASS_CONFLICT_FLASHPOINT: str = "conflict_flashpoint"

NCA_SUBCLASS_VALUES: frozenset[str] = frozenset(
    {
        "narrative_singularity",
        "crowd_event",
        "ritual_moment",
        "anecdotal_beat",
        "procedural_curiosity",
        "conflict_flashpoint",
    }
)

NCA_ASSIGNABLE_SUBCLASSES: frozenset[str] = frozenset(
    {
        "crowd_event",
        "ritual_moment",
        "anecdotal_beat",
        "procedural_curiosity",
        "conflict_flashpoint",
    }
)

NCA_REQUIRED_INPUT_FIELDS: frozenset[str] = frozenset(
    {
        "actorRole",
        "action",
        "unusualProcedural",
    }
)

assert len(NCA_SUBCLASS_VALUES) == 6, (
    f"NCA_SUBCLASS_VALUES drift: expected 6, got {len(NCA_SUBCLASS_VALUES)}"
)
assert len(NCA_ASSIGNABLE_SUBCLASSES) == 5, (
    f"NCA_ASSIGNABLE_SUBCLASSES drift: expected 5, got {len(NCA_ASSIGNABLE_SUBCLASSES)}"
)
assert "narrative_singularity" in NCA_SUBCLASS_VALUES, (
    "narrative_singularity missing from ontology"
)
assert "narrative_singularity" not in NCA_ASSIGNABLE_SUBCLASSES, (
    "narrative_singularity must not be assignable in NCA v1.0"
)
assert NCA_ASSIGNABLE_SUBCLASSES < NCA_SUBCLASS_VALUES, (
    "NCA_ASSIGNABLE_SUBCLASSES must be a strict subset of NCA_SUBCLASS_VALUES"
)
assert NCA_VERSION == "NCA-1.0"
assert NCA_SUBCLASS_TAXONOMY_VERSION == "NCA_SUBCLASS_TAXONOMY-1.0"
assert NCA_RULE_LOGIC_VERSION == "NCA_RULE_LOGIC-1.0"
