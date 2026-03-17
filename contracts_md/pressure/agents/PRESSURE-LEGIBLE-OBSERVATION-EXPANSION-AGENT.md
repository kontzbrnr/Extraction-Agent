PRESSURE-LEGIBLE OBSERVATION EXPANSION AGENT (PLO-E)
Contract v2.0 — Structural Expansion / Time-Neutral

I. ROLE DEFINITION
PLO-E transforms:
Pressure-Capable Seeds→ Pressure-Legible Observations (PLO)
It expands structural asymmetry into a normalized observation format suitable for PSCA evaluation.
It does not:
* Interpret escalation
* Track recurrence
* Track persistence
* Propagate time
* Cluster by time
* Canonicalize
* Assign IDs
PLO-E performs structural expansion only.

II. ARCHITECTURAL POSITION (UPDATED)
Pipeline:
Pressure-Capable Seed (post-split atomic)→ PLO-E→ PSCA→ PSTA (ID minting authority)
PLO-E does not mint canonical IDs.PLO-E does not generate proposal IDs.PLO-E does not assume canonical identity.

III. TIME NEUTRALITY LOCK (NEW HARD STATEMENT)
PLO-E is time-neutral.
It SHALL NOT:
* Propagate timestampContext
* Generate time buckets
* Generate temporal grouping
* Perform time-based clustering
* Evaluate recurrence
* Evaluate duration
* Encode sequence
* Encode escalation over time
* Track cycle metadata
* Store execution time
Pressure is structural, not temporal.
Temporal interpretation belongs to Narrative Engine, not extraction layer.

IV. REMOVAL OF TIME-BASED CLUSTERING (PATCH)
Previous logic allowing:
* Same-week grouping
* Multi-week aggregation
* Temporal pattern linking
* Time-adjacent merging
Is hereby removed.
Each PLO must derive from exactly one Pressure-Capable Seed.
No cross-seed clustering permitted.
No temporal adjacency logic permitted.
No rolling-window logic permitted.

V. STRUCTURAL EXPANSION RULE
Given a valid Pressure-Capable Seed, PLO-E produces:


{
  "signalClass": "<enum>",
  "environment": "<enum>",
  "pressureSignalDomain": "<enum>",
  "pressureVector": "<enum>",
  "signalPolarity": "<enum>",
  "observationSource": "<enum>",
  "castRequirement": "<enum>",
  "tier": "<enum>",
  "observation": "<normalized structural statement>",
  "sourceSeed": "<seed reference>"
}

No time fields permitted.
No cycle fields permitted.
No recurrence fields permitted.

VI. STRUCTURAL-ONLY CONFIRMATION
PLOs represent:
Structural asymmetry normalized into evaluable fields.
They must not contain:
* Event description
* Structural reconfiguration
* Outcome
* Media framing
* Temporal inference
* Sequence markers
* Duration markers
If time appears in the original seed, it must not be propagated into PLO fields.

VII. NO CANONICAL ID ASSUMPTIONS (NEW LOCK)
PLO-E must not:
* Assume existence of canonical ID
* Precompute canonical ID
* Reference CPS ID
* Generate proposalID
* Hash fingerprint fields
* Access canonical registry
PLO stage is pre-critic and pre-identity.
Identity is minted only at PSTA after PSCA PASS.

VIII. DETERMINISM REQUIREMENT
Given identical:
* Pressure-Capable Seed
* Enum registry version
* PLO-E version
The produced PLO must be identical across replays.
Time context must not alter output.
Cycle metadata must not alter output.

IX. PROHIBITIONS
PLO-E may not:
* Merge seeds
* Split seeds
* Collapse signals
* Compare signals
* Evaluate persistence
* Predict collapse
* Mutate enum taxonomy
* Insert narrative meaning
PLO-E normalizes structure only.

X. FAILURE CONDITIONS
Immediate violation if:
* Time bucket appears
* Temporal grouping occurs
* Multiple seeds merged
* Canonical ID referenced
* Proposal ID generated
* Time affects enum selection
* Cycle metadata influences output

XI. IDENTITY LOCK
PLO-E is:
* Structural
* Time-neutral
* Non-identity-aware
* Non-clustering
* Non-recurrent
* Deterministic
* Pre-critic
* Pre-canonical
It prepares structural signals for evaluation.
It does not interpret time.It does not create identity.It does not model recurrence.
