"use strict";

const artifact = require("./artifact.js");
const evidence = require("./evidence.js");
const provenance = require("./provenance.js");

module.exports = {
  ...artifact,
  ...evidence,
  ...provenance,
};
