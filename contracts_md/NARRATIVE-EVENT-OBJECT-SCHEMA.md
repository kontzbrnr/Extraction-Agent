Narrative Event Object Schema (Pre-NCA)
Name: ATOMIC NARRATIVE EVENT OBJECT (ANE) + 2B EMISSION ENVELOPEVersion: v1.0Status: LOCKED (incorporates KP1/KP2/KP3 rulings)Applies To: Research Extraction Layer → Narrative Lane (Pre-NCA)

I. PURPOSE
I.1 Why this contract exists
NCA is a pure classifier: it accepts only atomic narrative event seeds, rejects composites, and outputs classification only with no enrichment.META and SANTA, however, require fully canonicalizable event content to transform into their canonical schemas.
This contract defines the missing formal object:AtomicNarrativeEventObjectV1 (ANE-1.0) and its deterministic 2B envelope so the pipeline has a stable object to carry through NCA into canonical transformers.

II. ARCHITECTURAL POSITION
II.1 Pipeline placement
Extraction / EMI boundary (event detection + splitting upstream) → 2B (Narrative Structural Assembler) → NCA → (CME → META) / (CSN → SANTA)
NCA assumes atomicity and rejects composites. Therefore, 2B is the first guaranteed schema formation layer analogous to 2A’s role in the pressure lane.

III. OBJECTS DEFINED
III.1 ANE Core Object (canonicalizable pre-NCA event)
Object: AtomicNarrativeEventObjectV1schemaVersion: "ANE-1.0"
This object is:
* identity-abstracted
* atomic (single discrete occurrence)
* non-framing / non-discourse
* non-pressure (event material only)
III.2 2B Emission Envelope (LOCKED Option B)
Object: NarrativeEventAssemblyEnvelopeV1schemaVersion: "2B-EMIT-1.0"
This envelope contains:
* ANE object (immutable, passed to NCA)
* Diagnostics (for auditability, dedup support, registry growth telemetry)
This mirrors the assembler doctrine: construct deterministic objects + diagnostic metadata; do not judge.

IV. ATOMIC NARRATIVE EVENT OBJECT v1.0 (ANE-1.0)
IV.1 Required fields
ANE-1.0 SHALL contain exactly these fields, in this deterministic order:
{
  "schemaVersion": "ANE-1.0",
  "eventSeedId": "ANESEED_<sha256hex>",
  "actorRole": "<EVENT_ENUM_REGISTRY_V1 token | OTHER>",
  "action": "<EVENT_ENUM_REGISTRY_V1 token | OTHER>",
  "objectRole": "<EVENT_ENUM_REGISTRY_V1 token | OTHER | null>",
  "contextRole": "<EVENT_ENUM_REGISTRY_V1 token | OTHER | null>",
  "eventDescription": "<neutral declarative string>",
  "timestampContext": "<normalized precise token>",
  "timestampBucket": "<TIME_BUCKET_REGISTRY_V1 token | OTHER_TIME_BUCKET>",
  "sourceReference": "<archival pointer string>"
}
IV.2 Field semantics (non-negotiable)
* eventSeedId is the pre-classification identity (NOT a canonical CME/CSN ID).
* actorRole/action/objectRole/contextRole are registry governed tokens (KP2).
* timestampContext is the authoritative precise timeline marker; timestampBucket is grouping only (KP3).
* eventDescription is neutral and non-causal (NCA rejects discourse/framing; narrative event must be discrete occurrence).
IV.3 Nullability rules
* objectRole MAY be null
* contextRole MAY be nullAll other fields are required and non-empty.
IV.4 Prohibited content rules (ANE-1.0)
ANE MUST be rejected by 2B if:
* composite / multi-event structure detected (NCA would reject; upstream split failure)
* Media Context / discourse content detected (framing, commentary, rhetorical labeling)
* identity abstraction violated (proper nouns in roles/description that should be abstracted)
* causal inference language appears in eventDescription (“because”, “therefore”, “in order to”, motive claims)

V. 2B EMISSION ENVELOPE v1.0 (2B-EMIT-1.0) — LOCKED
V.1 Envelope structure
2B SHALL emit:
{
  "schemaVersion": "2B-EMIT-1.0",
  "event": { /* ANE-1.0 object */ },
  "diagnostics": { /* EventAssemblyDiagnosticsV1 */ }
}
V.2 Immutability rule (critical)
* After 2B emission, no downstream agent may mutate event fields.
* NCA performs classification only, no enrichment.
* Transformers canonicalize; they do not revise pre-NCA identity or re-map pre-NCA enums as a substitute for missing structure (2B owns the enforcement point).

