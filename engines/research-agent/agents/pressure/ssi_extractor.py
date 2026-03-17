"""
pressure/ssi_extractor.py

Deterministic NLP extraction using spaCy — Phase 7.2

Model loaded once at module level. Never mutated.

Contract authority:
    STRUCTURAL-SIGNAL-INTERPRETER.md

Invariant compliance:
    INV-1: _NLP loaded at module level. Never mutated.
    INV-5: Identical input → identical output given pinned model version.
           spaCy version assertion at import time.
"""

from __future__ import annotations

import spacy

from engines.research_agent.agents.pressure.ssi_schema import SPACY_MODEL_NAME, SPACY_MODEL_VERSION_PREFIX

# ── Import-time version assertion (INV-5) ─────────────────────────────────────

assert spacy.__version__.startswith(SPACY_MODEL_VERSION_PREFIX), (
    f"spaCy version mismatch: expected {SPACY_MODEL_VERSION_PREFIX}.x, "
    f"got {spacy.__version__}. Pinned for INV-5."
)

# ── Model loading (INV-1) ─────────────────────────────────────────────────────

_NLP = spacy.load(SPACY_MODEL_NAME)


# ── Extraction function ───────────────────────────────────────────────────────

def extract_structural_fields(
    observation_text: str,
) -> tuple[str | None, str | None, str | None]:
    """Extract structural fields from observation text using dependency parsing.

    Returns (actorGroup_raw, action_raw, objectRole_raw).
    Returns None for any field that cannot be extracted.

    Strategy:
      actorGroup_raw : nsubj (or nsubjpass) of root token, including
                       compound modifiers. Fallback: first noun chunk.
      action_raw     : root verb lemma.
      objectRole_raw : dobj or pobj of root token, including compound
                       modifiers and amod. Fallback: last noun chunk that
                       is not the subject chunk.

    All spans are stripped and lowercased for normalization.

    INV-5: Deterministic given pinned spaCy model version.
    """
    doc = _NLP(observation_text)

    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    if root is None:
        return None, None, None

    # action_raw: root verb lemma
    action_raw = root.lemma_.strip().lower() if root.pos_ == "VERB" else None

    # actorGroup_raw: nsubj / nsubjpass span
    actor_group_raw: str | None = None
    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass") and token.head == root:
            span_tokens = [
                t for t in doc
                if t.dep_ == "compound" and t.head == token
            ] + [token]
            span_tokens.sort(key=lambda t: t.i)
            actor_group_raw = " ".join(t.text for t in span_tokens).strip().lower()
            break
    if actor_group_raw is None:
        chunks = list(doc.noun_chunks)
        if chunks:
            actor_group_raw = chunks[0].text.strip().lower()

    # objectRole_raw: dobj / pobj of root
    object_role_raw: str | None = None
    for token in doc:
        if token.dep_ in ("dobj", "pobj") and token.head == root:
            span_tokens = [
                t for t in doc
                if t.dep_ in ("compound", "amod") and t.head == token
            ] + [token]
            span_tokens.sort(key=lambda t: t.i)
            object_role_raw = " ".join(t.text for t in span_tokens).strip().lower()
            break
    if object_role_raw is None:
        chunks = list(doc.noun_chunks)
        subject_text = actor_group_raw or ""
        candidates = [c for c in chunks if c.text.strip().lower() != subject_text]
        if candidates:
            object_role_raw = candidates[-1].text.strip().lower()

    return actor_group_raw, action_raw, object_role_raw
