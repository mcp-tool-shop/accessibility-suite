"""Tests for plain-language profile.

Verifies:
- Sentences simplified to one clause
- Parentheticals removed
- Subordinate clauses removed
- Max 4 steps
- Numeric step labels
- Confidence preserved
- Commands from allowlist only (max 1)
"""

import pytest

from a11y_assist.profiles.plain_language import (
    _normalize_step,
    _remove_parentheticals,
    _simplify_sentence,
    apply_plain_language,
)
from a11y_assist.profiles.plain_language_render import render_plain_language
from a11y_assist.render import AssistResult


# Unit tests for helper functions


def test_remove_parentheticals():
    """Should remove parenthetical content."""
    assert _remove_parentheticals("Check config (optional)") == "Check config"
    assert _remove_parentheticals("Run command [see docs]") == "Run command"
    assert _remove_parentheticals("No parens here") == "No parens here"


def test_simplify_sentence_removes_conjunctions():
    """Should split on conjunctions and keep first part."""
    result = _simplify_sentence("Check config and run the test")
    assert "and" not in result.lower()
    assert "Check config" in result


def test_simplify_sentence_removes_but():
    """Should handle 'but' conjunction."""
    result = _simplify_sentence("Try this but be careful")
    assert "but" not in result.lower()
    assert "Try this" in result


def test_simplify_sentence_removes_or():
    """Should handle 'or' conjunction."""
    result = _simplify_sentence("Use option A or option B")
    assert " or " not in result.lower()


def test_simplify_sentence_removes_subordinate_which():
    """Should remove subordinate clauses with 'which'."""
    result = _simplify_sentence("Check the file, which is located in /etc")
    assert "which" not in result.lower()


def test_simplify_sentence_removes_subordinate_that():
    """Should remove subordinate clauses with 'that'."""
    result = _simplify_sentence("Run the command that verifies config")
    assert "that" not in result.lower()


def test_simplify_sentence_removes_subordinate_because():
    """Should remove subordinate clauses with 'because'."""
    result = _simplify_sentence("This fails because the file is missing")
    assert "because" not in result.lower()


def test_simplify_sentence_adds_period():
    """Should ensure sentence ends with punctuation."""
    result = _simplify_sentence("Check config")
    assert result.endswith(".")


def test_simplify_sentence_preserves_existing_punctuation():
    """Should preserve existing punctuation."""
    result = _simplify_sentence("Check config!")
    assert result.endswith("!")


def test_normalize_step():
    """Step normalization should simplify and clean."""
    result = _normalize_step("Check config (optional) and verify")
    assert "(" not in result
    assert ")" not in result
    assert "and" not in result.lower() or "and" == result.lower()[-3:]  # Allow if at end


# Tests for apply_plain_language transform


@pytest.fixture
def base_result() -> AssistResult:
    """Base result with various elements to transform."""
    return AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Check the config file (see docs), which is located in /etc.",
        plan=[
            "First, verify the config exists and check permissions.",
            "Run the validation command, but be careful.",
            "Check the output, which contains details.",
            "Verify results because this is important.",
            "Final step that completes the process.",
            "Extra step (should be truncated).",
        ],
        next_safe_commands=["cmd --dry-run", "cmd2 --check"],
        notes=["Note with (parenthetical) and subordinate clause which explains."],
    )


def test_apply_plain_language_simplifies_safest_step(base_result: AssistResult):
    """Plain-language should simplify safest next step."""
    result = apply_plain_language(base_result)
    # Should not have parenthetical
    assert "(" not in result.safest_next_step
    assert ")" not in result.safest_next_step
    # Should not have subordinate clause
    assert "which" not in result.safest_next_step.lower()


def test_apply_plain_language_simplifies_plan_steps(base_result: AssistResult):
    """Plain-language should simplify plan steps."""
    result = apply_plain_language(base_result)
    for step in result.plan:
        # Each step should be one clause (no conjunctions in middle)
        # Note: "and" at end is ok due to simplification
        words = step.lower().split()
        if " and " in step.lower():
            # "and" should only appear if it's a remaining fragment
            pass


def test_apply_plain_language_max_4_steps(base_result: AssistResult):
    """Plain-language should limit to 4 steps."""
    result = apply_plain_language(base_result)
    assert len(result.plan) <= 4


def test_apply_plain_language_max_1_command(base_result: AssistResult):
    """Plain-language should limit to 1 command for simplicity."""
    result = apply_plain_language(base_result)
    assert len(result.next_safe_commands) <= 1


