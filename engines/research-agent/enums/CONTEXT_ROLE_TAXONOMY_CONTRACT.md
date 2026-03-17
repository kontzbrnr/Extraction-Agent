CONTEXT ROLE TAXONOMY CONTRACT
Narrative Lane — contextRole Field Governance
Contract v1.0

I. PURPOSE

contextRole is the most ambiguous field in the narrative canonical schema.
Its boundaries with objectRole, with time fields, and with lifecycle metadata
are frequently violated at extraction.

This contract defines:
* What constitutes a valid contextRole
* What is explicitly not contextRole
* Null permissibility
* Fingerprint participation rules
* Hard prohibitions against lifecycle, recurrence, and emotional injection

II. DEFINITION

contextRole is the situational or environmental frame within which the event
occurred. It answers: IN WHAT STRUCTURAL CONTEXT did this event take place?

contextRole is the surrounding condition, not the target.
contextRole is structural framing, not narrative judgment.
contextRole is schema-bound, not free text.

contextRole participates in CSN_FINGERPRINT_V1.
contextRole is optional. Null is permitted.
contextRole maps to an enum value from EVENT_ENUM_REGISTRY_V1 or is null.

III. WHAT COUNTS AS contextRole

A valid contextRole satisfies all of the following:
1. It describes the situational or environmental frame of the event.
2. It is directly determinable from source material.
3. It maps to a defined token in EVENT_ENUM_REGISTRY_V1.
4. It is structural, not evaluative.
5. It is free of temporal specificity (no calendar dates, no week numbers).
   Temporal specificity belongs to TIME_BUCKET_REGISTRY_V1, not contextRole.

Valid contextRole examples:
* An event that occurred during a game → contextRole: game_day
* An event that occurred during training camp → contextRole: training_camp
* An event that occurred during a media availability → contextRole: media_availability
* An event with no determinable context → contextRole: null
* An event that occurred during the postseason → contextRole: postseason

IV. WHAT DOES NOT COUNT AS contextRole

The following SHALL NOT appear as contextRole values:

1. Calendar time. Week numbers, months, dates are not contextRole.
   "Week 14" is not contextRole. Use TIME_BUCKET_REGISTRY_V1 at ANE level.
   "November" is not contextRole.

2. Lifecycle phase. "first year," "second season," "contract year" are not
   contextRole. These encode lifecycle metadata and are prohibited from
   canonical objects entirely.

3. Recurrence indicators. "again," "repeated," "for the third time" —
   these are not contextRole. Recurrence is modeled via Cycle Association Log
   only. It does not participate in canonical identity.

4. Emotional or evaluative states. "tense atmosphere," "hostile environment,"
   "celebratory mood" are not contextRole. These are narrative framing.
   eventDescription is the appropriate location for observational prose.

5. Outcome-bearing conditions. "post-loss environment," "following the victory"
   are not contextRole. Outcomes are not canonical context.

6. Player status. "injured player's context," "suspension context" are not
   contextRole for the receiving player. These are lifecycle descriptors.
   EXCEPTION: injury_period and suspension_period are valid contextRole tokens
   when they describe the structural phase the event occurred in, not the
   player's personal status.

7. Proper nouns. Named venues, cities, or franchise names are not contextRole.
   contextRole is abstract and institutional, not location-specific.

V. NULL PERMISSIBILITY

contextRole MAY be null.
contextRole is optional in the canonical schema.
contextRole null does not invalidate a canonical object.
contextRole null contributes an empty string to fingerprint normalization.

When contextRole MUST be null:
* The situational frame is not determinable from source material.
* No valid token accurately represents the context without inference.
* The event is context-independent (pure actor-action, no meaningful frame).

When contextRole MUST be assigned:
* A clear situational frame exists in source material.
* That frame maps to a valid EVENT_ENUM_REGISTRY_V1 token.
* Assigning null would lose structurally significant framing information.

contextRole SHALL NOT be assigned to avoid null.
An incorrect contextRole is worse than null.

VI. FINGERPRINT PARTICIPATION

contextRole participates in CSN_FINGERPRINT_V1.
This means: two events identical in all other fields but with different
contextRole values produce different canonical IDs.
This is correct behavior. The same action in a different structural context
is a different event.

Assignment must be consistent:
* Given identical source material, identical contextRole must be assigned.
* Inconsistency across runs is a determinism violation.
* Null and a token are not equivalent. Do not alternate.

Implication: contextRole assignment is load-bearing.
Extractors must apply it with the same discipline as actorRole and action.

VII. TIME AS contextRole — PROHIBITED

