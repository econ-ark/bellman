// Lay out the DOT text on standard input with the WebAssembly build of Graphviz
// (@viz-js/viz) and write the SVG to standard output. graphviz_layout.py runs
// this file when Graphviz's own `dot` program is not on the PATH, and passes
// as the one argument the folder whose node_modules/ holds the package: the
// repository root, where `npm install` from the root package.json places it.
// The package is resolved from that folder, not from this file's, so the
// package folder needs no node_modules of its own.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const packageRoot = process.argv[2];
if (packageRoot === undefined) {
  process.stderr.write('graphviz_layout.mjs takes one argument, the folder whose node_modules holds @viz-js/viz.\n');
  process.exit(2);
}
const requireFromRoot = createRequire(join(packageRoot, 'package.json'));
const { instance } = requireFromRoot('@viz-js/viz');
const viz = await instance();
process.stdout.write(viz.renderString(readFileSync(0, 'utf8'), { format: 'svg', engine: 'dot' }));
