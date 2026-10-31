---
title: The build of the text fonts
audience: developer
type: index
topic: [user-interface]
---

# The build of the text fonts

This folder is the one recipe for the text fonts of Bellman Workbench, Archivo and IBM Plex Mono. It records the seven files it copies to `../../bellman_workbench/public/fonts/`, which Solara serves at `static/assets/fonts/`, so that every runtime font is served locally (model interface specification 0.4, §5.2; R-D1, R-D22). `brand.css` declares each font file in an `@font-face` rule. The mathematics font, STIX Two Math, stays beside the graph's bundle in `../../bellman_workbench/public/flow/` (§7) and is copied by `../flow/build.sh`.

## The sources

`package.json` pins two Fontsource packages at exact versions, and `package-lock.json` fixes them; neither package has a dependency. Fontsource takes both fonts from Google Fonts (`https://github.com/google/fonts`), as each package's `metadata.json` states.

| Font | Package | Version | Google Fonts version | License | Copyright |
|---|---|---|---|---|---|
| Archivo | `@fontsource-variable/archivo` | 5.3.0 | v25 | SIL Open Font License 1.1 | 2020 The Archivo Project Authors |
| IBM Plex Mono | `@fontsource/ibm-plex-mono` | 5.3.0 | v20 | SIL Open Font License 1.1 | 2017 IBM Corp. |

Archivo is the variable package's one file of the Latin subset, `archivo-latin-standard-normal.woff2`, which holds the weight axis from 100 to 900 and the width axis from 62 to 125 percent; it is served alone, and `brand.css` declares it with `font-weight: 100 900` and `font-stretch: 62% 125%` (R-D2). IBM Plex Mono is four files of the Latin subset: the weights 400, 500 and 600, and the italic of 400. Each package's `LICENSE` is copied beside its files as `Archivo-OFL.txt` and `IBM-Plex-Mono-OFL.txt`.

## The command

With Node 22 and npm, run `bash build.sh` from this folder. The script installs the lockfile with `npm ci` and copies the seven files to `../../bellman_workbench/public/fonts/`. Set `npm_config_cache` to choose a cache folder. Registry access is needed unless the cache holds the packages. `node_modules/` is not tracked.

## The record of the build

Built on 6 October 2026 with Node v22.17.1, npm 10.9.2, macOS (darwin-arm64). Lockfile version 3, 2 packages under `node_modules/`; lockfile SHA-256 `9e4484cadecf14f08791948f810d67d180990dec1485139ba3dcc64d820dc0da`.

| File | Bytes | SHA-256 |
|---|---:|---|
| `bellman_workbench/public/fonts/Archivo-OFL.txt` | 4,503 | `c3c8402eec0e31dc9a76851235b1c02a0bb821488b2db8e35bcc2ab60ca8fc2b` |
| `bellman_workbench/public/fonts/IBM-Plex-Mono-OFL.txt` | 5,299 | `23b0a9d0c6d3f140a0b77e483c5cfa6bba574325ef5cb189ed9f2fec4884533f` |
| `bellman_workbench/public/fonts/archivo-latin-standard-normal.woff2` | 90,104 | `e3a28eade21a900c7155a247757f4b2834c07bb7ef07ad7efa55cebaac1e8f5e` |
| `bellman_workbench/public/fonts/ibm-plex-mono-latin-400-italic.woff2` | 16,448 | `0840095faae86403735a8c04014b72cb29e7923646b222b360b7e8252932e4e3` |
| `bellman_workbench/public/fonts/ibm-plex-mono-latin-400-normal.woff2` | 14,708 | `08949f728dc52d528e69b1667d15c89a5686a4ee9a296ff90983985f99c380f7` |
| `bellman_workbench/public/fonts/ibm-plex-mono-latin-500-normal.woff2` | 14,888 | `01d285447409c8a588692162439a038b8cbd7871309ee20267b0d2d91c6e8e22` |
| `bellman_workbench/public/fonts/ibm-plex-mono-latin-600-normal.woff2` | 15,620 | `0d1f0b8d0722224e32e9f28261bdc86c79115be73444ae5eceb73976a1bcdf83` |

The 400 file of IBM Plex Mono and its license have the bytes of the two files that `../flow/build.sh` copied to `public/flow/` before this recipe took them over. No build on another platform was checked.

## The seven symbols

The page prints Υ, ≺, ∼, ≻, ρ, Γ and ℝ in running heads, perch titles and source text. Which of them each file holds was measured with fontTools 4.66 on every subset of the two packages: the `.woff` copies of IBM Plex Mono's `latin`, `latin-ext`, `cyrillic`, `cyrillic-ext` and `vietnamese` subsets, Archivo's `latin`, `latin-ext` and `vietnamese` files, the five served files, and STIX Two Math's served file. The environment's Python has no `brotli` module, which fontTools needs to read a `.woff2` file, so each `.woff2` file was decompressed by Node's `zlib.brotliDecompressSync`; for the 400 file of IBM Plex Mono, that reading and the reading of the package's `.woff` copy agree.

No file of Archivo or of IBM Plex Mono, served or not, holds any of the seven, and neither package has a Greek or a mathematical subset; so no further subset is served. STIX Two Math's served file holds all seven, and each of the four font stacks of `brand.css` names STIX Two Math directly after its first face. The browser therefore draws each of the seven in STIX Two Math wherever Archivo or IBM Plex Mono stands first.

| Symbol | Drawn in | Advance width in STIX Two Math |
|---|---|---:|
| Υ | STIX Two Math | 0.647 em |
| ≺ | STIX Two Math | 0.720 em |
| ∼ | STIX Two Math | 0.720 em |
| ≻ | STIX Two Math | 0.720 em |
| ρ | STIX Two Math | 0.515 em |
| Γ | STIX Two Math | 0.569 em |
| ℝ | STIX Two Math | 0.729 em |

Every character of IBM Plex Mono is 0.600 em wide, so a symbol drawn in STIX Two Math is not one `ch` wide in source text: at 12.5 px, one `ch` is 7.5 px and ℝ is 9.1 px.
