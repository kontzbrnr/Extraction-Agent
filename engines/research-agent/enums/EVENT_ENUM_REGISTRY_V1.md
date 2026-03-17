EVENT ENUM REGISTRY — v1.0
Narrative Lane Canonical Vocabulary
Contract Authority: EVENT_ENUM_REGISTRY_V1

I. REGISTRY IDENTITY

registryId: EVENT_ENUM_REGISTRY_V1
version: ENUM_v1.0
lane: narrative
schemaVersion: CSN-1.0
fingerprintVersion: CSN_FINGERPRINT_V1

II. PURPOSE

This registry defines the complete canonical vocabulary for all narrative-lane
enum-bound fields. It is the sole authoritative source for:

* actorRole
* action
* objectRole
* contextRole
* ncaSubclass

No narrative canonical object may use any value not present in this registry.
No agent may introduce free text in place of a registered enum.
No enum may be shared with the Pressure lane.

III. GOVERNANCE RULES

1. snake_case only. No camelCase, PascalCase, hyphenation, or spaces.
2. No synonyms. One canonical token per concept. Closest-fit required.
3. No duplication. No two tokens may represent the same structural role.
4. No cross-lane reuse. Pressure enums SHALL NOT appear here. Narrative enums
   SHALL NOT appear in the Pressure registry.
5. No free text. Free text in any enum field constitutes a contract violation.
6. Extension requires version bump. No token may be added to ENUM_v1.0 after
   lock. All additions require ENUM_v1.1 or higher.
7. Tokens are immutable. Existing tokens may not be renamed, repurposed, or
   retired within a version. Retirement requires a new version.
8. Tokens are atomic. No compound concepts. No composite roles.
9. Tokens are semantically minimal. Least-specific token that satisfies the
   structural requirement. No specificity inflation.
10. Tokens are deterministic. Given identical source material, identical token
    assignment must result across all invocations.

IV. FINGERPRINT PARTICIPATION

The following fields participate in CSN_FINGERPRINT_V1:
* actorRole
* action
* objectRole
* contextRole
* subclass (ncaSubclass token, assigned by NCA)
* sourceReference (not enum-governed)

Enum registry version (ENUM_v1.0) is identity-affecting.
Any token change that affects fingerprint-participating fields SHALL:
1. Increment enumRegistryVersion
2. Increment fingerprintVersion
3. Require replay determinism validation

V. TOKEN LIST — actorRole

Purpose: The role of the primary initiating or experiencing actor in the event.
Ontological coverage: person, unit, org, abstract_system
Full taxonomy defined in ACTOR_ROLE_TAXONOMY_CONTRACT.md.

Allowed values:

head_coach
offensive_coordinator
defensive_coordinator
special_teams_coordinator
position_coach
quarterback
skill_player
offensive_lineman
defensive_lineman
linebacker
defensive_back
specialist
practice_squad_player
captain
general_manager
front_office_executive
owner
agent
medical_staff_member
referee
league_official
media_member
position_group
offensive_unit
defensive_unit
special_teams_unit
coaching_staff
roster_group
franchise
league_body
fan_base
unspecified_actor

Notes:
* Composite roles (e.g., veteran_quarterback) are prohibited.
* Multi-token actorRole is prohibited. One token per field.
* If no actor is identifiable, use: unspecified_actor
* Person-level tokens take precedence over unit-level when a single individual
  is the actor.

VI. TOKEN LIST — action

Purpose: The discrete structural action that occurred.
Ontological coverage: observed fact only. No interpretation. No framing.
Full taxonomy defined in ACTION_TAXONOMY_CONTRACT.md.

Allowed values:

appeared
departed
addressed
performed
refused
entered
exited
issued
withdrew
assembled
chanted
disrupted
celebrated
awarded
declined
missed
attended
participated
received
relocated
designated
presented
returned
challenged_authority
was_removed
was_ejected
was_designated
was_waived
was_signed
was_traded
was_released
observed
interacted
escorted

