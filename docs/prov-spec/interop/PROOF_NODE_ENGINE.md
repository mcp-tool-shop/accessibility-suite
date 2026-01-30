# Interop Proof: Node.js Engine

**Date:** 2025-01-26
**Spec Version:** 0.1.0
**Engine:** prov-engine-js v0.1.0

This document provides evidence that prov-spec vectors can be validated by an independent, non-Python implementation.

---

## Engine Details

| Property | Value |
|----------|-------|
| Name | prov-engine-js |
| Version | 0.1.0 |
| Language | JavaScript (Node.js 18+) |
| Dependencies | None (built-ins only) |
| Repository | https://github.com/prov-spec/prov-engine-js |

## Implemented Methods

- `integrity.digest.sha256`
- `adapter.wrap.envelope_v0_1`

## Vector Results

### integrity.digest.sha256

```
$ node prov-engine.js check-vector spec/vectors/integrity.digest.sha256
PASS: integrity.digest.sha256 vector
```

**Input:**
```json
{"key": "value", "number": 42, "nested": {"a": 1, "b": 2}}
```

**Output:**
```json
{
  "canonical_form": "{\"key\":\"value\",\"nested\":{\"a\":1,\"b\":2},\"number\":42}",
  "digest": {
    "alg": "sha256",
    "value": "54fb66ce0aa908012dc9c432d77d16df95a3d5033a557d1c14cfc6d82a63ae34"
  }
}
```

**Verification:** Output matches `spec/vectors/integrity.digest.sha256/expected.json` exactly.

---

### adapter.wrap.envelope_v0_1

```
$ node prov-engine.js check-vector spec/vectors/adapter.wrap.envelope_v0_1
PASS: adapter.wrap.envelope_v0_1 vector
```

**Input:**
```json
{"ok": true, "count": 3, "message": "Operation completed"}
```

**Output:**
```json
{
  "schema_version": "mcp.envelope.v0.1",
  "result": {"ok": true, "count": 3, "message": "Operation completed"}
}
```

**Verification:** Output matches `spec/vectors/adapter.wrap.envelope_v0_1/expected.json` exactly.

---

## Capability Manifest

```json
{
  "schema": "prov-capabilities@v0.1",
  "engine": {
    "name": "prov-engine-js",
    "version": "0.1.0",
    "vendor": "prov-spec",
    "license": "MIT"
  },
  "implements": [
    "adapter.wrap.envelope_v0_1",
    "integrity.digest.sha256"
  ],
  "conformance_level": "fully-conformant",
  "constraints": {
    "canonicalization": "jcs-subset",
    "supported_digest_algorithms": ["sha256"]
  }
}
```

---

## Conclusion

The Node.js engine:

1. Passes all applicable prov-spec vectors
2. Produces byte-identical output to the Python reference
3. Implements canonicalization per PROV_METHODS_SPEC.md Section 6
4. Has zero dependencies beyond Node.js built-ins
5. Shares no code with the Python reference implementation

This constitutes proof of language-neutral interoperability.
