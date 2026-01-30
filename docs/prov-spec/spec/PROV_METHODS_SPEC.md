# Provenance Methods Specification (prov-spec)

```
Version:   0.1.0
Status:    Stable
Published: 2025-01-26
```

**This specification defines the grammar, semantics, and conformance requirements for provenance method identifiers used in `prov.record.v0.1`.**

---

## 0. Change Control

This section defines the rules for evolving this specification.

### Allowed Changes by Version Type

| Change Type | Patch (0.1.x) | Minor (0.x.0) | Major (x.0.0) |
|-------------|---------------|---------------|---------------|
| Typo fixes, clarifications | YES | YES | YES |
| New method IDs | NO | YES | YES |
| New optional fields | NO | YES | YES |
| Normative requirement changes | NO | YES | YES |
| Grammar changes | NO | NO | YES |
| Canonicalization changes | NO | NO | YES |
| Breaking semantic changes | NO | NO | YES |

### Stability Guarantee

> **Method IDs marked `stable` are append-only and will never change semantics.**
> **Compatibility is guaranteed within a major version.**

### Deprecation Policy

- Deprecated methods remain valid forever
- Deprecated methods MUST have `superseded_by` in the catalog
- Implementations SHOULD emit warnings for deprecated methods
- Implementations MUST NOT reject deprecated methods

---

## 1. Scope

This specification covers:
- Method ID syntax and grammar
- Semantic contracts for each method namespace
- Versioning and compatibility rules
- Canonicalization requirements
- Conformance and compliance

It does NOT cover:
- Transport protocols
- Authentication/authorization
- Storage formats beyond JSON

---

## 2. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

| Term | Definition |
|------|------------|
| **Method ID** | A stable, namespaced identifier describing a processing step applied during provenance construction |
| **Record** | A `prov.record.v0.1` JSON object documenting a tool invocation |
| **Evidence** | An `evidence.v0.1` object linking an output field to its source |
| **Artifact** | An `artifact.v0.1` object representing an input or output with optional digest |
| **Digest** | A cryptographic hash of artifact content |
| **Envelope** | An `mcp.envelope.v0.1` wrapper containing result and optional provenance |

---

## 3. Method ID Grammar

### 3.1 Syntax

Method IDs MUST conform to the following ABNF grammar:

```abnf
method-id     = namespace *("." segment) [version-suffix]
namespace     = segment
segment       = ALPHA *(ALPHA / DIGIT / "_")
version-suffix = "_v" major "_" minor
major         = 1*DIGIT
minor         = 1*DIGIT
ALPHA         = %x61-7A  ; lowercase a-z only
DIGIT         = %x30-39  ; 0-9
```

### 3.2 Regular Expression

For validation, use:

```regex
^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*(_v[0-9]+_[0-9]+)?$
```

### 3.3 Examples

Valid:
- `adapter.wrap.envelope_v0_1`
- `integrity.digest.sha256`
- `engine.extract.evidence.json_pointer`
- `lineage.parent.link`

Invalid:
- `Adapter.Wrap` (uppercase)
- `adapter-wrap` (hyphen instead of dot)
- `adapter.wrap.v0.1` (version uses dots)
- `123.method` (starts with digit)

---

## 4. Namespaces

### 4.1 Defined Namespaces

| Namespace | Purpose | Owner |
|-----------|---------|-------|
| `adapter.*` | Envelope wrapping, transport, execution | Adapter implementations |
| `engine.*` | Evidence extraction, normalization, provenance construction | Processing engines |
| `integrity.*` | Hashing, signatures, verification | Cryptographic operations |
| `lineage.*` | Parent linking, graph operations | Provenance chain management |

### 4.2 Reserved Namespaces (Future)

The following namespaces are RESERVED for future use:

| Namespace | Intended Purpose |
|-----------|------------------|
| `policy.*` | Access control, retention policies |
| `attestation.*` | Third-party attestations, compliance claims |
| `execution.*` | Runtime environment, resource usage |
| `audit.*` | Audit trail operations |

Implementations MUST NOT use reserved namespaces until formally specified.

---

## 5. Semantic Contracts

When a provenance record claims a method ID, the record MUST satisfy that method's semantic contract.

### 5.1 Adapter Methods

