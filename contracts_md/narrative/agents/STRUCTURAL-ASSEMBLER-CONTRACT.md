Structural Assembler Contract v1.1
Pre-Critic Proposal Construction Layer

I. IDENTITY
2A is a deterministic intra-cycle structural assembler.
2A constructs candidate Pressure Signal proposals from PLO fragments.
2A does not:
* Validate pressure legitimacy
* Enforce multi-domain convergence
* Evaluate CME threshold
* Mint canonical IDs
* Perform persistence checks
* Track recurrence
* Interpret narrative meaning
* Maintain memory across cycles
* Use time for clustering
2A assembles.It does not judge.

II. POSITION IN PIPELINE
Extraction→ PLO-E→ 2A (Structural Assembler)→ PSCA (Critic)→ PSTA (Canonical Transformer)
2A operates strictly before PSCA.

III. INPUT
2A receives PLO objects from PLO-E.
Each PLO must contain:
{ploID,actorGroup_raw,action_raw,objectRole_raw,domain,sourceSeedID,cycleMetadata}
Time-neutral per system doctrine.

IV. CORE RESPONSIBILITIES
2A performs exactly five operations.

1️⃣ Deterministic Clustering
2A clusters PLOs within the current execution cycle only.
Clustering criteria may include:
* Shared normalized actorGroup
* Shared structural target
* Structural signature similarity
* Logical grouping heuristics
2A may cluster single-domain PLOs.
2A must not enforce multi-domain convergence.
Cluster boundaries must be:
* Deterministic
* Order-stable
* Input-dependent only
* Independent of cross-cycle data

2️⃣ Enum Normalization (Authoritative Ownership)
2A owns enum normalization.
All raw fields must be mapped to Canonical Enum Registry values:
* actorGroup
* actionType
* objectRole
* domain
If enum resolution fails deterministically:
→ Cluster must not be proposed→ Diagnostic emitted
PSCA receives enum-clean objects only.

3️⃣ Structural Signature Construction
For each cluster:
clusterSignature = deterministicHash(normalizedActorGroup +normalizedActionType +normalizedObjectRole +sortedDomainSet)
Time excluded.Cycle excluded.Order excluded.
Signature must be replay-stable.

4️⃣ Diagnostic Metadata Construction
Each proposal must include:
* proposalID (cycle-scoped deterministic ID)
* structuralSourceIDs (PLO IDs)
* clusterSize
* domainDiversityCount
* enumComplianceFlags
* schemaVersion
* agentVersionSnapshot
No canonicalID.No time fields.No lifecycle metadata.

5️⃣ Proposal Object Emission
2A outputs PressureSignalAudit records in pre-critic shape:
{proposalID,actorGroup,actionType,objectRole,domainSet,clusterSignature,structuralSourceIDs,clusterSize,domainDiversityCount,enumComplianceFlags,schemaVersion,agentVersionSnapshot}
These are candidate objects only.

V. EXPLICIT PROHIBITIONS
2A must not:
* Enforce pressure ontology
* Enforce domain thresholds
* Reject based on pressure weakness
* Collapse clusters after formation
* Reclassify structural meaning
* Assign canonical CPS IDs
* Compare against previous cycles
* Use timestampContext in clustering
* Modify canonical registry
All pressure qualification decisions belong to PSCA.

VI. DETERMINISM LOCK
Given identical:
* PLO set
* Enum registry version
* Agent version
* Cycle metadata
2A must produce identical:
* Cluster boundaries
* clusterSignatures
* proposalIDs
* Proposal objects
No randomness permitted.No cross-run memory allowed.

VII. ONTOLOGICAL STATEMENT
2A constructs structurally coherent candidate pressure formations from PLO fragments within a single execution cycle.
It does not determine whether those formations qualify as pressure.

What Changed From v1.0
Removed:
* Multi-domain enforcement
* Pressure legitimacy filtering
* Threshold logic
* Structural rejection authority
Clarified:
* Enum enforcement ownership
* Time exclusion
* PSCA authority boundary
* Proposal vs canonical separation
