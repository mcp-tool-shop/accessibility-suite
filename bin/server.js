#!/usr/bin/env node
"use strict";

/**
 * MCP Server for a11y tools.
 *
 * Implements the Model Context Protocol for:
 * - a11y.evidence: Evidence capture
 * - a11y.diagnose: Accessibility diagnosis
 *
 * Supports MCP envelope v0.1 for requests/responses.
 */

const readline = require("readline");
const { evidence, diagnose, tools } = require("../src/tools/index.js");
const {
  ENVELOPE_VERSION,
  ERROR_CODES,
  generateRequestId,
  createResponseEnvelope,
  createErrorEnvelope,
  normalizeRequest,
} = require("../src/envelope.js");

// In-memory bundle store for the session
const bundleStore = {};

/**
 * Handle incoming MCP request.
 */
async function handleRequest(request) {
  const { id, method, params } = request;

  try {
    switch (method) {
      case "initialize":
        return {
          jsonrpc: "2.0",
          id,
          result: {
            protocolVersion: "2024-11-05",
            capabilities: {
              tools: {},
            },
            serverInfo: {
              name: "a11y-mcp-tools",
              version: "0.2.0",
            },
          },
        };

      case "tools/list":
        return {
          jsonrpc: "2.0",
          id,
          result: {
            tools: tools.map((t) => ({
              name: t.name,
              description: t.description,
              inputSchema: t.inputSchema,
            })),
          },
        };

      case "tools/call":
        return await handleToolCall(id, params);

      default:
        return {
          jsonrpc: "2.0",
          id,
          error: {
            code: -32601,
            message: `Method not found: ${method}`,
          },
        };
    }
  } catch (err) {
    return {
      jsonrpc: "2.0",
      id,
      error: {
        code: -32603,
        message: err.message,
      },
    };
  }
}

/**
 * Handle tool call with envelope support.
 */
async function handleToolCall(id, params) {
  const { name, arguments: args } = params;

  // Normalize to envelope format (supports both raw and envelope input)
  const envelope = normalizeRequest(args, name);
  const requestId = envelope.mcp?.request_id || generateRequestId();
  const input = envelope.input || args;

  let result;
  let responseEnvelope;

  try {
    switch (name) {
      case "a11y.evidence":
        result = await evidence.execute(input);
        if (result.ok) {
          // Store bundle for later diagnosis
          if (result.bundle) {
            bundleStore[result.bundle.bundle_id] = result.bundle;
          }
          responseEnvelope = createResponseEnvelope(requestId, name, {
            bundle: result.bundle,
          });
        } else {
          responseEnvelope = createErrorEnvelope(
            requestId,
            name,
            result.error?.code || ERROR_CODES.CAPTURE_FAILED,
            result.error?.message || "Evidence capture failed",
            result.error?.fix
          );
        }
        break;

      case "a11y.diagnose":
        // Check if bundle_id is provided and resolve from store
        if (input.bundle_id && !input.bundle) {
          const storedBundle = bundleStore[input.bundle_id];
          if (!storedBundle) {
            responseEnvelope = createErrorEnvelope(
              requestId,
              name,
              ERROR_CODES.BUNDLE_NOT_FOUND,
              `Bundle not found: ${input.bundle_id}`,
              "Capture evidence first using a11y.evidence, or provide bundle inline."
            );
            break;
          }
          input.bundle = storedBundle;
        }

        result = await diagnose.execute(input, bundleStore);
        if (result.ok) {
          responseEnvelope = createResponseEnvelope(requestId, name, {
            diagnosis: result.diagnosis,
          });
        } else {
          responseEnvelope = createErrorEnvelope(
            requestId,
            name,
            result.error?.code || ERROR_CODES.INTERNAL_ERROR,
            result.error?.message || "Diagnosis failed",
            result.error?.fix
          );
        }
        break;

      default:
        return {
          jsonrpc: "2.0",
          id,
          error: {
            code: -32602,
            message: `Unknown tool: ${name}`,
          },
        };
    }

    return {
      jsonrpc: "2.0",
      id,
      result: {
        content: [
          {
            type: "text",
            text: JSON.stringify(responseEnvelope, null, 2),
          },
        ],
      },
    };
  } catch (err) {
    const errorEnvelope = createErrorEnvelope(
      requestId,
      name,
      ERROR_CODES.INTERNAL_ERROR,
      err.message
    );

    return {
      jsonrpc: "2.0",
      id,
      result: {
        content: [
          {
            type: "text",
            text: JSON.stringify(errorEnvelope, null, 2),
          },
        ],
      },
    };
  }
}

/**
 * Main entry point.
 */
async function main() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false,
  });

  console.error("a11y-mcp-tools server started (v0.2.0, envelope: " + ENVELOPE_VERSION + ")");

  for await (const line of rl) {
    if (!line.trim()) continue;

    try {
      const request = JSON.parse(line);
      const response = await handleRequest(request);
      console.log(JSON.stringify(response));
    } catch (err) {
      console.error("Parse error:", err.message);
      console.log(
        JSON.stringify({
          jsonrpc: "2.0",
          id: null,
          error: {
            code: -32700,
            message: "Parse error",
          },
        })
      );
    }
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
