CANONICAL INTEGRITY VALIDATOR (CIV)
Inline Structural Integrity Enforcement — v1.0

I. ONTOLOGICAL ROLE
CIV is:
* Deterministic
* Stateless
* Non-mutating
* Post-canonicalization
* Pre-orchestrator commit
It verifies canonical objects before they are written to the canonical store.
It is not PQG.It is not a governance auditor.It is not a cluster engine.
It is a structural firewall.

II. PIPELINE POSITION
For Pressure:
Extraction→ IAV (identity abstraction)→ PLO-E→ 2A→ PSCA→ PSTA (mint canonicalCPSID)→ CIV→ Orchestrator commit
For Narrative:
Extraction→ IAV→ EMI→ NCA / META / SANTA→ Canonicalization→ CIV→ Orchestrator commit
CIV must see fully formed canonical objects.

III. WHAT CIV VALIDATES
CIV verifies structural invariants only.
It does NOT:
* Reclassify
* Re-score
* Re-evaluate eligibility
* Re-run clustering
* Re-evaluate thresholds
It verifies:

1️⃣ Schema Completeness
All required fields present.
No unknown fields.
No missing enum fields.

2️⃣ Enum Registry Compliance
All enum fields must:
* Exist in Canonical Enum Registry
* Match enumVersion snapshot
No dynamic enum insertion allowed.

3️⃣ Identity Abstraction Integrity
Verify:
* No proper nouns
* No unabstracted named entities
* No literal names in structural fields
If violation:
→ Reject canonical object→ REJECT_IDENTITY_CONTAMINATION

4️⃣ Time Binding Compliance
Verify:
* timestampContext exists
* Structured object shape
* season present
* phase valid enum
* week nullable
* No illegal fields
Verify:
* timestampContext not included in ID derivation (structural identity key excludes time ordering effects)

5️⃣ ID Integrity Check
Verify:
* canonicalID matches deterministic hash recipe
* Structural Identity Key correctly derived
* No mismatch between ID and structural payload
If mismatch:
→ REJECT_ID_HASH_MISMATCH
This protects determinism.

6️⃣ Version Snapshot Integrity
Verify object includes:
* schemaVersion
* enumVersion
* contractVersion
Matches orchestrator cycle snapshot.

7️⃣ Cross-Family Field Contamination
Pressure object must not contain:
* narrative subclass
* lifecycle metadata
* recurrence metadata
Narrative object must not contain:
* pressure clusterSignature
* structuralSourceIDs
Lane purity must be enforced.

IV. FAILURE POLICY
If CIV fails:
* Canonical object is rejected
* It is not written to canonical store
* Rejection logged with deterministic reason code
* Run continues
No mutation permitted.No silent correction permitted.

V. REASON CODE ENUM (CIV)
Examples:
* REJECT_SCHEMA_INCOMPLETE
* REJECT_ENUM_INVALID
* REJECT_IDENTITY_CONTAMINATION
* REJECT_TIME_SHAPE_INVALID
* REJECT_ID_HASH_MISMATCH
* REJECT_VERSION_MISMATCH
* REJECT_LANE_FIELD_CONTAMINATION
These feed PQG metrics later.

VI. DETERMINISM GUARANTEE
Given identical canonical object input:
CIV must produce identical verdict.
No scoring.No thresholds.No heuristics.
Pure structural verification.

VII. ORCHESTRATOR COMMIT POLICY
Only CIV-PASS objects may be committed.
Commit step is atomic per object.
Rejections do not halt run.

VIII. WHY THIS MATTERS
Without CIV:
* One agent bug corrupts canonical store
* Silent enum drift can spread
* ID recipe bug invalidates replay
* Identity abstraction leak goes unnoticed
* Version mismatch propagates
With CIV:
You have a canonical firewall.

IX. GLOBAL PIPELINE ORDERING (SUPERSEDING CLAUSE)

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

🔒 CANONICAL FINGERPRINT AUTHORITY LOCK
I. Sole Definition Authority
CPS_FINGERPRINT_V1 is defined exclusively within the PSTA v4 Contract.
PSTA v4 is the sole authoritative source for:
* Fingerprint field composition
* Field ordering
* Normalization rules
* Hashing algorithm specification
* Canonical ID construction format
* schemaVersion participation
* enumRegistryVersion participation
No other document defines or enumerates fingerprint fields.

II. Prohibition of Parallel Definitions
No contract, doctrine, stabilization plan, or agent specification may:
* Restate fingerprint field lists
* Embed structural identity keys
* Define hashing logic
* Specify field concatenation order
* Define canonical ID formatting rules
* Reproduce CPS_FINGERPRINT_V1 schema
* Introduce alternate fingerprint versions
All canonical ID references must defer to:
“CPS_FINGERPRINT_V1 as defined in PSTA v4.”
Any duplicate fingerprint specification constitutes a contract violation.

III. Version Governance Rule
If fingerprint composition changes:
* fingerprintVersion SHALL increment within PSTA v4.
* No other contract may independently revise fingerprint logic.
* All downstream contracts inherit fingerprint changes implicitly via PSTA authority.
Canonical identity must remain single-source governed.

IV. Identity Non-Participation Rule
Documents other than PSTA v4 SHALL NOT:
* Modify canonical identity logic
* Influence fingerprint derivation
* Inject lifecycle or time fields into identity
* Introduce run-order dependence
* Construct canonical IDs
Canonical ID mint authority remains exclusively within PSTA.

V. Supremacy Clause
If any document contains language inconsistent with PSTA v4 fingerprint definition, PSTA v4 SHALL govern.
This clause eliminates parallel identity specifications across the system.


🔒 GLOBAL CANONICAL IMMUTABILITY LOCK
I. Post-Canonicalization Freeze Rule
After canonicalization (mint event):
Canonical objects SHALL be immutable.
No downstream agent may:
* Modify fingerprint fields
* Modify structural identity key fields
* Modify enum-participating fields
* Modify schemaVersion
* Modify enumRegistryVersion
* Modify canonical ID
* Replace canonical object record
* Merge canonical objects
* Retroactively alter canonical registry
Canonical identity is permanently frozen at mint time.

II. Permitted Post-Canonical Updates
Only the following may change post-canonicalization:
* Cycle Association Logs
* Audit metadata records
* External analytic registries (e.g., cluster membership indexes)
* Decay modeling (if external)
* PQG advisory outputs
These must be stored outside the canonical object.

III. Downstream Agent Restriction
The following agents are explicitly prohibited from mutating canonical objects:
* CIV
* Cluster Engine
* PQG
* Orchestrator
* Any post-processing agent
They may read canonical objects but shall not modify them.

IV. Replay Determinism Guarantee
Because canonical objects are immutable:
* Replay with identical input SHALL produce identical canonical registry.
* No downstream analytic pass may alter canonical identity.
* System state drift is prohibited at canonical layer.


