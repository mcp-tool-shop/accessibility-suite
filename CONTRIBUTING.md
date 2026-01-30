# Contributing to a11y-evidence-engine

Thank you for your interest in contributing to a11y-evidence-engine! We appreciate your help in building a robust accessibility evidence engine with provenance tracking.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in [GitHub Issues](https://github.com/mcp-tool-shop/a11y-evidence-engine/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (Node version, OS)
   - Sample HTML if relevant

### Contributing Code

1. **Fork the repository** and create a branch from `main`
2. **Set up your development environment**
   ```bash
   npm install
   ```
3. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Ensure all tests pass: `npm test`
   - Update documentation as needed
4. **Commit your changes**
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable
5. **Submit a pull request**
   - Describe what your PR does and why
   - Link to related issues

### Development Workflow

```bash
# Install dependencies
npm install

# Run tests
npm test

# Scan HTML files (test the CLI)
npm run scan -- fixtures/html/example.html

# Test the engine directly
node bin/a11y-engine.js scan path/to/html --out results
```

### Testing

All new features should include tests. Tests are located in the `test/` directory and use Node's built-in test runner.

```javascript
// Example test structure
import { test } from 'node:test';
import assert from 'node:assert/strict';

test('should detect missing lang attribute', () => {
  const html = '<html><head></head><body></body></html>';
  const findings = scan(html);
  assert.equal(findings[0].rule, 'html.document.missing_lang');
});
```

### Adding New Rules

1. Add rule implementation in `src/rules/`
2. Add test cases in `test/*.test.js`
3. Update README.md with rule documentation
4. Ensure provenance records are generated correctly

### Code Style

- Use ES modules (`import`/`export`)
- Prefer `const` over `let`
- Use descriptive variable names
- Add JSDoc comments for public APIs
- Follow existing patterns for consistency

### Provenance Design Principles

- **Deterministic** - Same input produces same output
- **Verifiable** - Evidence can be independently verified
- **Tamper-evident** - SHA-256 digests detect any changes
- **Traceable** - prov-spec records document all operations
- **Evidence-anchored** - Findings reference specific artifact locations (JSON Pointer)

## Project Structure

```
a11y-evidence-engine/
├── bin/               # CLI entry point
├── src/               # Source code
│   ├── cli.js         # CLI implementation
│   ├── scanner.js     # Core scanner
│   ├── rules/         # Rule implementations
│   └── provenance.js  # Provenance generation
├── test/              # Test suite
├── fixtures/          # Test fixtures
└── package.json       # Project configuration
```

## Exit Codes

Maintain CI-native exit codes:
- `0` - No findings with severity `error`
- `2` - At least one `error` finding
- `3` - Internal engine failure / invalid input

## Provenance Records

Ensure all findings include three prov-spec records:
1. `record.json` - Evidence extraction
2. `digest.json` - SHA-256 integrity
3. `envelope.json` - MCP envelope

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Questions?

Open an issue or start a discussion. We're here to help!
