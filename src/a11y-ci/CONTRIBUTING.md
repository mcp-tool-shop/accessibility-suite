# Contributing to a11y-ci

Thank you for your interest in contributing to a11y-ci! This is a CI gate for a11y-lint scorecards with low-vision-first output.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in [GitHub Issues](https://github.com/mcp-tool-shop-org/a11y-ci/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (Python version, OS)
   - Example scorecard files if relevant

### Contributing Code

1. **Fork the repository** and create a branch from `main`
2. **Make your changes**
   - Follow the existing code style
   - Maintain low-vision-first output contract
   - Ensure deterministic behavior (no network calls)
3. **Test your changes**
   ```bash
   pytest tests/ -v
   ```
4. **Commit your changes**
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable
5. **Submit a pull request**
   - Describe what your PR does and why
   - Link to related issues

### Development Workflow

```bash
# Clone the repository
git clone https://github.com/mcp-tool-shop-org/a11y-ci.git
cd a11y-ci

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linter
ruff check .

# Test CLI
a11y-ci gate --current tests/fixtures/scorecard.json
```

### Low-Vision-First Output Contract

All CLI output must follow the predictable structure:

```
[STATUS] Title (ID: NAMESPACE.CATEGORY.DETAIL)

What:
  What happened.

Why:
  Why it happened.

Fix:
  How to fix it.
```

**Guidelines:**
- Use `[OK]`, `[WARN]`, `[ERROR]`, or `[INFO]` status prefixes
- Always include an ID in the format `NAMESPACE.CATEGORY.DETAIL`
- Structure output in What/Why/Fix sections
- Keep language clear and direct
- Avoid color-only information (use text markers)

### Testing Requirements

- All gate logic must have unit tests
- Test both pass and fail scenarios
- Test baseline comparison logic
- Test allowlist validation (including expiry)
- Test exit codes (0=pass, 2=input error, 3=gate failed)
- Include fixture scorecard files when relevant

### Code Style

- Use type hints for all functions
- Follow PEP 8 conventions
- Use descriptive variable names
- Keep functions small and focused
- Use `ruff` for linting and formatting

### Design Principles

- **Deterministic** - No network calls, same input produces same output
- **CI-friendly** - Clear exit codes, machine-readable JSON input
- **Low-vision-first** - Predictable text structure, no color-only info
- **Strict by default** - Fails on serious+ findings unless explicitly configured
- **No permanent exceptions** - Allowlist entries must have expiry dates

### Adding Features

When adding new features:

1. Open an issue first to discuss the approach
2. Maintain backward compatibility with existing scorecards
3. Update README.md with usage examples
4. Add tests for the new functionality
5. Ensure output follows the low-vision-first contract

### Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md (if exists)
3. Create git tag: `git tag v0.x.x`
4. Push tag: `git push origin v0.x.x`
5. GitHub Actions will publish to PyPI

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Questions?

Open an issue or start a discussion. We're here to help!

## Related Projects

- [a11y-lint](https://github.com/mcp-tool-shop-org/a11y-lint) - Linter that produces scorecards
- [a11y-assist](https://github.com/mcp-tool-shop-org/a11y-assist) - CLI assistant for accessibility
- [a11y-mcp-tools](https://github.com/mcp-tool-shop-org/a11y-mcp-tools) - MCP tools for accessibility
