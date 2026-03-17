from copy import deepcopy

from ncg.narrative_pipeline_gate import enforce_narrative_pipeline


def _event(**overrides):
    base = {
        "id": "evt_001",
        "classification": "CSN",
        "standaloneSubclass": "anecdotal_beat",
        "actorRole": "skill_player",
        "action": "appeared",
        "objectRole": None,
        "contextRole": None,
        "timestampContext": "2025_W10",
        "eventDescription": "A one-off event occurred.",
        "sourceReference": "ref_001",
        "unusualProcedural": False,
    }
    base.update(overrides)
    return base


def test_cme_classification_deferred_guard_blocks_meta(monkeypatch):
    calls = {"meta": 0, "santa": 0}

    def fake_nca(event):
        return True, None, {"classification": "CME", "standaloneSubclass": None}

    def fake_meta(event):
        calls["meta"] += 1
        return True, None, {"canonicalObject": {"eventType": "CME"}}

    def fake_santa(event):
        calls["santa"] += 1
        return True, None, {"canonicalObject": {"eventType": "CSN"}}

    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_nca", fake_nca)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_meta", fake_meta)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_santa", fake_santa)

    passed, rejections, audit = enforce_narrative_pipeline(_event(classification="CME"))
    assert passed is False
    assert rejections["rejected"] is True
    assert rejections["reason"] == "ERR_CME_CLASSIFICATION_DEFERRED"
    assert calls["meta"] == 0
    assert calls["santa"] == 0
    assert audit is None


def test_valid_csn_event_pass_and_santa_called(monkeypatch):
    calls = {"meta": 0, "santa": 0}

    def fake_nca(event):
        return True, None, {"classification": "CSN", "standaloneSubclass": "anecdotal_beat"}

    def fake_meta(event):
        calls["meta"] += 1
        return True, None, {"canonicalObject": {"eventType": "CME"}}

    def fake_santa(event):
        calls["santa"] += 1
        return True, None, {"canonicalObject": {"eventType": "CSN"}}

    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_nca", fake_nca)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_meta", fake_meta)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_santa", fake_santa)

    passed, rejections, audit = enforce_narrative_pipeline(_event())
    assert passed is True
    assert rejections == []
    assert calls["meta"] == 0
    assert calls["santa"] == 1
    assert "transformer" in audit


def test_nca_failure_blocks_transformers(monkeypatch):
    calls = {"meta": 0, "santa": 0}

    def fake_nca(event):
        return False, {"reasonCode": "REJECT_NCA"}, None

    def fake_meta(event):
        calls["meta"] += 1
        return True, None, {}

    def fake_santa(event):
        calls["santa"] += 1
        return True, None, {}

    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_nca", fake_nca)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_meta", fake_meta)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_santa", fake_santa)

    passed, rejections, audit = enforce_narrative_pipeline(_event())
    assert passed is False
    assert len(rejections) == 1
    assert calls["meta"] == 0
    assert calls["santa"] == 0
    assert "nca" in audit
    assert "ncg" not in audit
    assert "transformer" not in audit


def test_ncg_failure_blocks_transformers(monkeypatch):
    calls = {"meta": 0, "santa": 0}

    def fake_nca(event):
        return True, None, {"classification": "CSN", "standaloneSubclass": "anecdotal_beat"}

    def fake_ncg(event):
        return False, {"reasonCode": "FAIL_NCG"}, {"verdict": "FAIL"}

    def fake_meta(event):
        calls["meta"] += 1
        return True, None, {}

    def fake_santa(event):
        calls["santa"] += 1
        return True, None, {}

    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_nca", fake_nca)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_ncg", fake_ncg)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_meta", fake_meta)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_santa", fake_santa)

    passed, rejections, audit = enforce_narrative_pipeline(_event())
    assert passed is False
    assert len(rejections) == 1
    assert calls["meta"] == 0
    assert calls["santa"] == 0
    assert "nca" in audit
    assert "ncg" in audit
    assert "transformer" not in audit


def test_composite_audit_key_presence_by_path(monkeypatch):
    def fake_nca(event):
        return True, None, {"classification": "CSN", "standaloneSubclass": "anecdotal_beat"}

    def fake_ncg(event):
        return True, None, {"verdict": "PASS"}

    def fake_santa(event):
        return True, None, {"canonicalObject": {"eventType": "CSN"}}

    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_nca", fake_nca)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_ncg", fake_ncg)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_santa", fake_santa)

    passed, _rejections, audit = enforce_narrative_pipeline(_event())
    assert passed is True
    assert "nca" in audit
    assert "ncg" in audit
    assert "transformer" in audit


def test_input_event_not_mutated(monkeypatch):
    def fake_nca(event):
        return True, None, {"classification": "CSN", "standaloneSubclass": "anecdotal_beat"}

    def fake_ncg(event):
        return True, None, {"verdict": "PASS"}

    def fake_santa(event):
        return True, None, {"canonicalObject": {"eventType": "CSN"}}

    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_nca", fake_nca)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_ncg", fake_ncg)
    monkeypatch.setattr("ncg.narrative_pipeline_gate.enforce_santa", fake_santa)

    event = _event()
    before = deepcopy(event)
    _ = enforce_narrative_pipeline(event)
    assert event == before