VI. EVENTASSEMBLYDIAGNOSTICS v1.0
VI.1 Required diagnostic fields
Diagnostics SHALL include:
{
  "schemaVersion": "EAD-1.0",
  "agentVersionSnapshot": "<2B version>",
  "registryVersion": "EVENT_ENUM_REGISTRY_V1",
  "timeRegistryVersion": "TIME_BUCKET_REGISTRY_V1",
  "fingerprintVersion": "ANE_FINGERPRINT_V1",

  "rawActorRole": "<string|null>",
  "rawAction": "<string|null>",
  "rawObjectRole": "<string|null>",
  "rawContextRole": "<string|null>",

  "roleMappingFlags": {
    "actorRole": "mapped|fallback_other",
    "action": "mapped|fallback_other",
    "objectRole": "mapped|fallback_other|null",
    "contextRole": "mapped|fallback_other|null"
  },

  "rawTimestampContext": "<string>",
  "timeMappingFlag": "mapped|fallback_other_time_bucket",

  "splitProvenance": {
    "wasSplit": true,
    "sourceUnitId": "<upstream unit id>",
    "splitIndex": 1,
    "splitCount": 3
  },

  "dedup": {
    "dedupKey": "<string>",
    "collisionCheck": "none|collision_detected",
    "collisionNotes": "<string|null>"
  }
}
VI.2 Diagnostic purpose lock
Diagnostics exist to prevent:
* critic ambiguity (analogous principle in 2A)
* logging inconsistency
* PQG blind spots
* version drift risk
Diagnostics SHALL NOT be used for:
* classification hints (NCA must remain context-agnostic/input-dependent only)
* narrative weighting
* significance scoring

VII. KP1 IMPLEMENTATION — EVENTSEEDID SPEC v1.0 (LOCKED)
VII.1 Authority + timing
eventSeedId SHALL be minted only by 2B, at emission time, and never upstream/downstream.
VII.2 Fingerprint recipe (ANE_FINGERPRINT_V1) — Reference Mirror Only

**Authority Governance:**

This section mirrors ANE_FINGERPRINT_V1 as defined in NARRATIVE-STRUCTURAL-ASSEMBLER.md (2B).

2B (NARRATIVE-STRUCTURAL-ASSEMBLER) is the exclusive mint authority.
If any divergence occurs between this section and 2B's specification, 2B prevails.
This schema SHALL NOT independently modify or redefine fingerprint structure.

**Specification (as authorized by 2B):**

Normalization (deterministic, versioned):
* norm(x) = trim → lowercase → collapse whitespace to _ → remove disallowed punctuation → empty token if null

Canonical concatenation (exact order):
ANE-1.0 |
actorRole_norm |
action_norm |
objectRole_norm |
contextRole_norm |
timestampContext_norm |
sourceReference_norm

Hash:
* SHA-256 → lowercase hex

ID format:
* ANESEED_<sha256hex>

Exclusion rule:
* eventDescription SHALL NOT participate in fingerprinting (phrasing drift risk).

VIII. KP2 IMPLEMENTATION — EVENT ENUM REGISTRY v1.0 (LOCKED)
VIII.1 Governance
EVENT_ENUM_REGISTRY_V1 governs:
* actorRole
* action
* objectRole
* contextRole
2B is the exclusive enforcement point (mirrors 2A’s “enum normalization ownership” doctrine).
VIII.2 Unknown token policy (LOCKED)
If raw token cannot be mapped deterministically:
* mapped token = OTHER
* raw token captured in diagnostics (rawActorRole, etc.)
* mapping flag = fallback_other
No hard rejection for unknown tokens alone (unless other violations occur).

IX. KP3 IMPLEMENTATION — TIME NORMALIZATION + TIME BUCKET REGISTRY v1.0 (LOCKED)
IX.1 Dual time fields (required)
ANE MUST contain:
* timestampContext = precise normalized token
* timestampBucket = TIME_BUCKET_REGISTRY_V1 token or OTHER_TIME_BUCKET
IX.2 Mapping rules (deterministic patterns only)
2B SHALL map timestampContext → timestampBucket using pattern rules (no inference).If mapping fails:
* timestampBucket = OTHER_TIME_BUCKET
* rawTimestampContext captured
* timeMappingFlag = fallback_other_time_bucket
IX.3 Fingerprint interaction (LOCKED)
Fingerprint includes timestampContext_norm only.timestampBucket is excluded to avoid ID churn when bucket taxonomy evolves.

