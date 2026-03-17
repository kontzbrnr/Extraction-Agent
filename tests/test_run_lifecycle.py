from infra.orchestration.runtime.run_lifecycle import RunLifecycleEngine
from infra.orchestration.runtime.run_models import RunRequest


def _request(profile: str) -> RunRequest:
    return RunRequest(
        profile=profile,
        entry_stage="narrative",
        payload={"ledger_root": "/tmp/ledger"},
    )


def test_process_next_run_and_process_all_runs_sequential():
    engine = RunLifecycleEngine()

    processed_profiles = []

    def _fake_start_run(run_request: RunRequest):
        processed_profiles.append(run_request.profile)
        return {"profile": run_request.profile, "status": "SUCCEEDED"}

    engine.controller.start_run = _fake_start_run

    engine.enqueue_run(_request("p1"))
    first = engine.process_next_run()

    assert first == {"profile": "p1", "status": "SUCCEEDED"}
    assert processed_profiles == ["p1"]

    engine.enqueue_run(_request("p2"))
    engine.enqueue_run(_request("p3"))

    remaining = engine.process_all_runs()

    assert remaining == [
        {"profile": "p2", "status": "SUCCEEDED"},
        {"profile": "p3", "status": "SUCCEEDED"},
    ]
    assert processed_profiles == ["p1", "p2", "p3"]
    assert engine.queue.is_empty()
