---
title: Solara's own interface files in the package
audience: developer
type: index
topic: [user-interface]
---

# Solara's own interface files in the package

## The sources

These files are the local copies of the three packages named by Solara 1.62.1's page template for its Vue 3 application. Each archive is refused unless its SHA-512 integrity matches the value below, recorded from the npm registry on 4 October 2026.

| Package folder | Archive | SHA-512 integrity |
|---|---|---|
| `requirejs@2.3.6` | [https://registry.npmjs.org/requirejs/-/requirejs-2.3.6.tgz](https://registry.npmjs.org/requirejs/-/requirejs-2.3.6.tgz) | `sha512-ipEzlWQe6RK3jkzikgCupiTbTvm4S0/CAU5GlgptkN5SO6F3u0UD0K18wy6ErDqiCyP4J4YYe1HuAShvsxePLg==` |
| `font-awesome@4.5.0` | [https://registry.npmjs.org/font-awesome/-/font-awesome-4.5.0.tgz](https://registry.npmjs.org/font-awesome/-/font-awesome-4.5.0.tgz) | `sha512-XGGY8CN/NT8e5fKOC/K7CESNQ3+2oYOfZqwZcKgEMtcmTiHtFIH+XZWRoU0HtcdwhtSkpWXLfTIUlTdJ4PhX8A==` |
| `@widgetti/solara-vuetify3-app@5.2.0` | [https://registry.npmjs.org/@widgetti/solara-vuetify3-app/-/solara-vuetify3-app-5.2.0.tgz](https://registry.npmjs.org/@widgetti/solara-vuetify3-app/-/solara-vuetify3-app-5.2.0.tgz) | `sha512-9UMyjf9KASR9PucZ7848upx1gqOqlUnG5Hh5or5CTaN/Um+AxAHQGwv8x4fFJzco/OaccsWdtsqb3bmYAnBo+Q==` |

The selection covers ipywidgets 8. It holds the files named in `solara/server/templates/solara.html.j2` at lines 20, 27, 249, 251 and 286, every file their stylesheets name with `url()`, and the application's additional script chunks and license file. Two groups of files are left out, and a section below describes each: the files for ipywidgets 7, and the font sources that no browser able to run the page requests. The Font Awesome path is the default in `solara/server/settings.py`. The Workbench requires Vue 3 and runs Solara in production mode. This selection implements unit G's G-D12 and C15.

## The version of ipywidgets

ipywidgets is the widget library that Solara builds on. Solara's page names its stylesheet and its script by the major version of the installed ipywidgets (`solara/server/server.py`, line 35, and lines 20 and 251 of the template). Under version 7 the page asks for `main7.css` and `solara-vuetify-app7.min.js`. Under version 8 it asks for `main8.css` and `solara-vuetify-app8.min.js`.

Since 15 November 2026 the package requires `ipywidgets>=8` (`pyproject.toml`), and `fetch.py` copies the files for version 8 alone. The five files for version 7 are left out, 5,139,199 bytes: the script, its two chunks, its license file and the stylesheet.

If the page ran under ipywidgets 7, it would ask for those files. Solara would then fetch them from its content delivery network and write them into `bellman_workbench/solara-cdn/`.

## The font sources left out

A stylesheet offers each font face in two to five formats. A browser requests the first source whose format it reads.

Since 15 November 2026 the function `fallback_sources` of `fetch.py` leaves out the sources that no browser able to run the page requests. They are 55 files, 4,097,656 bytes, in the Embedded OpenType, TrueType, WOFF and SVG formats.

In each of the 35 `@font-face` rules of the three stylesheets the source that stays is in the WOFF2 format. It is a file in 29 rules, and data written in the stylesheet in 6.

Leaving the other sources out is safe because every browser that can run the page reads WOFF2. Solara's scripts use the optional chaining operator `?.`. Chrome and Edge read that operator from version 80, Firefox from 74 and Safari from 13.1, and each of those versions reads WOFF2.

No stylesheet is rewritten, so each still names the files left out. If a client asked for one of them, Solara would fetch it from its content delivery network and write it into `bellman_workbench/solara-cdn/` (`get_path` in `solara/server/cdn_helper.py`). With the network closed that fetch fails, and the client receives no file.

## The command

From the repository root, run `venv/bin/python packages/bellman-workbench/js/solara-cdn/fetch.py`. It fetches the three pinned archives, checks their integrity, replaces only `bellman_workbench/solara-cdn/`, writes its notices, and prints the record below. The script reads the existing Solara distribution's license and the STIX Two Math notice from the graph's package assets; it fetches no license from another site.

## The record of the fetch of 15 November 2026

| File | Bytes | SHA-256 |
|---|---:|---|
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/03074b16509774c0aa6d.woff2` | 15,340 | `c912a9ce0c3122d4b2b29ad26bfe06b0390d1a5bdaa5d6128692c0befd1dfbbd` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/06db94b5fad70e44175d.woff2` | 16,944 | `aa4650a411dfe1c9beb794ffaf08c7909cdfbb05672d79b3a9976672cbba75ec` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/12a47ed5fd5585f0f422.woff2` | 60,840 | `0c9a3f7fdc13a3ff04b74e9b982c28fa738fa9373bd43bd24dbca5f2dc360f24` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/172d3529b26f8cedef6b.woff2` | 11,316 | `51814d270d06ff0255dba0799994fa4d8c84d11f09951d47595f4abb1f3602dc` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/1ab7bbddcdbde1b6f274.woff2` | 15,436 | `1d5b7c64458f4af91dcfee0354be47adde1f739b5aded03a7ab6068a1bb6ca97` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/20f389c4120be058d80a.woff2` | 16,780 | `99cd42a3c072d918f2f44984a807cf7aa16e13545fd0875fc07c6c65f99e715b` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/2d241905f5d9b81989af.woff2` | 15,552 | `5a8c1e7681318caa29e9f44e8a6e271f6a4067a2703e9916dfd4fe9099241db7` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/39890742bc957b368704.woff2` | 25,324 | `0f60d1b897938ec918c8ce073092411baf9438f6739465693ff18b0f9d20b021` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/692.solara-vuetify-app8.min.js` | 432,995 | `2d63864238ebcc06d1dd440ca45604a4d055c0c42ae03bec5a1fd8ca391b5389` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/6d3d25f4820d0da8f01f.woff2` | 16,440 | `7af58c5ec8f132a2ddde9027c6d7814decce4d3b822a11192a42a20e2e973264` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/73ea273a72f4aca30ca5.woff2` | 28,076 | `0cdd387c9590a1a9f9794560022dbb59654a7d86f187aa0c81495ad42d3a7308` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/7d393d382f3e7fb1c637.woff2` | 12,028 | `00b26ac825e2095056396e0553b8ac26d3f8ad158c3826e28b4c45b385c4714a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/815babffe97b00a1f30b.woff2` | 15,440 | `eca8ffa764a66cd084800e2e71c4176ef089ebd805515664a6cb8d4fb3b598bf` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/872.solara-vuetify-app8.min.js` | 3,590 | `daeba39b80150d33b9eded009da40529758503581db76c4313e055b1935db67c` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/89323fb7fad1b22f5923.woff2` | 17,124 | `f35f6616aa2148b09cbdefd3aec6d3d3e94b83327346ef0d5cdac2e3b6537526` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/931d67ea207ab37ee693.woff2` | 11,348 | `74444efd593c005e3f4573b44524704c0af0a937fe911cca9e94068d0d140d3f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/941530f23d86c39ba672.woff2` | 15,316 | `6309b0265edb8a409b1a120036a651230824b326e26a5f24eca1b9f544e2a42f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/95591a929f0d32aa282a.woff2` | 12,216 | `e99ae51144bf1232efcc1bfe5add36262c6866b0faab24fa75740e1b98577a62` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/9d267b4b73e6ea5bb396.woff2` | 16,644 | `6fe8b4e5a73712c3fd3b99d6f61cc39c0546a9b93291e6c80beb5f399eb25424` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/ae5f802c41ddc61a6c12.woff2` | 17,156 | `3876391b89d4721d89ebcedd0798bf7705ea1ad285fa6cad487fb88c1d6042a8` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/c295e7f71970f03c0549.woff2` | 13,568 | `71d517d67827787cfabdf186914cc3358eda539e37931941f2b2fd4a21f68c0b` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/c81d1b2a4b75d3eded60.woff2` | 9,644 | `036d4e95149b69ff9bcc0cd55771efeb25ffa3947293e69acd78d5ac328c684b` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/cb41c1e71debe927815c.woff2` | 15,344 | `3e253b66056519aa065b00a453bac37ac5ed8f3e6fe7b542e93a9dcdcc11d0bc` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/cd5e231e0cc53b2cb2c0.woff2` | 10,344 | `68e8c73ef42afd3ccec58bf0fba302cce448938e7fc020a5e31f8a952eee1342` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/d8ba12774e48a5a73c24.woff2` | 16,572 | `756f65bc72ad18ac281e8ef320de3347f26d402701aeb8f659f33ffb8f036ccb` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/d9f39587ab2751b33bcf.woff2` | 283,040 | `3248c66efa5ff60a1088aa4ab9d39b395fcc2e77e03ae454621885aa1017f3a8` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/dcbcbd93bac0470b462d.woff2` | 16,400 | `dc47344dbb6cb5b655c8460d561f4df5f501b90c804ad3c6cec65fe322351ab1` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/f650f111a3b890d116f1.woff2` | 26,272 | `c2342cd8b869e01752a9321dc17213fc40d4d04c79688c1d43f2cf316abd7866` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/f9ca3454c3a66edb5a81.woff2` | 16,940 | `a44484ecc8b7aa5da1603d6a7256d3eea3c5c8e5c6f50bcdb220b303e4b2010a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fe2176f79edaa716e621.woff2` | 16,988 | `97479ca6cce906abc961ecac96faa5f9ca2e61b8e7670d475826bcdee9a7c267` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fonts.css` | 358,991 | `a2a7e767994b322d030a4b7a6f7b622948b4bbcef9b33be64a044d526a0b157a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/main8.css` | 1,024,101 | `189800ae3ca8b00ac15080ef80f5de89fb7f283584a9c6afb9d51b97dfd02b1f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/solara-vuetify-app8.min.js` | 3,898,817 | `7992f32ba41c3d3c4f4221429f404c07b84e226354e62e431c8ffbdaa7cd4fcd` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/solara-vuetify-app8.min.js.LICENSE.txt` | 3,835 | `0bb98850bf294a4a80b411b27194cb3ae8ae8b33da240a7bbbe697ef6c81d553` |
| `bellman_workbench/solara-cdn/LICENSES.txt` | 8,259 | `9de630c062601c83ef386e6f5288d7cff4021ba9f350dd4b7cafd4a43e6da9e7` |
| `bellman_workbench/solara-cdn/font-awesome@4.5.0/css/font-awesome.min.css` | 27,466 | `ddd92f10ad162c7449eff0acaf40598c05b1111739587edb75e5326b6697c5d5` |
| `bellman_workbench/solara-cdn/font-awesome@4.5.0/fonts/fontawesome-webfont.woff2` | 66,624 | `ff82aeed6b9bb6701696c84d1b223d2e682eb78c89117a438ce6cfea8c498995` |
| `bellman_workbench/solara-cdn/requirejs@2.3.6/require.js` | 86,483 | `9485f0917f97fcf4f63a5ea365200ffd57f123f451382a2f9a1ad2e2fd51ac9b` |

38 files, 6,675,593 bytes. Of these, 37 are selected package files totaling 6,667,334 bytes; `LICENSES.txt` is 8,259 bytes.

The fetch of 5 October 2026 copied 98 files, 15,912,488 bytes. Of the 38 files of this record, 37 hold the same bytes as on that day. `LICENSES.txt` differs in one sentence, which names the one license file that now stands beside the application's scripts. The other 60 files of that day are now left out: the 55 font sources and the five files for ipywidgets 7.

## The notices

`LICENSES.txt` names each package folder and its declared license. It preserves the author and license comments of RequireJS and Font Awesome, the MIT text from the installed `solara-ui` distribution, and the SIL Open Font License 1.1 text from the STIX Two Math notice for Font Awesome's fonts. The Solara application's `LICENSE.txt` file stands beside its scripts and retains the notices of the packages they include. The archives contain no separate top-level license file. These local notices and the fetch record accompany the installed files.
