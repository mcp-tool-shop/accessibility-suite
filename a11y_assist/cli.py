"""CLI entry point for a11y-assist.

Commands:
- explain: High-confidence assist from cli.error.v0.1 JSON
- triage: Best-effort assist from raw text
- last: Assist from ~/.a11y-assist/last.log
- assist-run: Wrapper that captures output for `last`
- ingest: Import findings from a11y-evidence-engine
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Callable, List, Optional, Set, Tuple

import click

from . import __version__
from .from_cli_error import (
    CliErrorValidationError,
    assist_from_cli_error,
    load_cli_error,
)
from .guard import GuardViolation, get_guard_context, validate_profile_transform
from .methods import (
    METHOD_GUARD_VALIDATE,
    METHOD_NORMALIZE_RAW_TEXT,
    METHOD_PROFILE_COGNITIVE_LOAD,
    METHOD_PROFILE_DYSLEXIA,
    METHOD_PROFILE_LOWVISION,
    METHOD_PROFILE_PLAIN_LANGUAGE,
    METHOD_PROFILE_SCREEN_READER,
    with_method,
)
from .parse_raw import parse_raw
from .profiles import (
    apply_cognitive_load,
    apply_dyslexia,
    apply_plain_language,
    apply_screen_reader,
    render_cognitive_load,
    render_dyslexia,
    render_plain_language,
    render_screen_reader,
)
from .render import AssistResult, Confidence, Evidence, render_assist, to_response_dict
from .storage import read_last_log, write_last_log


def output_result(
    rendered: str,
    result: AssistResult,
    json_response: bool,
    json_out: Optional[str],
) -> None:
    """Output the result according to flags.

    Args:
        rendered: The rendered text output
        result: The AssistResult (for JSON serialization)
        json_response: If True, print JSON instead of rendered text
        json_out: If set, write JSON to this path (in addition to rendered output)
    """
    if json_response:
        # JSON to stdout instead of rendered text
        click.echo(json.dumps(to_response_dict(result), indent=2))
    else:
        # Rendered text to stdout (default)
        click.echo(rendered, nl=False)

    # Write JSON to file if requested (regardless of json_response)
    if json_out:
        Path(json_out).write_text(
            json.dumps(to_response_dict(result), indent=2),
            encoding="utf-8",
        )

# Profile registry
PROFILE_CHOICES = [
    "lowvision",
    "cognitive-load",
    "screen-reader",
    "dyslexia",
    "plain-language",
]


def get_renderer(profile: str) -> Callable[[AssistResult], str]:
    """Get the renderer function for a profile."""
    if profile == "cognitive-load":
        return render_cognitive_load
    if profile == "screen-reader":
        return render_screen_reader
    if profile == "dyslexia":
        return render_dyslexia
    if profile == "plain-language":
        return render_plain_language
    return render_assist


def apply_profile(result: AssistResult, profile: str) -> AssistResult:
    """Apply profile transformation to result and add method ID."""
    if profile == "cognitive-load":
        transformed = apply_cognitive_load(result)
        return with_method(transformed, METHOD_PROFILE_COGNITIVE_LOAD)
    if profile == "screen-reader":
        transformed = apply_screen_reader(result)
        return with_method(transformed, METHOD_PROFILE_SCREEN_READER)
    if profile == "dyslexia":
        transformed = apply_dyslexia(result)
        return with_method(transformed, METHOD_PROFILE_DYSLEXIA)
    if profile == "plain-language":
        transformed = apply_plain_language(result)
        return with_method(transformed, METHOD_PROFILE_PLAIN_LANGUAGE)
    # Default: lowvision (no transform, just add method)
    return with_method(result, METHOD_PROFILE_LOWVISION)


def render_with_profile_guarded(
    base_text: str,
    base_result: AssistResult,
    profile: str,
    input_kind: str,
) -> str:
    """Transform and render result according to profile, with guard validation.

    Args:
        base_text: Original input text for content support checking
        base_result: Base AssistResult before transformation
        profile: Profile name to apply
        input_kind: Type of input (cli_error_json, raw_text, last_log)

    Returns:
        Rendered output string

    Raises:
        GuardViolation: If profile transform violates invariants
    """
    # Apply profile transformation (adds profile method ID)
    transformed = apply_profile(base_result, profile)

    # Get allowed commands from base result
    allowed_commands: Set[str] = set(base_result.next_safe_commands)

    # Create guard context
    ctx = get_guard_context(
        profile=profile,
        confidence=base_result.confidence,
        input_kind=input_kind,
        allowed_commands=allowed_commands,
    )

    # Validate the transformation
    validate_profile_transform(base_text, base_result, transformed, ctx)

    # Add guard method ID after validation passes
    transformed = with_method(transformed, METHOD_GUARD_VALIDATE)

    # Render (metadata is not rendered, only stored in result)
    renderer = get_renderer(profile)
    return renderer(transformed)


def _handle_guard_violation(e: GuardViolation) -> None:
    """Handle a guard violation by printing error and exiting."""
    click.echo("[ERROR] A11Y.ASSIST.ENGINE.GUARD.FAIL", err=True)
    click.echo("", err=True)
    click.echo("What:", err=True)
    click.echo("  A profile produced output that violates engine safety rules.", err=True)
    click.echo("", err=True)
    click.echo("Why:", err=True)
    click.echo("  This indicates a bug in a profile transform or renderer.", err=True)
    click.echo("", err=True)
    click.echo("Fix:", err=True)
    click.echo("  Run tests; open an issue; include profile name and guard codes.", err=True)
    click.echo("", err=True)
    click.echo("Guard codes:", err=True)
    for issue in e.issues:
        click.echo(f"  - {issue.code}: {issue.message}", err=True)
    raise SystemExit(2)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__)
def main():
    """a11y-assist: low-vision-first assistant for CLI failures (v0.1 non-interactive)."""
    pass


@main.command("explain")
@click.option(
    "--json",
    "json_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to cli.error.v0.1 JSON file.",
)
@click.option(
    "--profile",
    type=click.Choice(PROFILE_CHOICES),
    default="lowvision",
    help="Accessibility profile (default: lowvision).",
)
@click.option(
    "--json-response",
    "json_response",
    is_flag=True,
    help="Output assist.response.v0.1 JSON instead of rendered text.",
)
@click.option(
    "--json-out",
    "json_out",
    type=click.Path(dir_okay=False),
    help="Write assist.response.v0.1 JSON to file (in addition to rendered output).",
)
def explain_cmd(json_path: str, profile: str, json_response: bool, json_out: Optional[str]):
    """Explain a structured cli.error.v0.1 JSON message."""
    try:
        obj = load_cli_error(json_path)
        result = assist_from_cli_error(obj)

        # Read the original JSON for content support checking
        with open(json_path) as f:
            base_text = f.read()

        try:
            output = render_with_profile_guarded(
                base_text, result, profile, "cli_error_json"
            )
            # Get the transformed result for JSON output
            transformed = apply_profile(result, profile)
            transformed = with_method(transformed, METHOD_GUARD_VALIDATE)
            output_result(output, transformed, json_response, json_out)
        except GuardViolation as e:
            _handle_guard_violation(e)

    except CliErrorValidationError as e:
        # Low confidence: we couldn't validate
        res = AssistResult(
            anchored_id=None,
            confidence="Low",
            safest_next_step="Emit a valid cli.error.v0.1 JSON message and retry.",
            plan=[
                "Validate your JSON output against cli.error.v0.1.",
                "Include an (ID: NAMESPACE.CATEGORY.DETAIL) field.",
                "Ensure What/Why/Fix are present for WARN/ERROR.",
            ],
            next_safe_commands=[],
            notes=["Validation errors (first 5): " + "; ".join(e.errors[:5])],
        )
        # For validation errors, base_text is the error message itself
        base_text = "; ".join(e.errors)
        try:
            output = render_with_profile_guarded(
                base_text, res, profile, "cli_error_json"
            )
            transformed = apply_profile(res, profile)
            transformed = with_method(transformed, METHOD_GUARD_VALIDATE)
            output_result(output, transformed, json_response, json_out)
        except GuardViolation as ge:
            _handle_guard_violation(ge)
        raise SystemExit(2)


@main.command("triage")
@click.option(
    "--stdin",
    "use_stdin",
    is_flag=True,
    help="Read raw CLI output from stdin.",
)
@click.option(
    "--profile",
    type=click.Choice(PROFILE_CHOICES),
    default="lowvision",
    help="Accessibility profile (default: lowvision).",
)
@click.option(
    "--json-response",
    "json_response",
    is_flag=True,
    help="Output assist.response.v0.1 JSON instead of rendered text.",
)
@click.option(
    "--json-out",
    "json_out",
    type=click.Path(dir_okay=False),
    help="Write assist.response.v0.1 JSON to file (in addition to rendered output).",
)
def triage_cmd(use_stdin: bool, profile: str, json_response: bool, json_out: Optional[str]):
    """Triage raw CLI output (best effort)."""
    if not use_stdin:
        click.echo("Use: a11y-assist triage --stdin", err=True)
        raise SystemExit(2)

    text = sys.stdin.read()
    err_id, status, blocks = parse_raw(text)

    notes: List[str] = []
    confidence: Confidence = "Low"
    if err_id:
        confidence = "Medium"
    else:
        notes.append("No (ID: ...) found. Emit cli.error.v0.1 for high-confidence assist.")

    safest = "Follow the tool's Fix steps, starting with the least risky check."
    plan: List[str] = []

    fix_lines = blocks.get("Fix:", [])
    if fix_lines:
        plan = fix_lines[:]
    else:
        plan = [
            "Re-run the command with increased verbosity/logging.",
            "Update the tool to emit (ID: ...) and What/Why/Fix blocks.",
            "If this is your tool, adopt cli.error.v0.1 JSON output.",
        ]

    # Build evidence for raw text
    evidence: List[Evidence] = []
    if fix_lines:
        evidence.append(Evidence(field="safest_next_step", source="raw_text:Fix:1"))
        for i, _ in enumerate(plan):
            evidence.append(Evidence(field=f"plan[{i}]", source=f"raw_text:Fix:{i+1}"))

    safe_cmds = [line for line in plan if "--dry-run" in line][:3]
    for i, cmd in enumerate(safe_cmds):
        # Find which fix line it came from
        for j, fix_line in enumerate(plan):
            if cmd == fix_line:
                evidence.append(
                    Evidence(field=f"next_safe_commands[{i}]", source=f"raw_text:Fix:{j+1}")
                )
                break

    res = AssistResult(
        anchored_id=err_id,
        confidence=confidence,
        safest_next_step=safest,
        plan=plan,
        next_safe_commands=safe_cmds,
        notes=notes,
        methods_applied=(METHOD_NORMALIZE_RAW_TEXT,),
        evidence=tuple(evidence),
    )

    try:
        output = render_with_profile_guarded(text, res, profile, "raw_text")
        transformed = apply_profile(res, profile)
        transformed = with_method(transformed, METHOD_GUARD_VALIDATE)
        output_result(output, transformed, json_response, json_out)
    except GuardViolation as e:
        _handle_guard_violation(e)


@main.command("last")
@click.option(
    "--profile",
    type=click.Choice(PROFILE_CHOICES),
    default="lowvision",
    help="Accessibility profile (default: lowvision).",
)
@click.option(
    "--json-response",
    "json_response",
    is_flag=True,
    help="Output assist.response.v0.1 JSON instead of rendered text.",
)
@click.option(
    "--json-out",
    "json_out",
    type=click.Path(dir_okay=False),
    help="Write assist.response.v0.1 JSON to file (in addition to rendered output).",
)
def last_cmd(profile: str, json_response: bool, json_out: Optional[str]):
    """Assist using the last captured log (~/.a11y-assist/last.log)."""
    text = read_last_log()
    if not text.strip():
        res = AssistResult(
            anchored_id=None,
            confidence="Low",
            safest_next_step="Run a command via assist-run or provide input via triage --stdin.",
            plan=["Try: assist-run <your-command>", "Then: a11y-assist last"],
            next_safe_commands=[],
            notes=["No last.log found."],
        )
        # For empty last log, use the error message as base text
        base_text = "No last.log found. Run assist-run command."
        try:
            output = render_with_profile_guarded(base_text, res, profile, "last_log")
            transformed = apply_profile(res, profile)
            transformed = with_method(transformed, METHOD_GUARD_VALIDATE)
            output_result(output, transformed, json_response, json_out)
        except GuardViolation as e:
            _handle_guard_violation(e)
        raise SystemExit(2)

    err_id, status, blocks = parse_raw(text)
    confidence: Confidence = "Medium" if err_id else "Low"
    notes: List[str] = [] if err_id else ["No (ID: ...) found in last.log."]

    fix_lines = blocks.get("Fix:", [])
    plan: List[str] = fix_lines or [
        "Re-run with verbosity.",
        "Adopt cli.error.v0.1 output for high-confidence assistance.",
    ]

    # Build evidence for last.log (same as raw_text)
    evidence: List[Evidence] = []
    if fix_lines:
        evidence.append(Evidence(field="safest_next_step", source="raw_text:Fix:1"))
        for i, _ in enumerate(plan):
            evidence.append(Evidence(field=f"plan[{i}]", source=f"raw_text:Fix:{i+1}"))

    safe_cmds = [line for line in plan if "--dry-run" in line][:3]
    for i, cmd in enumerate(safe_cmds):
        for j, fix_line in enumerate(plan):
            if cmd == fix_line:
                evidence.append(
                    Evidence(field=f"next_safe_commands[{i}]", source=f"raw_text:Fix:{j+1}")
                )
                break

    res = AssistResult(
        anchored_id=err_id,
        confidence=confidence,
        safest_next_step="Start with the first Fix step. Prefer non-destructive checks.",
        plan=plan,
        next_safe_commands=safe_cmds,
        notes=notes,
        methods_applied=(METHOD_NORMALIZE_RAW_TEXT,),
        evidence=tuple(evidence),
    )

    try:
        output = render_with_profile_guarded(text, res, profile, "last_log")
        transformed = apply_profile(res, profile)
        transformed = with_method(transformed, METHOD_GUARD_VALIDATE)
        output_result(output, transformed, json_response, json_out)
    except GuardViolation as e:
        _handle_guard_violation(e)


def assist_run():
    """Wrapper entry-point (console_script): captures stdout/stderr to last.log.

    Usage: assist-run <cmd> [args...]
    """
    if len(sys.argv) < 2:
        print("Usage: assist-run <command> [args...]", file=sys.stderr)
        raise SystemExit(2)

    cmd = sys.argv[1:]
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    output = proc.stdout or ""

    # Print original output unchanged
    sys.stdout.write(output)

    # Save for a11y-assist last
    write_last_log(output)

    if proc.returncode != 0:
        print("\nTip: run `a11y-assist last` for help", file=sys.stderr)

    raise SystemExit(proc.returncode)


@main.command("ingest")
@click.argument(
    "findings_path",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(file_okay=False),
    help="Output directory for derived artifacts (default: alongside findings.json under a11y-assist/).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format for stdout (default: text).",
)
@click.option(
    "--min-severity",
    type=click.Choice(["info", "warning", "error"]),
    default="info",
    help="Minimum severity to include (default: info).",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Fail if evidence_ref files are missing or provenance fails validation.",
)
@click.option(
    "--verify-provenance",
    is_flag=True,
    help="Validate each referenced provenance bundle and verify digests.",
)
@click.option(
    "--fail-on",
    type=click.Choice(["error", "warning", "never"]),
    default="error",
    help="Exit nonzero if findings exist at/above this severity (default: error).",
)
def ingest_cmd(
    findings_path: str,
    out_dir: Optional[str],
    output_format: str,
    min_severity: str,
    strict: bool,
    verify_provenance: bool,
    fail_on: str,
):
    """Ingest findings from a11y-evidence-engine.

    Takes findings.json and produces:
    - ingest-summary.json: Normalized stats and grouping
    - advisories.json: Fix-oriented tasks with evidence links
    """
    from .ingest import (
        IngestError,
        ingest,
        render_text_summary,
        write_advisories,
        write_ingest_summary,
    )

    findings = Path(findings_path)

    # Determine output directory
    if out_dir:
        out = Path(out_dir)
    else:
        out = findings.parent / "a11y-assist"

    # Run ingest
    try:
        result = ingest(
            findings,
            verify_provenance_flag=(verify_provenance or strict),
            min_severity=min_severity,
        )
    except IngestError as e:
        click.echo(f"Ingest failed: {e}", err=True)
        raise SystemExit(3)

    # Check strict mode
    if strict:
        if result.provenance_errors:
            click.echo("Provenance verification failed:", err=True)
            for err in result.provenance_errors:
                click.echo(f"  - {err}", err=True)
            raise SystemExit(3)

    # Write output files
    write_ingest_summary(result, out / "ingest-summary.json")
    write_advisories(result, out / "advisories.json")

    # Output to stdout
    if output_format == "json":
        summary = {
            "source_engine": result.source_engine,
            "source_version": result.source_version,
            "ingested_at": result.ingested_at,
            "target": result.target,
            "summary": result.summary,
            "by_rule": result.by_rule,
            "output_dir": str(out),
        }
        if verify_provenance or strict:
            summary["provenance_verified"] = result.provenance_verified
        click.echo(json.dumps(summary, indent=2))
    else:
        click.echo(render_text_summary(result))
        click.echo(f"\nOutput: {out}")

    # Determine exit code based on --fail-on
    if fail_on == "never":
        raise SystemExit(0)

    errors = result.summary.get("errors", 0)
    warnings = result.summary.get("warnings", 0)

    if fail_on == "error" and errors > 0:
        raise SystemExit(2)
    if fail_on == "warning" and (errors > 0 or warnings > 0):
        raise SystemExit(2)

    raise SystemExit(0)
