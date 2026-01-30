"""Screen-reader profile transformation.

Transforms AssistResult for users consuming output via:
- Screen readers / TTS
- Braille displays
- Listen-first workflows

Invariants (non-negotiable):
1. No invented facts - only rephrases existing content
2. No invented commands - SAFE commands must be verbatim from input
3. SAFE-only remains absolute
4. Additive behavior - doesn't rewrite original output
5. Deterministic - no randomness, no network calls

Screen-reader-specific invariants:
6. No meaning in punctuation/formatting alone
7. No "visual navigation" references (see above, below, left, right, arrow)
8. No parentheticals as meaning carriers
9. Avoid dense inline abbreviations unless expanded
"""

from __future__ import annotations

import re
from typing import List, Optional

from ..render import AssistResult, Confidence

# Max step length (audio tolerates longer than visual)
MAX_STEP_LENGTH = 110

# Max note length
MAX_NOTE_LENGTH = 120

# Max steps by confidence
MAX_STEPS_DEFAULT = 5
MAX_STEPS_LOW = 3

# Boilerplate prefixes to strip
BOILERPLATE_PREFIXES = re.compile(
    r"^(re-?run:\s*|run:\s*|try:\s*|next:\s*|\$\s*|>\s*)", re.IGNORECASE
)

# Parenthetical patterns
PARENTHETICAL_RE = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]\s*")

# Visual navigation phrases to remove
VISUAL_NAV_PHRASES = re.compile(
    r"\b(see\s+)?(above|below|left|right|arrow)\b", re.IGNORECASE
)

# Abbreviation expansions (small, fixed set for determinism)
ABBREVIATIONS = [
    (re.compile(r"\bCLI\b"), "command line"),
    (re.compile(r"\bID\b"), "I D"),
    (re.compile(r"\bURL\b"), "U R L"),
    (re.compile(r"\bJSON\b"), "J S O N"),
    (re.compile(r"\benv\b"), "environment"),
    (re.compile(r"\bSFTP\b"), "S F T P"),
    (re.compile(r"\bSSH\b"), "S S H"),
    (re.compile(r"\bAPI\b"), "A P I"),
]

# Symbol replacements for better TTS
SYMBOL_REPLACEMENTS = [
    ("->", " to "),
    ("=>", " to "),
    (" & ", " and "),
]


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


def _remove_visual_references(s: str) -> str:
    """Remove visual navigation references."""
    result = VISUAL_NAV_PHRASES.sub("", s)
    # Clean up double spaces
    return re.sub(r"\s+", " ", result).strip()


def _expand_abbreviations(s: str) -> str:
    """Expand a small, fixed set of abbreviations for TTS."""
    for pattern, expansion in ABBREVIATIONS:
        s = pattern.sub(expansion, s)
    return s


def _replace_symbols(s: str) -> str:
    """Replace symbols that screen readers read awkwardly."""
    for old, new in SYMBOL_REPLACEMENTS:
        s = s.replace(old, new)
    # Clean up double spaces
    return re.sub(r"\s+", " ", s).strip()


def _one_sentence(s: str) -> str:
    """Keep only the first sentence/clause."""
    # Split on semicolon first
    if ";" in s:
        s = s.split(";")[0].strip()

    # Split on comma with multiple clauses (be conservative)
    # Only split if comma appears to separate independent clauses
    # For now, keep simple: first sentence only
    sentences = s.split(". ")
    if sentences:
        first = sentences[0].strip()
        return first
    return s


def _ensure_period(s: str) -> str:
    """Ensure string ends with a period."""
    s = s.strip()
    if s and not s.endswith("."):
        s += "."
    return s


