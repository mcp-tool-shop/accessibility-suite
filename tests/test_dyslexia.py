"""Tests for dyslexia profile.

Verifies:
- Parentheticals removed
- Visual references removed
- Symbolic emphasis removed
- Abbreviations expanded
- Max 5 steps
- Step numbering with "Step N:" prefix
- Confidence preserved
- Commands from allowlist only
"""

import pytest

from a11y_assist.profiles.dyslexia import (
    _expand_abbreviations,
    _normalize_step,
    _remove_parentheticals,
    _remove_symbolic_emphasis,
    _remove_visual_refs,
    apply_dyslexia,
)
from a11y_assist.profiles.dyslexia_render import render_dyslexia
from a11y_assist.render import AssistResult


# Unit tests for helper functions


def test_remove_parentheticals():
    """Should remove parenthetical content."""
    assert _remove_parentheticals("Check config (optional)") == "Check config"
    assert _remove_parentheticals("Run command [see docs]") == "Run command"
    assert _remove_parentheticals("No parens here") == "No parens here"


def test_remove_visual_refs():
    """Should remove visual navigation references."""
    assert _remove_visual_refs("See above for details") == "for details"
    assert _remove_visual_refs("Check below") == "Check"
    assert _remove_visual_refs("Click the left arrow") == "Click the"
    assert _remove_visual_refs("No visual refs") == "No visual refs"


def test_remove_symbolic_emphasis():
    """Should remove symbolic emphasis characters."""
    assert _remove_symbolic_emphasis("*important*") == "important"
    assert _remove_symbolic_emphasis("_underlined_") == "underlined"
    assert _remove_symbolic_emphasis("Step → Next") == "Step  Next"
    assert _remove_symbolic_emphasis("No symbols") == "No symbols"


def test_expand_abbreviations():
    """Should expand abbreviations once."""
    assert "command line" in _expand_abbreviations("Use the CLI tool")
    assert "I D" in _expand_abbreviations("Check the ID field")
    assert "J S O N" in _expand_abbreviations("Parse the JSON file")
    assert "A P I" in _expand_abbreviations("Call the API")
    assert "S F T P" in _expand_abbreviations("Upload via SFTP")


def test_normalize_step_removes_parentheticals():
    """Step normalization should remove parentheticals."""
    result = _normalize_step("Run the check (optional)")
    assert "(" not in result
    assert ")" not in result


def test_normalize_step_removes_visual_refs():
    """Step normalization should remove visual references."""
    result = _normalize_step("See above for more info")
    assert "above" not in result


def test_normalize_step_truncates_long_text():
    """Step normalization should truncate to 110 chars."""
    long_text = "A" * 150
    result = _normalize_step(long_text)
    assert len(result) <= 110
    assert result.endswith("...")


# Tests for apply_dyslexia transform


@pytest.fixture
def base_result() -> AssistResult:
    """Base result with various elements to transform."""
    return AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Check the CLI config (see docs above).",
        plan=[
            "Step 1: Verify the JSON file (optional).",
            "Step 2: Run the API check → next step.",
            "Step 3: See below for SFTP details.",
            "Step 4: Final check.",
            "Step 5: Done.",
            "Step 6: Extra step (should be truncated).",
        ],
        next_safe_commands=["cmd --dry-run", "cmd2 --check"],
        notes=["Note with *emphasis* and (parenthetical).", "Second note."],
    )


def test_apply_dyslexia_removes_parentheticals(base_result: AssistResult):
    """Dyslexia transform should remove parentheticals."""
    result = apply_dyslexia(base_result)
    assert "(" not in result.safest_next_step
    assert ")" not in result.safest_next_step
    for step in result.plan:
        assert "(" not in step
        assert ")" not in step


def test_apply_dyslexia_removes_visual_refs(base_result: AssistResult):
    """Dyslexia transform should remove visual references."""
    result = apply_dyslexia(base_result)
    assert "above" not in result.safest_next_step.lower()
    for step in result.plan:
        assert "below" not in step.lower()


def test_apply_dyslexia_removes_symbolic_emphasis(base_result: AssistResult):
    """Dyslexia transform should remove symbolic emphasis."""
    result = apply_dyslexia(base_result)
    for note in result.notes:
        assert "*" not in note


def test_apply_dyslexia_expands_abbreviations(base_result: AssistResult):
    """Dyslexia transform should expand abbreviations."""
    result = apply_dyslexia(base_result)
    # CLI expanded in safest_next_step
    assert "command line" in result.safest_next_step.lower()


def test_apply_dyslexia_max_5_steps(base_result: AssistResult):
    """Dyslexia transform should limit to 5 steps."""
    result = apply_dyslexia(base_result)
    assert len(result.plan) <= 5


def test_apply_dyslexia_max_2_notes(base_result: AssistResult):
    """Dyslexia transform should limit to 2 notes."""
    result = apply_dyslexia(base_result)
    assert len(result.notes) <= 2


