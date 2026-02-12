# a11y-assist v0.1.0 Released
### Human help for CLI failures — without replacing ground truth

Today we're releasing **a11y-assist v0.1.0**, a low-vision-first assistant for command-line tools that helps users *act* on failures without rewriting, hiding, or second-guessing the original output.

a11y-assist is the third component in the accessibility toolchain:

- **a11y-lint** defines the accessibility contract
- **a11y-ci** enforces it in continuous integration
- **a11y-assist** helps humans recover when things go wrong

## What problem this solves

CLI errors often fail users at the worst possible moment:
- when they're under time pressure
- when output is dense or poorly structured
- when vision or cognitive load makes scanning difficult

a11y-assist does **not** fix errors automatically.
Instead, it provides a clear, additive explanation that helps users regain control.

## Key principles

- **Additive, not destructive**
  The original tool output is never modified or hidden.

- **Ground truth anchored**
  When available, assistance is anchored to `cli.error.v0.1` IDs and structure.

- **Low-vision-first**
  Output uses clear labeling, spacing, redundancy, and short line lengths.

- **Safe by default**
  v0.1 emits only non-destructive, read-only next steps.

- **Deterministic and local**
  No background services. No network calls. No hidden state.

## What's included in v0.1.0

- `a11y-assist explain --json <file>`
  High-confidence assistance from structured CLI error JSON

- `a11y-assist triage --stdin`
  Best-effort help for raw terminal output (clearly labeled lower confidence)

- `a11y-assist last`
  Assistance for the most recent failed command via a local wrapper

- `assist-run <command>`
  A zero-config wrapper that captures output and suggests help on failure

## What this release deliberately does *not* include

- No interactive chat
- No autonomous fixes
- No risky command suggestions
- No AI dependency

These capabilities are intentionally deferred to future versions.

## Why this matters

Accessibility is not just about correctness — it's about **recoverability**.

a11y-assist makes CLI tools more humane without sacrificing determinism, debuggability, or trust.

---

Repository: https://github.com/mcp-tool-shop-org/a11y-assist
Release: v0.1.0
