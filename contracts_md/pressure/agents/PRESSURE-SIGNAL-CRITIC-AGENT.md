PRESSURE SIGNAL CRITIC AGENT
Contract v2.0 — Structural Convergence & Sanity Gate Enforcement

I. ROLE (REAFFIRMED)
PSCA evaluates PressureSignalAuditRecord proposals emitted by Agent 2A.
Authority:
* PASS
* REJECT
* COLLAPSE
* RECLASSIFY
PSCA does not:
* Transform
* Fingerprint
* Mint canonical IDs
* Modify content
* Interpret narrative meaning
PSCA is structural disqualification + convergence enforcement only.

II. FORMAL INPUT SCHEMA (NEW)
PSCA SHALL receive only:
PressureSignalAuditRecordV1 (PSAR_v1.0)


{
  "auditSchemaVersion": "PSAR_v1.0",
  "proposalId": "PSPROPOSAL_<sha256hex>",
  "clusterSize": <integer>,
  "domainDiversityCount": <integer>,
  "domains": ["<pressure_signal_domain>", "..."],
  "signalIds": ["<internal temporary id>", "..."],
  "environmentSet": ["<environment>", "..."],
  "vectorSet": ["<pressure_vector>", "..."],
  "tierSet": [1,2,3],
  "containsInterpretiveLanguage": <boolean>,
  "containsSymbolicStaging": <boolean>,
  "containsOutcomeEncoding": <boolean>
}

If malformed → produce no output.

III. proposalId GENERATION RULE (NEW)
proposalId SHALL be content-derived and deterministic.
PSPROPOSAL_FINGERPRINT_V1
Fingerprint fields (exact order):


PSAR_v1.0 |
sorted(signalIds) |
sorted(domains) |
clusterSize |
domainDiversityCount

SHA-256 → lowercase hex
Format:


PSPROPOSAL_<sha256hex>

proposalId:
* Does NOT use run counters
* Does NOT use timestamps
* Does NOT use cycle metadata
* Must be stable across replay

IV. STRUCTURAL SANITY GATE (EXPANDED)
Threshold Parameters (Versioned Constants)


MIN_CLUSTER_SIZE = 2
MIN_DOMAIN_DIVERSITY = 2

These are explicit convergence thresholds.

A. Single-Domain Rejection Rule (NEW)
If:


domainDiversityCount < MIN_DOMAIN_DIVERSITY

→ REJECT→ reasonCode = REJECT_INSUFFICIENT_DOMAIN_DIVERSITY→ stop evaluation
Single-domain clusters are structurally insufficient.

B. Multi-Domain Convergence Enforcement Rule (NEW)
A cluster must demonstrate:
* ≥ MIN_CLUSTER_SIZE
* ≥ MIN_DOMAIN_DIVERSITY
* No overweight encoding
* No narrative completeness
Convergence means:Pressure exists only when at least two distinct domains intersect.
If convergence absent → REJECT.

V. FULL STRUCTURAL VALIDITY CHECKLIST (REORDERED & LOCKED)
Evaluation order is mandatory.

1️⃣ Cluster Size Gate
If:


clusterSize < MIN_CLUSTER_SIZE

→ REJECT→ reasonCode = REJECT_INSUFFICIENT_CLUSTER_SIZE

2️⃣ Domain Diversity Gate
If:


domainDiversityCount < MIN_DOMAIN_DIVERSITY

→ REJECT→ reasonCode = REJECT_INSUFFICIENT_DOMAIN_DIVERSITY

3️⃣ Intentionality Check
If containsSymbolicStaging = true→ REJECT→ reasonCode = REJECT_INTENTIONAL_THEATER

4️⃣ Narrative Saturation Test
If cluster independently forms a complete story→ REJECT→ reasonCode = REJECT_NARRATIVE_COMPLETE

5️⃣ Fragmentation Check
If signals are fragments of a unified staged act→ COLLAPSE→ reasonCode = COLLAPSE_FRAGMENTED_STAGED_UNIT

6️⃣ Explicit Meaning Check
If containsInterpretiveLanguage = true→ REJECT→ reasonCode = REJECT_MEANING_LEAKAGE

7️⃣ Overweight Signal Check
If containsOutcomeEncoding = true→ RECLASSIFY→ reasonCode = RECLASSIFY_OVERWEIGHT_SIGNAL

If all checks pass → PASS.

VI. VERDICT PERSISTENCE POLICY (NEW)
All verdicts SHALL persist to ledger.
Verdict	Persist?	Canonical ID?
PASS	Yes	YES (downstream only)
REJECT	Yes	NO
COLLAPSE	Yes	NO
RECLASSIFY	Yes	NO
PSCA does not mint canonical IDs.
Canonical CPS IDs are minted only:
✔ After criticStatus = PASS✔ By PSTA✔ Post-critic
(Reaffirming Addendum A4)

VII. PRESSURE SIGNAL AUDIT RECORD OUTPUT FORMAT (REVISED)
For each proposal:
PASS


proposalId: PSPROPOSAL_<hash>
Verdict: PASS
reasonCode: PASS_ALL_CHECKS
canonicalEligible: true


REJECT


proposalId: PSPROPOSAL_<hash>
Verdict: REJECT
reasonCode: <specific_reason>
canonicalEligible: false


COLLAPSE


proposalId: PSPROPOSAL_<hash>
Verdict: COLLAPSE
reasonCode: COLLAPSE_FRAGMENTED_STAGED_UNIT
canonicalEligible: false


RECLASSIFY


proposalId: PSPROPOSAL_<hash>
Verdict: RECLASSIFY
reasonCode: RECLASSIFY_OVERWEIGHT_SIGNAL
suggestedType: MediaEvent | NarrativeEnvironment
canonicalEligible: false

No narrative commentary permitted.

VIII. CANONICAL ID MINTING CONSTRAINT (EXPLICIT LOCK)
PSCA SHALL NEVER:
* Mint CPS IDs
* Assign CPS IDs
* Precompute CPS IDs
* Reference fingerprinting logic
Canonical ID minting occurs:
Extraction→ PLO-E→ PSCA (PASS)→ PSTA (ID minting)
Never earlier.

IX. DETERMINISM LOCK
Given identical:
* PSAR_v1.0 input
* Threshold constants
* PSCA version
PSCA MUST produce identical:
* proposalId
* verdict
* reasonCode
No scoring.No weighting.No probabilistic logic.
Binary structural gates only.

SECTION X — GLOBAL PIPELINE ORDERING (SUPERSEDING CLAUSE)

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