X. COMPATIBILITY WITH DOWNSTREAM CONTRACTS (HARD REQUIREMENTS)
X.1 NCA compatibility
* NCA SHALL receive ANE objects that are atomic and non-composite; composite inputs are rejected.
* NCA output remains strictly {classification, standaloneSubclass} with no enrichment.
X.2 META compatibility (CME)
META canonical CME schema requires: actorRole, action, objectRole, contextRole, eventDescription, timestampContext, sourceReference, subtype, permanence, id.Pre-NCA ANE supplies the event content fields; META adds subtype/permanence/id and performs canonical normalization and dedup.
X.3 SANTA compatibility (CSN)
SANTA canonical schema requires: actorRole, action, objectRole, contextRole, subclass, eventDescription, timestampContext, sourceReference, id.SANTA dedup occurs within the same timestampContext only, which is supported by KP3’s precise timestampContext.

XI. FAILURE STATES (2B REJECTION CODES)
2B SHALL reject (and log) any unit that violates:
* ERR_COMPOSITE_EVENT_DETECTED
* ERR_MEDIA_CONTEXT_DETECTED
* ERR_IDENTITY_ABSTRACTION_VIOLATION
* ERR_EVENT_ENUM_MAPPING_NONDETERMINISTIC
* ERR_TIMESTAMP_NORMALIZATION_FAILURE (only if normalization itself fails; bucket failure falls back)
* ERR_SOURCE_REFERENCE_MISSING
* ERR_REQUIRED_FIELD_MISSING
* ERR_SCHEMA_VERSION_MISMATCH
Rejection logging MUST preserve:
* original upstream unit reference
* reasonCode
* 2B version snapshot
(Parity with SANTA/META rejection ledger posture: “never silently discard.”)

XII. DETERMINISM LOCK
Given identical:
* upstream event material (post-split)
* EVENT_ENUM_REGISTRY_V1
* TIME_BUCKET_REGISTRY_V1
* ANE_FINGERPRINT_V1
* 2B agent version
2B MUST produce identical:
* ANE field values (including eventSeedId)
* envelope diagnostics
* mapping flags
* bucket assignments
No randomness permitted. No cross-run memory permitted.

XIII. REFERENCE IMPLEMENTATION EXAMPLE (one emitted envelope)
{
  "schemaVersion": "2B-EMIT-1.0",
  "event": {
    "schemaVersion": "ANE-1.0",
    "eventSeedId": "ANESEED_8a1f...c92e",
    "actorRole": "head_coach",
    "action": "announced",
    "objectRole": "starting_quarterback",
    "contextRole": null,
    "eventDescription": "A head coach announced a change to the starting quarterback.",
    "timestampContext": "season_2020_week_03",
    "timestampBucket": "REGULAR_SEASON_WEEK",
    "sourceReference": "doc:abc123#p4l22"
  },
  "diagnostics": {
    "schemaVersion": "EAD-1.0",
    "agentVersionSnapshot": "2B-0.1.0",
    "registryVersion": "EVENT_ENUM_REGISTRY_V1",
    "timeRegistryVersion": "TIME_BUCKET_REGISTRY_V1",
    "fingerprintVersion": "ANE_FINGERPRINT_V1",
    "rawActorRole": "Head Coach",
    "rawAction": "announced",
    "rawObjectRole": "starting QB",
    "rawContextRole": null,
    "roleMappingFlags": {
      "actorRole": "mapped",
      "action": "mapped",
      "objectRole": "mapped",
      "contextRole": "null"
    },
    "rawTimestampContext": "2020 Wk 3",
    "timeMappingFlag": "mapped",
    "splitProvenance": {
      "wasSplit": false,
      "sourceUnitId": "UPSTREAM-7781",
      "splitIndex": 0,
      "splitCount": 0
    },
    "dedup": {
      "dedupKey": "ANE-1.0|head_coach|announced|starting_quarterback||season_2020_week_03|doc:abc123#p4l22",
      "collisionCheck": "none",
      "collisionNotes": null
    }
  }
}

