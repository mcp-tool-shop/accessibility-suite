# Ally Engine Contract (a11y-assist)

**Status:** Finalized (v0.3.1)
**Scope:** Engine-level guarantees and invariants

Ally is a deterministic recovery engine for CLI failures.
It helps humans recover from errors without rewriting, hiding, or second-guessing the tool's original output.

This document defines the platform contract for Ally as an engine behind current and future applications.

---

## 1. Design goals (non-negotiable)

Ally is designed to be:

- **Additive** – never rewrites or suppresses ground-truth output
- **Deterministic** – same input always produces the same output
- **Safe by default** – v0.x emits SAFE-only command suggestions
- **Profile-driven** – presentation policies change *how*, not *what*
- **Guarded** – engine invariants are enforced at runtime
- **Adapter-friendly** – CLI today, MCP/IDE/CI adapters later

Ally is intentionally conservative. When in doubt, it withholds help rather than inventing it.

---

## 2. Ground truth vs Assist output

### 2.1 Ground truth

Ground truth is produced by the tool that failed. Preferred formats:

- `cli.error.v0.1` JSON (highest confidence)
- `a11y-lint` scorecard JSON (medium confidence)
- Raw CLI text (lowest confidence; best-effort only)

**Ground truth is never modified by Ally.**

### 2.2 Assist output

Assist output is an additional block clearly labeled as such (e.g., `ASSIST (Low Vision):`).

Assist output:

- explains the situation
- suggests safe next steps
- discloses confidence
- preserves user control

---

## 3. Engine API (source of truth)

All adapters (CLI, MCP, IDE, CI) are thin layers over the engine API.

### 3.1 assist.request (engine input)

**Schema:** `assist.request.v0.1`

Required:

- `profile` – presentation policy (lowvision, cognitive-load, screen-reader, etc.)
- `input.kind` – cli_error_json | scorecard_json | raw_text | last_log

Optional:

- `preferences.max_steps`
- `preferences.show_next_command`

### 3.2 assist.response (engine output)

**Schema:** `assist.response.v0.1`

Required:

- `confidence` – High | Medium | Low
- `safest_next_step` – one sentence
- `plan` – ordered list of steps

Optional:

- `anchored_id` – string or null
- `next_safe_commands` – SAFE commands only
- `notes`
- `methods_applied` – audit-only method identifiers (see §15)
- `evidence` – audit-only source anchors (see §15)

This schema is the engine contract.
Human-readable output is a *rendering* of this structure.

---

## 4. Confidence semantics (monotonic and enforced)

Confidence reflects the reliability of the input, not the quality of the advice.

| Confidence | Meaning |
|------------|---------|
| High | Validated `cli.error.v0.1` JSON |
| Medium | Scorecard input or raw text with explicit `(ID: …)` |
| Low | Raw text without ID, partial parsing, or validation failure |

### Invariant

**Confidence may never increase during profile transformation.**
Profiles may only preserve or downgrade confidence.

Enforced by the Profile Guard.

---

## 5. Safety model

### 5.1 Risk taxonomy

- **SAFE** – read-only, dry-run, validation, inspection
- **RISKY** – reversible state changes
- **DESTRUCTIVE** – irreversible state changes

### v0.x policy

- Ally MAY emit SAFE commands only
- Ally MUST NOT emit RISKY or DESTRUCTIVE commands
- Ally NEVER executes commands

### Command provenance rule

Every emitted command must:

1. appear verbatim in the ground truth (e.g., Fix lines or structured next)
2. be classified SAFE
3. be allowed by confidence level (no commands on Low confidence)

Enforced by the Profile Guard.

---

## 6. Profiles (policy transforms)

Profiles are deterministic presentation policies.

### 6.1 Profile contract

A profile is a pure function:

```
AssistResult (base) → AssistResult (profiled)
```

**Allowed:**

- reorder steps
- truncate steps
- simplify phrasing
- change rendering style

**Forbidden:**

- inventing IDs
- inventing commands
- adding new facts
- increasing confidence
- bypassing safety rules

### 6.2 Built-in profiles (v0.3.x)

| Profile | Purpose |
|---------|---------|
| lowvision | Visual clarity, spacing, redundancy |
| cognitive-load | Reduce steps and complexity |
| screen-reader | Audio-first, spoken-friendly output |
| dyslexia | Reduced reading friction, explicit labels |
| plain-language | Maximum clarity, one clause per sentence |

