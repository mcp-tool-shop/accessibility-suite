"""Cognitive-load profile renderer.

Renders AssistResult with cognitive-load specific formatting:
- Goal line at top
- First/Next/Last labels instead of numbers
- Maximum clarity and brevity
"""

from __future__ import annotations

from typing import List

from ..render import AssistResult

# Step labels for cognitive-load profile
STEP_LABELS = ["First", "Next", "Last"]


def render_cognitive_load(result: AssistResult) -> str:
    """Render an AssistResult in cognitive-load format.

    Format:
        ASSIST (Cognitive Load):
        - Anchored to: ID or (none)
        - Confidence: High/Medium/Low

        Goal: Get back to a known-good state.

        Safest next step:
          <step>

        Plan:
          First: <step>
          Next: <step>
          Last: <step>

        Next (SAFE):
          <command>   (only if confidence is High or Medium)

        Notes:
          - note
    """
    lines: List[str] = []

    # Header
    lines.append("ASSIST (Cognitive Load):")

    if result.anchored_id:
        lines.append(f"- Anchored to: {result.anchored_id}")
    else:
        lines.append("- Anchored to: (none)")

    lines.append(f"- Confidence: {result.confidence}")
    lines.append("")

    # Goal (fixed text)
    lines.append("Goal: Get back to a known-good state.")
    lines.append("")

    # Safest next step
    lines.append("Safest next step:")
    lines.append(f"  {result.safest_next_step}")
    lines.append("")

    # Plan with First/Next/Last labels
    lines.append("Plan:")
    for i, step in enumerate(result.plan[:3]):
        label = STEP_LABELS[i] if i < len(STEP_LABELS) else f"Step {i + 1}"
        lines.append(f"  {label}: {step}")

    # Next (SAFE) - only show if commands exist
    # Note: cognitive-load transform already filters for confidence
    if result.next_safe_commands:
        lines.append("")
        lines.append("Next (SAFE):")
        # Only show first command for cognitive-load
        lines.append(f"  {result.next_safe_commands[0]}")

    # Notes (max 2, already reduced by transform)
    if result.notes:
        lines.append("")
        lines.append("Notes:")
        for note in result.notes[:2]:
            lines.append(f"  - {note}")

    return "\n".join(lines) + "\n"
