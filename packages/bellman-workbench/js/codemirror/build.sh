#!/usr/bin/env bash
# Builds the editor bundle and its license notices and copies both to the
# folder Solara serves, with KaTeX's stylesheet, its fonts and its license,
# which the preview of a note reads (unit N, Task 4). Run from any
# directory; the script works in its own folder. Requires Node 22 and npm.
# npm ci installs the exact versions of package-lock.json into node_modules
# (a network request unless the npm cache holds them); rollup writes
# dist/bellman-workbench.js; licenses.mjs writes the notices of the packages
# in package-lock.json from their license files under node_modules. KaTeX's
# fonts are copied in the WOFF2 format alone, the first format its
# stylesheet names, which every browser the page supports reads. README.md
# in this folder records the Node version and the digests of one build; a
# rebuild on the same platform gives the same bytes.
set -euo pipefail
cd "$(dirname "$0")"
npm ci
npx rollup -c
node licenses.mjs > dist/LICENSES.txt
public=../../bellman_workbench/public/codemirror
mkdir -p "$public"
cp dist/bellman-workbench.js "$public/bellman-workbench.js"
cp dist/LICENSES.txt "$public/LICENSES.txt"
rm -rf "$public/katex"
mkdir -p "$public/katex/fonts"
cp node_modules/katex/dist/katex.min.css "$public/katex/katex.min.css"
cp node_modules/katex/dist/fonts/*.woff2 "$public/katex/fonts/"
cp node_modules/katex/LICENSE "$public/katex/LICENSE"
node --version
(cd "$public" && sha256sum bellman-workbench.js LICENSES.txt katex/katex.min.css katex/LICENSE)
(cd "$public/katex/fonts" && ls *.woff2 | wc -l && cat *.woff2 | sha256sum)
