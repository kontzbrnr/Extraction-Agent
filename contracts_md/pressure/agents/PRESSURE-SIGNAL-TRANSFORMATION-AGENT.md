PRESSURE-SIGNAL TRANSFORMATION AGENT — CONTRACT v4
(Post–PSCA / Deterministic / Stateless / Content-Derived Identity)

I. ROLE DEFINITION (REVISED)
The Pressure-Signal Transformation Agent (PSTA) converts critic-validated Pressure-Legible Observations into canonical pressure signal objects.
It performs:
* Structural normalization
* Enum validation (per CANONICAL ENUM REGISTRY v1.0)
* Deterministic content fingerprinting
* Canonical ID minting (post-critic PASS only)
It does not:
* Evaluate pressure strength
* Reclassify signals
* Perform deduplication across registry
* Access cross-run state
* Generate sequential identifiers
* Reference run metadata
* Interpret meaning
* Cluster signals
PSTA is purely transformational and identity-minting.

II. PIPELINE POSITION (CLARIFIED)
Correct order (LOCKED):
Extraction→ PLO-E→ PSCA (Critic Gate)→ PSTA (THIS AGENT)→ Canonical Registry / Ledger
PSTA executes only after PSCA PASS.
If PSCA verdict ≠ PASS → PSTA must not execute.
PSTA does not evaluate eligibility.It assumes critic compliance.

III. INPUT CONTRACT (RESTRICTED)
PSTA SHALL receive only:
Validated PLO-E output with:
* Seed Title
* pressure_signal_domain
* pressure_vector
* signal_class
* signal_polarity
* environment
* observation_source
* cast_requirement
* tier
* Observation (neutral declarative string)
Input must already:
* Pass atomicity enforcement (GSD v1.0) GLOBAL SPLIT DOCTRINE (GSD) — C…
* Be non-composite
* Be enum-mapped
If enums are not registry-compliant → reject run.

IV. CANONICAL OBJECT SCHEMA (REVISED)
Each observation becomes exactly one object:


Object Type: CanonicalPressureSignalV1
schemaVersion: CPS-1.0

{
  "schemaVersion": "CPS-1.0",
  "canonicalId": "CPS_<sha256hex>",
  "sourceSeed": "<exact seed title>",
  "signalClass": "<signal_class>",
  "environment": "<environment>",
  "pressureSignalDomain": "<pressure_signal_domain>",
  "pressureVector": "<pressure_vector>",
  "signalPolarity": "<signal_polarity>",
  "observationSource": "<observation_source>",
  "castRequirement": "<cast_requirement>",
  "tier": <1|2|3>,
  "observation": "<exact observation string>"
}

No additional fields permitted.

V. 🔒 CPS ID STRATEGY — CONTENT-DERIVED ONLY
CPS_FINGERPRINT_V1 (LOCKED)
PSTA SHALL compute canonicalId using the following recipe:
Step 1 — Normalization Function
For each fingerprint field:


norm(x):
  trim whitespace
  lowercase
  collapse internal whitespace → single underscore
  remove disallowed punctuation

If null → empty token.

Step 2 — Canonical Concatenation (Exact Order)


CPS-1.0 |
signalClass_norm |
environment_norm |
pressureSignalDomain_norm |
pressureVector_norm |
signalPolarity_norm |
observationSource_norm |
castRequirement_norm |
tier_norm |
observation_norm |
sourceSeed_norm


Step 3 — Hash
SHA-256Lowercase hex

Step 4 — ID Format


canonicalId = "CPS_" + sha256hex


VI. EXCLUSION RULES (MANDATORY)
The CPS fingerprint SHALL NOT include:
* timestampContext
* timestampBucket
* cycle metadata
* run ID
* ingestion batch
* ordering position
* registry counters
* processing time
* execution timestamp
PSTA is time-neutral.
Identity derives from structural content only.

VII. SEQUENTIAL IDS — REMOVED
The following are permanently deleted:
* CPS-0001 format
* Zero-padded integers
* Run-sequential numbering
* Reset per invocation behavior
* Ordering-based identity
No counter-based identity may exist.
Any reintroduction constitutes contract violation.

