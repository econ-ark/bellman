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

The selection covers ipywidgets 7 and 8: the files named in `solara/server/templates/solara.html.j2` at lines 20, 27, 249, 251 and 286, every file their stylesheets name with `url()`, and the application's additional script chunks and license files. The Font Awesome path is the default in `solara/server/settings.py`. The Workbench requires Vue 3 and runs Solara in production mode. This selection implements unit G's G-D12 and C15.

## The command

From the repository root, run `venv/bin/python packages/bellman-workbench/js/solara-cdn/fetch.py`. It fetches the three pinned archives, checks their integrity, replaces only `bellman_workbench/solara-cdn/`, writes its notices, and prints the record below. The script reads the existing Solara distribution's license and the STIX Two Math notice from the graph's package assets; it fetches no license from another site.

## The record of the fetch of 5 October 2026

| File | Bytes | SHA-256 |
|---|---:|---|
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/00b1fb69fb78ff50fd55.ttf` | 174,048 | `42d4cdf860fe35b70930ac54e8b468b3b93124798ce252441f33134855a452d4` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/02271ec5cb9f5b4588ac.woff` | 12,316 | `11e4dc8a6471ff6d6ee561d53d10fde8f7489e798257ff449c5d37c197435605` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/03074b16509774c0aa6d.woff2` | 15,340 | `c912a9ce0c3122d4b2b29ad26bfe06b0390d1a5bdaa5d6128692c0befd1dfbbd` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/06db94b5fad70e44175d.woff2` | 16,944 | `aa4650a411dfe1c9beb794ffaf08c7909cdfbb05672d79b3a9976672cbba75ec` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/073b3402d036714b4370.woff` | 10,588 | `d96cdf2b3bdd4d64a8fd5f74a4c467f123a8a73931cd435889f08ffaf9bf947a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/0c1f88355a2ec847fc41.woff` | 19,936 | `136939ae23ff6c6b2c746bac1e689475022fd4a71a9925de792a149a55295231` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/0c3b8929d377c0e9b2f3.woff` | 29,912 | `c76c5d696297d51b9cb1639c7da4334f0e7dec81b42b11213b5e25ef671bb822` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/12a47ed5fd5585f0f422.woff2` | 60,840 | `0c9a3f7fdc13a3ff04b74e9b982c28fa738fa9373bd43bd24dbca5f2dc360f24` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/155.solara-vuetify-app7.min.js` | 432,947 | `c35e1827a35f35d878839aa266dbde3355d9ebc94cfdee231ba56e14921d13df` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/172d3529b26f8cedef6b.woff2` | 11,316 | `51814d270d06ff0255dba0799994fa4d8c84d11f09951d47595f4abb1f3602dc` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/1ab7bbddcdbde1b6f274.woff2` | 15,436 | `1d5b7c64458f4af91dcfee0354be47adde1f739b5aded03a7ab6068a1bb6ca97` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/1d19ca2fdcd9bd75a7dd.woff` | 20,012 | `3bfe46bb1ca35b205306c5ec664e99e4a816f48a417b6b42e77a1f43f0bc4e7a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/20f389c4120be058d80a.woff2` | 16,780 | `99cd42a3c072d918f2f44984a807cf7aa16e13545fd0875fc07c6c65f99e715b` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/2b389797cf8bdbea58fb.woff` | 19,888 | `468e579fe1210fa55525b1c470ed2d1958404512a2dd4fb972cac5ce0ff00b1f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/2d241905f5d9b81989af.woff2` | 15,552 | `5a8c1e7681318caa29e9f44e8a6e271f6a4067a2703e9916dfd4fe9099241db7` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/2f7bc363fc5424ebda59.ttf` | 19,436 | `f36ea897e19f4a2e571d1e900e4e3710e438deb05a842486045ba0a3e616a4ad` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/306.solara-vuetify-app7.min.js` | 3,539 | `4084fda643a7862956074618717d11e764b927ae9a3014c84fabf59c95ca4513` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/354501bac435c3264834.woff` | 13,296 | `9be7ceb88004ab8ad124082246fbfcca4091e36385d4ec6ed1df67375dad50fb` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/39890742bc957b368704.woff2` | 25,324 | `0f60d1b897938ec918c8ce073092411baf9438f6739465693ff18b0f9d20b021` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/399c3cc75ca92df8083c.woff` | 21,132 | `ff0ce937f3d297f5f253b78df5eb2a03f5513be18292f2d9041439c6d9d62207` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/3f07ed67f06c720120ce.woff` | 18,668 | `850c0af5c2238497febaf5e461d880bf458c341f42f4f330f1b1ab5698b1998e` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/428978dc7837d46de091.woff` | 19,412 | `a6f7ec0d846ac7ad975adb8959c37ed49b94acbc4ae436db9ce9e20287e4a64c` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/479700ea91d964d295d7.eot` | 69,177 | `bc51f6335abbf55955ffc85a84cf3e20d86261b54f5aea9f5e2b4022c53c893c` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/4ad7c7e8bb8d10a34bb7.ttf` | 10,364 | `c647367d1dd4e162468717d020e1fc0f1dc5c26ebfdffbe55261713bf88c5877` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/4c6b94fd1d07f8beff7c.woff` | 16,028 | `e14fed02b1aba7ce9f5afd5844b5d0321b22351febc720e0de8b8723527609f7` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/4c761b3711973ab04edf.ttf` | 19,584 | `9163df9c7122432e6495b4229fa9071cf9ae86a758ae5efc4924ec2e1a6dbce1` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/4f35fbcc9ee8614c2bcc.woff` | 30,772 | `c6368d87e8a1a3a5d337623d83d8dc4b868f242a9ad476237d6f8d1e0f168cdc` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/55cf6665278898f1149c.woff` | 21,528 | `2cfe69657c55133dac6ea017b4452efff2131422abd9e90500a072df7ca5a9c8` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/57f5c1837853986ea1db.ttf` | 11,508 | `a6b2099fb555c60e3a0db3a08842ebf1d732c6eb4e4bf44913613bed4fc4e39b` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/5908ecb9ed942e5e61fa.eot` | 844,600 | `5fb8df34a3b78887e8619cae09ffd26cb1933f3d3f47789caa360667f16ad3c2` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/5b49f4993ae22d7975b4.ttf` | 24,504 | `1ece03f79f95277d57dc7f6b435a74e1379b0d46104a8530286b60ff49369ea0` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/692.solara-vuetify-app8.min.js` | 432,995 | `2d63864238ebcc06d1dd440ca45604a4d055c0c42ae03bec5a1fd8ca391b5389` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/6d3d25f4820d0da8f01f.woff2` | 16,440 | `7af58c5ec8f132a2ddde9027c6d7814decce4d3b822a11192a42a20e2e973264` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/6de7d4b539221a49e9e2.ttf` | 12,228 | `95b6d2f1a50173bfedb8c63e1d1c99b10427d0a4df4201cb44513b226951a22b` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/6fdf0ac577be0ba82a4c.woff` | 13,208 | `5e28753be717dac97f559f49bc10be9cf3c124ddcabda6659d11cb68febc6463` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/73ea273a72f4aca30ca5.woff2` | 28,076 | `0cdd387c9590a1a9f9794560022dbb59654a7d86f187aa0c81495ad42d3a7308` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/7489a2fbfb9bfe704420.ttf` | 12,368 | `07d8e303ce4fc12b4bb54f1004170dd190a1f3db45d400fe68060df3e0897268` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/7d393d382f3e7fb1c637.woff2` | 12,028 | `00b26ac825e2095056396e0553b8ac26d3f8ad158c3826e28b4c45b385c4714a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/7e873d3833eb108a0758.ttf` | 12,344 | `ed0b74372feefcbb9c0666b2e210da37b7e49fa7fbbf3eeb11db5f693dacfbb7` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/815babffe97b00a1f30b.woff2` | 15,440 | `eca8ffa764a66cd084800e2e71c4176ef089ebd805515664a6cb8d4fb3b598bf` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/8169508bf58f8bd92ad8.ttf` | 51,336 | `138ac28d1663b3037e9c5f52371fa5c63d8324f4a38d22cd573e6ea3a3fd0cf8` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/828abcb200061cffbaae.ttf` | 32,968 | `70ee1f64a20f2048c21940ef46d0144fd215baa953ca69afd1e31e98544f708f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/853be92419a6c3766b9a.ttf` | 63,632 | `68534840bcfdd2bffb6f0e8deb48684dd01e7f04ea2813267577afb906de1d13` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/872.solara-vuetify-app8.min.js` | 3,590 | `daeba39b80150d33b9eded009da40529758503581db76c4313e055b1935db67c` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/89323fb7fad1b22f5923.woff2` | 17,124 | `f35f6616aa2148b09cbdefd3aec6d3d3e94b83327346ef0d5cdac2e3b6537526` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/8a5f936332e8028c7278.ttf` | 31,308 | `08ce98e51b04d58945a301e639e02b6998af29fdfd61a7b8afdd07bbfc479d4a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/8d593cfaa96238d5e2f8.woff` | 14,112 | `91ee67500cc0129aa0ace3ac5c61ff1692102f0f31d02b69347fba35dcb75bf2` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/931d67ea207ab37ee693.woff2` | 11,348 | `74444efd593c005e3f4573b44524704c0af0a937fe911cca9e94068d0d140d3f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/941530f23d86c39ba672.woff2` | 15,316 | `6309b0265edb8a409b1a120036a651230824b326e26a5f24eca1b9f544e2a42f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/95591a929f0d32aa282a.woff2` | 12,216 | `e99ae51144bf1232efcc1bfe5add36262c6866b0faab24fa75740e1b98577a62` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/96759856b4e70f3a8338.woff` | 18,748 | `8a8d244581371912b8f3f5a23e2437cb2a59cd9bcaebb0346e722c05737a2571` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/9d267b4b73e6ea5bb396.woff2` | 16,644 | `6fe8b4e5a73712c3fd3b99d6f61cc39c0546a9b93291e6c80beb5f399eb25424` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/9d37d7cdb0c45a07e980.woff` | 21,268 | `cfcb9a5ffdd06bd66618756360ba3dadda497d92b687304ca942bed02b72ab70` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/9eba1d77abcf2aa6e94e.ttf` | 53,580 | `d0332f52868370fd83ae7fa46470f90c8f2eab2fcf12bc4f88080b340c95a830` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/a4fa71c6483584debf08.woff` | 21,856 | `ecac75bfaf3df79cc8b13f735c7f08cb006d47f039a68524284b34deba2c997c` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/ae5f802c41ddc61a6c12.woff2` | 17,156 | `3876391b89d4721d89ebcedd0798bf7705ea1ad285fa6cad487fb88c1d6042a8` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/b257a18c016f37ee4543.ttf` | 22,364 | `3931dd81faed86ba021bb2bbdc36f5bed9a38d6b4f4077aca59b265aa1b02083` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/b9cd458ac6d5889ff9c3.woff` | 14,408 | `ece03cfd83e22c212cdef66feb8442d25a083beb988db3f1883f3f9738d750ba` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/bbe05489cd38a31d1694.ttf` | 844,380 | `ed23537da2cc192dbbcd49c7440ae7918453b411ddc7e5b3ca67d4228bbbb06f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/bf2d440b3a42ea78a998.ttf` | 31,196 | `f9377ab0271cda59af24bcffbd46a4d0c8a3572ffafdbb38de2ad5ea7b0d5ee5` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/c295e7f71970f03c0549.woff2` | 13,568 | `71d517d67827787cfabdf186914cc3358eda539e37931941f2b2fd4a21f68c0b` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/c5c02d763c89380dcb4e.ttf` | 27,556 | `f01f3e87d9c6a61c0c081ceb577abd864eb00a612f7ac1620dd6915fad2ef5aa` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/c81d1b2a4b75d3eded60.woff2` | 9,644 | `036d4e95149b69ff9bcc0cd55771efeb25ffa3947293e69acd78d5ac328c684b` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/cb41c1e71debe927815c.woff2` | 15,344 | `3e253b66056519aa065b00a453bac37ac5ed8f3e6fe7b542e93a9dcdcc11d0bc` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/cd5e231e0cc53b2cb2c0.woff2` | 10,344 | `68e8c73ef42afd3ccec58bf0fba302cce448938e7fc020a5e31f8a952eee1342` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/d4c409dfe110747b1763.woff` | 19,916 | `3ab30e780c8b0bcc4998b838a5b30c3bfe28edead312906dc3c12271fae0699a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/d562e886c52f12660a41.woff` | 33,516 | `30da91e84c893f875e252689faebdc590b2871145e8adc7f9a9d4dbd8ce0b251` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/d8ba12774e48a5a73c24.woff2` | 16,572 | `756f65bc72ad18ac281e8ef320de3347f26d402701aeb8f659f33ffb8f036ccb` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/d9f39587ab2751b33bcf.woff2` | 283,040 | `3248c66efa5ff60a1088aa4ab9d39b395fcc2e77e03ae454621885aa1017f3a8` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/da9606b68b5c8ac55cfb.woff` | 404,384 | `58aab5f73138d701a07088a9d4fd015505d1ed58a19804954e155322f5e794de` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/dcbcbd93bac0470b462d.woff2` | 16,400 | `dc47344dbb6cb5b655c8460d561f4df5f501b90c804ad3c6cec65fe322351ab1` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/eab8651ccfe511d144fd.woff` | 19,936 | `48433679240732ed1a9b98e195a75785607795037757e3571ff91878a20a93b2` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/ed305b5434865e06ffde.ttf` | 19,572 | `1e6f9579e90e2cac37f8f60a597c436e075c114385652b7cbeb0dec0421291b3` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/f27d09b1ffc7796288d3.woff` | 21,564 | `c8912ebd82b4df2eb87e37b1f66432fa2186182e08bb8a533ba4c2df6ce67fba` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/f2a0933406f783065152.woff` | 79,612 | `4c463e02509bd9ab8787f6e37f2e926d405e5e22be38643264746c4ddc6755cb` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/f650f111a3b890d116f1.woff2` | 26,272 | `c2342cd8b869e01752a9321dc17213fc40d4d04c79688c1d43f2cf316abd7866` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/f9ca3454c3a66edb5a81.woff2` | 16,940 | `a44484ecc8b7aa5da1603d6a7256d3eea3c5c8e5c6f50bcdb220b303e4b2010a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fa675e5e4bec9eb250b6.ttf` | 33,580 | `0d85ae7cc30f23790a7f1a58c4a112fdca8aae769b6ba11429af1d98b1b6cb3a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fbebe70817c0f48eb4ee.woff` | 19,824 | `1570f866bf6eae82041e407280894a86ad2b8b275e01908ae156914dc693a4ed` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fbf369016a137c8f7460.woff` | 21,776 | `96e0bf768fc3c6fdb04c5d11aa1a63080b27bd48754444ac10d449886720af78` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fc9ba5249878cd8f8d88.ttf` | 16,648 | `1c67f068fea8bb09bf099c088b1cf64bd27516a6e07f4684344873564bb66a67` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fd947498bc16392e76c2.woff` | 19,676 | `f1d6ef86f3b11a528bd5185199bd2443ecb2b0dead96d88674b5a2c12be24bdf` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fe2176f79edaa716e621.woff2` | 16,988 | `97479ca6cce906abc961ecac96faa5f9ca2e61b8e7670d475826bcdee9a7c267` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/fonts.css` | 358,991 | `a2a7e767994b322d030a4b7a6f7b622948b4bbcef9b33be64a044d526a0b157a` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/main7.css` | 995,932 | `1d2c47eca7ad1e0e0cb8ea07e2ca524061ab718db7809c22ede91ccb2d4647bb` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/main8.css` | 1,024,101 | `189800ae3ca8b00ac15080ef80f5de89fb7f283584a9c6afb9d51b97dfd02b1f` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/solara-vuetify-app7.min.js` | 3,702,226 | `f21ee1db4a47c3ff9fe446afd413f69420896e1f78236b5eb715dc8f1591254e` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/solara-vuetify-app7.min.js.LICENSE.txt` | 4,555 | `cdeb43493a7a7b79e3fc6829689d08fc61c6103d4ca880c78bf1729951afdadd` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/solara-vuetify-app8.min.js` | 3,898,817 | `7992f32ba41c3d3c4f4221429f404c07b84e226354e62e431c8ffbdaa7cd4fcd` |
| `bellman_workbench/solara-cdn/@widgetti/solara-vuetify3-app@5.2.0/dist/solara-vuetify-app8.min.js.LICENSE.txt` | 3,835 | `0bb98850bf294a4a80b411b27194cb3ae8ae8b33da240a7bbbe697ef6c81d553` |
| `bellman_workbench/solara-cdn/LICENSES.txt` | 8,299 | `eb4434f897fcc9f0c7b3f2f0b47e19d08c6b7e2e77c7015173d55438324bc244` |
| `bellman_workbench/solara-cdn/font-awesome@4.5.0/css/font-awesome.min.css` | 27,466 | `ddd92f10ad162c7449eff0acaf40598c05b1111739587edb75e5326b6697c5d5` |
| `bellman_workbench/solara-cdn/font-awesome@4.5.0/fonts/fontawesome-webfont.eot` | 70,807 | `e219ece8f4d3e4ac455ef31cd3a7c7b5057ea68a109937fc26b03c6e99ee9322` |
| `bellman_workbench/solara-cdn/font-awesome@4.5.0/fonts/fontawesome-webfont.svg` | 365,616 | `d67041fe5d50eef9ef671643968f7ce6b130eaaaaa2ce4d496b18d0a33aeb87b` |
| `bellman_workbench/solara-cdn/font-awesome@4.5.0/fonts/fontawesome-webfont.ttf` | 142,072 | `7b5a4320fba0d4c8f79327645b4b9cc875a2ec617a557e849b813918eb733499` |
| `bellman_workbench/solara-cdn/font-awesome@4.5.0/fonts/fontawesome-webfont.woff` | 83,588 | `c812ddc9e475d3e65d68a6b3b589ce598a2a5babb7afc55477d59215c4a38a40` |
| `bellman_workbench/solara-cdn/font-awesome@4.5.0/fonts/fontawesome-webfont.woff2` | 66,624 | `ff82aeed6b9bb6701696c84d1b223d2e682eb78c89117a438ce6cfea8c498995` |
| `bellman_workbench/solara-cdn/requirejs@2.3.6/require.js` | 86,483 | `9485f0917f97fcf4f63a5ea365200ffd57f123f451382a2f9a1ad2e2fd51ac9b` |

98 files, 15,912,488 bytes. Of these, 97 are selected package files totaling 15,904,189 bytes; `LICENSES.txt` is 8,299 bytes.

## The notices

`LICENSES.txt` names each package folder and its declared license. It preserves the author and license comments of RequireJS and Font Awesome, the MIT text from the installed `solara-ui` distribution, and the SIL Open Font License 1.1 text from the STIX Two Math notice for Font Awesome's fonts. The Solara application's two `LICENSE.txt` files stand beside its scripts and retain the notices of their included packages. The archives contain no separate top-level license file. These local notices and the fetch record accompany the installed files.
