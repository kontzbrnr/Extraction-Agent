from __future__ import annotations

import ast
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _non_test_py_files() -> list[Path]:
    blocked_parts = {"tests", "__pycache__", "vendor", ".venv", "node_modules"}
    return [
        p
        for p in PROJECT_ROOT.rglob("*.py")
        if not any(part in blocked_parts for part in p.parts)
    ]


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _call_targets(tree: ast.AST) -> list[str]:
    targets: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                targets.append(fn.id)
            elif isinstance(fn, ast.Attribute):
                targets.append(fn.attr)
    return targets


# ── Phase 2.1 — CPS mint authority proofs ────────────────────────────────────

def test_2_1_only_psta_calls_derive_cps_fingerprint():
    call_sites: list[str] = []
    for path in _non_test_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if "derive_cps_fingerprint" in _call_targets(tree):
            call_sites.append(_relative(path))

    assert call_sites == ["engines/research-agent/agents/pressure/psta.py"]


def test_2_1_cps_id_regex_literal_only_in_cps_id_format():
    regex_literals = (
        re.compile(r"\^CPS_\[a-f0-9\]\{64\}\$"),
        re.compile(r"CPS_\[a-f0-9\]\{64\}"),
    )

    matches: list[str] = []
    for path in _non_test_py_files():
        text = path.read_text(encoding="utf-8")
        if any(rx.search(text) for rx in regex_literals):
            matches.append(_relative(path))

    assert matches == ["engines/research-agent/agents/pressure/cps_id_format.py"]


def test_2_1_only_cps_constructor_writes_canonical_id_on_pressure_objects():
    writers: list[str] = []
    for path in _non_test_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue

            key_values = {}
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    key_values[key.value] = value

            if "canonicalId" not in key_values or "laneType" not in key_values:
                continue

            lane_value = key_values["laneType"]
            is_pressure_lane = (
                isinstance(lane_value, ast.Constant)
                and lane_value.value in {"PRESSURE", "CPS"}
            ) or (
                isinstance(lane_value, ast.Name) and lane_value.id == "PSTA_LANE_TYPE"
            )
            if is_pressure_lane:
                rel = _relative(path)
                if rel not in writers:
                    writers.append(rel)

    assert writers == ["engines/research-agent/agents/pressure/cps_constructor.py"]


# ── Phase 2.2 — Narrative mint authority proofs ──────────────────────────────

def test_2_2_only_ane_fingerprint_defines_aneseed_id_construction():
    matches: list[str] = []
    pattern = re.compile(r"ANESEED_PREFIX\s*\+\s*digest|ANESEED_PREFIX\}\{digest")
    for path in _non_test_py_files():
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            matches.append(_relative(path))

    assert matches == ["engines/research-agent/agents/narrative/ane_fingerprint.py"]
