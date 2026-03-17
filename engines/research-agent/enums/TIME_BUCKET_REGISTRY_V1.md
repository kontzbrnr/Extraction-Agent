TIME BUCKET REGISTRY — v1.0
Narrative Lane — Temporal Staging Governance
Contract Authority: TIME_BUCKET_REGISTRY_V1

I. PURPOSE

This registry defines the canonical time bucket system for the Narrative lane.
Time buckets are referenced but have been undefined until this contract.
This contract formally defines, locks, and governs them.

Time buckets serve a specific and limited role:
* They provide deterministic temporal staging at the ANE (Atomic Narrative Event)
  pre-NCA level.
* They do NOT participate in canonical CSN object schema.
* They do NOT participate in CSN_FINGERPRINT_V1.
* They inform the timestampContext field, which is present in canonical CSN
  objects but is explicitly excluded from fingerprinting.

II. TIME BUCKET ONTOLOGY

Time buckets exist at two tiers:
* Tier A — Season Phase (coarse): structural phase of the football calendar
* Tier B — Calendar Week (fine): specific week within a season or offseason

Both tiers are assigned at ANE staging.
Tier A is the primary structural anchor.
Tier B provides temporal resolution within a Tier A phase.

Tier A and Tier B together constitute a fully qualified time bucket.
Neither tier alone is a complete time bucket assignment.

III. TIER A — SEASON PHASE BUCKETS

Purpose: Identifies the structural phase of the football calendar.
Format: season_phase_token
Allowed values:

offseason          — period between end of postseason and start of training camp
training_camp      — formal pre-season training phase (practice opens through
                     final preseason game)
preseason          — formal preseason game period
regular_season     — weeks 1 through end of regular season schedule
playoffs           — wild card through conference championship week
championship_week  — super bowl or equivalent championship week
draft_period       — formal draft window (typically within offseason)
free_agency_period — formal free agency window (typically within offseason)

Notes:
* draft_period and free_agency_period are sub-phases of offseason.
  They may be assigned instead of offseason when the source material is
  clearly situated within those sub-phases.
* Tier A phases are mutually exclusive for any given event.
  An event cannot be in both preseason and regular_season simultaneously.
* Tier A phases are exhaustive. Every event must fall within one.
* If the Tier A phase cannot be determined → assign offseason as default
  only when no other phase is determinable. Flag for review.

IV. TIER B — CALENDAR WEEK BUCKETS

Purpose: Provides temporal resolution within a Tier A phase.
Format: YYYY_WXX (ISO week format)

bucketId format:
  YYYY_WXX
  where:
    YYYY = four-digit year (calendar year of the week start)
    W    = literal character "W"
    XX   = two-digit ISO week number (01 through 53), zero-padded

Examples:
  2024_W01   = First ISO week of 2024
  2024_W32   = 32nd ISO week of 2024
  2025_W01   = First ISO week of 2025

Rules:
* ISO week numbering standard (ISO 8601) applies.
  Week 01 is the week containing the first Thursday of the year.
* All Tier B values are zero-padded to two digits (W01 not W1).
* Year in Tier B is the calendar year of the week's Monday.
  For weeks crossing year boundaries, use the ISO year, not the calendar year
  of the specific event date.
* Tier B is always present alongside Tier A. Never assign Tier A without Tier B.
  If the specific week cannot be determined → use W00 as an explicit
  unknown-week marker. W00 is reserved for unresolvable week assignment only.

V. FULLY QUALIFIED TIME BUCKET FORMAT

A complete time bucket assignment is:

bucketId: YYYY_WXX
seasonPhase: <tier_a_token>

These two fields together constitute the TIME_BUCKET_V1 record.

Stored at ANE level in timestampBucket field.
NOT stored in canonical CSN object (timestampBucket is an excluded field per
NARRATIVE-FIELD-INVENTORY.md).

VI. OVERLAP POLICY

Tier A phases are designed to be non-overlapping for any given event.
If source material places an event at a phase boundary:
* Use the phase the event is structurally closer to.
* Do not split across two phases.
* If genuinely ambiguous → flag for human review; use the later phase.

Tier B weeks are non-overlapping by definition (ISO weeks do not overlap).

VII. INCLUSIVE vs EXCLUSIVE BOUNDARY POLICY

