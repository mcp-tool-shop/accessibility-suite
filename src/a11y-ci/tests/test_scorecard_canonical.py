
import json
from dataclasses import replace
from pathlib import Path

import pytest
from a11y_ci.scorecard import Scorecard, compute_fingerprint, normalize_severity

def test_fingerprint_stability():
    """Fingerprint should be stable for identical content."""
    f1 = {"id": "A", "message": "msg", "location": {"path": "p"}}
    f2 = {"id": "A", "message": "msg", "location": {"path": "p"}}
    # Different ordering in dict shouldn't matter due to sort_keys=True
    f3 = {"location": {"path": "p"}, "message": "msg", "id": "A"}
    
    fp1 = compute_fingerprint(f1)
    fp2 = compute_fingerprint(f2)
    fp3 = compute_fingerprint(f3)
    
    assert fp1 == fp2 == fp3
    assert len(fp1) == 64  # SHA256 hex digest

def test_canonical_sort_order():
    """Findings should be sorted by Severity (desc), then ID, then Fingerprint."""
    # S: serious, M: minor
    findings = [
        {"id": "B", "severity": "minor", "message": "msg1"},
        {"id": "A", "severity": "serious", "message": "msg2"},
        {"id": "C", "severity": "minor", "message": "msg3"},
    ]
    
    sc = Scorecard(raw={}, findings=findings).canonicalize()
    
    # Expected order:
    # 1. A (serious)
    # 2. B (minor)
    # 3. C (minor)
    
    assert sc.findings[0]["id"] == "A"
    assert sc.findings[1]["id"] == "B"
    assert sc.findings[2]["id"] == "C"

def test_deduplication():
    """Duplicate findings (same fingerprint) should collapse to one."""
    f = {"id": "A", "severity": "serious", "message": "msg", "location": {"path": "p"}}
    findings = [f, f.copy(), f.copy()]  # 3 identical
    
    sc = Scorecard(raw={}, findings=findings).canonicalize()
    
    # Should be 1 finding
    assert len(sc.findings) == 1
    assert sc.findings[0]["id"] == "A"

def test_dedupe_preserves_highest_severity():
    """If fingerprints collide (forced), keep highest severity."""
    # This scenario is unlikely with auto-fingerprinting unless content matches,
    # but if manually provided or if collision happens:
    
    # Manually force same fingerprint but different severity to test conflict resolution logic
    fp = "same-hash"
    f1 = {"id": "A", "severity": "minor", "fingerprint": fp}
    f2 = {"id": "A", "severity": "critical", "fingerprint": fp} # Critical should win
    
    findings = [f1, f2]
    sc = Scorecard(raw={}, findings=findings).canonicalize()
    
    assert len(sc.findings) == 1
    assert sc.findings[0]["severity"] == "critical"

def test_load_canonicalizes_automatically(tmp_path):
    """Loading a scorecard should automatically canonicalize findings."""
    data = {
        "meta": {"tool": "test", "version": "1"},
        "findings": [
            {"id": "B", "severity": "minor", "message": "m"},
            {"id": "A", "severity": "serious", "message": "m"},
        ]
    }
    p = tmp_path / "test.json"
    p.write_text(json.dumps(data))
    
    sc = Scorecard.load(str(p))
    
    # Check sort order: A (serious) then B (minor)
    assert sc.findings[0]["id"] == "A"
    assert sc.findings[1]["id"] == "B"
    # Check fingerprint added
    assert "fingerprint" in sc.findings[0]
