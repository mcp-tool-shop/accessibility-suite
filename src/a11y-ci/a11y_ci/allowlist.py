"""Allowlist handling with schema validation and expiry checking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from importlib import resources
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from jsonschema import Draft202012Validator


def _load_schema() -> Dict[str, Any]:
    """Load the allowlist JSON schema."""
    with resources.files("a11y_ci.schemas").joinpath("allowlist.schema.json").open("rb") as f:
        return json.load(f)


_SCHEMA = _load_schema()
_VALIDATOR = Draft202012Validator(_SCHEMA)


class AllowlistError(Exception):
    """Raised when allowlist validation fails."""

    pass


@dataclass(frozen=True)
class AllowlistEntry:
    """A single allowlist entry."""

    id: str  # The ID or fingerprint being allowed
    kind: str  # 'id' or 'fingerprint'
    expires: str
    reason: str
    owner: str
    ticket: Optional[str] = None


@dataclass(frozen=True)
class Allowlist:
    """Parsed allowlist with entries."""

    entries: List[AllowlistEntry]

    @staticmethod
    def load(path: str) -> "Allowlist":
        """Load and validate an allowlist from a JSON file."""
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        errors = []
        for e in sorted(_VALIDATOR.iter_errors(obj), key=lambda x: x.path):
            loc = ".".join([str(p) for p in e.path]) or "(root)"
            errors.append(f"{loc}: {e.message}")
        if errors:
            raise AllowlistError("allowlist validation failed:\n" + "\n".join(errors))

        allow = obj.get("allow", [])
        entries: List[AllowlistEntry] = []
        for item in allow:
            # Determine kind and id
            fingerprint = item.get("fingerprint")
            finding_id = item.get("finding_id") or item.get("id")
            
            if fingerprint:
                kind, val = "fingerprint", fingerprint
            else:
                kind, val = "id", finding_id
                
            entries.append(
                AllowlistEntry(
                    id=val.strip(),
                    kind=kind,
                    expires=item["expires"].strip(),
                    reason=item["reason"].strip(),
                    owner=item.get("owner", "unknown"),
                    ticket=item.get("ticket"),
                )
            )
        return Allowlist(entries=entries)

    def is_suppressed(self, f: Dict[str, Any]) -> bool:
        """Check if a finding is suppressed by any active entry."""
        # Note: Expiry check should happen before calling this, or we rely on caller to filter expired entries first.
        # However, for simplicity here, we assume 'self.entries' contains valid entries.
        # But wait, 'expired_entries' filters them out? No, that just returns them.
        
        # We need to check both ID and Fingerprint
        fid = f.get("id")
        fp = f.get("fingerprint")
        
        for e in self.entries:
            if e.kind == "id" and e.id == fid:
                return True
            if e.kind == "fingerprint" and e.id == fp:
                return True
        return False

    def suppressed_ids(self) -> Set[str]:
        """Get set of finding IDs that are suppressed (legacy helper)."""
        return {e.id for e in self.entries if e.kind == "id"}

    def expired_entries(self, today: Optional[date] = None) -> List[AllowlistEntry]:
        """Get list of entries that have expired."""
        today = today or date.today()
        expired: List[AllowlistEntry] = []
        for e in self.entries:
            try:
                # expires is ISO date yyyy-mm-dd
                y, m, d = e.expires.split("-")
                exp = date(int(y), int(m), int(d))
                if exp < today:
                    expired.append(e)
            except ValueError:
                # Invalid date format, treat as expired/invalid
                expired.append(e)
        return expired

    def active_entries(self, today: Optional[date] = None) -> "Allowlist":
        """Return new Allowlist with only non-expired entries."""
        today = today or date.today()
        # reusing logic above roughly
        exps = set(self.expired_entries(today))
        return Allowlist(entries=[e for e in self.entries if e not in exps])
