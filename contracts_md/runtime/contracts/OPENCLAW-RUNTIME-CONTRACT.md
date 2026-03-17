📜 OPENCLAW RUNTIME CONTRACT v1.0
(OpenClaw — Ledger-Driven, Stateless Trigger Shell)

I. ROLE DEFINITION
OpenClaw is the outer execution shell for the research agent runtime.
OpenClaw is not an agent.
OpenClaw does not interpret.
OpenClaw does not make ontology decisions.
OpenClaw only triggers orchestrator actions.
This constraint is permanent and non-negotiable.
It exists to prevent architecture drift.

OpenClaw:
* Receives an invocation trigger
* Passes minimum required inputs to the orchestrator
* Waits for the orchestrator result
* Returns an execution summary
* Exits

OpenClaw does not:
* Interpret worker outputs
* Make decisions about canonical objects
* Influence pipeline routing
* Evaluate ontology classifications
* Modify orchestrator results
* Carry state between invocations

II. INVOCATION RULE (THE LOCK)
One invocation = one orchestrator action.
OpenClaw does not run multi-step loops internally.
OpenClaw does not chain orchestrator calls within a single trigger.
Each OpenClaw invocation starts fresh from ledger state.
External scheduler drives the next invocation.

This rule exists to preserve replay determinism.
Internal looping would make invocation boundaries non-observable
and crash recovery non-deterministic.

III. AUTHORITY CHAIN
OpenClaw's sole downstream call target is the orchestrator.

OpenClaw invokes:
* orchestrator_run(ledger_root) — and nothing else

OpenClaw does NOT directly invoke:
* PLO-E (Pressure-Legible Observation Expansion)
* IAV (Identity Abstraction Validator)
* PSTA (Pressure Signal Transformation Agent)
* EMI (Event Material Identifier)
* Media mint
* CIV (Canonical Integrity Validator)
* Any extraction agent
* Any critic agent
* Any transformation agent

Those agents remain under orchestrator authority exclusively.
A direct call from OpenClaw into any of those agents constitutes
a contract violation.

IV. MINIMUM INPUT SURFACE
OpenClaw accepts only the minimum invocation parameters:
* ledger_root       — required. Absolute path to ledger root directory.
* env_path          — required. Path to environment / repo root.
* run_id            — optional. Identifier for the current season run.
* mode              — required. Must be "deterministic". No other value permitted.
* seed              — optional. Fixed seed value where relevant.

OpenClaw does not expose per-agent tuning parameters.
OpenClaw does not accept ontology configuration.
OpenClaw does not accept pipeline routing overrides.

V. LEDGER-FIRST MANDATE
Before every OpenClaw-triggered run, the orchestrator must:
1. Read global_state.json
2. Read current season/run state
3. Inspect incomplete batch flag
4. Determine next valid action
5. Proceed only from ledger truth

OpenClaw must not pass state data to the orchestrator as a substitute
for ledger reads. The orchestrator's ledger reads are unconditional.
This is non-negotiable.

OpenClaw does not know what action the orchestrator will take.
OpenClaw does not predict or pre-evaluate the next action.
OpenClaw triggers. The orchestrator decides.

VI. CONCURRENCY PROHIBITION
Before any real runtime invocation:
* Single writer enforced
* Single orchestrator invocation at a time
* No parallel canonical commits

OpenClaw must not be invoked concurrently.
Concurrent invocation constitutes a contract violation.
The external scheduler is responsible for serialization.

VII. HARD FAIL ON STATE AMBIGUITY
If the orchestrator cannot determine the next valid action from ledger state:
* Halt immediately
* Return a deterministic error code
* Write no canonical state
* Do not guess
* Do not attempt recovery by interpretation

OpenClaw surfaces the error to the caller and exits.
It does not retry. It does not re-invoke. It does not patch state.
The next valid trigger is the caller's responsibility.

VIII. PROHIBITIONS
OpenClaw may not:
* Cache ledger state between invocations
* Modify the orchestrator result before returning it
* Suppress orchestrator errors
* Introduce timeouts that mask orchestrator failure
* Pass pre-computed action directives to the orchestrator
* Execute any pipeline stage directly
* Emit canonical objects
* Write to the canonical registry
* Read the canonical registry
* Interpret terminationStatus values
* Make branching decisions based on orchestrator output content
* Invoke the orchestrator more than once per trigger

IX. SYSTEM CHARACTER
OpenClaw is:
* Stateless per invocation
* Ledger-driven (via orchestrator)
* Non-interpretive
* Non-ontological
* Trigger-bounded
* Deterministic in invocation behavior

It is not adaptive.
It is not intelligent.
It is a controlled trigger surface.

X. GOVERNING AUTHORITY
Orchestrator-layer behavior is governed exclusively by:
    ORCHESTRATOR-EXECUTION-CONTRACT.md v1.0

This document governs only the OpenClaw invocation boundary.
Conflicts between this document and ORCHESTRATOR-EXECUTION-CONTRACT.md
are resolved in favor of ORCHESTRATOR-EXECUTION-CONTRACT.md for all
matters within the orchestrator boundary.

OpenClaw is outside the orchestrator boundary.
The orchestrator boundary begins at orchestrator_run().