Adding a new profile is non-breaking.
Changing semantics of an existing profile is a breaking change.

---

## 7. Profile Guard (runtime invariant enforcement)

### 7.1 Purpose

The Profile Guard enforces engine invariants after every profile transform.

Guard violations indicate engine bugs, not user errors.

### 7.2 Enforced invariants (v0.3.x)

**Hard errors (fail execution):**

- Anchored ID invented or changed
- Confidence increased
- Invented commands
- Commands emitted on Low confidence
- Exceeding profile step limits
- Forbidden tokens (e.g., parentheticals in screen-reader)
- Visual navigation references in screen-reader output

**Warnings (non-fatal):**

- Content Support Invariant violations
  (output contains facts not supported by base input)

Warnings are surfaced for developers but do not block output by default.

### 7.3 Guard behavior

- Violations raise `GuardViolation`
- CLI emits structured error output with guard codes
- Exit code: 2 (engine/validation failure)
- Output must not be trusted when guard fails

---

## 8. Content Support Invariant (WARN-level)

Profiles must not introduce new factual topics.

### Enforcement approach

A deterministic heuristic checks whether each output step:

1. shares content tokens with base input text, or
2. consists only of allowed "glue" language plus supported tokens

If unsupported, a WARN-level guard issue is emitted.

This balances safety with legitimate rephrasing.

---

## 9. CLI adapter behavior (current reference)

**Commands:**

- `explain --json <path>`
- `triage --stdin`
- `last`
- `assist-run <command...>`

**Rules:**

- Original tool output is printed unchanged
- Assist block is clearly labeled
- Guard is always enforced

**Exit codes:**

- 0 – success
- 2 – validation/guard failure

The CLI is the reference adapter, not the engine itself.

---

## 10. Determinism and locality

- No randomness
- No timestamps
- No network calls
- Local state limited to:
  - `~/.a11y-assist/last.log`

Telemetry, analytics, or remote calls are explicitly out of scope.

---

## 11. Versioning policy

### Schemas

- `cli.error.v0.1`
- `assist.request.v0.1`
- `assist.response.v0.1`

### Versioning rules

- **Patch:** bug fixes, stricter enforcement, clearer wording
- **Minor:** new profiles, new optional fields, new adapters
- **Major:** changes to required fields or invariant semantics

Backward compatibility is preferred but correctness takes priority.

---

## 12. Testing requirements (quality gate)

Every release must include:

- Determinism tests (same input → same output)
- Guard unit tests for every invariant
- Profile integration tests
- Golden tests for all profiles:
  - lowvision
  - cognitive-load
  - screen-reader
  - dyslexia
  - plain-language
- Methods metadata tests (if metadata is present, it must not affect deterministic output)

If a change cannot be proven safe by tests, it must not ship.

---

## 13. MCP and future adapters (explicitly deferred)

Ally becomes an MCP tool only after:

1. engine contracts are stable
2. guard invariants are proven in real usage
3. consumers want programmatic access

When this happens, MCP will be a thin adapter over the engine API.

---

## 14. Methods metadata (optional, audit-only)

Ally may emit optional metadata fields in `assist.response.v0.1` to support auditing and future "methods/tests" mapping.
These fields must not change engine behavior and must not be required.

### 14.1 methods_applied

Optional list of stable method identifiers indicating which deterministic procedures contributed to the output.

Examples:
- `engine.normalize.from_cli_error_v0_1`
- `profile.screen_reader.apply`
- `guard.validate_profile_transform`

Rules:
- append-only and stable once published
- identifiers are descriptive, not user-facing UI
- may be omitted or empty

### 14.2 evidence

Optional list of lightweight source anchors mapping output text back to input text.

Each evidence entry references:
- `field`: which output field it supports (e.g., `safest_next_step`, `plan[0]`)
- `source`: where it came from (e.g., `cli.error.fix[1]`, `cli.error.why[0]`, `raw_text:Fix:2`)
- optional `note`

Rules:
- anchors must be deterministic
- no large blobs; references only
- may be omitted or empty

### 14.3 Rendering and testing

- Renderers must ignore metadata by default (no visible output change)
- Golden fixtures compare rendered text only; metadata does not affect comparison
- Dedicated metadata tests verify correctness without affecting golden test stability

---

## 15. Design philosophy (final)

> Accessibility is not a feature.
> It is a contract—explicit, testable, enforced, and safe.
