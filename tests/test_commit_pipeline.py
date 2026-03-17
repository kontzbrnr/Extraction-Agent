def test_commit_pipeline(orchestrator):

    cps_obj = {
        "canonicalId": "CPS_TEST_001",
        "lane": "CPS",
        "data": {"test": True}
    }

    result = orchestrator._commit_canonical_object(
        obj=cps_obj,
        lane="CPS",
        cycle_snapshot={},
        batch_id="test_batch",
        collector=None
    )

    assert result["status"] == "accepted"

    # Duplicate test
    result2 = orchestrator._commit_canonical_object(
        obj=cps_obj,
        lane="CPS",
        cycle_snapshot={},
        batch_id="test_batch",
        collector=None
    )

    assert result2["status"] == "duplicate"
