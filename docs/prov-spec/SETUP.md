# Getting Started with prov-spec

This guide is for engineers who want to validate, implement, or integrate with prov-spec.

**You do not need to use any specific language or framework to comply.**

---

## Repository Structure

```
prov-spec/
├── spec/                # Normative specification, schemas, vectors
├── tools/python/        # Reference validator (optional)
├── interop/             # Interoperability proofs
├── WHY.md               # Design intent and non-goals
└── CONFORMANCE_LEVELS.md
```

**Only the `spec/` directory is normative.**

---

## Option A: Validate provenance records (recommended first step)

### Requirements

- Python 3.10+

### Run the reference validator

```bash
cd prov-spec
python tools/python/prov_validator.py --help
```

### Validate a provenance record

```bash
python tools/python/prov_validator.py \
  validate-methods path/to/record.json --strict
```

This checks:
- Method IDs
- Required fields
- Semantic constraints
- Catalog compliance

---

## Option B: Validate against official test vectors

### Run a built-in vector check

```bash
python tools/python/prov_validator.py \
  check-vector integrity.digest.sha256
```

Vectors include **must-pass** and **must-fail** cases.

**Passing vectors is sufficient to demonstrate method compliance.**

---

## Option C: Declare engine capabilities (no imports required)

Third-party engines declare support using a capability manifest:

```json
{
  "schema": "mcp-tool-shop/prov-capabilities@v0.1",
  "engine": {
    "name": "example-engine",
    "version": "1.0.0"
  },
  "implements": [
    "integrity.digest.sha256",
    "adapter.wrap.envelope_v0_1"
  ]
}
```

### Validate the manifest

```bash
python tools/python/prov_validator.py \
  validate-manifest prov-capabilities.json
```

---

## Option D: Implement prov-spec in any language

To implement a method:

1. Read its normative requirements in `spec/PROV_METHODS_SPEC.md`
2. Implement the method exactly as specified
3. Run the corresponding test vectors
4. (Optional) Publish a `prov-capabilities.json`

**No SDK, framework, or library is required.**

---

## Reference tooling policy

The Python validator is provided for **convenience only**.

- It is **not required** for conformance
- Alternative validators and engines are encouraged
- All authority lives in the specification and vectors

---

## Versioning and upgrades

- v0.1.0 is **stable**
- Method IDs are **append-only**
- New behavior will only appear in new versions
- Existing records remain valid forever

---

## Where to start (TL;DR)

If you are new:

1. Run one vector check
2. Read `WHY.md`
3. Implement one method
4. Stop there

**prov-spec is intentionally small.**
