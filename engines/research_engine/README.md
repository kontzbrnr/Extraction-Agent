# engines/research_engine

This directory is the import-safe package namespace for runtime adapter code used by the orchestrator.

## Relationship to hyphenated tree

- `engines/research-engine/` contains ledger/runtime modules in hyphenated filesystem layout.
- `engines/research_engine/` contains import-safe package modules referenced by code such as:
  - `engines.research_engine.agent_runtime.*`

Because Python module names cannot contain `-`, underscored paths are required for imports.
