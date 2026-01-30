"""Dyslexia profile renderer.

Output format optimized for reduced reading friction:
- Extra vertical spacing between sections
- One idea per line
- Explicit labels
- Numbered steps with "Step N:" prefix
- No dense paragraphs
"""

from __future__ import annotations

from ..render import AssistResult


def render_dyslexia(result: AssistResult) -> str:
    """Render AssistResult in dyslexia-friendly format.

    Format:
    ASSIST (Dyslexia):
    Anchored ID: <ID or none>
    Confidence: High | Medium | Low

    Summary:
    <derived from context>

    Safest next step:
    <one sentence>

    Plan:
    - Step 1: <sentence>
    - Step 2: <sentence>
    ...

    Next safe command:
    <command>

    Notes:
    - <sentence>
    """
    lines = []

    # Header - each piece on its own line
    lines.append("ASSIST (Dyslexia):")
    lines.append("")
    lines.append(f"Anchored ID: {result.anchored_id or 'none'}")
    lines.append("")
    lines.append(f"Confidence: {result.confidence}")
    lines.append("")

    # Safest next step - explicit label
    lines.append("Safest next step:")
    lines.append(f"  {result.safest_next_step}")
    lines.append("")

    # Plan - numbered with "Step N:" prefix
    if result.plan:
        lines.append("Plan:")
        for i, step in enumerate(result.plan, 1):
            lines.append(f"  - Step {i}: {step}")
        lines.append("")

    # Next safe command - only if confidence is not Low
    if result.next_safe_commands and result.confidence != "Low":
        lines.append("Next safe command:")
        # Show first command only for simplicity
        lines.append(f"  {result.next_safe_commands[0]}")
        lines.append("")

    # Notes - max 2, each on its own line
    if result.notes:
        lines.append("Notes:")
        for note in result.notes[:2]:
            lines.append(f"  - {note}")
        lines.append("")

    return "\n".join(lines)
