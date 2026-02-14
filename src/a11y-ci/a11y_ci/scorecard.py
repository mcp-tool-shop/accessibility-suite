"""Scorecard loading and severity handling.

This reads a11y-lint scorecards but is defensive: it supports either:
- summary bucket counts, and/or
- findings[] with severity and an ID (id, rule_id, or finding_id)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from .severity import (
    SEVERITY_ORDER,
    is_at_least,
    normalize_severity,
    severity_rank,
)


def compute_fingerprint(f: Dict[str, Any]) -> str:
    """Compute a stable hash for a finding."""
    # Core identity fields
    identity = {
        "id": f.get("id"),
        "message": f.get("message"),
        "location": f.get("location"),
    }
    # Use a sorted JSON dump for stability
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def finding_id(f: Dict[str, Any]) -> str:
    """Extract finding ID from a finding dict, tolerating different key names."""
    for k in ("id", "rule_id", "finding_id", "code"):
        v = f.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    # fallback: deterministic-ish
    title = f.get("title") or f.get("message") or "unknown"
    return f"UNKNOWN:{str(title)[:80]}"

# Remove legacy severity functions (now in severity.py)


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

        # Validate against schema
        try:
            schema_path = Path(__file__).parent / "schema" / "scorecard.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.validate(instance=obj, schema=schema)
        except FileNotFoundError:
            # Fallback for dev/test environments where schema might not be installed alongside
            pass

        findings = obj.get("findings") or []
        if not isinstance(findings, list):
            findings = []
        # normalize severities
        for f in findings:
            if isinstance(f, dict):
                f["severity"] = normalize_severity(str(f.get("severity", "info")))
        return Scorecard(raw=obj, findings=[f for f in findings if isinstance(f, dict)]).canonicalize()


    def canonicalize(self) -> "Scorecard":
        """Return a new Scorecard with stable, de-duped findings."""
        # 1. Compute fingerprints & De-dupe
        unique_findings: Dict[str, Dict[str, Any]] = {}

        for f in self.findings:
            # Copy to avoid mutating original if it was shared
            f_copy = f.copy()

            # Ensure ID is standard (handle legacy rule_id)
            if "id" not in f_copy:
                f_copy["id"] = finding_id(f_copy)

            # Ensure fingerprint
            if not f_copy.get("fingerprint"):
                f_copy["fingerprint"] = compute_fingerprint(f_copy)
            
            fp = f_copy["fingerprint"]

            # De-dupe logic:
            # If we already have this fingerprint, we check if the new one is "better"
            # For now, we assume same fingerprint = same issue.
            # We'll just keep the first one, or maybe the one with more info?
            # Let's keep the one with the highest severity rank just in case
            if fp not in unique_findings:
                unique_findings[fp] = f_copy
            else:
                current_sev = severity_rank(unique_findings[fp].get("severity", "info"))
                new_sev = severity_rank(f_copy.get("severity", "info"))
                if new_sev > current_sev:
                    unique_findings[fp] = f_copy

        # 2. Sort deterministically
        # Sort key: (Severity Rule (Desc), ID (Asc), Fingerprint (Asc))
        sorted_findings = sorted(
            unique_findings.values(),
            key=lambda x: (
                -1 * severity_rank(x.get("severity", "info")),  # Critical (4) -> Info (0). Multiply by -1 for Desc
                x.get("id", ""),
                x.get("fingerprint", ""),
            ),
        )

        return replace(self, findings=sorted_findings)


    def counts(self) -> Dict[str, int]:
        """Get severity counts. Computed from canonical findings (ignores legacy summary)."""
        out = {k: 0 for k in SEVERITY_ORDER}
        for f in self.findings:
            sev = normalize_severity(str(f.get("severity", "info")))
            out[sev] += 1
        return out

    def ids_at_or_above(self, threshold: str) -> List[str]:
        """Get sorted list of finding IDs at or above severity threshold."""
        thr = normalize_severity(threshold)
        ids = []
        for f in self.findings:
            sev = normalize_severity(str(f.get("severity")))
            if is_at_least(sev, thr):
                ids.append(finding_id(f))
        return sorted(set(ids))

    def findings_at_or_above(self, threshold: str) -> List[Dict[str, Any]]:
        """Get findings at or above severity threshold."""
        thr = normalize_severity(threshold)
        return [
            f
            for f in self.findings
            if is_at_least(normalize_severity(str(f.get("severity"))), thr)
        ]
