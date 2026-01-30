#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-results}"

rm -rf "$OUT"
mkdir -p "$OUT"

echo "==> Scan (a11y-evidence-engine)"
a11y-engine scan ./html --out "$OUT"

echo "==> Ingest + verify provenance (a11y-assist)"
# Fail CI if any errors exist (default fail-on error)
a11y-assist ingest "$OUT/findings.json" \
  --out "$OUT/a11y-assist" \
  --verify-provenance \
  --strict \
  --format text

echo "==> Done"
