from __future__ import annotations

import uuid
from datetime import datetime, timezone
from importlib import import_module

from infra.orchestration.runtime.run_models import RunRecord, RunRequest, RunStatus
from infra.orchestration.runtime.run_packet import RunPacket
from infra.orchestration.runtime.run_state_store import (
    create_run_directory,
    create_run_record,
    update_run_status,
    write_packet,
    write_run_error,
    write_run_result,
)


class RunController:
    def start_run(self, run_request: RunRequest) -> dict:
        run_id = f"run_{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        packet = RunPacket(
            run_id=run_id,
            stage=run_request.entry_stage,
            agent_name=run_request.entry_stage,
            payload=run_request.payload,
            metadata={"profile": run_request.profile},
            context={},
        )

        run_record = RunRecord(
            run_id=run_id,
            status=RunStatus.QUEUED,
            created_at=now,
            updated_at=now,
            profile=run_request.profile,
            entry_stage=run_request.entry_stage,
        )

        create_run_directory(run_id)
        write_packet(run_id, packet)
        create_run_record(run_record)
        update_run_status(run_id, RunStatus.RUNNING)

        try:
            orchestrator_module = import_module("infra.orchestration.runtime.orchestrator")
            execute = getattr(orchestrator_module, "execute")
            _result = execute(packet)
            write_run_result(
                run_id,
                {
                    "run_id": run_id,
                    "status": RunStatus.SUCCEEDED.value,
                },
            )
            update_run_status(run_id, RunStatus.SUCCEEDED)
            return {
                "run_id": run_id,
                "status": RunStatus.SUCCEEDED.value,
            }
        except Exception as exc:
            write_run_error(run_id, exc)
            update_run_status(run_id, RunStatus.FAILED)
            return {
                "run_id": run_id,
                "status": RunStatus.FAILED.value,
            }
