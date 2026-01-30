# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01

### Added

- **PROV_METHODS_SPEC.md** — Normative specification for provenance method IDs
  - Method ID grammar (ABNF + regex)
  - Semantic contracts for all namespaces
  - Canonicalization rules (JCS-subset)
  - Versioning and compatibility policy
  - Conformance levels

- **Method Catalog** — 19 stable method IDs across 4 namespaces
  - `adapter.*` (5 methods) — envelope wrapping, transport
  - `engine.*` (6 methods) — evidence extraction, provenance construction
  - `integrity.*` (6 methods) — hashing, signatures, verification
  - `lineage.*` (2 methods) — parent linking, graph operations

- **Reserved Namespaces** — 4 namespaces reserved for future use
  - `policy.*`, `attestation.*`, `execution.*`, `audit.*`

- **JSON Schemas**
  - `prov.record.schema.v0.1.json` — Provenance record
  - `artifact.schema.v0.1.json` — Artifact metadata
  - `artifact.ref.schema.v0.1.json` — Artifact references
  - `evidence.schema.v0.1.json` — Evidence anchors
  - `mcp.envelope.schema.v0.1.json` — MCP envelope wrapper
  - `mcp.request.schema.v0.1.json` — MCP request format
  - `prov-capabilities.schema.json` — Capability manifest
  - `methods.schema.json` — Method catalog format

- **Test Vectors**
  - `integrity.digest.sha256` — Digest computation
  - `adapter.wrap.envelope_v0_1` — Envelope wrapping
  - `engine.extract.evidence.json_pointer` — Evidence extraction
  - `method_id_syntax` — Grammar validation
  - Negative vectors for must-fail cases

- **Conformance Levels**
  - Level 1: Integrity
  - Level 2: Engine
  - Level 3: Lineage

- **Reference Tools**
  - Python validator (`prov_validator`)

- **Documentation**
  - CONFORMANCE_LEVELS.md
  - MCP_COMPATIBILITY.md
  - PROV_METHODS_CATALOG.md

### Security

- All method IDs are stable and append-only
- No semantic changes without major version bump
- Canonicalization prevents hash ambiguity

---

## Stability Guarantee

> Method IDs marked `stable` are append-only and will never change semantics.
> Compatibility is guaranteed within a major version.
