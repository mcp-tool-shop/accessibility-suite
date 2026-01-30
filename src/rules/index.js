"use strict";

const imgMissingAlt = require("./img_missing_alt.js");
const formControlMissingLabel = require("./form_control_missing_label.js");
const interactiveMissingName = require("./interactive_missing_name.js");
const documentMissingLang = require("./document_missing_lang.js");

/**
 * All available rules.
 * Each rule exports: { id, run(nodes, context) => findings[] }
 */
const rules = [
  documentMissingLang,
  imgMissingAlt,
  formControlMissingLabel,
  interactiveMissingName,
];

/**
 * Run all rules against parsed HTML nodes.
 *
 * @param {Array} nodes - Flat nodes array from parseHtml
 * @param {Object} context - { filePath, relativePath }
 * @returns {Array} Raw findings (without finding_id assigned)
 */
function runRules(nodes, context) {
  const findings = [];

  for (const rule of rules) {
    const ruleFindings = rule.run(nodes, context);
    findings.push(...ruleFindings);
  }

  return findings;
}

module.exports = { rules, runRules };
