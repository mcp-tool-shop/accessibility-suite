# prov-spec — Implementer Checklist (v0.1.0)

This checklist is for engineers implementing prov-spec–compliant provenance methods or validators.

**If you can check every box below, your implementation is compliant.**

---

## 1. Scope Check (before you write code)

- [ ] I am implementing **specific method IDs**, not "provenance in general"
- [ ] I understand that prov-spec standardizes **contracts**, not storage, transport, or policy
- [ ] I am **not adding behavior** that is not explicitly specified

> If you want flexibility, stop here—prov-spec is intentionally strict.

---

## 2. Method Identification

- [ ] Every provenance record includes a valid `method_id`
- [ ] The `method_id` **exactly matches** an entry in `spec/methods.json`
- [ ] I do not invent or rename method IDs
- [ ] I treat method IDs as **stable contracts**, not strings of convenience

> **Rule:** If the ID is marked `stable`, its semantics must never change.

---

## 3. Semantic Compliance (most important)

For each implemented method:

- [ ] I have read the method's normative requirements in `PROV_METHODS_SPEC.md`
- [ ] All **MUST** requirements are implemented
- [ ] All **MUST NOT** constraints are enforced
- [ ] Optional behavior is clearly optional and documented

> **Rule:** Passing tests without meeting semantics is non-compliant.

---

## 4. Canonicalization & Integrity (if applicable)

If your method involves hashing, signing, or verification:

- [ ] I use the **exact canonicalization algorithm** specified
- [ ] I hash/sign the **canonical bytes**, not ad-hoc serialization
- [ ] I reject non-canonical or ambiguous inputs
- [ ] Digest values match expected length, encoding, and format exactly

> **Common failure:** Correct algorithm, wrong bytes.

---

## 5. Record Shape & Fields

- [ ] Output records include all required fields
- [ ] Field names, types, and nesting match the spec
- [ ] No required fields are omitted
- [ ] No forbidden fields are added

Validate against the JSON Schemas in `spec/schemas/`.

---

## 6. Test Vectors (mandatory)

For each implemented method:

- [ ] All **positive** test vectors pass
- [ ] All **negative** (must-fail) vectors fail correctly
- [ ] Failures are **explicit** (errors), not silent acceptance

> **Rule:** If a must-fail vector passes, the implementation is wrong.

---

## 7. Capability Declaration (recommended)

If publishing an engine or tool:

- [ ] I provide a `prov-capabilities.json`
- [ ] Declared methods **exactly match** what is implemented
- [ ] The manifest validates against `prov-capabilities.schema.json`

This enables automated interoperability without code imports.

---

## 8. Conformance Level

- [ ] I know which conformance level I meet:
  - **Level 1:** Integrity
  - **Level 2:** Engine
  - **Level 3:** Lineage
- [ ] I do not claim a higher level than implemented
- [ ] Unsupported levels are not implied

> Partial compliance is acceptable—misrepresentation is not.

---

## 9. Language & Tooling Neutrality

- [ ] My implementation does **not depend** on prov-spec reference tooling
- [ ] I treat the Python validator as **optional**
- [ ] I could replace the validator and still be compliant

> Authority lives in the spec and vectors, not in code.

---

## 10. Versioning Discipline

- [ ] I record which spec version I target (e.g. `v0.1.0`)
- [ ] I do not assume future behavior
- [ ] I understand that stable method semantics **never change**

If the spec updates, re-run vectors before upgrading claims.

---

## Final Sanity Check

Ask yourself:

> *"Could someone else independently implement this method and produce the same result?"*

- If the answer is **yes**, you're done.
- If the answer is **maybe**, re-read the spec.

---

**prov-spec exists to make provenance verifiable without trusting the producer.**

**This checklist exists to make that practical.**
