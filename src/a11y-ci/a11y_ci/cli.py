"""CLI entry point for a11y-ci."""

from __future__ import annotations

import click
import json
import jsonschema

from . import __version__
from .allowlist import Allowlist, AllowlistError
from .gate import gate
from .render import CliMessage, render
from .scorecard import Scorecard

EXIT_PASS = 0
EXIT_INPUT_ERROR = 2
EXIT_FAIL = 3


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__)
def main():
    """a11y-ci: CI gate for a11y-lint scorecards."""
    pass


@main.command("gate")
@click.option(
    "--current",
    "current_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to current scorecard JSON.",
)
@click.option(
    "--baseline",
    "baseline_path",
    required=False,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to baseline scorecard JSON (optional).",
)
@click.option(
    "--fail-on",
    "fail_on",
    default="serious",
    show_default=True,
    type=click.Choice(["info", "minor", "moderate", "serious", "critical"], case_sensitive=False),
    help="Minimum severity to fail on.",
)
@click.option(
    "--allowlist",
    "allowlist_path",
    required=False,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to allowlist JSON (optional).",
)
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"], case_sensitive=False),
    help="Output format (default: text).",
)
@click.option(
    "--emit-mcp",
    "emit_mcp",
    is_flag=True,
    help="Emit MCP evidence payload.",
)
@click.option(
    "--mcp-out",
    "mcp_out",
    required=False,
    type=click.Path(dir_okay=False),
    help="Path to write MCP payload.",
)
def gate_cmd(
    current_path: str,
    baseline_path: str | None,
    fail_on: str,
    allowlist_path: str | None,
    output_format: str,
    emit_mcp: bool,
    mcp_out: str | None,
):
    """Evaluate policy gate against scorecards."""
    try:
        current = Scorecard.load(current_path)
        baseline = Scorecard.load(baseline_path) if baseline_path else None
        allowlist = Allowlist.load(allowlist_path) if allowlist_path else None
    except jsonschema.ValidationError as e:
        msg = CliMessage(
            status="ERROR",
            id="A11Y.CI.SCHEMA.INVALID",
            title="Scorecard format invalid",
            what=[f"Schema validation error: {e.message}"],
            why=["The input JSON does not match the required schema."],
            fix=[
                f"Path: {' -> '.join(str(p) for p in e.path)}",
                "Ensure the JSON follows the current scorecard schema.",
            ],
        )
        click.echo(render(msg), nl=False)
        raise SystemExit(EXIT_INPUT_ERROR)
    except AllowlistError as e:
        msg = CliMessage(
            status="ERROR",
            id="A11Y.CI.ALLOWLIST.INVALID",
            title="Allowlist is invalid",
            what=["The allowlist file failed schema validation."],
            why=[
                "The allowlist must include finding_id, expires, and reason for each entry."
            ],
            fix=[
                "Fix the allowlist JSON and re-run the gate.",
                f"Details: {str(e).splitlines()[0]}",
            ],
        )
        click.echo(render(msg), nl=False)
        raise SystemExit(EXIT_INPUT_ERROR)
    except Exception as e:
        msg = CliMessage(
            status="ERROR",
            id="A11Y.CI.INPUT.INVALID",
            title="Could not read inputs",
            what=["One or more input files could not be parsed."],
            why=["The scorecard JSON may be malformed or missing required fields."],
            fix=[
                "Verify the JSON files exist and are valid.",
                f"Error: {type(e).__name__}: {e}",
            ],
        )
        click.echo(render(msg), nl=False)
        raise SystemExit(EXIT_INPUT_ERROR)

    result = gate(current=current, baseline=baseline, fail_on=fail_on, allowlist=allowlist)

    if emit_mcp or mcp_out:
        from .mcp_payload import build_mcp_payload

        artifacts = [{"kind": "scorecard", "path": current_path}]
        if baseline_path:
            artifacts.append({"kind": "baseline", "path": baseline_path})
        if allowlist_path:
            artifacts.append({"kind": "allowlist", "path": allowlist_path})

        payload = build_mcp_payload(result, current, fail_on, artifacts)
        payload_json = json.dumps(payload, indent=2)

        if mcp_out:
            with open(mcp_out, "w", encoding="utf-8") as f:
                f.write(payload_json)
        elif emit_mcp:
            click.echo(payload_json)

    if result.ok:
        if output_format == "json":
            from .report import print_json_report
            print_json_report(result)
        else:
            from .report import print_text_report
            print_text_report(result)
        raise SystemExit(EXIT_PASS)

    # Failure case
    if output_format == "json":
        from .report import print_json_report
        print_json_report(result)
    else:
        from .report import print_text_report
        print_text_report(result)
    
    raise SystemExit(EXIT_FAIL)
