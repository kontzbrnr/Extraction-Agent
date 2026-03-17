# CANONICAL PRESSURE OBJECT — FIELD INVENTORY
## Micro-Project 0.2 Extraction Summary
**Extracted from:**
1. PRESSURE-CAPABLE-SEED-STRUCTURAL-CONTRACT.md
2. PRESSURE-SIGNAL-AUDIT-RECORD.md (PSAR v1.0)
3. PRESSURE-LIFECYCLE-CONTRACT.md
4. PRESSURE-SIGNAL-TRANSFORMATION-AGENT.md (PSTA v4)

---

## FINGERPRINT-PARTICIPATING FIELDS
*(CPS_FINGERPRINT_V1 — as defined in PSTA v4, Section XIII-2)*

| Field Name | Type | Required/Optional | Fallback Token | Source |
|---|---|---|---|---|
| `schemaVersion` | string | REQUIRED | (PSTA declares: "CPS-1.0") | PSTA v4 (IV) |
| `signalClass` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `environment` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `pressureSignalDomain` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `pressureVector` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `signalPolarity` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `observationSource` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `castRequirement` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `tier` | integer | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `observation` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |
| `sourceSeed` | string | REQUIRED | empty string (null → "") | PSTA v4 (V, XIII-2) |

---

## NON-FINGERPRINT STRUCTURAL FIELDS
*(These are canonical object fields that do NOT participate in fingerprint)*

| Field Name | Type | Required/Optional | Fallback Token | Source |
|---|---|---|---|---|
| `canonicalId` | string (CPS_<sha256hex>) | REQUIRED | computed; no fallback | PSTA v4 (IV, V) |
| `enumRegistryVersion` | string | REQUIRED (per lifecycle) | (referenced but minting deferred to PSTA) | PSTA v4 (inherited) |
| `fingerprintVersion` | string | REQUIRED (immutable field) | "CPS_FINGERPRINT_V1" | PSTA v4 (XIII); Lifecycle (III) |

---

## EXPLICITLY EXCLUDED FIELDS
*(Must NOT appear in canonical object per Lifecycle & PSTA contracts)*

| Field Name | Reason | Source |
|---|---|---|
| `timestampContext` | Time-neutral identity rule; NOT in fingerprint; stored externally | PSTA v4 (VI); Lifecycle (III) |
| `timestampBucket` | Time-neutral identity rule; NOT in fingerprint | PSTA v4 (VI); Lifecycle (III) |
| `cycleID` | Time-neutral identity rule; NOT in fingerprint | Lifecycle (III) |
| `season` | Time-neutral identity rule; NOT in fingerprint | Lifecycle (III) |
| `phase` | Time-neutral identity rule; NOT in fingerprint | Lifecycle (III) |
| `week` | Time-neutral identity rule; NOT in fingerprint | Lifecycle (III) |
| `runIndex` | Time-neutral identity rule; NOT in fingerprint | Lifecycle (III) |
| `executionTimestamp` | Time-neutral identity rule; NOT in fingerprint | PSTA v4 (VI) |
| `processingTime` | Time-neutral identity rule; NOT in fingerprint | PSTA v4 (VI) |
| `proposalID` | Pre-critic metadata; NOT part of canonical object; stored in PSAR only | PSAR (V); Lifecycle (III) |
| `clusterSignature` | Diagnostic metadata; NOT part of canonical object; stored in PSAR only | PSAR (VII-B) |
| `clusterSize` | Diagnostic metadata; NOT part of canonical object; stored in PSAR only | PSAR (VIII) |
| `domainDiversityCount` | Diagnostic metadata; NOT part of canonical object; stored in PSAR only | PSAR (VIII) |
| `structuralSourceIDs` | Diagnostic metadata; NOT part of canonical object; stored in PSAR only | PSAR (VIII) |
| `enumComplianceFlags` | Diagnostic metadata; NOT part of canonical object; stored in PSAR only | PSAR (VIII) |
| `criticStatus` | Verdict metadata; NOT part of canonical object; stored in PSAR post-critic | PSAR (IX) |
| `failureStage` | Verdict metadata; NOT part of canonical object; stored in PSAR post-critic | PSAR (IX) |
| `reasonCode` | Verdict metadata; NOT part of canonical object; stored in PSAR post-critic | PSAR (IX) |
| `collapseDirective` | Verdict metadata; NOT part of canonical object; stored in PSAR post-critic | PSAR (IX) |
| `reclassificationTarget` | Verdict metadata; NOT part of canonical object; stored in PSAR post-critic | PSAR (IX) |
| `agentVersionSnapshot` | Metadata; NOT part of canonical object; stored in PSAR | PSAR (VI) |
| `firstSeen` | Lifecycle metadata; explicitly prohibited | Lifecycle (X) |
| `lastSeen` | Lifecycle metadata; explicitly prohibited | Lifecycle (X) |
| `observedCycles` | Lifecycle metadata; explicitly prohibited | Lifecycle (X) |
| `recurrenceCount` | Lifecycle metadata; explicitly prohibited | Lifecycle (X) |
| `decayScore` | Lifecycle metadata; explicitly prohibited | Lifecycle (X) |
| `lifecycleStatus` | Lifecycle metadata; explicitly prohibited | Lifecycle (X) |
| `activity flags` | Lifecycle metadata; explicitly prohibited | Lifecycle (X) |
| `continuation indicators` | Lifecycle metadata; explicitly prohibited | Lifecycle (X) |
| `ingestion batch` | Fingerprint exclusion rule | PSTA v4 (VI) |
| `ordering position` | Fingerprint exclusion rule; no order-dependent identity | PSTA v4 (VI) |
| `registry counters` | Stateless guarantee; no global state | PSTA v4 (VI) |

