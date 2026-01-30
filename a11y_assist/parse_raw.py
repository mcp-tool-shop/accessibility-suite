"""Best-effort parser for raw CLI output.

Never invents an ID. Confidence is Low/Medium only.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# Match [OK]/[WARN]/[ERROR] with optional (ID: ...)
STATUS_RE = re.compile(r"^\[(OK|WARN|ERROR)\]\s+(.+?)\s*(\((ID:\s*.+)\))?\s*$")

# Match (ID: NAMESPACE.CATEGORY.DETAIL) anywhere in text
ID_IN_PARENS_RE = re.compile(r"\(ID:\s*([A-Z][A-Z0-9]*(?:\.[A-Z0-9]+)+)\)")


def extract_id(text: str) -> Optional[str]:
    """Extract an error ID from text if present."""
    m = ID_IN_PARENS_RE.search(text)
    if not m:
        return None
    return m.group(1)


def extract_blocks(lines: List[str]) -> Dict[str, List[str]]:
    """Extract What:/Why:/Fix: blocks from lines."""
    blocks: Dict[str, List[str]] = {"What:": [], "Why:": [], "Fix:": []}
    current: Optional[str] = None

    for line in lines:
        s = line.rstrip("\n")
        stripped = s.strip()

        # Check if this is a block header
        if stripped in blocks:
            current = stripped
            continue

        # If we're in a block and line is indented, add it
        if current and s.startswith("  "):
            blocks[current].append(stripped)
        elif current and stripped == "":
            # Allow blank lines inside blocks
            continue
        else:
            # Non-indented lines end the current block
            current = None

    return blocks


def parse_raw(text: str) -> Tuple[Optional[str], str, Dict[str, List[str]]]:
    """Parse raw CLI output.

    Returns:
        (error_id or None, status string, blocks dict)
    """
    lines = text.splitlines()
    status = "UNKNOWN"

    if lines:
        first_line = lines[0].strip()
        m = STATUS_RE.match(first_line)
        if m:
            status = m.group(1)

    err_id = extract_id(text)
    blocks = extract_blocks(lines)

    return err_id, status, blocks
