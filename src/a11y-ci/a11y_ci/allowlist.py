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
    """A single allowlist entry with required fields."""

    finding_id: str
    expires: str
    reason: str


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
            entries.append(
                AllowlistEntry(
                    finding_id=item["finding_id"].strip(),
                    expires=item["expires"].strip(),
                    reason=item["reason"].strip(),
                )
            )
        return Allowlist(entries=entries)

    def suppressed_ids(self) -> Set[str]:
        """Get set of finding IDs that are suppressed."""
        return {e.finding_id for e in self.entries}

    def expired_entries(self, today: Optional[date] = None) -> List[AllowlistEntry]:
        """Get list of entries that have expired."""
        today = today or date.today()
        expired: List[AllowlistEntry] = []
        for e in self.entries:
            # expires is ISO date yyyy-mm-dd
            y, m, d = e.expires.split("-")
            exp = date(int(y), int(m), int(d))
            if exp < today:
                expired.append(e)
        return expired
