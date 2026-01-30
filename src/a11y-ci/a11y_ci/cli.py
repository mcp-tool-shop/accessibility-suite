"""CLI entry point for a11y-ci."""

from __future__ import annotations

import click

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
def gate_cmd(
    current_path: str,
    baseline_path: str | None,
    fail_on: str,
    allowlist_path: str | None,
):
    """Evaluate policy gate against scorecards."""
    try:
        current = Scorecard.load(current_path)
        baseline = Scorecard.load(baseline_path) if baseline_path else None
        allowlist = Allowlist.load(allowlist_path) if allowlist_path else None
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

    if result.ok:
        msg = CliMessage(
            status="OK",
            id="A11Y.CI.GATE.PASS",
            title="Accessibility gate passed",
            what=["No policy violations were detected."],
            why=["Current findings meet the configured threshold and baseline policy."],
            fix=["Proceed with merge/release."],
        )
        click.echo(render(msg), nl=False)
        raise SystemExit(EXIT_PASS)

    # fail message (low-vision friendly, actionable)
    what_lines = ["Accessibility policy violations were detected."]
    why_lines = result.reasons[:]
    fix_lines = [
        "Review the current scorecard and address the listed findings.",
        "If this is intentional, add a time-bounded allowlist entry with justification.",
        f"Re-run: a11y-ci gate --current {current_path}"
        + (f" --baseline {baseline_path}" if baseline_path else "")
        + (f" --allowlist {allowlist_path}" if allowlist_path else ""),
    ]

    # Include a short list of blocking IDs in Fix for immediate control
    if result.current_blocking_ids:
        fix_lines.append(
            "Blocking IDs (current): "
            + ", ".join(result.current_blocking_ids[:12])
            + (" ..." if len(result.current_blocking_ids) > 12 else "")
        )
    if result.new_blocking_ids:
        fix_lines.append(
            "New blocking IDs (regression): "
            + ", ".join(result.new_blocking_ids[:12])
            + (" ..." if len(result.new_blocking_ids) > 12 else "")
        )

    msg = CliMessage(
        status="ERROR",
        id="A11Y.CI.GATE.FAIL",
        title="Accessibility gate failed",
        what=what_lines,
        why=why_lines if why_lines else ["Gate policy was not satisfied."],
        fix=fix_lines,
    )
    click.echo(render(msg), nl=False)
    raise SystemExit(EXIT_FAIL)
