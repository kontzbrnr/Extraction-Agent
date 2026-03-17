from ncg.ncg_audit_log import make_ncg_audit_log


def test_pass_verdict_log_shape_and_values():
    log = make_ncg_audit_log(
        verdict="PASS",
        reason_code="PASS_ALL_NCG_CHECKS",
        failure_stage=None,
        event_ref="evt_001",
    )
    assert set(log.keys()) == {
        "ncgAuditSchemaVersion",
        "ncgVersion",
        "eventRef",
        "verdict",
        "reasonCode",
        "failureStage",
    }
    assert log["verdict"] == "PASS"


def test_fail_verdict_log_contains_failure_stage():
    log = make_ncg_audit_log(
        verdict="FAIL",
        reason_code="FAIL_NCG_MISSING_CLASSIFICATION",
        failure_stage="1_CLASSIFICATION_GATE",
        event_ref="evt_002",
    )
    assert log["verdict"] == "FAIL"
    assert log["failureStage"] is not None


def test_audit_log_deterministic_for_identical_inputs():
    args = {
        "verdict": "FAIL",
        "reason_code": "FAIL_NCG_MISSING_CLASSIFICATION",
        "failure_stage": "1_CLASSIFICATION_GATE",
        "event_ref": None,
    }
    assert make_ncg_audit_log(**args) == make_ncg_audit_log(**args)


def test_event_ref_none_when_missing():
    event = {"foo": "bar"}
    event_ref = event.get("eventSeedId") or event.get("id") or None
    assert event_ref is None
