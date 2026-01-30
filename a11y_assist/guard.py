"""Profile Guard: centralized invariant checker for profile transforms.

Runs after every profile transform to prevent unsafe drift.
Guard failures are engine bugs, not user errors.

Invariants enforced:
1. Anchored ID cannot be invented or changed
2. Confidence cannot increase
3. SAFE-only commands: no new commands, no risky
4. Step count caps enforced
5. Profile must not add new factual content
6. Profile-specific constraints (parentheticals, visual refs)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Set

from .render import AssistResult, Confidence

Severity = Literal["ERROR", "WARN"]

# Stopwords to ignore in content overlap checking
STOPWORDS = frozenset([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "also", "now", "and", "but", "or", "if", "it",
    "its", "this", "that", "these", "those", "what", "which", "who",
    "whom", "your", "you", "we", "they", "them", "their", "our", "my",
])

# Allowed glue vocabulary for plan steps (common action words)
GLUE_VOCABULARY = frozenset([
    "step", "first", "next", "last", "run", "rerun", "re-run", "confirm",
    "check", "verify", "try", "retry", "follow", "start", "continue",
    "do", "ensure", "make", "see", "look", "update", "fix", "apply",
    "tool", "tools", "command", "commands", "output", "input", "file",
    "files", "error", "errors", "warning", "warnings", "dry", "dryrun",
    "dry-run", "validate", "validation", "config", "configuration",
    "line", "cli", "json", "order", "instructions", "steps",
])

# Visual navigation patterns
VISUAL_NAV_PATTERNS = re.compile(
    r"\b(see\s+)?(above|below|left|right|arrow)\b", re.IGNORECASE
)

# Parenthetical pattern
PARENTHETICAL_PATTERN = re.compile(r"[\(\)\[\]]")

# Confidence ordering (lower index = lower confidence)
CONFIDENCE_ORDER = {"Low": 0, "Medium": 1, "High": 2}


@dataclass(frozen=True)
class GuardIssue:
    """A single guard violation."""

    severity: Severity
    code: str  # e.g. A11Y.ASSIST.GUARD.COMMANDS.INVENTED
    message: str  # human-readable
    details: Dict[str, str] = field(default_factory=dict)


class GuardViolation(Exception):
    """Exception raised when profile transform violates invariants."""

    def __init__(self, issues: List[GuardIssue]):
        super().__init__("Profile guard violation")
        self.issues = issues

    def __str__(self) -> str:
        lines = ["Profile guard violation:"]
        for issue in self.issues:
            lines.append(f"  [{issue.severity}] {issue.code}: {issue.message}")
            for k, v in issue.details.items():
                lines.append(f"    {k}: {v}")
        return "\n".join(lines)


@dataclass(frozen=True)
class GuardContext:
    """Context for guard validation."""

    profile: str  # e.g. "screen-reader"
    confidence: Confidence  # High/Medium/Low
    input_kind: str  # cli_error_json|raw_text|scorecard_json|last_log
    allowed_safe_commands: frozenset[str]  # derived from base inputs verbatim

    # Per-profile constraints
    forbid_parentheticals: bool = False
    forbid_visual_refs: bool = False
    max_steps: Optional[int] = None  # enforce if set
    allow_commands_on_low: bool = False  # default: no commands on Low confidence


def _tokenize_content(text: str) -> Set[str]:
    """Tokenize text into lowercase content words.

    - Letters/numbers only
    - Strip punctuation
    - Drop stopwords
    - Drop tokens < 3 chars
    """
    # Extract alphanumeric tokens
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    # Filter
    return {
        t for t in tokens
        if len(t) >= 3 and t not in STOPWORDS
    }


def _is_content_supported(line: str, base_tokens: Set[str]) -> bool:
    """Check if a line is supported by base text content.

    A line is supported if:
    - It shares at least one content word with base text, OR
    - It's composed solely of glue vocabulary + base content words
    """
    line_tokens = _tokenize_content(line)

    if not line_tokens:
        # Empty line or all stopwords/short words - allowed
        return True

    # Check for overlap with base
    overlap = line_tokens & base_tokens
    if overlap:
        return True

    # Check if all tokens are glue vocabulary
    non_glue = line_tokens - GLUE_VOCABULARY
    if not non_glue:
        return True

    # Check if non-glue tokens are in base
    unsupported = non_glue - base_tokens
    return len(unsupported) == 0


def _check_id_invariant(
    base: AssistResult, profiled: AssistResult, issues: List[GuardIssue]
) -> None:
    """Check: Anchored ID cannot be invented or changed."""
    if base.anchored_id is None:
        if profiled.anchored_id is not None:
            issues.append(GuardIssue(
                severity="ERROR",
                code="A11Y.ASSIST.GUARD.ID.INVENTED",
                message="Profile invented an anchored ID that didn't exist in base",
                details={
                    "base_id": "None",
                    "profiled_id": str(profiled.anchored_id),
                },
            ))
    else:
        if profiled.anchored_id != base.anchored_id:
            issues.append(GuardIssue(
                severity="ERROR",
                code="A11Y.ASSIST.GUARD.ID.CHANGED",
                message="Profile changed the anchored ID",
                details={
                    "base_id": str(base.anchored_id),
                    "profiled_id": str(profiled.anchored_id),
                },
            ))


def _check_confidence_invariant(
    base: AssistResult, profiled: AssistResult, issues: List[GuardIssue]
) -> None:
    """Check: Confidence cannot increase."""
    base_level = CONFIDENCE_ORDER.get(base.confidence, 0)
    profiled_level = CONFIDENCE_ORDER.get(profiled.confidence, 0)

    if profiled_level > base_level:
        issues.append(GuardIssue(
            severity="ERROR",
            code="A11Y.ASSIST.GUARD.CONFIDENCE.INCREASED",
            message="Profile increased confidence level (not allowed)",
            details={
                "base_confidence": base.confidence,
                "profiled_confidence": profiled.confidence,
            },
        ))


def _check_commands_invariant(
    base: AssistResult,
    profiled: AssistResult,
    ctx: GuardContext,
    issues: List[GuardIssue],
) -> None:
    """Check: SAFE-only commands - no new commands, no risky."""
    # Check each profiled command
    for cmd in profiled.next_safe_commands:
        # Normalize for comparison (strip $ prefix)
        normalized_cmd = cmd.lstrip("$ ").strip()

        # Check if command is in allowed set
        allowed = False
        for allowed_cmd in ctx.allowed_safe_commands:
            normalized_allowed = allowed_cmd.lstrip("$ ").strip()
            if normalized_cmd == normalized_allowed:
                allowed = True
                break

        if not allowed:
            issues.append(GuardIssue(
                severity="ERROR",
                code="A11Y.ASSIST.GUARD.COMMANDS.INVENTED",
                message="Profile included a command not in the allowed set",
                details={
                    "command": cmd,
                    "allowed_commands": ", ".join(ctx.allowed_safe_commands) or "(none)",
                },
            ))

    # Check Low confidence rule
    if ctx.confidence == "Low" and not ctx.allow_commands_on_low:
        if profiled.next_safe_commands:
            issues.append(GuardIssue(
                severity="ERROR",
                code="A11Y.ASSIST.GUARD.COMMANDS.DISALLOWED_LOW_CONF",
                message="Profile included commands on Low confidence (not allowed)",
                details={
                    "commands": ", ".join(profiled.next_safe_commands),
                },
            ))


def _check_step_count_invariant(
    profiled: AssistResult, ctx: GuardContext, issues: List[GuardIssue]
) -> None:
    """Check: Step count caps enforced."""
    if ctx.max_steps is not None:
        if len(profiled.plan) > ctx.max_steps:
            issues.append(GuardIssue(
                severity="ERROR",
                code="A11Y.ASSIST.GUARD.PLAN.TOO_MANY_STEPS",
                message=f"Profile exceeded max steps ({ctx.max_steps})",
                details={
                    "max_steps": str(ctx.max_steps),
                    "actual_steps": str(len(profiled.plan)),
                },
            ))


def _check_content_support_invariant(
    base_text: str,
    profiled: AssistResult,
    issues: List[GuardIssue],
) -> None:
    """Check: Profile must not add new factual content."""
    base_tokens = _tokenize_content(base_text)

    # Check safest_next_step
    if not _is_content_supported(profiled.safest_next_step, base_tokens):
        issues.append(GuardIssue(
            severity="WARN",
            code="A11Y.ASSIST.GUARD.CONTENT.UNSUPPORTED",
            message="Safest next step contains content not found in base text",
            details={
                "text": profiled.safest_next_step[:80],
            },
        ))

    # Check plan steps
    for i, step in enumerate(profiled.plan):
        if not _is_content_supported(step, base_tokens):
            issues.append(GuardIssue(
                severity="WARN",
                code="A11Y.ASSIST.GUARD.CONTENT.UNSUPPORTED",
                message=f"Plan step {i + 1} contains content not found in base text",
                details={
                    "step": step[:80],
                },
            ))


def _check_parentheticals_constraint(
    profiled: AssistResult, issues: List[GuardIssue]
) -> None:
    """Check: No parentheticals allowed (profile-specific)."""
    fields_to_check = [
        ("safest_next_step", profiled.safest_next_step),
    ]
    fields_to_check.extend(
        (f"plan[{i}]", step) for i, step in enumerate(profiled.plan)
    )
    fields_to_check.extend(
        (f"notes[{i}]", note) for i, note in enumerate(profiled.notes)
    )

    for field_name, text in fields_to_check:
        if PARENTHETICAL_PATTERN.search(text):
            issues.append(GuardIssue(
                severity="ERROR",
                code="A11Y.ASSIST.GUARD.TEXT.PARENTHETICALS_FORBIDDEN",
                message=f"Parentheticals found in {field_name} (forbidden by profile)",
                details={
                    "field": field_name,
                    "text": text[:80],
                },
            ))


def _check_visual_refs_constraint(
    profiled: AssistResult, issues: List[GuardIssue]
) -> None:
    """Check: No visual navigation references (profile-specific)."""
    fields_to_check = [
        ("safest_next_step", profiled.safest_next_step),
    ]
    fields_to_check.extend(
        (f"plan[{i}]", step) for i, step in enumerate(profiled.plan)
    )
    fields_to_check.extend(
        (f"notes[{i}]", note) for i, note in enumerate(profiled.notes)
    )

    for field_name, text in fields_to_check:
        if VISUAL_NAV_PATTERNS.search(text):
            issues.append(GuardIssue(
                severity="ERROR",
                code="A11Y.ASSIST.GUARD.TEXT.VISUAL_REFS_FORBIDDEN",
                message=f"Visual navigation reference found in {field_name} (forbidden by profile)",
                details={
                    "field": field_name,
                    "text": text[:80],
                },
            ))


def validate_profile_transform(
    base_text: str,
    base_result: AssistResult,
    profiled_result: AssistResult,
    ctx: GuardContext,
) -> None:
    """Validate that a profile transform respects all invariants.

    Args:
        base_text: The source text for content support checking
        base_result: The AssistResult before profile transformation
        profiled_result: The AssistResult after profile transformation
        ctx: Guard context with profile rules and constraints

    Raises:
        GuardViolation: If any invariant is violated
    """
    issues: List[GuardIssue] = []

    # 1. Anchored ID invariant
    _check_id_invariant(base_result, profiled_result, issues)

    # 2. Confidence invariant
    _check_confidence_invariant(base_result, profiled_result, issues)

    # 3. Commands invariant
    _check_commands_invariant(base_result, profiled_result, ctx, issues)

    # 4. Step count invariant
    _check_step_count_invariant(profiled_result, ctx, issues)

    # 5. Content support invariant (WARN only)
    _check_content_support_invariant(base_text, profiled_result, issues)

    # 6. Profile-specific constraints
    if ctx.forbid_parentheticals:
        _check_parentheticals_constraint(profiled_result, issues)

    if ctx.forbid_visual_refs:
        _check_visual_refs_constraint(profiled_result, issues)

    # Raise if any ERROR-level issues
    errors = [i for i in issues if i.severity == "ERROR"]
    if errors:
        raise GuardViolation(errors)

    # For WARN-level issues, we could log them but don't fail
    # (In future, could add a strict mode that fails on WARN too)


# Profile rules configuration
def get_guard_context(
    profile: str,
    confidence: Confidence,
    input_kind: str,
    allowed_commands: Set[str],
) -> GuardContext:
    """Create a GuardContext for a profile.

    Args:
        profile: Profile name (lowvision, cognitive-load, screen-reader, dyslexia, plain-language)
        confidence: Confidence level from base result
        input_kind: Type of input (cli_error_json, raw_text, etc.)
        allowed_commands: Set of allowed SAFE commands from base

    Returns:
        GuardContext configured for the profile
    """
    # Base configuration
    forbid_parentheticals = False
    forbid_visual_refs = False
    max_steps: Optional[int] = None
    allow_commands_on_low = False

    if profile == "lowvision":
        max_steps = 5
    elif profile == "cognitive-load":
        max_steps = 3
    elif profile == "screen-reader":
        forbid_parentheticals = True
        forbid_visual_refs = True
        # Screen-reader: 5 steps normally, 3 on Low confidence
        max_steps = 3 if confidence == "Low" else 5
    elif profile == "dyslexia":
        forbid_parentheticals = True
        forbid_visual_refs = True
        max_steps = 5
    elif profile == "plain-language":
        forbid_parentheticals = True
        max_steps = 4

    return GuardContext(
        profile=profile,
        confidence=confidence,
        input_kind=input_kind,
        allowed_safe_commands=frozenset(allowed_commands),
        forbid_parentheticals=forbid_parentheticals,
        forbid_visual_refs=forbid_visual_refs,
        max_steps=max_steps,
        allow_commands_on_low=allow_commands_on_low,
    )
