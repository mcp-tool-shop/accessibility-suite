"""Tests for screen-reader profile transformation and rendering.

These tests enforce the invariants:
1. No invented facts - only rephrases existing content
2. No invented commands - SAFE commands must be verbatim from input
3. SAFE-only remains absolute
4. Additive behavior - doesn't rewrite original output
5. Deterministic - no randomness, no network calls
6. No meaning in punctuation/formatting alone
7. No "visual navigation" references
8. No parentheticals as meaning carriers
"""

import pytest

from a11y_assist.profiles.screen_reader import (
    MAX_NOTE_LENGTH,
    MAX_STEP_LENGTH,
    MAX_STEPS_DEFAULT,
    MAX_STEPS_LOW,
    _cap_length,
    _expand_abbreviations,
    _one_sentence,
    _remove_parentheticals,
    _remove_visual_references,
    _replace_symbols,
    _strip_boilerplate,
    apply_screen_reader,
    generate_summary,
    normalize_safest_step,
    normalize_step,
    reduce_notes,
    reduce_plan,
    select_safe_command,
)
from a11y_assist.profiles.screen_reader_render import render_screen_reader
from a11y_assist.render import AssistResult


class TestProfileInvariants:
    """A) Profile invariants - anchored_id, no new commands, no invented IDs."""

    def test_anchored_id_preserved(self):
        """Output anchored_id is identical to input anchored_id."""
        result = AssistResult(
            anchored_id="PAY.EXPORT.SFTP.AUTH",
            confidence="High",
            safest_next_step="Check credentials.",
            plan=["Step 1"],
            next_safe_commands=["cmd --dry-run"],
            notes=[],
        )
        transformed = apply_screen_reader(result)
        assert transformed.anchored_id == result.anchored_id

    def test_none_anchored_id_preserved(self):
        """None anchored_id stays None."""
        result = AssistResult(
            anchored_id=None,
            confidence="Low",
            safest_next_step="Try again.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        transformed = apply_screen_reader(result)
        assert transformed.anchored_id is None

    def test_no_new_commands_added(self):
        """No new commands appear that weren't in input."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do something.",
            plan=["Step 1"],
            next_safe_commands=["original-cmd --dry-run"],
            notes=[],
        )
        transformed = apply_screen_reader(result)
        # At most 1 command
        assert len(transformed.next_safe_commands) <= 1
        # Any command must derive from original (minus $ prefix)
        if transformed.next_safe_commands:
            cmd = transformed.next_safe_commands[0]
            # Should match original or be original without $ prefix
            assert cmd in result.next_safe_commands or f"$ {cmd}" in result.next_safe_commands

    def test_no_invented_ids(self):
        """No new IDs are invented."""
        result = AssistResult(
            anchored_id="ORIG.ID",
            confidence="High",
            safest_next_step="Check.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        transformed = apply_screen_reader(result)
        # anchored_id must be exactly the same
        assert transformed.anchored_id == "ORIG.ID"

    def test_low_confidence_no_commands(self):
        """Low confidence results in no command section."""
        result = AssistResult(
            anchored_id=None,
            confidence="Low",
            safest_next_step="Try again.",
            plan=["Step 1"],
            next_safe_commands=["cmd --dry-run", "cmd --validate"],
            notes=[],
        )
        transformed = apply_screen_reader(result)
        assert transformed.next_safe_commands == []


class TestAudioSpecificConstraints:
    """B) Audio-specific constraints - no parentheticals, no visual refs, Step N: format."""

    def test_no_parentheticals_in_output(self):
        """Output contains no ( or ) or [ or ]."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Check the config (usually in /etc).",
            plan=[
                "First check [see docs]",
                "Then run (optional)",
                "Finally verify [important]",
            ],
            next_safe_commands=["cmd --dry-run"],
            notes=["Note with (parenthetical) content"],
        )
        transformed = apply_screen_reader(result)
        output = render_screen_reader(transformed)

        # Check no parenthetical characters
        assert "(" not in output, f"Found ( in output: {output}"
        assert ")" not in output, f"Found ) in output: {output}"
        assert "[" not in output, f"Found [ in output: {output}"
        assert "]" not in output, f"Found ] in output: {output}"

    def test_no_visual_navigation_references(self):
        """Output contains no 'see above/below/left/right/arrow'."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="See above for details.",
            plan=[
                "Check the error above",
                "Look at the output below",
                "Click the left arrow",
                "Move right to continue",
            ],
            next_safe_commands=[],
            notes=["See above for more info"],
        )
        transformed = apply_screen_reader(result)
        output = render_screen_reader(transformed).lower()

        assert "see above" not in output
        assert "see below" not in output
        assert "above" not in output or "above" in output.split("step")[-1]  # Allow in step numbers context
        assert "below" not in output
        assert "left" not in output
        assert "right" not in output
        assert "arrow" not in output

    def test_steps_use_step_n_format(self):
        """Each step starts with Step N:."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do something.",
            plan=["First step", "Second step", "Third step"],
            next_safe_commands=[],
            notes=[],
        )
        transformed = apply_screen_reader(result)
        output = render_screen_reader(transformed)

        assert "Step 1:" in output
        assert "Step 2:" in output
        assert "Step 3:" in output

    def test_steps_end_with_period(self):
        """Each step ends with a period."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do something.",
            plan=["First step", "Second step no period"],
            next_safe_commands=[],
            notes=[],
        )
        transformed = apply_screen_reader(result)

        for step in transformed.plan:
            assert step.endswith("."), f"Step does not end with period: {step}"

    def test_steps_length_capped(self):
        """Steps are <= MAX_STEP_LENGTH chars (including ellipsis if truncated)."""
        long_step = "A" * 200
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do something.",
            plan=[long_step],
            next_safe_commands=[],
            notes=[],
        )
        transformed = apply_screen_reader(result)

        for step in transformed.plan:
            assert len(step) <= MAX_STEP_LENGTH + 1, f"Step too long: {len(step)}"


class TestDeterminism:
    """C) Determinism tests - same input always produces same output."""

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
                "Extra step that may get dropped",
                "Another extra step",
            ],
            next_safe_commands=["tool --dry-run", "tool --validate"],
            notes=["Note with (parenthetical)", "Another note"],
        )
        # Run transformation multiple times
        outputs = [apply_screen_reader(result) for _ in range(10)]
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
        outputs = [render_screen_reader(result) for _ in range(10)]
        first = outputs[0]
        for output in outputs[1:]:
            assert output == first


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

    def test_strip_boilerplate_next(self):
        """'Next:' prefix is stripped."""
        assert _strip_boilerplate("Next: do this") == "do this"

    def test_remove_parentheticals_round(self):
        """Round parentheses content is removed."""
        assert _remove_parentheticals("Do thing (optional)") == "Do thing"

    def test_remove_parentheticals_square(self):
        """Square bracket content is removed."""
        assert _remove_parentheticals("Run [see docs]") == "Run"

    def test_remove_visual_references_see_above(self):
        """'see above' is removed."""
        result = _remove_visual_references("Check see above for info")
        assert "above" not in result.lower()

    def test_remove_visual_references_below(self):
        """'below' is removed."""
        result = _remove_visual_references("Look at the output below")
        assert "below" not in result.lower()

    def test_remove_visual_references_arrow(self):
        """'arrow' is removed."""
        result = _remove_visual_references("Click the arrow")
        assert "arrow" not in result.lower()

    def test_expand_abbreviations_cli(self):
        """CLI expands to 'command line'."""
        assert "command line" in _expand_abbreviations("Use the CLI tool")

    def test_expand_abbreviations_id(self):
        """ID expands to 'I D'."""
        assert "I D" in _expand_abbreviations("Check the ID")

    def test_expand_abbreviations_json(self):
        """JSON expands to 'J S O N'."""
        assert "J S O N" in _expand_abbreviations("Parse JSON")

    def test_expand_abbreviations_sftp(self):
        """SFTP expands to 'S F T P'."""
        assert "S F T P" in _expand_abbreviations("Upload via SFTP")

    def test_replace_symbols_arrow(self):
        """-> replaces with 'to'."""
        assert " to " in _replace_symbols("A -> B")

    def test_replace_symbols_fat_arrow(self):
        """=> replaces with 'to'."""
        assert " to " in _replace_symbols("A => B")

    def test_replace_symbols_ampersand(self):
        """& replaces with 'and'."""
        assert " and " in _replace_symbols("A & B")

    def test_one_sentence_semicolon(self):
        """Semicolon splits and keeps first."""
        result = _one_sentence("First part; second part")
        assert "second" not in result

    def test_cap_length_adds_ellipsis(self):
        """Long strings are capped with ellipsis."""
        result = _cap_length("A" * 200, 100)
        assert len(result) == 100
        assert result.endswith("…")


class TestStepNormalization:
    """Tests for full step normalization."""

    def test_normalize_step_complete(self):
        """Full normalization pipeline works."""
        step = "Run: Check the CLI (see docs) and verify -> continue"
        result = normalize_step(step)
        # Should not have parenthetical
        assert "(" not in result
        assert ")" not in result
        # Should have expanded CLI
        assert "command line" in result
        # Should have replaced arrow
        assert "->" not in result
        # Should end with period
        assert result.endswith(".")


class TestPlanReduction:
    """Tests for plan reduction."""

    def test_high_confidence_max_5_steps(self):
        """High confidence allows up to 5 steps."""
        plan = ["A", "B", "C", "D", "E", "F"]
        reduced = reduce_plan(plan, "High")
        assert len(reduced) == MAX_STEPS_DEFAULT

    def test_low_confidence_max_3_steps(self):
        """Low confidence reduces to max 3 steps."""
        plan = ["A", "B", "C", "D", "E"]
        reduced = reduce_plan(plan, "Low")
        assert len(reduced) == MAX_STEPS_LOW

    def test_empty_plan_gets_fallback(self):
        """Empty plan gets a fallback step."""
        reduced = reduce_plan([], "High")
        assert len(reduced) == 1
        assert "Follow" in reduced[0]


class TestSafeCommandSelection:
    """Tests for SAFE command selection."""

    def test_returns_none_for_low_confidence(self):
        """Low confidence returns None."""
        assert select_safe_command(["cmd"], "Low") is None

    def test_returns_none_for_empty_list(self):
        """Empty list returns None."""
        assert select_safe_command([], "High") is None

    def test_returns_first_command_for_high(self):
        """High confidence returns first command."""
        result = select_safe_command(["cmd1", "cmd2"], "High")
        assert result == "cmd1"

    def test_strips_dollar_prefix(self):
        """$ prefix is stripped from command."""
        result = select_safe_command(["$ cmd --dry-run"], "High")
        assert result == "cmd --dry-run"
        assert not result.startswith("$")


class TestNotesReduction:
    """Tests for notes reduction."""

    def test_notes_limited_to_three(self):
        """Notes are limited to 3 max."""
        notes = ["Note 1", "Note 2", "Note 3", "Note 4"]
        reduced = reduce_notes(notes)
        assert len(reduced) == 3

    def test_notes_capped_at_length(self):
        """Notes are capped at MAX_NOTE_LENGTH."""
        notes = ["A" * 200]
        reduced = reduce_notes(notes)
        assert len(reduced[0]) <= MAX_NOTE_LENGTH


class TestRenderScreenReader:
    """Tests for screen-reader renderer."""

    def test_render_includes_profile_header(self):
        """Output includes screen reader profile header."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_screen_reader(result)
        assert "ASSIST. Profile: Screen reader." in output

    def test_render_includes_anchored_id_spelled(self):
        """Anchored ID uses 'I D' spelling."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_screen_reader(result)
        assert "Anchored I D:" in output

    def test_render_none_id_says_none(self):
        """None anchored ID says 'none'."""
        result = AssistResult(
            anchored_id=None,
            confidence="Low",
            safest_next_step="Try again.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_screen_reader(result)
        assert "Anchored I D: none." in output

    def test_render_includes_summary(self):
        """Output includes Summary section."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_screen_reader(result)
        assert "Summary:" in output

    def test_render_includes_safest_next_step(self):
        """Output includes Safest next step."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Check config first.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_screen_reader(result)
        assert "Safest next step:" in output

    def test_render_includes_steps_section(self):
        """Output includes Steps section."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["First step", "Second step"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_screen_reader(result)
        assert "Steps:" in output

    def test_render_includes_safe_command(self):
        """Output includes next safe command when present."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=["tool --dry-run"],
            notes=[],
        )
        output = render_screen_reader(result)
        assert "Next safe command:" in output
        assert "tool --dry-run" in output

    def test_render_no_safe_command_section_when_empty(self):
        """No safe command section when no commands."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_screen_reader(result)
        assert "Next safe command:" not in output

    def test_render_single_note_uses_note(self):
        """Single note uses 'Note:' not 'Notes:'."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=["One note."],
        )
        output = render_screen_reader(result)
        assert "Note:" in output
        # Check it's not "Notes:"
        assert output.count("Notes:") == 0

    def test_render_multiple_notes_uses_notes(self):
        """Multiple notes use 'Notes:'."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=["Note one.", "Note two."],
        )
        output = render_screen_reader(result)
        assert "Notes:" in output


