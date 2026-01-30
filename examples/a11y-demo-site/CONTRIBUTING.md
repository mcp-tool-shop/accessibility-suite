# Contributing to a11y-demo-site

Thank you for your interest in contributing to a11y-demo-site! This repository demonstrates accessibility testing with provenance verification.

## How to Contribute

### Reporting Issues

If you find a problem or have a suggestion:

1. Check if the issue already exists in [GitHub Issues](https://github.com/mcp-tool-shop/a11y-demo-site/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment details

### Contributing Code

1. **Fork the repository** and create a branch from `main`
2. **Make your changes**
   - Add or modify HTML examples
   - Update scripts if needed
   - Update documentation
3. **Test locally**
   ```bash
   ./scripts/a11y.sh
   ```
4. **Commit your changes**
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable
5. **Submit a pull request**
   - Describe what your PR does and why
   - Link to related issues

### Local Testing

**Prerequisites:**
- `npm install -g a11y-evidence-engine`
- `pip install a11y-assist`

**Run the demo:**
```bash
./scripts/a11y.sh
```

Results will be in `results/`:
- `findings.json` - Accessibility findings
- `provenance/` - Provenance bundles
- `a11y-assist/` - Fix advisories

### Adding HTML Examples

To add new accessibility test cases:

1. Create or modify HTML files in `html/`
2. Add intentional accessibility issues for demonstration
3. Document the issues in README.md
4. Run `./scripts/a11y.sh` to verify findings are detected

### CI Workflow

The GitHub Actions workflow:
- Runs accessibility scans on all HTML files
- Verifies provenance integrity
- Uploads results as artifacts
- Fails on accessibility errors (by design, to demonstrate detection)

## Project Purpose

This demo site intentionally contains accessibility issues to demonstrate:
- Evidence-based accessibility testing
- Provenance tracking with SHA-256 integrity
- Fix-oriented advisory generation
- CI integration with artifact uploads

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Questions?

Open an issue or start a discussion. We're here to help!
