"""
Extraction audit log record builder.

Contract authority: roadmap 3.6, GSD Section X Determinism Lock.
No schema file exists. Record is in-memory only.
Caller is responsible for any persistence.

INV-1: No module-level mutable state.
INV-5: Identical inputs always produce identical output.
"""

from engines.research_agent.agents.extraction.rule_version import EXTRACTION_RULE_VERSION


def make_extraction_audit_log(
    rec_count: int,
    source_reference: str,
    rule_version: str = EXTRACTION_RULE_VERSION,
) -> dict:
    """Return a structured audit record for one extraction run.

    Args:
        rec_count: Number of Raw Extraction Candidates produced.
        source_reference: Reference to source material.
        rule_version: Extraction rule version (defaults to EXTRACTION_RULE_VERSION).

    Returns:
        Dict with keys: recCount, sourceReference, ruleVersion.

    Raises:
        ValueError: If rec_count < 0, source_reference is not a non-empty string,
                    or rule_version is not a non-empty string.
    """
    if rec_count < 0:
        raise ValueError(f"rec_count must be non-negative, got {rec_count}")

    if not isinstance(source_reference, str):
        raise ValueError(
            f"source_reference must be a string, got {type(source_reference).__name__}"
        )

    if not source_reference.strip():
        raise ValueError("source_reference must be non-empty after strip()")

    if not isinstance(rule_version, str):
        raise ValueError(
            f"rule_version must be a string, got {type(rule_version).__name__}"
        )

    if not rule_version.strip():
        raise ValueError("rule_version must be non-empty after strip()")

    return {
        "recCount": rec_count,
        "sourceReference": source_reference,
        "ruleVersion": rule_version,
    }
