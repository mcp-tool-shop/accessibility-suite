"use strict";

/**
 * Schema validation tests.
 *
 * Validates golden fixtures against tool schemas to ensure
 * the contract can't drift.
 */

const { describe, it } = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const path = require("path");

const Ajv2020 = require("ajv/dist/2020");
const addFormats = require("ajv-formats");

// Schema paths
const SCHEMAS_DIR = path.join(__dirname, "../src/schemas");
const TOOLS_SCHEMAS_DIR = path.join(SCHEMAS_DIR, "tools");
const FIXTURES_DIR = path.join(__dirname, "../fixtures");

/**
 * Load a JSON file and remove $schema to avoid meta-schema issues.
 */
function loadSchema(filePath) {
  const schema = JSON.parse(fs.readFileSync(filePath, "utf8"));
  delete schema.$schema;
  return schema;
}

/**
 * Load a JSON file.
 */
function loadJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

/**
 * Create an AJV instance with all schemas loaded.
 */
function createValidator() {
  const ajv = new Ajv2020({
    strict: false,
    allErrors: true,
    verbose: true,
  });
  addFormats(ajv);

  // Load core schemas for $ref resolution
  const bundleSchema = loadSchema(path.join(SCHEMAS_DIR, "evidence.bundle.schema.v0.1.json"));
  const diagnosisSchema = loadSchema(path.join(SCHEMAS_DIR, "diagnosis.schema.v0.1.json"));

  // Add schemas with their $id URLs for proper $ref resolution
  ajv.addSchema(bundleSchema, "https://mcp-tool-shop.github.io/schemas/evidence.bundle.v0.1.json");
  ajv.addSchema(diagnosisSchema, "https://mcp-tool-shop.github.io/schemas/diagnosis.v0.1.json");

  return ajv;
}