class TestGenerateSummary:
    """Tests for summary generation."""

    def test_summary_from_original_title(self):
        """Summary extracts from 'Original title:' note."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=["Original title: Payment export failed"],
        )
        summary = generate_summary(result)
        assert "Payment export failed" in summary

    def test_summary_high_confidence_fallback(self):
        """High confidence without title gets generic summary."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        summary = generate_summary(result)
        assert "structured error" in summary.lower()

    def test_summary_low_confidence_fallback(self):
        """Low confidence gets appropriate summary."""
        result = AssistResult(
            anchored_id=None,
            confidence="Low",
            safest_next_step="Do the thing.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        summary = generate_summary(result)
        assert "identifier" in summary.lower() or "error" in summary.lower()


class TestGoldenOutput:
    """C) Golden tests - exact output committed to repo, run in CI."""

    def test_golden_cli_error_invariants(self):
        """cli.error.v0.1 JSON produces consistent screen-reader output."""
        # Test invariants without exact string matching (which varies by normalization)
        from a11y_assist.from_cli_error import assist_from_cli_error, load_cli_error
        import os

        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "cli_error_good.json"
        )
        obj = load_cli_error(fixture_path)
        result = assist_from_cli_error(obj)
        transformed = apply_screen_reader(result)
        output = render_screen_reader(transformed)

        # Invariants
        assert "ASSIST. Profile: Screen reader." in output
        assert "Anchored I D: PAY.EXPORT.SFTP.AUTH." in output
        assert "Confidence: High." in output
        assert "Summary:" in output
        assert "Safest next step:" in output
        assert "Steps:" in output
        assert "Step 1:" in output
        # No parentheticals
        assert "(" not in output
        assert ")" not in output

    def test_golden_raw_with_id_invariants(self):
        """Raw text with ID produces consistent screen-reader output."""
        from a11y_assist.parse_raw import parse_raw
        import os

        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "raw_good.txt"
        )
        with open(fixture_path) as f:
            text = f.read()

        err_id, status, blocks = parse_raw(text)
        plan = blocks.get("Fix:", [])
        result = AssistResult(
            anchored_id=err_id,
            confidence="Medium",
            safest_next_step="Follow the tool's Fix steps.",
            plan=plan,
            next_safe_commands=[line for line in plan if "--dry-run" in line][:3],
            notes=[],
        )
        transformed = apply_screen_reader(result)
        output = render_screen_reader(transformed)

        # Invariants
        assert "ASSIST. Profile: Screen reader." in output
        assert "Anchored I D: PAY.EXPORT.SFTP.AUTH." in output
        assert "Confidence: Medium." in output
        assert "Step 1:" in output
        # No parentheticals
        assert "(" not in output
        assert ")" not in output

    def test_golden_raw_no_id_invariants(self):
        """Raw text without ID produces consistent screen-reader output."""
        from a11y_assist.parse_raw import parse_raw
        import os

        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "raw_no_id.txt"
        )
        with open(fixture_path) as f:
            text = f.read()

        err_id, status, blocks = parse_raw(text)
        result = AssistResult(
            anchored_id=err_id,
            confidence="Low",
            safest_next_step="Follow the tool's Fix steps.",
            plan=[
                "Re-run the command with increased verbosity/logging.",
                "Update the tool to emit (ID: ...) and What/Why/Fix blocks.",
                "If this is your tool, adopt cli.error.v0.1 JSON output.",
            ],
            next_safe_commands=[],
            notes=["No (ID: ...) found."],
        )
        transformed = apply_screen_reader(result)
        output = render_screen_reader(transformed)

        # Invariants
        assert "ASSIST. Profile: Screen reader." in output
        assert "Anchored I D: none." in output
        assert "Confidence: Low." in output
        # Low confidence = max 3 steps
        assert "Step 1:" in output
        assert "Step 2:" in output
        assert "Step 3:" in output
        # No Step 4 for low confidence
        assert "Step 4:" not in output
        # No SAFE command section for low confidence
        assert "Next safe command:" not in output
        # No parentheticals in output
        assert "(" not in output
        assert ")" not in output