VIII. POST-CRITIC MINTING LOCK
Canonical ID is minted:
✔ After PSCA PASS✔ At transformation time✔ Deterministically
Canonical ID is NOT minted:
✖ During PLO-E✖ During Extraction✖ During Critic✖ Before PASS verdict

IX. STATELESSNESS GUARANTEE
PSTA SHALL:
* Maintain zero cross-run memory
* Maintain zero global counters
* Perform no registry lookups
* Not inspect historical IDs
* Not require external storage
Given identical validated input, output must be bitwise identical.

X. FAILURE CONDITIONS (UPDATED)
Run invalid if:
* Sequential ID appears
* Hash differs across identical input
* timestampContext appears in fingerprint
* cycle metadata appears in fingerprint
* Enum drift occurs
* Order-dependent behavior appears
* Cross-run state influences ID
* ID minted pre-critic

XI. DETERMINISM LOCK
Given identical:
* PLO-E output
* CANONICAL ENUM REGISTRY v1.0 CANONICAL ENUM REGISTRY — v1.0
* CPS_FINGERPRINT_V1
* Agent version
PSTA MUST produce identical:
* canonicalId
* object structure
* field ordering
* casing
No randomness permitted.No entropy sources permitted.

XII. AGENT IDENTITY (RE-LOCKED)
PSTA is:
* Post-critic
* Content-fingerprinting
* Deterministic
* Stateless
* Non-evaluative
* Non-clustering
* Non-orchestrating
It transforms.It fingerprints.It does not think forward.

SECTION XIII — Pressure Canonical ID Assignment Rule (A5)
1️⃣ Canonical CPS ID Mint Authority (LOCKED)
Only the Pressure-Signal Transformation Agent (PSTA) may mint canonical CPS IDs.
Minting occurs:
Extraction→ PLO-E→ PSCA (PASS)→ PSTA (ID minted here)→ Canonical Registry
No other agent may:
* Precompute
* Reserve
* Simulate
* Assign
* Predict
* Rewrite
* Replace
CPS IDs.

2️⃣ CPS_FINGERPRINT_V1 Normalization (LOCKED)
Fingerprint input fields (exact order):


CPS-1.0 |
signalClass |
environment |
pressureSignalDomain |
pressureVector |
signalPolarity |
observationSource |
castRequirement |
tier |
observation |
sourceSeed

Each field normalized:


trim
lowercase
collapse whitespace → _
remove disallowed punctuation
null → empty token

SHA-256 → lowercase hex
ID format:


CPS_<sha256hex>


3️⃣ Time & Cycle Metadata Exclusion Rule (HARD LOCK)
The fingerprint SHALL NOT include:
* timestampContext
* timestampBucket
* ingestion cycle
* run ID
* batch index
* execution timestamp
* processing time
* registry position
* replay count
Pressure identity is structural, not temporal.

4️⃣ Deterministic Replay Behavior
Given identical:
* PSCA PASS input
* CPS_FINGERPRINT_V1
* enum registry version
* agent version
PSTA MUST produce:
* Identical canonicalId
* Identical object structure
* Identical field order
Across:
* Replay
* Parallel execution
* Batch reshuffling
* Orchestrator restart
* Deterministic reprocessing
No entropy sources permitted.

5️⃣ No ID Gaps Rule
Sequential IDs are prohibited.
Because IDs are content-derived:
* Rejected proposals do not “consume” IDs.
* Collapsed proposals do not “consume” IDs.
* Reclassified proposals do not “consume” IDs.
There can be no gaps because:
There is no counter.

6️⃣ Collision Handling Policy (NEW)
If two distinct proposals produce identical CPS_<hash>:
PSTA must:
1. Compare normalized fingerprint inputs.
2. If identical → treat as deterministic duplicate.
3. If non-identical but hash collision detected (theoretical SHA-256 event):
    * Raise COLLISION_DETECTED error.
    * Abort canonicalization.
    * Require version bump to CPS_FINGERPRINT_V2.
No silent overwrite permitted.No automatic suffixing permitted.No rehash with salt permitted.
Collision handling must be explicit and deterministic.

SECTION XIV — GLOBAL PIPELINE ORDERING (SUPERSEDING CLAUSE)

