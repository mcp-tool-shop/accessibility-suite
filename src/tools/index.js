"use strict";

const evidence = require("./evidence.js");
const diagnose = require("./diagnose.js");

module.exports = {
  evidence,
  diagnose,
  tools: [evidence.toolDefinition, diagnose.toolDefinition],
};
