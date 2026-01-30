"""Provenance Validator Tool.

Reference implementation for prov-spec validation.

Validates:
- Method ID syntax (grammar conformance)
- Method catalog membership (known IDs)
- Capability manifest schemas
- Provenance record semantic contracts
- Test vectors

Usage:
    python prov_validator.py validate-methods record.json
    python prov_validator.py validate-manifest prov-capabilities.json
    python prov_validator.py check-vector integrity.digest.sha256
    python prov_validator.py list-methods
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Spec version
SPEC_VERSION = "0.1.0"

# Method ID grammar (from PROV_METHODS_SPEC.md Section 3)
METHOD_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*(_v[0-9]+_[0-9]+)?$"
)

# Known namespaces
STABLE_NAMESPACES = {"adapter", "engine", "integrity", "lineage"}
RESERVED_NAMESPACES = {"policy", "attestation", "execution", "audit"}


def find_spec_root() -> Path:
    """Find the spec root directory."""
    # Try relative to this file
    here = Path(__file__).parent
    candidates = [
        here.parent.parent / "spec",  # tools/python/prov_validator.py
        here.parent / "spec",  # tools/prov_validator.py
        here / "spec",  # prov_validator.py in root
        Path.cwd() / "spec",  # current directory
    ]
    for path in candidates:
        if path.exists() and (path / "methods.json").exists():
            return path
    return Path.cwd() / "spec"


def load_json(path: Path) -> Any:
    """Load JSON from file."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_method_catalog() -> Dict[str, Any]:
    """Load the method catalog from spec/methods.json."""
    spec_path = find_spec_root() / "methods.json"
    if spec_path.exists():
        return load_json(spec_path)
    return {"methods": [], "namespaces": {}}


def canonical_json(obj: Any) -> str:
    """Serialize to canonical JSON for stable hashing.

    - Sorted keys
    - No whitespace
    - UTF-8
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def compute_artifact_digest(content: Any) -> Dict[str, str]:
    """Compute digest for an artifact's content."""
    if isinstance(content, bytes):
        data = content
    elif isinstance(content, str):
        data = content.encode("utf-8")
    else:
        data = canonical_json(content).encode("utf-8")
    return {"alg": "sha256", "value": compute_sha256(data)}


def validate_method_id_syntax(method_id: str) -> Tuple[bool, Optional[str]]:
    """Validate method ID matches grammar.

    Returns:
        (is_valid, error_message)
    """
    if not METHOD_ID_PATTERN.match(method_id):
        return False, f"Method ID '{method_id}' does not match grammar"
    return True, None


def validate_method_id_namespace(method_id: str) -> Tuple[bool, Optional[str]]:
    """Validate method ID uses a known namespace.

    Returns:
        (is_valid, error_message)
    """
    namespace = method_id.split(".")[0]
    if namespace in RESERVED_NAMESPACES:
        return False, f"Method ID '{method_id}' uses reserved namespace '{namespace}'"
    if namespace not in STABLE_NAMESPACES:
        return False, f"Method ID '{method_id}' uses unknown namespace '{namespace}'"
    return True, None


