"""Screen-reader profile renderer.

Renders AssistResult with screen-reader specific formatting:
- Spoken-friendly headers (no visual punctuation as meaning carriers)
- Fixed section order for predictability
- Step N: labels instead of numbers alone
- No parentheticals in output
"""

from __future__ import annotations

from typing import List

from ..render import AssistResult
from .screen_reader import generate_summary


def render_screen_reader(result: AssistResult) -> str:
    """Render an AssistResult in screen-reader format.

    Format:
        ASSIST. Profile: Screen reader.
        Anchored I D: <id or none>.
        Confidence: High|Medium|Low.

        Summary: <very short>.

        Safest next step: <one sentence>.

        Steps:
        Step 1: <step>.
        Step 2: <step>.
        ...

        Next safe command:
        <command>

        Note: <note>.
        OR
        Notes:
        <note>.
        <note>.
    """
    lines: List[str] = []

    # Header (spoken-friendly)
    lines.append("ASSIST. Profile: Screen reader.")

    # Anchored ID (spelled out for TTS)
    if result.anchored_id:
        lines.append(f"Anchored I D: {result.anchored_id}.")
    else:
        lines.append("Anchored I D: none.")

    lines.append(f"Confidence: {result.confidence}.")
    lines.append("")

    # Summary (one sentence)
    summary = generate_summary(result)
    lines.append(f"Summary: {summary}")
    lines.append("")

    # Safest next step
    lines.append(f"Safest next step: {result.safest_next_step}")
    lines.append("")

    # Steps with "Step N:" labels
    lines.append("Steps:")
    for i, step in enumerate(result.plan, start=1):
        lines.append(f"Step {i}: {step}")

    # Next safe command (only if present)
    if result.next_safe_commands:
        lines.append("")
        lines.append("Next safe command:")
        # Command alone on its own line, no $ prefix
        lines.append(result.next_safe_commands[0])

    # Notes
    if result.notes:
        lines.append("")
        if len(result.notes) == 1:
            lines.append(f"Note: {result.notes[0]}")
        else:
            lines.append("Notes:")
            for note in result.notes:
                lines.append(note)

    return "\n".join(lines) + "\n"
