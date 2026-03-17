PRESSURE LIFECYCLE CONTRACT
Canonical Pressure Signal (CPS) Governance — v2.0System-Level Enforcement Document

I. PURPOSE
This contract defines the lifecycle rules governing Canonical Pressure Signal (CPS) objects.
Its purpose is to:
* Preserve canonical layer immutability
* Enforce time-neutral structural identity
* Prevent recurrence modeling inside canonical layer
* Protect replay determinism
* Maintain strict separation between extraction system and narrative engine
This contract applies exclusively to Canonical Pressure Signal (CPS) objects minted by PSTA.

II. DEFINITIONS
CPS (Canonical Pressure Signal):An immutable, time-neutral structural pressure type minted by PSTA after PSCA PASS validation.
Canonical CPS ID:A deterministic identifier derived exclusively from CPS_FINGERPRINT_V1.
Cycle Association Log:A downstream ledger linking Canonical CPS ID to observed cycle metadata (season, phase, week, cycleID).
Narrative Engine:A downstream system responsible for recurrence modeling, decay modeling, arc formation, and temporal state simulation.

III. CANONICAL IDENTITY POLICY
1️⃣ Time-Neutral Structural Identity
Canonical CPS objects represent timeless structural pressure types.
Canonical CPS ID is derived exclusively from:
* CPS_FINGERPRINT_V1
* schemaVersion
* enumRegistryVersion
Canonical CPS ID SHALL NOT include:
* timestampContext
* timestampBucket
* season
* phase
* week
* cycleID
* runIndex
* execution timestamp
* proposalID
2️⃣ Cross-Window Identity Continuity
If identical structural pressure conditions appear in multiple distinct temporal windows:
They SHALL resolve to the same Canonical CPS ID.
Temporal distinction does not imply canonical distinction.
3️⃣ Temporal Modeling Boundary
Time participates in:
* Recurrence tracking
* Analytics
* Escalation modeling
* Narrative arc formation
Time does NOT participate in:
* Canonical identity
* Fingerprint derivation
* Deduplication key generation
* Canonical object minting

IV. IMMUTABILITY RULE
1️⃣ Write-Once Canonical Objects
Once a CPS object is minted:
* No structural fields may be edited.
* No enum fields may be modified.
* No fingerprint fields may be altered.
* No canonical metadata may be updated.
* No lifecycle fields may be introduced.
CPS objects are write-once, read-only.
2️⃣ Immutable Field Scope
The following fields are immutable:
* signal_class
* environment
* pressure_signal_domain
* pressure_vector
* signal_polarity
* cast_requirement
* tier
* fingerprintVersion
* schemaVersion
* enumRegistryVersion
Any structural correction requires:
* Contract revision
* Fingerprint version increment (if applicable)
* Future-run correction
* PQG governance record
No retroactive mutation is permitted.

V. DEDUPLICATION POLICY
1️⃣ Canonical Dedup Key
Deduplication key = Canonical CPS ID.
2️⃣ Duplicate Structural Occurrence
If a proposal resolves to an existing Canonical CPS ID:
* No new CPS object is minted.
* Proposal is collapsed into existing canonical object.
* Cycle Association Log is updated.
* Audit trail is preserved.
3️⃣ Hash Collision Event
If a true SHA-256 fingerprint collision occurs:
* Canonicalization SHALL abort.
* Critical collision SHALL be logged.
* fingerprintVersion increment SHALL be required.
* Manual review SHALL occur.
Structural duplication and hash collision are distinct cases.

V-A. PRESSURE LANE DEDUP DOCTRINE (FORMAL CONSOLIDATION)
1️⃣ Authority Boundary (LOCK)
Dedup detection occurs exclusively inside PSTA at canonicalization boundary.
PSTA is the sole authority permitted to:
* Compute CPS_FINGERPRINT_V1
* Derive Canonical CPS ID
* Check registry for existing ID
* Determine NEW_CANONICAL vs DUPLICATE
* Detect cryptographic hash collision
The Orchestrator:
* Does not compute fingerprints
* Does not derive canonical IDs
* Does not perform dedup checks
* Does not re-verify registry state
Registry layer is passive storage only.
No distributed identity authority is permitted.

