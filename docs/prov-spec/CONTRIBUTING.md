# Contributing to prov-spec

Thank you for your interest in contributing to prov-spec! This is a formal specification for provenance method IDs, records, and validation.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in [GitHub Issues](https://github.com/mcp-tool-shop/prov-spec/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (Python version, OS)

### Contributing to the Specification

**Before proposing a new method ID:**

1. Open an issue describing:
   - The real-world use case
   - Why existing method IDs don't suffice
   - Expected behavior and semantics
2. Wait for maintainer feedback
3. Method IDs require real-world justification — we don't speculatively add IDs

**Spec changes:**

1. Fork the repository and create a branch from `main`
2. Make your changes to files in `spec/`
3. Update `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
4. Submit a pull request with:
   - Clear description of changes
   - Rationale for the change
   - Backward compatibility analysis

### Contributing Reference Tools

Reference tools in `tools/` are provided for convenience and are not normative.

1. **Python validator** (`tools/python/prov_validator.py`):
   - Follow existing code style
   - Add test cases for new features
   - Ensure all test vectors pass
   - Keep dependencies minimal

### Adding Test Vectors

Test vectors live in `spec/vectors/[method-id]/`:

1. Create a new directory for the method ID
2. Add `input.json` and `expected.json` files
3. Follow the format of existing vectors
4. Ensure deterministic behavior
5. Update the method's documentation

### Development Workflow

```bash
# Clone the repository
git clone https://github.com/mcp-tool-shop/prov-spec.git
cd prov-spec

# Verify installation
python tools/python/prov_validator.py --help

# List known methods
python tools/python/prov_validator.py list-methods

# Run a specific test vector
python tools/python/prov_validator.py check-vector integrity.digest.sha256

# Validate a provenance record
python tools/python/prov_validator.py validate-methods record.json --strict
```

### Specification Style Guide

- Use RFC 2119 keywords (MUST, SHOULD, MAY) consistently
- Include examples for every requirement
- Keep language precise and unambiguous
- Reference existing standards where applicable
- Use ABNF notation for grammar rules

### Versioning Policy

- **Spec version:** Semantic Versioning 2.0.0
- **Method catalog:** Append-only within major version
- **Schemas:** `additionalProperties: false` for forward compatibility
- **Method IDs marked `stable`:** Append-only, semantics never change

### Conformance Levels

When adding features, consider the conformance level:

| Level | Name | Requirements |
|-------|------|--------------|
| **1** | Integrity | `integrity.digest.*` methods |
| **2** | Engine | Level 1 + `engine.*` methods |
| **3** | Lineage | Level 2 + `lineage.*` methods |

See [CONFORMANCE_LEVELS.md](CONFORMANCE_LEVELS.md) for details.

### Reserved Namespaces

These namespaces are reserved for future use:
- `policy.*` - Access control, permissions
- `attestation.*` - Signed claims, witnesses
- `execution.*` - Runtime context, environments
- `audit.*` - Compliance, logging

### Code Review Process

1. Maintainers review for:
   - Specification clarity
   - Backward compatibility
   - Real-world justification
   - Test coverage
2. Address feedback promptly
3. Maintainers merge when approved

### Testing Requirements

- All test vectors must pass
- New method IDs require test vectors
- Schema changes require validation examples
- Reference tools must validate correctly

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Questions?

Open an issue or start a discussion. We're here to help!

## References

- [PROV_METHODS_SPEC.md](spec/PROV_METHODS_SPEC.md) — Normative specification
- [CONFORMANCE_LEVELS.md](CONFORMANCE_LEVELS.md) — Conformance tiers
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html) — Key words for RFCs
