# a11y-evidence-engine

Headless accessibility evidence engine that emits [prov-spec](https://github.com/mcp-tool-shop/prov-spec) provenance records.

Designed to pair with **a11y-assist**: this engine finds issues and captures verifiable evidence; a11y-assist turns those findings into fixes.

## Features

- **Deterministic output**: Same input always produces identical findings and provenance
- **prov-spec compatible**: Every finding includes cryptographically verifiable evidence
- **CI-friendly**: Exit codes designed for automation
- **No browser required**: Pure static HTML analysis

## Installation

```bash
npm install -g a11y-evidence-engine
```

## Usage

```bash
# Scan a file or directory
a11y-engine scan ./path/to/html --out ./results

# View help
a11y-engine --help
```

## Output

```
results/
├── findings.json                    # All findings with metadata
└── provenance/
    └── finding-0001/
        ├── record.json              # engine.extract.evidence.json_pointer
        ├── digest.json              # integrity.digest.sha256
        └── envelope.json            # adapter.wrap.envelope_v0_1
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No findings with severity `error` |
| 2 | At least one `error` finding |
| 3 | Internal engine failure / invalid input |

## Rules (v0.1.0)

| Rule ID | Description |
|---------|-------------|
| `html.document.missing_lang` | `<html>` element missing `lang` attribute |
| `html.img.missing_alt` | `<img>` element missing `alt` attribute |
| `html.form_control.missing_label` | Form control missing associated label |
| `html.interactive.missing_name` | Interactive element missing accessible name |

## Provenance

Each finding includes three prov-spec records:

1. **record.json**: Evidence extraction using `engine.extract.evidence.json_pointer`
2. **digest.json**: SHA-256 hash of canonical evidence using `integrity.digest.sha256`
3. **envelope.json**: Wrapped result using `adapter.wrap.envelope_v0_1`

These records are independently verifiable without trusting the engine.

## License

MIT
