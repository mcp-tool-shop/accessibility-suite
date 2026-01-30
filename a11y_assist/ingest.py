"""Ingest command for a11y-evidence-engine findings.

Takes findings.json from a11y-evidence-engine and produces:
- ingest-summary.json: Normalized stats and grouping
- advisories.json: Fix-oriented tasks with evidence links
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import __version__

# Default fix guidance per rule
DEFAULT_GUIDANCE: Dict[str, Tuple[str, str]] = {
    "html.document.missing_lang": (
        "Add language attribute to document",
        'Add lang="en" (or correct locale) to the <html> element.',
    ),
    "html.img.missing_alt": (
        "Add alt text to images",
        'Add a meaningful alt attribute, or mark decorative images with alt="" and role="presentation".',
    ),
    "html.form_control.missing_label": (
        "Associate labels with form controls",
        "Add <label for> association, or use aria-label/aria-labelledby.",
    ),
    "html.interactive.missing_name": (
        "Add accessible names to interactive elements",
        "Ensure text content, aria-label, aria-labelledby, or title attribute is present.",
    ),
}


@dataclass
class IngestResult:
    """Result of ingesting findings."""

    source_engine: str
    source_version: str
    ingested_at: str
    target: Dict[str, Any]
    summary: Dict[str, int]
    by_rule: List[Dict[str, Any]]
    top_files: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    provenance_verified: bool = False
    provenance_errors: List[str] = field(default_factory=list)


def load_findings(findings_path: Path) -> Dict[str, Any]:
    """Load and validate findings.json structure."""
    if not findings_path.exists():
        raise IngestError(f"Findings file not found: {findings_path}")

    try:
        with open(findings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise IngestError(f"Invalid JSON in findings file: {e}")

    # Basic validation
    required = ["engine", "version", "summary", "findings"]
    missing = [k for k in required if k not in data]
    if missing:
        raise IngestError(f"Missing required fields: {missing}")

    if not isinstance(data["findings"], list):
        raise IngestError("'findings' must be an array")

    return data


def verify_provenance(
    finding: Dict[str, Any], base_dir: Path
) -> Tuple[bool, Optional[str]]:
    """Verify provenance for a single finding.

    Returns (success, error_message).
    """
    evidence_ref = finding.get("evidence_ref")
    if not evidence_ref:
        return False, f"{finding.get('finding_id', 'unknown')}: Missing evidence_ref"

    # Check all files exist
    for key in ["record", "digest", "envelope"]:
        ref_path = evidence_ref.get(key)
        if not ref_path:
            return False, f"{finding.get('finding_id')}: Missing {key} reference"

        full_path = base_dir / ref_path
        if not full_path.exists():
            return False, f"{finding.get('finding_id')}: File not found: {ref_path}"

    # Verify digest matches canonical evidence
    try:
        record_path = base_dir / evidence_ref["record"]
        digest_path = base_dir / evidence_ref["digest"]

        with open(record_path, "r", encoding="utf-8") as f:
            record = json.load(f)
        with open(digest_path, "r", encoding="utf-8") as f:
            digest_record = json.load(f)

        # Extract evidence from record
        prov = record.get("prov.record.v0.1", {})
        outputs = prov.get("outputs", [])
        if not outputs:
            return False, f"{finding.get('finding_id')}: No outputs in record"

        evidence = outputs[0].get("artifact.v0.1", {}).get("content")
        if evidence is None:
            return False, f"{finding.get('finding_id')}: No evidence content in record"

        # Extract expected digest
        digest_prov = digest_record.get("prov.record.v0.1", {})
        digest_outputs = digest_prov.get("outputs", [])
        if not digest_outputs:
            return False, f"{finding.get('finding_id')}: No outputs in digest record"

        expected_digest = (
            digest_outputs[0].get("artifact.v0.1", {}).get("digest", {}).get("value")
        )
        if not expected_digest:
            return False, f"{finding.get('finding_id')}: No digest value found"

        # Compute actual digest using canonical JSON
        canonical = canonicalize(evidence)
        actual_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        if actual_digest != expected_digest:
            return (
                False,
                f"{finding.get('finding_id')}: Digest mismatch (expected {expected_digest[:16]}..., got {actual_digest[:16]}...)",
            )

        return True, None

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return False, f"{finding.get('finding_id')}: Error verifying provenance: {e}"


def canonicalize(value: Any) -> str:
    """Canonicalize JSON per prov-spec (sorted keys, no whitespace)."""
    if value is None:
        return "null"

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, str):
        return json.dumps(value)

    if isinstance(value, (int, float)):
        if not (isinstance(value, bool)) and not (
            isinstance(value, float) and (value != value or abs(value) == float("inf"))
        ):
            return json.dumps(value)
        raise ValueError("Non-finite numbers not allowed")

    if isinstance(value, list):
        items = [canonicalize(item) for item in value]
        return "[" + ",".join(items) + "]"

    if isinstance(value, dict):
        keys = sorted(value.keys())
        pairs = [json.dumps(k) + ":" + canonicalize(value[k]) for k in keys]
        return "{" + ",".join(pairs) + "}"

    raise ValueError(f"Non-JSON value type: {type(value)}")


def group_by_rule(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group findings by rule_id with counts."""
    counts: Dict[str, Dict[str, Any]] = {}

    for finding in findings:
        rule_id = finding.get("rule_id", "unknown")
        severity = finding.get("severity", "info")

        if rule_id not in counts:
            counts[rule_id] = {"rule_id": rule_id, "severity": severity, "count": 0}
        counts[rule_id]["count"] += 1

    # Sort by count descending, then rule_id
    return sorted(counts.values(), key=lambda x: (-x["count"], x["rule_id"]))


