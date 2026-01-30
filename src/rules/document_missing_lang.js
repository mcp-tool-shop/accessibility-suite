"use strict";

const { findElements } = require("../html_parse.js");

const RULE_ID = "html.document.missing_lang";

/**
 * Check for <html> element missing lang attribute.
 * WCAG 3.1.1 - Language of Page (Level A)
 */
function run(nodes, context) {
  const findings = [];

  const htmlElements = findElements(nodes, (n) => n.tagName === "html");

  for (const node of htmlElements) {
    const lang = node.attrs.lang;

    if (!lang || lang.trim() === "") {
      findings.push({
        rule_id: RULE_ID,
        severity: "error",
        confidence: 1.0,
        message: "Document is missing a lang attribute on the <html> element.",
        location: {
          file: context.relativePath,
          json_pointer: `/nodes/${node.index}`,
        },
        evidence: {
          tagName: node.tagName,
          attrs: filterAttrs(node.attrs, ["lang"]),
        },
      });
    }
  }

  return findings;
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
