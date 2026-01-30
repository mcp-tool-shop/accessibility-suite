"""Plain-language profile transform.

Maximizes understandability through:
- Active voice
- Present tense
- One clause per sentence
- No idioms or metaphors
- No jargon unless already present
- Short, clear sentences

Max 4 steps. Confidence preserved or downgraded.
"""

from __future__ import annotations

import re
from typing import List

from ..render import AssistResult

# Parenthetical pattern
PARENTHETICAL = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]\s*")

# Conjunction pattern for splitting
CONJUNCTIONS = re.compile(r"\s*(?:,\s*and\s+|,\s*but\s+|,\s*or\s+|\s+and\s+|\s+but\s+|\s+or\s+)")

# Subordinate clause starters
SUBORDINATE = re.compile(
    r"\s*(?:,\s*)?(?:which|that|who|whom|whose|when|where|while|although|because|if|unless|until|after|before|since)\s+.*$",
    re.IGNORECASE,
)


def _remove_parentheticals(text: str) -> str:
    """Remove parenthetical content."""
    return PARENTHETICAL.sub(" ", text).strip()


def _simplify_sentence(text: str) -> str:
    """Simplify a sentence to one clause.

    - Remove parentheticals
    - Split on conjunctions, keep first clause
    - Remove subordinate clauses
    """
    result = _remove_parentheticals(text)

    # Split on conjunctions, keep first part
    parts = CONJUNCTIONS.split(result, maxsplit=1)
    if parts:
        result = parts[0].strip()

    # Remove subordinate clauses
    result = SUBORDINATE.sub("", result).strip()

    # Clean up trailing punctuation issues
    result = re.sub(r"\s+", " ", result).strip()

    # Ensure ends with period if it doesn't have punctuation
    if result and not result[-1] in ".!?:":
        result = result + "."

    return result


def _normalize_step(step: str) -> str:
    """Normalize a step for plain-language profile.

    - Simplify to one clause
    - Remove complex structures
    """
    result = _simplify_sentence(step)

    # Remove any remaining parentheticals
    result = _remove_parentheticals(result)

    # Clean up
    result = re.sub(r"\s+", " ", result).strip()

    return result


def apply_plain_language(result: AssistResult) -> AssistResult:
    """Apply plain-language profile transformation.

    - Simplify sentences to one clause
    - Remove parentheticals
    - Remove subordinate clauses
    - Max 4 steps
    - Preserve or downgrade confidence
    """
    # Simplify safest next step
    safest = _simplify_sentence(result.safest_next_step)

    # Normalize and limit plan steps
    plan: List[str] = []
    for step in result.plan[:4]:  # Max 4 steps
        normalized = _normalize_step(step)
        if normalized and len(normalized) > 2:  # Skip trivially empty
            plan.append(normalized)

    # Simplify notes (max 2)
    notes: List[str] = []
    for note in result.notes[:2]:
        simplified = _simplify_sentence(note)
        if simplified and len(simplified) > 2:
            notes.append(simplified)

    # Commands: preserve only safe commands, max 1 for simplicity
    commands = result.next_safe_commands[:1]

    return AssistResult(
        anchored_id=result.anchored_id,
        confidence=result.confidence,  # Preserved (guard enforces no increase)
        safest_next_step=safest,
        plan=plan,
        next_safe_commands=commands,
        notes=notes,
    )
