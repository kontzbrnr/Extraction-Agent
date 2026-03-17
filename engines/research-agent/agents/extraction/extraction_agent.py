"""
ExtractionAgent — Phase 3.1 Skeleton

Governing contract: ORCHESTRATOR-EXECUTION-CONTRACT.md §IV Step 3.

INV-1: All reads are performed at call time inside extract().
       No batch data, cluster data, or result state is stored on self.
INV-4: Lane is passed per-call. It is never stored on self.
INV-5: Consumers of `content` from read_batch() MUST sort keys
       before any canonical operation. ingestedAt MUST NOT be used
       as canonical identity input.
"""

from infra.ingestion.raw_material.store import read_batch
from engines.research_engine.ledger.batch_collector import BatchCollector


class ExtractionAgent:
    """
    Reads raw material from RawMaterialStore by batch_id and
    accumulates extraction results into a BatchCollector.

    Stateless: __init__ stores only immutable configuration.
    No cross-batch memory. No cross-lane state.
    """

    def __init__(self, store_path: str) -> None:
        """
        Args:
            store_path: Path to the raw_material store JSON file.
                        Stored as immutable config only.
                        No disk read is performed here (INV-1).
        """
        self._store_path = store_path
        # NO other instance variables. Do not add self.results,
        # self._cache, self._batch_id, self._lane, or any container.

    def extract(
        self,
        batch_id: str,
        lane: str,
        collector: BatchCollector,
    ) -> None:
        """
        Process one cluster for the given batch_id and lane.

        Reads raw material freshly from disk on every call (INV-1).
        Accumulates results into collector keyed by lane (INV-4).
        Must not use read_batch()'s ingestedAt for canonical
        identity (INV-5). Must sort content keys before any
        canonical operation (INV-5).

        Args:
            batch_id:  Identifier of the batch to read.
            lane:      Lane identifier for this cluster (INV-4).
            collector: BatchCollector instance for this batch run.
                       Passed explicitly — never stored on self.

        Raises:
            NotImplementedError: Implementation pending Phase 3.x.
            ValueError:          If batch_id is empty.
            RawMaterialReadError:    If store is unreadable.
            RawMaterialNotFoundError: If batch_id not in store.
        """
        raise NotImplementedError(
            "ExtractionAgent.extract() — implementation pending Phase 3.x"
        )
