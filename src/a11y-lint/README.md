# a11y-lint

![a11y](https://img.shields.io/badge/a11y-low--vision--first-blue)
![contract](https://img.shields.io/badge/output-contract--stable-green)
![tests](https://img.shields.io/badge/tests-176%2B-brightgreen)
![license](https://img.shields.io/badge/license-MIT-black)

**Low-vision-first accessibility linting for CLI output.**

Validates that error messages follow accessible patterns with the **[OK]/[WARN]/[ERROR] + What/Why/Fix** structure.

## Philosophy

### Rule Categories

This tool distinguishes between two types of rules:

- **WCAG Rules**: Mapped to specific WCAG success criteria. Violations may constitute accessibility barriers.
- **Policy Rules**: Best practices for cognitive accessibility. Not WCAG requirements, but improve usability for users with cognitive disabilities.

Currently, only `no-color-only` (WCAG SC 1.4.1) is a WCAG-mapped rule. All other rules are policy rules that improve message clarity and readability.

### Grades vs. CI Gating

**Important:** Letter grades (A-F) are *derived summaries* for executive reporting. They should **never** be the primary mechanism for CI gating.

For CI pipelines, gate on:
- Specific rule failures (especially WCAG-mapped rules like `no-color-only`)
- Error count thresholds
- Regressions from a baseline

```bash
# Good: Gate on errors
a11y-lint scan output.txt && echo "Passed" || echo "Failed"

# Good: Gate on specific rules
a11y-lint scan --enable=no-color-only output.txt

# Avoid: Gating purely on letter grades
```

### Badges and Conformance

Scores and badges are **informational only**. They do NOT imply WCAG conformance or accessibility certification. This tool checks policy rules beyond minimum WCAG requirements.

## Installation

```bash
pip install a11y-lint
```

Or install from source:

```bash
git clone https://github.com/mcp-tool-shop-org/a11y-lint.git
cd a11y-lint
pip install -e ".[dev]"
```

## Quick Start

Scan CLI output for accessibility issues:

```bash
# Scan a file
a11y-lint scan output.txt

# Scan from stdin
echo "ERROR: It failed" | a11y-lint scan --stdin

# Generate a report
a11y-lint report output.txt -o report.md
```

## CLI Commands

### `scan` - Check for accessibility issues

```bash
a11y-lint scan [OPTIONS] INPUT

Options:
  --stdin              Read from stdin instead of file
  --color [auto|always|never]  Color output mode (default: auto)
  --json               Output results as JSON
  --format [plain|json|markdown]  Output format
  --disable RULE       Disable specific rules (can repeat)
  --enable RULE        Enable only specific rules (can repeat)
  --strict             Treat warnings as errors
```

The `--color` option controls colored output:
- `auto` (default): Respect `NO_COLOR` and `FORCE_COLOR` environment variables, auto-detect TTY
- `always`: Force colored output
- `never`: Disable colored output

### `validate` - Validate JSON messages against schema

```bash
a11y-lint validate messages.json
a11y-lint validate -v messages.json  # Verbose output
```

### `scorecard` - Generate accessibility scorecard

```bash
a11y-lint scorecard output.txt
a11y-lint scorecard --json output.txt     # JSON output
a11y-lint scorecard --badge output.txt    # shields.io badge
```

### `report` - Generate markdown report

```bash
a11y-lint report output.txt
a11y-lint report output.txt -o report.md
a11y-lint report --title="My Report" output.txt
```

### `list-rules` - Show available rules

```bash
a11y-lint list-rules          # Simple list
a11y-lint list-rules -v       # Verbose with categories and WCAG refs
```

### `schema` - Print the JSON schema

```bash
a11y-lint schema
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NO_COLOR` | Disable colored output (any value) |
| `FORCE_COLOR` | Force colored output (any value, overrides NO_COLOR=false) |

See [no-color.org](https://no-color.org/) for the standard.

## Rules

### WCAG Rules

| Rule | Code | WCAG | Description |
|------|------|------|-------------|
| `no-color-only` | CLR001 | 1.4.1 | Don't convey information only through color |

### Policy Rules

| Rule | Code | Description |
|------|------|-------------|
| `line-length` | FMT001 | Lines should be 120 characters or fewer |
| `no-all-caps` | LNG002 | Avoid all-caps text (hard to read) |
| `plain-language` | LNG001 | Avoid technical jargon (EOF, STDIN, etc.) |
| `emoji-moderation` | SCR001 | Limit emoji use (confuses screen readers) |
| `punctuation` | LNG003 | Error messages should end with punctuation |
| `error-structure` | A11Y003 | Errors should explain why and how to fix |
| `no-ambiguous-pronouns` | LNG004 | Avoid starting with "it", "this", etc. |

## Error Message Format

All error messages follow the What/Why/Fix structure:

```
[ERROR] CODE: What happened
  Why: Explanation of why this matters
  Fix: Actionable suggestion

[WARN] CODE: What to improve
  Why: Why this matters
  Fix: How to improve (optional)

[OK] CODE: What was checked
```

## JSON Schema

Messages conform to the CLI error schema (`schemas/cli.error.schema.v0.1.json`):

```json
{
  "level": "ERROR",
  "code": "A11Y001",
  "what": "Brief description of what happened",
  "why": "Explanation of why this matters",
  "fix": "How to fix the issue",
  "location": {
    "file": "path/to/file.txt",
    "line": 10,
    "column": 5,
    "context": "relevant text snippet"
  },
  "rule": "rule-name",
  "metadata": {}
}
```

## Python API

```python
from a11y_lint import scan, Scanner, A11yMessage, Level

# Quick scan
messages = scan("ERROR: It failed")

# Custom scanner
scanner = Scanner()
scanner.disable_rule("line-length")
messages = scanner.scan_text(text)

# Create messages programmatically
msg = A11yMessage.error(
    code="APP001",
    what="Configuration file missing",
    why="The app cannot start without config.yaml",
    fix="Create config.yaml in the project root"
)

# Validate against schema
from a11y_lint import is_valid, validate_message
assert is_valid(msg)

# Generate scorecard
from a11y_lint import create_scorecard
card = create_scorecard(messages)
print(card.summary())
print(f"Score: {card.overall_score}% ({card.overall_grade})")

# Generate markdown report
from a11y_lint import render_report_md
markdown = render_report_md(messages, title="My Report")
```

## CI Integration

### GitHub Actions Example

```yaml
- name: Check CLI accessibility
  run: |
    # Capture CLI output
    ./your-cli --help > cli_output.txt 2>&1 || true

    # Lint for accessibility issues
    # Exit code 1 = errors found, 0 = clean
    a11y-lint scan cli_output.txt

    # Or strict mode (warnings = errors)
    a11y-lint scan --strict cli_output.txt
```

### Best Practices

1. **Gate on errors, not grades**: Use exit codes, not letter grades
2. **Enable specific rules**: For WCAG compliance, enable `no-color-only`
3. **Track baselines**: Use JSON output to detect regressions
4. **Treat badges as informational**: They don't imply conformance

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
pyright
```

## License

MIT
