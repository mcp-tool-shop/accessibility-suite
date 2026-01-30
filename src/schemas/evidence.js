"use strict";

/**
 * Evidence anchor schema and utilities.
 *
 * An evidence anchor points to a specific location within an artifact:
 * - JSON Pointer for structured data
 * - CSS selector for DOM elements
 * - Line span for source files
 * - Snippet for context
 */

/**
 * Create an evidence anchor.
 *
 * @param {Object} params
 * @param {string} params.artifactId - Reference to artifact
 * @param {string} [params.jsonPointer] - JSON Pointer (RFC 6901)
 * @param {string} [params.selector] - CSS selector
 * @param {Object} [params.lineSpan] - { start, end }
 * @param {string} [params.snippet] - Context snippet
 * @returns {Object} Evidence anchor
 */
function createEvidenceAnchor({
  artifactId,
  jsonPointer,
  selector,
  lineSpan,
  snippet,
}) {
  const anchor = {
    artifact_id: artifactId,
  };

  if (jsonPointer) anchor.json_pointer = jsonPointer;
  if (selector) anchor.selector = selector;
  if (lineSpan) anchor.line_span = lineSpan;
  if (snippet) anchor.snippet = snippet;

  return anchor;
}

/**
 * Create a JSON Pointer from a node index.
 *
 * @param {number} index - Node index in flat array
 * @returns {string} JSON Pointer
 */
function nodePointer(index) {
  return `/nodes/${index}`;
}

/**
 * Create a JSON Pointer for a DOM path.
 *
 * @param {string[]} path - Array of element names/indices
 * @returns {string} JSON Pointer
 */
function domPointer(path) {
  return "/dom/" + path.map(escapePointerSegment).join("/");
}

/**
 * Escape a JSON Pointer segment.
 */
function escapePointerSegment(str) {
  return String(str).replace(/~/g, "~0").replace(/\//g, "~1");
}

/**
 * Extract a snippet from content around a position.
 *
 * @param {string} content - Full content
 * @param {number} start - Start position
 * @param {number} [maxLength=100] - Maximum snippet length
 * @returns {string} Snippet
 */
function extractSnippet(content, start, maxLength = 100) {
  const halfLen = Math.floor(maxLength / 2);
  const snippetStart = Math.max(0, start - halfLen);
  const snippetEnd = Math.min(content.length, start + halfLen);

  let snippet = content.slice(snippetStart, snippetEnd);

  if (snippetStart > 0) snippet = "..." + snippet;
  if (snippetEnd < content.length) snippet = snippet + "...";

  return snippet;
}

module.exports = {
  createEvidenceAnchor,
  nodePointer,
  domPointer,
  escapePointerSegment,
  extractSnippet,
};
