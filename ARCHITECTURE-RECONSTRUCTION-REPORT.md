# Architecture Reconstruction Report

## contentlib-docs

**Audit Date:** March 16, 2026
**Repository Size:** 54,201 files (625 source files excluding dependencies)
**Audit Mode:** Read-only architecture reconstruction

---

## 1. Repository Structure Overview

The repository implements a **deterministic, ledger-driven research pipeline** for harvesting, extracting, classifying, and canonicalizing NFL narrative and pressure-signal data from web sources. It is a hybrid TypeScript/Python system with a Next.js dashboard for operational visibility.

### Top-Level Directory Map

| Directory | Language | Purpose |
|-----------|----------|---------|
| `engines/deep-search/` | TypeScript | Corpus harvesting engine (Brave Search API) |
| `engines/research-agent/` | Python | Core extraction/classification/canonicalization agents (~100+ modules) |
| `engines/research_engine/` | Python | Agent runtime framework with adapters and ledger integration |
| `infra/` | Python | Orchestration runtime (OpenClaw), MCP validator, ingestion bridge |
| `runtime/` | Python | FastAPI server bridging Mission Control to the orchestrator |
| `mission-control/` | TypeScript | Next.js 16 operational dashboard (UI + API routes) |
| `src/nti/` | TypeScript | NTI (Narrative-Temporal Integration) CLI and packet adapter |
| `the-script/` | TypeScript | Hybrid TS/Python extraction orchestrator (V2) |
| `shared-corpus/` | Data | Harvested source packets (JSON metadata + raw text) |
| `contracts_md/` | Markdown | 47 specification contracts governing system behavior |
| `tests/` | Python | Integration tests for the runtime engine |
| `docs/` | Markdown | Field inventories and working notes |

### Key Configuration Files

| File | Role |
|------|------|
| `package.json` | Root workspace: defines four npm scripts (`harvest:v1`, `intake:v1`, `dev`, `nti`) |
| `.env` | Brave API key |
| `artifactRegistry.json` | SHA-256 fingerprint registry for artifact deduplication |
| `milvus.db` | Vector database (28KB, likely embryonic) |

---

## 2. Runtime Entrypoints

The system has **five confirmed runtime entrypoints**, spanning three languages and two execution models (CLI scripts and HTTP servers).

### Entrypoint 1: Corpus Harvester

- **Command:** `npm run harvest:v1`
- **File:** `engines/deep-search/corpus-harvester/runHarvest.ts`
- **Runtime:** Node.js via `npx tsx`
- **Purpose:** Searches Brave Search API with 60 NFL-themed queries, fetches articles, extracts text, builds source packets, writes them to `shared-corpus/`.

### Entrypoint 2: Packet Intake Validator

- **Command:** `npm run intake:v1`
- **File:** `engines/deep-search/agents/ingest/runIntake.ts`
- **Runtime:** Node.js via `npx tsx`
- **Purpose:** Scans `shared-corpus/` for packets, validates structure and metadata completeness, moves rejected packets to a rejection directory with logged reasons.

### Entrypoint 3: NTI CLI

- **Command:** `npm run nti`
- **File:** `src/nti/cli.ts`
- **Runtime:** Node.js via `ts-node`
- **Purpose:** Enumerates validated packets, loads and adapts them to `NtiSourceDocument` format, then invokes extraction (currently a stub).

### Entrypoint 4: FastAPI Bridge Server

- **File:** `runtime/server.py`
- **Runtime:** Python/FastAPI (localhost:8000)
- **Purpose:** REST API bridging Mission Control to the Python orchestrator. Endpoints: `GET /health`, `POST /run`, `GET /runs`, `POST /run-harvest`.

### Entrypoint 5: Mission Control Dashboard

- **Command:** `npm run dev`
- **File:** `mission-control/` (Next.js 16 application)
- **Runtime:** Node.js
- **Purpose:** Operational dashboard with pages for runs, registry, pipeline status, agents, and tools. Communicates with the FastAPI bridge.

