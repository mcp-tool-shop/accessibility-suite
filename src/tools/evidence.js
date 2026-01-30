"use strict";

/**
 * a11y.evidence MCP tool
 *
 * Captures tamper-evident evidence bundles from inputs (HTML, CLI logs, files).
 * Produces canonical artifacts + digests + provenance.
 *
 * SAFE-only: never edits user files.
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { Parser } = require("htmlparser2");

const {
  createArtifact,
  artifactId,
  createProvenanceRecord,
  EVIDENCE_METHODS,
} = require("../schemas/index.js");

/**
 * Execute the a11y.evidence tool.
 *
 * @param {Object} input - Tool input
 * @returns {Object} Tool response
 */
async function execute(input) {
  try {
    const result = await captureEvidence(input);
    return { ok: true, bundle: result };
  } catch (err) {
    return {
      ok: false,
      error: {
        code: "EVIDENCE_CAPTURE_FAILED",
        message: err.message,
      },
    };
  }
}

/**
 * Capture evidence from targets.
 *
 * @param {Object} input
 * @returns {Object} Evidence bundle
 */
async function captureEvidence(input) {
  const { targets = [], capture = {}, integrity = {}, labels = [] } = input;

  const bundleId = `bundle:${crypto.randomUUID()}`;
  const artifacts = [];
  const methods = [];
  const inputPaths = [];

  // Process each target
  for (const target of targets) {
    inputPaths.push(target.path || target.url || "unknown");

    if (target.kind === "file") {
      const fileArtifacts = await captureFile(target, capture, labels);
      artifacts.push(...fileArtifacts);
    } else if (target.kind === "cli_log") {
      const logArtifact = await captureCliLog(target, labels);
      artifacts.push(logArtifact);
    } else if (target.kind === "url") {
      // URL fetching would go here (not implemented in v0.1.0)
      throw new Error(`URL capture not yet implemented: ${target.url}`);
    }
  }

  // Track methods used
  if (artifacts.some((a) => a.labels.includes("html"))) {
    methods.push(EVIDENCE_METHODS.CAPTURE_HTML);
  }
  if (artifacts.some((a) => a.labels.includes("dom-snapshot"))) {
    methods.push(EVIDENCE_METHODS.CAPTURE_DOM);
  }
  if (artifacts.some((a) => a.labels.includes("cli-log"))) {
    methods.push(EVIDENCE_METHODS.CAPTURE_FILE);
  }

  methods.push(EVIDENCE_METHODS.INTEGRITY_SHA256);
  methods.push(EVIDENCE_METHODS.PROVENANCE_RECORD);

  // Build provenance record
  const provenance = createProvenanceRecord({
    methods,
    inputs: inputPaths,
    outputs: artifacts.map((a) => a.artifact_id),
  });

  // Add environment info if requested
  let environment = null;
  if (capture.environment?.include) {
    environment = captureEnvironment(capture.environment.include);
  }

  return {
    bundle_id: bundleId,
    artifacts,
    provenance,
    environment,
    labels,
    created_at: new Date().toISOString(),
  };
}

/**
 * Capture a file target.
 */
async function captureFile(target, capture, globalLabels) {
  const filePath = path.resolve(target.path);

  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }

  const content = fs.readFileSync(filePath, "utf8");
  const baseName = path.basename(filePath, path.extname(filePath));
  const ext = path.extname(filePath).toLowerCase();

  const artifacts = [];

  // Determine if HTML
  const isHtml = ext === ".html" || ext === ".htm";

  if (isHtml) {
    // Create HTML artifact
    let htmlContent = content;

    if (capture.html?.canonicalize) {
      htmlContent = canonicalizeHtml(content, capture.html);
    }

    const htmlArtifact = createArtifact({
      id: artifactId("html", baseName),
      mediaType: "text/html",
      locator: { kind: "file", path: target.path },
      content: htmlContent,
      labels: ["source", "html", ...globalLabels],
    });
    artifacts.push(htmlArtifact);

    // Create DOM snapshot if requested
    if (capture.dom?.snapshot) {
      const domSnapshot = createDomSnapshot(content, capture.dom);
      const domArtifact = createArtifact({
        id: artifactId("dom", baseName),
        mediaType: "application/json",
        locator: { kind: "derived", from: htmlArtifact.artifact_id },
        content: JSON.stringify(domSnapshot, null, 2),
        labels: ["derived", "dom-snapshot", ...globalLabels],
      });
      artifacts.push(domArtifact);
    }
  } else {
    // Generic file artifact
    const fileArtifact = createArtifact({
      id: artifactId("file", baseName),
      mediaType: getMimeType(ext),
      locator: { kind: "file", path: target.path },
      content,
      labels: ["source", "file", ...globalLabels],
    });
    artifacts.push(fileArtifact);
  }

  return artifacts;
}

/**
 * Capture a CLI log.
 */
async function captureCliLog(target, globalLabels) {
  const filePath = path.resolve(target.path);

  if (!fs.existsSync(filePath)) {
    throw new Error(`CLI log not found: ${filePath}`);
  }

  const content = fs.readFileSync(filePath, "utf8");
  const baseName = path.basename(filePath, path.extname(filePath));

  return createArtifact({
    id: artifactId("log", baseName),
    mediaType: "text/plain",
    locator: { kind: "file", path: target.path },
    content,
    labels: ["source", "cli-log", ...globalLabels],
  });
}

