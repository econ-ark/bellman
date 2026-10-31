// The Rollup configuration of the editor bundle.
// Input: src/editor.js. Output: dist/bellman-workbench.js, one IIFE script that
// defines window.bellmanEditor. build.sh copies the output to
// ../../bellman_workbench/public/codemirror/bellman-workbench.js, the path Solara serves.
import { readFileSync } from "node:fs";

import { nodeResolve } from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";

const manifest = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8"));

// The version string of the bundle: the exact version of each CodeMirror
// package named in package.json, so that the bundle reports what it holds.
const versions = Object.entries(manifest.dependencies)
  .filter(([name]) => name === "codemirror" || name.startsWith("@codemirror/"))
  .map(([name, version]) => `${name}@${version}`)
  .join(" ");

const VERSIONS_ID = "\0bellman-workbench-versions";

// A one-module plugin that answers the import "bellman-workbench-versions"
// with the string above; the versions live in package.json only.
const versionsModule = {
  name: "bellman-workbench-versions",
  resolveId(source) {
    return source === "bellman-workbench-versions" ? VERSIONS_ID : null;
  },
  load(id) {
    return id === VERSIONS_ID ? `export default ${JSON.stringify(versions)};` : null;
  },
};

export default {
  input: "src/editor.js",
  output: {
    file: "dist/bellman-workbench.js",
    format: "iife",
    name: "bellmanEditor",
    sourcemap: false,
  },
  plugins: [versionsModule, nodeResolve(), terser()],
};