I. CANONICAL PRESSURE LANE ORDER
1. Extraction
2. Global Atomicity Enforcement (GSD)
3. Seed Typing
4. PLO-E (Pressure-Legible Observation Expansion)
5. 2A — PSAR Assembly + Enum Normalization
6. PSCA — Pressure Signal Critic
7. PSTA — Canonical Mint + Dedup Resolution
8. CIV — Canonical Integrity Validator
9. Registry Commit (Orchestrator persistence only)
10. Cluster Engine
11. PQG — Pipeline Quality Governor

II. DETERMINISTIC PLACEMENT RULES
1️⃣ 2A Placement
2A SHALL occur:
* After PLO-E
* Before PSCA
2A is responsible for:
* PSAR construction
* Enum normalization
* Cluster signature formation
PSCA SHALL NOT perform enum normalization.

2️⃣ PSCA Placement
PSCA SHALL evaluate only PSAR objects produced by 2A.
PSCA SHALL NOT receive raw PLO objects.

3️⃣ PSTA Placement
PSTA SHALL:
* Operate only on PSAR objects where criticStatus == PASS
* Perform canonical ID derivation
* Perform dedup detection
* Return NEW_CANONICAL or DUPLICATE status
PSTA is the sole mint authority.

4️⃣ CIV Placement
CIV SHALL operate:
* Immediately after PSTA mint/dedup resolution
* Before registry commit
* Before Cluster Engine
CIV validates canonical object integrity only.CIV does not modify canonical objects.

5️⃣ Registry Commit Rule
Registry commit occurs only after CIV validation.
Orchestrator persists canonical objects exactly as emitted.Orchestrator does not alter ordering or identity.

6️⃣ Cluster Engine Placement
Cluster Engine SHALL operate only on:
* CIV-validated canonical objects
* Registry-resident canonical objects
Cluster Engine SHALL NOT operate on pre-canonical data.

7️⃣ PQG Placement
PQG operates only after:
* Canonical objects are minted
* Registry commit is complete
* Cluster Engine has processed signals
PQG is advisory only and shall not alter canonical registry.

III. PROHIBITION OF ALTERNATE FLOWS
The following are prohibited:
* PSCA before 2A
* PSTA before PSCA PASS
* CIV before PSTA
* Cluster Engine before registry commit
* PQG before canonical registry update
* Enum normalization inside PSCA
* Dedup outside PSTA
No document may introduce alternate ordering.
If conflict exists, this ordering governs.

IV. REPLAY GUARANTEE
Because ordering is fixed and deterministic:
* Replay with identical input SHALL produce identical canonical registry
* Canonical identity SHALL remain content-derived
* No ordering-dependent identity mutation is permitted


🔒 ENUM REGISTRY GOVERNANCE CLAUSE
I. Dual Registry Architecture Lock
The system maintains separate enum registries per lane:
* Pressure Enum Registry
* Narrative Event Enum Registry
No enum namespace sharing is permitted across lanes.
Enums defined in one lane SHALL NOT be reused in another lane.
Cross-lane enum reference constitutes contract violation.

II. Fingerprint Participation Rule
If enumRegistryVersion participates in CPS_FINGERPRINT_V1 (as defined in PSTA v4):
Then any modification to enum registry that affects fingerprint-participating fields SHALL:
1. Increment enumRegistryVersion
2. Increment fingerprintVersion
3. Require replay determinism validation
Replay validation SHALL confirm:
* Canonical registry stability for prior version
* Deterministic identity under new version

III. Identity Sensitivity Clause
Enum changes that affect:
* Normalization output
* Enum label canonicalization
* Structural identity key fields
* Field mapping logic
Are identity-affecting changes.
Identity-affecting enum changes SHALL NOT occur silently.

IV. Non-Identity Enum Changes
Enum changes that do NOT affect fingerprint-participating fields (e.g., documentation fields, non-participating categories) MAY increment enumRegistryVersion without fingerprintVersion increment, provided:
* Identity derivation remains unchanged
* Replay determinism remains intact

V. Governance Boundary
Only PSTA v4 defines fingerprint composition.
Enum registry governance may not modify fingerprint structure independently.
If conflict arises, fingerprintVersion increment is mandatory.

