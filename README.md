<p align="center">
  <img src="logo.png" width="200" alt="accessibility-suite">
</p>

# accessibility-suite

> Part of [MCP Tool Shop](https://mcptoolshop.com)


Unified monorepo for accessibility testing, evidence generation, and compliance tooling.

## Migrated Repositories

The following repositories have been merged into this monorepo. Please file all issues and PRs here.

| Original Repo | New Location |
|---------------|--------------|
| `a11y-assist` | [`src/a11y-assist/`](src/a11y-assist/) |
| `a11y-ci` | [`src/a11y-ci/`](src/a11y-ci/) |
| `a11y-lint` | [`src/a11y-lint/`](src/a11y-lint/) |
| `a11y-evidence-engine` | [`src/a11y-evidence-engine/`](src/a11y-evidence-engine/) |
| `a11y-mcp-tools` | [`src/a11y-mcp-tools/`](src/a11y-mcp-tools/) |
| `a11y-demo-site` | [`examples/a11y-demo-site/`](examples/a11y-demo-site/) |

## Projects

| Project | Description | Tech |
|---------|-------------|------|
| `src/a11y-assist/` | Accessibility testing assistant | Python |
| `src/a11y-ci/` | CI/CD integration for accessibility checks | Python |
| `src/a11y-lint/` | Accessibility linter | Python |
| `src/a11y-evidence-engine/` | Evidence generation and reporting | Node.js |
| `src/a11y-mcp-tools/` | MCP server tools for accessibility | Node.js |
| `examples/a11y-demo-site/` | Demo site for testing | HTML |
| `docs/prov-spec/` | Provenance specification | Spec |

## Quick Start

```bash
# Clone
git clone https://github.com/mcp-tool-shop-org/accessibility-suite.git
cd accessibility-suite

# Python tools (a11y-assist, a11y-ci, a11y-lint)
cd src/a11y-lint
pip install -e .
a11y-lint --help

# Node.js tools (a11y-evidence-engine, a11y-mcp-tools)
cd src/a11y-evidence-engine
npm install
npm test
```

## License

MIT
