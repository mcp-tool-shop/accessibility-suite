
"""Tests for MCP CLI integration."""
import json
from pathlib import Path
from click.testing import CliRunner
from a11y_ci.cli import main

FIXTURES = Path(__file__).parent / "fixtures"

def test_emit_mcp_output(tmp_path):
    """Test standard MCP file output generation."""
    mcp_out = tmp_path / "evidence.json"
    runner = CliRunner()
    
    # Run with --mcp-out
    # Using fail fixture to ensure it works on failure too
    result = runner.invoke(main, [
        "gate",
        "--current", str(FIXTURES / "current_fail.json"),
        "--fail-on", "serious",
        "--mcp-out", str(mcp_out)
    ])
    
    # Should still fail
    assert result.exit_code == 3
    
    # But file should exist
    assert mcp_out.exists()
    
    data = json.loads(mcp_out.read_text("utf-8"))
    assert data["tool"] == "a11y-ci"
    assert data["gate"]["decision"] == "fail"
    # The fixture "current_fail.json" likely has findings, ensure blocking is populated
    # (Gate logic determines blocking based on severity)
    # If fail_on=serious, and current_fail has serious findings...
    assert len(data["blocking"]) > 0

def test_emit_mcp_stdout():
    """Test --emit-mcp printing to stdout.""" 
    runner = CliRunner()
    result = runner.invoke(main, [
        "gate",
        "--current", str(FIXTURES / "current_fail.json"),
        "--emit-mcp" 
    ])
    assert result.exit_code == 3
    # Check that output contains JSON-like content for MCP
    # Output also contains report text, so we adjust expectations
    assert '"tool": "a11y-ci"' in result.output
    # And normal report
    assert "[ERROR]" in result.output

def test_mcp_with_json_output(tmp_path):
    """Test valid output when --format json and --emit-mcp are used."""
    mcp_out = tmp_path / "evidence.json"
    runner = CliRunner()
    
    result = runner.invoke(main, [
        "gate",
        "--current", str(FIXTURES / "current_fail.json"),
        "--format", "json",
        "--mcp-out", str(mcp_out)
    ])
    
    assert result.exit_code == 3
    assert mcp_out.exists()
    
    # Stdout should match JSON report schema
    # mcp_out should match MCP schema
    
    report_json = json.loads(result.output)
    mcp_json = json.loads(mcp_out.read_text("utf-8"))
    
    assert "blocking" in report_json
    assert "blocking" in mcp_json
    
    # They are different structures (Report vs Payload)
    # Payload has run_id, tool_version, etc at top level
    assert "tool_version" in mcp_json
    # Report has them in 'meta' usually? Or structure defined in report.py
