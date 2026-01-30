"""Tests for cognitive-load profile transformation and rendering.

These tests enforce the invariants:
1. No invented facts - only rephrases existing content
2. No invented commands - SAFE commands must be verbatim from input
3. SAFE-only remains absolute
4. Additive behavior - doesn't rewrite original output
5. Deterministic - no randomness, no network calls
"""

import pytest

from a11y_assist.profiles.cognitive_load import (
    MAX_STEP_LENGTH,
    _cap_length,
    _reduce_conjunctions,
    _remove_parentheticals,
    _strip_boilerplate,
    _to_imperative,
    apply_cognitive_load,
    normalize_safest_step,
    normalize_step,
    reduce_notes,
    reduce_plan,
    select_safe_command,
)
from a11y_assist.profiles.cognitive_load_render import (
    STEP_LABELS,
    render_cognitive_load,
)
from a11y_assist.render import AssistResult


class TestNoInvention:
    """7.1 No invention test: output contains only input-derived content."""

    def test_no_extra_plan_steps_added(self):
        """Transformation never adds plan steps beyond input."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Check the config file.",
            plan=["Step A", "Step B"],
            next_safe_commands=["cmd --dry-run"],
            notes=["Note 1"],
        )
        transformed = apply_cognitive_load(result)
        # Should have at most input plan steps (2), never more
        assert len(transformed.plan) <= 2

    def test_no_extra_commands_added(self):
        """Transformation never adds commands beyond input."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do something.",
            plan=["Step 1"],
            next_safe_commands=["cmd1 --dry-run", "cmd2 --validate"],
            notes=[],
        )
        transformed = apply_cognitive_load(result)
        # At most 1 command for cognitive-load profile
        assert len(transformed.next_safe_commands) <= 1
        # And it must be from original set
        if transformed.next_safe_commands:
            assert transformed.next_safe_commands[0] in result.next_safe_commands

    def test_safe_commands_are_verbatim(self):
        """SAFE commands must be exactly as provided in input."""
        original_cmd = "mytool --dry-run --verbose"
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Run the check.",
            plan=["Step 1"],
            next_safe_commands=[original_cmd],
            notes=[],
        )
        transformed = apply_cognitive_load(result)
        # Command must be EXACTLY as provided - no modification
        assert transformed.next_safe_commands[0] == original_cmd


class TestPlanCappedAtThree:
    """7.2 Plan capped at 3 steps."""

    def test_plan_max_three_steps(self):
        """Plan never exceeds 3 steps."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Start here.",
            plan=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
            next_safe_commands=[],
            notes=[],
        )
        transformed = apply_cognitive_load(result)
        assert len(transformed.plan) <= 3

    def test_reduce_plan_preserves_order(self):
        """First 3 steps are preserved in order."""
        plan = ["A", "B", "C", "D", "E"]
        reduced = reduce_plan(plan)
        assert reduced == ["A.", "B.", "C."]  # After normalization adds periods

    def test_empty_plan_gets_fallback(self):
        """Empty plan gets a reasonable fallback."""
        reduced = reduce_plan([])
        assert len(reduced) == 1
        assert "Follow" in reduced[0]


class TestSafeOmittedOnLowConfidence:
    """7.3 SAFE command omitted on Low confidence."""

    def test_low_confidence_no_safe_commands(self):
        """Low confidence results in empty SAFE commands."""
        result = AssistResult(
            anchored_id=None,
            confidence="Low",
            safest_next_step="Check things.",
            plan=["Step 1"],
            next_safe_commands=["cmd --dry-run", "cmd --validate"],
            notes=[],
        )
        transformed = apply_cognitive_load(result)
        assert transformed.next_safe_commands == []

    def test_medium_confidence_keeps_one_command(self):
        """Medium confidence keeps one SAFE command."""
        result = AssistResult(
            anchored_id=None,
            confidence="Medium",
            safest_next_step="Check things.",
            plan=["Step 1"],
            next_safe_commands=["cmd --dry-run", "cmd --validate"],
            notes=[],
        )
        transformed = apply_cognitive_load(result)
        assert len(transformed.next_safe_commands) == 1

    def test_high_confidence_keeps_one_command(self):
        """High confidence keeps one SAFE command."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Check things.",
            plan=["Step 1"],
            next_safe_commands=["cmd --dry-run", "cmd --validate"],
            notes=[],
        )
        transformed = apply_cognitive_load(result)
        assert len(transformed.next_safe_commands) == 1


