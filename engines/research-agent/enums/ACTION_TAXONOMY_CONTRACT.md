ACTION TAXONOMY CONTRACT
Narrative Lane — action Field Governance
Contract v1.0

I. PURPOSE

The action field is the most structurally dangerous enum in the narrative lane.
An incorrectly defined action token introduces:
* Interpretive contamination into canonical identity
* Causal framing in ostensibly neutral records
* Fingerprint instability across extraction runs

This contract defines:
* What qualifies as a valid action token
* Atomicity rules
* Tense and form requirements
* Event-type vs claim-type distinction
* Observed-fact vs narrative-framing distinction
* Explicit prohibitions

II. DEFINITION

action is the discrete structural thing that occurred.
action captures WHAT HAPPENED structurally.
action does not capture WHY it happened.
action does not capture WHAT IT MEANS.
action does not capture WHAT RESULTED from it.

action maps to a single enum token from EVENT_ENUM_REGISTRY_V1.
action participates in CSN_FINGERPRINT_V1.
Errors in action produce incorrect canonical IDs.

III. FORM REQUIREMENTS

1. Verbs only. action tokens must be verb-form.
   No nouns, no noun phrases, no gerunds as primary token.

2. Base/infinitive form only. Tense does NOT participate.
   — VIOLATION: "addressed_media" (compound with object) → REJECT
   — VIOLATION: "was_addressing" (progressive) → stored form exists; see Section IV
   — REQUIRED: "addressed"

3. Tense exclusion rule. Tense SHALL NOT participate in token identity.
   Past, present, and future tense all resolve to the same token.
   "He addressed" and "she addresses" both map to: addressed

4. Active and passive forms both permitted as separate tokens where structural
   distinction is meaningful.
   Active example: "general_manager" + "designated" + "roster_slot"
   Passive example: "practice_squad_player" + "was_designated" + (null)
   Active and passive are structurally distinct events.
   was_* prefix tokens are reserved for passive-voice structural events only.

IV. EVENT-TYPE vs CLAIM-TYPE DISTINCTION

Event-type tokens: record a physical, procedural, or observable action.
Claim-type tokens: record a speech act, statement issuance, or communicative act.

BOTH are permitted. The distinction must be preserved in the token itself.

Event-type tokens (sampling):
appeared, departed, entered, exited, performed, celebrated, assembled,
chanted, disrupted, refused, relocated, participated, returned, interacted

Claim-type tokens (sampling):
addressed, issued, challenged_authority, declined, withdrawn

Rules:
* Do not conflate event-type and claim-type.
  "addressed" = speech act (claim-type)
  "appeared" = physical event (event-type)
  These are distinct tokens. Do not merge.
* Claim-type tokens must describe the speech act, not its content.
  "issued" covers any formal statement issuance.
  The content of the statement is captured in eventDescription, not action.

V. OBSERVED FACT vs NARRATIVE FRAMING DISTINCTION

This is the critical boundary.

Observed fact: directly verifiable from source record without interpretation.
Narrative framing: interpretation, emotional tone, or causal attribution applied
to an event by a reporter, analyst, or observer.

action tokens MUST represent observed fact.
action tokens MUST NOT represent narrative framing.

Examples:
* OBSERVED FACT: A coach stood up during a press conference.
  → actorRole: head_coach | action: appeared | (or addressed if speech-act)
* NARRATIVE FRAMING: A coach defiantly challenged reporters.
  → "defiantly" is framing. "challenged reporters" is interpretive.
  → Extract the structural action: addressed or issued
  → Framing belongs in eventDescription (narrative prose), not action token.

The action token must be verifiable:
* Can an independent observer confirm this action occurred?
* Would two neutral observers assign the same action token?
* Is the token free of emotional or causal coloring?
If NO to any: reject or select a more neutral token.

VI. ATOMICITY RULES

Each action token represents exactly one discrete action.
Compound verbs are prohibited with one exception.

PROHIBITED compound patterns:
* refused_to_participate → use: refused (object: practice_session or unspecified)
* publicly_addressed → use: addressed (framing "publicly" belongs in eventDescription)
* violently_confronted → REJECT (sentiment contamination)
* emotionally_withdrew → REJECT (sentiment contamination)

ONE EXCEPTION — challenged_authority:
This token is permanently admitted as a compound because:
* "challenged" alone is ambiguous (contested? questioned? disputed?)
* "challenged_authority" has a locked structural meaning: an actor performed
  an observable act of formal or procedural resistance directed at an authority
  structure (referee, league official, coach, front office, or league body).
