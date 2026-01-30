"""Tests for the explain command (cli.error.v0.1 JSON)."""

from pathlib import Path

import pytest

from a11y_assist.from_cli_error import (
    CliErrorValidationError,
    assist_from_cli_error,
    load_cli_error,
)

FIX = Path(__file__).parent / "fixtures"


class TestLoadCliError:
    """Tests for loading cli.error.v0.1 JSON files."""

    def test_load_valid_array_format(self):
        """Load valid JSON with array format for what/why/fix."""
        obj = load_cli_error(str(FIX / "cli_error_good.json"))
        assert obj["code"] == "PAY001"
        assert obj["id"] == "PAY.EXPORT.SFTP.AUTH"

    def test_load_valid_string_format(self):
        """Load valid JSON with string format for what/why/fix."""
        obj = load_cli_error(str(FIX / "cli_error_string_format.json"))
        assert obj["code"] == "CFG001"
        assert obj["what"] == "Configuration file missing"

    def test_load_missing_code_raises(self):
        """Missing code field raises validation error."""
        with pytest.raises(CliErrorValidationError) as exc_info:
            load_cli_error(str(FIX / "cli_error_missing_id.json"))
        assert "code" in str(exc_info.value.errors)


class TestAssistFromCliError:
    """Tests for generating assist from cli.error.v0.1."""

    def test_explain_from_valid_cli_error(self):
        """Generate high-confidence assist from valid JSON."""
        obj = load_cli_error(str(FIX / "cli_error_good.json"))
        res = assist_from_cli_error(obj)
        assert res.confidence == "High"
        assert res.anchored_id == "PAY.EXPORT.SFTP.AUTH"
        assert res.plan
        assert len(res.plan) >= 1

    def test_explain_uses_code_as_fallback_id(self):
        """Use code field as fallback when id is not present."""
        obj = load_cli_error(str(FIX / "cli_error_string_format.json"))
        res = assist_from_cli_error(obj)
        assert res.anchored_id == "CFG001"

    def test_plan_contains_fix_steps(self):
        """Plan is built from fix field."""
        obj = load_cli_error(str(FIX / "cli_error_good.json"))
        res = assist_from_cli_error(obj)
        assert "Verify credentials." in res.plan

    def test_safe_commands_extracted(self):
        """SAFE commands extracted from fix with --dry-run."""
        obj = load_cli_error(str(FIX / "cli_error_good.json"))
        res = assist_from_cli_error(obj)
        # Should find the dry-run command
        dry_run_cmds = [c for c in res.next_safe_commands if "--dry-run" in c]
        assert len(dry_run_cmds) >= 1

    def test_notes_include_original_title(self):
        """Notes include the original title."""
        obj = load_cli_error(str(FIX / "cli_error_good.json"))
        res = assist_from_cli_error(obj)
        assert any("Payment export failed" in n for n in res.notes)
