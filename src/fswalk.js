"use strict";

const fs = require("fs");
const path = require("path");

/**
 * Gather all .html files from a path.
 * If path is a file, returns [path].
 * If path is a directory, recursively finds all .html files.
 *
 * @param {string} targetPath - File or directory path
 * @returns {string[]} Array of absolute file paths, sorted for determinism
 */
function walkHtmlFiles(targetPath) {
  const resolved = path.resolve(targetPath);

  if (!fs.existsSync(resolved)) {
    throw new Error(`Path does not exist: ${resolved}`);
  }

  const stat = fs.statSync(resolved);

  if (stat.isFile()) {
    if (resolved.endsWith(".html") || resolved.endsWith(".htm")) {
      return [resolved];
    }
    throw new Error(`Not an HTML file: ${resolved}`);
  }

  if (stat.isDirectory()) {
    const files = [];
    walkDir(resolved, files);
    // Sort for deterministic ordering
    return files.sort();
  }

  throw new Error(`Invalid path type: ${resolved}`);
}

function walkDir(dir, files) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      walkDir(fullPath, files);
    } else if (entry.isFile()) {
      if (entry.name.endsWith(".html") || entry.name.endsWith(".htm")) {
        files.push(fullPath);
      }
    }
  }
}

module.exports = { walkHtmlFiles };
