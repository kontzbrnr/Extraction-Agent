# CANONICAL NARRATIVE OBJECT — FIELD INVENTORY
## Micro-Project 0.3 Extraction Summary

**Extracted from:**
1. NARRATIVE-EVENT-OBJECT-SCHEMA.md (ANE-1.0 / 2B-EMIT-1.0)
2. NARRATIVE-EVENT-SEED-STRUCTURAL-CONTRACT.md
3. NARRATIVE-LIFECYCLE-CONTRACT.md
4. STANDALONE-NARRATIVE-TRANSFORMER-AGENT.md (SANTA CSN-1.0)

---

## CRITICAL SEMANTIC NOTE

**Two distinct canonical narrative types are defined in contracts:**

1. **CME (Canonical Mainstream Event)** — defined in META contract (not provided in extraction)
2. **CSN (Canonical Standalone Narrative)** — defined in SANTA contract (Section III)

**This inventory captures CSN fields only** (SANTA jurisdiction).
CME fields are outside the scope of provided contracts.

---

## FINGERPRINT-PARTICIPATING FIELDS
*(CSN_FINGERPRINT_V1 — as defined in SANTA v1.0, Section III.1)*

| Field Name | Type | Required/Optional | Fallback Token | Normalization | Participates |
|---|---|---|---|---|---|
| `actorRole` | string | REQUIRED | (normalized: empty string if null) | trim→lowercase→collapse_ws→remove_punct | YES |
| `action` | string | REQUIRED | (normalized: empty string if null) | trim→lowercase→collapse_ws→remove_punct | YES |
| `objectRole` | string | OPTIONAL/NULLABLE | (normalized: empty string if null) | trim→lowercase→collapse_ws→remove_punct | YES |
| `contextRole` | string | OPTIONAL/NULLABLE | (normalized: empty string if null) | trim→lowercase→collapse_ws→remove_punct | YES |
| `subclass` | string | REQUIRED | (normalized: empty string if null) | trim→lowercase→collapse_ws→remove_punct | YES |
| ~~`permanence`~~ | ~~string~~ | **REMOVED** | — | — | **NO — Option B locked. Field does not exist. Fingerprint formula corrected.** |
| `sourceReference` | string | REQUIRED | (normalized: empty string if null) | trim→lowercase→collapse_ws→remove_punct | YES |

**Fingerprint Concatenation Order (corrected — Option B locked):**
```
CSN-1.0 |
actorRole_norm |
action_norm |
objectRole_norm |
contextRole_norm |
subclass_norm |
sourceReference_norm
```
> `permanence_norm` removed. SANTA v1.0 Section III.1 fingerprint formula contained an error.
> `permanence` is not a canonical object field. Ruling: Option B. Locked.

**Hash:** SHA-256 → lowercase hex  
**ID Format:** `CSN_<sha256hex>`

---

## NON-FINGERPRINT STRUCTURAL FIELDS

| Field Name | Type | Required/Optional | Fallback Token | Source |
|---|---|---|---|---|
| `id` | string | REQUIRED | (computed; format: CSN_<sha256hex>) | SANTA v1.0 (III) |
| `eventType` | string | REQUIRED | const: "CSN" | SANTA v1.0 (III) |
| `eventDescription` | string | REQUIRED | (no fallback; required non-empty) | SANTA v1.0 (III) |
| `timestampContext` | string | REQUIRED | (no fallback; required non-empty) | SANTA v1.0 (III) |

**Note:** `eventDescription` and `timestampContext` are structural but **do NOT participate in fingerprinting** (SANTA v1.0, Section III.1 Exclusion Rule).

---

## FIELD ORDERING (DETERMINISTIC SERIALIZATION)
*(Per SANTA v1.0, Section III — "Fields must be Deterministically ordered")*

Canonical CSN object field order:
1. `id`
2. `eventType`
3. `actorRole`
4. `action`
5. `objectRole`
6. `contextRole`
7. `subclass`
8. `eventDescription`
9. `timestampContext`
10. `sourceReference`
11. (permanence — appears in fingerprint but position TBD; inferred from fingerprint formula)

**Authority:** SANTA contract specifies deterministic ordering as requirement; exact positional order not explicitly stated in provided text. Fingerprint order implies concatenation sequence but not canonical object field order.

---

## EXPLICITLY EXCLUDED FIELDS
*(Must NOT appear in canonical CSN object)*

