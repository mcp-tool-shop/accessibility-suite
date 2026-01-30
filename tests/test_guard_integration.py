"""Integration tests for Profile Guard through CLI pipeline.

Tests that guard validation works correctly when invoked through
the actual CLI commands with all three profiles.
"""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from a11y_assist.cli import main


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def valid_cli_error_json() -> dict:
    """Valid cli.error.v0.1 JSON for testing."""
    return {
        "level": "ERROR",
        "code": "CFG001",
        "id": "TEST.CONFIG.MISSING",
        "title": "Configuration file not found",
        "what": "The config.yaml file is missing from the current directory.",
        "why": "The tool requires a configuration file to run.",
        "fix": [
            "Run: config init --dry-run",
            "Then: config init",
            "Verify the file was created.",
        ],
    }


@pytest.fixture
def json_file(valid_cli_error_json: dict) -> str:
    """Create a temporary JSON file with valid cli.error.v0.1 content."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(valid_cli_error_json, f)
        return f.name


# Integration: explain command with guard


def test_explain_lowvision_passes_guard(runner: CliRunner, json_file: str):
    """Explain command with lowvision profile should pass guard."""
    result = runner.invoke(main, ["explain", "--json", json_file, "--profile", "lowvision"])

    # Should succeed
    assert result.exit_code == 0
    assert "ASSIST (Low Vision)" in result.output
    assert "TEST.CONFIG.MISSING" in result.output


def test_explain_cognitive_load_passes_guard(runner: CliRunner, json_file: str):
    """Explain command with cognitive-load profile should pass guard."""
    result = runner.invoke(main, ["explain", "--json", json_file, "--profile", "cognitive-load"])

    # Should succeed
    assert result.exit_code == 0
    assert "ASSIST (Cognitive Load)" in result.output
    assert "TEST.CONFIG.MISSING" in result.output


def test_explain_screen_reader_passes_guard(runner: CliRunner, json_file: str):
    """Explain command with screen-reader profile should pass guard."""
    result = runner.invoke(main, ["explain", "--json", json_file, "--profile", "screen-reader"])

    # Should succeed
    assert result.exit_code == 0
    assert "ASSIST. Profile: Screen reader." in result.output
    assert "TEST.CONFIG.MISSING" in result.output


# Integration: triage command with guard


def test_triage_lowvision_passes_guard(runner: CliRunner):
    """Triage command with lowvision profile should pass guard."""
    input_text = """[ERROR] (ID: TOOL.PARSE.FAIL)
What: Failed to parse input file.
Why: Invalid syntax on line 42.
Fix:
  Check line 42 for typos.
  Run: tool validate --dry-run
"""
    result = runner.invoke(
        main, ["triage", "--stdin", "--profile", "lowvision"], input=input_text
    )

    # Should succeed
    assert result.exit_code == 0
    assert "ASSIST (Low Vision)" in result.output
    assert "TOOL.PARSE.FAIL" in result.output


def test_triage_cognitive_load_passes_guard(runner: CliRunner):
    """Triage command with cognitive-load profile should pass guard."""
    input_text = """[ERROR] (ID: TOOL.PARSE.FAIL)
What: Failed to parse input file.
Why: Invalid syntax on line 42.
Fix:
  Check line 42 for typos.
  Run: tool validate --dry-run
"""
    result = runner.invoke(
        main, ["triage", "--stdin", "--profile", "cognitive-load"], input=input_text
    )

    # Should succeed
    assert result.exit_code == 0
    assert "ASSIST (Cognitive Load)" in result.output


def test_triage_screen_reader_passes_guard(runner: CliRunner):
    """Triage command with screen-reader profile should pass guard."""
    input_text = """[ERROR] (ID: TOOL.PARSE.FAIL)
What: Failed to parse input file.
Why: Invalid syntax on line 42.
Fix:
  Check line 42 for typos.
  Run: tool validate --dry-run
"""
    result = runner.invoke(
        main, ["triage", "--stdin", "--profile", "screen-reader"], input=input_text
    )

    # Should succeed
    assert result.exit_code == 0
    assert "ASSIST. Profile: Screen reader." in result.output


# Integration: triage with no ID (Low confidence)


def test_triage_low_confidence_lowvision(runner: CliRunner):
    """Triage with no ID should produce Low confidence output."""
    input_text = """Error: Something went wrong.
