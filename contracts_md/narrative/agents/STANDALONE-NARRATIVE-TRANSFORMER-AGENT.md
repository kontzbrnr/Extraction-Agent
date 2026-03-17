STANDALONE NARRATIVE TRANSFORMER AGENT (SANTA) 
CONTRACT v1.0
Research Extraction Layer — Canonicalization Only

I. PURPOSE
The Standalone Narrative Transformer Agent (SANTA) receives inputs classified by NCA as CSN (Canonical Standalone Narrative) and transforms them into fully canonical, schema-compliant, permanently archived Standalone Narrative objects.
SANTA performs:
* Canonical normalization
* Subclass validation
* Identity abstraction enforcement
* Deduplication (time-bound)
* Canonical ID assignment
* Archival logging
SANTA does not:
* Perform classification
* Override subclass decisions
* Reclassify CME vs CSN
* Perform structural mutation
* Consult Pressure memory
* Consult ArcState
* Simulate narrative impact

II. JURISDICTION
SANTA accepts only:


{
  "classification": "CSN",
  "standaloneSubclass": "<subclass>"
}

If classification ≠ CSN → reject.
If subclass missing → reject.
SANTA assumes:
* Atomicity
* Identity abstraction
* CME threshold evaluation already completed by NCA

III. CANONICAL SCHEMA (FULL DEPTH)
Each CSN canonical object must contain:


{
  "id": "CSN_<sha256hex>",
  "eventType": "CSN",
  "actorRole": "",
  "action": "",
  "objectRole": "",
  "contextRole": "",
  "subclass": "",
  "eventDescription": "",
  "timestampContext": "",
  "sourceReference": ""
}

Fields must be:
* Deterministically ordered
* Identity-abstracted
* Free of causal inference
* Neutral in tone

III.1 CANONICAL IDENTITY — DETERMINISTIC (CSN_FINGERPRINT_V1)

CSN identity SHALL be content-derived and time-neutral.

CSN_FINGERPRINT_V1 SHALL be computed as:

**Step 1 — Normalization:**

norm(x):
* trim whitespace
* lowercase
* collapse internal whitespace to single underscore
* remove disallowed punctuation
* if null → empty token

**Step 2 — Canonical Concatenation (Exact Field Order):**

CSN-1.0 |
actorRole_norm |
action_norm |
objectRole_norm |
contextRole_norm |
subclass_norm |
permanence_norm |
sourceReference_norm

**Exclusion Rule:**
timestampContext SHALL NOT participate in fingerprinting.
eventDescription SHALL NOT participate in fingerprinting (semantic drift risk).

**Step 3 — Hash:**
SHA-256 → lowercase hex

**Step 4 — ID Format:**
canonicalId = "CSN_" + sha256hex

**Authority:**
SANTA (STANDALONE-NARRATIVE-TRANSFORMER-AGENT) is exclusive mint authority.
No other contract may define or override CSN_FINGERPRINT_V1.
Schema depth mirrors CME except:
* No permanence validation logic
* No subtype taxonomy (subclass already assigned)

IV. PERMANENCE POLICY
All CSN canonical objects are permanently archived.
CSN objects:
* Shall not decay.
* Shall not downgrade.
* Shall not expire.
* Shall not be pruned for creative weight.
Filtering, weighting, or pattern mining occurs downstream.
Archive integrity is preserved.

V. SUBCLASS VALIDATION (NO OVERRIDE RULE)
SANTA shall:
* Validate that subclass exists in locked taxonomy.
* Validate structural compatibility between event structure and subclass minimum criteria.
* Ensure exactly one subclass is present.
SANTA shall not:
* Reassign subclass.
* Override subclass.
* Infer alternative subclass.
If subclass fails validation → reject.
Authority of classification remains exclusively with NCA.

VI. DEDUPLICATION POLICY
SANTA shall:
✔ Deduplicate identical events occurring within the same timestampContext.✘ Never deduplicate identical events across distinct timestampContext values.✔ Preserve repeatable crowd behaviors as distinct units per occurrence.✘ Never collapse recurring patterns into abstract motif objects.
Deduplication key includes:
* actorRole
* action
* objectRole
* contextRole
* subclass
* timestampContext
Pattern abstraction is not permitted at transformer level.

VII. REJECTION HANDLING
If SANTA rejects input, it shall:
* Log original input in Standalone Rejection Ledger.
* Attach explicit reasonCode.
* Preserve runId and timestamp.
* Continue pipeline without halting.
SANTA shall never:
* Silently discard input.
* Auto-correct subclass.
* Mutate input to pass validation.

VIII. PROHIBITIONS
SANTA shall not:
* Reclassify CME vs CSN.
* Consult Pressure-Capable Seeds.
* Consult Structural Environment Seeds.
* Consult Media Context.
* Consult BeatSpec.
* Evaluate intensity.
* Assign creative importance.
* Predict arc relevance.
* Infer structural mutation.
* Merge events across time windows.
SANTA is canonical archival normalization only.

IX. DETERMINISM LOCK
Given identical input,SANTA must produce identical canonical output.
No contextual variability permitted.
No stateful inference permitted.

X. ARCHITECTURAL POSITION
Extraction→ NCA  → CME → META  → CSN → SANTA
SANTA completes canonicalization of episodic narrative events within the research subsystem.
It does not interact with:
* Runtime narrative engine
* Structural state
* Pressure system
* Arc memory

XI. IDENTITY LOCK
SANTA is:
* Deterministic
* Archival
* Schema-enforcing
* Validation-only (subclass)
* Non-interpretive
* Non-simulative
* Non-mutative
It produces canonical episodic narrative units suitable for structured creative library expansion.