def group_by_file(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group findings by file with severity counts."""
    file_counts: Dict[str, Dict[str, int]] = {}

    for finding in findings:
        file_path = finding.get("location", {}).get("file", "unknown")
        severity = finding.get("severity", "info")

        if file_path not in file_counts:
            file_counts[file_path] = {"errors": 0, "warnings": 0, "info": 0}

        if severity == "error":
            file_counts[file_path]["errors"] += 1
        elif severity == "warning":
            file_counts[file_path]["warnings"] += 1
        else:
            file_counts[file_path]["info"] += 1

    # Build result sorted by errors desc, then file name
    result = [
        {"file": f, **counts}
        for f, counts in sorted(
            file_counts.items(), key=lambda x: (-x[1]["errors"], x[0])
        )
    ]

    return result[:10]  # Top 10 files


def build_advisories(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build advisories grouped by rule with fix guidance."""
    by_rule: Dict[str, List[Dict[str, Any]]] = {}

    for finding in findings:
        rule_id = finding.get("rule_id", "unknown")
        if rule_id not in by_rule:
            by_rule[rule_id] = []
        by_rule[rule_id].append(finding)

    advisories = []
    adv_num = 1

    # Sort rules by count descending for priority
    for rule_id in sorted(by_rule.keys(), key=lambda r: -len(by_rule[r])):
        instances = by_rule[rule_id]
        first = instances[0]

        title, fix = DEFAULT_GUIDANCE.get(
            rule_id, (f"Fix {rule_id}", "Review the accessibility issue and apply appropriate fix.")
        )

        advisory = {
            "advisory_id": f"adv-{adv_num:04d}",
            "rule_id": rule_id,
            "severity": first.get("severity", "error"),
            "confidence": first.get("confidence", 0.9),
            "title": title,
            "recommended_fix": fix,
            "instances": [
                {
                    "finding_id": inst.get("finding_id"),
                    "location": inst.get("location"),
                    "evidence_ref": inst.get("evidence_ref"),
                }
                for inst in instances
            ],
        }
        advisories.append(advisory)
        adv_num += 1

    return advisories


def ingest(
    findings_path: Path,
    verify_provenance_flag: bool = False,
    min_severity: str = "info",
) -> IngestResult:
    """Ingest findings from a11y-evidence-engine.

    Args:
        findings_path: Path to findings.json
        verify_provenance_flag: If True, verify all provenance bundles
        min_severity: Minimum severity to include (info, warning, error)

    Returns:
        IngestResult with summary and advisories
    """
    data = load_findings(findings_path)
    base_dir = findings_path.parent

    # Filter by severity
    severity_order = {"info": 0, "warning": 1, "error": 2}
    min_level = severity_order.get(min_severity, 0)

    filtered_findings = [
        f
        for f in data["findings"]
        if severity_order.get(f.get("severity", "info"), 0) >= min_level
    ]

    # Verify provenance if requested
    prov_errors: List[str] = []
    prov_verified = False

    if verify_provenance_flag:
        prov_verified = True
        for finding in filtered_findings:
            success, error = verify_provenance(finding, base_dir)
            if not success and error:
                prov_errors.append(error)
                prov_verified = False

    # Build result
    return IngestResult(
        source_engine=data.get("engine", "unknown"),
        source_version=data.get("version", "unknown"),
        ingested_at=datetime.now(timezone.utc).isoformat(),
        target=data.get("target", {}),
        summary=data.get("summary", {}),
        by_rule=group_by_rule(filtered_findings),
        top_files=group_by_file(filtered_findings),
        findings=filtered_findings,
        provenance_verified=prov_verified,
        provenance_errors=prov_errors,
    )


def write_ingest_summary(result: IngestResult, out_path: Path) -> None:
    """Write ingest-summary.json."""
    summary = {
        "source_engine": result.source_engine,
        "source_version": result.source_version,
        "ingested_at": result.ingested_at,
        "target": result.target,
        "summary": result.summary,
        "by_rule": result.by_rule,
        "top_files": result.top_files,
    }

    if result.provenance_verified:
        summary["provenance_verified"] = True
    elif result.provenance_errors:
        summary["provenance_verified"] = False
        summary["provenance_errors"] = result.provenance_errors

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def write_advisories(result: IngestResult, out_path: Path) -> None:
    """Write advisories.json."""
    advisories = build_advisories(result.findings)

    output = {
        "schema": "a11y-assist/advisories@v0.1",
        "generated_by": {
            "tool": "a11y-assist",
            "command": "ingest",
            "version": __version__,
        },
        "advisories": advisories,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)


def render_text_summary(result: IngestResult) -> str:
    """Render a human-readable summary."""
    lines = []
    lines.append(f"Source: {result.source_engine} v{result.source_version}")
    lines.append(f"Target: {result.target.get('path', 'unknown')}")
    lines.append("")

    s = result.summary
    lines.append(
        f"Files scanned: {s.get('files_scanned', 0)}  "
        f"Errors: {s.get('errors', 0)}  "
        f"Warnings: {s.get('warnings', 0)}  "
        f"Info: {s.get('info', 0)}"
    )
    lines.append("")

    if result.by_rule:
        lines.append("By rule:")
        for rule in result.by_rule[:5]:
            lines.append(
                f"  {rule['rule_id']}: {rule['count']} ({rule['severity']})"
            )
        lines.append("")

    if result.top_files:
        lines.append("Top files:")
        for f in result.top_files[:5]:
            lines.append(f"  {f['file']}: {f['errors']} errors, {f['warnings']} warnings")
        lines.append("")

    if result.provenance_verified:
        lines.append("Provenance: VERIFIED")
    elif result.provenance_errors:
        lines.append(f"Provenance: FAILED ({len(result.provenance_errors)} errors)")
        for err in result.provenance_errors[:3]:
            lines.append(f"  - {err}")

    return "\n".join(lines)


class IngestError(Exception):
    """Error during ingest."""

    pass
