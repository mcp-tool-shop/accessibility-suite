"use strict";

/**
 * JSON Pointer utilities per RFC 6901.
 */

/**
 * Build a JSON pointer from nodes index.
 * @param {number} index - Node index
 * @returns {string} JSON pointer
 */
function nodePointer(index) {
  return `/nodes/${index}`;
}

/**
 * Escape a string for use in a JSON pointer segment.
 * @param {string} str - Raw string
 * @returns {string} Escaped string
 */
function escapePointer(str) {
  return str.replace(/~/g, "~0").replace(/\//g, "~1");
}

/**
 * Unescape a JSON pointer segment.
 * @param {string} str - Escaped string
 * @returns {string} Raw string
 */
function unescapePointer(str) {
  return str.replace(/~1/g, "/").replace(/~0/g, "~");
}

module.exports = { nodePointer, escapePointer, unescapePointer };
