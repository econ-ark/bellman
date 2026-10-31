// The Rollup configuration of the graph's bundle.
// Input: src/index.js. Output: dist/bellman-flow.js, one IIFE script that
// defines window.BellmanFlow. build.sh copies the output to
// ../../bellman_workbench/public/flow/bellman-flow.js, the path Solara serves.
import commonjs from "@rollup/plugin-commonjs";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import replace from "@rollup/plugin-replace";
import terser from "@rollup/plugin-terser";

export default {
  input: "src/index.js",
  output: {
    file: "dist/bellman-flow.js",
    format: "iife",
    sourcemap: false,
  },
  plugins: [
    // React's entry files choose their production build by NODE_ENV
    replace({
      preventAssignment: true,
      values: { "process.env.NODE_ENV": JSON.stringify("production") },
    }),
    nodeResolve({ browser: true }),
    // React and its dependencies are CommonJS; the two scripts of src/ keep
    // their own heads
    commonjs({ include: /node_modules/ }),
    terser(),
  ],
};
