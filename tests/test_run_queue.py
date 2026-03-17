from infra.orchestration.runtime.run_models import RunRequest
from infra.orchestration.runtime.run_queue import RunQueue


def _request(profile: str) -> RunRequest:
    return RunRequest(
        profile=profile,
        entry_stage="narrative",
        payload={"ledger_root": "/tmp/ledger"},
    )


def test_run_queue_fifo_order():
    queue = RunQueue()

    r1 = _request("p1")
    r2 = _request("p2")
    r3 = _request("p3")

    queue.enqueue(r1)
    queue.enqueue(r2)
    queue.enqueue(r3)

    assert queue.size() == 3
    assert queue.dequeue() == r1
    assert queue.dequeue() == r2
    assert queue.dequeue() == r3
    assert queue.is_empty()
