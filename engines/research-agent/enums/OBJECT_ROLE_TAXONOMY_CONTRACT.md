OBJECT ROLE TAXONOMY CONTRACT
Narrative Lane — objectRole Field Governance
Contract v1.0

I. PURPOSE

objectRole is the most ambiguity-prone field in the narrative canonical schema.
The boundary between actorRole, objectRole, and contextRole is frequently
misapplied at extraction. Misassignment corrupts canonical identity.

This contract defines:
* The structural meaning of objectRole
* How objectRole differs from actorRole
* How objectRole differs from contextRole
* Null permissibility and requirements
* Identity consequences of objectRole assignment

II. DEFINITION

objectRole is the abstract structural role of the entity, object, or target
that is the recipient, subject, or direct object of the action.

objectRole answers the question: WHAT or WHO received, bore, or was the
direct structural target of the action?

objectRole is distinct from:
* actorRole — who initiated or primarily experienced the event
* contextRole — the situational or environmental frame of the event

objectRole participates in CSN_FINGERPRINT_V1.
objectRole is optional. Null is permitted.
objectRole maps to an enum value from EVENT_ENUM_REGISTRY_V1 or is null.

III. STRUCTURAL DISTINCTION: objectRole vs actorRole

The boundary between actorRole and objectRole is causal direction.

actorRole is the entity that performs, initiates, or primarily experiences.
objectRole is the entity or thing that receives, is acted upon, or is the
target of that action.

Decision rule:
— Who or what did the acting? → actorRole
— Who or what received the action or was the target? → objectRole

Examples of correct assignment (structural, not specific):
* A coach addresses the media.
  actorRole: head_coach | action: addressed | objectRole: media_audience
  Rationale: coach initiates (actor); media receives the address (object)

* A general manager releases a player from roster.
  actorRole: general_manager | action: was_released
  objectRole: roster_slot
  Rationale: the player's position on the roster is the object of the
  release action; the roster_slot is what is structurally vacated

* A fan base assembles.
  actorRole: fan_base | action: assembled | objectRole: null
  Rationale: assembly has no structural target; objectRole is null

* A league official ejects a player.
  actorRole: league_official | action: was_ejected
  objectRole: null or game_event
  (Depends on whether the game event is structurally relevant)

IV. STRUCTURAL DISTINCTION: objectRole vs contextRole

objectRole is the DIRECT TARGET of the action.
contextRole is the SITUATIONAL FRAME in which the action occurred.

A game_day is not objectRole; it is contextRole.
A press_conference is objectRole if it is the target of the action
  (e.g., actorRole: head_coach | action: addressed | objectRole: press_conference).
A press_conference is contextRole if it is the setting in which something else
  occurred.

Decision rule:
— Could the action have been directed elsewhere? Does the object specify where
  the action was aimed? → objectRole
— Is this the surrounding situation, not the target? → contextRole
— Can it be removed without changing the structural meaning of the action? → contextRole

V. NULL PERMISSIBILITY

objectRole MAY be null.
objectRole is optional in the canonical schema.
objectRole null does not invalidate a canonical object.
objectRole null contributes an empty string to fingerprint normalization.

When objectRole MUST be null:
* The action has no structural target.
* No recipient, no directed object, no target entity exists in source material.
* Assigning a token would require inference or fabrication.

When objectRole MUST be assigned:
* The action has an identifiable direct structural target.
* The target is determinable from source material without inference.
* The target maps to a valid EVENT_ENUM_REGISTRY_V1 token.

objectRole SHALL NOT be assigned by default or habit.
objectRole SHALL NOT be invented to fill the field.
An incorrect objectRole is worse than null.

VI. objectRole CANNOT EQUAL actorRole

objectRole SHALL NOT contain the same token as actorRole in the same canonical
object.

Rationale: An actor cannot be both the initiating and receiving entity of the
same discrete action within a single canonical event. If this appears to be
the case, the event is either:
* Composite (must be split at extraction), OR
* Misclassified (actor/object assignment is incorrect)

Violation example:
actorRole: quarterback | action: interacted | objectRole: quarterback
→ REJECT: actorRole equals objectRole. Event is composite or misassigned.

Permitted reflexive-adjacent case:
actorRole: captain | action: addressed | objectRole: roster_group
→ VALID even if captain is part of roster_group. The token classes differ.

VII. TOKEN LIST

Allowed values for objectRole (from EVENT_ENUM_REGISTRY_V1.md):

media_audience        — collective audience of a media address or broadcast
position_group        — a defined position group within the team
roster_slot           — a formal position on the active or practice roster
coaching_position     — a formal coaching role or coaching staff seat
game_official         — a referee or officiating body member
league_authority      — a formal league governance entity
teammate              — a fellow player within the same franchise
opponent              — a player or unit from an opposing franchise
field_surface         — the physical playing field or practice field
facility              — a building, training facility, or physical location
practice_session      — a formally scheduled practice event
game_event            — a formally scheduled game or competitive event
contract_offer        — a formal contractual offer or agreement
interview_session     — a formal interview or media availability session
press_conference      — a formal press conference or media event
award_ceremony        — a formal awards event
crowd_gathering       — a mass assembly of fans or public spectators
ritual_sequence       — a defined recurring ritual pattern or ceremony
team_meeting          — an internal team gathering or formal meeting
travel_event          — a team travel or road trip occasion
medical_event         — a medical procedure, evaluation, or appointment
unspecified_object    — object is present but cannot be structurally classified

VIII. unspecified_object USAGE RULE

unspecified_object is a fallback token of last resort.
It signals: an object exists but cannot be classified to a specific token.

unspecified_object is NOT a default assignment.
unspecified_object requires:
* Confirmation that an object exists in the structural event.
* Confirmation that no existing token accurately represents it.
* A notation in the eventDescription explaining the unclassifiable nature.

If an object does not exist → assign null. Do not assign unspecified_object.
If an object can be classified → assign the correct token. Do not assign
unspecified_object.

IX. IDENTITY CONSEQUENCE

objectRole participates in CSN_FINGERPRINT_V1.
Two canonical objects with identical (actorRole, action, contextRole, subclass,
sourceReference) but different objectRole values produce different canonical IDs.
This is correct behavior: a different structural target is a different event.

Assignment must therefore be consistent:
* Given identical source material, identical objectRole must be assigned.
* Inconsistency across runs is a determinism violation.
* Null vs. a token are not equivalent. Do not alternate.

X. LOCK STATEMENT

objectRole is identity-bearing. It participates in CSN_FINGERPRINT_V1.
objectRole may be null. Null is a valid and sometimes required value.
objectRole SHALL NOT equal actorRole.
All assigned values must resolve to EVENT_ENUM_REGISTRY_V1.
No free text permitted.
No inference-based assignment permitted.
No default assignment permitted (unspecified_object is not a default).
This contract is locked at v1.0.
Extension requires OBJECT_ROLE_TAXONOMY_CONTRACT v1.1 and ENUM_v1.1.
This contract integrates with:
* EVENT_ENUM_REGISTRY_V1.md
* ACTOR_ROLE_TAXONOMY_CONTRACT.md
* CONTEXT_ROLE_TAXONOMY_CONTRACT.md
* STANDALONE-NARRATIVE-TRANSFORMER-AGENT.md (SANTA)
* CANONICAL-INTEGRITY-VALIDATOR.md (CIV)