def _cap_length(s: str, max_len: int = MAX_STEP_LENGTH) -> str:
    """Cap string length, truncating with ellipsis if needed."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def normalize_step(step: str) -> str:
    """Normalize a single step for screen-reader profile.

    Order of operations:
    1. Strip boilerplate prefixes
    2. Remove parentheticals
    3. Remove visual navigation references
    4. Expand abbreviations
    5. Replace awkward symbols
    6. Keep one sentence
    7. Ensure ends with period
    8. Cap length
    """
    s = step.strip()
    if not s:
        return s

    # 1. Strip boilerplate
    s = _strip_boilerplate(s)

    # 2. Remove parentheticals
    s = _remove_parentheticals(s)

    # 3. Remove visual navigation references
    s = _remove_visual_references(s)

    # 4. Expand abbreviations
    s = _expand_abbreviations(s)

    # 5. Replace symbols
    s = _replace_symbols(s)

    # 6. One sentence
    s = _one_sentence(s)

    # 7. Ensure period
    s = _ensure_period(s)

    # 8. Cap length
    s = _cap_length(s)

    return s


def normalize_safest_step(s: str) -> str:
    """Normalize safest_next_step for screen-reader profile.

    - One sentence max
    - No parentheticals
    - Ends with period
    """
    if not s:
        return "Follow the steps in order."

    # Remove parentheticals
    s = _remove_parentheticals(s)

    # Remove visual references
    s = _remove_visual_references(s)

    # Expand abbreviations
    s = _expand_abbreviations(s)

    # Replace symbols
    s = _replace_symbols(s)

    # One sentence
    s = _one_sentence(s)

    # Ensure period
    s = _ensure_period(s)

    return _cap_length(s, MAX_STEP_LENGTH)


def generate_summary(result: AssistResult) -> str:
    """Generate a one-sentence summary from the result.

    Uses available information without inventing facts.
    """
    # Try to derive from safest_next_step or first plan item
    if result.notes:
        # Look for "Original title:" note
        for note in result.notes:
            if note.lower().startswith("original title:"):
                title = note.split(":", 1)[1].strip()
                if title:
                    return _ensure_period(_cap_length(title, 80))

    # Fall back to a generic summary based on confidence
    if result.confidence == "High":
        return "A structured error was detected."
    elif result.confidence == "Medium":
        return "An error was detected with partial information."
    else:
        return "The input did not include a stable error identifier."


def reduce_plan(plan: List[str], confidence: Confidence) -> List[str]:
    """Reduce plan to appropriate number of normalized steps.

    - High/Medium confidence: max 5 steps
    - Low confidence: max 3 steps (reduce listening time)
    """
    if not plan:
        return ["Follow the tool's instructions."]

    max_steps = MAX_STEPS_LOW if confidence == "Low" else MAX_STEPS_DEFAULT

    normalized = [normalize_step(s) for s in plan if s.strip()]
    # Filter out empty results
    normalized = [s for s in normalized if s]

    if not normalized:
        return ["Follow the tool's instructions."]

    return normalized[:max_steps]


def select_safe_command(
    commands: List[str], confidence: Confidence
) -> Optional[str]:
    """Select at most one SAFE command for screen-reader profile.

    Rules:
    - Only include if confidence is High or Medium
    - Return first command only
    - No command synthesis
    - Never prefix with $ (screen readers read it as "dollar")
    """
    if confidence == "Low":
        return None

    if not commands:
        return None

    cmd = commands[0]
    # Strip leading $ if present (verbatim but remove the symbol)
    if cmd.startswith("$ "):
        cmd = cmd[2:]
    elif cmd.startswith("$"):
        cmd = cmd[1:]

    return cmd


def reduce_notes(notes: List[str], max_notes: int = 3) -> List[str]:
    """Reduce notes for screen-reader profile.

    - Max 3 notes
    - Each note is one sentence max
    - Remove parentheticals
    - Cap each at 120 chars
    """
    if not notes:
        return []

    reduced = []
    for note in notes[:max_notes]:
        n = _remove_parentheticals(note)
        n = _remove_visual_references(n)
        n = _expand_abbreviations(n)
        n = _replace_symbols(n)
        n = _one_sentence(n)
        n = _ensure_period(n)
        n = _cap_length(n, MAX_NOTE_LENGTH)
        if n and n != ".":
            reduced.append(n)

    return reduced


def apply_screen_reader(result: AssistResult) -> AssistResult:
    """Transform AssistResult for screen-reader profile.

    This transformation:
    1. Reduces plan steps (5 for High/Medium, 3 for Low)
    2. Normalizes step language for TTS
    3. Expands abbreviations
    4. Removes parentheticals and visual references
    5. Selects at most 1 SAFE command (none if Low confidence)
    6. Reduces notes to 3 max

    Invariants enforced:
    - No invented facts (only rephrases existing content)
    - No invented commands (SAFE commands verbatim from input)
    - Deterministic output
    """
    # Reduce and normalize plan
    reduced_plan = reduce_plan(result.plan, result.confidence)

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
