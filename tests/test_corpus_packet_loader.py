import json

import pytest

from infra.orchestration.runtime.corpus_packet_loader import (
    NoValidCorpusPacketError,
    load_first_valid_corpus_packet,
)


def _write_packet_dir(base_dir, packet_dir_name: str, *, metadata=None, raw_text="hello", include_complete=True):
    packet_dir = base_dir / packet_dir_name
    packet_dir.mkdir(parents=True, exist_ok=True)

    if metadata is not None:
        (packet_dir / "packet.json").write_text(
            json.dumps(metadata),
            encoding="utf-8",
        )

    (packet_dir / "raw.txt").write_text(raw_text, encoding="utf-8")

    if include_complete:
        (packet_dir / "_complete").write_text("complete\n", encoding="utf-8")

    return packet_dir


def test_returns_first_valid_packet(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "shared-corpus" / "2000_2001"

    _write_packet_dir(
        root,
        "packet_0002",
        metadata={"packet_id": "packet_0002", "source_title": "Two"},
        raw_text="text two",
    )
    _write_packet_dir(
        root,
        "packet_0001",
        metadata={"packet_id": "packet_0001", "source_title": "One"},
        raw_text="text one",
    )

    packet = load_first_valid_corpus_packet()

    assert packet["packet_id"] == "packet_0001"
    assert packet["raw_text"] == "text one"
    assert packet["source_title"] == "One"


def test_rejects_packet_missing_packet_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "shared-corpus" / "2000_2001"

    _write_packet_dir(
        root,
        "packet_0001",
        metadata=None,
        raw_text="text one",
        include_complete=True,
    )

    with pytest.raises(NoValidCorpusPacketError):
        load_first_valid_corpus_packet()


def test_rejects_packet_with_empty_raw_text(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "shared-corpus" / "2000_2001"

    _write_packet_dir(
        root,
        "packet_0001",
        metadata={"packet_id": "packet_0001"},
        raw_text="   \n\t",
        include_complete=True,
    )

    with pytest.raises(NoValidCorpusPacketError):
        load_first_valid_corpus_packet()


def test_deterministic_ordering_with_multiple_packets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "shared-corpus" / "2000_2001"

    _write_packet_dir(
        root,
        "packet_0010",
        metadata={"packet_id": "packet_0010", "source_title": "Ten"},
        raw_text="text ten",
    )
    _write_packet_dir(
        root,
        "packet_0003",
        metadata={"packet_id": "packet_0003", "source_title": "Three"},
        raw_text="text three",
    )
    _write_packet_dir(
        root,
        "packet_0007",
        metadata={"packet_id": "packet_0007", "source_title": "Seven"},
        raw_text="text seven",
    )

    packet = load_first_valid_corpus_packet()

    assert packet["packet_id"] == "packet_0003"
    assert packet["source_title"] == "Three"
