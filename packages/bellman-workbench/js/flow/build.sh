#!/usr/bin/env bash
# Builds the graph's bundle and its license notices, and copies them, ELK's
# unchanged file with its license, React Flow's base stylesheet and the
# mathematics font with its license to the folder Solara serves; the text
# fonts are copied by ../fonts/build.sh. Run from any directory; the script
# works in its own folder. Requires Node 22 and npm.
# npm ci installs the exact versions of package-lock.json into node_modules
# (a network request unless the npm cache holds them); rollup writes
# dist/bellman-flow.js; licenses.mjs writes the notices of the packages in
# package-lock.json from their license files under node_modules. README.md
# in this folder records the Node version and the digests of one build; a
# rebuild on the same platform gives the same bytes.
set -euo pipefail
cd "$(dirname "$0")"
npm ci
npx rollup -c
node licenses.mjs > dist/LICENSES.txt
target=../../bellman_workbench/public/flow
mkdir -p "$target"
cp dist/bellman-flow.js "$target/bellman-flow.js"
cp dist/LICENSES.txt "$target/LICENSES.txt"
cp node_modules/elkjs/lib/elk.bundled.js "$target/elk.bundled.js"
cp node_modules/elkjs/LICENSE.md "$target/elkjs-LICENSE.md"
cp node_modules/@xyflow/react/dist/base.css "$target/base.css"
cp node_modules/@fontsource/stix-two-math/files/stix-two-math-latin-400-normal.woff2 "$target/"
cp node_modules/@fontsource/stix-two-math/LICENSE "$target/STIX-Two-Math-OFL.txt"
node --version
(cd ../.. && sha256sum bellman_workbench/public/flow/*)
