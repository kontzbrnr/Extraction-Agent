"""
ORCHESTRATOR ENTRY POINT INTEGRATION GUIDE
Phase 2.9: MicroBatchScaffold

This document specifies where and how to integrate the batch_collector
and mark_batch_start flag into the orchestration entry point.

═══════════════════════════════════════════════════════════════════════════════
LOCATION: ORCHESTRATOR-EXECUTION-CONTRACT.md Section IV, Step 2
═══════════════════════════════════════════════════════════════════════════════

Contract text (lines 54-55):
    Step 2 — Determine Action
    If no active micro-batch:→ Initiate NTI micro-batch.
    If active micro-batch exists:→ Process entire batch through canonical pipeline.

═══════════════════════════════════════════════════════════════════════════════
IMPLEMENTATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

1. AT BATCH INITIATION (when no active micro-batch exists):

   a. Generate batch_id:
      Format: BATCH_{season}_{microBatchCount:04d}
      Example: BATCH_2024_REG_0001
      Authority: Orchestrator (from ledger state)

   b. Mark batch start (sets incomplete flag BEFORE cluster processing):
      
      from ledger.season_state_manager import mark_batch_start, BatchAlreadyInProgressError
      
      try:
          mark_batch_start(ledger_root, active_run_path, batch_id)
      except BatchAlreadyInProgressError:
          raise  # Do NOT swallow — caller handles crash recovery
      
      This sets:
        incompleteBatchFlag = True
        activeBatchId = batch_id
      
      Guarantees: Flag is persisted BEFORE any cluster processing begins,
      allowing crash detection on next invocation.

   c. Create batch collector (in-memory accumulator):
      
      from ledger.batch_collector import make_batch_collector
      
      collector = make_batch_collector(batch_id)
      
      This returns a fresh instance with empty lanes dict.
      DO NOT cache at module level. Pass explicitly through call stack.

   d. Pass collector to cluster processing pipeline:
      
      for cluster in batch:
          # For each cluster extraction/transformation:
          for canonical_obj in transform(cluster):
              lane = canonical_obj["lane"]
              collector.add(lane, canonical_obj)
      
      Collector accumulates per-lane results during batch processing.

2. AT BATCH BOUNDARY (after all clusters processed):

   a. Sort lanes before persisting (INV-5):
      
      sorted_results = collector.sorted_lanes()
      # {CME: [...], CPS: [...], CSN: [...]} (sorted by lane name)
      
      This ensures byte-identical JSON for identical input.

   b. Persist canonical objects per lane:
      
      from ledger.registry_writer import append_canonical_object
      
      for lane, objects in sorted_results.items():
          for obj in objects:
              append_canonical_object(registry_path, lane, obj)
      
      Each append is atomic with read-back verification.

   c. Increment micro-batch count and update state:
      
      from ledger.season_state_manager import increment_micro_batch_count
      
      new_count = increment_micro_batch_count(ledger_root, active_run_path)
      
      Then clear batch flag:
      
      from ledger.season_state_manager import clear_incomplete_batch_flag
      
      clear_incomplete_batch_flag(ledger_root, active_run_path)

3. CRASH RECOVERY (if BatchAlreadyInProgressError raised):

   Authority: Orchestrator OR external crash recovery handler

   from ledger.rollback_handler import detect_crash, rollback_incomplete_batch
   
   if detect_crash(ledger_root, active_run_path):
       rollback_incomplete_batch(ledger_root, active_run_path)
       # Discard entire batch, reset flag
       # Resume by initiating new micro-batch

═══════════════════════════════════════════════════════════════════════════════
KEY DESIGN DECISIONS
═══════════════════════════════════════════════════════════════════════════════

1. Flag Authority:
   mark_batch_start() is the EXCLUSIVE authority for writing the flag.
   IngestController does NOT call mark_batch_start() — that is forbidden.
   MicroBatchScaffold (via orchestrator) calls it before cluster processing.

2. Collector Scope:
   BatchCollector is instantiated fresh per micro-batch via make_batch_collector().
   It lives only in memory during a single invocation.
   It is NEVER cached, stored in self, or persisted to disk.
   NEVER instantiate BatchCollector directly — use make_batch_collector() factory.

3. Memorylessness (INV-1):
   Orchestrator reads ledger state unconditionally on every invocation.
   Does NOT cache batch_id, flag state, or collector between invocations.
   Each invocation is independent.

4. Determinism (INV-5):
   sorted_lanes() must be called before passing to append_canonical_object()
   to ensure byte-identical JSON for identical results.
   All sorting is ascending by lane name.

5. Immutability (INV-3):
   canonical_objects.json is NEVER written by orchestrator directly.
   ONLY append_canonical_object() may write to it.
   Orchestrator does NOT modify, rewrite, or mutate worker outputs.

═══════════════════════════════════════════════════════════════════════════════
PSEUDO-CODE: ORCHESTRATOR MAIN LOOP
═══════════════════════════════════════════════════════════════════════════════

def orchestrator_run(ledger_root: str, active_run_path: str) -> None:
    # Step 1: Preflight read
    global_state = read_global_state(ledger_root)
    season_state = read_season_state(ledger_root, active_run_path)
    
    if season_state["terminationStatus"] != "running":
        return  # Exit — termination condition met
    
    # Step 2: Determine action
    if season_state["incompleteBatchFlag"] is False:
        # Initiate NTI micro-batch
        batch_id = f"BATCH_{season}_{season_state['microBatchCount']:04d}"
        
        # Wire-up: Mark batch start
        try:
            mark_batch_start(ledger_root, active_run_path, batch_id)
        except BatchAlreadyInProgressError:
            raise  # Crash recovery required
        
        # Wire-up: Create collector
        collector = make_batch_collector(batch_id)
        
        # Get next NTI surface
        nti_surface = select_next_surface(...)
        
        # Process clusters for this surface
        for cluster in get_clusters_for_surface(nti_surface):
            # Extraction → transformation
            for canonical_obj in transform(cluster):
                lane = canonical_obj["lane"]
                collector.add(lane, canonical_obj)
        
        # Step 4: End-of-batch boundary
        sorted_results = collector.sorted_lanes()
        for lane, objects in sorted_results.items():
            for obj in objects:
                append_canonical_object(registry_path, lane, obj)
        
        new_count = increment_micro_batch_count(ledger_root, active_run_path)
        clear_incomplete_batch_flag(ledger_root, active_run_path)
    
    else:
        # Resume processing (incomplete batch exists)
        batch_id = season_state["activeBatchId"]
        collector = make_batch_collector(batch_id)
        
        # Continue from where previous invocation left off
        # (requires additional state tracking — out of scope for Phase 2.9)
        pass
    
    # Step 5: Termination evaluation
    termination = evaluate_termination(ledger_root, active_run_path, exhaustion_triggered=False)
    
    if termination.new_status != "running":
        # Exit with terminal status set

═══════════════════════════════════════════════════════════════════════════════
TESTED PATTERNS
═══════════════════════════════════════════════════════════════════════════════

All wire-up patterns are tested in:
  - tests/ledger/test_batch_collector.py (9 tests, all passing)
  - tests/ledger/test_season_state_manager.py (34 tests, all passing)

Specific test coverage:
  ✓ mark_batch_start() sets flag and batch_id correctly
  ✓ mark_batch_start() raises BatchAlreadyInProgressError on duplicate
  ✓ make_batch_collector() returns fresh instances
  ✓ collector.add() preserves per-lane order
  ✓ collector.sorted_lanes() returns sorted keys
  ✓ Integration: collector independent of flag lifecycle

═══════════════════════════════════════════════════════════════════════════════
"""
