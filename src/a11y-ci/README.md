# a11y-ci

![gate](https://img.shields.io/badge/gate-strict-blue)
![contract](https://img.shields.io/badge/output-low--vision--first-green)
![license](https://img.shields.io/badge/license-MIT-black)

CI gate for `a11y-lint` scorecards. Low-vision-first output.

## What it does

- Fails if current run has findings at/above `--fail-on` (default: `serious`)
- Optional baseline comparison:
  - fails on serious+ count regression
  - fails if new serious+ finding IDs appear
- Optional allowlist with required reason + expiry

## Install

```bash
pip install a11y-ci
```

## Usage

### Gate (typical CI)

```bash
a11y-ci gate --current a11y.scorecard.json --baseline baseline/a11y.scorecard.json
```

### Allowlist

```bash
a11y-ci gate --current a11y.scorecard.json --baseline baseline/a11y.scorecard.json --allowlist a11y-ci.allowlist.json
```

### Fail severity

```bash
a11y-ci gate --current a11y.scorecard.json --fail-on moderate
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Pass |
| 2 | Input/validation error |
| 3 | Policy gate failed |

## Output Contract

All output follows the low-vision-first contract:

```
[OK] Title (ID: NAMESPACE.CATEGORY.DETAIL)

What:
  What happened.

Why:
  Why it happened.

Fix:
  How to fix it.
```

## Allowlist Format

Allowlist entries require:
- `finding_id`: The rule/finding ID to suppress
- `expires`: ISO date (yyyy-mm-dd) — expired entries fail the gate
- `reason`: Minimum 10 chars explaining the suppression

```json
{
  "version": "1",
  "allow": [
    {
      "finding_id": "CLI.COLOR.ONLY",
      "expires": "2026-12-31",
      "reason": "Temporary suppression for legacy output. Tracked in issue #12."
    }
  ]
}
```

## GitHub Actions Example

```yaml
- name: a11y gate
  run: |
    a11y-lint scan output.txt --json > a11y.scorecard.json
    a11y-ci gate --current a11y.scorecard.json --baseline baseline/a11y.scorecard.json
```

## Notes

- This tool is deterministic. It does not call network services.
- Expired allowlist entries fail the gate (no permanent exceptions).
- Scorecards are format-tolerant: reads `summary` when present, otherwise computes from `findings`.

## License

MIT
