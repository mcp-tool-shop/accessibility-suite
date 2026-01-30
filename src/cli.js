"use strict";

const { scan } = require("./scan.js");
const path = require("path");

const HELP = `
a11y-engine - Headless accessibility evidence engine

USAGE:
  a11y-engine scan <path> --out <dir>   Scan HTML files and emit findings
  a11y-engine --help                    Show this help

OPTIONS:
  --out <dir>   Output directory for findings.json and provenance (default: ./out)

EXIT CODES:
  0   No findings with severity 'error'
  2   At least one 'error' finding
  3   Internal engine failure / invalid input
`;

async function run(args) {
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.log(HELP);
    return 0;
  }

  const command = args[0];

  if (command === "scan") {
    return runScan(args.slice(1));
  }

  console.error(`Unknown command: ${command}`);
  console.log(HELP);
  return 3;
}

async function runScan(args) {
  // Parse arguments
  let targetPath = null;
  let outDir = "./out";

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--out" && args[i + 1]) {
      outDir = args[++i];
    } else if (!args[i].startsWith("-")) {
      targetPath = args[i];
    }
  }

  if (!targetPath) {
    console.error("Error: No target path specified");
    return 3;
  }

  try {
    const result = await scan(targetPath, outDir);

    console.log(`Scanned ${result.summary.files_scanned} file(s)`);
    console.log(`  Errors:   ${result.summary.errors}`);
    console.log(`  Warnings: ${result.summary.warnings}`);
    console.log(`  Info:     ${result.summary.info}`);
    console.log(`\nOutput: ${path.resolve(outDir)}/findings.json`);

    // Exit code based on error count
    return result.summary.errors > 0 ? 2 : 0;
  } catch (err) {
    console.error(`Scan failed: ${err.message}`);
    return 3;
  }
}

module.exports = { run };
