# Execution Roadmap

## contentlib-docs: From Contract-Complete to Execution-Complete

**Date:** March 16, 2026

---

## Premise

This roadmap is built on a single observation: the system's modules exist and its contracts are thorough, but the sequencing layer that connects them does not yet function. The problem is not "what to build" but "what to wire, in what order, with what proof of correctness."

Every phase below targets one thing: reducing the gap between what the contracts specify and what the code enforces at runtime. Each phase produces a testable artifact — not just code, but evidence that the code does what the contract says it must.

---

## Current State (Verified)

| Layer | Status | Evidence |
|-------|--------|----------|
| Harvest pipeline | Working | Packets exist in shared-corpus/ |
| Intake validation | Working | Rejection logs produced |
| Extraction agents (individual) | Implemented | PSTA, CIV, routing_gate, extraction_agent all have code |
| Extraction Orchestrator V2 | Implemented | 382-line TS orchestrator with Python bridge |
| Orchestrator Step 3 (canonical pipeline) | **Stub** | `_run_canonical_pipeline()` is a `pass` statement |
| NTI extraction call | **Missing** | `runExtraction.ts` does not exist |
| ANE constructor | **Skeletal** | Broken imports, no KP lock enforcement |
| CIV Check 6 (version snapshot) | **Stub** | Returns `(True, None)` unconditionally |
| Python dependencies | **Incomplete** | requirements.txt has only FastAPI/uvicorn |
| Artifact gate | **Bypassed** | Always returns "accept" |

---

## Phase 0: Foundation (Do This First)

**Goal:** Make the codebase runnable before touching any pipeline logic.

### 0.1 — Fix Python dependency manifest

The current `requirements.txt` lists only FastAPI and uvicorn. The agents import `jsonschema` (CIV schema validation), use hashlib (PSTA fingerprinting), and reference dataclass structures that need typing extensions on older Python versions.

**Action:** Audit every Python import across `engines/research-agent/` and `engines/research_engine/`. Produce a complete `requirements.txt` (or `pyproject.toml`) that includes all runtime and test dependencies. Pin versions.

**Verification:** `pip install -r requirements.txt && python -m pytest engines/research-agent/tests/ --collect-only` succeeds with zero import errors.

### 0.2 — Resolve directory ambiguity

Four directory variants exist: `research-agent` / `research_agent` and `research-engine` / `research_engine`. The hyphenated versions contain the real code. The underscored versions contain only `__init__.py` files.

**Action:** Determine whether the underscore variants are Python package shims (needed for `import engines.research_agent.agents.civ.civ`). If so, document this explicitly. If not, remove them. The Extraction Orchestrator V2 imports via `engines.research_agent.agents.pressure.psta` — this path must resolve.

**Verification:** From the project root, `python -c "from engines.research_agent.agents.pressure.psta import enforce_psta"` succeeds.

### 0.3 — Fix ANE constructor imports

`ane_constructor.py` line 8 uses `from narrative.ane_id_format import validate_aneseed_id` — a relative import that will fail.

**Action:** Fix to absolute import path consistent with the project's import convention.

**Verification:** `python -c "from engines.research_agent.agents.narrative.ane_constructor import build_ane_object"` succeeds.

### 0.4 — Run existing test suite

108 test files exist but it's unclear if they pass.

**Action:** Run the full test suite. Record which tests pass, fail, or error. Do not fix anything yet — just establish the baseline.

**Verification:** A test report with pass/fail/error counts for every test file.

---

## Phase 1: Wire the Sequencing Layer

**Goal:** Make data flow from a validated packet through extraction and canonicalization in a single invocation, producing a canonical object in the registry.

This is the critical phase. Everything else is refinement.

### 1.1 — Create `runExtraction.ts`

The NTI CLI calls `await runExtraction(ntiDoc)` on line 27 of `runNtiFromSharedCorpus.ts`, importing from `../extraction/runExtraction` — a module that does not exist.

**Action:** Create `src/extraction/runExtraction.ts`. This module must accept an `NtiSourceDocument`, invoke the Extraction Orchestrator V2, and return the result. It is a thin adapter: receive NTI document, call `extractionOrchestratorV2.runExtractionPipeline()`, return the result.

**Verification:** `npm run nti -- 2000-2001` processes at least one packet through the full extraction pipeline (REC production through PSTA/SANTA output) without crashing. Console output shows stage-by-stage results.

### 1.2 — Wire orchestrator Step 3 to extraction agents

`_run_canonical_pipeline()` in `orchestrator.py` (lines 356-391) is a `pass` statement. The docstring documents the intended stage order. The commit wrapper (`_commit_canonical_object()`, lines 394-527) is already implemented and calls CIV + registry append.