---

## 3. Execution Call Graphs

### 3.1 Harvest Pipeline Call Graph

```
runHarvest.ts
  main()
  -> runHarvest(SEASON_CORPUS_HARVEST)            [harvestController.ts]
     -> buildQueriesForSeason(seasonWindow)        [HARVEST_QUERIES_V1.ts]
        -> returns 6 HarvestQuerySets (60 queries total)
     -> FOR EACH querySet, FOR EACH query:
        -> runDeepSearchRawQuery(query)            [deepsearchClient.ts]
           -> braveSearch(query)                   [braveClient.ts]
              -> fetch("api.search.brave.com")
              -> normalize -> SearchResult[]
        -> FOR EACH result:
           -> isAllowedSource(url)                 [sourceFilter.ts]
           -> shouldAcceptResult(result, seenKeys) [duplicateGuard.ts]
              -> buildDuplicateKey(result)
           -> fetchArticle(url)                    [articleFetcher.ts]
           -> extractArticle(html, url)            [extractArticle.ts]
              -> JSDOM + Readability OR cheerio fallback
           -> cleanText(articleText)               [cleanText.ts]
           -> validate text length >= 500 chars
           -> buildPacket(result, ...)             [packetBuilder.ts]
              -> slugify(publication)
              -> normalizeDateToYYYYMMDD()
              -> currentTimestampISO()
           -> artifactGate(packet)                 [artifactGate.ts]
              -> (currently bypassed, always "accept")
           -> writePacket(packet, ...)             [packetWriter.ts]
              -> mkdir + write packet.json, raw.txt, _complete
     -> return {packetsWritten, queriesRun, skippedDuplicates, packetPaths}
```

### 3.2 Intake Validation Call Graph

```
runIntake.ts
  main()
  -> intakeValidatedPackets(sharedCorpusRoot, seasonWindow)  [runPacketIntake.ts]
     -> scanSeasonPackets(root, seasonWindow)                 [packetScanner.ts]
        -> listChildDirectories(seasonPath)
     -> FOR EACH packetDir:
        -> validatePacket(packetDir)                          [packetValidationGate.ts]
           -> check required files: packet.json, raw.txt, _complete
           -> parse packet.json, validate metadata fields
           -> check raw.txt length >= 500 chars
           -> return {isValid, reasons[]}
        -> IF invalid: moveRejectedPacket(dir, root, reasons)
           -> fs.renameSync + write rejection_log.json
     -> return {accepted[], rejected[]}
```

### 3.3 NTI Pipeline Call Graph

```
cli.ts
  main()
  -> runNtiFromSharedCorpus(season)                           [runNtiFromSharedCorpus.ts]
     -> enumerateSharedCorpusPackets(season)                  [enumerateSharedCorpusPackets.ts]
     -> FOR EACH packetPath:
        -> loadSharedCorpusPacket(path)                       [loadSharedCorpusPacket.ts]
        -> adaptSharedCorpusPacketToNti(packet)               [adaptSharedCorpusPacketToNti.ts]
        -> runExtraction(ntiDoc)                              [runExtraction.ts]
           -> (STUB: no-op)
```

### 3.4 Python Orchestrator Call Graph

```
entrypoint.py
  run_research_agent(ledger_root, env_path, mode)
  -> assert_ledger_reachable(ledger_root)                     [ledger_gate.py]
  -> acquire_run_lock(ledger_root)                            [concurrency_guard.py]
  -> orchestrator_run(ledger_root)                            [orchestrator.py]
     -> STEP 1: Preflight Read (load global_state.json)
     -> STEP 2: Determine Action (new_batch | crash_recovery)
     -> STEP 3: Canonical Pipeline Processing
        -> (Phase 13.1 stub: not yet wired to extraction agents)
     -> STEP 4: End-of-Batch Boundary
        -> increment counters, checkpoint state
     -> STEP 5: Termination Evaluation
        -> NTI audit, sealed/exhausted check
     -> _commit_canonical_object()
        -> CPS dedup + CIV validation + registry append
  -> write_invocation_log(result)                             [invocation_logger.py]
  -> release_run_lock()
```

