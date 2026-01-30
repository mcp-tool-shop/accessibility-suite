"""Unit tests for Profile Guard invariants.

Tests each guard check individually to ensure violations are detected.
"""

import pytest

from a11y_assist.guard import (
    GuardContext,
    GuardIssue,
    GuardViolation,
    get_guard_context,
    validate_profile_transform,
)
from a11y_assist.render import AssistResult


# Fixtures

@pytest.fixture
def base_result_high() -> AssistResult:
    """High confidence base result with commands."""
    return AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the fix command.",
        plan=["Step 1: Check config.", "Step 2: Run fix."],
        next_safe_commands=["fix --dry-run"],
        notes=["Original error message."],
    )


@pytest.fixture
def base_result_low() -> AssistResult:
    """Low confidence base result."""
    return AssistResult(
        anchored_id=None,
        confidence="Low",
        safest_next_step="Check the output.",
        plan=["Re-run with verbosity."],
        next_safe_commands=[],
        notes=["No ID found."],
    )


@pytest.fixture
def base_text() -> str:
    """Sample base text for content support checking."""
    return "Error: Config file not found. Run fix --dry-run to repair."


# Test: ID Invariant


def test_guard_id_invented_fails(base_result_low: AssistResult, base_text: str):
    """Guard should fail when profile invents an ID that didn't exist."""
    # Base has no ID
    profiled = AssistResult(
        anchored_id="INVENTED.ID.001",  # Invented!
        confidence="Low",
        safest_next_step="Check the output.",
        plan=["Re-run with verbosity."],
        next_safe_commands=[],
        notes=["No ID found."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="Low",
        input_kind="raw_text",
        allowed_commands=set(),
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform(base_text, base_result_low, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.ID.INVENTED"
        for issue in exc_info.value.issues
    )


def test_guard_id_changed_fails(base_result_high: AssistResult, base_text: str):
    """Guard should fail when profile changes an existing ID."""
    profiled = AssistResult(
        anchored_id="DIFFERENT.ID.002",  # Changed!
        confidence="High",
        safest_next_step="Run the fix command.",
        plan=["Step 1: Check config.", "Step 2: Run fix."],
        next_safe_commands=["fix --dry-run"],
        notes=["Original error message."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"fix --dry-run"},
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform(base_text, base_result_high, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.ID.CHANGED"
        for issue in exc_info.value.issues
    )


def test_guard_id_preserved_passes(base_result_high: AssistResult, base_text: str):
    """Guard should pass when ID is preserved correctly."""
    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",  # Same as base
        confidence="High",
        safest_next_step="Run the fix command.",
        plan=["Step 1: Check config.", "Step 2: Run fix."],
        next_safe_commands=["fix --dry-run"],
        notes=["Original error message."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"fix --dry-run"},
    )

    # Should not raise
    validate_profile_transform(base_text, base_result_high, profiled, ctx)


# Test: Confidence Invariant


def test_guard_confidence_increase_fails(base_result_low: AssistResult, base_text: str):
    """Guard should fail when profile increases confidence level."""
    profiled = AssistResult(
        anchored_id=None,
        confidence="High",  # Increased from Low!
        safest_next_step="Check the output.",
        plan=["Re-run with verbosity."],
        next_safe_commands=[],
        notes=["No ID found."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="Low",
        input_kind="raw_text",
        allowed_commands=set(),
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform(base_text, base_result_low, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.CONFIDENCE.INCREASED"
        for issue in exc_info.value.issues
    )


def test_guard_confidence_decrease_passes(base_result_high: AssistResult, base_text: str):
    """Guard should allow confidence to decrease (conservative)."""
    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="Medium",  # Decreased from High - OK
        safest_next_step="Run the fix command.",
        plan=["Step 1: Check config.", "Step 2: Run fix."],
        next_safe_commands=["fix --dry-run"],
        notes=["Original error message."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"fix --dry-run"},
    )

    # Should not raise
    validate_profile_transform(base_text, base_result_high, profiled, ctx)


def test_guard_confidence_same_passes(base_result_high: AssistResult, base_text: str):
    """Guard should allow same confidence level."""
    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",  # Same as base
        safest_next_step="Run the fix command.",
        plan=["Step 1: Check config.", "Step 2: Run fix."],
        next_safe_commands=["fix --dry-run"],
        notes=["Original error message."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"fix --dry-run"},
    )

    # Should not raise
    validate_profile_transform(base_text, base_result_high, profiled, ctx)


# Test: Commands Invariant


def test_guard_command_invented_fails(base_result_high: AssistResult, base_text: str):
    """Guard should fail when profile invents a command not in allowed set."""
    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the fix command.",
        plan=["Step 1: Check config.", "Step 2: Run fix."],
        next_safe_commands=["rm -rf /"],  # Invented dangerous command!
        notes=["Original error message."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"fix --dry-run"},  # Only this is allowed
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform(base_text, base_result_high, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.COMMANDS.INVENTED"
        for issue in exc_info.value.issues
    )


def test_guard_command_not_in_allowed_set_fails(base_result_high: AssistResult, base_text: str):
    """Guard should fail when command is not in the allowed set."""
    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the fix command.",
        plan=["Step 1: Check config.", "Step 2: Run fix."],
        next_safe_commands=["fix --dry-run", "another-command"],
        notes=["Original error message."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"fix --dry-run"},  # Only one allowed
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform(base_text, base_result_high, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.COMMANDS.INVENTED"
        for issue in exc_info.value.issues
    )


def test_guard_low_conf_disallows_commands(base_result_low: AssistResult, base_text: str):
    """Guard should fail when Low confidence result has commands."""
    profiled = AssistResult(
        anchored_id=None,
        confidence="Low",
        safest_next_step="Check the output.",
        plan=["Re-run with verbosity."],
        next_safe_commands=["some-command"],  # Commands on Low!
        notes=["No ID found."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="Low",
        input_kind="raw_text",
        allowed_commands={"some-command"},  # Even if allowed, still fails
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform(base_text, base_result_low, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.COMMANDS.DISALLOWED_LOW_CONF"
        for issue in exc_info.value.issues
    )


def test_guard_command_with_dollar_prefix_passes(base_result_high: AssistResult, base_text: str):
    """Guard should handle $ prefix normalization correctly."""
    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the fix command.",
        plan=["Step 1: Check config.", "Step 2: Run fix."],
        next_safe_commands=["$ fix --dry-run"],  # With $ prefix
        notes=["Original error message."],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"fix --dry-run"},  # Without prefix
    )

    # Should not raise - $ prefix is normalized
    validate_profile_transform(base_text, base_result_high, profiled, ctx)


# Test: Step Count Invariant


def test_guard_plan_too_many_steps_fails():
    """Guard should fail when plan exceeds max steps."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Follow the steps.",
        plan=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6"],
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Follow the steps.",
        plan=["Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6"],  # 6 steps
        next_safe_commands=[],
        notes=[],
    )

    # lowvision profile has max_steps=5
    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform("test content", base, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.PLAN.TOO_MANY_STEPS"
        for issue in exc_info.value.issues
    )


def test_guard_cognitive_load_max_3_steps():
    """Cognitive-load profile should enforce max 3 steps."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Follow the steps.",
        plan=["Step 1", "Step 2", "Step 3", "Step 4"],  # 4 steps
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Follow the steps.",
        plan=["Step 1", "Step 2", "Step 3", "Step 4"],  # 4 steps > 3 max
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="cognitive-load",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform("test content", base, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.PLAN.TOO_MANY_STEPS"
        for issue in exc_info.value.issues
    )


def test_guard_plan_within_limit_passes():
    """Guard should pass when plan is within step limit."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Follow the steps.",
        plan=["Step 1", "Step 2", "Step 3"],  # 3 steps
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Follow the steps.",
        plan=["Step 1", "Step 2", "Step 3"],
        next_safe_commands=[],
        notes=[],
    )

    # cognitive-load has max_steps=3
    ctx = get_guard_context(
        profile="cognitive-load",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    # Should not raise
    validate_profile_transform("test content", base, profiled, ctx)


# Test: Screen-reader Specific Constraints


def test_guard_parentheticals_forbidden():
    """Screen-reader profile should forbid parentheticals."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the command",
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the command (see docs)",  # Parenthetical!
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="screen-reader",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform("test content docs command", base, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.TEXT.PARENTHETICALS_FORBIDDEN"
        for issue in exc_info.value.issues
    )


def test_guard_brackets_also_forbidden():
    """Screen-reader profile should forbid square brackets too."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the command",
        plan=["Step 1 [optional]"],  # Square brackets!
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the command",
        plan=["Step 1 [optional]"],
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="screen-reader",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform("test content optional command", base, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.TEXT.PARENTHETICALS_FORBIDDEN"
        for issue in exc_info.value.issues
    )


def test_guard_visual_refs_forbidden():
    """Screen-reader profile should forbid visual navigation references."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the command",
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="See above for details",  # Visual ref!
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="screen-reader",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform("test content details command", base, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.TEXT.VISUAL_REFS_FORBIDDEN"
        for issue in exc_info.value.issues
    )


def test_guard_visual_refs_below_forbidden():
    """Screen-reader should forbid 'below' visual reference."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Check the output",
        plan=["See below for instructions"],  # Visual ref!
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Check the output",
        plan=["See below for instructions"],
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="screen-reader",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform("test content instructions output", base, profiled, ctx)

    assert any(
        issue.code == "A11Y.ASSIST.GUARD.TEXT.VISUAL_REFS_FORBIDDEN"
        for issue in exc_info.value.issues
    )


def test_guard_lowvision_allows_parentheticals():
    """Lowvision profile should allow parentheticals."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the command (see docs)",  # Parenthetical OK
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run the command (see docs)",
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    # Should not raise - lowvision allows parentheticals
    validate_profile_transform("test content docs command", base, profiled, ctx)


# Test: Content Support (WARN level - doesn't fail but is tracked)


def test_guard_unsupported_content_is_warn_not_error():
    """Unsupported content should produce WARN, not fail."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Check configuration.",
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Contact the administrator immediately.",  # Not in base
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    # Should NOT raise - WARN level doesn't fail
    # Content support is a WARN, not an ERROR
    validate_profile_transform("Check configuration and retry.", base, profiled, ctx)


# Test: GuardContext Factory


def test_get_guard_context_lowvision():
    """Lowvision profile should have correct constraints."""
    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"cmd1", "cmd2"},
    )

    assert ctx.profile == "lowvision"
    assert ctx.max_steps == 5
    assert ctx.forbid_parentheticals is False
    assert ctx.forbid_visual_refs is False
    assert ctx.allow_commands_on_low is False


def test_get_guard_context_cognitive_load():
    """Cognitive-load profile should have correct constraints."""
    ctx = get_guard_context(
        profile="cognitive-load",
        confidence="Medium",
        input_kind="raw_text",
        allowed_commands=set(),
    )

    assert ctx.profile == "cognitive-load"
    assert ctx.max_steps == 3
    assert ctx.forbid_parentheticals is False
    assert ctx.forbid_visual_refs is False


def test_get_guard_context_screen_reader_high():
    """Screen-reader profile on High confidence should allow 5 steps."""
    ctx = get_guard_context(
        profile="screen-reader",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    assert ctx.profile == "screen-reader"
    assert ctx.max_steps == 5
    assert ctx.forbid_parentheticals is True
    assert ctx.forbid_visual_refs is True


def test_get_guard_context_screen_reader_low():
    """Screen-reader profile on Low confidence should allow only 3 steps."""
    ctx = get_guard_context(
        profile="screen-reader",
        confidence="Low",
        input_kind="raw_text",
        allowed_commands=set(),
    )

    assert ctx.profile == "screen-reader"
    assert ctx.max_steps == 3
    assert ctx.forbid_parentheticals is True
    assert ctx.forbid_visual_refs is True


# Test: Multiple Violations


def test_guard_multiple_violations_reported():
    """Guard should report all violations, not just the first."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Run command.",
        plan=["Step 1"],
        next_safe_commands=["safe-cmd"],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="CHANGED.ID",  # Violation 1: ID changed
        confidence="High",
        safest_next_step="Run command.",
        plan=["Step 1"],
        next_safe_commands=["invented-cmd"],  # Violation 2: Command invented
        notes=[],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands={"safe-cmd"},
    )

    with pytest.raises(GuardViolation) as exc_info:
        validate_profile_transform("test content", base, profiled, ctx)

    codes = [issue.code for issue in exc_info.value.issues]
    assert "A11Y.ASSIST.GUARD.ID.CHANGED" in codes
    assert "A11Y.ASSIST.GUARD.COMMANDS.INVENTED" in codes


# Test: GuardViolation String Representation


def test_guard_violation_str():
    """GuardViolation should have a readable string representation."""
    issues = [
        GuardIssue(
            severity="ERROR",
            code="A11Y.ASSIST.GUARD.ID.INVENTED",
            message="Profile invented an ID",
            details={"base_id": "None", "profiled_id": "FAKE.ID"},
        ),
    ]
    violation = GuardViolation(issues)
    s = str(violation)

    assert "Profile guard violation" in s
    assert "A11Y.ASSIST.GUARD.ID.INVENTED" in s
    assert "Profile invented an ID" in s
    assert "FAKE.ID" in s


# Test: Edge Cases


def test_guard_empty_commands_passes():
    """Guard should pass when both base and profiled have no commands."""
    base = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Check manually.",
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id="TEST.ERROR.001",
        confidence="High",
        safest_next_step="Check manually.",
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="High",
        input_kind="cli_error_json",
        allowed_commands=set(),
    )

    # Should not raise
    validate_profile_transform("Check manually", base, profiled, ctx)


def test_guard_none_id_preserved():
    """Guard should pass when None ID is preserved as None."""
    base = AssistResult(
        anchored_id=None,
        confidence="Low",
        safest_next_step="Check output.",
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    profiled = AssistResult(
        anchored_id=None,  # Still None - correct
        confidence="Low",
        safest_next_step="Check output.",
        plan=["Step 1"],
        next_safe_commands=[],
        notes=[],
    )

    ctx = get_guard_context(
        profile="lowvision",
        confidence="Low",
        input_kind="raw_text",
        allowed_commands=set(),
    )

    # Should not raise
    validate_profile_transform("Check output", base, profiled, ctx)
