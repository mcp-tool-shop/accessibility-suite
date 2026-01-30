# a11y-assist v0.3.1

Sixth stable release of **a11y-assist**, adding audit metadata support for traceability.

## Added

### Methods metadata (audit-only)
Optional metadata fields in `assist.response.v0.1` for auditing and traceability:

- `methods_applied`: List of stable method identifiers (e.g., `engine.normalize.from_cli_error_v0_1`, `profile.screen_reader.apply`, `guard.validate_profile_transform`)
- `evidence`: Source anchors mapping output fields back to input (e.g., `plan[0]` → `cli.error.fix[0]`)

Rules:
- Metadata does not affect rendering output (golden tests unchanged)
- Method IDs are append-only and stable once published
- Evidence anchors are deterministic and lightweight

### New module: `a11y_assist.methods`
Helper functions for adding methods and evidence:
- `with_method()`, `with_methods()` - add method IDs
- `with_evidence()` - add evidence anchors
- `evidence_for_plan()` - generate plan step evidence

### Governance artifacts
- `CONTRIBUTING.md` - contributor guidelines and core principles
- Golden fixtures (`tests/fixtures/`) - frozen expected outputs for all 5 profiles
- `tests/test_golden.py` - exact string match tests against fixtures
- `tests/test_methods_metadata.py` - 16 tests for metadata correctness

## Changed

- Version bump to 0.3.1
- ENGINE.md updated to v0.3.1 with §14 Methods metadata
- Response schema updated with optional `methods_applied` and `evidence` properties
- 253 tests total (16 new metadata tests + 7 golden tests)

## Unchanged from v0.3.0

All v0.3.0 features remain stable:
- Dyslexia and plain-language profiles
- All existing profiles (lowvision, cognitive-load, screen-reader)
- Profile Guard runtime safety
- Core commands: explain, triage, last, assist-run
- Safety guarantees: no invented IDs, SAFE-only, deterministic

---

# a11y-assist v0.3.0

Fifth stable release of **a11y-assist**, completing the inclusive profile set with dyslexia and plain-language profiles.

## Added

### Dyslexia profile (`--profile dyslexia`)
Reduces reading friction without reducing information:

- Extra vertical spacing between sections
- One idea per line
- Explicit labels (never implied by formatting)
- "Step N:" prefix for predictable structure
- No parentheticals
- No symbolic emphasis (*, _, →)
- No visual navigation references
- Abbreviations expanded (CLI → command line, ID → I D)
- Max 5 steps, max 2 notes

### Plain-language profile (`--profile plain-language`)
Maximizes understandability through simplicity:

- Active voice, present tense
- One clause per sentence
- Subordinate clauses removed
- Conjunctions split (keeps first clause)
- No parentheticals
- Simple numeric step labels
- Max 4 steps, max 1 command
- Notes omitted for clarity

### Complete inclusive profile set
Ally now supports five principled profiles:

| Profile | Primary benefit |
|---------|-----------------|
| lowvision | Visual clarity |
| cognitive-load | Reduced mental steps |
| screen-reader | Audio-first |
| dyslexia | Reduced reading friction |
| plain-language | Maximum clarity |

## Changed

- Version bump to 0.3.0
- 50 new tests for dyslexia and plain-language (230 total)
- Guard updated to enforce dyslexia and plain-language constraints

## Unchanged from v0.2.2

All v0.2.2 features remain stable:
- Profile Guard runtime safety
- Screen-reader, cognitive-load, lowvision profiles
- Core commands: explain, triage, last, assist-run
- Safety guarantees: no invented IDs, SAFE-only, deterministic

---

# a11y-assist v0.2.2

Fourth stable release of **a11y-assist**, adding the Profile Guard runtime safety system.

## Added

### Profile Guard (`guard.py`)
Centralized runtime invariant checker that runs after every profile transform:

- **ID Invariant**: Anchored ID cannot be invented or changed
- **Confidence Invariant**: Confidence cannot increase (only same or decrease)
- **Commands Invariant**: SAFE-only commands - no invented commands, no commands on Low confidence
- **Step Count Invariant**: Enforces max steps per profile (lowvision: 5, cognitive-load: 3, screen-reader: 3-5)
- **Content Support Invariant**: Profile must not add new factual content (WARN only)
- **Profile-Specific Constraints**: Screen-reader forbids parentheticals and visual references

### Guard API
- `GuardIssue`: Frozen dataclass for guard violations
- `GuardViolation`: Exception raised when invariants are violated
- `GuardContext`: Frozen dataclass with profile rules and constraints
- `validate_profile_transform()`: Main validation function
- `get_guard_context()`: Factory function for profile-specific contexts

### Guard Error Output
Guard failures produce structured error messages:
```
[ERROR] A11Y.ASSIST.ENGINE.GUARD.FAIL

What:
  A profile produced output that violates engine safety rules.

Why:
  This indicates a bug in a profile transform or renderer.

Fix:
  Run tests; open an issue; include profile name and guard codes.

Guard codes:
  - A11Y.ASSIST.GUARD.COMMANDS.INVENTED: Profile included a command not in the allowed set
```