### 3.5 Extraction Orchestrator V2 Call Graph

```
extractionOrchestratorV2.ts
  runExtractionPipeline(ntiDoc)
  -> Python bridge subprocess calls:
     -> Stage 1: rec_producer.produce_rec(rawText)
     -> Stage 2: split_mechanics.split_rec(rec)  [GSD]
     -> Stage 3 (Pressure Lane):
        -> PLO-E expansion
        -> PSTA canonicalization
     -> Stage 4 (Narrative Lane):
        -> NCA classification
        -> SANTA transformation
        -> CSN canonicalization
  -> return ExtractionOrchestratorResult
```

---

## 4. Core Architecture Files (Ranked)

### Tier 1 -- Core Runtime Controllers (8 files)

These files define the system's execution behavior. Removing any one would break the runtime.

| # | File | Role |
|---|------|------|
| 1 | `engines/deep-search/corpus-harvester/harvestController.ts` | Main harvest loop; orchestrates all search, fetch, build, write operations |
| 2 | `infra/orchestration/runtime/orchestrator.py` | Core Python orchestrator; implements micro-batch execution contract |
| 3 | `the-script/extraction-agent/orchestrator/extractionOrchestratorV2.ts` | Hybrid TS/Python extraction pipeline orchestrator |
| 4 | `infra/orchestration/openclaw/entrypoint.py` | OpenClaw runtime entry; validates, locks, invokes orchestrator |
| 5 | `runtime/server.py` | FastAPI bridge; connects dashboard to orchestrator |
| 6 | `engines/deep-search/agents/ingest/runPacketIntake.ts` | Packet validation orchestrator |
| 7 | `src/nti/runNtiFromSharedCorpus.ts` | NTI packet enumeration and adaptation pipeline |
| 8 | `mission-control/src/lib/ledger.server.ts` | Server-side ledger access for dashboard |

### Tier 2 -- Core Pipeline Modules (18 files)

These implement the system's processing stages.

| # | File | Role |
|---|------|------|
| 9 | `engines/deep-search/corpus-harvester/deepsearchClient.ts` | Search API adapter (Brave) |
| 10 | `engines/deep-search/corpus-harvester/braveClient.ts` | Brave Search HTTP client |
| 11 | `engines/deep-search/corpus-harvester/extractArticle.ts` | HTML-to-text extraction |
| 12 | `engines/deep-search/corpus-harvester/packetBuilder.ts` | Source packet construction |
| 13 | `engines/deep-search/corpus-harvester/packetWriter.ts` | Disk I/O for packets |
| 14 | `engines/deep-search/corpus-harvester/duplicateGuard.ts` | URL/title deduplication |
| 15 | `engines/deep-search/corpus-harvester/sourceFilter.ts` | Domain blocklist |
| 16 | `engines/deep-search/corpus-harvester/articleFetcher.ts` | HTTP article fetch |
| 17 | `engines/deep-search/corpus-harvester/cleanText.ts` | Text sanitization pipeline |
| 18 | `engines/deep-search/agents/ingest/packetValidationGate.ts` | Packet structural validation |
| 19 | `engines/deep-search/agents/ingest/packetScanner.ts` | Filesystem packet discovery |
| 20 | `engines/research-agent/agents/extraction/extraction_agent.py` | IAV extraction enforcement |
| 21 | `engines/research-agent/agents/classification/routing_gate.py` | Seed type routing |
| 22 | `engines/research-agent/agents/pressure/psta.py` | Pressure signal canonical minting |
| 23 | `engines/research-agent/agents/narrative/ane_constructor.py` | Narrative event construction |
| 24 | `engines/research-agent/agents/CIV/civ.py` | Canonical Integrity Validator |
| 25 | `infra/mcp/mcp_agent.py` | Media Context Processor |
| 26 | `engines/research_engine/agent_runtime/agent_registry.py` | Agent registration/dispatch |

