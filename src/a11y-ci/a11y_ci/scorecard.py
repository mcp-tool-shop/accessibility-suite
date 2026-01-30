"""Scorecard loading and severity handling.

This reads a11y-lint scorecards but is defensive: it supports either:
- summary bucket counts, and/or
- findings[] with severity and an ID (id, rule_id, or finding_id)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

SEVERITY_ORDER = ["info", "minor", "moderate", "serious", "critical"]


def severity_ge(a: str, threshold: str) -> bool:
    """Check if severity `a` is >= `threshold`."""
    try:
        return SEVERITY_ORDER.index(a) >= SEVERITY_ORDER.index(threshold)
    except ValueError:
        return False


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


def finding_id(f: Dict[str, Any]) -> str:
    """Extract finding ID from a finding dict, tolerating different key names."""
    for k in ("id", "rule_id", "finding_id", "code"):
        v = f.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    # fallback: deterministic-ish
    title = f.get("title") or f.get("message") or "unknown"
    return f"UNKNOWN:{str(title)[:80]}"


@dataclass(frozen=True)
class Scorecard:
    """Parsed scorecard with findings and computed counts."""

    raw: Dict[str, Any]
    findings: List[Dict[str, Any]]

    @staticmethod
    def load(path: str) -> "Scorecard":
        """Load a scorecard from a JSON file."""
        p = Path(path)
        obj = json.loads(p.read_text(encoding="utf-8"))
        findings = obj.get("findings") or []
        if not isinstance(findings, list):
            findings = []
        # normalize severities
        for f in findings:
            if isinstance(f, dict):
                f["severity"] = normalize_severity(str(f.get("severity", "info")))
        return Scorecard(raw=obj, findings=[f for f in findings if isinstance(f, dict)])

    def counts(self) -> Dict[str, int]:
        """Get severity counts. Prefers summary if present; otherwise computes from findings."""
        s = self.raw.get("summary")
        if isinstance(s, dict) and all(k in s for k in SEVERITY_ORDER):
            out = {k: int(s.get(k, 0) or 0) for k in SEVERITY_ORDER}
            return out
        out = {k: 0 for k in SEVERITY_ORDER}
        for f in self.findings:
            out[normalize_severity(str(f.get("severity")))] += 1
        return out

    def ids_at_or_above(self, threshold: str) -> List[str]:
        """Get sorted list of finding IDs at or above severity threshold."""
        thr = normalize_severity(threshold)
        ids = []
        for f in self.findings:
            sev = normalize_severity(str(f.get("severity")))
            if severity_ge(sev, thr):
                ids.append(finding_id(f))
        return sorted(set(ids))

    def findings_at_or_above(self, threshold: str) -> List[Dict[str, Any]]:
        """Get findings at or above severity threshold."""
        thr = normalize_severity(threshold)
        return [
            f
            for f in self.findings
            if severity_ge(normalize_severity(str(f.get("severity"))), thr)
        ]
