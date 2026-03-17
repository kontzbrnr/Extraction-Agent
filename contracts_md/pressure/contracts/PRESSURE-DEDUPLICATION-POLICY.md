PRESSURE DEDUPLICATION POLICY
Canonical CPS Identity & Collapse Rules — v1.0

I. PURPOSE
Defines deterministic duplicate handling for Canonical Pressure Signal (CPS) objects.
Ensures:
* No intra-cycle canonical duplication
* No cross-cycle collapse
* Deterministic replay stability
* Canonical immutability preservation

II. DEDUP SCOPE
1️⃣ Intra-Cycle Deduplication
Within a single orchestrator cycle and identical timestampContext:
If two or more PSCA-PASS proposals share identical Structural Identity Key:
They SHALL collapse into a single CPS object.
Collapse occurs before canonical ID minting.
Only one canonicalCpsID is minted.
All proposalIDs remain logged for PQG traceability.

2️⃣ Cross-Cycle Handling
If structural identity matches but timestampContext differs:
They SHALL produce distinct CPS objects.
No cross-cycle deduplication is permitted.
Time participates in identity.

III. STRUCTURAL IDENTITY KEY
Two proposals are considered identical if and only if:
* actorGroup identical
* actionType identical
* objectRole identical
* domainSet identical (order-insensitive)
* timestampContext identical
Diagnostic fields excluded from identity:
* structuralSourceIDs
* clusterSize
* domainDiversityCount
* enumComplianceFlags
* proposalID
* agentVersionSnapshot
Structural Identity Key = deterministic hash of the five identity fields.

IV. SOURCE TOLERANCE RULE
Differences in structuralSourceIDs SHALL NOT create distinct canonical objects.
Canonical identity models structural condition only.
Evidence aggregation is diagnostic, not ontological.

V. DEDUP ENFORCEMENT LOCATION
Deduplication SHALL occur in PSTA prior to canonical ID minting.
PSCA does not perform deduplication.
PQG may detect post-run anomalies but shall not rewrite canonical objects.

VI. CANONICAL ID MINTING
canonicalCpsID SHALL be minted only after:
* PSCA PASS
* Dedup collapse resolution
Canonical ID must derive from Structural Identity Key only.
ID must not depend on proposal ordering.

VII. DETERMINISM GUARANTEE
Given identical:
* Input material
* Clustering behavior
* Time binding
* Enum registry
* Contract versions
Deduplication outcome SHALL be identical across replays.

Phase 1.2 is now structurally consistent with:
* Phase 1.1 lifecycle
* Time binding hybrid model
* Immutable canonical policy
* ID namespace integrity


