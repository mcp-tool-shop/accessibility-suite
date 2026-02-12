# Contributing to a11y-mcp-tools

Thank you for your interest in contributing to a11y-mcp-tools! We appreciate your help in making web accessibility testing more robust and evidence-based.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in [GitHub Issues](https://github.com/mcp-tool-shop-org/a11y-mcp-tools/issues)
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

# Test CLI locally
node bin/cli.js evidence --target fixtures/html/example.html --dom-snapshot

# Test MCP server locally
node bin/server.js
```

### Testing

All new features should include tests. Tests are located in the `test/` directory and use Node's built-in test runner.

```javascript
// Example test structure
import { test } from 'node:test';
import assert from 'node:assert/strict';

test('should detect accessibility issue', () => {
  // Arrange
  const html = '<img src="test.jpg">';
  
  // Act
  const result = diagnose({ html });
  
  // Assert
  assert.equal(result.findings.length, 1);
  assert.equal(result.findings[0].rule, 'alt');
});
```

### Adding New WCAG Rules

1. Add rule implementation in `src/rules/`
2. Add test cases in `test/*.test.js`
3. Update README.md with rule documentation
4. Add method ID to PROV_METHODS_CATALOG.md
5. Update schemas if needed

### Code Style

- Use ES modules (`import`/`export`)
- Prefer `const` over `let`
- Use descriptive variable names
- Add JSDoc comments for public APIs
- Follow existing patterns for consistency

### MCP Envelope Design Principles

- **Tamper-evident** - All evidence includes integrity digests
- **Traceable** - Provenance records for all operations
- **Deterministic** - Same input produces same output
- **Evidence-anchored** - Findings reference specific artifact locations
- **SAFE guidance** - Fix suggestions describe intent, not direct code writes

## Project Structure

```
a11y-mcp-tools/
├── bin/               # CLI and server entry points
├── src/               # Source code
│   ├── tools/         # MCP tool implementations
│   ├── rules/         # WCAG rule checkers
│   ├── schemas/       # JSON schemas
│   └── index.js       # Main exports
├── test/              # Test suite
├── fixtures/          # Test fixtures
└── package.json       # Project configuration
```

## Schema Validation

All requests and responses must validate against JSON schemas in `src/schemas/`:
- `envelope.schema.v0.1.json` - MCP envelope format
- `evidence.bundle.schema.v0.1.json` - Evidence bundle
- `diagnosis.schema.v0.1.json` - Diagnosis output

## Exit Codes

Maintain CI-native exit codes:
- `0` - Success (no findings at/above severity threshold)
- `2` - Findings exist (operation succeeded, but issues found)
- `3` - Capture/validation failure
- `4` - Provenance verification failed

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Questions?

Open an issue or start a discussion. We're here to help!
