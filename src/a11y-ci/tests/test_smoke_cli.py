"""Smoke tests for a11y-ci CLI."""

from pathlib import Path
from click.testing import CliRunner
from a11y_ci.cli import main

FIXTURES = Path(__file__).parent / "fixtures"

def test_gate_pass_smoke():
    """Gate should pass with a clean scorecard (exit 0)."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "gate",
        "--current", str(FIXTURES / "current_ok.json"),
        "--fail-on", "serious"
    ])
    assert result.exit_code == 0
    assert "[OK]" in result.output

def test_gate_fail_smoke():
    """Gate should fail with findings above threshold (exit 3)."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "gate",
        "--current", str(FIXTURES / "current_fail.json"),
        "--fail-on", "serious"
    ])
    assert result.exit_code == 3
    assert "[ERROR]" in result.output
    # Ensure failure reason is clear
    assert "Current run has" in result.output

def test_gate_malformed_input():
    """Gate should fail gracefully on malformed/missing input (exit 2)."""
    runner = CliRunner()
    result = runner.invoke(main, [
        "gate",
        "--current", "non_existent_file.json"
    ])
    assert result.exit_code == 2
    assert "Invalid value for '--current'" in result.output
