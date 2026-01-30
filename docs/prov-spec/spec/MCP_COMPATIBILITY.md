# MCP Envelope Compatibility Policy v0.1

**Status:** Normative (v0.3.1+)

This document defines how adapters wrap legacy tool outputs into `mcp.envelope.v0.1` safely.

---

## How to adopt (minimal)

You can adopt the MCP envelope and provenance system incrementally.

### If you already return JSON
Wrap your tool output in `mcp.envelope.v0.1`:

```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": { "your": "existing json payload" },
  "provenance": null
}
```

Your existing payload remains unchanged and unconstrained.

### If you return text output
Wrap it as a string result:

```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": "your existing text output",
  "provenance": null
}
```

### If you want provenance (recommended for audits)
Attach a `prov.record.v0.1` record with:
- input artifacts (`inputs[]`)
- output artifacts (`outputs[]`)
- applied method IDs (`methods[]`)
- optional evidence anchors (`evidence[]`)
- optional lineage (`parents[]`)

```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": { "..." : "..." },
  "provenance": {
    "schema_version": "prov.record.v0.1",
    "run_id": "uuid",
    "tool": { "name": "your-tool", "version": "vX.Y.Z", "adapter": "mcp" },
    "inputs": [],
    "outputs": [],
    "methods": [],
    "evidence": [],
    "parents": []
  }
}
```

---

## 1. What Counts as "Legacy"

Anything that returns a payload that is **not** already an `mcp.envelope.v0.1` object:

- Plain string output
- Raw JSON object result
- Arrays, numbers, booleans
- Tool-specific response objects (e.g., `assist.response.v0.1`)

---

## 2. Wrapping Rule

Adapters **MAY** wrap legacy results into:

```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": <original_payload>,
  "provenance": null
}
```

This is always safe and preserves meaning.

---

## 3. Results with Existing schema_version

If the legacy payload is an object with its own `schema_version` (e.g., `assist.response.v0.1`), keep it intact as `result`:

```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": { "schema_version": "assist.response.v0.1", ... },
  "provenance": null
}
```

**Do not** rename fields. **Do not** reformat. **Do not** "upgrade" schemas.

---

## 4. Error Handling

If a tool fails and the adapter can only observe:
- An exception
- A non-zero exit code
- stderr text

Then wrap:
- `result`: `null` (or original partial output if available)
- `errors[]`: At least one entry describing the failure

### Example

```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": null,
  "errors": [
    {
      "code": "ADAPTER.EXECUTION.FAILED",
      "message": "Tool execution failed with exit code 2.",
      "details": { "exit_code": 2 }
    }
  ],
  "provenance": null
}
```

If the tool itself provides structured errors, prefer those codes.

---

## 5. Provenance Attachment (Opt-in)

Adapters **SHOULD** only attach provenance when:

1. They can compute reliable artifact digests and sources, **AND**
2. It won't require network calls unless the caller opted in

Otherwise, set `provenance: null`.

### Opt-in Convention

Use `params._meta` for provenance control:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `capture_provenance` | boolean | `false` | Attach `prov.record.v0.1` to envelope |
| `capture_artifacts` | boolean | `false` | Compute digests for input/output artifacts |
| `provenance_mode` | string | `"minimal"` | `"minimal"` or `"full"` |

---

## 6. Determinism Preference

If `mcp.request.preferences.deterministic` is `true` (default):

- Adapters **SHOULD** omit timestamps
- Adapters **SHOULD** avoid network calls
- Tools **MAY** downgrade behavior (e.g., skip enrichment)

---

## 7. Pass-through Rule (No Double-wrap)

If a tool already returns `mcp.envelope.v0.1`, adapters **MUST** return it unchanged.

**No nesting.**

---

## 8. Forward Compatibility Rule

Consumers must treat unknown top-level envelope fields as invalid (since `additionalProperties: false`), so:

- Add new envelope fields only with a **major version bump**, OR
- Create `mcp.envelope.v0.2` when adding top-level fields

Within `result`, anything goes.

---

## 9. Examples

### 9.1 Legacy JSON Result

**Input:**
```json
{ "ok": true, "count": 3 }
```

**Wrapped:**
```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": { "ok": true, "count": 3 }
}
```

### 9.2 Legacy String

**Input:**
```
"done"
```

**Wrapped:**
```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": "done"
}
```

### 9.3 Tool Already Returns Envelope

**Input:**
```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": { ... },
  "provenance": { ... }
}
```

**Output:** Return unchanged.

---

## 10. References

- `mcp.envelope.schema.v0.1.json`: Envelope schema
- `mcp.request.schema.v0.1.json`: Request schema
- `prov.record.schema.v0.1.json`: Provenance record schema
- `artifact.ref.schema.v0.1.json`: Artifact reference schema