### Tier 3 -- Data Model Definitions (12 files)

These define the schemas and type contracts the system operates on.

| # | File | Role |
|---|------|------|
| 27 | `engines/deep-search/corpus-harvester/types.ts` | TypeScript type definitions (HarvestDirective, SearchResult, SourcePacket) |
| 28 | `engines/deep-search/corpus-harvester/HARVEST_QUERIES_V1.ts` | 60 NFL query templates across 6 passes |
| 29 | `engines/research-agent/schemas/canonical_pressure_object.schema.json` | CPS canonical schema |
| 30 | `engines/research-agent/schemas/canonical_narrative_csn_object.schema.json` | CSN canonical schema |
| 31 | `engines/research-agent/schemas/canonical_media_context_object.schema.json` | CME canonical schema |
| 32 | `engines/research-agent/schemas/rec.schema.json` | Raw Extraction Container schema |
| 33 | `engines/research-agent/schemas/au.schema.json` | Atomic Unit schema |
| 34 | `engines/research-agent/schemas/ledger/global_state.schema.json` | Global execution state |
| 35 | `engines/research-agent/schemas/ledger/season_state.schema.json` | Season-level state |
| 36 | `engines/research-agent/version_lock.json` | Authoritative version snapshot |
| 37 | `engines/research_engine/agent_runtime/agent_packet.py` | AgentRunPacket dataclass |
| 38 | `engines/research_engine/agent_runtime/agent_result.py` | AgentResult dataclass |

### Tier 4 -- Utilities and Helpers (8 files)

| # | File | Role |
|---|------|------|
| 39 | `engines/deep-search/corpus-harvester/utils.ts` | slugify, normalizeDateToYYYYMMDD, safeString |
| 40 | `engines/deep-search/corpus-harvester/artifactGate.ts` | SHA-256 fingerprint quality gate (currently bypassed) |
| 41 | `infra/orchestration/openclaw/concurrency_guard.py` | Run lock acquisition |
| 42 | `infra/orchestration/openclaw/invocation_logger.py` | JSONL invocation logging |
| 43 | `infra/orchestration/openclaw/ledger_gate.py` | Ledger reachability assertion |
| 44 | `engines/research_engine/ledger/atomic_write.py` | Atomic file operations |
| 45 | `engines/research_engine/ledger/rollback_handler.py` | Crash recovery rollback |
| 46 | `src/nti/adaptSharedCorpusPacketToNti.ts` | Packet format adapter |

---

## 5. Runtime Pipeline Reconstruction

The system executes as a **four-phase pipeline** with a clear handoff boundary between phases:

### Phase A: Corpus Harvesting (TypeScript)

1. A `HarvestDirective` is loaded, specifying the season window ("2000-2001"), target source count (30-40), and output root.
2. Six query passes are generated from `HARVEST_QUERIES_V1.ts`, producing 60 search queries covering narrative texture, media reaction, conflict events, structural context, anomalies, and general discovery.
3. Each query is executed against Brave Search API (10 results per query).
4. For each search result: the URL is checked against a domain blocklist (YouTube, Twitter/X, Reddit, Facebook are blocked); deduplication is applied via a composite key of URL, title, publication, and date; the article HTML is fetched and extracted to plain text using Readability with a cheerio fallback; the text is cleaned (ads removed, whitespace normalized) and validated for minimum length (500 chars).
5. A `BuiltSourcePacket` is constructed with deterministic packet ID (`{season}_{publication}_{ordinal}`), normalized metadata, and raw text.
6. The packet is written to disk as three files: `packet.json` (metadata), `raw.txt` (article text), and `_complete` (completion marker).
7. Harvesting stops when `targetMaxSources` is reached.

### Phase B: Intake Validation (TypeScript)

