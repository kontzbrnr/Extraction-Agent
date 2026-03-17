SUBCLASS RULEBOOK JURISDICTION CONTRACT
NCA Taxonomy Authority — v1.0

I. PURPOSE
Defines jurisdiction and governance of subclass taxonomy.
Prevents:
* Cross-agent subclass logic duplication
* Silent rule drift
* Reclassification mutation
* Taxonomy fragmentation

II. TAXONOMY AUTHORITY
Subclass taxonomy SHALL reside exclusively within the NCA contract.
No other agent may:
* Define subclass criteria
* Modify subclass logic
* Override subclass decision
* Introduce subclass reinterpretation

III. DOWNSTREAM TRUST RULE
SANTA and META SHALL:
* Accept NCA subclass assignment as authoritative
* Validate schema compliance only
* Not re-evaluate subclass logic
Subclass interpretation authority is non-transferable.

IV. VERSIONING
NCA contract SHALL define:
* subclassTaxonomyVersion
* subclassRuleLogicVersion
Canonical objects SHALL store:
* subclass
* subclassTaxonomyVersion
* subclassRuleLogicVersion
Version fields SHALL NOT participate in ID derivation.

V. IMMUTABILITY
Subclass assignment is immutable post-canonicalization.
No retroactive reclassification permitted.
Taxonomy updates affect future runs only.

VI. GOVERNANCE
PQG may:
* Audit subclass distribution
* Detect classification anomalies
* Recommend taxonomy revisions
PQG may not:
* Rewrite canonical subclass
* Override NCA logic

VII. LOCK STATEMENT
Subclass taxonomy authority resides exclusively in NCA.
No agent outside NCA may interpret, modify, or override subclass logic.
