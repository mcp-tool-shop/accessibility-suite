
import json
from datetime import date, timedelta
from pathlib import Path
import pytest
from a11y_ci.allowlist import Allowlist

def test_allowlist_loading_and_filtering(tmp_path):
    """Test loading allowlist with IDs and fingerprints."""
    # Future date
    future = (date.today() + timedelta(days=30)).isoformat()
    
    data = {
        "version": "1",
        "allow": [
            {
                "finding_id": "ID.1",
                "expires": future,
                "reason": "Tracking ticket #123",
                "owner": "TeamA"
            },
            {
                "fingerprint": "a" * 64,
                "expires": future,
                "reason": "Specific instance waiver",
                "owner": "TeamB"
            }
        ]
    }
    
    p = tmp_path / "allow.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    
    al = Allowlist.load(str(p))
    
    # Check suppression logic
    assert al.is_suppressed({"id": "ID.1"})
    assert not al.is_suppressed({"id": "ID.2"})
    assert al.is_suppressed({"fingerprint": "a" * 64})
    assert not al.is_suppressed({"fingerprint": "b" * 64})

def test_allowlist_expiry(tmp_path):
    """Test that expired entries are detected."""
    past = (date.today() - timedelta(days=1)).isoformat()
    future = (date.today() + timedelta(days=1)).isoformat()
    
    data = {
        "version": "1",
        "allow": [
            {
                "id": "EXPIRED",
                "expires": past,
                "reason": "Old waiver reason",
                "owner": "TeamOwner"
            },
            {
                "id": "VALID",
                "expires": future,
                "reason": "New waiver reason",
                "owner": "TeamOwner"
            }
        ]
    }
    
    p = tmp_path / "allow.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    
    al = Allowlist.load(str(p))
    expired = al.expired_entries()
    
    assert len(expired) == 1
    assert expired[0].id == "EXPIRED"
    
    active = al.active_entries()
    assert len(active.entries) == 1
    assert active.entries[0].id == "VALID"

def test_allowlist_legacy_support(tmp_path):
    """Test legacy format support (finding_id without id)."""
    future = (date.today() + timedelta(days=30)).isoformat()
    data = {
        "version": "1",
        "allow": [
            {
                "finding_id": "LEGACY",
                "expires": future,
                "reason": "Old format",
                "owner": "Arch"
            }
        ]
    }
    p = tmp_path / "allow.json"
    p.write_text(json.dumps(data))
    
    al = Allowlist.load(str(p))
    assert al.entries[0].id == "LEGACY"
    assert al.entries[0].kind == "id"
