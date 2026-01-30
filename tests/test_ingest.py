"""Tests for the ingest command."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from a11y_assist.ingest import (
    IngestError,
    build_advisories,
    canonicalize,
    group_by_file,
    group_by_rule,
    ingest,
    load_findings,
    verify_provenance,
    write_advisories,
    write_ingest_summary,
)


@pytest.fixture
def sample_findings(tmp_path: Path) -> Path:
    """Create a sample findings.json for testing."""
    findings = {
        "engine": "a11y-evidence-engine",
        "version": "0.1.0",
        "target": {"path": "./test-html"},
        "summary": {"files_scanned": 2, "errors": 3, "warnings": 1, "info": 0},
        "findings": [
            {
                "finding_id": "finding-0001",
                "rule_id": "html.img.missing_alt",
                "severity": "error",
                "confidence": 0.98,
                "message": "Image element is missing alt text.",
                "location": {"file": "index.html", "json_pointer": "/nodes/5"},
                "evidence_ref": {
                    "record": "provenance/finding-0001/record.json",
                    "digest": "provenance/finding-0001/digest.json",
                    "envelope": "provenance/finding-0001/envelope.json",
                },
            },
            {
                "finding_id": "finding-0002",
                "rule_id": "html.img.missing_alt",
                "severity": "error",
                "confidence": 0.98,
                "message": "Image element is missing alt text.",
                "location": {"file": "index.html", "json_pointer": "/nodes/8"},
                "evidence_ref": {
                    "record": "provenance/finding-0002/record.json",
                    "digest": "provenance/finding-0002/digest.json",
                    "envelope": "provenance/finding-0002/envelope.json",
                },
            },
            {
                "finding_id": "finding-0003",
                "rule_id": "html.form_control.missing_label",
                "severity": "error",
                "confidence": 0.95,
                "message": "Form control is missing an associated label.",
                "location": {"file": "form.html", "json_pointer": "/nodes/3"},
                "evidence_ref": {
                    "record": "provenance/finding-0003/record.json",
                    "digest": "provenance/finding-0003/digest.json",
                    "envelope": "provenance/finding-0003/envelope.json",
                },
            },
            {
                "finding_id": "finding-0004",
                "rule_id": "html.document.missing_lang",
                "severity": "warning",
                "confidence": 1.0,
                "message": "Document is missing lang attribute.",
                "location": {"file": "form.html", "json_pointer": "/nodes/0"},
                "evidence_ref": {
                    "record": "provenance/finding-0004/record.json",
                    "digest": "provenance/finding-0004/digest.json",
                    "envelope": "provenance/finding-0004/envelope.json",
                },
            },
        ],
    }

    findings_path = tmp_path / "findings.json"
    findings_path.write_text(json.dumps(findings, indent=2))
    return findings_path


@pytest.fixture
def findings_with_provenance(tmp_path: Path, sample_findings: Path) -> Path:
    """Create findings with valid provenance bundles."""
    # Create provenance directories
    for i in range(1, 5):
        prov_dir = tmp_path / f"provenance/finding-000{i}"
        prov_dir.mkdir(parents=True, exist_ok=True)

        # Evidence content
        evidence = {
            "document_ref": "test.html",
            "pointer": f"/nodes/{i}",
            "evidence": {"tagName": "img", "attrs": {}},
        }

        # Compute digest
        canonical = canonicalize(evidence)
        import hashlib

        digest_value = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        # Write record.json
        record = {
            "prov.record.v0.1": {
                "method_id": "engine.extract.evidence.json_pointer",
                "timestamp": "2026-01-26T00:00:00Z",
                "inputs": [],
                "outputs": [{"artifact.v0.1": {"name": "evidence", "content": evidence}}],
                "agent": {"name": "test", "version": "1.0"},
            }
        }
        (prov_dir / "record.json").write_text(json.dumps(record))

        # Write digest.json
        digest = {
            "prov.record.v0.1": {
                "method_id": "integrity.digest.sha256",
                "timestamp": "2026-01-26T00:00:00Z",
                "inputs": [],
                "outputs": [
                    {
                        "artifact.v0.1": {
                            "name": "digest",
                            "digest": {"algorithm": "sha256", "value": digest_value},
                        }
                    }
                ],
                "agent": {"name": "test", "version": "1.0"},
            }
        }
        (prov_dir / "digest.json").write_text(json.dumps(digest))

        # Write envelope.json
        envelope = {"mcp.envelope.v0.1": {"result": {}, "provenance": {}}}
        (prov_dir / "envelope.json").write_text(json.dumps(envelope))

    return sample_findings


class TestLoadFindings:
    def test_load_valid_findings(self, sample_findings: Path):
        data = load_findings(sample_findings)
        assert data["engine"] == "a11y-evidence-engine"
        assert len(data["findings"]) == 4

    def test_load_missing_file(self, tmp_path: Path):
        with pytest.raises(IngestError, match="not found"):
            load_findings(tmp_path / "nonexistent.json")

    def test_load_invalid_json(self, tmp_path: Path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")
        with pytest.raises(IngestError, match="Invalid JSON"):
            load_findings(bad_file)

    def test_load_missing_required_fields(self, tmp_path: Path):
        incomplete = tmp_path / "incomplete.json"
        incomplete.write_text('{"engine": "test"}')
        with pytest.raises(IngestError, match="Missing required"):
            load_findings(incomplete)


class TestCanonicalize:
    def test_sorted_keys(self):
        assert canonicalize({"z": 1, "a": 2}) == '{"a":2,"z":1}'

    def test_nested_objects(self):
        obj = {"b": {"d": 1, "c": 2}, "a": 1}
        assert canonicalize(obj) == '{"a":1,"b":{"c":2,"d":1}}'

    def test_arrays_preserve_order(self):
        assert canonicalize([3, 1, 2]) == "[3,1,2]"

    def test_null_and_booleans(self):
        assert canonicalize(None) == "null"
        assert canonicalize(True) == "true"
        assert canonicalize(False) == "false"

    def test_strings_escaped(self):
        assert canonicalize('hello "world"') == '"hello \\"world\\""'


class TestGroupByRule:
    def test_groups_correctly(self, sample_findings: Path):
        data = load_findings(sample_findings)
        grouped = group_by_rule(data["findings"])

        assert len(grouped) == 3
        # Should be sorted by count descending
        assert grouped[0]["rule_id"] == "html.img.missing_alt"
        assert grouped[0]["count"] == 2


class TestGroupByFile:
    def test_groups_correctly(self, sample_findings: Path):
        data = load_findings(sample_findings)
        grouped = group_by_file(data["findings"])

        assert len(grouped) == 2
        # index.html has 2 errors, form.html has 1 error + 1 warning
        assert grouped[0]["file"] == "index.html"
        assert grouped[0]["errors"] == 2


class TestBuildAdvisories:
    def test_builds_advisories(self, sample_findings: Path):
        data = load_findings(sample_findings)
        advisories = build_advisories(data["findings"])

        assert len(advisories) == 3
        # First advisory should be for most common rule
        assert advisories[0]["rule_id"] == "html.img.missing_alt"
        assert len(advisories[0]["instances"]) == 2
        assert advisories[0]["title"] == "Add alt text to images"


class TestIngest:
    def test_basic_ingest(self, sample_findings: Path):
        result = ingest(sample_findings)

        assert result.source_engine == "a11y-evidence-engine"
        assert result.source_version == "0.1.0"
        assert len(result.findings) == 4
        assert len(result.by_rule) == 3

    def test_filter_by_severity(self, sample_findings: Path):
        result = ingest(sample_findings, min_severity="error")

        # Should exclude the warning
        assert len(result.findings) == 3

    def test_provenance_verification_missing_files(self, sample_findings: Path):
        result = ingest(sample_findings, verify_provenance_flag=True)

        # Should have errors because provenance files don't exist
        assert not result.provenance_verified
        assert len(result.provenance_errors) > 0

    def test_provenance_verification_success(self, findings_with_provenance: Path):
        result = ingest(findings_with_provenance, verify_provenance_flag=True)

        assert result.provenance_verified
        assert len(result.provenance_errors) == 0


class TestWriteOutputs:
    def test_write_summary(self, sample_findings: Path, tmp_path: Path):
        result = ingest(sample_findings)
        out_path = tmp_path / "output" / "ingest-summary.json"

        write_ingest_summary(result, out_path)

        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert data["source_engine"] == "a11y-evidence-engine"
        assert "by_rule" in data

    def test_write_advisories(self, sample_findings: Path, tmp_path: Path):
        result = ingest(sample_findings)
        out_path = tmp_path / "output" / "advisories.json"

        write_advisories(result, out_path)

        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert data["schema"] == "a11y-assist/advisories@v0.1"
        assert len(data["advisories"]) == 3


class TestVerifyProvenance:
    def test_missing_evidence_ref(self, tmp_path: Path):
        finding = {"finding_id": "test-001"}
        success, error = verify_provenance(finding, tmp_path)

        assert not success
        assert "Missing evidence_ref" in error

    def test_missing_file(self, tmp_path: Path):
        finding = {
            "finding_id": "test-001",
            "evidence_ref": {
                "record": "provenance/record.json",
                "digest": "provenance/digest.json",
                "envelope": "provenance/envelope.json",
            },
        }
        success, error = verify_provenance(finding, tmp_path)

        assert not success
        assert "not found" in error

    def test_valid_provenance(self, findings_with_provenance: Path):
        data = load_findings(findings_with_provenance)
        base_dir = findings_with_provenance.parent

        for finding in data["findings"]:
            success, error = verify_provenance(finding, base_dir)
            assert success, f"Failed for {finding['finding_id']}: {error}"
