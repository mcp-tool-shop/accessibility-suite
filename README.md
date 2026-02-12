# accessibility-suite

Unified monorepo for accessibility testing, evidence generation, and compliance tooling.

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
