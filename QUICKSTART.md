# Quickstart (60 seconds): a11y-evidence-engine + a11y-assist

This flow gives you:
1. **Deterministic accessibility findings**
2. **Verifiable provenance** for each finding
3. **Fix-oriented advisories**

---

## 1) Install

```bash
npm install -g a11y-evidence-engine
pip install a11y-assist
```

---

## 2) Scan your HTML and emit provenance

```bash
a11y-engine scan ./html-dir --out ./results
```

You now have:
- `results/findings.json`
- `results/provenance/finding-0001/{record.json,digest.json,envelope.json}`

---

## 3) Ingest findings into a11y-assist

```bash
a11y-assist ingest ./results/findings.json --out ./results/a11y-assist --format text
```

Optional strict mode (fails if provenance is missing or invalid):

```bash
a11y-assist ingest ./results/findings.json --verify-provenance --strict
```

---

## 4) What you get

- A readable summary in your terminal
- `results/a11y-assist/ingest-summary.json`
- `results/a11y-assist/advisories.json` (fix-oriented tasks with evidence links)

---

## Example output

```
Source: a11y-evidence-engine v0.1.0
Target: ./html-dir

Files scanned: 12  Errors: 4  Warnings: 1  Info: 0

By rule:
  html.img.missing_alt: 2 (error)
  html.form_control.missing_label: 2 (error)

Top files:
  index.html: 2 errors, 0 warnings

Provenance: VERIFIED

Output: ./results/a11y-assist
```

---

## CLI reference

```
a11y-assist ingest <findings.json> [options]

Options:
  --out <dir>              Output directory (default: alongside findings.json)
  --format text|json       Output format for stdout (default: text)
  --min-severity           Filter: info|warning|error (default: info)
  --strict                 Fail on missing/invalid provenance
  --verify-provenance      Validate provenance bundles
  --fail-on                Exit nonzero on: error|warning|never (default: error)
```

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success, no findings at/above `--fail-on` |
| 2 | Success, but findings exist at/above `--fail-on` |
| 3 | Ingest/validation failure |

---

**That's it.** You can now build fixes with evidence you can verify.
