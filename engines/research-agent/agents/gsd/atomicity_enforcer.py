"""
AtomicityEnforcer — Phase 4.1 Skeleton

Contract authority: GLOBAL-SPLIT-DOCTRINE.md (GSD) v1.0
Pipeline position: Receives RECs from extraction layer.
Produces AU set + PCR set before seed typing.

INV-1: __init__ stores no state. enforce() is stateless per call.
INV-2: No AU or PCR fingerprint computation in this module.
INV-5: Given identical recs and identical rule version,
       enforce() must produce identical (au_set, pcr_set).
"""


class AtomicityEnforcer:
    """
    Global Split Doctrine enforcement gate.
    Transforms composite and non-composite RECs into atomic units
    and parent composite records.
    """

    def __init__(self) -> None:
        """Pure transformation gate. No configuration required.
        No disk reads. No disk writes.
        No mutable state stored on self.
        """
        pass
        # NO other instance variables. Do not add self._aus,
        # self._pcrs, self._recs, or any container.

    def enforce(
        self,
        recs: list[dict],
        source_reference: str,
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """Apply Global Split Doctrine to a set of RECs.

        For each REC:
          - If isComposite is False: wrap as a single AU (splitIndex=0).
          - If isComposite is True and deterministically separable:
              produce sibling AUs; retain PCR unchanged.
          - If isComposite is True and boundary unclear:
              reject with ERR_COMPOSITE_BOUNDARY_UNCLEAR.

        Args:
            recs: List of REC dicts. Each must conform to REC-1.0 schema.
            source_reference: Article or cluster pointer. Required on
                              every AU produced. Never derived from REC
                              content (caller-supplied).

        Returns:
            (au_set, pcr_set, rejection_set) where:
              au_set:       List of AU dicts conforming to AU-1.0 schema.
                            Ordered by (parentSourceID, splitIndex) ascending.
              pcr_set:      List of PCR dicts conforming to PCR-1.0 schema.
                            One PCR per composite REC that was split.
              rejection_set: List of REJECTION-1.0 dicts. One per REC
                             rejected due to unclear atomicity boundary.

        Raises:
            NotImplementedError: Implementation pending Phase 4.x.
        """
        raise NotImplementedError(
            "AtomicityEnforcer.enforce() — implementation pending Phase 4.x"
        )