#### `adapter.wrap.envelope_v0_1`
**Contract:** Record was created by wrapping a non-envelope payload.
- Record MUST be inside an `mcp.envelope.v0.1`
- Original payload MUST be preserved in `envelope.result`

#### `adapter.pass_through.envelope_v0_1`
**Contract:** Tool returned an envelope; adapter passed it through unchanged.
- Envelope MUST NOT be double-wrapped
- Original provenance (if any) MUST be preserved

#### `adapter.provenance.attach_record_v0_1`
**Contract:** Adapter attached a `prov.record.v0.1` to the envelope.
- `envelope.provenance` MUST be a valid `prov.record.v0.1`
- `provenance.tool.adapter` SHOULD identify the adapter

#### `adapter.errors.capture`
**Contract:** Adapter captured execution failure.
- `envelope.errors` MUST contain at least one error entry
- Error entry MUST have `code` and `message` fields

#### `adapter.warnings.capture`
**Contract:** Adapter captured non-fatal warnings.
- `envelope.warnings` MUST contain at least one warning entry

### 5.2 Engine Methods

#### `engine.prov.record_v0_1.build`
**Contract:** Constructed a provenance record.
- Record MUST have `schema_version: "prov.record.v0.1"`
- Record MUST have valid `run_id`, `tool`, `inputs`, `outputs`, `methods`, `evidence`, `parents`

#### `engine.prov.artifact.register_input`
**Contract:** Registered input artifact(s).
- `provenance.inputs` MUST contain at least one artifact
- Each artifact MUST have `artifact_id` and `media_type`

#### `engine.prov.artifact.register_output`
**Contract:** Registered output artifact(s).
- `provenance.outputs` MUST contain at least one artifact
- Each artifact MUST have `artifact_id` and `media_type`

#### `engine.extract.evidence.json_pointer`
**Contract:** Evidence uses JSON pointer fragments.
- At least one evidence entry MUST have `source` containing `#json:/`
- Fragment MUST be a valid JSON Pointer (RFC 6901)

#### `engine.extract.evidence.text_lines`
**Contract:** Evidence uses text line ranges.
- At least one evidence entry MUST have `source` containing `#text:line:`
- Format: `#text:line:<start>[-<end>]`

#### `engine.coerce.evidence.v0_1`
**Contract:** Normalized evidence to canonical schema.
- All evidence entries MUST have `schema_version: "evidence.v0.1"`

### 5.3 Integrity Methods

#### `integrity.digest.sha256`
**Contract:** Computed SHA-256 digest(s).
- At least one artifact MUST have `digest.alg == "sha256"`
- `digest.value` MUST be lowercase hex, 64 characters
- Content MUST be canonicalized per Section 6

#### `integrity.digest.sha512`
**Contract:** Computed SHA-512 digest(s).
- At least one artifact MUST have `digest.alg == "sha512"`
- `digest.value` MUST be lowercase hex, 128 characters

#### `integrity.digest.blake3`
**Contract:** Computed BLAKE3 digest(s).
- At least one artifact MUST have `digest.alg == "blake3"`
- `digest.value` MUST be lowercase hex, 64 characters

#### `integrity.record_digest.compute`
**Contract:** Computed digest of the provenance record itself.
- `provenance.integrity.record_digest` MUST be present
- Digest computed over canonical JSON of record (excluding `integrity` field)

#### `integrity.signature.create`
**Contract:** Created cryptographic signature.
- `provenance.integrity.signature` MUST be present
- Signature MUST cover `integrity.record_digest`

#### `integrity.signature.verify`
**Contract:** Verified existing signature.
- Signature verification MUST have succeeded
- This method is typically claimed by verification tools, not producers

### 5.4 Lineage Methods

#### `lineage.parent.link`
**Contract:** Linked to parent provenance record(s).
- `provenance.parents` MUST contain at least one `run_id`
- Parent records SHOULD be retrievable

#### `lineage.graph.build`
**Contract:** Constructed provenance graph.
- Multiple records were linked into a DAG structure
- This method is typically claimed by graph-building tools

---

## 6. Canonicalization

### 6.1 JSON Canonicalization

For digest computation, JSON content MUST be canonicalized as follows:

1. **Encoding:** UTF-8, no BOM
2. **Keys:** Sorted lexicographically (Unicode code point order)
3. **Whitespace:** No whitespace between tokens (compact form)
4. **Numbers:** No leading zeros, no trailing zeros after decimal, no positive sign
5. **Strings:** Minimal escaping (only required escapes)
6. **Separators:** `,` between elements, `:` between key-value

This is compatible with [JCS (RFC 8785)](https://www.rfc-editor.org/rfc/rfc8785) subset.

### 6.2 Implementation

```python
import json

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
```

### 6.3 Digest Computation

To compute a digest:
1. Canonicalize the content per Section 6.1
2. Encode as UTF-8 bytes
3. Apply the hash algorithm
4. Encode result as lowercase hexadecimal

---

## 7. Versioning and Compatibility

### 7.1 Method ID Versioning

Method IDs MAY include a version suffix (`_vMAJOR_MINOR`).

- **Unversioned IDs** (e.g., `integrity.digest.sha256`): Semantics are stable and MUST NOT change.
- **Versioned IDs** (e.g., `adapter.wrap.envelope_v0_1`): Semantics are frozen for that version.

### 7.2 Allowed Changes

| Change Type | Allowed? |
|-------------|----------|
| Add new method ID | YES |
| Add new namespace | YES |
| Deprecate method ID | YES (with `superseded_by`) |
| Remove method ID | NO |
| Rename method ID | NO |
| Change semantics of existing ID | NO |

### 7.3 Deprecation

To deprecate a method ID:
1. Mark status as `deprecated` in catalog
2. Add `superseded_by` pointing to replacement
3. Continue supporting deprecated ID indefinitely

### 7.4 Breaking Changes

If semantics MUST change:
1. Create a new method ID (with new version suffix if applicable)
2. Deprecate the old ID
3. Document migration path

---

## 8. Security Considerations

### 8.1 Digest Integrity

- Digests SHOULD be computed by the producing system
- Consumers SHOULD verify digests when artifacts are retrieved
- Digest algorithm MUST be explicitly stated (no default assumptions)

### 8.2 Signature Trust

- Signatures attest to record integrity, not content truthfulness
- Signature verification requires trusted key distribution (out of scope)
- Unsigned records are valid but offer no integrity guarantee

### 8.3 Method ID Spoofing

- Claiming a method ID without satisfying its contract is a conformance violation
- Validators SHOULD check semantic contracts, not just syntax
- Malicious actors could claim methods falsely; consumers MUST NOT trust claims blindly

---

## 9. Conformance

### 9.1 Conformance Levels

| Level | Requirements |
|-------|--------------|
| **Syntax-Conformant** | Method IDs match grammar (Section 3) |
| **Semantics-Conformant** | Method claims satisfy contracts (Section 5) |
| **Fully-Conformant** | Syntax + Semantics + Canonicalization (Section 6) |

### 9.2 Conformance Declaration

Implementations MAY declare conformance by shipping a `prov-capabilities.json` manifest:

```json
{
  "schema": "prov-capabilities@v0.1",
  "engine": {
    "name": "example-engine",
    "version": "1.0.0"
  },
  "implements": [
    "adapter.wrap.envelope_v0_1",
    "integrity.digest.sha256"
  ],
  "conformance_level": "fully-conformant",
  "canonicalization": "jcs-subset"
}
```

### 9.3 Test Vectors

Implementations SHOULD validate against published test vectors in `spec/vectors/`.

---

## 10. References

- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) - Key words for RFCs
- [RFC 6901](https://www.rfc-editor.org/rfc/rfc6901) - JSON Pointer
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) - JSON Canonicalization Scheme
- `PROV_METHODS_CATALOG.md` - Stable method ID registry
- `MCP_COMPATIBILITY.md` - Envelope compatibility policy

---

## Appendix A: Method Catalog

See `PROV_METHODS_CATALOG.md` for the complete registry of stable method IDs.

## Appendix B: Schema Files

- `prov.record.schema.v0.1.json` - Provenance record schema
- `evidence.schema.v0.1.json` - Evidence anchor schema
- `artifact.schema.v0.1.json` - Artifact metadata schema
- `mcp.envelope.schema.v0.1.json` - Envelope wrapper schema
- `prov-capabilities.schema.json` - Capability manifest schema
