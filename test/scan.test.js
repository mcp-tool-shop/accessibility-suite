"use strict";

const { describe, it, before, after } = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const path = require("path");
const { scan } = require("../src/scan.js");

const FIXTURES_DIR = path.join(__dirname, "..", "fixtures");
const TEST_OUT_DIR = path.join(__dirname, "..", "test-output");

describe("scan", () => {
  before(() => {
    // Clean up test output
    if (fs.existsSync(TEST_OUT_DIR)) {
      fs.rmSync(TEST_OUT_DIR, { recursive: true });
    }
  });

  after(() => {
    // Clean up test output
    if (fs.existsSync(TEST_OUT_DIR)) {
      fs.rmSync(TEST_OUT_DIR, { recursive: true });
    }
  });

  describe("good fixtures", () => {
    it("should find no errors in accessible HTML", async () => {
      const outDir = path.join(TEST_OUT_DIR, "good");
      const result = await scan(path.join(FIXTURES_DIR, "good"), outDir);

      assert.strictEqual(result.summary.errors, 0);
      assert.strictEqual(result.findings.length, 0);
    });
  });

  describe("bad fixtures", () => {
    it("should detect missing alt text", async () => {
      const outDir = path.join(TEST_OUT_DIR, "img-missing-alt");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "img-missing-alt.html"),
        outDir
      );

      assert.strictEqual(result.summary.errors, 2);

      const altFindings = result.findings.filter(
        (f) => f.rule_id === "html.img.missing_alt"
      );
      assert.strictEqual(altFindings.length, 2);

      // Check evidence_ref exists
      for (const finding of altFindings) {
        assert.ok(finding.evidence_ref);
        assert.ok(finding.evidence_ref.record);
        assert.ok(finding.evidence_ref.digest);
        assert.ok(finding.evidence_ref.envelope);
      }
    });

    it("should detect missing labels", async () => {
      const outDir = path.join(TEST_OUT_DIR, "input-missing-label");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "input-missing-label.html"),
        outDir
      );

      const labelFindings = result.findings.filter(
        (f) => f.rule_id === "html.form_control.missing_label"
      );
      assert.strictEqual(labelFindings.length, 2);
    });

    it("should detect missing accessible names", async () => {
      const outDir = path.join(TEST_OUT_DIR, "button-no-name");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "button-no-name.html"),
        outDir
      );

      const nameFindings = result.findings.filter(
        (f) => f.rule_id === "html.interactive.missing_name"
      );
      // 2 empty buttons + 1 empty link = 3
      assert.strictEqual(nameFindings.length, 3);
    });

    it("should detect missing lang attribute", async () => {
      const outDir = path.join(TEST_OUT_DIR, "missing-lang");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "missing-lang.html"),
        outDir
      );

      const langFindings = result.findings.filter(
        (f) => f.rule_id === "html.document.missing_lang"
      );
      assert.strictEqual(langFindings.length, 1);
    });
  });

  describe("output structure", () => {
    it("should produce findings.json with correct structure", async () => {
      const outDir = path.join(TEST_OUT_DIR, "structure");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "img-missing-alt.html"),
        outDir
      );

      // Check top-level structure
      assert.strictEqual(result.engine, "a11y-evidence-engine");
      assert.strictEqual(result.version, "0.1.0");
      assert.ok(result.target);
      assert.ok(result.summary);
      assert.ok(Array.isArray(result.findings));

      // Check findings.json was written
      const findingsPath = path.join(outDir, "findings.json");
      assert.ok(fs.existsSync(findingsPath));

      const written = JSON.parse(fs.readFileSync(findingsPath, "utf8"));
      assert.deepStrictEqual(written, result);
    });

    it("should assign deterministic finding IDs", async () => {
      const outDir = path.join(TEST_OUT_DIR, "deterministic");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "img-missing-alt.html"),
        outDir
      );

      assert.strictEqual(result.findings[0].finding_id, "finding-0001");
      assert.strictEqual(result.findings[1].finding_id, "finding-0002");
    });
  });

  describe("directory scanning", () => {
    it("should scan all HTML files in a directory", async () => {
      const outDir = path.join(TEST_OUT_DIR, "all-bad");
      const result = await scan(path.join(FIXTURES_DIR, "bad"), outDir);

      // Should scan all 4 bad fixture files
      assert.strictEqual(result.summary.files_scanned, 4);

      // Should find issues from all files
      assert.ok(result.summary.errors > 0);
    });
  });
});
