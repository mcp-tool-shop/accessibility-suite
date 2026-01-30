"use strict";

/**
 * a11y.diagnose MCP tool
 *
 * Run deterministic accessibility checks over evidence bundles.
 * Emits:
 * - Structured findings
 * - Fix guidance (SAFE-only intent patches)
 * - Evidence pointers (JSON Pointer / selector / line spans)
 */

const {
  createEvidenceAnchor,
  nodePointer,
  createProvenanceRecord,
  DIAGNOSE_METHODS,
} = require("../schemas/index.js");

/**
 * WCAG rules registry.
 * Each rule has: id, severity, check function, fix generator.
 */
const RULES = {
  lang: {
    id: "a11y.lang.missing",
    wcag: "wcag.3.1.1",
    severity: "high",
    message: "Document is missing a lang attribute on <html>.",
    check: checkLangMissing,
    fix: fixLangMissing,
  },
  alt: {
    id: "a11y.img.missing_alt",
    wcag: "wcag.1.1.1",
    severity: "high",
    message: "Image element is missing alt text.",
    check: checkImgMissingAlt,
    fix: fixImgMissingAlt,
  },
  "button-name": {
    id: "a11y.button.missing_name",
    wcag: "wcag.4.1.2",
    severity: "high",
    message: "Button element is missing an accessible name.",
    check: checkButtonMissingName,
    fix: fixButtonMissingName,
  },
  "link-name": {
    id: "a11y.link.missing_name",
    wcag: "wcag.4.1.2",
    severity: "high",
    message: "Link element is missing an accessible name.",
    check: checkLinkMissingName,
    fix: fixLinkMissingName,
  },
  label: {
    id: "a11y.input.missing_label",
    wcag: "wcag.1.3.1",
    severity: "high",
    message: "Form control is missing an associated label.",
    check: checkInputMissingLabel,
    fix: fixInputMissingLabel,
  },
};

/**
 * Execute the a11y.diagnose tool.
 *
 * @param {Object} input - Tool input
 * @param {Object} bundleStore - In-memory bundle store (for demo)
 * @returns {Object} Tool response
 */
async function execute(input, bundleStore = {}) {
  try {
    const result = await diagnose(input, bundleStore);
    return { ok: true, diagnosis: result };
  } catch (err) {
    return {
      ok: false,
      error: {
        code: "DIAGNOSIS_FAILED",
        message: err.message,
      },
    };
  }
}

/**
 * Run diagnosis on evidence bundle.
 */