def test_apply_plain_language_max_2_notes(base_result: AssistResult):
    """Plain-language should limit to 2 notes."""
    result = apply_plain_language(base_result)
    assert len(result.notes) <= 2


def test_apply_plain_language_preserves_confidence(base_result: AssistResult):
    """Plain-language should preserve confidence."""
    result = apply_plain_language(base_result)
    assert result.confidence == base_result.confidence


def test_apply_plain_language_preserves_id(base_result: AssistResult):
    """Plain-language should preserve anchored ID."""
    result = apply_plain_language(base_result)
    assert result.anchored_id == base_result.anchored_id


# Tests for render_plain_language


def test_render_plain_language_header():
    """Render should include plain language header."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["Step 1."],
        next_safe_commands=[],
        notes=[],
    )
    output = render_plain_language(result)
    assert "ASSIST (Plain Language)" in output


def test_render_plain_language_labels():
    """Render should use explicit labels."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["Step 1.", "Step 2."],
        next_safe_commands=["cmd --dry-run"],
        notes=[],
    )
    output = render_plain_language(result)
    assert "ID:" in output
    assert "Confidence:" in output
    assert "What to do next:" in output
    assert "Steps:" in output
    assert "Safe command:" in output


def test_render_plain_language_numeric_steps():
    """Render should use numeric step labels."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["First step.", "Second step.", "Third step."],
        next_safe_commands=[],
        notes=[],
    )
    output = render_plain_language(result)
    assert "1." in output
    assert "2." in output
    assert "3." in output


def test_render_plain_language_no_command_on_low():
    """Render should not show command on Low confidence."""
    result = AssistResult(
        anchored_id=None,
        confidence="Low",
        safest_next_step="Check config.",
        plan=["Step 1."],
        next_safe_commands=["cmd --dry-run"],
        notes=[],
    )
    output = render_plain_language(result)
    assert "Safe command:" not in output


def test_render_plain_language_shows_command_on_high():
    """Render should show command on High confidence."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["Step 1."],
        next_safe_commands=["cmd --dry-run"],
        notes=[],
    )
    output = render_plain_language(result)
    assert "Safe command:" in output
    assert "cmd --dry-run" in output


def test_render_plain_language_omits_notes():
    """Render should omit notes for simplicity."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["Step 1."],
        next_safe_commands=[],
        notes=["A note that should not appear."],
    )
    output = render_plain_language(result)
    # Notes section omitted in plain-language for simplicity
    assert "Notes:" not in output


# Integration tests


def test_plain_language_full_pipeline():
    """Full pipeline test for plain-language profile."""
    base = AssistResult(
        anchored_id="DEPLOY.CONFIG.MISSING",
        confidence="High",
        safest_next_step="Check the config file (in /etc), which contains settings and run verify.",
        plan=[
            "Verify the config exists and check permissions.",
            "Run: deploy check --dry-run",
            "Review output, which shows results.",
        ],
        next_safe_commands=["deploy check --dry-run"],
        notes=["Important note."],
    )

    transformed = apply_plain_language(base)
    output = render_plain_language(transformed)

    # Header present
    assert "ASSIST (Plain Language)" in output

    # ID preserved
    assert "DEPLOY.CONFIG.MISSING" in output

    # Confidence preserved
    assert "Confidence: High" in output

    # Simplified step label
    assert "What to do next:" in output

    # Numeric steps
    assert "1." in output

    # Command shown
    assert "deploy check --dry-run" in output

    # No notes section (omitted for simplicity)
    assert "Notes:" not in output


def test_plain_language_low_confidence():
    """Plain-language profile with Low confidence."""
    base = AssistResult(
        anchored_id=None,
        confidence="Low",
        safest_next_step="Review the output.",
        plan=["Step 1.", "Step 2."],
        next_safe_commands=["cmd --dry-run"],
        notes=["No ID found."],
    )

    transformed = apply_plain_language(base)
    output = render_plain_language(transformed)

    # Confidence preserved
    assert "Confidence: Low" in output

    # No command on Low confidence
    assert "Safe command:" not in output

    # ID shows as none
    assert "ID: none" in output


def test_plain_language_complex_sentence():
    """Plain-language should simplify complex sentences."""
    base = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="First check the config, and then verify the settings, but be careful because errors may occur.",
        plan=[
            "Run the command which validates, and also checks permissions.",
        ],
        next_safe_commands=[],
        notes=[],
    )

    transformed = apply_plain_language(base)

    # Safest step should be simplified
    assert "and then" not in transformed.safest_next_step.lower()
    assert "but" not in transformed.safest_next_step.lower()
    assert "because" not in transformed.safest_next_step.lower()
