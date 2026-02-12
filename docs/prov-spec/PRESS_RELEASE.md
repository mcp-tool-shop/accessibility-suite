# prov-spec v0.1.0 Released

**A formal, language-neutral specification for verifiable provenance**

*January 26, 2026*

---

Today marks the release of **prov-spec v0.1.0**, a formal, versioned specification and conformance suite for provenance method identifiers, records, and validation.

prov-spec defines a minimal, stable interoperability surface for provenance systems—focusing on **what can be verified**, not how systems are built. It is designed to be implementation-agnostic, language-neutral, and durable over time.

---

## What prov-spec provides

- Normative specification using RFC 2119 language
- Stable, append-only method identifiers with frozen semantics
- Machine-readable catalogs and JSON Schemas
- Positive and negative test vectors for deterministic validation
- Conformance levels for incremental adoption
- Reference validator tooling (optional, non-privileged)

---

## What prov-spec does not do

prov-spec intentionally does **not** define:

- Storage formats
- Transport protocols
- User interfaces
- Policy or governance models

This restraint is deliberate. **prov-spec standardizes contracts, not implementations.**

---

## Proven interoperability

To demonstrate language neutrality, a zero-dependency Node.js provenance engine was implemented independently and validated against prov-spec test vectors **without importing any prov-spec code**. The engine passes all applicable vectors, confirming that the specification is executable and portable.

---

## Stability guarantees

- Method identifiers marked `stable` are **append-only**
- Semantics for stable methods will **never change**
- Compatibility is guaranteed within a major version

**prov-spec v0.1.0 is considered stable.**

---

## Who this is for

- Provenance engine authors
- Tool and platform integrators
- Infrastructure and security teams
- Auditors and verification systems
- Anyone who needs provenance to remain verifiable beyond the lifetime of a single system

---

## Availability

prov-spec v0.1.0 is available now under the MIT license.

- Specification: [github.com/mcp-tool-shop-org/prov-spec](https://github.com/mcp-tool-shop-org/prov-spec)
- Node.js Reference Engine: [github.com/mcp-tool-shop-org/prov-engine-js](https://github.com/mcp-tool-shop-org/prov-engine-js)

---

> **prov-spec exists so provenance can outlive the systems that generate it.**