8. The intake validator scans the `shared-corpus/{season}/` directory for all packet subdirectories.
9. Each packet is validated for: presence of required files (`packet.json`, `raw.txt`, `_complete`); valid JSON with required metadata fields (`packet_id`, `source_title`, `publication`, `date_published`, `url`, `season_window`, `harvest_timestamp`, `harvester_version`); raw text length at least 500 characters.
10. Valid packets remain in place; invalid packets are moved to a rejection directory with a `rejection_log.json` recording failure reasons and timestamp.

### Handoff Boundary (Filesystem)

The `shared-corpus/` directory serves as the deterministic filesystem boundary between the TypeScript harvester and the Python extraction pipeline. The `HANDOFF-LAYER-SPECIFICATION.md` contract governs this boundary.

### Phase C: Extraction and Canonicalization (Python, orchestrated from TypeScript)

11. The NTI CLI enumerates validated packets, loads them, and adapts each to an `NtiSourceDocument`.
12. The Extraction Orchestrator V2 bridges to Python via subprocess, executing: REC (Raw Extraction Container) production from raw text; GSD (Granular Structure Distribution) splitting into atomic units; classification and routing to the appropriate lane.
13. The **Pressure Lane** processes signals through: PLO-E (Pressure Legible Observation Expansion), 2A assembly and enum normalization, PSCA (Pressure Signal Critic Agent) audit, and PSTA (Pressure Signal Transformation Agent) canonical minting with deterministic fingerprint-based IDs.
14. The **Narrative Lane** processes events through: NCA (Narrative Classification Agent), SANTA (Standalone Narrative Transformer Agent) or META (Media Event Transformer Agent), and CSN canonicalization with ANE (Atomic Narrative Event) envelope wrapping.
15. The CIV (Canonical Integrity Validator) validates each canonical object for schema completeness, enum compliance, identity abstraction, and cross-lane contamination.

### Phase D: Orchestration and Ledger Commit (Python)

16. The OpenClaw orchestrator executes in discrete, stateless invocations following a five-step micro-batch flow: Preflight Read (load ledger state), Determine Action (new batch vs. crash recovery), Canonical Pipeline Processing, End-of-Batch Boundary (checkpoint), and Termination Evaluation.
17. Canonical objects are committed atomically with CPS deduplication and CIV validation.
18. State is persisted to the ledger as `global_state.json`, season-specific `state.json`, `canonical_objects.json`, and `cycle_log.json`.
19. The Pipeline Quality Governor (PQG) observes metrics without mutating data.

---

## 6. Data Model Explanation

### Source Packet (Harvester Output)

The fundamental data unit produced by harvesting. Each packet occupies a directory containing three files.

**`packet.json` fields:** `packet_id` (deterministic slug), `source_title`, `publication`, `author`, `date_published` (YYYY-MM-DD or "unknown_date"), `url`, `season_window`, `team_context[]`, `narrative_tags[]`, `harvest_timestamp` (ISO 8601), `harvester_version`.

**`raw.txt`:** Cleaned article text, minimum 500 characters.

**`_complete`:** Completion marker file containing the string "complete".

### NtiSourceDocument (Extraction Input)

Adapted from a source packet for the extraction pipeline: `sourceId`, `sourceType`, `seasonWindow`, `title`, `publication`, `author`, `url`, `rawText`, `teamContext[]`, `narrativeTags[]`.

### Atomic Unit (AU)

The smallest extractable observation from a source document, produced by the GSD split. Routed to either the pressure or narrative lane based on classification.

### Canonical Pressure Signal (CPS)

The canonical output of the pressure lane. Key fields: deterministic fingerprint-based ID (CPS_FINGERPRINT_V1), signal_class, pressure_signal_domain, pressure_vector, signal_polarity, observation_source, and frozen enum values from the Canonical Enum Registry.

### Canonical Narrative Event (CSN/ANE)

The canonical output of the narrative lane, wrapped in an ANE v1.0 + 2B-EMIT envelope. Features a deterministic `eventSeedId` with KP1/KP2/KP3 lock mechanism for identity integrity.

### Canonical Media Event (CME)

Output of the media lane for media-framing observations. Validated by the MCP agent against prohibited language rules.

### Ledger State

