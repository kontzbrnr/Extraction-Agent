import json
from pathlib import Path

from infra.orchestration.entrypoints import start_run


def test_start_run_main_creates_run_record():
    runs_root = Path("runtime") / "runs"
    before = set(p.name for p in runs_root.iterdir() if p.is_dir()) if runs_root.exists() else set()

    start_run.main()

    after = set(p.name for p in runs_root.iterdir() if p.is_dir())
    new_dirs = sorted(after - before)

    assert new_dirs, "Expected at least one new run directory"

    latest_dir = runs_root / new_dirs[-1]
    run_record_path = latest_dir / "run_record.json"

    assert run_record_path.exists()

    record = json.loads(run_record_path.read_text(encoding="utf-8"))
    assert "run_id" in record
    assert record["run_id"].startswith("run_")
