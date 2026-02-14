"""Reporting logic for gate results."""

import json
from dataclasses import asdict
from typing import Any, Dict, List

from .gate import GateResult
from .help import get_help
from .render import CliMessage, render
from .severity import SEVERITY_ORDER


def _format_counts(counts: Dict[str, int], baseline: Dict[str, int] | None) -> List[str]:
    """Format counts with optional baseline deltas."""
    lines = []
    for sev in reversed(SEVERITY_ORDER):
        count = counts.get(sev, 0)
        base_count = baseline.get(sev, 0) if baseline else 0
        delta = count - base_count
        
        delta_str = ""
        if baseline and delta != 0:
            sign = "+" if delta > 0 else ""
            delta_str = f" ({sign}{delta})"
            
        if count > 0 or (baseline and base_count > 0):
            lines.append(f"{sev.title()}: {count}{delta_str}")
            
    if not lines:
        lines.append("No findings.")
    return lines


def print_text_report(result: GateResult):
    """Print human-readable report using CliMessage."""
    counts_lines = _format_counts(result.current_counts, result.baseline_counts)
    
    if result.ok:
        msg = CliMessage(
            status="OK",
            id="A11Y.CI.GATE.PASS",
            title="Accessibility gate passed",
            what=["No policy violations detected."] + counts_lines,
            why=["Current findings meet the configured threshold."],
            fix=["Proceed with merge/release."],
        )
        print(render(msg), end="")
        return

    # Failure case
    what_lines = ["Accessibility policy violations were detected."]
    what_lines.append("")
    what_lines.append("Summary:")
    what_lines.extend([f"  {line}" for line in counts_lines])
    
    why_lines = result.reasons[:]
    
    fix_lines = [
        "Address the listed findings or update the baseline.",
        "Run local check: a11y-ci gate --current <path>",
    ]
    
    if result.current_blocking_ids:
        fix_lines.append("")
        fix_lines.append("Blocking IDs (Top 10):")
        
        for bid in result.current_blocking_ids[:10]:
            line = f"- {bid}"
            info = get_help(bid)
            if info:
                # Add hint and link
                fix_lines.append(f"  {line}")
                fix_lines.append(f"    Fix: {info.hint}")
                fix_lines.append(f"    Docs: {info.url}")
            else:
                fix_lines.append(line)
                
        if len(result.current_blocking_ids) > 10:
             fix_lines.append(f"... and {len(result.current_blocking_ids) - 10} more.")

    if result.new_blocking_ids:
        fix_lines.append("")
        fix_lines.append("New Regression IDs (Top 10):")
        fix_lines.extend([f"- {bid}" for bid in result.new_blocking_ids[:10]])

    msg = CliMessage(
        status="ERROR",
        id="A11Y.CI.GATE.FAIL",
        title="Accessibility gate failed",
        what=what_lines,
        why=why_lines if why_lines else ["Gate policy was not satisfied."],
        fix=fix_lines,
    )
    print(render(msg), end="")


def print_json_report(result: GateResult):
    """Print machine-readable JSON report."""
    
    # Enrich blocking findings with help
    blocking_details = []
    for bid in result.current_blocking_ids:
        item = {"id": bid}
        info = get_help(bid)
        if info:
            item["help_url"] = info.url
            item["help_hint"] = info.hint
        else:
            item["help_url"] = None
            item["help_hint"] = None
        blocking_details.append(item)

    payload = {
        "gate": "PASS" if result.ok else "FAIL",
        "timestamp": "ISO8601-TODO", # or omit
        "counts": result.current_counts,
        "baseline_counts": result.baseline_counts,
        "reasons": result.reasons,
        "blocking": {
            "current_ids": result.current_blocking_ids,
            "details": blocking_details, # enriched list
            "new_ids": result.new_blocking_ids,
            "new_fingerprints": result.new_fingerprints if hasattr(result, "new_fingerprints") else [],
        }
    }
    print(json.dumps(payload, indent=2))