The orchestrator persists execution state across four structures: `global_state.json` (cross-run counters and status), season-level `state.json` (per-season execution progress), `canonical_objects.json` (registry of all committed canonical objects), and `cycle_log.json` (NTI cycle history).

---

## 7. System Purpose

Based strictly on code behavior, this system is designed to **build a structured, canonicalized knowledge corpus of NFL narrative and pressure-signal data from web sources**.

**Inputs:** The system expects a season window specification (currently "2000-2001") and access to the Brave Search API. It generates 60 targeted search queries across six discovery categories (narrative texture, media reaction, conflict events, structural context, anomalies, and general discovery) to find NFL-related articles.

**Processing:** Articles are harvested, validated, and then passed through a multi-lane extraction pipeline that decomposes raw text into atomic observations. Each observation is classified and routed to either a pressure-signal lane (coaching changes, salary cap disputes, player suspensions) or a narrative-event lane (games, trades, organizational decisions). A media-context lane handles media framing observations separately.

**Outputs:** The system produces canonicalized, fingerprint-identified structured objects (CPS, CSN, CME) stored in a ledger-based registry. Each object has a deterministic identity derived from its content, making the entire pipeline reproducible and deduplication-safe.

**Workflow Automated:** The system automates the transformation of unstructured sports journalism into a structured, typed, and validated knowledge graph of NFL events and pressure signals, with strict governance contracts ensuring no interpretive inference contaminates the canonical output.

---

## 8. Architecture Strengths

**Contract-driven design.** The 47 markdown contracts in `contracts_md/` are remarkably thorough. They define not just data schemas but behavioral invariants (INV-1 through INV-5), identity governance rules, lane isolation policies, and crash recovery procedures. This is unusually disciplined for a system at this stage.

**Deterministic identity model.** Canonical objects are identified by content-derived SHA-256 fingerprints rather than sequential counters or runtime state. This makes deduplication inherent to the data model and ensures reproducibility across runs.

**Strong separation of concerns.** The architecture cleanly separates harvesting (TypeScript/Brave API), validation (TypeScript/filesystem), extraction (Python agents), orchestration (Python/ledger), and visualization (Next.js/React). Each layer communicates through well-defined filesystem or HTTP boundaries.

**Modularity of the agent system.** The research-agent engine contains 100+ Python modules organized by domain (extraction, classification, pressure, narrative, media, CIV, EMI, GSD, MCP). Each agent has a single responsibility and communicates through typed data structures.

**Crash safety and ledger integrity.** The orchestrator implements an incompleteBatchFlag persisted before processing, with a one-retry envelope and automatic rollback on double failure. The concurrency guard prevents parallel execution.

**Comprehensive test coverage.** 108 test files in the research-agent engine, plus 8 integration tests in the root tests directory, covering classification, extraction, pressure, narrative, EMI, GSD, ledger operations (including crash simulation), and orchestrator lifecycle.

**Lane isolation.** Pressure, narrative, and media processing lanes are architecturally isolated with explicit cross-lane contamination checks in the CIV.

---

## 9. Weakness and Risk Analysis

### 9.1 Incomplete Pipeline Wiring

The most significant weakness is that the extraction pipeline is not yet wired end-to-end. The NTI CLI's `runExtraction()` function is a stub (no-op). The Python orchestrator's canonical pipeline processing step is marked as "Phase 13.1" and is not yet connected to the extraction agents. The Extraction Orchestrator V2 exists in `the-script/` but is not called from either the NTI CLI or the Python orchestrator.

### 9.2 Artifact Gate Bypassed

The `artifactGate.ts` module always returns "accept" regardless of input. The SHA-256 fingerprint infrastructure exists but is inactive. This means duplicate or low-quality content can pass through harvesting unchecked.

### 9.3 Missing Publication Metadata

All five existing packets in `shared-corpus/` have empty `publication` and `author` fields, and `date_published` is set to "unknown_date". The Brave Search API returns limited metadata (title, URL, description), and the system does not currently extract publication/author/date from the article HTML. This will degrade the quality of canonical objects downstream.

