#!/usr/bin/env node
"use strict";

/**
 * a11y CLI - Command-line interface for a11y MCP tools.
 *
 * Maps directly to MCP tool calls with standard exit codes:
 *   0 = success, no findings at/above --fail-on
 *   2 = success, findings exist (but not a tool failure)
 *   3 = capture/validation failure (bad input, schema fail, etc.)
 *   4 = provenance verification failed (digest mismatch)
 */

const fs = require("fs");
const path = require("path");
const { evidence, diagnose } = require("../src/tools/index.js");
const {
  createRequestEnvelope,
  createResponseEnvelope,
  createErrorEnvelope,
  ERROR_CODES,
} = require("../src/envelope.js");

const VERSION = "0.2.0";

// Exit codes (CI-native)
const EXIT_OK = 0;              // Success, no findings
const EXIT_FINDINGS = 2;        // Success, findings exist
const EXIT_VALIDATION = 3;      // Capture/validation failure
const EXIT_PROVENANCE = 4;      // Provenance verification failed

/**
 * Parse command-line arguments.
 */
function parseArgs(args) {
  const result = {
    command: null,
    flags: {},
    positional: [],
  };

  let i = 0;
  while (i < args.length) {
    const arg = args[i];

    if (!result.command && !arg.startsWith("-")) {
      result.command = arg;
      i++;
      continue;
    }

    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      const nextArg = args[i + 1];

      // Boolean flags vs value flags
      if (
        !nextArg ||
        nextArg.startsWith("-") ||
        key === "dom-snapshot" ||
        key === "canonicalize" ||
        key === "strip-dynamic" ||
        key === "fix" ||
        key === "json" ||
        key === "envelope" ||
        key === "verify-provenance" ||
        key === "help" ||
        key === "version"
      ) {
        result.flags[key] = true;
        i++;
      } else {
        result.flags[key] = nextArg;
        i += 2;
      }
    } else if (arg.startsWith("-")) {
      // Short flags
      const key = arg.slice(1);
      result.flags[key] = true;
      i++;
    } else {
      result.positional.push(arg);
      i++;
    }
  }

  return result;
}

/**
 * Print help message.
 */
function printHelp() {
  console.log(`
a11y - Accessibility evidence capture and diagnosis

USAGE:
  a11y <command> [options]

COMMANDS:
  evidence    Capture tamper-evident evidence bundles
  diagnose    Run accessibility diagnosis on evidence

EVIDENCE OPTIONS:
  --target <path>       File to capture (can be repeated)
  --dom-snapshot        Include DOM snapshot artifact
  --canonicalize        Canonicalize HTML content
  --strip-dynamic       Strip dynamic attributes (React, Vue, Angular)
  --label <label>       Add label to artifacts (can be repeated)
  --out <path>          Output bundle to file (default: stdout)
  --envelope            Wrap output in MCP envelope

DIAGNOSE OPTIONS:
  --bundle <path>       Path to evidence bundle JSON
  --bundle-id <id>      Bundle ID (when using MCP server)
  --profile <profile>   WCAG profile (wcag-2.0-a, wcag-2.0-aa, wcag-2.1-a,
                        wcag-2.1-aa, wcag-2.2-a, wcag-2.2-aa) (default: wcag-2.2-aa)
  --rules <rules>       Comma-separated rule names to run
  --exclude <rules>     Comma-separated rules to exclude
  --fix                 Include fix guidance in findings
  --verify-provenance   Verify artifact digests before diagnosis
  --fail-on <severity>  Exit 2 if findings at/above severity (default: low)
  --out <path>          Output diagnosis to file (default: stdout)
  --envelope            Wrap output in MCP envelope

GLOBAL OPTIONS:
  --json                Output as JSON (default)
  --envelope            Wrap output in MCP envelope
  --help, -h            Show this help message
  --version, -v         Show version

EXIT CODES:
  0  Success (no findings at/above --fail-on)
  2  Findings exist (tool succeeded, but issues found)
  3  Capture/validation failure (bad input, schema error)
  4  Provenance verification failed (digest mismatch)

EXAMPLES:
  # Capture evidence from HTML file
  a11y evidence --target index.html --dom-snapshot --out evidence.json

  # Diagnose captured evidence
  a11y diagnose --bundle evidence.json --fix

  # Diagnose with specific WCAG profile
  a11y diagnose --bundle evidence.json --profile wcag-2.1-aa --fix

  # With provenance verification
  a11y diagnose --bundle evidence.json --verify-provenance --fix

  # Output with MCP envelope
  a11y evidence --target page.html --envelope

  # One-liner capture and diagnose
  a11y evidence --target page.html --dom-snapshot | a11y diagnose --fix
`);
}

