"""Cognitive-load profile transformation.

Transforms AssistResult for users who benefit from reduced cognitive load:
- ADHD / executive dysfunction
- Autism / sensory overload
- Anxiety under incident conditions
- Novices under stress

Invariants (non-negotiable):
1. No invented facts - only rephrases existing content
2. No invented commands - SAFE commands must be verbatim from input
3. SAFE-only remains absolute
4. Additive behavior - doesn't rewrite original output
5. Deterministic - no randomness, no network calls
"""

from __future__ import annotations

import re
from typing import List, Optional

from ..render import AssistResult, Confidence

# Boilerplate prefixes to strip
BOILERPLATE_PREFIXES = re.compile(
    r"^(re-?run:\s*|run:\s*|try:\s*|\$\s*|>\s*)", re.IGNORECASE
)

# Phrases to rewrite to imperative form
IMPERATIVE_REWRITES = [
    (re.compile(r"^you should\s+", re.IGNORECASE), "Do "),
    (re.compile(r"^please\s+", re.IGNORECASE), "Do "),
    (re.compile(r"^consider\s+", re.IGNORECASE), "Try "),
    (re.compile(r"^it may help to\s+", re.IGNORECASE), "Try "),
]

# Conjunction replacements
CONJUNCTION_REPLACEMENTS = [
    (" and then ", ". Then "),
    (" and ", ". "),
    (" but ", ". "),
]

# Parenthetical patterns
PARENTHETICAL_RE = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]\s*")

# Max step length
MAX_STEP_LENGTH = 90


def _strip_boilerplate(s: str) -> str:
    """Strip boilerplate prefixes from a string."""
    return BOILERPLATE_PREFIXES.sub("", s).strip()


def _remove_parentheticals(s: str) -> str:
    """Remove parenthetical content (...) and [...] from string."""
    result = PARENTHETICAL_RE.sub(" ", s).strip()
    # If removal empties the string, revert
    if not result:
        return s
    # Clean up double spaces
    return re.sub(r"\s+", " ", result)


def _to_imperative(s: str) -> str:
    """Convert phrases to imperative form."""
    for pattern, replacement in IMPERATIVE_REWRITES:
        s = pattern.sub(replacement, s)
    return s


def _reduce_conjunctions(s: str) -> str:
    """Replace conjunctions, keep only first sentence."""
    for old, new in CONJUNCTION_REPLACEMENTS:
        s = s.replace(old, new)

    # Keep only first sentence
    sentences = s.split(". ")
    if sentences:
        first = sentences[0].strip()
        if first and not first.endswith("."):
            first += "."
        return first
    return s


def _cap_length(s: str, max_len: int = MAX_STEP_LENGTH) -> str:
    """Cap string length, truncating with ellipsis if needed."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def normalize_step(step: str) -> str:
    """Normalize a single step according to cognitive-load rules.

    Order of operations:
    1. Strip boilerplate prefixes
    2. Remove parentheticals
    3. Convert to imperative form
    4. Reduce conjunctions (keep first sentence)
    5. Cap length at 90 chars
    """
    s = step.strip()
    if not s:
        return s

    # 1. Strip boilerplate
    s = _strip_boilerplate(s)

    # 2. Remove parentheticals
    s = _remove_parentheticals(s)

    # 3. Convert to imperative
    s = _to_imperative(s)

    # 4. Reduce conjunctions
    s = _reduce_conjunctions(s)

    # 5. Cap length
    s = _cap_length(s)

    return s


def normalize_safest_step(s: str) -> str:
    """Normalize safest_next_step for cognitive-load.

    - Remove parentheticals
    - Remove subordinate clauses (split on ; or ,)
    - Ensure ends with period
    - One sentence max
    """
    if not s:
        return "Follow the Fix steps."

    # Remove parentheticals
    s = _remove_parentheticals(s)

    # Split on semicolon or comma, keep first segment
    for sep in [";", ","]:
        if sep in s:
            s = s.split(sep)[0].strip()
            break

    # Reduce conjunctions to get one sentence
    s = _reduce_conjunctions(s)

    # Ensure ends with period
    s = s.strip()
    if s and not s.endswith("."):
        s += "."

    return _cap_length(s, MAX_STEP_LENGTH)


def reduce_plan(plan: List[str], max_steps: int = 3) -> List[str]:
    """Reduce plan to max_steps normalized items.

    No merging, no summarization beyond normalization.
    """
    if not plan:
        return ["Follow the tool's Fix steps in order."]

    normalized = [normalize_step(s) for s in plan if s.strip()]
    # Filter out empty results
    normalized = [s for s in normalized if s]

    if not normalized:
        return ["Follow the tool's Fix steps in order."]

    return normalized[:max_steps]


def select_safe_command(
    commands: List[str], confidence: Confidence
) -> Optional[str]:
    """Select at most one SAFE command for cognitive-load.

    Rules:
    - Only include if confidence is High or Medium
    - Return first command only
    - No command synthesis
    """
    if confidence == "Low":
        return None

    if not commands:
        return None

    # Return first command, no modification (must be verbatim)
    return commands[0]


def reduce_notes(notes: List[str], max_notes: int = 2) -> List[str]:
    """Reduce notes to max_notes, remove parentheticals, cap length."""
    if not notes:
        return []

    reduced = []
    for note in notes[:max_notes]:
        n = _remove_parentheticals(note)
        n = _cap_length(n, 100)
        if n:
            reduced.append(n)

    return reduced


def apply_cognitive_load(result: AssistResult) -> AssistResult:
    """Transform AssistResult for cognitive-load profile.

    This transformation:
    1. Reduces plan to exactly 3 steps max
    2. Normalizes step language (no conjunctions, parentheticals)
    3. Selects at most 1 SAFE command (none if Low confidence)
    4. Reduces notes to 2 max

    Invariants enforced:
    - No invented facts (only rephrases existing content)
    - No invented commands (SAFE commands verbatim from input)
    - Deterministic output
    """
    # Reduce and normalize plan
    reduced_plan = reduce_plan(result.plan)

    # Normalize safest next step
    normalized_safest = normalize_safest_step(result.safest_next_step)

    # Select single SAFE command (or None)
    safe_cmd = select_safe_command(result.next_safe_commands, result.confidence)
    safe_commands = [safe_cmd] if safe_cmd else []

    # Reduce notes
    reduced_notes = reduce_notes(result.notes)

    return AssistResult(
        anchored_id=result.anchored_id,
        confidence=result.confidence,
        safest_next_step=normalized_safest,
        plan=reduced_plan,
        next_safe_commands=safe_commands,
        notes=reduced_notes,
    )
