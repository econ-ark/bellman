#!/usr/bin/env bash
# Copies the text fonts of the Workbench, Archivo and IBM Plex Mono, with
# their licenses, from their Fontsource packages to the folder Solara
# serves. Run from any directory; the script works in its own folder.
# Requires Node 22 and npm. npm ci installs the exact versions of
# package-lock.json into node_modules (a network request unless the npm
# cache holds them). Archivo is one variable file holding the weight and
# the width axes; IBM Plex Mono is four files, the weights 400, 500 and 600
# and the italic of 400. README.md in this folder records the Node version
# and the digests of one build.
set -euo pipefail
cd "$(dirname "$0")"
npm ci
target=../../bellman_workbench/public/fonts
mkdir -p "$target"
cp node_modules/@fontsource-variable/archivo/files/archivo-latin-standard-normal.woff2 "$target/"
cp node_modules/@fontsource-variable/archivo/LICENSE "$target/Archivo-OFL.txt"
for face in 400-normal 500-normal 600-normal 400-italic; do
  cp "node_modules/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-$face.woff2" "$target/"
done
cp node_modules/@fontsource/ibm-plex-mono/LICENSE "$target/IBM-Plex-Mono-OFL.txt"
node --version
(cd ../.. && sha256sum bellman_workbench/public/fonts/*)
