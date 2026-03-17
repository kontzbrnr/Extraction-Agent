CANONICAL ENUM REGISTRY — v1.0
Applies to:
* signal_class
* environment
* pressure_signal_domain
* pressure_vector
* signal_polarity
* observation_source
* cast_requirement
* tier

1️⃣ signal_class
Purpose: What structural type of surface this signal represents.
Allowed values:

ambient_framing
observed_behavior
procedural_change
environmental_cue
structural_condition
transactional_event
Notes:
* structural_condition handles roster architecture, contract structure, authority layering.
* transactional_event covers formal signings/draft selections when treated as pressure signals (not media events).
No further expansion without ontology review.

2️⃣ environment
Purpose: Where the pressure is situated.
Allowed values:

organization
locker_room
practice
stadium
team_travel
league
medical
draft_room
front_office
New Additions:
* league (supra-franchise layer)
* medical (procedural medical context)
* draft_room (controlled selection environment)
* front_office (governance interior layer)
Keep environment spatial/institutional — not emotional.

3️⃣ pressure_signal_domain
Purpose: Conceptual dimension of tension.
Allowed values:

structural_configuration
authority_distribution
control_autonomy
standards_evaluation
culture_cohesion
preparation_installation
timing_horizon
resource_allocation
redundancy_fragility
access_information
public_legibility
environmental_constraint
availability_status
compliance_regulation
Critical Principle:
Domains must be:
* Non-overlapping
* Structural
* Not evaluative
No synonyms allowed.No duplication under different wording.

4️⃣ pressure_vector
Purpose: Directional surface of pressure expression.
Allowed values:

visibility
evaluation
expectation
exposure
volatility
constraint
reliability
authority
compliance
availability
Important:
Vector is how pressure manifests,not what it “means.”
Keep this list tight.No more than 10–12 long-term.

5️⃣ signal_polarity
Purpose: Structural polarity only — not narrative judgment.
Allowed values:

positive
negative
ambiguous
compressive
expansive
neutral
Definitions:
* compressive = narrowing role, restriction, reduced autonomy
* expansive = increased authority, widened role
* ambiguous = unclear directional valence
* neutral = operational fact without directional tilt

6️⃣ observation_source
Purpose: Origin of observation.
Allowed values:

user_provided
internal_observer
environmental
official_record
league_record
media_record
transaction_log
medical_report
Do not collapse these.Source fidelity matters later.

7️⃣ cast_requirement
Purpose: Minimum entity type required.
Allowed values:

individual_player
position_group
coach
front_office
ownership
franchise
league
group
unspecified
No hybrids. One primary anchor only.

8️⃣ tier
Purpose: System weight class.
Allowed values:

1
2
3
Suggested internal meaning:
* Tier 1 = Local structural signal
* Tier 2 = Multi-role influence surface
* Tier 3 = Cross-domain destabilizer
Keep numeric for scalability.

🧱 Hard Lock Rule
From this point forward:
• No enum may be added without registry revision• No synonyms allowed• No domain duplication• No capitalization drift• All enums snake_case
This is now your ontology backbone.


🔒 ENUM REGISTRY GOVERNANCE CLAUSE
I. Dual Registry Architecture Lock
The system maintains separate enum registries per lane:
* Pressure Enum Registry
* Narrative Event Enum Registry
No enum namespace sharing is permitted across lanes.
Enums defined in one lane SHALL NOT be reused in another lane.
Cross-lane enum reference constitutes contract violation.

II. Fingerprint Participation Rule
If enumRegistryVersion participates in CPS_FINGERPRINT_V1 (as defined in PSTA v4):
Then any modification to enum registry that affects fingerprint-participating fields SHALL:
1. Increment enumRegistryVersion
2. Increment fingerprintVersion
3. Require replay determinism validation
Replay validation SHALL confirm:
* Canonical registry stability for prior version
* Deterministic identity under new version

III. Identity Sensitivity Clause
Enum changes that affect:
* Normalization output
* Enum label canonicalization
* Structural identity key fields
* Field mapping logic
Are identity-affecting changes.
Identity-affecting enum changes SHALL NOT occur silently.

IV. Non-Identity Enum Changes
Enum changes that do NOT affect fingerprint-participating fields (e.g., documentation fields, non-participating categories) MAY increment enumRegistryVersion without fingerprintVersion increment, provided:
* Identity derivation remains unchanged
* Replay determinism remains intact

V. Governance Boundary
Only PSTA v4 defines fingerprint composition.
Enum registry governance may not modify fingerprint structure independently.
If conflict arises, fingerprintVersion increment is mandatory.