/**
 * Evidence command handler.
 */
async function handleEvidence(flags, positional) {
  // Collect targets
  const targets = [];

  // From --target flags (may be repeated)
  if (flags.target) {
    const targetPaths = Array.isArray(flags.target)
      ? flags.target
      : [flags.target];
    for (const p of targetPaths) {
      targets.push({ kind: "file", path: p });
    }
  }

  // From positional args
  for (const p of positional) {
    targets.push({ kind: "file", path: p });
  }

  if (targets.length === 0) {
    console.error("Error: No targets specified. Use --target <path>");
    process.exit(EXIT_VALIDATION);
  }

  // Build capture options
  const capture = {
    html: {},
    dom: {},
    environment: { include: ["os", "node", "tool_versions"] },
  };

  if (flags["dom-snapshot"]) {
    capture.dom.snapshot = true;
    capture.dom.include_css_selectors = true;
  }

  if (flags.canonicalize) {
    capture.html.canonicalize = true;
  }

  if (flags["strip-dynamic"]) {
    capture.html.strip_dynamic = true;
  }

  // Collect labels
  const labels = [];
  if (flags.label) {
    const labelList = Array.isArray(flags.label) ? flags.label : [flags.label];
    labels.push(...labelList);
  }

  // Build input
  const input = { targets, capture, labels };

  // Execute
  const result = await evidence.execute(input);

  if (!result.ok) {
    if (flags.envelope) {
      const errorEnvelope = createErrorEnvelope(
        `req_cli_${Date.now()}`,
        "a11y.evidence",
        result.error?.code || ERROR_CODES.CAPTURE_FAILED,
        result.error?.message || "Evidence capture failed"
      );
      console.log(JSON.stringify(errorEnvelope, null, 2));
    } else {
      console.error(`Error: ${result.error.message}`);
    }
    process.exit(EXIT_VALIDATION);
  }

  // Output
  let output;
  if (flags.envelope) {
    const envelope = createResponseEnvelope(
      `req_cli_${Date.now()}`,
      "a11y.evidence",
      { bundle: result.bundle }
    );
    output = JSON.stringify(envelope, null, 2);
  } else {
    output = JSON.stringify(result.bundle, null, 2);
  }

  if (flags.out) {
    fs.writeFileSync(flags.out, output + "\n");
    console.error(`Bundle written to: ${flags.out}`);
  } else {
    console.log(output);
  }

  process.exit(EXIT_OK);
}

/**
 * Diagnose command handler.
 */
