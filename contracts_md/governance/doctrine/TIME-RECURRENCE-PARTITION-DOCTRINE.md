TIME & RECURRENCE PARTITION DOCTRINE — v1.0
I. PURPOSE
This doctrine formally partitions:
* Temporal identity participation
* Recurrence modeling
* Extraction neutrality
It prevents temporal leakage across lanes and prohibits recurrence from influencing extraction behavior.

II. CORE AXIOM
Time participates in canonical identity only when ontology is occurrence-based.
Time does not participate in canonical identity when ontology is structural-type-based.
Recurrence is never modeled during extraction.

III. LANE-SPECIFIC TIME RULES
1️⃣ Narrative Lane (Occurrence Ontology)
Narrative objects represent discrete events in time.
Therefore:
* timestampContext SHALL participate in ANE fingerprinting.
* Each discrete occurrence at a different time SHALL produce a distinct canonical identity.
* Event identity is occurrence-bound.
* Two identical actions in different time contexts are distinct narrative events.
Rationale:Narrative ontology captures what happened, and events are temporally anchored by definition.

2️⃣ Pressure Lane (Structural-Type Ontology)
Pressure objects represent structural asymmetry types.
Therefore:
* timestampContext SHALL NOT participate in CPS fingerprinting.
* Canonical CPS identity SHALL be time-neutral.
* Structural asymmetries are defined independent of when they manifest.
* Identical structural patterns across different time windows SHALL resolve to the same canonical CPS ID.
Rationale:Pressure ontology captures structural conditions, not temporal occurrences.

IV. EXTRACTION NEUTRALITY RULE
Extraction SHALL operate memorylessly.
Extraction SHALL NOT:
* Check prior canonical IDs
* Suppress repeated structural types
* Suppress repeated event types
* Modify seed typing based on recurrence
* Query historical presence
* Adjust thresholds due to prior frequency
Atomicity enforcement, seed typing, critic evaluation, and canonical transformation SHALL remain recurrence-agnostic.

V. RECURRENCE MODELING BOUNDARY
Recurrence is permitted only at:
* PQG (Pipeline Quality Governor)
* Narrative Engine modeling layer
* Post-canonical analytics systems
Recurrence SHALL be modeled as:
CanonicalID + CycleAssociationLog
Recurrence SHALL NOT alter canonical identity.

VI. CANONICAL ID INVARIANTS
Narrative Lane
Canonical identity = structural fields + timestampContext
Pressure Lane
Canonical identity = structural fields onlyTime excluded
Cycle metadata SHALL NEVER participate in canonical identity in any lane.

VII. PROHIBITIONS
The system SHALL NOT:
* Encode recurrence into fingerprint recipes
* Encode recurrence into seed typing
* Encode recurrence into critic evaluation
* Encode recurrence into canonical transformation
* Create time-fragmented pressure identities
* Collapse distinct narrative events across time

VIII. DETERMINISM LOCK
Given identical:
* Source material
* Registry versions
* Fingerprint version
* Schema versions
Canonical identities MUST resolve identically across replays.
No recurrence-aware logic is permitted during identity formation.

IX. ARCHITECTURAL CONSEQUENCE
This doctrine enforces:
* Narrative = occurrence modeling
* Pressure = structural-type modeling
* Recurrence = analytics-only layer
* Extraction = memoryless and neutral
* Canonical identity = stable and replay-safe

## TIME PARTICIPATION AUTHORITY CLAUSE

Time participation in canonical identity is lane-governed.

Pressure Lane:
Time participation rules are defined exclusively within PSTA v4.

Narrative Lane:
Time participation rules are defined exclusively within
the 2B Structural Assembler fingerprint specification.

No other agent, contract, or doctrine may:

- Add time fields to canonical identity
- Remove time fields from canonical identity
- Modify timestamp participation in fingerprint derivation
- Introduce time-bucket–based identity mutation
- Alter recurrence semantics at canonical layer

Time may influence canonical identity only if defined
by the lane's mint authority contract.

All other documents must treat time as non-identity-bearing.