async function diagnose(input, bundleStore) {
  const {
    bundle_id,
    bundle, // Allow passing bundle directly for testing
    artifacts: artifactIds,
    profile = "wcag-2.2-aa",
    rules: ruleConfig = {},
    output: outputConfig = {},
    integrity = {},
  } = input;

  // Get bundle (from store or direct)
  const evidenceBundle = bundle || bundleStore[bundle_id];
  if (!evidenceBundle) {
    throw new Error(`Bundle not found: ${bundle_id}`);
  }

  // Verify provenance if requested
  let provenanceVerified = false;
  if (integrity.verify_provenance) {
    provenanceVerified = verifyBundleProvenance(evidenceBundle);
  }

  // Determine which rules to run
  const include = ruleConfig.include || Object.keys(RULES);
  const exclude = new Set(ruleConfig.exclude || []);
  const activeRules = include.filter((r) => !exclude.has(r) && RULES[r]);

  // Get artifacts to analyze
  const targetArtifacts = artifactIds
    ? evidenceBundle.artifacts.filter((a) => artifactIds.includes(a.artifact_id))
    : evidenceBundle.artifacts.filter((a) => a.labels.includes("dom-snapshot"));

  // Run rules and collect findings
  const findings = [];
  const methods = [DIAGNOSE_METHODS.WCAG_RULES];

  for (const artifact of targetArtifacts) {
    // Parse DOM snapshot if needed
    const domData = parseDomArtifact(artifact, evidenceBundle);
    if (!domData) continue;

    for (const ruleName of activeRules) {
      const rule = RULES[ruleName];
      const ruleFindings = rule.check(domData, artifact.artifact_id);

      for (const finding of ruleFindings) {
        const fullFinding = {
          id: rule.id,
          severity: rule.severity,
          message: rule.message,
          rule: rule.wcag,
          targets: [finding.target],
        };

        // Add fix guidance if requested
        if (outputConfig.include_fix_guidance) {
          const fix = rule.fix(finding, domData);
          if (fix) {
            fullFinding.fix = fix;
          }
        }

        findings.push(fullFinding);
      }
    }
  }

  methods.push(DIAGNOSE_METHODS.EXTRACT_POINTER);
  if (outputConfig.include_fix_guidance) {
    methods.push(DIAGNOSE_METHODS.GENERATE_FIX);
  }

  // Build summary
  const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
  for (const f of findings) {
    severityCounts[f.severity] = (severityCounts[f.severity] || 0) + 1;
  }

  // Build provenance
  const provenance = createProvenanceRecord({
    methods,
    inputs: [bundle_id || "inline-bundle", ...targetArtifacts.map((a) => a.artifact_id)],
    outputs: findings.map((f, i) => `finding:${i}`),
  });
  provenance.verified = provenanceVerified;

  return {
    summary: {
      profile,
      targets: targetArtifacts.length,
      findings_total: findings.length,
      severity_counts: severityCounts,
    },
    findings,
    provenance,
  };
}

/**
 * Parse a DOM artifact to extract nodes.
 */
function parseDomArtifact(artifact, bundle) {
  if (!artifact.labels.includes("dom-snapshot")) {
    return null;
  }

  // For DOM snapshots, we need the actual content
  // In a real implementation, this would read from storage
  // For now, we assume the artifact has embedded content or we find it in bundle
  try {
    // Try to find the DOM content (would normally be stored separately)
    // This is a simplified version for the MCP tool
    if (artifact._content) {
      return JSON.parse(artifact._content);
    }

    // Return a minimal structure for testing
    return { nodes: [], root: null };
  } catch {
    return null;
  }
}

/**
 * Verify bundle provenance (simplified).
 */
function verifyBundleProvenance(bundle) {
  // Check that provenance record exists and has required fields
  if (!bundle.provenance) return false;
  if (!bundle.provenance.methods || bundle.provenance.methods.length === 0)
    return false;
  if (!bundle.provenance.inputs || bundle.provenance.inputs.length === 0)
    return false;

  // In a full implementation, would verify digests
  return true;
}

// ============================================================================
// RULE IMPLEMENTATIONS
// ============================================================================

function checkLangMissing(domData, artifactId) {
  const findings = [];
  const { nodes } = domData;

  for (const node of nodes) {
    if (node.type !== "element" || node.tagName !== "html") continue;

    const lang = node.attrs?.lang;
    if (!lang || lang.trim() === "") {
      findings.push({
        target: createEvidenceAnchor({
          artifactId,
          jsonPointer: nodePointer(node.index),
          selector: "html",
          snippet: buildSnippet(node),
        }),
        node,
      });
    }
  }

  return findings;
}

function fixLangMissing(finding, domData) {
  return {
    safe: true,
    action: "add_attribute",
    path_hint: getPathHint(finding.target.artifact_id),
    patch: {
      op: "add",
      selector: "html",
      attribute: "lang",
      value: "en",
    },
  };
}

