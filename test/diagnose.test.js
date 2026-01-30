"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert");

const { diagnose, RULES } = require("../src/tools/diagnose.js");

// Create a test bundle with DOM snapshot
function createTestBundle(nodes) {
  const domContent = JSON.stringify({ nodes, root: nodes[0] });

  return {
    bundle_id: "test-bundle",
    artifacts: [
      {
        artifact_id: "artifact:dom:test",
        media_type: "application/json",
        labels: ["dom-snapshot"],
        _content: domContent,
      },
    ],
    provenance: {
      record_id: "prov:test",
      methods: ["engine.capture.html_v0_1"],
      inputs: ["test.html"],
      outputs: ["artifact:dom:test"],
    },
  };
}

describe("a11y.diagnose", () => {
  describe("lang rule", () => {
    it("should detect missing lang attribute", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: {},
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["lang"] },
        output: { include_fix_guidance: true },
      });

      assert.ok(result.findings.length > 0);
      assert.strictEqual(result.findings[0].id, "a11y.lang.missing");
      assert.ok(result.findings[0].fix);
    });

    it("should detect empty lang attribute", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: { lang: "" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["lang"] },
      });

      assert.ok(result.findings.length > 0);
    });

    it("should pass when lang is present", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: { lang: "en" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["lang"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });
  });

  describe("alt rule", () => {
    it("should detect missing alt on img", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "img",
          attrs: { src: "test.png" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["alt"] },
        output: { include_fix_guidance: true },
      });

      assert.ok(result.findings.length > 0);
      assert.strictEqual(result.findings[0].id, "a11y.img.missing_alt");
    });

    it("should skip decorative images (role=presentation)", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "img",
          attrs: { src: "test.png", role: "presentation" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["alt"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });

    it("should skip hidden images (aria-hidden=true)", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "img",
          attrs: { src: "test.png", "aria-hidden": "true" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["alt"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });
  });

  describe("button-name rule", () => {
    it("should detect button without accessible name", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "button",
          attrs: {},
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["button-name"] },
      });

      assert.ok(result.findings.length > 0);
      assert.strictEqual(result.findings[0].id, "a11y.button.missing_name");
    });

    it("should pass when button has text content", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "button",
          attrs: {},
          index: 0,
          children: [{ type: "text", content: "Click me", index: 1 }],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["button-name"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });

    it("should pass when button has aria-label", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "button",
          attrs: { "aria-label": "Close dialog" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["button-name"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });
  });

  describe("link-name rule", () => {
    it("should detect link without accessible name", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "a",
          attrs: { href: "/page" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["link-name"] },
      });

      assert.ok(result.findings.length > 0);
      assert.strictEqual(result.findings[0].id, "a11y.link.missing_name");
    });

    it("should skip anchors without href", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "a",
          attrs: { name: "anchor" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["link-name"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });
  });

  describe("label rule", () => {
    it("should detect input without label", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "input",
          attrs: { type: "text" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["label"] },
      });

      assert.ok(result.findings.length > 0);
      assert.strictEqual(result.findings[0].id, "a11y.input.missing_label");
    });

    it("should skip hidden inputs", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "input",
          attrs: { type: "hidden" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["label"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });

    it("should pass when input has aria-label", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "input",
          attrs: { type: "text", "aria-label": "Search" },
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["label"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });

    it("should pass when input has associated label", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "label",
          attrs: { for: "email" },
          index: 0,
          children: [],
        },
        {
          type: "element",
          tagName: "input",
          attrs: { type: "email", id: "email" },
          index: 1,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["label"] },
      });

      assert.strictEqual(result.findings.length, 0);
    });
  });

  describe("output structure", () => {
    it("should include summary with severity counts", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: {},
          index: 0,
          children: [],
        },
        {
          type: "element",
          tagName: "img",
          attrs: { src: "test.png" },
          index: 1,
          children: [],
        },
      ]);

      const result = await diagnose({ bundle });

      assert.ok(result.summary);
      assert.ok(result.summary.severity_counts);
      assert.strictEqual(result.summary.findings_total, result.findings.length);
    });

    it("should include provenance record", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: {},
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({ bundle });

      assert.ok(result.provenance);
      assert.ok(result.provenance.methods);
      assert.ok(result.provenance.inputs);
    });

    it("should include evidence anchors in findings", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: {},
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["lang"] },
      });

      assert.ok(result.findings[0].targets);
      assert.ok(result.findings[0].targets[0].artifact_id);
      assert.ok(result.findings[0].targets[0].json_pointer);
    });

    it("should include fix guidance when requested", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: {},
          index: 0,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["lang"] },
        output: { include_fix_guidance: true },
      });

      assert.ok(result.findings[0].fix);
      assert.strictEqual(result.findings[0].fix.safe, true);
      assert.ok(result.findings[0].fix.patch);
    });
  });

  describe("rule filtering", () => {
    it("should only run included rules", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: {},
          index: 0,
          children: [],
        },
        {
          type: "element",
          tagName: "img",
          attrs: { src: "test.png" },
          index: 1,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { include: ["lang"] },
      });

      // Should only find lang issue, not alt issue
      assert.ok(result.findings.every((f) => f.id === "a11y.lang.missing"));
    });

    it("should exclude specified rules", async () => {
      const bundle = createTestBundle([
        {
          type: "element",
          tagName: "html",
          attrs: {},
          index: 0,
          children: [],
        },
        {
          type: "element",
          tagName: "img",
          attrs: { src: "test.png" },
          index: 1,
          children: [],
        },
      ]);

      const result = await diagnose({
        bundle,
        rules: { exclude: ["lang"] },
      });

      // Should not find lang issue
      assert.ok(result.findings.every((f) => f.id !== "a11y.lang.missing"));
    });
  });
});
