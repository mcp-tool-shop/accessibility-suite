"""Core policy gate logic.

Rules:
1. Current has any findings at/above fail_on threshold -> FAIL
2. If baseline provided, regression in count at/above threshold -> FAIL
3. If baseline provided, new finding IDs at/above threshold -> FAIL
4. Expired allowlist entries -> FAIL (no permanent exceptions)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .allowlist import Allowlist
from .scorecard import (
    SEVERITY_ORDER,
    Scorecard,
    finding_id,
    normalize_severity,
    severity_ge,
)


@dataclass(frozen=True)
class GateResult:
    """Result of a gate evaluation."""

    ok: bool
    reasons: List[str]
    current_blocking_ids: List[str]
    new_blocking_ids: List[str]
    current_counts: Dict[str, int]
    baseline_counts: Optional[Dict[str, int]]


def apply_allowlist(scorecard: Scorecard, suppressed: Set[str]) -> Scorecard:
    """Return a new scorecard with suppressed findings removed."""
    if not suppressed:
        return scorecard
    filtered = [f for f in scorecard.findings if finding_id(f) not in suppressed]
    raw = dict(scorecard.raw)
    raw["findings"] = filtered
    # keep summary if present but it's now stale; recompute counts from findings downstream
    raw.pop("summary", None)
    return Scorecard(raw=raw, findings=filtered)


def gate(
    current: Scorecard,
    baseline: Optional[Scorecard],
    fail_on: str = "serious",
    allowlist: Optional[Allowlist] = None,
) -> GateResult:
    """Evaluate the policy gate.

    Args:
        current: Current scorecard to evaluate
        baseline: Optional baseline scorecard for regression detection
        fail_on: Severity threshold (default: serious)
        allowlist: Optional allowlist for suppressions

    Returns:
        GateResult with pass/fail status and reasons
    """
    fail_on = normalize_severity(fail_on)

    suppressed: Set[str] = set()
    reasons: List[str] = []

    if allowlist:
        suppressed = allowlist.suppressed_ids()
        expired = allowlist.expired_entries()
        if expired:
            reasons.append(
                "Allowlist contains expired entries (must be renewed or removed): "
                + ", ".join([e.finding_id for e in expired])
            )

    cur = apply_allowlist(current, suppressed)
    base = apply_allowlist(baseline, suppressed) if baseline else None

    cur_counts = cur.counts()
    base_counts = base.counts() if base else None

    # Rule 1: current has any at/above fail_on
    cur_blocking = cur.ids_at_or_above(fail_on)
    if cur_blocking:
        reasons.append(
            f"Current run has {len(cur_blocking)} finding(s) at or above '{fail_on}'."
        )

    new_blocking: List[str] = []
    if base:
        # Rule 2: serious+ regression count
        # We treat fail_on as the regression threshold too (default serious)
        def count_at_or_above(counts: Dict[str, int], thr: str) -> int:
            total = 0
            for sev, n in counts.items():
                if severity_ge(sev, thr):
                    total += int(n)
            return total

        cur_n = count_at_or_above(cur_counts, fail_on)
        base_n = count_at_or_above(base_counts or {}, fail_on)
        if cur_n > base_n:
            reasons.append(
                f"Regression: current has {cur_n} finding(s) at/above '{fail_on}' "
                f"vs baseline {base_n}."
            )

        # Rule 3: new blocking IDs at/above threshold
        base_ids = set(base.ids_at_or_above(fail_on))
        cur_ids = set(cur.ids_at_or_above(fail_on))
        new_blocking = sorted(cur_ids - base_ids)
        if new_blocking:
            reasons.append(
                f"New finding(s) at/above '{fail_on}' not present in baseline: "
                + ", ".join(new_blocking[:20])
                + (" ..." if len(new_blocking) > 20 else "")
            )

    ok = len([r for r in reasons if r]) == 0
    return GateResult(
        ok=ok,
        reasons=reasons,
        current_blocking_ids=cur_blocking,
        new_blocking_ids=new_blocking,
        current_counts=cur_counts,
        baseline_counts=base_counts,
    )
