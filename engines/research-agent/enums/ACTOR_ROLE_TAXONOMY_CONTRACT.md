ACTOR ROLE TAXONOMY CONTRACT
Narrative Lane — actorRole Governance
Contract v1.0

I. PURPOSE

This contract formally governs the actorRole field in narrative canonical objects.
actorRole cannot be casually assigned. It carries structural identity weight.
actorRole participates in CSN_FINGERPRINT_V1.
Errors in actorRole produce incorrect canonical IDs and break deduplication.

This contract defines:
* Ontological level hierarchy
* Role abstraction rules
* Boundary conditions (when actorRole becomes objectRole)
* Composite role prohibition
* Collision policy

II. DEFINITION

actorRole is the abstract role of the primary initiating or experiencing entity
in a narrative event.

actorRole captures WHO structurally caused or experienced the event.
actorRole does NOT capture WHO was affected by the event (see objectRole).
actorRole does NOT capture the situation or setting (see contextRole).

actorRole is always abstract. No proper nouns. No named individuals.
actorRole is always a single token. No compound tokens.
actorRole maps to an enum value from EVENT_ENUM_REGISTRY_V1.

III. ONTOLOGICAL LEVEL HIERARCHY

actorRole tokens are organized into four ontological levels.
Assignment must use the most specific applicable level.

Level 1 — PERSON (individual role):
Tokens that represent a single individual in a defined structural role.

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

Rules for Level 1:
* Use when the event initiator is a single identifiable individual.
* Do not use when two or more individuals of the same type are jointly involved;
  elevate to Level 2 (unit).
* Role specificity is required. Do not use a generic token when a specific role
  is determinable from source material.

Level 2 — UNIT (structured group within a franchise):
Tokens that represent a defined subunit of an organization.

position_group
offensive_unit
defensive_unit
special_teams_unit
coaching_staff
roster_group

Rules for Level 2:
* Use when the primary actor is a formally defined internal group.
* Do not use for ad hoc groupings or informal assemblies.
* fan_base is NOT Level 2. It is Level 3 (org-external).

Level 3 — ORG (organizational body):
Tokens that represent an entire organizational entity.

franchise
league_body
fan_base

Rules for Level 3:
* Use only when no Level 1 or Level 2 token applies.
* fan_base is org-level because it is externally constituted relative to the
  franchise structure.
* league_body covers any formal league-level institution.

Level 4 — ABSTRACT SYSTEM / UNSPECIFIED:
Tokens that represent no identifiable structural actor.

unspecified_actor

Rules for Level 4:
* Use only when actor cannot be structurally identified from source material.
* Unspecified_actor is a fallback of last resort.
* Do not use to avoid making a determination when a determination is possible.

IV. ROLE ABSTRACTION RULES

1. No proper nouns. Actor identity must be role-based.
   — VIOLATION: "Tom Brady" → REJECT
   — REQUIRED: "quarterback"

2. No descriptive qualifiers. Tokens must be bare role labels.
   — VIOLATION: "aging_veteran_quarterback" → REJECT
   — REQUIRED: "quarterback"

3. No compound roles. One structural role per token.
   — VIOLATION: "veteran_quarterback" → REJECT
   — VIOLATION: "injured_captain" → REJECT
   — REQUIRED: "quarterback" or "captain" (most structurally relevant role wins)

4. No status embedding. Role tokens do not carry lifecycle status.
   — VIOLATION: "injured_player" → REJECT (injury is contextRole, not actorRole)
   — REQUIRED: appropriate position-level token

5. No emotional or evaluative language.
   — VIOLATION: "troubled_quarterback" → REJECT
   — VIOLATION: "elite_defender" → REJECT

6. Abstraction is required even for franchise-level events.
   — VIOLATION: "Dallas Cowboys" → REJECT
   — REQUIRED: "franchise"

V. WHEN actorRole BECOMES objectRole

actorRole is the initiating or primary experiencing entity.
objectRole is the receiving or secondary entity.

Apply the following decision rule:

— Is the entity the one performing or experiencing the event first-hand?
  YES → actorRole
  NO  → objectRole

Examples (structural, not illustrative of actual events):
* A coach addresses the media.
  → actorRole: head_coach
  → objectRole: media_audience

* A player receives a designation.
  → actorRole: general_manager (designator)
  → objectRole: roster_slot or the player's positional role
  (designation is an action FROM front office, not FROM player)

* A crowd disrupts a game event.
  → actorRole: fan_base
  → objectRole: game_event

Role assignment must reflect causal/experiential direction, not importance.
The "more important" entity is not automatically the actor.

VI. MULTI-ROLE PROHIBITION

Multi-role tokens are prohibited.
composite tokens are prohibited.
A canonical event has exactly one actorRole value.

If an event appears to require two actors:
* Evaluate whether the event is truly atomic.
* If composite → reject at extraction. Do not force single actorRole.
* If atomic but ambiguous → assign the primary causal or experiential actor.
* Secondary actor maps to objectRole if applicable.

The following compound constructions are permanently disallowed:
* veteran_quarterback
* injured_captain
* backup_offensive_lineman
* young_linebacker
* starting_quarterback

Any token containing an underscore-joined adjective + role is disallowed.

VII. COLLISION POLICY

Collision = two events in the same timestampContext with identical
(actorRole, action, objectRole, contextRole, subclass) tuples.

Per SANTA v1.0 deduplication policy:
* Identical events within same timestampContext → deduplicate (one canonical object)
* Identical events across distinct timestampContext → distinct canonical objects

actorRole token assignment must be consistent to make deduplication reliable.
Given identical source material, identical actorRole must be assigned.
Inconsistent actorRole assignment across runs is a determinism violation.

VIII. BOUNDARY CONDITIONS — EDGE CASES

1. A player's agent acts on behalf of the player.
   → actorRole: agent (not the player)
   → The player maps to objectRole if they are the subject of the action.

2. A group of players collectively demonstrates.
   → actorRole: roster_group or position_group depending on specificity.
   → Not individual-level even if individual names are known.

3. League imposes a ruling.
   → actorRole: league_body or league_official depending on whether action
     is institutional or individual.

4. An event is crowd-initiated.
   → actorRole: fan_base
   → Subclass will typically be crowd_event.

5. A medical event involves a player.
   → Determine who initiated: medical_staff_member (if staff acted) or
     the player's positional token (if player experienced or initiated).

IX. LOCK STATEMENT

actorRole is identity-bearing. It participates in CSN_FINGERPRINT_V1.
Errors here produce incorrect canonical IDs.
No free text is permitted. All values must resolve to EVENT_ENUM_REGISTRY_V1.
No composite tokens. No proper nouns. No status embedding.
This contract is locked at v1.0.
Extension requires ACTOR_ROLE_TAXONOMY_CONTRACT v1.1 and ENUM_v1.1.
This contract integrates with:
* EVENT_ENUM_REGISTRY_V1.md
* STANDALONE-NARRATIVE-TRANSFORMER-AGENT.md (SANTA)
* IDENTITY-ABSTRACTION-ENFORCEMENT-CONTRACT.md
* CANONICAL-INTEGRITY-VALIDATOR.md (CIV)
