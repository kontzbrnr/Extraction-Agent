"""
Phase 13.10 — Identity Authority Prohibition Audit

Static assertions that orchestrator/orchestrator.py contains no code that
computes fingerprints, constructs canonical IDs, or uses cryptographic
identity primitives, in compliance with §I, §VIII, INV-2.

Contract references:
    §I:   Orchestrator does not compute fingerprints, does not derive
          canonical IDs, does not assign identifiers.
    §VIII: Orchestrator may not generate canonical identifiers or construct
           identity keys.
    INV-2: No hashlib, no fingerprint call, no canonical ID construction.

These tests read orchestrator.py as source text and inspect its runtime
namespace. They do not test runtime behavior.
"""

import importlib
import inspect
import re
import sys

import pytest

import infra.orchestration.runtime.orchestrator as orch_module


# ── Helpers ───────────────────────────────────────────────────────────────────

def _source() -> str:
    """Return the full source text of orchestrator/orchestrator.py."""
    return inspect.getsource(orch_module)


def _code_lines() -> list[str]:
    """Return non-comment, non-docstring lines of orchestrator.py source.

    Strips:
        - Lines whose first non-whitespace character is '#'
        - Lines that are part of triple-quoted string literals

    Note: This is a conservative approximation suitable for catching
    accidental live-code violations. A full AST walk is not required
    because the prohibited patterns have no legitimate live-code use
    in this module.
    """
    source = _source()
    source = re.sub(r'"""[\s\S]*?"""', "", source)
    source = re.sub(r"'''[\s\S]*?'''", "", source)
    lines = source.splitlines()
    result = []
    in_docstring = False
    for line in lines:
        stripped = line.strip()
        # Toggle docstring state on triple-quote boundaries.
        if stripped.startswith('"""') or stripped.startswith("'''"):
            in_docstring = not in_docstring
            continue
        if in_docstring:
            continue
        # Skip pure comment lines.
        if stripped.startswith("#"):
            continue
        result.append(line)
    return result


def _code_text() -> str:
    return "\n".join(_code_lines())


# ── Group A: Forbidden module imports ─────────────────────────────────────────

class TestForbiddenImports:
    """hashlib, uuid, and random must not appear in the orchestrator namespace.

    These modules provide cryptographic hashing and identifier generation
    primitives that are prohibited by INV-2 and §VIII.
    """

    def test_hashlib_not_in_namespace(self):
        assert "hashlib" not in orch_module.__dict__, (
            "hashlib is imported into orchestrator — violates INV-2 / §VIII"
        )

    def test_uuid_not_in_namespace(self):
        assert "uuid" not in orch_module.__dict__, (
            "uuid is imported into orchestrator — violates INV-2 / §VIII"
        )

    def test_random_not_in_namespace(self):
        assert "random" not in orch_module.__dict__, (
            "random is imported into orchestrator — ID generation via random "
            "is prohibited by §VIII"
        )

    def test_hashlib_not_importable_from_module(self):
        assert not hasattr(orch_module, "hashlib"), (
            "orchestrator exposes hashlib attribute — violates INV-2"
        )

    def test_uuid_not_importable_from_module(self):
        assert not hasattr(orch_module, "uuid"), (
            "orchestrator exposes uuid attribute — violates INV-2"
        )


# ── Group B: Forbidden source symbols ─────────────────────────────────────────

class TestForbiddenSourceSymbols:
    """Cryptographic and hashing symbols must not appear in live code.

    Checked against non-comment, non-docstring lines only so that
    legitimate prohibition reminders in docstrings do not trigger.
    """

    @pytest.mark.parametrize("symbol", [
        "hexdigest",
        "sha256",
        "sha512",
        "sha1",
        "md5",
        "hashlib",
        "uuid4",
        "uuid5",
        "uuid1",
        "uuid3",
    ])
    def test_symbol_absent_from_live_code(self, symbol):
        code = _code_text()
        assert symbol not in code, (
            f"Forbidden symbol '{symbol}' found in orchestrator live code — "
            f"violates INV-2 / §VIII"
        )


# ── Group C: No canonical ID construction ─────────────────────────────────────