def validate_method_id_catalog(
    method_id: str, catalog: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """Validate method ID is in the catalog.

    Returns:
        (is_valid, error_message)
    """
    known_ids = {m["id"] for m in catalog.get("methods", [])}
    if method_id not in known_ids:
        return False, f"Method ID '{method_id}' is not in the catalog"
    return True, None


def validate_methods_in_record(
    record: Dict[str, Any], strict: bool = False
) -> List[Dict[str, Any]]:
    """Validate all method IDs in a provenance record.

    Args:
        record: Provenance record (prov.record.v0.1)
        strict: If True, require methods to be in catalog

    Returns:
        List of validation issues
    """
    issues = []
    catalog = load_method_catalog() if strict else {"methods": []}

    methods = record.get("methods", [])
    if not methods:
        issues.append({
            "level": "warning",
            "message": "Provenance record has no methods claimed",
        })
        return issues

    for method_id in methods:
        # Check syntax
        valid, error = validate_method_id_syntax(method_id)
        if not valid:
            issues.append({"level": "error", "message": error})
            continue

        # Check namespace
        valid, error = validate_method_id_namespace(method_id)
        if not valid:
            issues.append({"level": "error", "message": error})

        # Check catalog membership (strict mode only)
        if strict:
            valid, error = validate_method_id_catalog(method_id, catalog)
            if not valid:
                issues.append({"level": "warning", "message": error})

    return issues


def validate_capability_manifest(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate a prov-capabilities.json manifest.

    Args:
        manifest: Capability manifest

    Returns:
        List of validation issues
    """
    issues = []
    catalog = load_method_catalog()

    # Check schema version
    if manifest.get("schema") != "prov-capabilities@v0.1":
        issues.append({
            "level": "error",
            "message": f"Invalid schema: {manifest.get('schema')}",
        })

    # Validate implemented methods
    for method_id in manifest.get("implements", []):
        valid, error = validate_method_id_syntax(method_id)
        if not valid:
            issues.append({"level": "error", "message": error})
        else:
            valid, error = validate_method_id_catalog(method_id, catalog)
            if not valid:
                issues.append({"level": "warning", "message": error})

    # Validate optional methods
    for method_id in manifest.get("optional", []):
        valid, error = validate_method_id_syntax(method_id)
        if not valid:
            issues.append({"level": "error", "message": error})

    return issues


def check_test_vector(vector_id: str, expect_fail: bool = False) -> List[Dict[str, Any]]:
    """Run a test vector and check results.

    Args:
        vector_id: Method ID for the test vector
        expect_fail: If True, expect the vector to fail

    Returns:
        List of validation issues
    """
    issues = []
    spec_root = find_spec_root()
    vectors_path = spec_root / "vectors" / vector_id

    if not vectors_path.exists():
        issues.append({
            "level": "error",
            "message": f"Test vector not found: {vector_id}",
        })
        return issues

    input_path = vectors_path / "input.json"
    expected_path = vectors_path / "expected.json"

    if not input_path.exists() or not expected_path.exists():
        issues.append({
            "level": "error",
            "message": f"Missing input.json or expected.json for {vector_id}",
        })
        return issues

    input_data = load_json(input_path)
    expected = load_json(expected_path)

    # Check specific vector types
    if vector_id == "integrity.digest.sha256":
        # Compute digest and compare
        computed_canonical = canonical_json(input_data)
        computed_digest = compute_artifact_digest(input_data)

        if computed_canonical != expected.get("canonical_form"):
            issues.append({
                "level": "error",
                "message": f"Canonical form mismatch: got {computed_canonical}",
            })

        if computed_digest != expected.get("digest"):
            issues.append({
                "level": "error",
                "message": f"Digest mismatch: got {computed_digest}",
            })

        if not issues:
            issues.append({
                "level": "info",
                "message": f"Test vector {vector_id} passed",
            })

    elif vector_id == "adapter.wrap.envelope_v0_1":
        # Check envelope wrapping
        expected_schema = expected.get("schema_version")
        expected_result = expected.get("result")

        if expected_schema != "mcp.envelope.v0.1":
            issues.append({
                "level": "error",
                "message": "Expected schema version mismatch",
            })

        if input_data != expected_result:
            issues.append({
                "level": "error",
                "message": "Result should equal input (wrapping test)",
            })

        if not issues:
            issues.append({
                "level": "info",
                "message": f"Test vector {vector_id} passed",
            })

    else:
        issues.append({
            "level": "warning",
            "message": f"No validator implemented for {vector_id}",
        })

    return issues


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=f"prov-spec validator (spec v{SPEC_VERSION})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"prov-spec validator v{SPEC_VERSION}"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # validate-methods command
    methods_parser = subparsers.add_parser(
        "validate-methods",
        help="Validate method IDs in a provenance record",
    )
    methods_parser.add_argument("file", type=Path, help="Path to provenance record JSON")
    methods_parser.add_argument(
        "--strict",
        action="store_true",
        help="Require methods to be in catalog",
    )

    # validate-manifest command
    manifest_parser = subparsers.add_parser(
        "validate-manifest",
        help="Validate a capability manifest",
    )
    manifest_parser.add_argument("file", type=Path, help="Path to manifest JSON")

    # check-vector command
    vector_parser = subparsers.add_parser(
        "check-vector",
        help="Run a test vector",
    )
    vector_parser.add_argument("vector_id", help="Method ID for test vector")
    vector_parser.add_argument(
        "--expect-fail",
        action="store_true",
        help="Expect the vector to fail",
    )

    # list-methods command
    subparsers.add_parser(
        "list-methods",
        help="List all known method IDs",
    )

    # list-vectors command
    subparsers.add_parser(
        "list-vectors",
        help="List all test vectors",
    )

    args = parser.parse_args()

    if args.command == "validate-methods":
        record = load_json(args.file)
        # Handle envelope vs raw record
        if record.get("schema_version") == "mcp.envelope.v0.1":
            record = record.get("provenance", {})
        issues = validate_methods_in_record(record, strict=args.strict)

    elif args.command == "validate-manifest":
        manifest = load_json(args.file)
        issues = validate_capability_manifest(manifest)

    elif args.command == "check-vector":
        issues = check_test_vector(args.vector_id, expect_fail=getattr(args, "expect_fail", False))

    elif args.command == "list-methods":
        catalog = load_method_catalog()
        print(f"prov-spec v{SPEC_VERSION} - Known method IDs:\n")
        for method in catalog.get("methods", []):
            status = method.get("status", "unknown")
            print(f"  [{status:11}] {method['id']}")
            print(f"               {method.get('summary', '')}")
        return 0

    elif args.command == "list-vectors":
        spec_root = find_spec_root()
        vectors_path = spec_root / "vectors"
        print(f"prov-spec v{SPEC_VERSION} - Test vectors:\n")
        if vectors_path.exists():
            for vector_dir in sorted(vectors_path.iterdir()):
                if vector_dir.is_dir():
                    has_positive = (vector_dir / "input.json").exists()
                    has_negative = (vector_dir / "negative").exists()
                    markers = []
                    if has_positive:
                        markers.append("positive")
                    if has_negative:
                        markers.append("negative")
                    print(f"  {vector_dir.name} ({', '.join(markers)})")
        return 0

    else:
        parser.print_help()
        return 1

    # Print results
    has_errors = False
    for issue in issues:
        level = issue["level"]
        msg = issue["message"]
        if level == "error":
            print(f"ERROR: {msg}")
            has_errors = True
        elif level == "warning":
            print(f"WARNING: {msg}")
        else:
            print(f"INFO: {msg}")

    if not issues:
        print("OK: No issues found")

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
