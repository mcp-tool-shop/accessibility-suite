import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const ROOT = process.cwd();

function readJson(relPath) {
  const p = path.join(ROOT, relPath);
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

/**
 * Loads a schema and removes $schema to avoid meta-schema issues.
 */
function loadSchema(relPath) {
  const schema = readJson(relPath);
  delete schema.$schema;
  return schema;
}

/**
 * Creates an AJV instance with all schemas loaded.
 * Uses split request/response schemas for stricter validation.
 */
function makeAjv() {
  const ajv = new Ajv2020({ allErrors: true, strict: false, verbose: true });
  addFormats(ajv);

  // Core schemas - register with their $id URLs for proper $ref resolution
  const evidenceBundle = loadSchema("src/schemas/evidence.bundle.schema.v0.1.json");
  const diagnosis = loadSchema("src/schemas/diagnosis.schema.v0.1.json");

  ajv.addSchema(evidenceBundle, "https://mcp-tool-shop.github.io/schemas/evidence.bundle.v0.1.json");
  ajv.addSchema(diagnosis, "https://mcp-tool-shop.github.io/schemas/diagnosis.v0.1.json");

  // Split request schemas
  const reqEvidence = loadSchema("src/schemas/tools/a11y.evidence.request.schema.v0.1.json");
  const reqDiagnose = loadSchema("src/schemas/tools/a11y.diagnose.request.schema.v0.1.json");

  ajv.addSchema(reqEvidence, "tools/a11y.evidence.request.schema.v0.1.json");
  ajv.addSchema(reqDiagnose, "tools/a11y.diagnose.request.schema.v0.1.json");

  // Split response schemas
  const respEvidence = loadSchema("src/schemas/tools/a11y.evidence.response.schema.v0.1.json");
  const respDiagnose = loadSchema("src/schemas/tools/a11y.diagnose.response.schema.v0.1.json");

  ajv.addSchema(respEvidence, "tools/a11y.evidence.response.schema.v0.1.json");
  ajv.addSchema(respDiagnose, "tools/a11y.diagnose.response.schema.v0.1.json");

  return ajv;
}

function validateOrThrow(ajv, schemaKey, data, label) {
  const validate = ajv.getSchema(schemaKey);
  assert.ok(validate, `Missing schema: ${schemaKey}`);
  const ok = validate(data);
  if (!ok) {
    const msg = JSON.stringify(validate.errors, null, 2);
    throw new Error(`${label} failed schema validation:\n${msg}`);
  }
}

// Request fixture tests (use request schemas)
test("a11y.evidence request fixture validates against request schema", () => {
  const ajv = makeAjv();
  const req = readJson("fixtures/requests/a11y.evidence.ok.json");
  validateOrThrow(ajv, "tools/a11y.evidence.request.schema.v0.1.json", req, "a11y.evidence request");
});

test("a11y.diagnose request fixture validates against request schema", () => {
  const ajv = makeAjv();
  const req = readJson("fixtures/requests/a11y.diagnose.ok.json");
  validateOrThrow(ajv, "tools/a11y.diagnose.request.schema.v0.1.json", req, "a11y.diagnose request");
});

// Response fixture tests (use response schemas)
test("a11y.evidence response fixture validates against response schema", () => {
  const ajv = makeAjv();
  const res = readJson("fixtures/responses/a11y.evidence.ok.json");
  validateOrThrow(ajv, "tools/a11y.evidence.response.schema.v0.1.json", res, "a11y.evidence response");
});

test("a11y.diagnose response fixture validates against response schema", () => {
  const ajv = makeAjv();
  const res = readJson("fixtures/responses/a11y.diagnose.ok.json");
  validateOrThrow(ajv, "tools/a11y.diagnose.response.schema.v0.1.json", res, "a11y.diagnose response");
});

// Error envelope tests
test("a11y.diagnose provenance-fail error envelope validates against response schema", () => {
  const ajv = makeAjv();
  const err = readJson("fixtures/responses/a11y.diagnose.provenance_fail.json");

  // Validate envelope structure
  assert.equal(err.mcp.envelope, "mcp.envelope_v0_1");
  assert.equal(err.mcp.tool, "a11y.diagnose");
  assert.equal(err.mcp.ok, false);

  // Validate error shape
  assert.ok(err.error?.code, "Error must have code");
  assert.ok(err.error?.message, "Error must have message");
  assert.ok(err.error?.fix, "Error must have fix guidance");

  // Validate against response schema (should match ok=false branch)
  validateOrThrow(ajv, "tools/a11y.diagnose.response.schema.v0.1.json", err, "a11y.diagnose error response");
});

// Negative tests: request should NOT validate against response schema (and vice versa)
test("a11y.evidence request should NOT validate against response schema", () => {
  const ajv = makeAjv();
  const req = readJson("fixtures/requests/a11y.evidence.ok.json");
  const validate = ajv.getSchema("tools/a11y.evidence.response.schema.v0.1.json");
  assert.ok(validate, "Missing schema");
  const ok = validate(req);
  assert.equal(ok, false, "Request should NOT validate against response schema");
});

test("a11y.evidence response should NOT validate against request schema", () => {
  const ajv = makeAjv();
  const res = readJson("fixtures/responses/a11y.evidence.ok.json");
  const validate = ajv.getSchema("tools/a11y.evidence.request.schema.v0.1.json");
  assert.ok(validate, "Missing schema");
  const ok = validate(res);
  assert.equal(ok, false, "Response should NOT validate against request schema");
});

// Cross-fixture consistency tests
test("Request and response fixtures have matching request_ids", () => {
  const evidenceReq = readJson("fixtures/requests/a11y.evidence.ok.json");
  const evidenceRes = readJson("fixtures/responses/a11y.evidence.ok.json");
  const diagnoseReq = readJson("fixtures/requests/a11y.diagnose.ok.json");
  const diagnoseRes = readJson("fixtures/responses/a11y.diagnose.ok.json");

  assert.equal(evidenceReq.mcp.request_id, evidenceRes.mcp.request_id, "Evidence request_id mismatch");
  assert.equal(diagnoseReq.mcp.request_id, diagnoseRes.mcp.request_id, "Diagnose request_id mismatch");
});

test("All fixtures use consistent envelope version", () => {
  const fixtures = [
    "fixtures/requests/a11y.evidence.ok.json",
    "fixtures/requests/a11y.diagnose.ok.json",
    "fixtures/responses/a11y.evidence.ok.json",
    "fixtures/responses/a11y.diagnose.ok.json",
    "fixtures/responses/a11y.diagnose.provenance_fail.json",
  ];

  for (const f of fixtures) {
    const data = readJson(f);
    assert.equal(data.mcp.envelope, "mcp.envelope_v0_1", `${f} has wrong envelope version`);
  }
});
