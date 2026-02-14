"""Severity definitions and utilities."""

from typing import Dict

SEVERITY_ORDER = ["info", "minor", "moderate", "serious", "critical"]
SEVERITY_RANK: Dict[str, int] = {k: i for i, k in enumerate(SEVERITY_ORDER)}


def normalize_severity(s: str) -> str:
    """Normalize severity string to canonical form."""
    s = (s or "").strip().lower()
    if s in SEVERITY_ORDER:
        return s
    # tolerate common alternates
    if s == "warning":
        return "moderate"
    if s == "error":
        return "serious"
    return "info"


def severity_rank(s: str) -> int:
    """Get integer rank of severity (higher is more severe)."""
    return SEVERITY_RANK.get(normalize_severity(s), -1)


def is_at_least(s: str, threshold: str) -> bool:
    """Check if severity `s` is at least as severe as `threshold`."""
    return severity_rank(s) >= severity_rank(threshold)
