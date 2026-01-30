"""Tests for render output."""

from a11y_assist.render import AssistResult, render_assist


class TestRenderAssist:
    """Tests for rendering AssistResult to text."""

    def test_render_includes_header(self):
        """Output includes ASSIST (Low Vision) header."""
        result = AssistResult(
            anchored_id="TEST.ID",
            confidence="High",
            safest_next_step="Do the thing.",
            plan=["Step 1", "Step 2"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_assist(result)
        assert "ASSIST (Low Vision):" in output

    def test_render_includes_anchored_id(self):
        """Output includes anchored ID."""
        result = AssistResult(
            anchored_id="PAY.EXPORT.AUTH",
            confidence="High",
            safest_next_step="Check credentials.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_assist(result)
        assert "Anchored to: PAY.EXPORT.AUTH" in output

    def test_render_no_id_shows_none(self):
        """Output shows (none) when no anchored ID."""
        result = AssistResult(
            anchored_id=None,
            confidence="Low",
            safest_next_step="Try again.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_assist(result)
        assert "Anchored to: (none)" in output

    def test_render_includes_confidence(self):
        """Output includes confidence level."""
        result = AssistResult(
            anchored_id=None,
            confidence="Medium",
            safest_next_step="Do something.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_assist(result)
        assert "Confidence: Medium" in output

    def test_render_includes_plan(self):
        """Output includes numbered plan steps."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Start here.",
            plan=["First step", "Second step", "Third step"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_assist(result)
        assert "1) First step" in output
        assert "2) Second step" in output
        assert "3) Third step" in output

    def test_render_limits_plan_to_five(self):
        """Plan is limited to 5 steps with ellipsis."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Start here.",
            plan=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6"],
            next_safe_commands=[],
            notes=[],
        )
        output = render_assist(result)
        assert "5) Step 5" in output
        assert "..." in output
        assert "6)" not in output

    def test_render_includes_safe_commands(self):
        """Output includes SAFE commands section."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Check first.",
            plan=["Step 1"],
            next_safe_commands=["tool --dry-run", "tool --validate"],
            notes=[],
        )
        output = render_assist(result)
        assert "Next (SAFE):" in output
        assert "tool --dry-run" in output

    def test_render_includes_notes(self):
        """Output includes notes section."""
        result = AssistResult(
            anchored_id=None,
            confidence="High",
            safest_next_step="Do it.",
            plan=["Step 1"],
            next_safe_commands=[],
            notes=["Note one", "Note two"],
        )
        output = render_assist(result)
        assert "Notes:" in output
        assert "- Note one" in output