function checkImgMissingAlt(domData, artifactId) {
  const findings = [];
  const { nodes } = domData;

  for (const node of nodes) {
    if (node.type !== "element" || node.tagName !== "img") continue;

    // Skip decorative images
    if (node.attrs?.role === "presentation" || node.attrs?.role === "none") continue;
    if (node.attrs?.["aria-hidden"] === "true") continue;

    const alt = node.attrs?.alt;
    if (alt === undefined) {
      findings.push({
        target: createEvidenceAnchor({
          artifactId,
          jsonPointer: nodePointer(node.index),
          selector: node.selector || "img",
          snippet: buildSnippet(node),
        }),
        node,
      });
    }
  }

  return findings;
}

function fixImgMissingAlt(finding, domData) {
  return {
    safe: true,
    action: "add_attribute",
    path_hint: getPathHint(finding.target.artifact_id),
    patch: {
      op: "add",
      selector: finding.target.selector,
      attribute: "alt",
      value: "", // Empty string for decorative, or "[describe image]" for content
    },
    note: 'Add meaningful alt text, or alt="" for decorative images.',
  };
}

function checkButtonMissingName(domData, artifactId) {
  const findings = [];
  const { nodes } = domData;

  for (const node of nodes) {
    if (node.type !== "element" || node.tagName !== "button") continue;

    if (!hasAccessibleName(node, nodes)) {
      findings.push({
        target: createEvidenceAnchor({
          artifactId,
          jsonPointer: nodePointer(node.index),
          selector: node.selector || "button",
          snippet: buildSnippet(node),
        }),
        node,
      });
    }
  }

  return findings;
}

function fixButtonMissingName(finding, domData) {
  return {
    safe: true,
    action: "add_content_or_attribute",
    path_hint: getPathHint(finding.target.artifact_id),
    patch: {
      op: "add",
      selector: finding.target.selector,
      attribute: "aria-label",
      value: "[button purpose]",
    },
    note: "Add text content or aria-label describing the button's action.",
  };
}

function checkLinkMissingName(domData, artifactId) {
  const findings = [];
  const { nodes } = domData;

  for (const node of nodes) {
    if (node.type !== "element" || node.tagName !== "a") continue;
    if (node.attrs?.href === undefined) continue; // Not a real link

    if (!hasAccessibleName(node, nodes)) {
      findings.push({
        target: createEvidenceAnchor({
          artifactId,
          jsonPointer: nodePointer(node.index),
          selector: node.selector || "a",
          snippet: buildSnippet(node),
        }),
        node,
      });
    }
  }

  return findings;
}

function fixLinkMissingName(finding, domData) {
  return {
    safe: true,
    action: "add_content_or_attribute",
    path_hint: getPathHint(finding.target.artifact_id),
    patch: {
      op: "add",
      selector: finding.target.selector,
      attribute: "aria-label",
      value: "[link destination]",
    },
    note: "Add text content or aria-label describing where the link goes.",
  };
}

function checkInputMissingLabel(domData, artifactId) {
  const findings = [];
  const { nodes } = domData;

  const formControls = ["input", "select", "textarea"];
  const exemptTypes = ["hidden", "submit", "reset", "button", "image"];

  // Build set of IDs that have labels
  const labeledIds = new Set();
  for (const node of nodes) {
    if (node.type === "element" && node.tagName === "label" && node.attrs?.for) {
      labeledIds.add(node.attrs.for);
    }
  }

  for (const node of nodes) {
    if (node.type !== "element" || !formControls.includes(node.tagName)) continue;

    // Skip exempt input types
    if (node.tagName === "input") {
      const type = (node.attrs?.type || "text").toLowerCase();
      if (exemptTypes.includes(type)) continue;
    }

    // Check for label
    const hasLabel =
      (node.attrs?.id && labeledIds.has(node.attrs.id)) ||
      node.attrs?.["aria-label"] ||
      node.attrs?.["aria-labelledby"];

    if (!hasLabel) {
      findings.push({
        target: createEvidenceAnchor({
          artifactId,
          jsonPointer: nodePointer(node.index),
          selector: node.selector || node.tagName,
          snippet: buildSnippet(node),
        }),
        node,
      });
    }
  }

  return findings;
}

