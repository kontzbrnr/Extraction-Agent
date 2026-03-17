from __future__ import annotations

import json
from pathlib import Path


class NoValidCorpusPacketError(Exception):
    pass


def _candidate_roots() -> list[Path]:
    cwd = Path.cwd()
    roots = [cwd / "shared-corpus", cwd / "contentlib-docs" / "shared-corpus"]
    deduped: list[Path] = []
    seen = set()
    for root in roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(root)
    return deduped


def _is_valid_packet_dir(packet_dir: Path) -> bool:
    packet_json_path = packet_dir / "packet.json"
    raw_text_path = packet_dir / "raw.txt"
    complete_path = packet_dir / "_complete"

    if not packet_json_path.is_file() or not raw_text_path.is_file() or not complete_path.is_file():
        return False

    try:
        json.loads(packet_json_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    raw_text = raw_text_path.read_text(encoding="utf-8")
    if raw_text.strip() == "":
        return False

    return True


def load_first_valid_corpus_packet() -> dict:
    packet_dirs: list[Path] = []

    for root in _candidate_roots():
        if not root.is_dir():
            continue
        for candidate in root.rglob("*"):
            if candidate.is_dir() and _is_valid_packet_dir(candidate):
                packet_dirs.append(candidate)

    if not packet_dirs:
        raise NoValidCorpusPacketError(
            "No valid corpus packet found under shared-corpus roots."
        )

    packet_dirs.sort(key=lambda path: path.as_posix())
    selected_dir = packet_dirs[0]

    metadata = json.loads((selected_dir / "packet.json").read_text(encoding="utf-8"))
    raw_text = (selected_dir / "raw.txt").read_text(encoding="utf-8")

    packet_id = metadata.get("packet_id")
    if not isinstance(packet_id, str) or packet_id.strip() == "":
        raise NoValidCorpusPacketError(
            f"Selected packet at {selected_dir} is missing packet_id in packet.json"
        )

    return {
        "packet_id": packet_id,
        "raw_text": raw_text,
        "source_title": metadata.get("source_title"),
        "publication": metadata.get("publication"),
        "url": metadata.get("url"),
        "season_window": metadata.get("season_window"),
    }
