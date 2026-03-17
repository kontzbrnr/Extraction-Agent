import json
import shutil
import uuid
from pathlib import Path

from infra.orchestration.runtime.run_models import RunRecord, RunStatus
from infra.orchestration.runtime.run_packet import RunPacket
from infra.orchestration.runtime.run_state_store import (
    create_run_directory,
    create_run_record,
    update_run_status,
    write_packet,
    write_run_result,
)


def test_run_state_store_persistence_flow():
    run_id = f"run_test_{uuid.uuid4()}"
    run_dir = Path("runtime") / "runs" / run_id

    packet = RunPacket(
        run_id=run_id,
        stage="narrative",
        agent_name="narrative",
        payload={"sample": True},
        metadata={"profile": "test"},
        context={},
    )

    record = RunRecord(
        run_id=run_id,
        status=RunStatus.QUEUED,
        created_at="2026-03-12T00:00:00+00:00",
        updated_at="2026-03-12T00:00:00+00:00",
        profile="test",
        entry_stage="narrative",
    )

    try:
        create_run_directory(run_id)
        write_packet(run_id, packet)
        create_run_record(record)
        update_run_status(run_id, RunStatus.RUNNING)
        write_run_result(run_id, {"run_id": run_id, "status": "SUCCEEDED"})

        assert (run_dir / "packet.json").exists()
        assert (run_dir / "run_record.json").exists()
        assert (run_dir / "result.json").exists()

        run_record_json = json.loads((run_dir / "run_record.json").read_text(encoding="utf-8"))
        assert run_record_json["status"] == "RUNNING"
    finally:
        if run_dir.exists():
            shutil.rmtree(run_dir)