**Action:** Implement `_run_canonical_pipeline()`. The function receives a `batch_id`, `season`, and `collector`. It must:

1. Load unprocessed source packets from the season corpus (or receive them from the batch collector).
2. For each packet, invoke the extraction agent adapter chain: Extraction → GSD → Classification → (Pressure Lane OR Narrative Lane) → CIV → Registry Commit.
3. Use the existing agent registry (`agent_registry.py`) and adapters (`extraction_adapter.py`, `classification_adapter.py`, `pressure_adapter.py`, `narrative_adapter.py`, `civ_adapter.py`).
4. Feed results to the existing `_commit_canonical_object()` function.

**Decision required from system owner:** Should Step 3 call Python agents natively (using the adapter pattern already in `research_engine/`), or should it invoke the TypeScript Extraction Orchestrator V2 via subprocess? The V2 orchestrator is the more complete implementation, but calling TypeScript from the Python orchestrator adds a language-crossing subprocess layer. The cleaner path is probably native Python using the adapters, but this means the V2 orchestrator becomes a parallel implementation rather than the canonical one.

**Verification:** `POST /run` via the FastAPI bridge produces at least one canonical object in `canonical_objects.json`.

### 1.3 — Validate the commit path end-to-end

The commit path (`_commit_canonical_object()`) calls CPS dedup, then CIV, then registry append. This path exists but has never received real data from Step 3.

**Action:** Write an integration test that:
1. Constructs a synthetic but schema-valid CPS object.
2. Passes it through `_commit_canonical_object()`.
3. Asserts: CIV passes, object appears in `canonical_objects.json`, duplicate submission is rejected.

**Verification:** Integration test passes. A second submission of the same object produces a dedup rejection.

---

## Phase 2: Prove Invariant Enforcement

**Goal:** For each critical contract invariant, produce a test that proves the code enforces it. This is the phase the builder's critique identified as most important.

### 2.1 — Pressure lane invariant proof

**Contract claim:** PSTA is the sole mint authority for CPS canonical IDs. No other module may derive, assign, or override a CPS ID.

**What to prove:**
- `cps_id_format.py` is the only module that contains the CPS ID regex pattern.
- `psta.py` is the only module that calls `derive_cps_fingerprint()`.
- `cps_constructor.py` receives a pre-minted ID and validates format but does not derive.
- No other code path writes to the `canonicalId` field of a CPS object.

**Action:** Write a test (or static analysis script) that:
1. Greps the codebase for all calls to `derive_cps_fingerprint` — asserts exactly one call site (in `psta.py`).
2. Greps for all assignments to `canonicalId` — asserts only `cps_constructor.py`.
3. Greps for the CPS ID regex pattern — asserts only `cps_id_format.py`.

**Verification:** The test passes. Any future code that violates mint authority will break this test.

### 2.2 — Narrative lane invariant proof

**Contract claim:** ANE objects use a KP1/KP2/KP3 lock mechanism for identity integrity.

**Current state:** `ane_constructor.py` is skeletal (43 lines) and does not implement KP lock enforcement. It accepts a pre-computed `event_seed_id` without validating its derivation.

**Action:** This is an implementation gap, not just a test gap. The builder must:
1. Implement KP1/KP2/KP3 validation in `ane_constructor.py` (verify that the seed ID was derived from the correct keypoints).
2. Write tests proving: an ANE object with a mismatched seed ID is rejected; an ANE object with missing keypoints is rejected; only the designated narrative mint module can produce seed IDs.

**Verification:** ANE constructor rejects malformed seed IDs. Codebase grep confirms single mint authority for narrative IDs.

### 2.3 — CIV gating proof

**Contract claim:** No canonical object reaches the registry without passing CIV.

**Current state:** The orchestrator calls CIV at line 478 before calling registry append at line 488. This is correct. But is there any other code path that calls `registry_writer.append_canonical_object()` without CIV?

