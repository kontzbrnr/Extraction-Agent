from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

import extraction.extraction_agent as extraction_agent_module
from engines.research_agent.agents.extraction.extraction_agent import ExtractionAgent
from engines.research_engine.ledger.batch_collector import BatchCollector, make_batch_collector


def test_init_stores_only_store_path() -> None:
    agent = ExtractionAgent("/path/to/store.json")

    assert agent._store_path == "/path/to/store.json"
    assert vars(agent) == {"_store_path": "/path/to/store.json"}


def test_init_does_not_read_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    def _must_not_be_called(*args, **kwargs):
        raise AssertionError("must not be called")

    monkeypatch.setattr(extraction_agent_module, "read_batch", _must_not_be_called)

    ExtractionAgent("/any/path")


def test_two_instances_share_no_state() -> None:
    a1 = ExtractionAgent("/path/a")
    a2 = ExtractionAgent("/path/b")

    assert a1._store_path != a2._store_path
    assert a1 is not a2


def test_extract_raises_not_implemented() -> None:
    agent = ExtractionAgent("/path/to/store.json")
    collector = make_batch_collector("BATCH_2024_0001")

    with pytest.raises(NotImplementedError):
        agent.extract("BATCH_2024_0001", "CPS", collector)


def test_extract_signature_accepts_correct_types() -> None:
    signature = inspect.signature(ExtractionAgent.extract)
    params = signature.parameters

    assert list(params.keys()) == ["self", "batch_id", "lane", "collector"]
    assert params["batch_id"].annotation is str
    assert params["lane"].annotation is str
    assert params["collector"].annotation is BatchCollector


def test_no_forbidden_imports() -> None:
    source_path = Path("/Users/nicholas/Desktop/contentlib-docs/research-agent/extraction/extraction_agent.py")
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])

    forbidden = {"time", "datetime", "uuid", "random"}
    assert imported_names.isdisjoint(forbidden)