Notes:
* Tense does not participate. Tokens are infinitive/base form.
* Actions must be verifiable from observable record.
* Interpretive, causal, or sentiment verbs are prohibited.
* Compound verbs are prohibited. One action per token.
* "challenged_authority" is the only permitted compound; its semantics are
  structurally locked (see ACTION_TAXONOMY_CONTRACT.md Section VI).

VII. TOKEN LIST — objectRole

Purpose: The structural role of the entity or object the action was directed
at, received by, or acted upon.
Full taxonomy defined in OBJECT_ROLE_TAXONOMY_CONTRACT.md.

Allowed values:

media_audience
position_group
roster_slot
coaching_position
game_official
league_authority
teammate
opponent
field_surface
facility
practice_session
game_event
contract_offer
interview_session
press_conference
award_ceremony
crowd_gathering
ritual_sequence
team_meeting
travel_event
medical_event
unspecified_object

Notes:
* objectRole may be null. Null is permitted when no structural object exists.
* objectRole SHALL NOT equal actorRole within the same canonical object.
* objectRole is distinct from contextRole. See OBJECT_ROLE_TAXONOMY_CONTRACT.md.

VIII. TOKEN LIST — contextRole

Purpose: The situational or environmental frame within which the event occurred.
Full taxonomy defined in CONTEXT_ROLE_TAXONOMY_CONTRACT.md.

Allowed values:

regular_season
preseason
postseason
training_camp
offseason
game_day
practice_day
travel_day
bye_week
draft_period
contract_period
injury_period
suspension_period
media_availability
public_event
internal_event
unspecified_context

Notes:
* contextRole may be null. Null is permitted when no context is determinable.
* Time is not contextRole. Calendar dates, timestamps, and week markers are
  governed by TIME_BUCKET_REGISTRY_V1.md, not this field.
* contextRole may not encode lifecycle, recurrence, or emotional tone.

IX. TOKEN LIST — ncaSubclass

Purpose: The standalone narrative subclass assigned by NCA.
Authority: NCA (classifier); SANTA validates only.
This taxonomy is locked. No addition or modification without version bump.

Allowed values:

narrative_singularity
crowd_event
ritual_moment
anecdotal_beat
procedural_curiosity
conflict_flashpoint

Definitions (structural):
* narrative_singularity — unique, non-recurring, structurally unrepeatable event
* crowd_event — event initiated or constituted by fan/audience behavior
* ritual_moment — habitual or ceremonial action performed by an actor or group
* anecdotal_beat — incidental narrative occurrence without structural consequence
* procedural_curiosity — unusual deviation from standard procedure
* conflict_flashpoint — visible, observable tension event between parties

Notes:
* Exactly one subclass must be assigned per CSN object.
* Hybrid subclassing is prohibited.
* If subclass cannot be deterministically assigned, NCA must reject.

X. DUAL REGISTRY ISOLATION LOCK

Narrative enum registry (EVENT_ENUM_REGISTRY_V1) is completely independent from
the Pressure enum registry (PRESSURE_ENUM_REGISTRY_V1).

The following SHALL NOT occur:
* Narrative tokens reused in Pressure lane
* Pressure tokens reused in Narrative lane
* Cross-lane enum reference in any canonical object
* Cross-lane enum comparison in any validator

Cross-lane enum contamination is a contract violation.
CIV must reject any canonical object containing cross-lane enum values.

XI. LOCK STATEMENT

This registry is locked at ENUM_v1.0.
No token may be added, removed, or renamed without incrementing to ENUM_v1.1.
No synonym is permitted for any existing token.
No free text is permitted in any enum-governed field.
This contract integrates with:
* ACTOR_ROLE_TAXONOMY_CONTRACT.md
* ACTION_TAXONOMY_CONTRACT.md
* OBJECT_ROLE_TAXONOMY_CONTRACT.md
* CONTEXT_ROLE_TAXONOMY_CONTRACT.md
* TIME_BUCKET_REGISTRY_V1.md
* NARRATIVE-CLASSIFICATION-AGENT.md (NCA)
* STANDALONE-NARRATIVE-TRANSFORMER-AGENT.md (SANTA)
* CANONICAL-INTEGRITY-VALIDATOR.md (CIV)