### 9.4 Hardcoded Season Window

The harvest configuration is hardcoded to "2000-2001" with a fixed target of 30-40 sources. There is no configuration layer for specifying different seasons, source counts, or query templates without modifying source code.

### 9.5 Single Search Provider

The system depends entirely on the Brave Search API. The `deepsearchClient.ts` contains remnants of a `/query` and `/query_raw` endpoint for a local "DeepSearcher" service, but these are unused. If Brave API access is lost or rate-limited, the entire harvest pipeline stops.

### 9.6 Silent Error Handling in Article Fetcher

`articleFetcher.ts` catches all fetch errors silently and returns an empty string. This means network failures, 403/429 responses, and timeouts are indistinguishable from empty pages. There is no retry logic, no backoff, and no error logging.

### 9.7 Dual Language Complexity

The system splits across TypeScript and Python, connected via subprocess calls (JSON over stdin/stdout) in the Extraction Orchestrator V2. This adds deployment complexity, makes debugging harder, and creates a potential serialization bottleneck for large-scale processing.

### 9.8 Vestigial and Duplicate Code

Multiple directory variants exist: `engines/research-agent/` (full implementation) vs. `engines/research_agent/` (empty `__init__.py`); similarly `engines/research-engine/` vs. `engines/research_engine/`. The `Archive/` directory contains a dated copy. This creates confusion about which code is authoritative.

### 9.9 API Key in Environment File

The Brave API key is stored in a plaintext `.env` file committed to the repository. This is a security risk if the repository is ever shared or pushed to a remote.

### 9.10 No Rate Limiting or Throttling

The harvest pipeline executes queries and article fetches as fast as possible with no rate limiting, no concurrency control, and no backoff. This risks API key revocation from Brave and potential blocking by article source domains.

---

## 10. Completion Assessment

**Classification: B -- Partially implemented system**

**Reasoning:**

The system has a complete and thoroughly specified contract layer (47 governance documents), a fully functional corpus harvesting pipeline (search, fetch, extract, validate, write), a comprehensive Python agent library with 100+ modules and 108 tests, a working FastAPI bridge and Next.js dashboard, and a well-designed ledger persistence layer.

However, the critical pipeline integration is incomplete. The NTI extraction step is a stub. The Python orchestrator's canonical pipeline processing is not yet wired to the extraction agents. The Extraction Orchestrator V2 exists but is not connected to either the NTI CLI or the orchestrator entry point. This means data flows into `shared-corpus/` successfully but cannot yet flow through extraction and canonicalization in an automated end-to-end run.

The system is best described as: contracts fully specified, individual modules substantially implemented and tested, but end-to-end integration not yet achieved.

---

## 11. Test Readiness

### Can the system currently be executed?

**Partially.** The following components can be executed independently:

**Harvest pipeline (YES):**
Requires only a valid Brave API key in `.env` and Node.js with tsx installed. Run `npm run harvest:v1`. This will produce packets in `shared-corpus/2000_2001/`.

**Intake validation (YES):**
Run `npm run intake:v1` after harvesting. Validates existing packets in shared-corpus.

**NTI CLI (PARTIALLY):**
Run `npm run nti -- 2000-2001`. This will enumerate and load packets but extraction is a no-op.

**Dashboard (YES):**
Run `npm run dev`. The Next.js dashboard will launch, but operational endpoints require the FastAPI bridge to be running.

**FastAPI bridge (LIKELY):**
Run `python runtime/server.py`. Requires Python with FastAPI/uvicorn installed. The `/run` endpoint invokes the orchestrator which will execute but canonical pipeline processing is stubbed.

**Python tests (LIKELY):**
108 test files in `engines/research-agent/tests/`. Require pytest and Python dependencies to be installed.

### What is missing for full end-to-end execution?

