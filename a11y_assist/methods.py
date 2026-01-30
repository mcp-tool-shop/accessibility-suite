"""Methods metadata helpers for audit traceability.

Provides utilities for adding method IDs and evidence anchors
to AssistResult without modifying core behavior.

These are audit-only and do not affect rendering output.
"""

from __future__ import annotations

from dataclasses import replace
from typing import List, Sequence

from .render import AssistResult, Evidence


# =============================================================================
# Method ID Constants
# =============================================================================

# Engine normalization methods
METHOD_NORMALIZE_CLI_ERROR = "engine.normalize.from_cli_error_v0_1"
METHOD_NORMALIZE_RAW_TEXT = "engine.normalize.from_raw_text"

# Profile methods
METHOD_PROFILE_LOWVISION = "profile.lowvision.apply"
METHOD_PROFILE_COGNITIVE_LOAD = "profile.cognitive_load.apply"
METHOD_PROFILE_SCREEN_READER = "profile.screen_reader.apply"
METHOD_PROFILE_DYSLEXIA = "profile.dyslexia.apply"
METHOD_PROFILE_PLAIN_LANGUAGE = "profile.plain_language.apply"

# Guard methods (coarse)
METHOD_GUARD_VALIDATE = "guard.validate_profile_transform"

# Guard methods (fine-grained)
METHOD_GUARD_ID_NO_INVENTION = "guard.id.no_invention"
METHOD_GUARD_CONFIDENCE_NO_INCREASE = "guard.confidence.no_increase"
METHOD_GUARD_COMMANDS_SAFE_ONLY = "guard.commands.safe_only"
METHOD_GUARD_PLAN_MAX_STEPS = "guard.plan.max_steps"
METHOD_GUARD_CONTENT_SUPPORT = "guard.content.support_heuristic"
METHOD_GUARD_NO_PARENTHETICALS = "guard.screen_reader.no_parentheticals"
METHOD_GUARD_NO_VISUAL_REFS = "guard.screen_reader.no_visual_refs"


# =============================================================================
# Helper Functions
# =============================================================================


def with_methods(result: AssistResult, methods: Sequence[str]) -> AssistResult:
    """Add method IDs to an AssistResult (deduplicating).

    Args:
        result: The AssistResult to update
        methods: Method IDs to add

    Returns:
        New AssistResult with methods added
    """
    current = list(result.methods_applied)
    for m in methods:
        if m not in current:
            current.append(m)
    return replace(result, methods_applied=tuple(current))


def with_evidence(result: AssistResult, evidence: Sequence[Evidence]) -> AssistResult:
    """Add evidence anchors to an AssistResult.

    Args:
        result: The AssistResult to update
        evidence: Evidence anchors to add

    Returns:
        New AssistResult with evidence added
    """
    current = list(result.evidence)
    current.extend(evidence)
    return replace(result, evidence=tuple(current))


def with_method(result: AssistResult, method: str) -> AssistResult:
    """Add a single method ID to an AssistResult.

    Args:
        result: The AssistResult to update
        method: Method ID to add

    Returns:
        New AssistResult with method added
    """
    return with_methods(result, [method])


def evidence_for_plan(
    plan: List[str],
    source_prefix: str = "cli.error.fix",
) -> List[Evidence]:
    """Generate evidence anchors for plan steps.

    Args:
        plan: List of plan steps
        source_prefix: Source path prefix (e.g., "cli.error.fix")

    Returns:
        List of Evidence objects mapping plan[i] to source[i]
    """
    return [
        Evidence(field=f"plan[{i}]", source=f"{source_prefix}[{i}]")
        for i in range(len(plan))
    ]


def evidence_for_commands(
    commands: List[str],
    source_indices: List[int],
    source_prefix: str = "cli.error.fix",
) -> List[Evidence]:
    """Generate evidence anchors for safe commands.

    Args:
        commands: List of safe commands
        source_indices: Index of each command in the source
        source_prefix: Source path prefix

    Returns:
        List of Evidence objects
    """
    result = []
    for i, idx in enumerate(source_indices):
        result.append(
            Evidence(
                field=f"next_safe_commands[{i}]",
                source=f"{source_prefix}[{idx}]",
            )
        )
    return result
