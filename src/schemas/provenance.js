"use strict";

/**
 * Provenance record utilities.
 *
 * Creates prov-spec compatible records for evidence capture and diagnosis.
 */

const crypto = require("crypto");

/**
 * Create a provenance record for evidence capture.
 *
 * @param {Object} params
 * @param {string[]} params.methods - Method IDs applied
 * @param {string[]} params.inputs - Input paths/IDs
 * @param {string[]} params.outputs - Output artifact IDs
 * @param {string} [params.agentName] - Agent name
 * @param {string} [params.agentVersion] - Agent version
 * @returns {Object} Provenance record
 */
function createProvenanceRecord({
  methods,
  inputs,
  outputs,
  agentName = "a11y-mcp-tools",
  agentVersion = "0.1.0",
}) {
  const recordId = `prov:record:${crypto.randomUUID()}`;

  return {
    record_id: recordId,
    methods,
    inputs,
    outputs,
    verified: false,
    timestamp: new Date().toISOString(),
    agent: {
      name: agentName,
      version: agentVersion,
    },
  };
}

/**
 * Create a full prov.record.v0.1 structure.
 *
 * @param {Object} params
 * @param {string} params.methodId - Primary method ID
 * @param {Object[]} params.inputArtifacts - Input artifact refs
 * @param {Object[]} params.outputArtifacts - Output artifact refs
 * @param {string} [params.agentName]
 * @param {string} [params.agentVersion]
 * @returns {Object} prov.record.v0.1 structure
 */
function createProvRecordV01({
  methodId,
  inputArtifacts,
  outputArtifacts,
  agentName = "a11y-mcp-tools",
  agentVersion = "0.1.0",
}) {
  return {
    "prov.record.v0.1": {
      method_id: methodId,
      timestamp: new Date().toISOString(),
      inputs: inputArtifacts.map((a) => ({
        "artifact.v0.1": {
          name: a.name || a.artifact_id,
          uri: a.uri || `artifact://${a.artifact_id}`,
          digest: a.digest,
        },
      })),
      outputs: outputArtifacts.map((a) => ({
        "artifact.v0.1": {
          name: a.name || a.artifact_id,
          content: a.content,
          digest: a.digest,
        },
      })),
      agent: {
        name: agentName,
        version: agentVersion,
      },
    },
  };
}

/**
 * Locked Method ID Catalog (v0.1)
 *
 * These IDs are stable and MUST NOT change within a major version.
 * See: https://github.com/mcp-tool-shop/prov-spec
 */

/**
 * Method IDs for envelope/adapter operations.
 */
const ADAPTER_METHODS = {
  // Wrap request/response in MCP envelope
  WRAP_ENVELOPE: "adapter.wrap.envelope_v0_1",
};

/**
 * Method IDs for evidence capture.
 */
const EVIDENCE_METHODS = {
  // Capture raw HTML with canonicalization
  CAPTURE_HTML: "engine.capture.html_canonicalize_v0_1",
  // Extract DOM snapshot for analysis
  CAPTURE_DOM: "engine.capture.dom_snapshot_v0_1",
  // Generic file capture
  CAPTURE_FILE: "engine.capture.file_v0_1",
  // SHA-256 integrity verification
  INTEGRITY_SHA256: "adapter.integrity.sha256_v0_1",
  // Provenance record creation
  PROVENANCE_RECORD: "adapter.provenance.record_v0_1",
};

/**
 * Method IDs for diagnosis.
 */
const DIAGNOSE_METHODS = {
  // WCAG rule evaluation engine
  WCAG_RULES: "engine.diagnose.wcag_rules_v0_1",
  // JSON Pointer evidence extraction
  EXTRACT_POINTER: "engine.extract.evidence.json_pointer_v0_1",
  // CSS selector evidence extraction
  EXTRACT_SELECTOR: "engine.extract.evidence.selector_v0_1",
  // Fix guidance generation
  GENERATE_FIX: "engine.generate.fix_guidance_v0_1",
};

module.exports = {
  createProvenanceRecord,
  createProvRecordV01,
  ADAPTER_METHODS,
  EVIDENCE_METHODS,
  DIAGNOSE_METHODS,
};