| Field Name | Reason | Source |
|---|---|---|
| `timestampBucket` | Pre-NCA metadata; excluded from canonical objects | NARRATIVE-EVENT-OBJECT-SCHEMA.md (ANE only, not canonical) |
| `eventSeedId` | Pre-classification identity; ANE-1.0 only, not in canonical objects | NARRATIVE-EVENT-OBJECT-SCHEMA.md (KP1) |
| `splitProvenance` | Pre-NCA diagnostic; not part of canonical object | NARRATIVE-EVENT-OBJECT-SCHEMA.md (ANE diagnostics only) |
| `dedup` (pre-canonical) | Diagnostic metadata; stored in ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `agentVersionSnapshot` | Diagnostic metadata; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `registryVersion` | Diagnostic metadata; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `timeRegistryVersion` | Diagnostic metadata; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `fingerprintVersion` | Diagnostic metadata; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `rawActorRole` | Diagnostic raw mapping; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `rawAction` | Diagnostic raw mapping; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `rawObjectRole` | Diagnostic raw mapping; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `rawContextRole` | Diagnostic raw mapping; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `roleMappingFlags` | Diagnostic mapping status; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `rawTimestampContext` | Diagnostic raw mapping; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `timeMappingFlag` | Diagnostic mapping status; part of ANE diagnostics, not canonical | NARRATIVE-EVENT-OBJECT-SCHEMA.md (VI) |
| `cycle` / `cycleID` | Time-based lifecycle metadata; stored externally in Cycle Association Log | NARRATIVE-LIFECYCLE-CONTRACT.md (II, IV) |
| `firstSeen` | Lifecycle metadata; stored externally | NARRATIVE-LIFECYCLE-CONTRACT.md (IX) |
| `lastSeen` | Lifecycle metadata; stored externally | NARRATIVE-LIFECYCLE-CONTRACT.md (IX) |
| `recurrenceCount` | Lifecycle metadata; stored externally | NARRATIVE-LIFECYCLE-CONTRACT.md (IX) |
| `decayScore` | Lifecycle metadata; stored externally | NARRATIVE-LIFECYCLE-CONTRACT.md (IX) |
| `clusterMembership` | External analytics; not part of canonical object | NARRATIVE-LIFECYCLE-CONTRACT.md (IX) |
| Any structural reconfiguration fields | Pressure lane only; cross-lane isolation enforced | NARRATIVE-LIFECYCLE-CONTRACT.md (XI) |
| Any Pressure enum references | Cross-lane enum isolation; prohibited | NARRATIVE-LIFECYCLE-CONTRACT.md (V, XI) |

---

## DISCRETE EVENT ENFORCEMENT RULES

*(Enforced at seed level by NARRATIVE-EVENT-SEED-STRUCTURAL-CONTRACT.md; carry forward to canonical)*

**Atomicity Requirement:**
- MUST originate from a single Atomic Unit (AU)
- MUST represent exactly one ontological component
- MUST NOT contain composite material
- MUST NOT require internal splitting

**Single-Occurrence Rule:**
- Describes exactly one discrete occurrence
- Cannot combine multiple actions
- Cannot aggregate a sequence
- Cannot summarize a trend
- Cannot imply duration

**Prohibited Language / Content:**
- No causal inference: "because", "therefore", "in order to", motive claims
- No escalation language: "signaled", "sparked", "marked the beginning", "historic", "turned the tide", "changed the trajectory", "created tension", "escalated", "led to", "resulting in"
- No interpretation or meaning implication
- No impact claims or trajectory encoding
- No resolution encoding
- No structural reconfiguration analysis
- No media framing or rhetorical positioning
- No proper nouns (identity abstraction required)

**Structural Format (Seed level):**
- SEED: [Event Title]
- Event Description: [Single neutral declarative sentence]
- Optional: Time Marker (if directly observable), Location (if directly observable)

**Inheritance to Canonical:**
- Canonical `eventDescription` must be neutral, factual, declarative
- Canonical object preserves atomicity constraint (ANE-1.0 pre-NCA; CSN post-canonicalization)
- SANTA applies no reclassification; authority remains with NCA

---

## CONFLICTS OR AMBIGUITIES FOUND

### ✅ AMBIGUITY RESOLVED — Option B Locked

**`permanence` Field Status: RESOLVED**

