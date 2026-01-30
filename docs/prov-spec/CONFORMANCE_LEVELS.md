# Conformance Levels

**Spec Version:** v0.1.0

This document defines testable conformance tiers for prov-spec implementations.

---

## Overview

Conformance is incremental. Each level builds on the previous.

| Level | Name | Badge | Requirements |
|-------|------|-------|--------------|
| **1** | Integrity | ![Level 1](https://img.shields.io/badge/prov--spec-L1%20Integrity-blue) | Correct hashing and canonicalization |
| **2** | Engine | ![Level 2](https://img.shields.io/badge/prov--spec-L2%20Engine-green) | Level 1 + provenance record construction |
| **3** | Lineage | ![Level 3](https://img.shields.io/badge/prov--spec-L3%20Lineage-purple) | Level 2 + parent linking and graph operations |

---

## Level 1: Integrity

**Focus:** Cryptographic correctness

### Required Methods

- `integrity.digest.sha256` (or `sha512` or `blake3`)

### Requirements

1. **Canonicalization:** JSON content MUST be canonicalized per spec Section 6
2. **Digest format:** `{ "alg": "<algorithm>", "value": "<lowercase-hex>" }`
3. **Determinism:** Same input MUST produce same digest

### Test Vectors

- `spec/vectors/integrity.digest.sha256/`

### How to Claim

```json
{
  "conformance_level": "L1-integrity",
  "implements": ["integrity.digest.sha256"]
}
```

---

## Level 2: Engine

**Focus:** Provenance record construction

### Required Methods

All of Level 1, plus:

- `adapter.wrap.envelope_v0_1`
- `adapter.provenance.attach_record_v0_1`
- `engine.prov.artifact.register_output`

### Requirements

1. **Envelope structure:** Valid `mcp.envelope.v0.1`
2. **Record structure:** Valid `prov.record.v0.1`
3. **No double-wrap:** Existing envelopes pass through unchanged
4. **Method claims:** Only claim methods actually applied

### Test Vectors

- `spec/vectors/adapter.wrap.envelope_v0_1/`
- `spec/vectors/engine.prov.artifact.register_output/`

### How to Claim

```json
{
  "conformance_level": "L2-engine",
  "implements": [
    "integrity.digest.sha256",
    "adapter.wrap.envelope_v0_1",
    "adapter.provenance.attach_record_v0_1",
    "engine.prov.artifact.register_output"
  ]
}
```

---

## Level 3: Lineage

**Focus:** Provenance chains and graphs

### Required Methods

All of Level 2, plus:

- `lineage.parent.link`

### Requirements

1. **Parent references:** `parents[]` contains valid `run_id` values
2. **Retrievability:** Parent records SHOULD be retrievable
3. **Acyclicity:** Lineage graph MUST be a DAG (no cycles)

### Test Vectors

- `spec/vectors/lineage.parent.link/`

### How to Claim

```json
{
  "conformance_level": "L3-lineage",
  "implements": [
    "integrity.digest.sha256",
    "adapter.wrap.envelope_v0_1",
    "adapter.provenance.attach_record_v0_1",
    "engine.prov.artifact.register_output",
    "lineage.parent.link"
  ]
}
```

---

## Optional Methods

These methods enhance conformance but are not required for any level:

| Method | Purpose |
|--------|---------|
| `engine.prov.artifact.register_input` | Track input artifacts |
| `engine.extract.evidence.json_pointer` | JSON pointer evidence anchors |
| `engine.extract.evidence.text_lines` | Text line evidence anchors |
| `integrity.signature.create` | Sign provenance records |
| `integrity.signature.verify` | Verify signatures |

Declare optional methods in `prov-capabilities.json`:

```json
{
  "optional": [
    "engine.prov.artifact.register_input",
    "integrity.signature.create"
  ]
}
```

---

## Validation Process

### Self-Declaration

1. Create `prov-capabilities.json` in your project root
2. List implemented methods
3. Declare conformance level
4. Document any known deviations

### Automated Validation

```bash
# Validate your manifest
python -m prov_validator validate-manifest prov-capabilities.json

# Run all applicable test vectors
python -m prov_validator check-vector integrity.digest.sha256
python -m prov_validator check-vector adapter.wrap.envelope_v0_1
```

### Conformance Report

Generate a report for auditors:

```bash
python -m prov_validator conformance-report prov-capabilities.json -o report.json
```

---

## Badge Usage

Add a conformance badge to your README:

```markdown
[![prov-spec L2](https://img.shields.io/badge/prov--spec-L2%20Engine-green)](https://github.com/prov-spec/prov-spec)
```

Renders as: ![prov-spec L2](https://img.shields.io/badge/prov--spec-L2%20Engine-green)

---

## Known Deviations

If your implementation deviates from spec, document it:

```json
{
  "known_deviations": [
    {
      "method_id": "integrity.digest.sha256",
      "deviation": "Uses uppercase hex instead of lowercase",
      "reason": "Legacy compatibility with existing system"
    }
  ]
}
```

Deviations don't disqualify conformance claims but MUST be disclosed.

---

## Upgrading Conformance

To move from Level 1 to Level 2:

1. Implement required Level 2 methods
2. Pass Level 2 test vectors
3. Update `prov-capabilities.json`
4. Update badge

No breaking changes are required — conformance is additive.
