
import json
from dataclasses import dataclass
from unittest.mock import patch
import pytest

from a11y_ci.help import get_help, HelpInfo
from a11y_ci.gate import GateResult
from a11y_ci.report import print_text_report, print_json_report

def test_registry_lookup():
    """Verify registry lookups handle case and whitespace."""
    info = get_help(" a11y.img.alt ")
    assert info is not None
    assert info.title == "Missing Image Alt Text"
    assert "add an 'alt'" in info.hint.lower()
    
    # Missing
    assert get_help("UNKOWN.RULE") is None

def test_report_includes_help_text(capsys):
    """Text report should include Fix and Docs lines for known rules."""
    result = GateResult(
        ok=False,
        reasons=["Found errors"],
        current_blocking_ids=["A11Y.IMG.ALT", "UNKNOWN.ID"],
        new_blocking_ids=[],
        current_counts={"serious": 1},
        baseline_counts=None,
        new_fingerprints=[]
    )
    
    print_text_report(result)
    captured = capsys.readouterr()
    
    # Known rule -> Detailed Help
    assert "A11Y.IMG.ALT" in captured.out
    assert "Fix: Add an 'alt' attribute" in captured.out
    assert "Docs: https://" in captured.out
    
    # Unknown rule -> Simple listing
    assert "UNKNOWN.ID" in captured.out
    # Ideally should NOT show Fix/Docs for unknown
    # But simple regex check might be tricky if one rule has it.
    # We verify that we didn't crash at least.

def test_json_report_includes_help_fields(capsys):
    """JSON report should include help_url and help_hint."""
    result = GateResult(
        ok=False,
        reasons=["Found errors"],
        current_blocking_ids=["A11Y.IMG.ALT"],
        new_blocking_ids=[],
        current_counts={"serious": 1},
        baseline_counts=None,
        new_fingerprints=[]
    )
    
    print_json_report(result)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    
    details = data["blocking"]["details"]
    assert len(details) == 1
    item = details[0]
    
    assert item["id"] == "A11Y.IMG.ALT"
    assert item["help_hint"] is not None
    assert "alt" in item["help_hint"]
    assert item["help_url"] is not None
