"use strict";

const { Parser } = require("htmlparser2");

/**
 * Parse HTML and build a flat nodes[] array in document order.
 * Each node has a stable index for JSON pointer references.
 *
 * @param {string} html - Raw HTML content
 * @returns {{ nodes: Array, root: Object|null }}
 */
function parseHtml(html) {
  const nodes = [];
  const stack = [];
  let root = null;

  const parser = new Parser(
    {
      onopentag(name, attrs) {
        const node = {
          type: "element",
          tagName: name.toLowerCase(),
          attrs: { ...attrs },
          children: [],
          parent: stack.length > 0 ? stack[stack.length - 1] : null,
          index: nodes.length,
        };

        nodes.push(node);

        if (node.parent) {
          node.parent.children.push(node);
        } else {
          root = node;
        }

        stack.push(node);
      },

      ontext(text) {
        // Only capture non-whitespace text for accessibility analysis
        const trimmed = text.trim();
        if (trimmed && stack.length > 0) {
          const textNode = {
            type: "text",
            content: text,
            trimmed: trimmed,
            parent: stack[stack.length - 1],
            index: nodes.length,
          };
          nodes.push(textNode);
          stack[stack.length - 1].children.push(textNode);
        }
      },

      onclosetag() {
        stack.pop();
      },
    },
    {
      lowerCaseTags: true,
      lowerCaseAttributeNames: true,
      decodeEntities: true,
    }
  );

  parser.write(html);
  parser.end();

  return { nodes, root };
}

/**
 * Get the text content of an element (concatenated child text nodes).
 * @param {Object} node - Element node
 * @returns {string}
 */
function getTextContent(node) {
  if (!node || !node.children) return "";

  let text = "";
  for (const child of node.children) {
    if (child.type === "text") {
      text += child.content;
    } else if (child.type === "element") {
      text += getTextContent(child);
    }
  }
  return text.trim();
}

/**
 * Find all elements matching a predicate.
 * @param {Array} nodes - Flat nodes array
 * @param {Function} predicate - (node) => boolean
 * @returns {Array}
 */
function findElements(nodes, predicate) {
  return nodes.filter((n) => n.type === "element" && predicate(n));
}

/**
 * Find element by ID.
 * @param {Array} nodes - Flat nodes array
 * @param {string} id - Element ID
 * @returns {Object|null}
 */
function getElementById(nodes, id) {
  return nodes.find((n) => n.type === "element" && n.attrs.id === id) || null;
}

module.exports = {
  parseHtml,
  getTextContent,
  findElements,
  getElementById,
};
