# engines/research_agent

This directory is a **Python package shim** for the hyphenated implementation tree at `engines/research-agent/`.

## Why it exists

Python import paths cannot include hyphens, so runtime modules import via:

- `engines.research_agent.*`
- `engines.research_engine.*`

The `engines/research-agent/` and `engines/research-engine/` directories remain the authoritative source layout on disk, while this underscored path provides package resolution for imports.

## Contract-critical note

Do not remove this directory unless all import paths are migrated away from `engines.research_agent.*`.
