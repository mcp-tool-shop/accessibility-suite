"use strict";

/**
 * MCP Envelope utilities (v0.1).
 *
 * Wraps tool inputs/outputs in standard MCP envelopes with
 * request IDs, client info, and structured error responses.
 */

const crypto = require("crypto");

const ENVELOPE_VERSION = "mcp.envelope_v0_1";

/**
 * Generate a unique request ID.
 */
function generateRequestId() {
  const bytes = crypto.randomBytes(12);
  return `req_${bytes.toString("base64url")}`;
}

/**
 * Create a request envelope.
 *
 * @param {string} tool - Tool name
 * @param {Object} input - Tool input
 * @param {Object} [client] - Client info
 * @returns {Object} Request envelope
 */
function createRequestEnvelope(tool, input, client = null) {
  return {
    mcp: {
      envelope: ENVELOPE_VERSION,
      request_id: generateRequestId(),
      tool,
      ...(client && { client }),
    },
    input,
  };
}

/**
 * Create a success response envelope.
 *
 * @param {string} requestId - Original request ID
 * @param {string} tool - Tool name
 * @param {Object} result - Tool result
 * @returns {Object} Response envelope
 */
function createResponseEnvelope(requestId, tool, result) {
  return {
    mcp: {
      envelope: ENVELOPE_VERSION,
      request_id: requestId,
      tool,
      ok: true,
    },
    result,
  };
}

/**
 * Create an error response envelope.
 *
 * @param {string} requestId - Original request ID
 * @param {string} tool - Tool name
 * @param {string} code - Error code
 * @param {string} message - Error message
 * @param {string} [fix] - Suggested fix
 * @returns {Object} Error envelope
 */
function createErrorEnvelope(requestId, tool, code, message, fix = null) {
  return {
    mcp: {
      envelope: ENVELOPE_VERSION,
      request_id: requestId,
      tool,
      ok: false,
    },
    error: {
      code,
      message,
      ...(fix && { fix }),
    },
  };
}

/**
 * Error codes for a11y tools.
 */
const ERROR_CODES = {
  // General errors
  INVALID_INPUT: "INVALID_INPUT",
  INTERNAL_ERROR: "INTERNAL_ERROR",

  // Evidence errors
  FILE_NOT_FOUND: "FILE_NOT_FOUND",
  CAPTURE_FAILED: "CAPTURE_FAILED",

  // Diagnosis errors
  BUNDLE_NOT_FOUND: "BUNDLE_NOT_FOUND",
  ARTIFACT_NOT_FOUND: "ARTIFACT_NOT_FOUND",
  INVALID_BUNDLE: "INVALID_BUNDLE",

  // Integrity errors
  PROVENANCE_VERIFICATION_FAILED: "PROVENANCE_VERIFICATION_FAILED",
  DIGEST_MISMATCH: "DIGEST_MISMATCH",

  // Schema errors
  SCHEMA_VALIDATION_FAILED: "SCHEMA_VALIDATION_FAILED",
};

/**
 * Wrap a tool execution with envelope handling.
 *
 * @param {string} tool - Tool name
 * @param {Function} handler - Tool handler function
 * @returns {Function} Wrapped handler
 */
function withEnvelope(tool, handler) {
  return async (envelope) => {
    const requestId = envelope?.mcp?.request_id || generateRequestId();

    try {
      // Validate envelope structure
      if (!envelope?.input) {
        return createErrorEnvelope(
          requestId,
          tool,
          ERROR_CODES.INVALID_INPUT,
          "Missing input in request envelope",
          "Wrap your input in { mcp: { ... }, input: { ... } }"
        );
      }

      // Execute handler
      const result = await handler(envelope.input);

      // Check for handler errors
      if (result.ok === false) {
        return createErrorEnvelope(
          requestId,
          tool,
          result.error?.code || ERROR_CODES.INTERNAL_ERROR,
          result.error?.message || "Unknown error",
          result.error?.fix
        );
      }

      // Return success envelope
      return createResponseEnvelope(requestId, tool, result);
    } catch (err) {
      return createErrorEnvelope(
        requestId,
        tool,
        ERROR_CODES.INTERNAL_ERROR,
        err.message,
        "Check tool input and try again"
      );
    }
  };
}

/**
 * Parse incoming request - supports both envelope and raw input.
 *
 * For backwards compatibility, accepts:
 * 1. Full envelope: { mcp: { ... }, input: { ... } }
 * 2. Raw input: { targets: [...], ... }
 *
 * @param {Object} request - Request (envelope or raw)
 * @param {string} tool - Tool name
 * @returns {Object} Normalized envelope
 */
function normalizeRequest(request, tool) {
  // Already an envelope
  if (request?.mcp?.envelope) {
    return request;
  }

  // Raw input - wrap in envelope
  return createRequestEnvelope(tool, request, {
    name: "a11y-mcp-tools",
    version: "0.1.0",
  });
}

module.exports = {
  ENVELOPE_VERSION,
  ERROR_CODES,
  generateRequestId,
  createRequestEnvelope,
  createResponseEnvelope,
  createErrorEnvelope,
  withEnvelope,
  normalizeRequest,
};
