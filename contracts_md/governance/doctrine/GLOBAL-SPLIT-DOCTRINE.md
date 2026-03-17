GLOBAL SPLIT DOCTRINE (GSD) — CONTRACT v1.0
Atomicity Enforcement Layer — Pre-Typing Structural Law
I. Core Principle
1. Atomicity is a global invariant. No seed type may contain composite material.
2. Seed typing is permitted only on atomic units.
3. Splitting is non-destructive. It creates sibling units; it never removes clauses from the source.
II. Definitions
* Raw Extraction Candidate (REC): Untyped text unit extracted from source material. May be composite.
* Composite REC: REC containing more than one separable ontological component (event, structural configuration, pressure asymmetry, media framing/discourse).
* Atomic Unit (AU): Post-split, indivisible unit containing exactly one ontological component eligible for seed typing.
* Seed: An atomic, post-split structural unit eligible for classification and routing (typed into exactly one seed category).
* Parent Composite Record (PCR): The original composite REC retained for traceability; never typed.
III. Pipeline Position
Extraction (REC generation)→ Atomicity Enforcement (Global Split Doctrine)→ Seed Typing (Pressure / Structural / Narrative Event / Media Context)→ Downstream lane agents (EMI/NCA/META/SANTA, PLO-E/PST, STA, Context registry)
Composite detection and splitting occur before any seed typing.
IV. Composite Detection Authority
Composite detection is global and must occur at the Extraction layer before seed typing. No lane-specific composite detection is permitted.
V. Split Mechanics
1. If a REC is composite and deterministically separable, produce:
    * Sibling Atomic Units (AU₁…AUₙ), each containing exactly one ontological component.
    * PCR retained unchanged for audit/replay.
2. No clause removal, truncation, paraphrase, or rewriting is permitted.
3. Each AU must maintain a pointer to its origin:
    * parentSourceID (PCR or REC id)
    * sourceReference (article/cluster pointer)
VI. Rejection Rule (Boundary Unclear)
If a composite REC contains multiple components but cannot be deterministically separated, it is rejected at Atomicity Enforcement (pre-typing).
* No partial extraction.
* No downstream deferral.
* Rejection must log a deterministic reason code.
VII.1. If a REC is composite and deterministically separable, produce:
    * Sibling Atomic Units (AU₁…AUₙ), each containing exactly one ontological component.
    * PCR retained unchanged for audit/replay.
2. No clause removal, truncation, paraphrase, or rewriting is permitted. Cross-Lane Outputs
A single composite REC may yield siblings typed into different seed types. This is expected and permitted.
Example:“Coach fired OC and retained play-calling duties.”→ Narrative Event Seed + Structural Environment Seed
VIII. Applicability
This doctrine applies equally to all seed types:
* Pressure-Capable Seeds
* Structural Environment Seeds
* Narrative Event Seeds
* Media Context Seeds
No exceptions.
IX. Status of the Parent Composite Record
The PCR is retained but never typed, never routed, and never enters downstream lane agents. It exists only for:
* audit and replay
* governance telemetry
* debugging split/rejection rates
X. Determinism Lock
Given identical input REC text and identical rule version, Atomicity Enforcement must produce identical:
* AU set (order + content)
* PCR retention decision
* rejection decisions + reason codes
