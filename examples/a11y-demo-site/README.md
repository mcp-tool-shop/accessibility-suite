# a11y-demo-site

A tiny end-to-end demo showing:

- `a11y-evidence-engine` produces accessibility findings + provenance bundles
- `a11y-assist ingest` generates fix-oriented advisories
- `--verify-provenance` recomputes SHA-256 over canonical evidence
- CI fails on accessibility errors **with Provenance: VERIFIED**

---

## One-command run (local)

**Prereqs:**
- `npm install -g a11y-evidence-engine`
- `pip install a11y-assist`

**Run:**

```bash
./scripts/a11y.sh
```

**Outputs:**

```
results/
├── findings.json
├── provenance/...
└── a11y-assist/
    ├── ingest-summary.json
    └── advisories.json
```

---

## CI behavior

GitHub Actions runs the same script and fails if any findings exist at/above `--fail-on error`.

When provenance verification succeeds, logs include:

```
Provenance: VERIFIED
```

---

## Inspecting results in GitHub Actions (artifacts)

This repo's CI uploads the full `results/` directory as a GitHub Actions artifact on every run (even when the job fails because the HTML is intentionally broken).

### Where to download the artifact

1. Go to the **Actions** tab in GitHub.
2. Click the most recent workflow run:
   - **"A11y (upload results)"** (recommended for inspection)
3. Scroll to the bottom of the run page.
4. Under **Artifacts**, download:
   - **`a11y-results`**

Unzip it locally. You'll see:

```
results/
├── findings.json
├── provenance/
│   └── finding-0001/
│       ├── record.json
│       ├── digest.json
│       └── envelope.json
└── a11y-assist/
    ├── ingest-summary.json
    └── advisories.json
```

### What to open first (recommended order)

1. **`results/a11y-assist/ingest-summary.json`**
   Quick overview of counts, top rules, and top files.

2. **`results/a11y-assist/advisories.json`**
   The fix-oriented task list. Each advisory includes `instances[]` with `evidence_ref` links.

3. **`results/provenance/finding-*/digest.json`**
   The stored `integrity.digest.sha256` record.

4. **`results/provenance/finding-*/record.json`**
   The evidence record (`engine.extract.evidence.json_pointer`) showing what was captured.

### What "Provenance: VERIFIED" means

When `a11y-assist ingest --verify-provenance` runs, it recomputes the SHA-256 digest from the canonicalized evidence and compares it to the stored digest.

If they match, CI prints:

```
Provenance: VERIFIED
```

This proves the captured evidence has not been tampered with since it was produced by the scan (**integrity**).
It does not, by itself, prove the original scan environment was trustworthy.

---

## The intentional bugs (for demo purposes)

**html/index.html:**
- `<html>` missing `lang` attribute
- `<img>` missing `alt` attribute
- `<button>` missing accessible name
- `<a>` (empty link) missing accessible name

**html/contact.html:**
- `<html lang="">` (empty lang)
- `<input>` missing associated label

---

## Fixing the demo (optional)

To make CI pass, fix the HTML:

```html
<!-- index.html -->
<html lang="en">
  ...
  <img src="hero.png" alt="Hero image">
  <button>Click me</button>
  <a href="/contact.html">Contact us</a>
```

```html
<!-- contact.html -->
<html lang="en">
  ...
  <label for="email">Email</label>
  <input type="email" id="email" />
```

---

## Related repos

| Repo | Description |
|------|-------------|
| [prov-spec](https://github.com/mcp-tool-shop/prov-spec) | Formal provenance specification |
| [a11y-evidence-engine](https://github.com/mcp-tool-shop/a11y-evidence-engine) | Accessibility scanner with provenance |
| [a11y-assist](https://github.com/mcp-tool-shop/a11y-assist) | Fix advisor with provenance verification |

---

## License

MIT
