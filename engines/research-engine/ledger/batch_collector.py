"""
ledger/batch_collector.py

In-memory batch result collector for a single micro-batch.

Role:
  Accumulates canonical objects per lane during micro-batch processing.
  Used exclusively within a single invocation — never cached at module
  or class level, never persisted to disk.

Governing authority: Research Agent Execution Roadmap, Phase 2.9.
  "MicroBatchScaffold: generates batch_id, marks batch start flag,
   creates BatchCollector instance, passes through call stack."

Design constraints:
  - Instance created fresh per batch (via make_batch_collector factory)
  - No disk I/O — data lives only in memory during invocation
  - No caching at module level — every call to make_batch_collector() 
    returns a new instance
  - Lane keys are arbitrary strings (e.g., "CPS", "CSN", "CME")
  - Per-lane order preserved; sorted_lanes() must be called before
    passing to append_canonical_object() to satisfy INV-5

INV-5 enforcement:
  sorted_lanes() returns a dict with sorted lane keys to ensure
  byte-identical JSON when canonical results are persisted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BatchCollector:
    """In-memory accumulator for canonical objects during a single micro-batch.

    Attributes:
        batch_id:  Batch identifier (e.g., "BATCH_2024_REG_0001").
        lanes:     Dict mapping lane names to lists of accumulated objects.
                   Created on first add() call per lane.
    """

    batch_id: str
    lanes: dict[str, list[Any]] = field(default_factory=dict)

    def add(self, lane: str, obj: Any) -> None:
        """Append obj to the given lane list.

        Creates the lane list on first access. Safe to call with any lane
        string. No validation of obj type or content.

        Args:
            lane: Lane identifier (e.g., "CPS", "CSN", "CME").
            obj:  Object to append. Stored as-is.
        """
        if lane not in self.lanes:
            self.lanes[lane] = []
        self.lanes[lane].append(obj)

    def sorted_lanes(self) -> dict[str, list[Any]]:
        """Return a new dict with sorted lane keys; per-lane order preserved.

        Lane keys are sorted ascending. Per-lane object order is unchanged.
        Must be called before passing to append_canonical_object() to
        satisfy INV-5 (byte-identical JSON for identical input).

        Returns:
            Dict mapping sorted lane names to their object lists.
        """
        return {k: self.lanes[k] for k in sorted(self.lanes)}


def make_batch_collector(batch_id: str) -> BatchCollector:
    """Factory function to create a new BatchCollector instance.

    Always returns a fresh instance. Never cached. Called once per
    micro-batch by the orchestration entry point.

    Args:
        batch_id: Batch identifier to store in the collector.

    Returns:
        A new BatchCollector instance with empty lanes dict.
    """
    return BatchCollector(batch_id=batch_id)
