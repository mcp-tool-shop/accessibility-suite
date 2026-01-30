"use strict";

const crypto = require("crypto");
const { canonicalize } = require("./canonicalize.js");

/**
 * Generate prov-spec provenance records for a finding.
 *
 * Emits three records:
 * 1. record.json - engine.extract.evidence.json_pointer
 * 2. digest.json - integrity.digest.sha256
 * 3. envelope.json - adapter.wrap.envelope_v0_1
 *
 * @param {Object} finding - Finding with evidence
 * @param {Object} options - { engineVersion }
 * @returns {{ record: Object, digest: Object, envelope: Object }}
 */
function emitProvenance(finding, options = {}) {
  const engineVersion = options.engineVersion || "0.1.0";
  const timestamp = options.timestamp || new Date().toISOString();

  // 1. Evidence extraction record
  const record = {
    "prov.record.v0.1": {
      method_id: "engine.extract.evidence.json_pointer",
      timestamp,
      inputs: [
        {
          "artifact.v0.1": {
            name: "source_document",
            uri: `file://${finding.location.file}`,
          },
        },
      ],
      outputs: [
        {
          "artifact.v0.1": {
            name: "evidence",
            content: {
              document_ref: finding.location.file,
              pointer: finding.location.json_pointer,
              evidence: finding.evidence,
            },
          },
        },
      ],
      agent: {
        name: "a11y-evidence-engine",
        version: engineVersion,
      },
    },
  };

  // 2. Integrity digest of canonical evidence
  const evidenceContent = record["prov.record.v0.1"].outputs[0]["artifact.v0.1"].content;
  const canonicalEvidence = canonicalize(evidenceContent);
  const evidenceDigest = crypto
    .createHash("sha256")
    .update(canonicalEvidence, "utf8")
    .digest("hex");

  const digest = {
    "prov.record.v0.1": {
      method_id: "integrity.digest.sha256",
      timestamp,
      inputs: [
        {
          "artifact.v0.1": {
            name: "evidence",
            content: evidenceContent,
          },
        },
      ],
      outputs: [
        {
          "artifact.v0.1": {
            name: "digest",
            digest: {
              algorithm: "sha256",
              value: evidenceDigest,
            },
          },
        },
      ],
      agent: {
        name: "a11y-evidence-engine",
        version: engineVersion,
      },
    },
  };

  // 3. Envelope wrapping the evidence record
  const envelope = {
    "mcp.envelope.v0.1": {
      result: {
        finding_id: finding.finding_id,
        rule_id: finding.rule_id,
        severity: finding.severity,
        message: finding.message,
        location: finding.location,
      },
      provenance: {
        "prov.record.v0.1": {
          method_id: "adapter.wrap.envelope_v0_1",
          timestamp,
          inputs: [
            {
              "artifact.v0.1": {
                name: "evidence_record",
                digest: {
                  algorithm: "sha256",
                  value: evidenceDigest,
                },
              },
            },
          ],
          outputs: [
            {
              "artifact.v0.1": {
                name: "envelope",
                content_type: "mcp.envelope.v0.1",
              },
            },
          ],
          agent: {
            name: "a11y-evidence-engine",
            version: engineVersion,
          },
        },
      },
    },
  };

  return { record, digest, envelope };
}

/**
 * Verify a digest matches the canonical evidence.
 *
 * @param {Object} evidence - Evidence object
 * @param {string} expectedDigest - Expected SHA-256 hex digest
 * @returns {boolean}
 */
function verifyDigest(evidence, expectedDigest) {
  const canonical = canonicalize(evidence);
  const actualDigest = crypto
    .createHash("sha256")
    .update(canonical, "utf8")
    .digest("hex");
  return actualDigest === expectedDigest;
}

module.exports = { emitProvenance, verifyDigest, canonicalize };
