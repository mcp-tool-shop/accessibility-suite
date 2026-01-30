"use strict";

/**
 * Generate deterministic finding IDs.
 * Findings are sorted by (file, rule_id, pointer) then numbered.
 *
 * @param {Array} findings - Raw findings array
 * @returns {Array} Findings with assigned finding_id
 */
function assignFindingIds(findings) {
  // Sort for deterministic ordering
  const sorted = [...findings].sort((a, b) => {
    // First by file
    const fileCompare = a.location.file.localeCompare(b.location.file);
    if (fileCompare !== 0) return fileCompare;

    // Then by rule_id
    const ruleCompare = a.rule_id.localeCompare(b.rule_id);
    if (ruleCompare !== 0) return ruleCompare;

    // Then by pointer (numeric extraction for proper sorting)
    const aIndex = extractPointerIndex(a.location.json_pointer);
    const bIndex = extractPointerIndex(b.location.json_pointer);
    return aIndex - bIndex;
  });

  // Assign sequential IDs
  return sorted.map((finding, index) => ({
    ...finding,
    finding_id: formatFindingId(index + 1),
  }));
}

/**
 * Extract numeric index from JSON pointer.
 * @param {string} pointer - e.g., "/nodes/12"
 * @returns {number}
 */
function extractPointerIndex(pointer) {
  const match = pointer.match(/\/nodes\/(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
}

/**
 * Format finding ID with zero-padding.
 * @param {number} num - Finding number (1-based)
 * @returns {string} e.g., "finding-0001"
 */
function formatFindingId(num) {
  return `finding-${String(num).padStart(4, "0")}`;
}

module.exports = { assignFindingIds, formatFindingId };
