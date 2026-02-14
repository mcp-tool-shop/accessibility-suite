
import json
import os
from unittest.mock import patch, mock_open
import pytest
from a11y_ci.mcp_payload import build_mcp_payload, sha256_file
from a11y_ci.gate import GateResult
from a11y_ci.scorecard import Scorecard
from a11y_ci.help import HelpInfo

def test_sha256_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world", encoding="utf-8")
    
    # known hash for "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert sha256_file(str(f)) == expected
    
    assert sha256_file("nonexistent") is None

@patch.dict(os.environ, {
    "GITHUB_REPOSITORY": "org/repo",
    "GITHUB_SHA": "sha123",
    "GITHUB_WORKFLOW": "wf",
    "GITHUB_RUN_ID": "456"
})
def test_build_mcp_payload():
    # Setup dependencies
    mock_findings = [
        {"id": "A11Y.IMG.ALT", "severity": "serious", "message": "Missing alt", "location": "img.png"},
        {"id": "OTHER.RULE", "severity": "minor", "message": "Other", "location": "other.js"}
    ]
    scorecard = Scorecard(raw={}, findings=mock_findings)
    
    result = GateResult(
        ok=False,
        reasons=["Found errors"],
        current_blocking_ids=["A11Y.IMG.ALT"], # Only one is blocking
        new_blocking_ids=[],
        current_counts={"serious": 1, "minor": 1},
        baseline_counts={"serious": 0, "minor": 1}, # serious increased
        new_fingerprints=[]
    )
    
    # Mock artifacts
    with patch("a11y_ci.mcp_payload.sha256_file", return_value="deadbeef"):
        payload = build_mcp_payload(
            result, 
            scorecard, 
            "serious", 
            [{"kind": "scorecard", "path": "path/to/sc.json"}]
        )
    
    # Assertions
    assert payload["tool"] == "a11y-ci"
    assert payload["repo"] == "org/repo"
    assert payload["commit_sha"] == "sha123"
    
    # Gate info
    assert payload["gate"]["decision"] == "fail"
    assert payload["gate"]["fail_on"] == "serious"
    assert payload["gate"]["deltas"]["serious"] == 1
    assert "minor" not in payload["gate"]["deltas"] # No change
    
    # Blocking details
    assert len(payload["blocking"]) == 1
    blk = payload["blocking"][0]
    assert blk["id"] == "A11Y.IMG.ALT"
    assert "help_url" in blk
    assert "help_hint" in blk
    assert blk["severity"] == "serious"
    
    # Artifacts
    assert len(payload["artifacts"]) == 1
    assert payload["artifacts"][0]["sha256"] == "deadbeef"
    assert payload["artifacts"][0]["kind"] == "scorecard"
