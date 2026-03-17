EVENT MATERIAL IDENTIFIER (EMI)
CONTRACT v1.0 — Stabilized
Pre-Classification Structural Gate — Atomic Event Enforcement Layer

I. PURPOSE
The Event Material Identifier (EMI) is a deterministic, stateless structural gate operating within the Extraction Layer.
EMI ensures atomic event eligibility for NCA.
EMI performs:
* Discrete event detection
* Deterministic composite splitting
* Event object extraction
* Atomicity enforcement
EMI does not:
* Classify events (CME vs CSN)
* Evaluate CME threshold
* Enrich schema
* Normalize semantics
* Detect pressure
* Detect conflict type
* Assign standalone subclass
* Interpret meaning
* Mutate original seeds
* Maintain memory
* Perform inference
EMI is a fork gate, not a supervisor.

II. JURISDICTION CLAUSE
EMI operates on all raw Extraction outputs prior to PLOE and NCA.
EMI does not operate on:
* Narrative Event Seeds already validated
* Media Context Seeds (as classified upstream)
* Pattern layer artifacts
* Canonical units
EMI precedes:
* PLOE
* NCA
NCA assumes atomic Narrative Event Seeds
NARRATIVE CLASSIFICATION AGENT …
Therefore EMI must enforce atomic event purity before NCA receives input.

III. CORE ONTOLOGICAL STATEMENT
EMI ensures atomic event eligibility for NCA.
This is its sole governing principle.

IV. EVENT ELIGIBILITY TEST (OCCURRENCE GATE)
An event shall be extracted if and only if all conditions below are satisfied.

1️⃣ Completed Occurrence Requirement
The action must be asserted as a completed, discrete occurrence within the unit itself.
Accepted examples:
* “Coach announced…”
* “Team fired…”
* “Practice was cancelled…”
* “League suspended…”
Rejected examples:
* “Coach may…”
* “Coach might…”
* “Reports suggest…”
* “Sources say…”
* Hypothetical or future-only framing
If presented only via speculation, rumor, or reporting language:→ No extraction→ Route to Media Context lane
EMI does not rewrite or truncate units to isolate event clauses.Extraction must rely on clause-level separability present in original structure.

2️⃣ Actor Attribution Requirement
The unit must contain a deterministically attributable actor group.
If actor is unclear, implicit, or requires inference:→ Reject seed
No placeholder actors permitted.No inference permitted.

3️⃣ Ledger Mutation Rule (Atomicity Definition)
Atomicity is defined as:
Single ledger mutation.
Ledger mutation is defined as:
Any discrete, completed, publicly legible occurrence eligible for canonical event recording, including:
* Structural mutations (hire, fire, sign, suspend, promote, role change, etc.)
* Public speech acts (announcement, criticism, declaration)
* Enumerated unusual procedural adjustments
Atomic unit = one ledger mutation.
No composite ledger mutations permitted within a single Event Object.

4️⃣ Granularity Rule
If a unit contains multiple completed, separable ledger mutations:
→ Extract each as separate Event Objects
Example:“Team fired OC and promoted QB coach.”→ Two atomic events
If composite boundary cannot be deterministically separated:→ Reject seed
No partial extraction permitted.

5️⃣ Event + Structural Clause Rule
If unit contains:
Discrete event + structural condition
→ Extract event object→ Pass original seed unchanged to PLOE
No stripping.No rewriting.No mutation.
Parallel fork.

6️⃣ Nested Action Clause Rule
If action contains future consequence:
“Coach announced he will bench QB next week.”
→ Extract only the completed announcement event→ Future action not extracted
Only completed ledger mutations qualify.

7️⃣ Public Speech Acts
Public speech acts are atomic events if:
* Publicly legible
* Completed
* Actor-attributed
Speech acts qualify as ledger mutations.
Durability classification is NCA’s responsibility.

8️⃣ Procedural Micro-Adjustments
Procedural adjustments qualify only if marked unusual.
Unusual = TRUE only if the unit contains an explicit deviation marker from a locked lexicon, including:
* first time
* unexpected
* unprecedented
* emergency
* cancellation
* league-mandated
* due to hazard
No baseline comparison allowed.No inference allowed.
If unusual marker absent:→ Do not extract

V. COMPOSITE SPLITTING DOCTRINE
If a seed contains multiple completed, separable ledger mutations:
→ Extract each as separate Event Objects
If composite structure cannot be deterministically separated:→ Reject seed
No partial extraction.

VI. REJECTION CONDITIONS
EMI shall reject a seed if:
* Event detection ambiguous
* Composite boundary unclear
* Actor attribution missing
* Speculative or conditional framing only
* Ledger mutation not completed
* No deterministically separable occurrence-level clause present
* Event clause inseparable from discourse framing
Rejection must include deterministic reason code.
No silent suppression permitted.

VII. PARALLEL FORK RULE
If seed qualifies as both:
Pressure-Capable Seed + Event Material
→ Event Object extracted→ Original seed continues unchanged to PLOE
EMI does not suppress pressure routing.

VIII. OUTPUT STRUCTURE
For each extracted event:


{
  "eventID": "<uniqueID>",
  "sourceSeedID": "<originalSeedID>",
  "actorGroup": "<actor as stated>",
  "actionVerb": "<verbatim action verb>",
  "ledgerMutation": true,
  "unusualProcedural": true | false
}

No classification field.No CME evaluation.No standalone subclass.No narrative metadata.No semantic normalization.No domain inference.No time inference.
Original seed remains unchanged.

IX. DETERMINISM LOCK
EMI must be:
* Stateless
* Binary (no confidence scoring)
* Input-dependent only
* Context-agnostic
* Memoryless
* Non-recursive
Given identical input, EMI must produce identical output.

X. RELATIONSHIP TO NCA
EMI guarantees:
* Atomic Narrative Event Seeds
* Non-composite Event Objects
* No speculative events
NCA shall reject composite or non-event units
NARRATIVE CLASSIFICATION AGENT …
EMI exists to prevent such rejection from occurring downstream.
EMI does not cleanse or modify seeds for NCA.It extracts only eligible atomic events.

XI. ARCHITECTURAL POSITION
Extraction→ EMI  → Event Objects (Narrative lane → NCA)  → Original Seed (Pressure lane → PLOE)
EMI never writes back to the seed.EMI never mutates canonical units.
EMI is a structural enforcement gate only.

XII. IDENTITY LOCK
EMI is:
DeterministicAtomicity-enforcingNon-interpretiveNon-classifyingNon-supervisoryFork-basedPre-classificationImmutable-source respecting

XIII. SYSTEM STABILITY GUARANTEE
Because EMI:
* Does not mutate seeds
* Does not classify
* Does not interpret
* Does not maintain memory
* Does not normalize semantics
It cannot contaminate:
* Pressure detection
* Conflict type activation
* Arc motif detection
* Pattern engine logic
It preserves lane purity.

XIV. COMPLETENESS STATEMENT
This contract is internally consistent with:
* NCA v1.0 jurisdiction boundary NARRATIVE CLASSIFICATION AGENT …
* CME Persistence Threshold
* Standalone taxonomy
* Pressure lane isolation
* Stateless determinism
EMI v1.0 is architecturally closed and stable.
