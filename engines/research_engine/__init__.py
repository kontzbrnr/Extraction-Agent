# Shim package: redirects engines.research_engine.* imports to the
# hyphenated source directory engines/research-engine/.
# Required because Python package names cannot contain hyphens.
# Do not delete.

from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
_legacy_dir = _pkg_dir.parent / "research-engine"

__path__ = [str(_pkg_dir), str(_legacy_dir)]
