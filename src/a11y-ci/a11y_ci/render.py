"""Low-vision-first CLI message rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

Status = Literal["OK", "WARN", "ERROR"]


@dataclass(frozen=True)
class CliMessage:
    """Structured CLI message following the What/Why/Fix contract."""

    status: Status
    id: str
    title: str
    what: List[str]
    why: List[str]
    fix: List[str]


def render(msg: CliMessage) -> str:
    """Render a CLI message to the low-vision-first format.

    Format:
        [STATUS] Title (ID: NAMESPACE.CATEGORY.DETAIL)

        What:
          What happened.

        Why:
          Why it happened.

        Fix:
          How to fix it.
    """
    head = f"[{msg.status}] {msg.title} (ID: {msg.id})"
    parts = [head, ""]
    parts.append("What:")
    parts.extend([f"  {x}" for x in msg.what])
    parts.append("")
    parts.append("Why:")
    parts.extend([f"  {x}" for x in msg.why])
    parts.append("")
    parts.append("Fix:")
    parts.extend([f"  {x}" for x in msg.fix])
    return "\n".join(parts) + "\n"
