PRESSURE SIGNAL AUDIT RECORD (PSAR)
Schema + Contract v1.0
Critic Input Model (2A → PSCA) + Verdict Append (PSCA → PSTA/PQG)

I. PURPOSE
The PressureSignalAudit Record (PSAR) is the single, stable object shape used to:
1. carry candidate pressure signal proposals from 2A to PSCA, and
2. carry PSCA verdict metadata forward to PSTA and PQG.
PSAR is the exclusive input type evaluated by PSCA.
PSAR is not a canonical object.PSAR does not contain canonical CPS IDs pre-critic.PSAR is time-neutral (cycle metadata is handled outside PSAR).

II. PIPELINE POSITION
PLO-E → 2A constructs PSAR (pre-critic) → PSCA appends verdict fields →
* If PASS → PSTA mints canonical CPS object (with canonicalCpsID)
* If not PASS → PSAR persists to PQG audit storage only
PSCA never mutates structural core fields.

III. ENUM COMPLIANCE ENFORCEMENT (LOCK)
Enum normalization is performed before PSCA, in 2A.
PSCA receives enum-clean PSAR objects only.
PSCA may validate enumComplianceFlags, but may not normalize enums.

IV. SHAPE STABILITY (LOCK)
PSAR uses one unified schema.
Pre-critic vs post-critic is represented by field population only:
* 2A populates structural + diagnostic fields
* PSCA populates verdict fields
No fields are removed. No structural fields are rewritten.

V. ID ASSIGNMENT TIMING (LOCK)
* proposalID exists in PSAR and is assigned by 2A (cycle-scoped, deterministic).
* No canonical CPS ID exists inside PSAR prior to PSCA PASS.
* Canonical CPS IDs are minted by PSTA after PASS.
PSAR may optionally include canonicalCpsID only after PASS as a convenience for linkage, but it must be null/absent pre-critic.

VI. VERSIONING STRATEGY (LOCK)
Each PSAR must include both:
* auditSchemaVersion
* enumRegistryVersion
And an agent snapshot:
* agentVersionSnapshot (minimum: PLOE, 2A, PSCA)

VII. PSAR v1.0 — REQUIRED FIELDS (STRUCTURAL CORE)
All required unless explicitly marked optional.
A) Identity & Version
* proposalID (string) REQUIRED
    * deterministic, cycle-scoped identifier created by 2A
    * stable under replay given identical inputs and clustering outcome
* auditSchemaVersion (string) REQUIRED
    * fixed value: "PSAR_v1.0"
* enumRegistryVersion (string) REQUIRED
    * e.g., "ENUM_v1.0" (must match Canonical Enum Registry)
* agentVersionSnapshot (object) REQUIRED
    * ploEVersion (string)
    * assembler2AVersion (string)
    * pscaVersion (string) (may be "unknown" pre-critic; must be set post-critic)

B) Enum-Normalized Structural Signature
All fields below must already be normalized to allowed enums/taxonomies.
* actorGroup (string) REQUIRED
    * enum-bound (or restricted vocabulary per pressure lane)
* actionType (string) REQUIRED
    * enum-bound verb class for pressure signals (not raw verb)
* objectRole (string) REQUIRED
* domainSet (array) REQUIRED
    * must contain unique values
    * must be deterministically ordered (lexicographic)
    * must be non-empty
* clusterSignature (string) REQUIRED
    * deterministic hash derived from:
        * actorGroup + actionType + objectRole + sorted(domainSet)
    * excludes time / cycle metadata

VIII. PSAR v1.0 — REQUIRED DIAGNOSTIC METADATA
* structuralSourceIDs (array) REQUIRED
    * list of PLO IDs that form the proposal
    * deterministically ordered (lexicographic)
* clusterSize (integer) REQUIRED
    * equals length(structuralSourceIDs)
* domainDiversityCount (integer) REQUIRED
    * equals length(domainSet)
* enumComplianceFlags (object) REQUIRED
    * actorGroupResolved (boolean)
    * actionTypeResolved (boolean)
    * objectRoleResolved (boolean)
    * domainSetResolved (boolean)
    * registryVersionMatched (boolean)
If any enumComplianceFlags are false, 2A must not emit PSAR (preferred), or must emit PSAR with an internal assembler-level failure record (if you want PQG to see failures). PSCA must treat such PSAR as malformed input and produce no output (per its input-boundary rule).

IX. PSCA VERDICT FIELDS (APPENDED, POST-CRITIC)
All verdict fields are optional pre-critic and must be populated post-critic.
* criticStatus (string) OPTIONAL pre-critic / REQUIRED post-criticAllowed values: PASS | REJECT | COLLAPSE | RECLASSIFY
* failureStage (string) OPTIONAL
    * which PSCA check triggered verdict
    * required for REJECT/COLLAPSE/RECLASSIFY