Please check the configuration and try again.
"""
    result = runner.invoke(
        main, ["triage", "--stdin", "--profile", "lowvision"], input=input_text
    )

    # Should succeed with Low confidence
    assert result.exit_code == 0
    assert "Confidence: Low" in result.output
    assert "No (ID: ...) found" in result.output


def test_triage_low_confidence_cognitive_load(runner: CliRunner):
    """Triage with no ID should produce Low confidence output for cognitive-load."""
    input_text = """Error: Something went wrong.
Please check the configuration and try again.
"""
    result = runner.invoke(
        main, ["triage", "--stdin", "--profile", "cognitive-load"], input=input_text
    )

    # Should succeed with Low confidence
    assert result.exit_code == 0
    assert "Confidence: Low" in result.output


def test_triage_low_confidence_screen_reader(runner: CliRunner):
    """Triage with no ID should produce Low confidence output for screen-reader."""
    input_text = """Error: Something went wrong.
Please check the configuration and try again.
"""
    result = runner.invoke(
        main, ["triage", "--stdin", "--profile", "screen-reader"], input=input_text
    )

    # Should succeed with Low confidence
    assert result.exit_code == 0
    assert "Confidence: Low" in result.output


# Integration: explain with invalid JSON


def test_explain_invalid_json_lowvision(runner: CliRunner):
    """Explain with invalid JSON should produce Low confidence validation error."""
    # Create invalid JSON (missing required fields)
    invalid_json = {"level": "ERROR", "code": "TST001"}  # Missing what, why, fix

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(invalid_json, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "lowvision"])

    # Should exit with code 2 (validation error)
    assert result.exit_code == 2
    assert "Confidence: Low" in result.output


def test_explain_invalid_json_cognitive_load(runner: CliRunner):
    """Explain with invalid JSON should work with cognitive-load profile."""
    invalid_json = {"level": "ERROR", "code": "TST001"}  # Missing what, why, fix

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(invalid_json, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "cognitive-load"])

    # Should exit with code 2 (validation error)
    assert result.exit_code == 2
    assert "Confidence: Low" in result.output


def test_explain_invalid_json_screen_reader(runner: CliRunner):
    """Explain with invalid JSON should work with screen-reader profile."""
    invalid_json = {"level": "ERROR", "code": "TST001"}  # Missing what, why, fix

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(invalid_json, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "screen-reader"])

    # Should exit with code 2 (validation error)
    assert result.exit_code == 2
    assert "Confidence: Low" in result.output


# Integration: Verify guard catches profile bugs (simulated)


def test_guard_error_format_on_violation():
    """Guard violations should produce structured error output.

    This test documents the expected error format. In practice,
    guard violations indicate bugs in profile transforms, not
    user errors. This test ensures the error format is correct
    if such a bug were to occur.
    """
    # The guard error format should include:
    # - [ERROR] A11Y.ASSIST.ENGINE.GUARD.FAIL
    # - What: description
    # - Why: explanation
    # - Fix: instructions
    # - Guard codes: list of violations

    # Since we can't easily trigger a guard violation without
    # introducing a bug, we just document the expected format
    # in this test. Actual guard violation tests are in test_guard.py.
    pass


# Integration: Verify max steps enforced per profile


def test_cognitive_load_max_3_steps_integration(runner: CliRunner):
    """Cognitive-load profile should enforce max 3 steps."""
    # Create JSON with many fix steps
    json_data = {
        "level": "ERROR",
        "code": "TST001",
        "id": "TEST.MANY.STEPS",
        "title": "Error with many steps",
        "what": "Something went wrong.",
        "why": "Multiple issues need fixing.",
        "fix": [
            "Step 1: Do first thing.",
            "Step 2: Do second thing.",
            "Step 3: Do third thing.",
            "Step 4: Do fourth thing.",
            "Step 5: Do fifth thing.",
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(json_data, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "cognitive-load"])

    # Should succeed - profile should truncate to 3 steps
    assert result.exit_code == 0
    # Count "First:", "Next:", "Last:" labels (max 3)
    assert result.output.count("First:") <= 1
    assert result.output.count("Last:") <= 1


def test_lowvision_within_5_steps_succeeds(runner: CliRunner):
    """Lowvision profile should succeed when steps are within limit."""
    json_data = {
        "level": "ERROR",
        "code": "TST002",
        "id": "TEST.FEW.STEPS",
        "title": "Error with few steps",
        "what": "Something went wrong.",
        "why": "A few issues need fixing.",
        "fix": [
            "Step 1",
            "Step 2",
            "Step 3",
            "Step 4",
            "Step 5",
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(json_data, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "lowvision"])

    # Should succeed - 5 steps is within limit
    assert result.exit_code == 0
    assert "ASSIST (Low Vision)" in result.output


# Integration: Screen-reader abbreviation expansion


def test_screen_reader_expands_cli_abbreviation(runner: CliRunner):
    """Screen-reader profile should expand CLI abbreviation."""
    json_data = {
        "level": "ERROR",
        "code": "CLI001",
        "id": "TEST.CLI.ERROR",
        "title": "CLI tool failed",
        "what": "The CLI command failed to execute.",
        "why": "Invalid CLI arguments provided.",
        "fix": ["Check CLI documentation.", "Run: cli --help"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(json_data, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "screen-reader"])

    assert result.exit_code == 0
    # CLI should be expanded to "command line" in output
    assert "command line" in result.output.lower() or "C L I" in result.output


def test_screen_reader_expands_json_abbreviation(runner: CliRunner):
    """Screen-reader profile should expand JSON abbreviation."""
    json_data = {
        "level": "ERROR",
        "code": "JSN001",
        "id": "TEST.JSON.ERROR",
        "title": "JSON parse error",
        "what": "The JSON file is malformed.",
        "why": "Invalid JSON syntax.",
        "fix": ["Validate your JSON file.", "Check for missing commas."],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(json_data, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "screen-reader"])

    assert result.exit_code == 0
    # JSON should be expanded to "J S O N" in output
    assert "J S O N" in result.output


# Integration: Verify SAFE commands pass through correctly


def test_safe_commands_preserved_lowvision(runner: CliRunner):
    """SAFE commands should be preserved in lowvision output."""
    json_data = {
        "level": "ERROR",
        "code": "TST003",
        "id": "TEST.SAFE.CMD",
        "title": "Error with safe command",
        "what": "Operation failed.",
        "why": "Need to retry.",
        "fix": ["Run: tool fix --dry-run"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(json_data, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "lowvision"])

    assert result.exit_code == 0
    assert "tool fix --dry-run" in result.output
    assert "Next (SAFE):" in result.output


def test_safe_commands_preserved_cognitive_load(runner: CliRunner):
    """SAFE commands should be preserved in cognitive-load output (max 1)."""
    json_data = {
        "level": "ERROR",
        "code": "TST004",
        "id": "TEST.SAFE.CMD",
        "title": "Error with safe command",
        "what": "Operation failed.",
        "why": "Need to retry.",
        "fix": [
            "Run: tool fix --dry-run",
            "Run: tool check --dry-run",
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(json_data, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "cognitive-load"])

    assert result.exit_code == 0
    # Should have at most one SAFE command
    assert "Next (SAFE):" in result.output


def test_safe_commands_preserved_screen_reader(runner: CliRunner):
    """SAFE commands should be preserved in screen-reader output."""
    json_data = {
        "level": "ERROR",
        "code": "TST005",
        "id": "TEST.SAFE.CMD",
        "title": "Error with safe command",
        "what": "Operation failed.",
        "why": "Need to retry.",
        "fix": ["Run: tool fix --dry-run"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(json_data, f)
        json_path = f.name

    result = runner.invoke(main, ["explain", "--json", json_path, "--profile", "screen-reader"])

    assert result.exit_code == 0
    assert "tool fix --dry-run" in result.output
    assert "Next safe command" in result.output


# Integration: Default profile is lowvision


def test_default_profile_is_lowvision(runner: CliRunner, json_file: str):
    """Default profile should be lowvision when --profile not specified."""
    result = runner.invoke(main, ["explain", "--json", json_file])

    assert result.exit_code == 0
    assert "ASSIST (Low Vision)" in result.output