---

## TIME-NEUTRALITY PROHIBITIONS
*(Fields explicitly prohibited due to temporal nature or stateful logic)*

**Hard Prohibition:**
- Any field containing temporal context (week, season, cycle, phase, timestamp, execution time, processing time)
- Any field dependent on run order or sequential positioning
- Any counter, state flag, or recurrence tracker
- Any lifecycle or decay simulation field

**Reason:** Canonical CPS objects are time-neutral structural types. Temporal modeling occurs externally via Cycle Association Log + Narrative Engine.

**Contract Source:** 
- PSTA v4 (VI, XIII-3)
- Lifecycle v2.0 (III — Time-Neutral Structural Identity; VIII — Decay Ownership Boundary; X — Lifecycle Metadata Prohibition)

---

## CONFLICTS OR AMBIGUITIES FOUND

### ✅ NONE DETECTED

All four contracts are internally consistent on the following critical points:

1. **Canonical Object Shape** — Defined uniformly in PSTA v4 (Section IV) as the authoritative schema:
   ```
   {
     "schemaVersion": "CPS-1.0",
     "canonicalId": "CPS_<sha256hex>",
     "sourceSeed": "<exact seed title>",
     "signalClass": "<signal_class>",
     "environment": "<environment>",
     "pressureSignalDomain": "<pressure_signal_domain>",
     "pressureVector": "<pressure_vector>",
     "signalPolarity": "<signal_polarity>",
     "observationSource": "<observation_source>",
     "castRequirement": "<cast_requirement>",
     "tier": <1|2|3>,
     "observation": "<exact observation string>"
   }
   ```

2. **Fingerprint Composition** — PSTA v4 Section XIII-2 is the sole definition authority.
   - Lifecycle and PSAR contracts defer to PSTA v4 for fingerprint logic.
   - No parallel fingerprint definitions exist.

3. **Time-Neutrality** — Uniformly enforced:
   - PSAR v1.0 prohibits time fields (Section XII).
   - Lifecycle v2.0 codifies time-neutral identity (Section III).
   - PSTA v4 excludes temporal data from fingerprint (Section VI, XIII-3).

4. **Immutability** — Consistently stated:
   - PSAR objects are pre-canonical and subject to verdict fields.
   - Canonical CPS objects are write-once, read-only (Lifecycle IV).
   - PSTA is the sole minting authority (Lifecycle Section V-A, PSTA Section XIII-1).

5. **Deduplication** — Single authority:
   - PSTA performs dedup at canonicalization boundary (Lifecycle V-A, PSTA Section XIV-3).
   - Orchestrator performs no dedup or identity logic.
   - Registry is passive storage.

6. **Enum Governance** — Dual registry architecture locked:
   - Pressure Enum Registry is separate from Narrative Event Enum Registry.
   - No cross-lane enum sharing permitted.
   - Lifecycle Contract v2.0 (Enum Registry Governance Clause).

---

## CANONICAL OBJECT IMMUTABILITY LOCK
*(Summary for schema enforcement)*

The following fields are explicitly designated as immutable post-canonicalization:
- `signalClass`
- `environment`
- `pressureSignalDomain`
- `pressureVector`
- `signalPolarity`
- `castRequirement`
- `tier`
- `fingerprintVersion`
- `schemaVersion`
- `enumRegistryVersion`

**Source:** Lifecycle v2.0, Section IV-2

---

## NORMALIZATION RULES FOR FINGERPRINT
*(As defined in PSTA v4, Section V)*

```
norm(x):
  trim whitespace
  lowercase
  collapse internal whitespace → single underscore
  remove disallowed punctuation
  if null → empty string ("")
```

**Concatenation Order (exact):**
```
CPS-1.0 |
signalClass_norm |
environment_norm |
pressureSignalDomain_norm |
pressureVector_norm |
signalPolarity_norm |
observationSource_norm |
castRequirement_norm |
tier_norm |
observation_norm |
sourceSeed_norm
```

**Hash:** SHA-256 → lowercase hex

**ID Format:** `CPS_<sha256hex>`

---

## CANONICAL ID MINT AUTHORITY
*(As defined in PSTA v4, Section XIII-1)*

- **Sole Authority:** PSTA only
- **Timing:** After PSCA PASS
- **Stateless:** No cross-run memory, no global counters, no registry lookups
- **Deterministic:** Identical input → identical canonicalId (bitwise)
- **No Sequential IDs:** Content-derived only; no counter-based identity

---

## NEXT STEPS (DEFERRED TO MICRO-PROJECT 0.2 IMPLEMENTATION)

This inventory is **conflict-free and ready for schema implementation**.

The JSON Schema for `canonical_pressure_signal.schema.json` will:
1. Include all fingerprint-participating fields as required
2. Include non-fingerprint structural fields (`canonicalId`, `enumRegistryVersion`, `fingerprintVersion`)
3. Set `additionalProperties: false`
4. Enforce proper field types (string, integer)
5. Define enum constraints per Pressure Enum Registry (external reference)
6. Include immutability annotations for documentation
7. Exclude all time-based and lifecycle fields entirely

---

**Inventory Status:** ✅ COMPLETE  
**Conflicts:** ✅ NONE  
**Ready for Schema Implementation:** ✅ YES