2️⃣ Duplicate Structural Occurrence (Expected Case)
If a proposal resolves to an existing Canonical CPS ID:
* No new CPS object SHALL be minted.
* Canonical registry SHALL remain unchanged.
* Canonical object SHALL NOT be mutated.
* Merge operations are prohibited.
* Retroactive edits are prohibited.
PSTA SHALL return status: DUPLICATE.
Orchestrator SHALL:
* Append Cycle Association Log entry
* Persist audit trail entry
* Not increment globalCanonicalCounter
Dedup collapse is treated as structural repetition, not anomaly.

3️⃣ Cryptographic Hash Collision (Critical Anomaly)
If two structurally distinct proposals produce identical SHA-256 fingerprint:
Canonicalization SHALL abort immediately.
Required actions:
* Log critical collision event
* Prevent registry insertion
* Require fingerprintVersion increment
* Require manual governance review
Structural duplicate and cryptographic collision are distinct conditions and SHALL NOT be conflated.

4️⃣ Counter Integrity Rule
globalCanonicalCounter SHALL increment only when:
PSTA.status == NEW_CANONICAL
If:
PSTA.status == DUPLICATE→ Counter SHALL NOT increment.
If:
PSTA.status == COLLISION_ABORT→ Counter SHALL NOT increment.
Registry cardinality MUST equal globalCanonicalCounter at all times.
Any drift constitutes contract violation.

5️⃣ Determinism Guarantee
Because dedup detection occurs at canonicalization boundary and no post-run merging is permitted:
* Replay with identical input SHALL produce identical canonical registry.
* Duplicate structural events SHALL collapse deterministically.
* Canonical layer SHALL remain immutable and stable.
No post-run dedup or merge logic is permitted.


VI. RECURRENCE POLICY
Canonical layer models:
* Structural pressure type existence
Canonical layer does NOT model:
* Recurrence frequency
* Persistence
* Cooling
* Escalation
* Duration
* Lifecycle state
Recurrence is modeled via:
CanonicalCPSID + CycleAssociationLog

VII. EXPIRATION POLICY
CPS objects:
* Do not expire
* Are not archived
* Are not marked inactive
* Are not removed due to inactivity
* Are not subject to decay thresholds
Canonical layer is a permanent structural ledger.

VIII. DECAY OWNERSHIP BOUNDARY
Decay, cooling, persistence, recurrence modeling, and arc formation are the exclusive responsibility of:
The downstream Narrative Engine.
Canonical layer:
* Does not track duration
* Does not track lastSeen
* Does not track recurrenceCount
* Does not simulate cooling
* Does not simulate state evolution

IX. MERGE POLICY
Once minted, CPS objects:
* SHALL NOT be merged.
* SHALL NOT be consolidated.
* SHALL NOT be replaced by corrected versions.
* SHALL NOT be retroactively collapsed.
If structural over-fragmentation occurs:
* PQG flags the issue.
* System logic is corrected for future runs.
* Historical canonical objects remain untouched.

X. LIFECYCLE METADATA PROHIBITION
CPS objects SHALL NOT contain:
* firstSeen
* lastSeen
* observedCycles
* recurrenceCount
* decayScore
* lifecycleStatus
* activity flags
* continuation indicators
Any recurrence modeling fields are prohibited at canonical level.

XI. DETERMINISM GUARANTEE
Because CPS objects are:
* Immutable
* Time-neutral
* Non-merging
* Non-expiring
* Non-recursive
Replay determinism is preserved under:
* Identical input
* Identical clustering
* Identical fingerprint recipe
* Identical enum registry
* Identical schema version
* Identical ID namespace policy
Temporal distribution does not affect canonical identity.

XII. ARCHITECTURAL SUMMARY
Under this contract:
Canonical CPS layer is:
* A static ledger of structural pressure types
* Immutable
* Time-neutral
* Non-stateful
* Non-decaying
* Non-aggregating
Narrative Engine layer is:
* Stateful
* Recurrence-aware
* Decay-aware
* Arc-forming
Extraction system and narrative engine remain formally separated.

XIII. LOCK STATEMENT
Pressure Lifecycle Contract v2.0 is:
* Deterministic
* Immutable
* Time-neutral
* Non-recursive
* Non-decaying
* Non-merging
* Replay-safe
* Governance-isolated
No CPS lifecycle behavior may deviate from this contract without formal version increment.


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

