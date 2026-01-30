"""Dyslexia profile transform.

Reduces reading friction without reducing information:
- Extra vertical spacing between sections
- One idea per line
- No dense paragraphs
- No italics/all-caps emphasis
- Labels always explicit
- No parentheticals
- No symbolic emphasis
- Abbreviations expanded once

Max 5 steps. Confidence preserved or downgraded.
"""

from __future__ import annotations

import re
from typing import List

from ..render import AssistResult

# Abbreviation expansions (letter-spelled for clarity)
ABBREVIATIONS = {
    r"\bCLI\b": "command line",
    r"\bID\b": "I D",
    r"\bJSON\b": "J S O N",
    r"\bAPI\b": "A P I",
    r"\bSFTP\b": "S F T P",
    r"\bSSH\b": "S S H",
    r"\bURL\b": "U R L",
    r"\bHTTP\b": "H T T P",
    r"\bHTTPS\b": "H T T P S",
}

# Parenthetical pattern
PARENTHETICAL = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]\s*")

# Visual reference pattern
VISUAL_REF = re.compile(r"\b(see\s+)?(above|below|left|right|arrow)\b", re.IGNORECASE)

# Symbolic emphasis pattern (*, _, →, emojis)
SYMBOLIC_EMPHASIS = re.compile(r"[*_→←↑↓]|[\U0001F300-\U0001F9FF]")


def _expand_abbreviations(text: str) -> str:
    """Expand abbreviations once for readability."""
    result = text
    for pattern, expansion in ABBREVIATIONS.items():
        result = re.sub(pattern, expansion, result, count=1)
    return result


def _remove_parentheticals(text: str) -> str:
    """Remove parenthetical content."""
    return PARENTHETICAL.sub(" ", text).strip()


def _remove_visual_refs(text: str) -> str:
    """Remove visual navigation references."""
    return VISUAL_REF.sub("", text).strip()


def _remove_symbolic_emphasis(text: str) -> str:
    """Remove symbolic emphasis characters."""
    return SYMBOLIC_EMPHASIS.sub("", text).strip()


def _normalize_step(step: str) -> str:
    """Normalize a step for dyslexia profile.

    - Remove parentheticals
    - Remove visual references
    - Remove symbolic emphasis
    - Expand abbreviations
    - Truncate to 110 chars
    """
    result = step
    result = _remove_parentheticals(result)
    result = _remove_visual_refs(result)
    result = _remove_symbolic_emphasis(result)
    result = _expand_abbreviations(result)

    # Clean up multiple spaces
    result = re.sub(r"\s+", " ", result).strip()

    # Truncate if too long
    if len(result) > 110:
        result = result[:107] + "..."

    return result


def _normalize_safest_step(text: str) -> str:
    """Normalize safest next step."""
    result = _remove_parentheticals(text)
    result = _remove_visual_refs(result)
    result = _remove_symbolic_emphasis(result)
    result = _expand_abbreviations(result)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def apply_dyslexia(result: AssistResult) -> AssistResult:
    """Apply dyslexia profile transformation.

    - Expand abbreviations
    - Remove parentheticals
    - Remove visual references
    - Remove symbolic emphasis
    - Max 5 steps
    - Preserve or downgrade confidence
    """
    # Normalize safest next step
    safest = _normalize_safest_step(result.safest_next_step)

    # Normalize and limit plan steps
    plan: List[str] = []
    for step in result.plan[:5]:  # Max 5 steps
        normalized = _normalize_step(step)
        if normalized:
            plan.append(normalized)

    # Normalize notes (max 2)
    notes: List[str] = []
    for note in result.notes[:2]:  # Max 2 notes
        normalized = _remove_parentheticals(note)
        normalized = _remove_symbolic_emphasis(normalized)
        normalized = _expand_abbreviations(normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if normalized:
            notes.append(normalized)

    # Commands: preserve only safe commands, max 3
    commands = result.next_safe_commands[:3]

    return AssistResult(
        anchored_id=result.anchored_id,
        confidence=result.confidence,  # Preserved (guard enforces no increase)
        safest_next_step=safest,
        plan=plan,
        next_safe_commands=commands,
        notes=notes,
    )
