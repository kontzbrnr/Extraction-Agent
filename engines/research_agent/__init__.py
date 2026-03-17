# Shim package: redirects engines.research_agent.* imports to the
# hyphenated source directory engines/research-agent/.
# Required because Python package names cannot contain hyphens.
# Do not delete.

from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
_legacy_dir = _pkg_dir.parent / "research-agent"

__path__ = [str(_legacy_dir)]
