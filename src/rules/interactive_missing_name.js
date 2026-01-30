"use strict";

const { findElements, getTextContent, getElementById } = require("../html_parse.js");

const RULE_ID = "html.interactive.missing_name";

/**
 * Check for interactive elements missing accessible names.
 * WCAG 4.1.2 - Name, Role, Value (Level A)
 *
 * Checks:
 * - <button> elements
 * - <a href="..."> elements (links)
 *
 * An accessible name can come from:
 * - Text content
 * - aria-label
 * - aria-labelledby
 * - title attribute (fallback)
 */
function run(nodes, context) {
  const findings = [];

  // Check buttons
  const buttons = findElements(nodes, (n) => n.tagName === "button");
  for (const node of buttons) {
    if (!hasAccessibleName(node, nodes)) {
      findings.push({
        rule_id: RULE_ID,
        severity: "error",
        confidence: 0.95,
        message: "Button element is missing an accessible name.",
        location: {
          file: context.relativePath,
          json_pointer: `/nodes/${node.index}`,
        },
        evidence: {
          tagName: node.tagName,
          attrs: filterAttrs(node.attrs, [
            "id",
            "type",
            "aria-label",
            "aria-labelledby",
            "title",
          ]),
          textContent: getTextContent(node).substring(0, 50),
        },
      });
    }
  }

  // Check links (anchors with href)
  const links = findElements(
    nodes,
    (n) => n.tagName === "a" && n.attrs.href !== undefined
  );
  for (const node of links) {
    if (!hasAccessibleName(node, nodes)) {
      findings.push({
        rule_id: RULE_ID,
        severity: "error",
        confidence: 0.95,
        message: "Link element is missing an accessible name.",
        location: {
          file: context.relativePath,
          json_pointer: `/nodes/${node.index}`,
        },
        evidence: {
          tagName: node.tagName,
          attrs: filterAttrs(node.attrs, [
            "href",
            "aria-label",
            "aria-labelledby",
            "title",
          ]),
          textContent: getTextContent(node).substring(0, 50),
        },
      });
    }
  }

  return findings;
}

/**
 * Check if an element has an accessible name.
 */
function hasAccessibleName(node, nodes) {
  // Check aria-label
  if (node.attrs["aria-label"] && node.attrs["aria-label"].trim()) {
    return true;
  }

  // Check aria-labelledby
  if (node.attrs["aria-labelledby"]) {
    const ids = node.attrs["aria-labelledby"].split(/\s+/);
    for (const id of ids) {
      const labelElement = getElementById(nodes, id);
      if (labelElement && getTextContent(labelElement).trim()) {
        return true;
      }
    }
  }

  // Check text content
  const textContent = getTextContent(node).trim();
  if (textContent) {
    return true;
  }

  // Check title as fallback
  if (node.attrs.title && node.attrs.title.trim()) {
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
