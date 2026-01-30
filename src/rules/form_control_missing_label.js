"use strict";

const { findElements, getElementById } = require("../html_parse.js");

const RULE_ID = "html.form_control.missing_label";

const FORM_CONTROLS = ["input", "select", "textarea"];
const EXEMPT_INPUT_TYPES = ["hidden", "submit", "reset", "button", "image"];

/**
 * Check for form controls missing associated labels.
 * WCAG 1.3.1 - Info and Relationships (Level A)
 * WCAG 4.1.2 - Name, Role, Value (Level A)
 *
 * A form control needs one of:
 * - Associated <label for="...">
 * - aria-label attribute
 * - aria-labelledby attribute (pointing to existing element)
 */
function run(nodes, context) {
  const findings = [];

  // Find all label elements for lookup
  const labels = findElements(nodes, (n) => n.tagName === "label");
  const labelForIds = new Set(
    labels.map((l) => l.attrs.for).filter((f) => f)
  );

  // Check form controls
  const controls = findElements(nodes, (n) => FORM_CONTROLS.includes(n.tagName));

  for (const node of controls) {
    // Skip exempt input types
    if (node.tagName === "input") {
      const type = (node.attrs.type || "text").toLowerCase();
      if (EXEMPT_INPUT_TYPES.includes(type)) {
        continue;
      }
    }

    if (!hasAccessibleLabel(node, labelForIds, nodes)) {
      findings.push({
        rule_id: RULE_ID,
        severity: "error",
        confidence: 0.95,
        message: `Form control <${node.tagName}> is missing an associated label.`,
        location: {
          file: context.relativePath,
          json_pointer: `/nodes/${node.index}`,
        },
        evidence: {
          tagName: node.tagName,
          attrs: filterAttrs(node.attrs, [
            "id",
            "name",
            "type",
            "aria-label",
            "aria-labelledby",
          ]),
        },
      });
    }
  }

  return findings;
}

/**
 * Check if a form control has an accessible label.
 */
function hasAccessibleLabel(node, labelForIds, nodes) {
  // Check aria-label
  if (node.attrs["aria-label"] && node.attrs["aria-label"].trim()) {
    return true;
  }

  // Check aria-labelledby (must point to existing element)
  if (node.attrs["aria-labelledby"]) {
    const ids = node.attrs["aria-labelledby"].split(/\s+/);
    for (const id of ids) {
      if (getElementById(nodes, id)) {
        return true;
      }
    }
  }

  // Check for associated label via 'for' attribute
  if (node.attrs.id && labelForIds.has(node.attrs.id)) {
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