def test_apply_dyslexia_preserves_confidence(base_result: AssistResult):
    """Dyslexia transform should preserve confidence."""
    result = apply_dyslexia(base_result)
    assert result.confidence == base_result.confidence


def test_apply_dyslexia_preserves_id(base_result: AssistResult):
    """Dyslexia transform should preserve anchored ID."""
    result = apply_dyslexia(base_result)
    assert result.anchored_id == base_result.anchored_id


def test_apply_dyslexia_preserves_commands(base_result: AssistResult):
    """Dyslexia transform should preserve safe commands."""
    result = apply_dyslexia(base_result)
    assert result.next_safe_commands == base_result.next_safe_commands[:3]


# Tests for render_dyslexia


def test_render_dyslexia_header():
    """Render should include dyslexia header."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["Step 1."],
        next_safe_commands=[],
        notes=[],
    )
    output = render_dyslexia(result)
    assert "ASSIST (Dyslexia):" in output


def test_render_dyslexia_explicit_labels():
    """Render should use explicit labels."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["Step 1.", "Step 2."],
        next_safe_commands=["cmd --dry-run"],
        notes=["A note."],
    )
    output = render_dyslexia(result)
    assert "Anchored ID:" in output
    assert "Confidence:" in output
    assert "Safest next step:" in output
    assert "Plan:" in output
    assert "Next safe command:" in output
    assert "Notes:" in output


def test_render_dyslexia_step_numbering():
    """Render should use 'Step N:' prefix."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["First step.", "Second step.", "Third step."],
        next_safe_commands=[],
        notes=[],
    )
    output = render_dyslexia(result)
    assert "- Step 1:" in output
    assert "- Step 2:" in output
    assert "- Step 3:" in output


def test_render_dyslexia_no_command_on_low():
    """Render should not show command on Low confidence."""
    result = AssistResult(
        anchored_id=None,
        confidence="Low",
        safest_next_step="Check config.",
        plan=["Step 1."],
        next_safe_commands=["cmd --dry-run"],
        notes=[],
    )
    output = render_dyslexia(result)
    assert "Next safe command:" not in output


def test_render_dyslexia_shows_command_on_high():
    """Render should show command on High confidence."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["Step 1."],
        next_safe_commands=["cmd --dry-run"],
        notes=[],
    )
    output = render_dyslexia(result)
    assert "Next safe command:" in output
    assert "cmd --dry-run" in output


def test_render_dyslexia_vertical_spacing():
    """Render should have blank lines between sections."""
    result = AssistResult(
        anchored_id="TEST.001",
        confidence="High",
        safest_next_step="Check config.",
        plan=["Step 1."],
        next_safe_commands=[],
        notes=[],
    )
    output = render_dyslexia(result)
    # Should have multiple blank lines for visual separation
    assert "\n\n" in output


# Integration tests


def test_dyslexia_full_pipeline():
    """Full pipeline test for dyslexia profile."""
    base = AssistResult(
        anchored_id="DEPLOY.CONFIG.MISSING",
        confidence="High",
        safest_next_step="Check the CLI configuration file (located in /etc/app).",
        plan=[
            "Verify the JSON config exists (optional step).",
            "Run: deploy check --dry-run",
            "See above for API endpoint details.",
        ],
        next_safe_commands=["deploy check --dry-run"],
        notes=["*Important*: This is critical."],
    )

    transformed = apply_dyslexia(base)
    output = render_dyslexia(transformed)

    # Header present
    assert "ASSIST (Dyslexia):" in output

    # ID preserved
    assert "DEPLOY.CONFIG.MISSING" in output

    # Confidence preserved
    assert "Confidence: High" in output

    # No parentheticals in content (header "(Dyslexia)" is ok)
    # Check that plan steps and notes don't have parentheticals
    for step in transformed.plan:
        assert "(" not in step
        assert ")" not in step
    assert "(" not in transformed.safest_next_step
    assert ")" not in transformed.safest_next_step

    # No visual refs
    assert "above" not in output.lower()

    # No symbolic emphasis
    assert "*" not in output

    # Step numbering
    assert "- Step 1:" in output

    # Command shown
    assert "deploy check --dry-run" in output


def test_dyslexia_low_confidence():
    """Dyslexia profile with Low confidence."""
    base = AssistResult(
        anchored_id=None,
        confidence="Low",
        safest_next_step="Review the output.",
        plan=["Step 1.", "Step 2."],
        next_safe_commands=["cmd --dry-run"],
        notes=["No ID found."],
    )

    transformed = apply_dyslexia(base)
    output = render_dyslexia(transformed)

    # Confidence preserved
    assert "Confidence: Low" in output

    # No command on Low confidence
    assert "Next safe command:" not in output

    # ID shows as none
    assert "Anchored ID: none" in output