describe("Schema Validation", () => {
  describe("a11y.evidence request schema", () => {
    it("should validate evidence request fixture", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.evidence.request.schema.v0.1.json"));
      const fixture = loadJson(path.join(FIXTURES_DIR, "requests/a11y.evidence.ok.json"));

      const validate = ajv.compile(schema);
      const valid = validate(fixture);

      if (!valid) {
        console.error("Validation errors:", JSON.stringify(validate.errors, null, 2));
      }

      assert.strictEqual(valid, true, `Evidence request should be valid: ${JSON.stringify(validate.errors)}`);
    });

    it("should reject invalid evidence request (missing targets)", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.evidence.request.schema.v0.1.json"));

      const invalidRequest = {
        mcp: {
          envelope: "mcp.envelope_v0_1",
          request_id: "req_test",
          tool: "a11y.evidence",
          client: { name: "test", version: "1.0.0" },
        },
        input: {
          capture: { html: { canonicalize: true } },
        },
      };

      const validate = ajv.compile(schema);
      const valid = validate(invalidRequest);

      assert.strictEqual(valid, false, "Should reject request without targets");
    });

    it("should reject evidence request with wrong tool name", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.evidence.request.schema.v0.1.json"));

      const invalidRequest = {
        mcp: {
          envelope: "mcp.envelope_v0_1",
          request_id: "req_test",
          tool: "a11y.diagnose",
          client: { name: "test", version: "1.0.0" },
        },
        input: {
          targets: [{ kind: "file", path: "test.html" }],
        },
      };

      const validate = ajv.compile(schema);
      const valid = validate(invalidRequest);

      assert.strictEqual(valid, false, "Should reject request with wrong tool name");
    });

    it("should require path for file targets", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.evidence.request.schema.v0.1.json"));

      const invalidRequest = {
        mcp: {
          envelope: "mcp.envelope_v0_1",
          request_id: "req_test",
          tool: "a11y.evidence",
          client: { name: "test", version: "1.0.0" },
        },
        input: {
          targets: [{ kind: "file" }],
        },
      };

      const validate = ajv.compile(schema);
      const valid = validate(invalidRequest);

      assert.strictEqual(valid, false, "Should reject file target without path");
    });

    it("should reject request with mcp.ok field (requests must not have ok)", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.evidence.request.schema.v0.1.json"));

      const invalidRequest = {
        mcp: {
          envelope: "mcp.envelope_v0_1",
          request_id: "req_test",
          tool: "a11y.evidence",
          client: { name: "test", version: "1.0.0" },
          ok: true,
        },
        input: {
          targets: [{ kind: "file", path: "test.html" }],
        },
      };

      const validate = ajv.compile(schema);
      const valid = validate(invalidRequest);

      assert.strictEqual(valid, false, "Should reject request with ok field");
    });
  });

  describe("a11y.diagnose request schema", () => {
    it("should validate diagnose request fixture", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.diagnose.request.schema.v0.1.json"));
      const fixture = loadJson(path.join(FIXTURES_DIR, "requests/a11y.diagnose.ok.json"));

      const validate = ajv.compile(schema);
      const valid = validate(fixture);

      if (!valid) {
        console.error("Validation errors:", JSON.stringify(validate.errors, null, 2));
      }

      assert.strictEqual(valid, true, `Diagnose request should be valid: ${JSON.stringify(validate.errors)}`);
    });

    it("should reject diagnose request without bundle_id", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.diagnose.request.schema.v0.1.json"));

      const invalidRequest = {
        mcp: {
          envelope: "mcp.envelope_v0_1",
          request_id: "req_test",
          tool: "a11y.diagnose",
          client: { name: "test", version: "1.0.0" },
        },
        input: {
          artifacts: ["artifact:dom:index"],
          profile: "wcag-2.2-aa",
        },
      };

      const validate = ajv.compile(schema);
      const valid = validate(invalidRequest);

      assert.strictEqual(valid, false, "Should reject request without bundle_id");
    });

    it("should reject diagnose request without artifacts", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.diagnose.request.schema.v0.1.json"));

      const invalidRequest = {
        mcp: {
          envelope: "mcp.envelope_v0_1",
          request_id: "req_test",
          tool: "a11y.diagnose",
          client: { name: "test", version: "1.0.0" },
        },
        input: {
          bundle_id: "bundle:test:12345678",
          profile: "wcag-2.2-aa",
        },
      };

      const validate = ajv.compile(schema);
      const valid = validate(invalidRequest);

      assert.strictEqual(valid, false, "Should reject request without artifacts");
    });

    it("should reject diagnose request without profile", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.diagnose.request.schema.v0.1.json"));

      const invalidRequest = {
        mcp: {
          envelope: "mcp.envelope_v0_1",
          request_id: "req_test",
          tool: "a11y.diagnose",
          client: { name: "test", version: "1.0.0" },
        },
        input: {
          bundle_id: "bundle:test:12345678",
          artifacts: ["artifact:dom:index"],
        },
      };

      const validate = ajv.compile(schema);
      const valid = validate(invalidRequest);

      assert.strictEqual(valid, false, "Should reject request without profile");
    });
  });

  describe("Response fixtures", () => {
    it("should validate evidence success response fixture", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.evidence.response.schema.v0.1.json"));
      const fixture = loadJson(path.join(FIXTURES_DIR, "responses/a11y.evidence.ok.json"));

      const validate = ajv.compile(schema);
      const valid = validate(fixture);

      if (!valid) {
        console.error("Validation errors:", JSON.stringify(validate.errors, null, 2));
      }

      assert.strictEqual(valid, true, `Evidence response should be valid: ${JSON.stringify(validate.errors)}`);
    });

    it("should validate diagnose success response fixture", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.diagnose.response.schema.v0.1.json"));
      const fixture = loadJson(path.join(FIXTURES_DIR, "responses/a11y.diagnose.ok.json"));

      const validate = ajv.compile(schema);
      const valid = validate(fixture);

      if (!valid) {
        console.error("Validation errors:", JSON.stringify(validate.errors, null, 2));
      }

      assert.strictEqual(valid, true, `Diagnose response should be valid: ${JSON.stringify(validate.errors)}`);
    });

    it("should validate diagnose provenance failure response fixture", () => {
      const ajv = createValidator();
      const schema = loadSchema(path.join(TOOLS_SCHEMAS_DIR, "a11y.diagnose.response.schema.v0.1.json"));
      const fixture = loadJson(path.join(FIXTURES_DIR, "responses/a11y.diagnose.provenance_fail.json"));

      const validate = ajv.compile(schema);
      const valid = validate(fixture);

      if (!valid) {
        console.error("Validation errors:", JSON.stringify(validate.errors, null, 2));
      }

      assert.strictEqual(valid, true, `Provenance failure response should be valid: ${JSON.stringify(validate.errors)}`);
    });
  });

  describe("Envelope structure", () => {
    it("should have consistent envelope structure across all fixtures", () => {
      const evidenceReq = loadJson(path.join(FIXTURES_DIR, "requests/a11y.evidence.ok.json"));
      const evidenceRes = loadJson(path.join(FIXTURES_DIR, "responses/a11y.evidence.ok.json"));
      const diagnoseReq = loadJson(path.join(FIXTURES_DIR, "requests/a11y.diagnose.ok.json"));
      const diagnoseRes = loadJson(path.join(FIXTURES_DIR, "responses/a11y.diagnose.ok.json"));
      const diagnoseErr = loadJson(path.join(FIXTURES_DIR, "responses/a11y.diagnose.provenance_fail.json"));

      // All should have envelope version
      assert.strictEqual(evidenceReq.mcp.envelope, "mcp.envelope_v0_1");
      assert.strictEqual(evidenceRes.mcp.envelope, "mcp.envelope_v0_1");
      assert.strictEqual(diagnoseReq.mcp.envelope, "mcp.envelope_v0_1");
      assert.strictEqual(diagnoseRes.mcp.envelope, "mcp.envelope_v0_1");
      assert.strictEqual(diagnoseErr.mcp.envelope, "mcp.envelope_v0_1");

      // Responses should have ok field
      assert.strictEqual(evidenceRes.mcp.ok, true);
      assert.strictEqual(diagnoseRes.mcp.ok, true);
      assert.strictEqual(diagnoseErr.mcp.ok, false);

      // Success responses should have result, error responses should have error
      assert.ok(evidenceRes.result);
      assert.ok(diagnoseRes.result);
      assert.ok(diagnoseErr.error);
    });
  });
});
