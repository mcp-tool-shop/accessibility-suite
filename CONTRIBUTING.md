# Contributing to Ally

Thank you for your interest in contributing to the Ally accessibility toolchain.

Ally is designed as **infrastructure**, not a feature playground.
Correctness, determinism, and user trust matter more than speed.

Please read this document carefully before submitting changes.

---

## Core principles (non-negotiable)

All contributions must respect these principles:

1. **Additive only**
   - Ally must never rewrite, hide, or correct ground-truth tool output.

2. **Deterministic**
   - Same input must always produce the same output.
   - No randomness, timestamps, or network calls.

3. **SAFE by default**
   - v0.x must never emit RISKY or DESTRUCTIVE commands.
   - Suggested commands must appear verbatim in the input.

4. **Confidence-honest**
   - Confidence may never increase.
   - If input is ambiguous, Ally must say so.

5. **Guarded**
   - All profile transforms are subject to the Profile Guard.
   - Guard violations are engine bugs and must not be bypassed.

---

## What kinds of contributions are welcome

### ✅ Good contributions
- Bug fixes
- Documentation improvements
- Test coverage
- New profiles (following the profile contract)
- Reference integrations
- CI and tooling improvements

### ❌ Not accepted (without major discussion)
- Auto-fix behavior
- Executing commands
- "Smart" inference that invents facts
- Removing safety checks
- Making output less explicit to appear "cleaner"

---

## Adding or modifying a profile

Profiles are **policy**, not intelligence.

When proposing a profile:
1. Document the target audience.
2. Define exact transformation rules.
3. Define guard constraints.
4. Add golden tests.
5. Prove no new facts or commands are introduced.

If a change cannot be proven safe by tests, it must not ship.

---

## Tests are mandatory

Every PR must include tests that demonstrate:
- determinism
- invariant preservation
- no invented IDs
- no invented commands
- correct guard behavior

Golden tests are strongly preferred.

---

## Questions or uncertainty

If you are unsure whether a change aligns with Ally's philosophy:
- open an issue first
- describe the problem, not the solution

Maintainers will help guide the decision.

---

## Code of conduct

Be respectful. Be patient. Accessibility work affects real people.

Thank you for helping make developer tools more humane.
