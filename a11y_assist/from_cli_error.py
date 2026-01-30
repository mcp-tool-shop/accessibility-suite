"""Load and validate cli.error.v0.1, produce deterministic assist.

High-confidence path: validated JSON with ID, What, Why, Fix.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import Draft202012Validator

from .methods import METHOD_NORMALIZE_CLI_ERROR, evidence_for_plan
from .render import AssistResult, Evidence


def _load_schema(name: str) -> Dict[str, Any]:
    """Load a JSON schema from the schemas package."""
    with resources.files("a11y_assist.schemas").joinpath(name).open("rb") as f:
        return json.load(f)


_CLI_ERROR_SCHEMA = _load_schema("cli.error.schema.v0.1.json")
_CLI_ERROR_VALIDATOR = Draft202012Validator(_CLI_ERROR_SCHEMA)


class CliErrorValidationError(Exception):
    """Raised when cli.error.v0.1 validation fails."""

    def __init__(self, errors: List[str]):
        super().__init__("cli.error.v0.1 validation failed")
        self.errors = errors


def load_cli_error(path: str) -> Dict[str, Any]:
    """Load and validate a cli.error.v0.1 JSON file."""
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    errs: List[str] = []
    for e in sorted(_CLI_ERROR_VALIDATOR.iter_errors(obj), key=lambda x: x.path):
        loc = ".".join([str(p) for p in e.path]) or "(root)"
        errs.append(f"{loc}: {e.message}")
    if errs:
        raise CliErrorValidationError(errs)
    return obj


def _normalize_to_list(value: Any) -> List[str]:
    """Normalize a value to a list of strings (handles both string and array formats)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return []


def assist_from_cli_error(obj: Dict[str, Any]) -> AssistResult:
    """Generate an AssistResult from a validated cli.error.v0.1 object.

    Deterministic: no guessing. Builds plan from Fix lines.
    Handles both string and array formats for what/why/fix.
    """
    # Support both 'id' and 'code' fields for ID
    err_id = obj.get("id") or obj.get("code")
    title = obj.get("title") or obj.get("what", "Issue")
    if isinstance(title, list):
        title = title[0] if title else "Issue"

    # Normalize to lists
    what = _normalize_to_list(obj.get("what"))
    why = _normalize_to_list(obj.get("why"))
    fix = _normalize_to_list(obj.get("fix"))

    # Build plan from Fix lines
    plan: List[str] = []
    for line in fix:
        if isinstance(line, str) and line.strip():
            plan.append(line.strip())

    if not plan:
        plan = ["Follow the Fix steps provided by the tool output."]

    safest_next = "Follow the Fix steps in order, starting with the least risky check."
    if why and isinstance(why[0], str) and why[0].strip():
        safest_next = (
            "Start by confirming the cause described under 'Why', "
            "then apply the first Fix step."
        )

    # SAFE commands: only include clearly non-destructive suggestions from fix text.
    # v0.1 is conservative: we only surface commands already present (not invented).
    next_cmds: List[str] = []
    for line in fix:
        if isinstance(line, str):
            # Accept explicit dry-run or command prefixes
            if "--dry-run" in line or line.strip().startswith(("$ ", "> ", "run ")):
                next_cmds.append(line.replace("$", "").replace(">", "").strip())
            # Accept "Re-run: <cmd>" style
            if line.lower().startswith("re-run:"):
                next_cmds.append(line.split(":", 1)[1].strip())

    # Filter to SAFE-only heuristically
    safe_filtered = [
        c for c in next_cmds if "--dry-run" in c or "validate" in c or "check" in c
    ]
    safe_filtered = list(dict.fromkeys(safe_filtered))  # dedupe preserving order

    notes = [
        f"Original title: {title}",
        "This assist block is additive; it does not replace the tool's output.",
    ]

    # Build evidence anchors for traceability
    evidence: List[Evidence] = []

    # Evidence for safest_next_step
    if why:
        evidence.append(Evidence(field="safest_next_step", source="cli.error.why[0]"))
    else:
        evidence.append(Evidence(field="safest_next_step", source="cli.error.fix[0]"))

    # Evidence for plan steps (map to fix lines)
    evidence.extend(evidence_for_plan(plan, source_prefix="cli.error.fix"))

    # Evidence for safe commands (track which fix line they came from)
    for i, cmd in enumerate(safe_filtered[:3]):
        # Find the original fix line index
        for j, fix_line in enumerate(fix):
            if cmd in fix_line or (
                fix_line.lower().startswith("re-run:") and cmd == fix_line.split(":", 1)[1].strip()
            ):
                evidence.append(
                    Evidence(field=f"next_safe_commands[{i}]", source=f"cli.error.fix[{j}]")
                )
                break

    return AssistResult(
        anchored_id=err_id if isinstance(err_id, str) else None,
        confidence="High",
        safest_next_step=safest_next,
        plan=plan,
        next_safe_commands=safe_filtered[:3],
        notes=notes,
        methods_applied=(METHOD_NORMALIZE_CLI_ERROR,),
        evidence=tuple(evidence),
    )
