"use strict";

const { findElements } = require("../html_parse.js");

const RULE_ID = "html.img.missing_alt";

/**
 * Check for <img> elements missing alt attribute.
 * WCAG 1.1.1 - Non-text Content (Level A)
 *
 * Exceptions:
 * - role="presentation" or role="none"
 * - aria-hidden="true"
 */
function run(nodes, context) {
  const findings = [];

  const imgElements = findElements(nodes, (n) => n.tagName === "img");

  for (const node of imgElements) {
    // Skip decorative images
    if (isDecorativeImage(node)) {
      continue;
    }

    const alt = node.attrs.alt;

    // Missing alt attribute entirely
    if (alt === undefined) {
      findings.push({
        rule_id: RULE_ID,
        severity: "error",
        confidence: 0.98,
        message: "Image element is missing alt text.",
        location: {
          file: context.relativePath,
          json_pointer: `/nodes/${node.index}`,
        },
        evidence: {
          tagName: node.tagName,
          attrs: filterAttrs(node.attrs, ["src", "alt", "role", "aria-hidden"]),
        },
      });
    }
  }

  return findings;
}

/**
 * Check if image is marked as decorative.
 */
function isDecorativeImage(node) {
  const role = node.attrs.role;
  if (role === "presentation" || role === "none") {
    return true;
  }

  const ariaHidden = node.attrs["aria-hidden"];
  if (ariaHidden === "true") {
    return true;
  }

  return false;
}

function filterAttrs(attrs, keys) {
  const filtered = {};
  for (const key of keys) {
    if (key in attrs) {
      filtered[key] = attrs[key];
    }
  }
  return filtered;
}

module.exports = { id: RULE_ID, run };
