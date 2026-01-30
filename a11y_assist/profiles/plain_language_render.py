"""Plain-language profile renderer.

Output format optimized for maximum clarity:
- Simple structure
- Explicit labels
- Numeric steps
- Short sections
"""

from __future__ import annotations

from ..render import AssistResult


def render_plain_language(result: AssistResult) -> str:
    """Render AssistResult in plain-language format.

    Format:
    ASSIST (Plain Language)
    ID: <ID or none>
    Confidence: High | Medium | Low

    What happened:
    <one simple sentence>

    What to do next:
    <one sentence>

    Steps:
    1. <sentence>
    2. <sentence>
    ...

    Safe command:
    <command>
    """
    lines = []

    # Header
    lines.append("ASSIST (Plain Language)")
    lines.append(f"ID: {result.anchored_id or 'none'}")
    lines.append(f"Confidence: {result.confidence}")
    lines.append("")

    # What to do next (maps to safest_next_step)
    lines.append("What to do next:")
    lines.append(f"  {result.safest_next_step}")
    lines.append("")

    # Steps - simple numeric list
    if result.plan:
        lines.append("Steps:")
        for i, step in enumerate(result.plan, 1):
            lines.append(f"  {i}. {step}")
        lines.append("")

    # Safe command - only if confidence is not Low
    if result.next_safe_commands and result.confidence != "Low":
        lines.append("Safe command:")
        lines.append(f"  {result.next_safe_commands[0]}")
        lines.append("")

    # Notes are omitted in plain-language for simplicity
    # (keeping output as clear as possible)

    return "\n".join(lines)