async function handleDiagnose(flags, positional) {
  let bundle = null;

  // Load bundle from file
  if (flags.bundle) {
    const bundlePath = path.resolve(flags.bundle);
    if (!fs.existsSync(bundlePath)) {
      console.error(`Error: Bundle file not found: ${bundlePath}`);
      process.exit(EXIT_VALIDATION);
    }
    try {
      bundle = JSON.parse(fs.readFileSync(bundlePath, "utf8"));
    } catch (err) {
      console.error(`Error: Failed to parse bundle: ${err.message}`);
      process.exit(EXIT_VALIDATION);
    }
  } else if (positional.length > 0) {
    // First positional as bundle path
    const bundlePath = path.resolve(positional[0]);
    if (!fs.existsSync(bundlePath)) {
      console.error(`Error: Bundle file not found: ${bundlePath}`);
      process.exit(EXIT_VALIDATION);
    }
    try {
      bundle = JSON.parse(fs.readFileSync(bundlePath, "utf8"));
    } catch (err) {
      console.error(`Error: Failed to parse bundle: ${err.message}`);
      process.exit(EXIT_VALIDATION);
    }
  } else {
    // Read from stdin
    const stdin = fs.readFileSync(0, "utf8");
    try {
      bundle = JSON.parse(stdin);
    } catch (err) {
      console.error("Error: Failed to parse bundle from stdin");
      process.exit(EXIT_VALIDATION);
    }
  }

  // Build rules filter
  const rules = {};
  if (flags.rules) {
    rules.include = flags.rules.split(",").map((r) => r.trim());
  }
  if (flags.exclude) {
    rules.exclude = flags.exclude.split(",").map((r) => r.trim());
  }

  // Build output options
  const outputOptions = {};
  if (flags.fix) {
    outputOptions.include_fix_guidance = true;
  }

  // Build integrity options
  const integrity = {};
  if (flags["verify-provenance"]) {
    integrity.verify_provenance = true;
  }

  // Get profile (default wcag-2.2-aa)
  const profile = flags.profile || "wcag-2.2-aa";
  const validProfiles = [
    "wcag-2.0-a",
    "wcag-2.0-aa",
    "wcag-2.1-a",
    "wcag-2.1-aa",
    "wcag-2.2-a",
    "wcag-2.2-aa",
  ];
  if (!validProfiles.includes(profile)) {
    console.error(`Error: Invalid profile '${profile}'. Valid profiles: ${validProfiles.join(", ")}`);
    process.exit(EXIT_VALIDATION);
  }

  // Execute
  const input = { bundle, rules, output: outputOptions, integrity, profile };
  const result = await diagnose.execute(input);

  if (!result.ok) {
    // Check for provenance verification failure
    const isProvenanceError =
      result.error?.code === ERROR_CODES.PROVENANCE_VERIFICATION_FAILED ||
      result.error?.code === ERROR_CODES.DIGEST_MISMATCH;

    if (flags.envelope) {
      const errorEnvelope = createErrorEnvelope(
        `req_cli_${Date.now()}`,
        "a11y.diagnose",
        result.error?.code || ERROR_CODES.INTERNAL_ERROR,
        result.error?.message || "Diagnosis failed",
        result.error?.fix
      );
      console.log(JSON.stringify(errorEnvelope, null, 2));
    } else {
      console.error(`Error: ${result.error.message}`);
    }

    process.exit(isProvenanceError ? EXIT_PROVENANCE : EXIT_VALIDATION);
  }

  // Output
  let output;
  if (flags.envelope) {
    const envelope = createResponseEnvelope(
      `req_cli_${Date.now()}`,
      "a11y.diagnose",
      { diagnosis: result.diagnosis }
    );
    output = JSON.stringify(envelope, null, 2);
  } else {
    output = JSON.stringify(result.diagnosis, null, 2);
  }

  if (flags.out) {
    fs.writeFileSync(flags.out, output + "\n");
    console.error(`Diagnosis written to: ${flags.out}`);
  } else {
    console.log(output);
  }

  // Exit based on findings
  const findingsCount = result.diagnosis.summary.findings_total;
  if (findingsCount > 0) {
    // Check --fail-on threshold
    const failOn = flags["fail-on"] || "low";
    const severityOrder = ["low", "medium", "high", "critical"];
    const failIndex = severityOrder.indexOf(failOn);

    // Count findings at or above threshold
    const counts = result.diagnosis.summary.severity_counts;
    let failingCount = 0;
    for (let i = failIndex; i < severityOrder.length; i++) {
      failingCount += counts[severityOrder[i]] || 0;
    }

    if (failingCount > 0) {
      console.error(`Found ${failingCount} issue(s) at/above '${failOn}' severity`);
      process.exit(EXIT_FINDINGS);
    }
  }

  process.exit(EXIT_OK);
}

/**
 * Main entry point.
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    printHelp();
    process.exit(EXIT_OK);
  }

  const { command, flags, positional } = parseArgs(args);

  // Global flags
  if (flags.help || flags.h) {
    printHelp();
    process.exit(EXIT_OK);
  }

  if (flags.version || flags.v) {
    console.log(`a11y v${VERSION}`);
    process.exit(EXIT_OK);
  }

  // Route to command handler
  switch (command) {
    case "evidence":
      await handleEvidence(flags, positional);
      break;

    case "diagnose":
      await handleDiagnose(flags, positional);
      break;

    default:
      if (command) {
        console.error(`Unknown command: ${command}`);
      }
      printHelp();
      process.exit(EXIT_VALIDATION);
  }
}

main().catch((err) => {
  console.error(`Fatal error: ${err.message}`);
  process.exit(EXIT_VALIDATION);
});