function fixInputMissingLabel(finding, domData) {
  const node = finding.node;
  const inputId = node.attrs?.id;

  if (inputId) {
    return {
      safe: true,
      action: "add_element",
      path_hint: getPathHint(finding.target.artifact_id),
      patch: {
        op: "insert_before",
        selector: finding.target.selector,
        element: "label",
        attributes: { for: inputId },
        content: "[field label]",
      },
      note: `Add <label for="${inputId}">...</label> before the input.`,
    };
  }

  return {
    safe: true,
    action: "add_attribute",
    path_hint: getPathHint(finding.target.artifact_id),
    patch: {
      op: "add",
      selector: finding.target.selector,
      attribute: "aria-label",
      value: "[field purpose]",
    },
    note: "Add aria-label or associate with a <label> element.",
  };
}

// ============================================================================
// HELPERS
// ============================================================================

function hasAccessibleName(node, nodes) {
  // Check aria-label
  if (node.attrs?.["aria-label"]?.trim()) return true;

  // Check aria-labelledby
  if (node.attrs?.["aria-labelledby"]) {
    const ids = node.attrs["aria-labelledby"].split(/\s+/);
    for (const id of ids) {
      if (nodes.some((n) => n.attrs?.id === id)) return true;
    }
  }

  // Check text content
  const text = getTextContent(node, nodes);
  if (text.trim()) return true;

  // Check title
  if (node.attrs?.title?.trim()) return true;

  return false;
}

function getTextContent(node, nodes) {
  if (!node.children) return "";

  let text = "";
  for (const child of node.children) {
    if (child.type === "text") {
      text += child.content || "";
    } else if (child.type === "element") {
      text += getTextContent(child, nodes);
    }
  }
  return text;
}

function buildSnippet(node) {
  const attrs = Object.entries(node.attrs || {})
    .map(([k, v]) => (v === "" ? k : `${k}="${v}"`))
    .join(" ");

  const attrStr = attrs ? ` ${attrs}` : "";
  return `<${node.tagName}${attrStr}>...</${node.tagName}>`;
}

function getPathHint(artifactId) {
  // Extract path from artifact ID
  // e.g., "artifact:dom:index" -> "html/index.html"
  const match = artifactId.match(/artifact:(?:dom|html):(.+)/);
  if (match) {
    return `html/${match[1]}.html`;
  }
  return "unknown";
}

/**
 * Tool definition for MCP registration.
 */
const toolDefinition = {
  name: "a11y.diagnose",
  description:
    "Run deterministic accessibility checks over evidence bundles. Emits structured findings with fix guidance and evidence pointers.",
  inputSchema: {
    type: "object",
    properties: {
      bundle_id: {
        type: "string",
        description: "ID of evidence bundle to diagnose",
      },
      bundle: {
        type: "object",
        description: "Evidence bundle (alternative to bundle_id)",
      },
      artifacts: {
        type: "array",
        description: "Specific artifact IDs to analyze (default: all DOM snapshots)",
        items: { type: "string" },
      },
      profile: {
        type: "string",
        description: "WCAG profile to check against",
        enum: ["wcag-2.0-a", "wcag-2.0-aa", "wcag-2.1-aa", "wcag-2.2-aa"],
        default: "wcag-2.2-aa",
      },
      rules: {
        type: "object",
        properties: {
          include: {
            type: "array",
            items: { type: "string" },
          },
          exclude: {
            type: "array",
            items: { type: "string" },
          },
        },
      },
      output: {
        type: "object",
        properties: {
          format: { type: "string", enum: ["json"] },
          include_fix_guidance: { type: "boolean" },
          include_evidence: { type: "boolean" },
        },
      },
      integrity: {
        type: "object",
        properties: {
          verify_provenance: { type: "boolean" },
        },
      },
    },
  },
};

module.exports = {
  execute,
  toolDefinition,
  diagnose,
  RULES,
};