1. The `runExtraction()` stub in `src/extraction/runExtraction.ts` must be wired to the Extraction Orchestrator V2.
2. The Python orchestrator's "Phase 13.1" canonical pipeline step must be connected to the extraction agent adapters.
3. Python dependencies need a `requirements.txt` or `pyproject.toml` (none exists at the root level).
4. The TS/Python subprocess bridge in `extractionOrchestratorV2.ts` requires the Python agent modules to be importable (correct PYTHONPATH and package structure).
5. The `.env` file must contain a valid `BRAVE_API_KEY`.

---

## 12. Critical Questions for the System Owner

### Architecture and Integration

1. **What connects the NTI CLI to the Extraction Orchestrator V2?** The `runExtraction()` stub and the extraction orchestrator in `the-script/` appear to be two halves of the same bridge. What is the planned wiring between them?

2. **Is `the-script/extraction-agent/` the canonical extraction orchestrator, or is it being superseded by the Python-native agent pipeline?** Both paths exist but neither is connected end-to-end.

3. **What is the intended relationship between the Python orchestrator (`infra/orchestration/`) and the TypeScript NTI CLI (`src/nti/`)?** Are they meant to be separate execution paths, or should one invoke the other?

4. **Which directory variants are authoritative?** `research-agent` vs `research_agent`, `research-engine` vs `research_engine` -- are the underscore variants deprecated import shims, or something else?

### Data Quality

5. **How will publication, author, and date metadata be populated?** Current packets have empty metadata. Will this be extracted from article HTML, or is there a planned metadata enrichment step?

6. **What is the minimum viable corpus size per season?** The current target is 30-40 sources. Is this sufficient for the extraction and canonicalization pipeline to produce meaningful output?

7. **How will the system handle paywalled or JavaScript-rendered content?** The current `articleFetcher.ts` does a simple HTTP GET, which will fail for sites requiring authentication or client-side rendering.

### Scaling and Operations

8. **What is the target scale?** Is this meant to process a single season (2000-2001) or all NFL seasons? The hardcoded configuration suggests single-season focus, but the architecture implies multi-season support.

9. **What rate limits apply to the Brave Search API?** With 60 queries per harvest run and 10 results per query, a single run makes 60 API calls plus up to 600 article fetches. What happens when this scales to multiple seasons?

10. **How will the FastAPI bridge and orchestrator be deployed?** The current setup assumes localhost. Is there a planned deployment target (Docker, cloud, etc.)?

### Governance and Contracts

11. **Are the 47 contracts in `contracts_md/` enforced programmatically, or are they aspirational specifications?** Some contracts (like the CIV and PQG) have corresponding code; others (like the Identity Abstraction Enforcement Contract) may not yet have implementations.

12. **What is the versioning strategy for contracts and schemas?** The `version_lock.json` pins CPS-1.0, CSN-1.0, CME-1.0, CSE-1.0. What triggers a version bump, and how are migrations handled?

13. **What is the role of `milvus.db`?** A 28KB Milvus vector database file exists at the root. Is this used for semantic search, embedding-based deduplication, or something else? It does not appear to be referenced by any runtime code.

### Testing and Validation

14. **Have the 108 Python tests been run recently, and do they pass?** No `requirements.txt` or CI configuration is present, so the test environment is unclear.

15. **Is there an integration test that exercises the full pipeline from harvest through canonicalization?** Unit tests exist for individual modules, but end-to-end validation appears absent.

16. **What constitutes a "correct" canonical object?** The CIV validates structural integrity, but who validates semantic correctness? Is there a gold-standard corpus for comparison?

### Security and Dependencies

17. **Should the `.env` file with the Brave API key be committed to the repository?** This is a security risk if the repo is shared.

18. **What Python version is required?** The code uses type hints and dataclasses, suggesting Python 3.7+, but the exact version requirement is not documented.

19. **How should the Node.js and Python dependency trees be managed?** There is `package.json` for Node but no Python dependency manifest at the project root.

20. **What is the long-term plan for the Archive directory?** It contains a dated copy of the research agent. Should it be removed to reduce confusion about which code is canonical?

---

*End of Architecture Reconstruction Report*