* It is NOT interpretive. It describes an observable structural confrontation.
* Semantics are locked by this contract. They may not be reinterpreted.

challenged_authority usage rule:
* The objectRole must be: game_official, league_authority, coaching_position,
  or an equivalent authority-bearing role.
* If no authority-bearing objectRole is present, challenged_authority is invalid.
  Use: addressed, issued, or interacted instead.

VII. EXPLICIT PROHIBITIONS

The following verb categories are permanently prohibited from action tokens:

1. CAUSAL VERBS — verbs that assert why something happened:
   — sparked, triggered, caused, provoked, inspired, motivated, led_to, prompted
   → These are causal interpretations, not observed events.

2. INTERPRETIVE VERBS — verbs that embed meaning:
   — signaled, revealed, demonstrated_that, confirmed, suggested, indicated,
     implied, showed, exposed, underscored
   → These assert interpretation, not occurrence.
   — EXCEPTION: demonstrated as a purely physical action is permitted:
     "demonstrated" = performed a visible physical demonstration (e.g., protest
     gesture, physical act). It does not mean "demonstrated that X was true."

3. SENTIMENT VERBS — verbs that embed emotional valence:
   — stormed, erupted, slammed, blasted, lashed_out, fumed, celebrated_wildly
   — EXCEPTION: celebrated is permitted as a neutral observable action.
     The sentiment qualifier (wildly) is prohibited; "celebrated" alone is not.

4. OUTCOME VERBS — verbs that assert a result:
   — transformed, changed, resolved, ended, began, initiated, launched, concluded
   → Outcomes are not events. If an event ended something, "departed" or
     "exited" captures the physical act. The ending is a consequence, not an action.

5. AGGREGATION VERBS — verbs that collapse multiple events:
   — repeatedly_addressed, consistently_refused, frequently_missed
   → Each occurrence is a discrete event. Aggregation is prohibited.
   → Temporal compression violates the atomicity rule.

VIII. TENSE CONSISTENCY GUARANTEE

All action tokens must produce identical canonical output regardless of
source material tense.

If source material reads "he refused practice" → action: refused
If source material reads "she will decline" → action: declined (not declined_future)
If source material reads "they are assembling" → action: assembled

Tense normalization occurs at extraction, before token assignment.
No tense variant creates a new token.
Tense is not an identity-bearing dimension.

IX. WAS_* TOKEN GOVERNANCE

was_* tokens represent passive-construction events where the actor is the
recipient of an organizational/structural action, not the initiator.

Permitted was_* tokens:
was_removed
was_ejected
was_designated
was_waived
was_signed
was_traded
was_released

Rules:
* was_* tokens imply the actorRole is the recipient of the action, not the
  initiator. The initiating party (e.g., front_office_executive) is typically
  not capturable as actorRole in these events.
* If the initiating party IS the primary actor in the event, use the active
  form and assign the initiating party as actorRole.
  Example: "GM releases player" → actorRole: general_manager | action: was_released
  is WRONG. Use: actorRole: general_manager | action: released (token not yet defined)
  — OR: actorRole: practice_squad_player | action: was_released (patient as actor)
  Assignment depends on the event's structural focal point.
* was_* tokens are exclusively for formally documented organizational actions.
  They are never used for informal events.

X. NULL RULE

action is REQUIRED. action SHALL NOT be null.
If no valid action token can be assigned, the event must be rejected.
Free text in the action field is a contract violation.

XI. LOCK STATEMENT

action participates in CSN_FINGERPRINT_V1.
Errors here produce incorrect canonical IDs and break deterministic deduplication.
No interpretive, causal, sentiment, outcome, or aggregation verbs permitted.
No compound verbs permitted except challenged_authority (semantics locked).
Tense does not participate.
Event-type and claim-type are both valid but must not be conflated.
This contract is locked at v1.0.
Extension requires ACTION_TAXONOMY_CONTRACT v1.1 and ENUM_v1.1.
This contract integrates with:
* EVENT_ENUM_REGISTRY_V1.md
* ACTOR_ROLE_TAXONOMY_CONTRACT.md
* STANDALONE-NARRATIVE-TRANSFORMER-AGENT.md (SANTA)
* CANONICAL-INTEGRITY-VALIDATOR.md (CIV)
* NARRATIVE-EVENT-SEED-STRUCTURAL-CONTRACT.md