| Contract | Claim |
|---|---|
| SANTA v1.0 (III.1) | `permanence_norm` appeared in fingerprint formula — **formula error, now corrected** |
| SANTA v1.0 (III) | `permanence` not listed in canonical object schema — **correct, field does not exist** |
| SANTA v1.0 (IV) | "All CSN canonical objects are permanently archived" — **system policy, not a field** |

**Ruling:** Option B. `permanence` is not a canonical object field. SANTA v1.0 Section III.1 fingerprint formula contained an error. `permanence_norm` has been removed from the CSN fingerprint concatenation sequence. The corrected sequence has six participating fields: actorRole, action, objectRole, contextRole, subclass, sourceReference.

---

### ALIGNMENT WITH NARRATIVE-LIFECYCLE-CONTRACT

**Time Participation Rule (Section IV):**
- "Narrative identity MAY include: timestampContext"
- `timestampContext` IS present in canonical CSN object (SANTA Section III)
- BUT `timestampContext` is explicitly EXCLUDED from fingerprinting (SANTA Section III.1)

**Reconciliation:** 
✅ This is consistent and intentional. `timestampContext` participates in canonical object (for archival/query purposes) but NOT in identity derivation. This preserves time-neutral deduplication across identical event types in different time windows.

---

### ALIGNMENT WITH ANE (PRE-NCA) vs CSN (POST-CANONICAL)

**ANE-1.0 (2B Emission) includes fields:**
- `timestampBucket` (excluded from canonical CSN)
- `eventSeedId` (becomes `id` / `CSN_<hash>` in canonical)
- Diagnostics envelope (external to canonical object)

**CSN-1.0 (SANTA Output) includes:**
- `id` (canonical identifier)
- `eventType` (const: "CSN")
- Same core event fields: actorRole, action, objectRole, contextRole, eventDescription, timestampContext, sourceReference
- Added field: `subclass` (from NCA classification)

**Transition is clean:** ANE is pre-NCA staging object; CSN is canonical archived object. No conflict.

---

## ENUM GOVERNANCE

| Registry | Lane | Governs | Authority | Source |
|---|---|---|---|---|
| EVENT_ENUM_REGISTRY_V1 | Narrative | actorRole, action, objectRole, contextRole | 2B (Narrative-Structural-Assembler) | NARRATIVE-EVENT-OBJECT-SCHEMA.md (KP2) |
| TIME_BUCKET_REGISTRY_V1 | Narrative | timestampBucket (ANE only, not canonical) | 2B | NARRATIVE-EVENT-OBJECT-SCHEMA.md (KP3) |
| Subclass Taxonomy | Narrative | subclass | NCA (classifier); SANTA validates only | STANDALONE-NARRATIVE-TRANSFORMER-AGENT.md (V) |

**Cross-Lane Isolation (enforced):**
- Narrative enums SHALL NOT reuse Pressure enums
- Pressure enums SHALL NOT influence Narrative identity
- Cross-lane enum reference is prohibited

---

## CANONICAL ID MINT AUTHORITY

- **Sole Authority:** 2B (Narrative-Structural-Assembler) for ANE_FINGERPRINT_V1 (eventSeedId)
- **Canonical Transformation:** SANTA for CSN_FINGERPRINT_V1 (canonicalId)
- **Timing:** ANE eventSeedId minted by 2B at emission; CSN id minted by SANTA at canonicalization
- **Stateless:** No cross-run memory; no registry lookups; deterministic only
- **Determinism:** Identical input → bitwise identical output (given identical registry versions)

---

## NORMALIZATION RECIPE *(Pre-fingerprint)*

```
For each fingerprint-participating field:
  trim whitespace
  lowercase
  collapse internal whitespace → single underscore
  remove disallowed punctuation
  if null → empty string ("")
```

**Applied to:** actorRole, action, objectRole, contextRole, subclass, sourceReference
> `permanence` removed per Option B ruling.

**NOT applied to (excluded from fingerprint):**
- eventDescription (semantic drift risk)
- timestampContext (excluded explicitly)
- Any non-fingerprint fields

---

## STATUS

**Inventory Status:** ✅ COMPLETE
**Conflicts:** ✅ NONE — Option B ruling eliminates the only ambiguity
**Ready for Schema Implementation:** ✅ YES

**Corrected fingerprint field count:** 6 (actorRole, action, objectRole, contextRole, subclass, sourceReference)
**`permanence` disposition:** Not a field. Not in fingerprint. Not in canonical object. Closed.
