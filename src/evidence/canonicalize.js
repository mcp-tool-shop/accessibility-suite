"use strict";

/**
 * Canonicalize a JSON value per prov-spec requirements.
 * - Sorted keys
 * - No whitespace
 * - UTF-8 (handled by Node.js strings)
 *
 * This is a JCS-subset per RFC 8785.
 *
 * @param {any} value - JSON-compatible value
 * @returns {string} Canonical JSON string
 */
function canonicalize(value) {
  if (value === null) {
    return "null";
  }

  const type = typeof value;

  if (type === "boolean") {
    return value ? "true" : "false";
  }

  if (type === "string") {
    return JSON.stringify(value);
  }

  if (type === "number") {
    if (!Number.isFinite(value)) {
      throw new Error("Non-finite numbers not allowed in canonical JSON");
    }
    return JSON.stringify(value);
  }

  if (Array.isArray(value)) {
    const items = value.map((item) => canonicalize(item));
    return "[" + items.join(",") + "]";
  }

  if (type === "object") {
    const keys = Object.keys(value).sort();
    const pairs = keys.map(
      (key) => JSON.stringify(key) + ":" + canonicalize(value[key])
    );
    return "{" + pairs.join(",") + "}";
  }

  throw new Error(`Non-JSON value type: ${type}`);
}

module.exports = { canonicalize };
