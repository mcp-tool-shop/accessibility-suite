# Provenance Method ID Catalog (v0.1)

Stable method IDs for provenance tracking in a11y-mcp-tools.

These IDs are **locked** and MUST NOT change within a major version.
See [prov-spec](https://github.com/mcp-tool-shop-org/prov-spec) for the full specification.

## Envelope Methods

| Method ID | Description |
|-----------|-------------|
| `adapter.wrap.envelope_v0_1` | Wrap request/response in MCP envelope |

## Provenance Methods

| Method ID | Description |
|-----------|-------------|
| `adapter.provenance.record_v0_1` | Create provenance record with inputs/outputs |

## Integrity Methods

| Method ID | Description |
|-----------|-------------|
| `adapter.integrity.sha256_v0_1` | SHA-256 digest for artifact integrity |

## Evidence Capture Methods

| Method ID | Description |
|-----------|-------------|
| `engine.capture.html_canonicalize_v0_1` | Capture HTML with canonicalization (sorted attrs, normalized whitespace) |
| `engine.capture.dom_snapshot_v0_1` | Extract DOM snapshot as flat node array |
| `engine.capture.file_v0_1` | Generic file capture (CLI logs, etc.) |

## Diagnosis Methods

| Method ID | Description |
|-----------|-------------|
| `engine.diagnose.wcag_rules_v0_1` | Evaluate WCAG accessibility rules |

## Evidence Extraction Methods

| Method ID | Description |
|-----------|-------------|
| `engine.extract.evidence.json_pointer_v0_1` | Extract evidence anchor via JSON Pointer (RFC 6901) |
| `engine.extract.evidence.selector_v0_1` | Extract evidence anchor via CSS selector |

## Fix Guidance Methods

| Method ID | Description |
|-----------|-------------|
| `engine.generate.fix_guidance_v0_1` | Generate SAFE-only fix guidance (intent patches) |

---

## Method ID Naming Convention

```
<namespace>.<action>.<target>_v<major>_<minor>
```

**Namespaces:**
- `adapter.*` - Data transformation, wrapping, integrity
- `engine.*` - Core processing (capture, diagnose, extract)

**Versioning:**
- Method IDs include version suffix (e.g., `_v0_1`)
- Breaking changes require new method ID
- Minor changes (backwards-compatible) use same ID

## Usage in Provenance Records

```json
{
  "provenance": {
    "record_id": "prov:record:abc123",
    "methods": [
      "adapter.wrap.envelope_v0_1",
      "adapter.provenance.record_v0_1",
      "adapter.integrity.sha256_v0_1",
      "engine.capture.html_canonicalize_v0_1",
      "engine.capture.dom_snapshot_v0_1"
    ],
    "inputs": ["html/index.html"],
    "outputs": ["artifact:html:index", "artifact:dom:index"],
    "verified": false,
    "created_at": "2026-01-27T04:12:00Z"
  }
}
```

## Adding New Methods

1. Choose appropriate namespace (`adapter.*` or `engine.*`)
2. Use descriptive action + target naming
3. Include version suffix
4. Add to this catalog with description
5. Update `src/schemas/provenance.js`

## Related

- [prov-spec](https://github.com/mcp-tool-shop-org/prov-spec) - Full provenance specification
- [envelope.schema.v0.1.json](src/schemas/envelope.schema.v0.1.json) - MCP envelope schema
- [evidence.bundle.schema.v0.1.json](src/schemas/evidence.bundle.schema.v0.1.json) - Bundle schema
- [diagnosis.schema.v0.1.json](src/schemas/diagnosis.schema.v0.1.json) - Diagnosis schema
