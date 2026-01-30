"use strict";

const fs = require("fs");
const path = require("path");
const { walkHtmlFiles } = require("./fswalk.js");
const { parseHtml } = require("./html_parse.js");
const { runRules } = require("./rules/index.js");
const { assignFindingIds } = require("./ids.js");
const { emitProvenance } = require("./evidence/prov_emit.js");

const ENGINE_NAME = "a11y-evidence-engine";
const ENGINE_VERSION = "0.1.0";

/**
 * Scan HTML files and produce findings with provenance.
 *
 * @param {string} targetPath - File or directory to scan
 * @param {string} outDir - Output directory
 * @returns {Object} Scan result with summary
 */
async function scan(targetPath, outDir) {
  const resolvedTarget = path.resolve(targetPath);
  const resolvedOut = path.resolve(outDir);

  // Gather HTML files
  const files = walkHtmlFiles(resolvedTarget);

  if (files.length === 0) {
    throw new Error(`No HTML files found in: ${resolvedTarget}`);
  }

  // Collect all findings
  const allFindings = [];
  const baseDir = fs.statSync(resolvedTarget).isDirectory()
    ? resolvedTarget
    : path.dirname(resolvedTarget);

  for (const filePath of files) {
    const html = fs.readFileSync(filePath, "utf8");
    const { nodes } = parseHtml(html);

    const relativePath = path.relative(baseDir, filePath).replace(/\\/g, "/");

    const context = {
      filePath,
      relativePath,
    };

    const findings = runRules(nodes, context);
    allFindings.push(...findings);
  }

  // Assign deterministic IDs
  const numberedFindings = assignFindingIds(allFindings);

  // Create output directory
  fs.mkdirSync(resolvedOut, { recursive: true });

  // Generate timestamp for all provenance records (deterministic within scan)
  const timestamp = new Date().toISOString();

  // Emit provenance for each finding
  const findingsWithRefs = [];

  for (const finding of numberedFindings) {
    const provDir = path.join(resolvedOut, "provenance", finding.finding_id);
    fs.mkdirSync(provDir, { recursive: true });

    const { record, digest, envelope } = emitProvenance(finding, {
      engineVersion: ENGINE_VERSION,
      timestamp,
    });

    // Write provenance files
    fs.writeFileSync(
      path.join(provDir, "record.json"),
      JSON.stringify(record, null, 2)
    );
    fs.writeFileSync(
      path.join(provDir, "digest.json"),
      JSON.stringify(digest, null, 2)
    );
    fs.writeFileSync(
      path.join(provDir, "envelope.json"),
      JSON.stringify(envelope, null, 2)
    );

    // Add evidence_ref to finding (without the raw evidence)
    const { evidence, ...findingWithoutEvidence } = finding;
    findingsWithRefs.push({
      ...findingWithoutEvidence,
      evidence_ref: {
        record: `provenance/${finding.finding_id}/record.json`,
        digest: `provenance/${finding.finding_id}/digest.json`,
        envelope: `provenance/${finding.finding_id}/envelope.json`,
      },
    });
  }

  // Build summary
  const summary = {
    files_scanned: files.length,
    errors: findingsWithRefs.filter((f) => f.severity === "error").length,
    warnings: findingsWithRefs.filter((f) => f.severity === "warning").length,
    info: findingsWithRefs.filter((f) => f.severity === "info").length,
  };

  // Build output
  const output = {
    engine: ENGINE_NAME,
    version: ENGINE_VERSION,
    target: {
      path: path.relative(process.cwd(), resolvedTarget).replace(/\\/g, "/") || ".",
    },
    summary,
    findings: findingsWithRefs,
  };

  // Write findings.json
  fs.writeFileSync(
    path.join(resolvedOut, "findings.json"),
    JSON.stringify(output, null, 2)
  );

  return output;
}

module.exports = { scan };
