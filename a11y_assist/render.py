"""Low-vision assist block rendering.

Clear labels, spacing, short lines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Tuple

Confidence = Literal["High", "Medium", "Low"]


@dataclass(frozen=True)
class Evidence:
    """Source anchor for audit traceability.

    Maps an output field back to its input source.
    """

    field: str  # e.g., "safest_next_step", "plan[0]"
    source: str  # e.g., "cli.error.fix[1]", "raw_text:Fix:2"
    note: Optional[str] = None


@dataclass(frozen=True)
class AssistResult:
    """Structured assist result with optional audit metadata."""

    anchored_id: Optional[str]
    confidence: Confidence
    safest_next_step: str
    plan: List[str]
    next_safe_commands: List[str]  # SAFE-only in v0.1
    notes: List[str]

    # Optional audit metadata (does not affect rendering)
    methods_applied: Tuple[str, ...] = field(default_factory=tuple)
    evidence: Tuple[Evidence, ...] = field(default_factory=tuple)


def render_assist(result: AssistResult) -> str:
    """Render an AssistResult to low-vision-friendly text.

    Format:
        ASSIST (Low Vision):
        - Anchored to: ID or (none)
        - Confidence: High/Medium/Low

        Safest next step:
          <step>

        Plan:
          1) step
          2) step

        Next (SAFE):
          <command>

        Notes:
          - note
    """
    lines: List[str] = []
    lines.append("ASSIST (Low Vision):")

    if result.anchored_id:
        lines.append(f"- Anchored to: {result.anchored_id}")
    else:
        lines.append("- Anchored to: (none)")

    lines.append(f"- Confidence: {result.confidence}")
    lines.append("")
    lines.append("Safest next step:")
    lines.append(f"  {result.safest_next_step}")
    lines.append("")

    lines.append("Plan:")
    for i, step in enumerate(result.plan[:5], start=1):
        lines.append(f"  {i}) {step}")
    if len(result.plan) > 5:
        lines.append("  ...")

    if result.next_safe_commands:
        lines.append("")
        lines.append("Next (SAFE):")
        for cmd in result.next_safe_commands[:3]:
            lines.append(f"  {cmd}")

    if result.notes:
        lines.append("")
        lines.append("Notes:")
        for n in result.notes[:5]:
            lines.append(f"  - {n}")

    return "\n".join(lines) + "\n"
