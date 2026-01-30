#!/usr/bin/env node
"use strict";

const { run } = require("../src/cli.js");

run(process.argv.slice(2))
  .then((code) => process.exit(code))
  .catch((err) => {
    console.error("Fatal error:", err.message);
    process.exit(3);
  });
