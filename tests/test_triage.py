"""Tests for the triage command (raw text parsing)."""

from pathlib import Path

import pytest

from a11y_assist.parse_raw import extract_id, parse_raw, extract_blocks

FIX = Path(__file__).parent / "fixtures"


class TestExtractId:
    """Tests for extracting IDs from text."""

    def test_extract_id_from_parens(self):
        """Extract ID from (ID: ...) format."""
        text = "[ERROR] Something failed (ID: PAY.EXPORT.SFTP.AUTH)"
        assert extract_id(text) == "PAY.EXPORT.SFTP.AUTH"

    def test_extract_id_multiline(self):
        """Extract ID from multiline text."""
        text = "Some text\n[ERROR] Failed (ID: APP.CONFIG.MISSING)\nMore text"
        assert extract_id(text) == "APP.CONFIG.MISSING"

    def test_no_id_returns_none(self):
        """Return None when no ID found."""
        text = "ERROR: It failed"
        assert extract_id(text) is None


class TestExtractBlocks:
    """Tests for extracting What/Why/Fix blocks."""

    def test_extract_all_blocks(self):
        """Extract all three block types."""
        lines = [
            "[ERROR] Failed",
            "",
            "What:",
            "  Something went wrong.",
            "",
            "Why:",
            "  Because reasons.",
            "",
            "Fix:",
            "  Do this.",
            "  Then this.",
        ]
        blocks = extract_blocks(lines)
        assert blocks["What:"] == ["Something went wrong."]
        assert blocks["Why:"] == ["Because reasons."]
        assert blocks["Fix:"] == ["Do this.", "Then this."]

    def test_missing_blocks_return_empty(self):
        """Missing blocks return empty lists."""
        lines = ["ERROR: It failed", "Please try again"]
        blocks = extract_blocks(lines)
        assert blocks["What:"] == []
        assert blocks["Why:"] == []
        assert blocks["Fix:"] == []


class TestParseRaw:
    """Tests for full raw text parsing."""

    def test_parse_raw_finds_id_and_fix(self):
        """Parse raw text with ID and Fix blocks."""
        text = (FIX / "raw_good.txt").read_text(encoding="utf-8")
        err_id, status, blocks = parse_raw(text)
        assert err_id == "PAY.EXPORT.SFTP.AUTH"
        assert status == "ERROR"
        assert "Fix:" in blocks
        assert len(blocks["Fix:"]) >= 1

    def test_parse_raw_no_id(self):
        """Parse raw text without ID."""
        text = (FIX / "raw_no_id.txt").read_text(encoding="utf-8")
        err_id, status, blocks = parse_raw(text)
        assert err_id is None
        assert status == "UNKNOWN"  # No [ERROR] prefix

    def test_parse_status_detection(self):
        """Detect status from [OK]/[WARN]/[ERROR] prefix."""
        text = "[WARN] Something might be wrong"
        err_id, status, blocks = parse_raw(text)
        assert status == "WARN"
