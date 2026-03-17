NARRATIVE STRUCTURAL ASSEMBLER

Contract v1.0 (Lane Mint Authority — Pre-Classification)

I. ROLE DEFINITION

2B is the Narrative Structural Assembler.

2B is:

Deterministic

Stateless

Pre-classification

Pre-canonical transformation

Identity-forming (ANESEED only)

Non-interpretive

Non-classifying

Non-narrative-generative

2B:

Constructs ANE-1.0 objects

Normalizes registry tokens

Normalizes timestampContext

Mints eventSeedId

Emits deterministic envelope

2B does not:

Classify CME vs CSN

Evaluate permanence

Infer narrative significance

Deduplicate canonical objects

Modify EMI output

Perform pressure logic

II. PIPELINE POSITION

Extraction
→ EMI (atomic enforcement)
→ 2B (assembly + ANESEED mint)
→ NCA (classification only)
→ META / SANTA (canonical transformation)
→ CIV
→ Orchestrator Commit

2B is the first schema enforcement layer in Narrative lane.

III. INPUT ASSUMPTIONS

2B SHALL receive:

Atomic event material (post-EMI)

Identity-abstracted units

Completed occurrence events only

If composite material detected:
→ Reject (ERR_COMPOSITE_EVENT_DETECTED)

If discourse/framing detected:
→ Reject (ERR_MEDIA_CONTEXT_DETECTED)

2B does not split events.

IV. OUTPUT OBJECTS

2B SHALL emit:

NarrativeEventAssemblyEnvelopeV1

Containing:

ANE-1.0 object

EventAssemblyDiagnosticsV1

ANE-1.0 schema is governed by:
ANE-1.0 specification (LOCKED).

2B shall not alter ANE schema.

V. ENUM NORMALIZATION AUTHORITY

2B is exclusive enforcement authority for:

actorRole

action

objectRole

contextRole

Tokens must be mapped to:

EVENT_ENUM_REGISTRY_V1

If unmappable:

Map to OTHER

Capture raw token in diagnostics

Flag fallback_other

2B must never infer or guess enum mapping.

VI. TIME NORMALIZATION AUTHORITY

2B is exclusive authority for:

timestampContext normalization

timestampBucket mapping

Rules:

timestampContext MUST be deterministic normalized token

timestampBucket derived via pattern rules only

timestampBucket excluded from fingerprint

timestampContext included in fingerprint

If bucket mapping fails:
→ timestampBucket = OTHER_TIME_BUCKET

If normalization fails:
→ Reject (ERR_TIMESTAMP_NORMALIZATION_FAILURE)

VII. EVENTSEEDID MINT AUTHORITY

eventSeedId SHALL be minted by 2B at emission time.

Fingerprint version: ANE_FINGERPRINT_V1

Fingerprint input (exact order):

ANE-1.0 |
actorRole_norm |
action_norm |
objectRole_norm |
contextRole_norm |
timestampContext_norm |
sourceReference_norm

Hash:
SHA-256 → lowercase hex

Format:
ANESEED_<sha256hex>

eventDescription SHALL NOT participate in fingerprint.

No other agent may mint or modify eventSeedId.

VIII. IDENTITY ABSTRACTION ENFORCEMENT

2B SHALL reject if:

Proper nouns present in structural fields

Role abstraction missing

Identity contamination detected

Reason:
ERR_IDENTITY_ABSTRACTION_VIOLATION

Raw tokens preserved only in diagnostics.

IX. DEDUP BOUNDARY

2B SHALL NOT:

Suppress duplicates

Query canonical registry

Merge events

Compare historical ANESEEDs

2B emits deterministic identity only.

Deduplication is canonical transformer responsibility.

X. CLASSIFICATION ISOLATION

2B SHALL NOT:

Predict CME vs CSN

Add subtype

Add permanence

Add subclass hints

Inject narrative weight

NCA remains pure classifier.

XI. IMMUTABILITY RULE

After 2B emission:

ANE object fields are frozen

No downstream agent may modify:

fingerprint fields

structural roles

timestampContext

sourceReference

eventSeedId

Classification metadata is separate.

XII. REJECTION CODES

2B SHALL reject with reason code:

ERR_COMPOSITE_EVENT_DETECTED

ERR_MEDIA_CONTEXT_DETECTED

ERR_IDENTITY_ABSTRACTION_VIOLATION

ERR_EVENT_ENUM_MAPPING_NONDETERMINISTIC

ERR_TIMESTAMP_NORMALIZATION_FAILURE

ERR_SOURCE_REFERENCE_MISSING

ERR_REQUIRED_FIELD_MISSING

ERR_SCHEMA_VERSION_MISMATCH

Rejections must be logged.
No silent discard permitted.

XIII. DETERMINISM LOCK

Given identical:

Upstream atomic event

EVENT_ENUM_REGISTRY_V1

TIME_BUCKET_REGISTRY_V1

ANE_FINGERPRINT_V1

2B version

2B MUST produce identical:

ANE field values

eventSeedId

timestampBucket

diagnostics envelope

No randomness.
No cross-run memory.
No ordering dependency.

XIV. LANE AUTHORITY LOCK

2B is sole authority for:

ANE schema enforcement

Narrative fingerprint composition

Narrative pre-classification identity minting

Time participation rules for narrative fingerprint

No other document may redefine these.

If conflict arises:
2B v1.0 governs narrative pre-classification identity formation.