class TestNoCanonicalIDConstruction:
    """The orchestrator must not construct canonical ID strings.

    Permitted: "CPS" as a lane name literal (e.g., lane == "CPS").
    Prohibited: Any construction of a CPS_ prefixed identifier
                (e.g., f"CPS_{hash_value}", "CPS_" + computed_value).
    """

    def test_no_cps_prefix_fstring_construction(self):
        """f"CPS_... construction is prohibited."""
        code = _code_text()
        # Match f-string or string concat patterns that build CPS_ IDs.
        pattern = r'f["\']CPS_'
        matches = re.findall(pattern, code)
        assert not matches, (
            f"Found canonical ID construction pattern in orchestrator: {matches}"
        )

    def test_no_cps_underscore_concatenation(self):
        """String concatenation producing CPS_ prefix is prohibited."""
        code = _code_text()
        pattern = r'"CPS_"\s*\+'
        matches = re.findall(pattern, code)
        assert not matches, (
            f"Found 'CPS_' + concatenation in orchestrator: {matches}"
        )

    def test_cps_lane_literal_is_permitted(self):
        """Sanity: the 'CPS' lane name literal must be present (dedup gate)."""
        # _commit_canonical_object checks: if lane == "CPS"
        src = _source()
        assert '"CPS"' in src or "'CPS'" in src, (
            "Expected 'CPS' lane literal not found — test setup error"
        )

    def test_no_canonical_id_field_assignment(self):
        """orchestrator must not assign to canonicalId fields."""
        code = _code_text()
        # Catch patterns like obj["canonicalId"] = ... or obj['canonicalId'] =
        pattern = r'(?:obj|canonical_obj|record)\s*\[["\']canonicalId["\']\]\s*='
        matches = re.findall(pattern, code)
        assert not matches, (
            f"Found canonicalId field assignment in orchestrator: {matches}"
        )


# ── Group D: No fingerprint derivation ────────────────────────────────────────

class TestNoFingerprintDerivation:
    """The word 'fingerprint' must not appear in orchestrator live code.

    Fingerprint derivation is exclusively PSTA's authority (§XIV, INV-2).
    Permitted occurrences: comments and docstrings only (already excluded
    by _code_lines()).
    """

    def test_fingerprint_absent_from_live_code(self):
        code = _code_text()
        assert "fingerprint" not in code.lower(), (
            "The word 'fingerprint' appears in orchestrator live code — "
            "violates INV-2. Fingerprint derivation is PSTA's sole authority."
        )

    def test_no_digest_calls(self):
        """Generic .digest() calls are prohibited (hash output access)."""
        code = _code_text()
        assert ".digest()" not in code, (
            "Found .digest() call in orchestrator — violates INV-2"
        )

    def test_no_encode_for_hashing_pattern(self):
        """str.encode() followed by a hash call is a fingerprint pattern."""
        code = _code_text()
        # Look for .encode( immediately followed (within 3 lines) by a
        # hash-like call — simplified: just check .encode() is absent unless
        # it appears in a non-identity context.
        # Orchestrator has no legitimate use of .encode() for identity.
        encode_matches = re.findall(r'\.encode\s*\(', code)
        assert not encode_matches, (
            f"Found .encode() in orchestrator live code — potential hash "
            f"input preparation, violates INV-2: {encode_matches}"
        )


# ── Group E: INV-2 docstring compliance marker ────────────────────────────────

class TestINV2DocstringPresence:
    """The module-level docstring must explicitly document INV-2 compliance."""

    def test_inv2_in_module_docstring(self):
        docstring = orch_module.__doc__ or ""
        assert "INV-2" in docstring, (
            "Module docstring does not reference INV-2 — compliance marker "
            "is required to make the prohibition explicit."
        )

    def test_inv2_docstring_mentions_no_hashlib(self):
        docstring = orch_module.__doc__ or ""
        assert "hashlib" in docstring.lower() or "fingerprint" in docstring.lower(), (
            "INV-2 module docstring must mention 'hashlib' or 'fingerprint' "
            "to be a substantive compliance statement."
        )

    def test_orchestrator_run_docstring_references_inv2(self):
        docstring = orch_module.orchestrator_run.__doc__ or ""
        assert "INV-2" in docstring, (
            "orchestrator_run docstring does not reference INV-2 — the "
            "public entry point must explicitly document identity prohibition."
        )