class TestNoParentheticals:
    """7.4 Parentheticals are removed."""

    def test_remove_round_parentheticals(self):
        """Round parentheses content is removed."""
        assert _remove_parentheticals("Do thing (optional)") == "Do thing"

    def test_remove_square_brackets(self):
        """Square bracket content is removed."""
        assert _remove_parentheticals("Run [see docs]") == "Run"

    def test_multiple_parentheticals_removed(self):
        """Multiple parentheticals are all removed."""
        result = _remove_parentheticals("A (note) B [info] C")
        assert "note" not in result
        assert "info" not in result

    def test_step_normalization_removes_parentheticals(self):
        """Full step normalization removes parentheticals."""
        result = normalize_step("Check the config (usually in /etc)")
        assert "(usually in /etc)" not in result

    def test_safest_step_removes_parentheticals(self):
        """Safest step normalization removes parentheticals."""
        result = normalize_safest_step("Start here (see manual for details)")
        assert "(see manual for details)" not in result


class TestOneSentencePerStep:
    """7.5 One sentence per step - conjunctions reduced."""

    def test_and_then_becomes_period_then(self):
        """'and then' becomes '. Then'."""
        result = _reduce_conjunctions("Do A and then do B")
        # Should keep only first sentence
        assert "Do A." == result or result.startswith("Do A")

    def test_and_splits_to_first_sentence(self):
        """'and' in middle splits and keeps first part."""
        result = _reduce_conjunctions("Check logs and restart service")
        assert "Check logs." == result

    def test_but_splits_to_first_sentence(self):
        """'but' in middle splits and keeps first part."""
        result = _reduce_conjunctions("Try this but be careful")
        assert "Try this." == result

    def test_full_step_is_one_sentence(self):
        """Full normalization results in one sentence."""
        result = normalize_step("First check the logs and then restart the service")
        # Should not contain 'and then'
        assert " and then " not in result
        # Should be one sentence (possibly truncated)
        assert result.count(". ") == 0 or result.endswith(".")


class TestLengthLimits:
    """7.6 Length limits are enforced."""

    def test_step_capped_at_90_chars(self):
        """Steps are capped at MAX_STEP_LENGTH (90) chars."""
        long_step = "A" * 150
        result = normalize_step(long_step)
        assert len(result) <= MAX_STEP_LENGTH

    def test_cap_length_adds_ellipsis(self):
        """Truncation adds ellipsis."""
        result = _cap_length("A" * 100, 50)
        assert len(result) == 50
        assert result.endswith("…")

    def test_notes_capped_at_100_chars(self):
        """Notes are capped at 100 chars."""
        notes = ["A" * 150]
        reduced = reduce_notes(notes)
        assert len(reduced[0]) <= 100


class TestNormalizationHelpers:
    """Tests for individual normalization functions."""

    def test_strip_boilerplate_run(self):
        """'Run:' prefix is stripped."""
        assert _strip_boilerplate("Run: mytool") == "mytool"

    def test_strip_boilerplate_rerun(self):
        """'Re-run:' prefix is stripped."""
        assert _strip_boilerplate("Re-run: command") == "command"

    def test_strip_boilerplate_dollar_sign(self):
        """'$ ' prefix is stripped."""
        assert _strip_boilerplate("$ ls -la") == "ls -la"

    def test_strip_boilerplate_greater_than(self):
        """'> ' prefix is stripped."""
        assert _strip_boilerplate("> npm install") == "npm install"

    def test_to_imperative_you_should(self):
        """'You should' becomes 'Do '."""
        assert _to_imperative("You should check the logs").startswith("Do ")

    def test_to_imperative_please(self):
        """'Please' becomes 'Do '."""
        assert _to_imperative("Please restart").startswith("Do ")

    def test_to_imperative_consider(self):
        """'Consider' becomes 'Try '."""
        assert _to_imperative("Consider updating").startswith("Try ")

    def test_to_imperative_it_may_help(self):
        """'It may help to' becomes 'Try '."""
        assert _to_imperative("It may help to restart").startswith("Try ")


