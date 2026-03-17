from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infra.orchestration.runtime.run_lifecycle import RunLifecycleEngine
from infra.orchestration.runtime.run_models import RunRequest
from infra.orchestration.runtime.corpus_packet_loader import load_first_valid_corpus_packet


def main():
    lifecycle = RunLifecycleEngine()

    packet = load_first_valid_corpus_packet()
    au = {
        "id": packet["packet_id"],
        "text": packet["raw_text"],
    }
    payload = {
        "au": au,
        "source_reference": packet["packet_id"],
        "source_title": packet.get("source_title"),
        "publication": packet.get("publication"),
        "url": packet.get("url"),
        "season_window": packet.get("season_window"),
    }

    run_request = RunRequest(
        profile="manual_corpus_run",
        entry_stage="extraction",
        payload=payload,
    )

    lifecycle.enqueue_run(run_request)

    results = lifecycle.process_all_runs()

    print("Run execution results:")
    print(results)


if __name__ == "__main__":
    main()