**Action:** Write a test that:
1. Greps for all calls to `append_canonical_object` — asserts they are all preceded by CIV validation.
2. Attempts to call `append_canonical_object` with a CIV-failing object directly — asserts the object does not appear in the registry. (This tests the registry writer's own guards, independent of the orchestrator.)

**Current gap:** The registry writer does NOT call CIV internally. It relies on the orchestrator to gate. This means any code that calls `append_canonical_object` directly bypasses CIV. Consider whether the registry writer should include a CIV check as a defensive layer.

**Verification:** Either (a) all call sites are audited and gated, or (b) the registry writer includes its own CIV call.

### 2.4 — Lane contamination proof

**Contract claim:** Pressure-lane fields never appear in narrative-lane objects and vice versa.

**Current state:** CIV Check 7 (lane contamination, lines 477-520 of `civ.py`) is implemented and uses `lane_isolation_audit` field sets.

**Action:** Write a test that constructs a CPS object with a CSN-only field injected, passes it through CIV, and asserts rejection. Repeat for every lane pair.

**Verification:** Cross-lane contamination is rejected in all directions.

### 2.5 — Implement CIV Check 6 (version snapshot)

**Current state:** Returns `(True, None)` unconditionally. Comment says "Phase 11.7."

**Action:** Implement version snapshot validation. The check should verify that `schemaVersion`, `enumVersion`, and `contractVersion` on the canonical object match the values in the cycle snapshot (derived from `version_lock.json`).

**Verification:** A canonical object with a mismatched schema version is rejected by CIV.

---

## Phase 3: Data Quality

**Goal:** Ensure the data entering the pipeline is rich enough to produce meaningful canonical output.

### 3.1 — Metadata extraction from article HTML

**Problem:** All five existing packets have empty `publication` and `author` fields, and `date_published` is "unknown_date". The Brave API returns limited metadata.

**Action:** Add a metadata extraction step to the harvest pipeline, between article fetch and packet construction. Extract: publication name (from `<meta property="og:site_name">` or domain), author (from `<meta name="author">` or byline patterns), and publish date (from `<meta property="article:published_time">`, `<time>` elements, or URL date patterns).

**Verification:** Re-harvest a small batch. At least 70% of packets have non-empty publication and date fields.

### 3.2 — Enable the artifact gate

**Problem:** `artifactGate.ts` always returns "accept". The SHA-256 fingerprint infrastructure exists but is inactive.

**Action:** Implement the gate logic: compute SHA-256 of the article text, check against `artifactRegistry.json`, reject duplicates, append new fingerprints.

**Verification:** Harvesting the same article twice produces one accepted packet and one rejected duplicate.

### 3.3 — Error handling in article fetcher

**Problem:** `articleFetcher.ts` catches all errors silently and returns empty string. No retry logic, no logging.

**Action:** Add: retry with exponential backoff (3 attempts), structured error logging (URL, status code, error type), and distinct handling for 403/429 (rate limit) vs. network errors vs. content errors.

**Verification:** A harvest run produces a log showing fetch success/failure rates with error categories.

---

## Phase 4: Operational Hardening

**Goal:** Make the system safe to run repeatedly without manual intervention.

### 4.1 — Configuration layer

**Problem:** Season window, target source count, and query templates are hardcoded.

**Action:** Create a configuration file (JSON or YAML) that specifies: `seasonWindow`, `targetMaxSources`, `querySetReference` (which query template to use), `outputRoot`, `braveApiKey` (reference to env var, not the value). The harvest controller should load this configuration instead of importing constants.

**Verification:** Changing the config file to a different season produces packets in the correct directory with the correct season tag.

### 4.2 — Rate limiting

**Problem:** No throttling on Brave API calls or article fetches.

**Action:** Add configurable rate limits: Brave API (max N requests per minute), article fetch (max M concurrent, with per-domain cooldown). Implement as a simple token bucket or sleep-based throttle.

**Verification:** Harvest run completes without 429 responses. Log shows inter-request delays.

### 4.3 — Secure API key handling

**Problem:** Brave API key is in plaintext `.env` committed to the repository.

**Action:** Add `.env` to `.gitignore`. Create `.env.example` with placeholder values. Document the required environment variables.

**Verification:** `git status` does not show `.env` as tracked.

### 4.4 — Clean up vestigial directories

**Problem:** `engines/research_agent/` (empty shim), `engines/research_engine/` (duplicate naming), and `Archive/` create confusion.

**Action:** If underscore directories are Python package shims, add a README in each explaining their role. If they are dead code, remove them. Move `Archive/` to a branch or delete it.

**Verification:** A new contributor can identify the authoritative code location for every module without asking.

---

## Phase 5: End-to-End Validation

**Goal:** Run the complete pipeline from harvest to canonical registry and verify the output is correct.

### 5.1 — Golden path test

**Action:** Create a single integration test that:
1. Starts with a known article text (fixture, not fetched live).
2. Constructs a valid source packet.
3. Runs it through intake validation.
4. Passes it through the extraction pipeline.
5. Asserts: at least one canonical object is produced; the object passes CIV; the object appears in the registry; the canonical ID is deterministic (running the same input twice produces the same ID).

**Verification:** Test passes. Re-running with identical input produces identical output (determinism proof).

### 5.2 — Multi-packet batch test

**Action:** Run 5 diverse packets (different publications, different narrative types) through the full pipeline. Verify: pressure-lane and narrative-lane objects are produced; no cross-lane contamination; deduplication works across the batch; the ledger state is consistent after the run.

**Verification:** `canonical_objects.json` contains objects from multiple lanes. `global_state.json` shows correct batch counts.

### 5.3 — Crash recovery test

**Action:** Simulate a crash mid-batch (kill the orchestrator after Step 3 starts but before Step 4 commits). Restart the orchestrator. Verify: the `incompleteBatchFlag` triggers crash recovery; no partial or corrupt objects appear in the registry; the system resumes cleanly.

**Verification:** Post-recovery registry contains only complete, CIV-validated objects.

---

## Phase Sequencing and Dependencies

```
Phase 0 ──────────────────────────────────────────┐
  0.1 Fix dependencies                            │
  0.2 Resolve directory ambiguity                  │
  0.3 Fix ANE imports                              │  NO PIPELINE WORK
  0.4 Run existing tests                           │  UNTIL THIS IS DONE
──────────────────────────────────────────────────-┘
         │
         ▼
Phase 1 ──────────────────────────────────────────┐
  1.1 Create runExtraction.ts ◄── enables NTI CLI │
  1.2 Wire orchestrator Step 3 ◄── enables /run   │  SEQUENCING LAYER
  1.3 Validate commit path                         │
──────────────────────────────────────────────────-┘
         │
         ▼
Phase 2 ──────────────────────────────────────────┐
  2.1 Pressure lane invariant proof                │
  2.2 Narrative lane invariant proof (+ ANE impl)  │  INVARIANT ENFORCEMENT
  2.3 CIV gating proof                             │
  2.4 Lane contamination proof                     │
  2.5 CIV Check 6 implementation                   │
──────────────────────────────────────────────────-┘
         │
         ▼
Phase 3 ──── can run in parallel with Phase 2 ────┐
  3.1 Metadata extraction                          │  DATA QUALITY
  3.2 Enable artifact gate                         │
  3.3 Error handling                               │
──────────────────────────────────────────────────-┘
         │
         ▼
Phase 4 ──── can run in parallel with Phase 2 ────┐
  4.1 Configuration layer                          │  OPERATIONAL HARDENING
  4.2 Rate limiting                                │
  4.3 Secure API key                               │
  4.4 Clean up directories                         │
──────────────────────────────────────────────────-┘
         │
         ▼
Phase 5 ──── requires Phase 1 + Phase 2 ──────────┐
  5.1 Golden path test                             │  END-TO-END VALIDATION
  5.2 Multi-packet batch test                      │
  5.3 Crash recovery test                          │
──────────────────────────────────────────────────-┘
```

**Critical path:** 0 → 1 → 2 → 5. Phases 3 and 4 are important but do not block the critical path.

---

## Decision Points for the System Owner

The roadmap assumes certain architectural choices. Two require your explicit decision before Phase 1 begins:

**Decision 1: Python-native vs. TypeScript bridge for Step 3.**

The Extraction Orchestrator V2 (`extractionOrchestratorV2.ts`, 382 lines) is the most complete extraction implementation. But it's in TypeScript, and the Python orchestrator would need to call it via subprocess. The alternative is to wire Step 3 using the Python adapter pattern already in `research_engine/agent_runtime/adapters/`. This means two implementations of the extraction sequence exist — one must become canonical.

Option A: Step 3 calls V2 via subprocess. Faster to ship (V2 already works). Adds a language boundary in the critical path.

Option B: Step 3 uses Python adapters natively. Cleaner architecture. Requires verifying that every adapter (extraction, classification, pressure, narrative) is as complete as V2's equivalent stages.

**Decision 2: Should the registry writer include defensive CIV gating?**

Currently, CIV is called by the orchestrator before registry append. The registry writer itself does not validate. This means any code that calls `append_canonical_object()` directly — a test, a migration script, a future module — bypasses CIV.

Option A: Keep CIV in the orchestrator only. Simpler. Relies on discipline.

Option B: Add a CIV check inside the registry writer as a defensive layer. Belt and suspenders. Adds a small performance cost (CIV runs twice if the orchestrator also calls it).

---

## What "Done" Looks Like

The system is execution-complete when:

1. `npm run harvest:v1` produces packets with populated metadata.
2. `npm run intake:v1` validates those packets.
3. `npm run nti -- {season}` or `POST /run` processes validated packets through extraction, classification, pressure/narrative lanes, CIV validation, and registry commit — producing canonical objects in `canonical_objects.json`.
4. Every canonical object in the registry has a deterministic, content-derived ID.
5. No canonical object reaches the registry without passing CIV (all 7 checks).
6. Lane isolation is provably enforced (test suite).
7. Crash recovery produces no corrupt or partial objects.
8. Running the same input twice produces the same output (determinism).

When all eight conditions are met, the system transitions from Grade B (partially implemented) to Grade D (production-ready).