Time CANNOT be contextRole.
Calendar dates, week markers, time-of-day, and year values are NOT contextRole.

Time is governed by TIME_BUCKET_REGISTRY_V1.md exclusively.
Time participates in canonical identity via the ANE timestampBucket (pre-NCA)
and via timestampContext (in the canonical CSN object, non-fingerprint).

Permitted contextRole tokens that overlap with time:
The following tokens are temporal in flavor but are structural phase markers,
not time values. They ARE valid contextRole:

regular_season        — the formal regular season competitive phase
preseason             — the formal preseason competitive phase
postseason            — the formal postseason competitive phase
training_camp         — the formal pre-season training phase
offseason             — the formal non-competitive organizational phase
bye_week              — the formally scheduled off-week within regular season
draft_period          — the formal player acquisition period
contract_period       — a formal contract negotiation or execution window
injury_period         — a period structurally defined by an active injury
suspension_period     — a period structurally defined by an active suspension

These tokens describe structural phases, not calendar time.
They do not carry specific temporal values and do not substitute for
TIME_BUCKET_REGISTRY_V1 time bucket assignment.

VIII. TOKEN LIST

Allowed values for contextRole (from EVENT_ENUM_REGISTRY_V1.md):

regular_season        — formal competitive regular season phase
preseason             — formal competitive preseason phase
postseason            — formal competitive postseason phase
training_camp         — pre-season training environment
offseason             — non-competitive organizational period
game_day              — day of a scheduled competitive game
practice_day          — day of a scheduled practice session
travel_day            — team travel day
bye_week              — formal off-week within a regular season schedule
draft_period          — formal player acquisition / draft window
contract_period       — formal contract negotiation or execution window
injury_period         — structurally defined active injury phase
suspension_period     — structurally defined active suspension phase
media_availability    — formal scheduled media access window
public_event          — any event occurring in a public-facing setting
internal_event        — any event occurring within internal franchise operations
unspecified_context   — context is present but cannot be classified

IX. LIFECYCLE INJECTION PROHIBITION

contextRole SHALL NOT encode lifecycle metadata.
Lifecycle information belongs exclusively in the Cycle Association Log
(external to canonical objects).

The following are lifecycle artifacts and SHALL NOT appear in contextRole:
* firstSeen, lastSeen, recurrenceCount, decayScore, clusterMembership
* Any token implying how many times an event has occurred
* Any token implying a trend, escalation, or decay trajectory
* Any token implying structural consequence or cumulative impact

No lifecycle concept may be backported into contextRole under any framing.

X. RECURRENCE ENCODING PROHIBITION

contextRole SHALL NOT encode recurrence.
"recurring_pattern," "habitual_context," "established_ritual" are not valid
contextRole tokens. They are lifecycle artifacts.

Recurrence is modeled exclusively via:
* Cycle Association Log (external to canonical objects)
* PQG analytics layer (post-canonical)

The canonical object itself must be recurrence-agnostic.
Two identical events at different times produce two separate canonical objects.
contextRole does not differentiate the first occurrence from the fiftieth.

XI. EMOTIONAL INTERPRETATION PROHIBITION

contextRole SHALL NOT carry emotional or evaluative coloring.
Tokens must be structurally neutral.

Prohibited constructions:
* tense_atmosphere
* hostile_environment
* celebratory_context
* controversial_backdrop
* charged_situation

These are narrative framing. They belong in eventDescription prose only.
They must never enter contextRole or any fingerprint-participating field.

XII. LOCK STATEMENT

contextRole is identity-bearing. It participates in CSN_FINGERPRINT_V1.
contextRole may be null. Null is a valid and sometimes required value.
Time is not contextRole. Calendar values do not belong here.
Lifecycle injection is prohibited. Recurrence encoding is prohibited.
Emotional interpretation is prohibited.
All assigned values must resolve to EVENT_ENUM_REGISTRY_V1.
No free text permitted.
This contract is locked at v1.0.
Extension requires CONTEXT_ROLE_TAXONOMY_CONTRACT v1.1 and ENUM_v1.1.
This contract integrates with:
* EVENT_ENUM_REGISTRY_V1.md
* OBJECT_ROLE_TAXONOMY_CONTRACT.md
* TIME_BUCKET_REGISTRY_V1.md
* TIME-RECURRENCE-PARTITION-DOCTRINE.md
* STANDALONE-NARRATIVE-TRANSFORMER-AGENT.md (SANTA)
* CANONICAL-INTEGRITY-VALIDATOR.md (CIV)
* NARRATIVE-LIFECYCLE-CONTRACT.md
