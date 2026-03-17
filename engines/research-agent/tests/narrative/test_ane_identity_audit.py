import re
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _non_test_py_files(root: Path) -> list[Path]:
    return [
        p
        for p in root.rglob("*.py")
        if "tests" not in p.parts and "__pycache__" not in p.parts
    ]


def test_only_ane_fingerprint_defines_ane_fingerprint_version():
    root = _project_root()
    pattern = re.compile(r'^\s*ANE_FINGERPRINT_VERSION\s*:\s*str\s*=\s*"ANE_FINGERPRINT_V1"', re.MULTILINE)
    matches = []
    for path in _non_test_py_files(root):
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            matches.append(path.relative_to(root).as_posix())
    assert matches == ["narrative/ane_fingerprint.py"]


def test_only_ane_fingerprint_builds_aneseed_id_using_prefix_variable():
    root = _project_root()
    pattern = re.compile(r'ANESEED_PREFIX\}\{digest\}|ANESEED_PREFIX\s*\+')
    matches = []
    for path in _non_test_py_files(root):
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            matches.append(path.relative_to(root).as_posix())
    assert matches == ["narrative/ane_fingerprint.py"]


def test_only_ane_id_format_defines_aneseed_prefix_constant():
    root = _project_root()
    pattern = re.compile(r'^\s*ANESEED_PREFIX\s*:\s*str\s*=', re.MULTILINE)
    matches = []
    for path in _non_test_py_files(root):
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            matches.append(path.relative_to(root).as_posix())
    assert matches == ["narrative/ane_id_format.py"]