/**
 * Canonicalize HTML content.
 * - Normalize whitespace (collapse runs)
 * - Sort attributes alphabetically
 * - Strip dynamic attributes if configured
 */
function canonicalizeHtml(html, options = {}) {
  const { strip_dynamic = false } = options;

  // Dynamic attributes to strip
  const dynamicAttrs = new Set([
    "data-reactid",
    "data-reactroot",
    "data-v-",
    "ng-",
    "_ngcontent",
    "_nghost",
  ]);

  let result = "";
  let inTag = false;
  let currentTag = "";
  let attrs = [];

  const parser = new Parser(
    {
      onopentag(name, attributes) {
        // Sort attributes
        const sortedAttrs = Object.entries(attributes)
          .filter(([key]) => {
            if (!strip_dynamic) return true;
            // Filter out dynamic attributes
            return !Array.from(dynamicAttrs).some(
              (d) => key.startsWith(d) || key.includes(d)
            );
          })
          .sort(([a], [b]) => a.localeCompare(b));

        const attrStr = sortedAttrs
          .map(([key, val]) => (val === "" ? key : `${key}="${escapeAttr(val)}"`))
          .join(" ");

        result += attrStr ? `<${name} ${attrStr}>` : `<${name}>`;
      },
      ontext(text) {
        // Normalize whitespace
        const normalized = text.replace(/\s+/g, " ");
        result += normalized;
      },
      onclosetag(name) {
        result += `</${name}>`;
      },
      oncomment(data) {
        result += `<!--${data}-->`;
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

  return result.trim();
}

/**
 * Create a DOM snapshot.
 */
function createDomSnapshot(html, options = {}) {
  const { include_css_selectors = true } = options;

  const nodes = [];
  const stack = [];

  const parser = new Parser(
    {
      onopentag(name, attrs) {
        const node = {
          type: "element",
          tagName: name.toLowerCase(),
          attrs: { ...attrs },
          children: [],
          index: nodes.length,
        };

        // Add CSS selector if requested
        if (include_css_selectors) {
          node.selector = buildSelector(node, stack);
        }

        nodes.push(node);

        if (stack.length > 0) {
          stack[stack.length - 1].children.push(node);
        }

        stack.push(node);
      },
      ontext(text) {
        const trimmed = text.trim();
        if (trimmed && stack.length > 0) {
          const textNode = {
            type: "text",
            content: text,
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

  return {
    nodes,
    root: nodes.find((n) => n.type === "element" && n.tagName === "html") || nodes[0],
  };
}

/**
 * Build a CSS selector for a node.
 */
function buildSelector(node, stack) {
  let selector = node.tagName;

  if (node.attrs.id) {
    selector += `#${node.attrs.id}`;
  } else if (node.attrs.class) {
    const classes = node.attrs.class.split(/\s+/).filter(Boolean);
    if (classes.length > 0) {
      selector += "." + classes.slice(0, 2).join(".");
    }
  }

  return selector;
}

/**
 * Capture environment info.
 */
function captureEnvironment(include) {
  const env = {};

  if (include.includes("os")) {
    env.os = {
      platform: process.platform,
      arch: process.arch,
    };
  }

  if (include.includes("node")) {
    env.node = process.version;
  }

  if (include.includes("tool_versions")) {
    env.tool_versions = {
      "a11y-mcp-tools": "0.1.0",
    };
  }

  return env;
}

/**
 * Escape attribute value.
 */
function escapeAttr(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Get MIME type from extension.
 */
function getMimeType(ext) {
  const mimeTypes = {
    ".html": "text/html",
    ".htm": "text/html",
    ".css": "text/css",
    ".js": "text/javascript",
    ".json": "application/json",
    ".txt": "text/plain",
    ".log": "text/plain",
    ".xml": "application/xml",
  };
  return mimeTypes[ext] || "application/octet-stream";
}

/**
 * Tool definition for MCP registration.
 */
const toolDefinition = {
  name: "a11y.evidence",
  description:
    "Capture tamper-evident evidence bundles from HTML files, CLI logs, or other inputs. Produces canonical artifacts + digests + provenance.",
  inputSchema: {
    type: "object",
    properties: {
      targets: {
        type: "array",
        description: "Files or URLs to capture",
        items: {
          type: "object",
          properties: {
            kind: {
              type: "string",
              enum: ["file", "cli_log", "url"],
            },
            path: { type: "string" },
            url: { type: "string" },
          },
          required: ["kind"],
        },
      },
      capture: {
        type: "object",
        description: "Capture options",
        properties: {
          html: {
            type: "object",
            properties: {
              canonicalize: { type: "boolean" },
              strip_dynamic: { type: "boolean" },
            },
          },
          dom: {
            type: "object",
            properties: {
              snapshot: { type: "boolean" },
              include_css_selectors: { type: "boolean" },
            },
          },
          environment: {
            type: "object",
            properties: {
              include: {
                type: "array",
                items: { type: "string" },
              },
            },
          },
        },
      },
      integrity: {
        type: "object",
        properties: {
          hash: { type: "string", enum: ["sha256"] },
          verify_provenance: { type: "boolean" },
        },
      },
      labels: {
        type: "array",
        items: { type: "string" },
      },
    },
    required: ["targets"],
  },
};

module.exports = {
  execute,
  toolDefinition,
  // Export internals for testing
  captureEvidence,
  canonicalizeHtml,
  createDomSnapshot,
};
