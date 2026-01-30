"use strict";

const { describe, it, before, after } = require("node:test");
const assert = require("node:assert");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { scan } = require("../src/scan.js");
const { canonicalize } = require("../src/evidence/canonicalize.js");

const FIXTURES_DIR = path.join(__dirname, "..", "fixtures");
const TEST_OUT_DIR = path.join(__dirname, "..", "test-output-vectors");

describe("provenance vectors", () => {
  before(() => {
    if (fs.existsSync(TEST_OUT_DIR)) {
      fs.rmSync(TEST_OUT_DIR, { recursive: true });
    }
  });

  after(() => {
    if (fs.existsSync(TEST_OUT_DIR)) {
      fs.rmSync(TEST_OUT_DIR, { recursive: true });
    }
  });

  describe("provenance file emission", () => {
    it("should emit record.json, digest.json, envelope.json for each finding", async () => {
      const outDir = path.join(TEST_OUT_DIR, "prov-files");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "img-missing-alt.html"),
        outDir
      );

      for (const finding of result.findings) {
        const provDir = path.join(outDir, "provenance", finding.finding_id);

        assert.ok(fs.existsSync(path.join(provDir, "record.json")));
        assert.ok(fs.existsSync(path.join(provDir, "digest.json")));
        assert.ok(fs.existsSync(path.join(provDir, "envelope.json")));
      }
    });
  });

  describe("digest verification", () => {
    it("should produce verifiable SHA-256 digests", async () => {
      const outDir = path.join(TEST_OUT_DIR, "digest-verify");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "img-missing-alt.html"),
        outDir
      );

      for (const finding of result.findings) {
        const provDir = path.join(outDir, "provenance", finding.finding_id);

        // Read the record and digest
        const record = JSON.parse(
          fs.readFileSync(path.join(provDir, "record.json"), "utf8")
        );
        const digest = JSON.parse(
          fs.readFileSync(path.join(provDir, "digest.json"), "utf8")
        );

        // Extract evidence from record
        const evidence =
          record["prov.record.v0.1"].outputs[0]["artifact.v0.1"].content;

        // Extract expected digest
        const expectedDigest =
          digest["prov.record.v0.1"].outputs[0]["artifact.v0.1"].digest.value;

        // Compute actual digest
        const canonical = canonicalize(evidence);
        const actualDigest = crypto
          .createHash("sha256")
          .update(canonical, "utf8")
          .digest("hex");

        assert.strictEqual(
          actualDigest,
          expectedDigest,
          `Digest mismatch for ${finding.finding_id}`
        );
      }
    });
  });

  describe("record structure", () => {
    it("should emit valid engine.extract.evidence.json_pointer records", async () => {
      const outDir = path.join(TEST_OUT_DIR, "record-structure");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "img-missing-alt.html"),
        outDir
      );

      const provDir = path.join(
        outDir,
        "provenance",
        result.findings[0].finding_id
      );
      const record = JSON.parse(
        fs.readFileSync(path.join(provDir, "record.json"), "utf8")
      );

      const prov = record["prov.record.v0.1"];

      assert.strictEqual(prov.method_id, "engine.extract.evidence.json_pointer");
      assert.ok(prov.timestamp);
      assert.ok(prov.inputs);
      assert.ok(prov.outputs);
      assert.ok(prov.agent);
      assert.strictEqual(prov.agent.name, "a11y-evidence-engine");
    });

    it("should emit valid integrity.digest.sha256 records", async () => {
      const outDir = path.join(TEST_OUT_DIR, "digest-structure");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "img-missing-alt.html"),
        outDir
      );

      const provDir = path.join(
        outDir,
        "provenance",
        result.findings[0].finding_id
      );
      const digest = JSON.parse(
        fs.readFileSync(path.join(provDir, "digest.json"), "utf8")
      );

      const prov = digest["prov.record.v0.1"];

      assert.strictEqual(prov.method_id, "integrity.digest.sha256");
      assert.ok(prov.outputs[0]["artifact.v0.1"].digest);
      assert.strictEqual(
        prov.outputs[0]["artifact.v0.1"].digest.algorithm,
        "sha256"
      );

      // Digest value should be 64 hex chars
      const digestValue = prov.outputs[0]["artifact.v0.1"].digest.value;
      assert.strictEqual(digestValue.length, 64);
      assert.match(digestValue, /^[a-f0-9]+$/);
    });

    it("should emit valid adapter.wrap.envelope_v0_1 records", async () => {
      const outDir = path.join(TEST_OUT_DIR, "envelope-structure");
      const result = await scan(
        path.join(FIXTURES_DIR, "bad", "img-missing-alt.html"),
        outDir
      );

      const provDir = path.join(
        outDir,
        "provenance",
        result.findings[0].finding_id
      );
      const envelope = JSON.parse(
        fs.readFileSync(path.join(provDir, "envelope.json"), "utf8")
      );

      assert.ok(envelope["mcp.envelope.v0.1"]);
      assert.ok(envelope["mcp.envelope.v0.1"].result);
      assert.ok(envelope["mcp.envelope.v0.1"].provenance);

      const prov = envelope["mcp.envelope.v0.1"].provenance["prov.record.v0.1"];
      assert.strictEqual(prov.method_id, "adapter.wrap.envelope_v0_1");
    });
  });

  describe("canonicalization", () => {
    it("should canonicalize JSON correctly", () => {
      // Test sorted keys
      const obj = { z: 1, a: 2, m: 3 };
      assert.strictEqual(canonicalize(obj), '{"a":2,"m":3,"z":1}');

      // Test nested objects
      const nested = { b: { d: 1, c: 2 }, a: 1 };
      assert.strictEqual(canonicalize(nested), '{"a":1,"b":{"c":2,"d":1}}');

      // Test arrays (preserve order)
      const arr = [3, 1, 2];
      assert.strictEqual(canonicalize(arr), "[3,1,2]");

      // Test strings with escaping
      assert.strictEqual(canonicalize('hello "world"'), '"hello \\"world\\""');

      // Test null and booleans
      assert.strictEqual(canonicalize(null), "null");
      assert.strictEqual(canonicalize(true), "true");
      assert.strictEqual(canonicalize(false), "false");
    });

    it("should reject non-finite numbers", () => {
      assert.throws(() => canonicalize(Infinity));
      assert.throws(() => canonicalize(-Infinity));
      assert.throws(() => canonicalize(NaN));
    });
  });
});
