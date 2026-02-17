# @mcptoolshop/a11y-ci

[![npm](https://img.shields.io/npm/v/@mcptoolshop/a11y-ci)](https://www.npmjs.com/package/@mcptoolshop/a11y-ci)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/mcp-tool-shop-org/accessibility-suite/blob/main/LICENSE)

**npm wrapper for [a11y-ci](https://github.com/mcp-tool-shop-org/accessibility-suite/tree/main/src/a11y-ci) — CI gate for accessibility scorecards.**

## Install

```bash
npm install @mcptoolshop/a11y-ci
```

This package provides a CLI wrapper that installs and delegates to the Python `a11y-ci` tool from the [accessibility-suite](https://github.com/mcp-tool-shop-org/accessibility-suite) monorepo.

## Usage

```bash
npx @mcptoolshop/a11y-ci --help
npx @mcptoolshop/a11y-ci scan ./my-site
npx @mcptoolshop/a11y-ci report --format json
```

## What is a11y-ci?

a11y-ci is a CI/CD integration for accessibility checks. It runs WCAG compliance scans and generates scorecards that can be used as quality gates in your CI pipeline.

### Features

- **CI-ready**: Designed for automated pipelines (GitHub Actions, GitLab CI, etc.)
- **WCAG compliance**: Tests against WCAG 2.1 AA guidelines
- **Scorecard output**: Machine-readable reports for pass/fail gating
- **Part of accessibility-suite**: Works alongside a11y-assist, a11y-lint, and a11y-evidence-engine

## Requirements

- Node.js >= 18
- Python 3.10+ (installed automatically via postinstall if needed)

## Links

- [GitHub Repository](https://github.com/mcp-tool-shop-org/accessibility-suite)
- [a11y-ci Source](https://github.com/mcp-tool-shop-org/accessibility-suite/tree/main/src/a11y-ci)

## License

MIT