All time buckets are fully inclusive on both ends.
A week bucket YYYY_WXX includes the full Monday-through-Sunday span.
A season phase bucket includes its entire structural duration.

No event falls "between" buckets.
All events must be assigned to a bucket.
No partial bucket membership.

VIII. BUCKET NORMALIZATION RULES

When normalizing a raw timestampContext string to a time bucket:

Step 1 — Parse the timestampContext for any date signal.
  Acceptable date signals: exact date, week reference, game number,
  month reference, season phase label.

Step 2 — Map to Tier A:
  Assign the most specific Tier A phase based on:
  * Explicit phase language in source ("during training camp", "week 7", etc.)
  * Contextual inference from game number, event type, or timing
  * If ambiguous → use offseason as fallback, flag for review.

Step 3 — Map to Tier B:
  Derive the ISO week number from any available date anchor.
  If exact date available → compute ISO week directly.
  If week number referenced → convert to YYYY_WXX format.
  If only month available → use the first full week of that month.
  If no date signal available → assign W00 and flag.

Step 4 — Compose bucketId:
  bucketId = YYYY_WXX (per Section IV format).

Step 5 — Store at ANE level only.
  Do not persist timestampBucket to canonical CSN object.

IX. IDENTITY PARTICIPATION RULE

timestampBucket (Tier A + Tier B) does NOT participate in CSN_FINGERPRINT_V1.

Per TIME & RECURRENCE PARTITION DOCTRINE:
* SANTA v1.0 explicitly excludes timestampContext from fingerprinting.
* Therefore timestampBucket, which is a derived staging artifact, also
  does not participate in canonical identity.

Time bucket assignment informs the timestampContext prose field only.
timestampContext is stored in the canonical CSN object for archival and
query purposes but is identity-excluded.

NOTE on NARRATIVE LIFECYCLE CONTRACT alignment:
Section IV of the Narrative Lifecycle Contract states "Narrative identity MAY
include timestampContext." This is not in conflict. Whether timestampContext
participates in identity is a decision of SANTA's fingerprint specification.
SANTA v1.0 explicitly excludes it. Therefore, under SANTA v1.0, narrative
canonical identity is time-neutral.

This may be revisited in a future fingerprint version. Any change requires:
* SANTA version increment
* fingerprintVersion increment
* Replay determinism revalidation

X. VERSIONING DISCIPLINE

TIME_BUCKET_REGISTRY_V1 is locked at v1.0.
Changes that require a version bump to V2:
* Addition or removal of Tier A phase tokens
* Change to bucketId format
* Change to week numbering standard
* Change to ISO week boundary rules

Changes that do NOT require a version bump:
* Documentation clarifications that do not alter behavior
* Additional examples or annotations

Version increments must be coordinated with:
* NARRATIVE-LIFECYCLE-CONTRACT.md (Section V enum governance)
* EVENT_ENUM_REGISTRY_V1.md (if time tokens are cross-referenced)
* SANTA fingerprint version if identity participation changes

XI. NO IMPLICIT TIME LOGIC

No agent may infer a time bucket from contextual knowledge not present in
source material.
No agent may assume a time bucket based on team, league, or seasonal expectations.
No agent may apply prior-run temporal memory to time bucket assignment.

All time bucket derivation must be deterministic from source material alone.
Given identical source material → identical time bucket assignment across all
runs, agents, and invocations.

Implicit time inference is a determinism violation.

XII. LOCK STATEMENT

TIME_BUCKET_REGISTRY_V1 is locked at v1.0.
Time buckets are ANE-level staging artifacts only.
Time buckets do not participate in canonical CSN identity.
Tier A phase tokens are exhaustive and mutually exclusive.
Tier B week tokens are ISO 8601 standard, zero-padded, non-overlapping.
Fully qualified time bucket = YYYY_WXX + seasonPhase token.
No implicit time inference permitted.
All derivation must be source-material-deterministic.
This contract integrates with:
* NARRATIVE-FIELD-INVENTORY.md (timestampBucket as excluded canonical field)
* TIME-RECURRENCE-PARTITION-DOCTRINE.md (time identity governance)
* NARRATIVE-LIFECYCLE-CONTRACT.md (enum governance Section V)
* STANDALONE-NARRATIVE-TRANSFORMER-AGENT.md (SANTA timestampContext exclusion)
* EVENT_ENUM_REGISTRY_V1.md (season phase alignment with contextRole tokens)