class TestRenderCognitiveLoad:
    """Tests for cognitive-load renderer."""

    def test_render_includes_cognitive_load_header(self):
        """Output includes ASSIST (Cognitive Load) header."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1", "Step 2"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_cognitive_load(result)
        assert "ASSIST (Cognitive Load):" in output

    def test_render_includes_goal_line(self):
        """Output includes fixed Goal line."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Start here.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_cognitive_load(result)
        assert "Goal: Get back to a known-good state." in output

    def test_render_uses_first_next_last_labels(self):
        """Plan uses First/Next/Last labels instead of numbers."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Start here.",
            plan=["Step A", "Step B", "Step C"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_cognitive_load(result)
        assert "First:" in output
        assert "Next:" in output
        assert "Last:" in output
        # Should NOT have numbered steps
        assert "1)" not in output

    def test_render_single_step_uses_first(self):
        """Single step plan uses First label."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Start here.",
            plan=["Only step"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_cognitive_load(result)
        assert "First:" in output

    def test_render_two_steps_uses_first_next(self):
        """Two step plan uses First and Next labels."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Start here.",
            plan=["Step A", "Step B"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_cognitive_load(result)
        assert "First:" in output
        assert "Next:" in output
        # Last only appears for 3 steps
        assert output.count("Last:") == 0

    def test_render_includes_safest_next_step(self):
        """Output includes safest next step."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Check the config file first.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_cognitive_load(result)
        assert "Safest next step:" in output
        assert "Check the config file first" in output

    def test_render_includes_safe_command_when_high_confidence(self):
        """SAFE command shown for High confidence."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Run the check.",
            plan=["Step 1"],
            next_safe_commands=["tool --dry-run"],
            notes=[],
        )
        output = render_cognitive_load(result)
        assert "Next (SAFE):" in output
        assert "tool --dry-run" in output

    def test_render_no_safe_section_when_empty(self):
        """No SAFE section when no commands."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Run the check.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_cognitive_load(result)
        assert "Next (SAFE):" not in output


class TestDeterminism:
    """Tests to ensure deterministic behavior."""

    def test_same_input_same_output(self):
        """Same input always produces same output."""
        result = AssistResult(
            anchored_id="DET.TEST",
            confidence="Medium",
            safest_next_step="Check the logs (verbose mode).",
            plan=[
                "First check the config and restart",
                "Then verify the connection",
                "Finally update the cache",
                "Extra step that gets dropped",
            ],
            next_safe_commands=["tool --dry-run", "tool --validate"],
            notes=["Note with (parenthetical)", "Another note"],
        )
        # Run transformation multiple times
        outputs = [apply_cognitive_load(result) for _ in range(10)]
        # All outputs should be identical
        first = outputs[0]
        for output in outputs[1:]:
            assert output == first

    def test_render_deterministic(self):
        """Rendering is deterministic."""
        result = AssistResult(
            anchored_id="DET.RENDER",
            confidence="High",
            safest_next_step="Do something.",
            plan=["Step 1", "Step 2"],
            next_safe_commands=["cmd --dry-run"],
            notes=["A note"],
        )
        outputs = [render_cognitive_load(result) for _ in range(10)]
        first = outputs[0]
        for output in outputs[1:]:
            assert output == first


class TestSelectSafeCommand:
    """Tests for select_safe_command function."""

    def test_returns_none_for_low(self):
        """Returns None for Low confidence."""
        assert select_safe_command(["cmd"], "Low") is None

    def test_returns_none_for_empty_list(self):
        """Returns None for empty command list."""
        assert select_safe_command([], "High") is None

    def test_returns_first_command_for_medium(self):
        """Returns first command for Medium confidence."""
        result = select_safe_command(["cmd1", "cmd2"], "Medium")
        assert result == "cmd1"

    def test_returns_first_command_for_high(self):
        """Returns first command for High confidence."""
        result = select_safe_command(["cmd1", "cmd2"], "High")
        assert result == "cmd1"


class TestNotesReduction:
    """Tests for notes reduction."""

    def test_notes_limited_to_two(self):
        """Notes are limited to 2 max."""
        notes = ["Note 1", "Note 2", "Note 3", "Note 4"]
        reduced = reduce_notes(notes)
        assert len(reduced) == 2

    def test_empty_notes_stays_empty(self):
        """Empty notes list stays empty."""
        assert reduce_notes([]) == []


class TestStepLabels:
    """Tests for STEP_LABELS constant."""

    def test_labels_are_first_next_last(self):
        """Labels are First, Next, Last."""
        assert STEP_LABELS == ["First", "Next", "Last"]
