import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from engines.research_engine.ledger.batch_collector import make_batch_collector
from infra.orchestration.runtime.orchestrator import _run_canonical_pipeline


def test_run_canonical_pipeline_collects_cps_and_csn(tmp_path: Path):
    season = "2000-2001"
    season_path = tmp_path / "shared-corpus" / "2000_2001"
    packet_dir = season_path / "packet-001"
    packet_dir.mkdir(parents=True)

    (packet_dir / "packet.json").write_text(
        json.dumps(
            {
                "packet_id": "packet-001",
                "source_title": "test title",
                "season_window": season,
                "team_context": [],
                "narrative_tags": [],
            }
        ),
        encoding="utf-8",
    )
    (packet_dir / "raw.txt").write_text("example raw text", encoding="utf-8")

    extraction_result = {
        "pressureLane": {"cpsObjects": [{"canonicalId": "CPS_" + "a" * 64}]},
        "narrativeLane": {"csnObjects": [{"id": "CSN_" + "b" * 64}]},
    }

    collector = make_batch_collector("BATCH_2000-2001_0001")

    with patch("infra.orchestration.runtime.orchestrator.subprocess.run") as mock_run:
        mock_run.return_value = SimpleNamespace(
            returncode=0,
            stdout=json.dumps(extraction_result),
            stderr="",
        )

        _run_canonical_pipeline(
            ledger_root=str(tmp_path),
            active_run_path="runs/active",
            season=season,
            batch_id="BATCH_2000-2001_0001",
            cycle_snapshot={
                "schemaVersion": "CPS-1.0",
                "enumVersion": "ENUM_v1.0",
                "contractVersion": "CIV-1.0",
            },
            collector=collector,
        )

    assert collector.lanes["CPS"] == extraction_result["pressureLane"]["cpsObjects"]
    assert collector.lanes["CSN"] == extraction_result["narrativeLane"]["csnObjects"]
