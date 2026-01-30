"use strict";

/**
 * Artifact schema and utilities.
 *
 * An artifact is a captured piece of content with:
 * - Unique ID
 * - Media type
 * - Locator (where it came from)
 * - Size and digest
 * - Labels for categorization
 */

const crypto = require("crypto");

/**
 * Create an artifact object.
 *
 * @param {Object} params
 * @param {string} params.id - Artifact ID (e.g., "artifact:html:index")
 * @param {string} params.mediaType - MIME type
 * @param {Object} params.locator - { kind: "file"|"derived"|"url", path|from|url }
 * @param {Buffer|string} params.content - Raw content for hashing
 * @param {string[]} [params.labels] - Optional labels
 * @returns {Object} Artifact object
 */
function createArtifact({ id, mediaType, locator, content, labels = [] }) {
  const contentBuffer = Buffer.isBuffer(content)
    ? content
    : Buffer.from(content, "utf8");

  const digest = crypto
    .createHash("sha256")
    .update(contentBuffer)
    .digest("hex");

  return {
    artifact_id: id,
    media_type: mediaType,
    locator,
    size_bytes: contentBuffer.length,
    digest: {
      alg: "sha256",
      hex: digest,
    },
    labels,
  };
}

/**
 * Generate an artifact ID from kind and name.
 *
 * @param {string} kind - e.g., "html", "dom", "log"
 * @param {string} name - e.g., "index", "contact"
 * @returns {string} Artifact ID
 */
function artifactId(kind, name) {
  return `artifact:${kind}:${name}`;
}

/**
 * Verify an artifact's digest.
 *
 * @param {Object} artifact - Artifact object
 * @param {Buffer|string} content - Content to verify
 * @returns {boolean}
 */
function verifyArtifact(artifact, content) {
  const contentBuffer = Buffer.isBuffer(content)
    ? content
    : Buffer.from(content, "utf8");

  const computed = crypto
    .createHash("sha256")
    .update(contentBuffer)
    .digest("hex");

  return computed === artifact.digest.hex;
}

module.exports = {
  createArtifact,
  artifactId,
  verifyArtifact,
};