* reasonCode (string) OPTIONAL
    * required for REJECT/COLLAPSE/RECLASSIFY
    * deterministic code from locked list (see section X)
* reclassificationTarget (string) OPTIONALAllowed values: MEDIA_EVENT | NARRATIVE_ENVIRONMENT | STANDALONE_NARRATIVE
    * required if criticStatus = RECLASSIFY
* collapseDirective (object) OPTIONAL
    * required if criticStatus = COLLAPSE
    * minimal structure:
        * targetType: "STANDALONE_NARRATIVE"
* canonicalCpsID (string) OPTIONAL
    * must be absent/null pre-critic
    * may be populated only after PASS and canonicalization (if you want to attach it later for linkage)
    * minted exclusively by PSTA

X. REASON CODE REGISTRY (PSCA)
PSCA must output a deterministic reasonCode when criticStatus ≠ PASS.
Minimum required codes (v1.0):
Structural Purity Codes (from PSCA contract)
* REJECT_INTENTIONALITY
* REJECT_NARRATIVE_SATURATION
* COLLAPSE_FRAGMENTATION
* REJECT_EXPLICIT_MEANING
* REJECT_NON_ACCIDENTAL_EMERGENCE
* RECLASSIFY_OVERWEIGHT_SIGNAL_MEDIA_EVENT
* REJECT_MISCLASSIFIED_OVERWEIGHT
Structural Sanity Gate Codes (Q10 lock)
* REJECT_INSUFFICIENT_CLUSTER_SIZE
* REJECT_INSUFFICIENT_DOMAIN_DIVERSITY
(If you later add more PSCA checks, they must introduce reason codes via version bump.)

XI. SANITY GATE THRESHOLDS (DETERMINISTIC)
PSCA may apply only minimal sanity thresholds:
* MIN_CLUSTER_SIZE (integer constant, version-bound)
* MIN_DOMAIN_DIVERSITY (integer constant, version-bound)
These constants must be defined in the PSCA contract or a shared constants registry and referenced by version.
PSAR does not contain these thresholds.PSAR contains the measured values only (clusterSize, domainDiversityCount).

XII. VALIDATION RULES (MUST)
Field Ordering
PSAR must be deterministically ordered when serialized.
No Time Fields
PSAR must not contain:
* timestampContext
* run timestamps
* cycle window
* “observed week”
Cycle metadata is attached at the run log level and linked by proposalID, not embedded.
No Canonical Fields Pre-Critic
PSAR must not contain:
* canonical IDs
* canonical write flags
* lifecycle fields (LastConfirmed, etc.)
* recurrence counters

XIII. EXAMPLE OBJECTS
A) Pre-Critic PSAR (2A Output)
{
  "proposalID": "PROP_2000_REG_003_0012",
  "auditSchemaVersion": "PSAR_v1.0",
  "enumRegistryVersion": "ENUM_v1.0",
  "agentVersionSnapshot": {
    "ploEVersion": "PLOE_v2.0",
    "assembler2AVersion": "2A_v1.1",
    "pscaVersion": "unknown"
  },
  "actorGroup": "coach",
  "actionType": "retained_control",
  "objectRole": "play_calling",
  "domainSet": ["authority_distribution","control_autonomy"],
  "clusterSignature": "SIG_8f31a0d2",
  "structuralSourceIDs": ["PLO_00017","PLO_00029"],
  "clusterSize": 2,
  "domainDiversityCount": 2,
  "enumComplianceFlags": {
    "actorGroupResolved": true,
    "actionTypeResolved": true,
    "objectRoleResolved": true,
    "domainSetResolved": true,
    "registryVersionMatched": true
  }
}
B) Post-Critic PSAR (PSCA Appended)
{
  "...same fields as above...": "...",
  "agentVersionSnapshot": {
    "ploEVersion": "PLOE_v2.0",
    "assembler2AVersion": "2A_v1.1",
    "pscaVersion": "PSCA_v1.0"
  },
  "criticStatus": "REJECT",
  "failureStage": "2_NARRATIVE_SATURATION_TEST",
  "reasonCode": "REJECT_NARRATIVE_SATURATION"
}

XIV. IMPLEMENTATION NOTES (NON-NORMATIVE)
* proposalID should be deterministic and cycle-scoped (e.g., derived from clusterSignature + stable ordinal).
* PSCA must treat malformed PSAR as “produce no output” per its input boundary.
* PSTA consumes only PSAR where criticStatus = PASS.

XV. LOCKED SUMMARY
This schema satisfies all locks:
* Candidate object audited (not PLOs, not seeds)
* Critic non-mutating
* Hybrid structural+diagnostic fields
* Enum compliance before critic
* Schema + enum version tagging
* Unified shape with appended verdict fields
* Canonical ID minted post-pass only
* Structural+diagnostic logging
* Deterministic critic
* Minimal sanity gate supported by clusterSize + domainDiversityCount