## Changed

- Version bump to 0.2.2
- 48 new tests for guard (180 total)
- All profile transforms now run through guard validation

## Unchanged from v0.2.1

All v0.2.1 features remain stable:
- Screen-reader profile
- Cognitive-load profile
- Low-vision profile (default)
- Core commands: explain, triage, last, assist-run
- Safety guarantees: no invented IDs, SAFE-only, deterministic

---

# a11y-assist v0.2.1

Third stable release of **a11y-assist**, adding the screen-reader accessibility profile.

## Added

### Screen-reader profile (`--profile screen-reader`)
Designed for users consuming output via:
- Screen readers / TTS
- Braille displays
- Listen-first workflows (hands busy, eyes fatigued)

Features:
- Spoken-friendly headers (periods instead of colons)
- "Step N:" labels for predictable listening
- Abbreviations expanded (CLI → command line, ID → I D, JSON → J S O N, SFTP → S F T P)
- No visual navigation references (above, below, left, right, arrow)
- No parentheticals (screen readers read them awkwardly)
- Low confidence reduces to 3 steps (less listening time)
- Summary line for quick context

### Profile selection now includes screen-reader
All commands support `--profile lowvision|cognitive-load|screen-reader`:
- `a11y-assist explain --json <path> --profile screen-reader`
- `a11y-assist triage --stdin --profile screen-reader`
- `a11y-assist last --profile screen-reader`

### Screen-reader invariants (in addition to base invariants)
- No meaning in punctuation/formatting alone
- No "visual navigation" references
- Avoid parentheticals as meaning carriers
- Abbreviations expanded for TTS clarity

## Changed

- Version bump to 0.2.1
- 56 new tests for screen-reader profile (132 total)

## Unchanged from v0.2.0

All v0.2.0 features remain stable:
- Cognitive-load profile (`--profile cognitive-load`)
- Low-vision profile (`--profile lowvision`, default)
- Core commands: explain, triage, last, assist-run
- Safety guarantees: no invented IDs, SAFE-only, deterministic

## Stability guarantees

- v0.2.x output format is considered stable for all three profiles
- No breaking changes without a major version bump
- Interactive or AI-assisted features will not be added to v0.x

## What's next (v0.3.0)

- Optional interactive mode
- Pluggable AI backends (opt-in)
- Deeper integration with a11y-ci workflows

---

# a11y-assist v0.2.0

Second stable release of **a11y-assist**, adding the cognitive-load accessibility profile.

## Added

### Cognitive-load profile (`--profile cognitive-load`)
Designed for users who benefit from reduced cognitive load:
- ADHD / executive dysfunction
- Autism / sensory overload
- Anxiety under incident conditions
- Novices under stress

Features:
- Fixed "Goal" line for orientation
- Max 3 plan steps (vs 5 in low-vision)
- First/Next/Last labels instead of numbers
- One SAFE command max (vs 3)
- Shorter, simpler sentences
- No parentheticals or verbose explanations

### Profile selection via `--profile` flag
All commands now support `--profile lowvision|cognitive-load`:
- `a11y-assist explain --json <path> --profile cognitive-load`
- `a11y-assist triage --stdin --profile cognitive-load`
- `a11y-assist last --profile cognitive-load`

### Invariants (non-negotiable)
The cognitive-load profile enforces strict invariants:
1. **No invented facts** - only rephrases existing content
2. **No invented commands** - SAFE commands are verbatim from input
3. **SAFE-only** remains absolute
4. **Additive** - doesn't rewrite original output
5. **Deterministic** - no randomness, no network calls

## Changed

- Default profile is `lowvision` (backward compatible)
- Version bump to 0.2.0

---

# a11y-assist v0.1.0

Initial stable release of **a11y-assist**, a low-vision-first assistant for CLI failures.

## Added

### Core commands
- `a11y-assist explain --json <path>`
  Deterministic assistance from validated `cli.error.v0.1` JSON

- `a11y-assist triage --stdin`
  Best-effort parsing of raw CLI output with explicit confidence labeling

- `a11y-assist last`
  Assist from the most recent captured command output

- `assist-run <command>`
  Wrapper that captures stdout/stderr and suggests help on failure

### Rendering
- Clear **ASSIST (Low Vision)** output block
- Explicit confidence levels: High / Medium / Low
- Structured sections:
  - Safest next step
  - Numbered plan (max 5)
  - SAFE next commands (when applicable)
  - Notes

### Safety guarantees
- Original CLI output is never modified
- No invented error IDs
- SAFE-only command suggestions in v0.1
- No network calls or background services

### Compatibility
- Anchors to `cli.error.v0.1` when present
- Gracefully degrades on raw text
- Works alongside existing tools without modification

## Stability guarantees

- v0.1 output format is considered stable
- No breaking changes without a major version bump
- Interactive or AI-assisted features will not be added to v0.x

## Known limitations

- Raw text triage is heuristic and lower confidence
- Assistance quality depends on the structure of input
- Interactive mode is intentionally not included

---

Thank you for helping make developer tools more humane.
