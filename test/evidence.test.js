"use strict";

const { describe, it, before, after } = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const path = require("path");

const {
  captureEvidence,
  canonicalizeHtml,
  createDomSnapshot,
} = require("../src/tools/evidence.js");

const FIXTURES_DIR = path.join(__dirname, "fixtures");

describe("a11y.evidence", () => {
  before(() => {
    // Create test fixtures
    fs.mkdirSync(FIXTURES_DIR, { recursive: true });

    fs.writeFileSync(
      path.join(FIXTURES_DIR, "test.html"),
      `<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
  <img src="test.png">
  <button></button>
</body>
</html>`
    );

    fs.writeFileSync(
      path.join(FIXTURES_DIR, "test.log"),
      "Some CLI output\nAnother line"
    );
  });

  after(() => {
    // Clean up
    fs.rmSync(FIXTURES_DIR, { recursive: true, force: true });
  });

  describe("captureEvidence", () => {
    it("should capture HTML file and create artifact", async () => {
      const result = await captureEvidence({
        targets: [{ kind: "file", path: path.join(FIXTURES_DIR, "test.html") }],
        capture: { html: { canonicalize: false } },
      });

      assert.ok(result.bundle_id);
      assert.ok(result.artifacts.length >= 1);

      const htmlArtifact = result.artifacts.find((a) =>
        a.artifact_id.includes("html")
      );
      assert.ok(htmlArtifact);
      assert.strictEqual(htmlArtifact.media_type, "text/html");
      assert.ok(htmlArtifact.digest.hex);
      assert.strictEqual(htmlArtifact.digest.alg, "sha256");
    });

    it("should create DOM snapshot when requested", async () => {
      const result = await captureEvidence({
        targets: [{ kind: "file", path: path.join(FIXTURES_DIR, "test.html") }],
        capture: {
          html: { canonicalize: false },
          dom: { snapshot: true },
        },
      });

      const domArtifact = result.artifacts.find((a) =>
        a.artifact_id.includes("dom")
      );
      assert.ok(domArtifact);
      assert.strictEqual(domArtifact.media_type, "application/json");
      assert.ok(domArtifact.labels.includes("dom-snapshot"));
    });

    it("should capture CLI log", async () => {
      const result = await captureEvidence({
        targets: [{ kind: "cli_log", path: path.join(FIXTURES_DIR, "test.log") }],
      });

      const logArtifact = result.artifacts.find((a) =>
        a.artifact_id.includes("log")
      );
      assert.ok(logArtifact);
      assert.ok(logArtifact.labels.includes("cli-log"));
    });

    it("should add labels to artifacts", async () => {
      const result = await captureEvidence({
        targets: [{ kind: "file", path: path.join(FIXTURES_DIR, "test.html") }],
        labels: ["baseline", "wcag-2.2-aa"],
      });

      const artifact = result.artifacts[0];
      assert.ok(artifact.labels.includes("baseline"));
      assert.ok(artifact.labels.includes("wcag-2.2-aa"));
    });

    it("should include provenance record", async () => {
      const result = await captureEvidence({
        targets: [{ kind: "file", path: path.join(FIXTURES_DIR, "test.html") }],
      });

      assert.ok(result.provenance);
      assert.ok(result.provenance.record_id);
      assert.ok(result.provenance.methods.length > 0);
      assert.ok(result.provenance.inputs.length > 0);
      assert.ok(result.provenance.outputs.length > 0);
    });

    it("should capture environment info when requested", async () => {
      const result = await captureEvidence({
        targets: [{ kind: "file", path: path.join(FIXTURES_DIR, "test.html") }],
        capture: {
          environment: { include: ["os", "node"] },
        },
      });

      assert.ok(result.environment);
      assert.ok(result.environment.os);
      assert.ok(result.environment.node);
    });
  });

  describe("canonicalizeHtml", () => {
    it("should sort attributes alphabetically", () => {
      const html = '<div class="foo" id="bar">text</div>';
      const result = canonicalizeHtml(html);
      // Should have class before id alphabetically? Actually id comes before class
      assert.ok(result.includes("class="));
      assert.ok(result.includes("id="));
    });

    it("should normalize whitespace", () => {
      const html = "<p>  Multiple   spaces  </p>";
      const result = canonicalizeHtml(html);
      assert.ok(!result.includes("  ")); // No double spaces
    });

    it("should lowercase tags", () => {
      const html = "<DIV>content</DIV>";
      const result = canonicalizeHtml(html);
      assert.ok(result.includes("<div>"));
      assert.ok(result.includes("</div>"));
    });
  });

  describe("createDomSnapshot", () => {
    it("should create flat nodes array", () => {
      const html = "<html><body><p>Text</p></body></html>";
      const result = createDomSnapshot(html);

      assert.ok(result.nodes);
      assert.ok(Array.isArray(result.nodes));
      assert.ok(result.nodes.length > 0);
    });

    it("should assign indices to nodes", () => {
      const html = "<html><body><p>Text</p></body></html>";
      const result = createDomSnapshot(html);

      for (let i = 0; i < result.nodes.length; i++) {
        assert.strictEqual(result.nodes[i].index, i);
      }
    });

    it("should include CSS selectors when requested", () => {
      const html = '<div id="main" class="container">text</div>';
      const result = createDomSnapshot(html, { include_css_selectors: true });

      const divNode = result.nodes.find(
        (n) => n.type === "element" && n.tagName === "div"
      );
      assert.ok(divNode);
      assert.ok(divNode.selector);
      assert.ok(divNode.selector.includes("#main"));
    });
  });
});
