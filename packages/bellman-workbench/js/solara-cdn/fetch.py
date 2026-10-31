"""Copies Solara's own interface files into Bellman Workbench's package
(model interface specification 0.4, §8 G (5); unit G, G-D12): the files of
three npm packages that the page of Solara 1.62.1 reads from a content
delivery network, which Solara serves at /_solara/cdn/ from the folder
SOLARA_ASSETS_PROXY_CACHE_DIR names, here bellman_workbench/solara-cdn/
(command.server_environment).

Each tarball is fetched from the npm registry and refused unless its digest
is the integrity recorded below. The files copied are those Solara's page
template names (solara/server/templates/solara.html.j2, lines 20, 27, 249,
251 and 286) for ipywidgets 7 and 8, every file their stylesheets name by
url(), and the application's chunks and license files; LICENSES.txt is
written beside them. Run with the repository's interpreter from any
directory: venv/bin/python packages/bellman-workbench/js/solara-cdn/fetch.py.
It prints the rows of the record in README.md."""

from __future__ import annotations

import base64
import hashlib
import io
import posixpath
import re
import shutil
import tarfile
import urllib.request
from importlib import metadata
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[2]
TARGET = WORKBENCH / "bellman_workbench" / "solara-cdn"
# the three packages, by the folder under TARGET Solara names each by, with
# the address of its tarball and the tarball's integrity as the npm
# registry records them (read on 4 October 2026)
PACKAGES = {
    "requirejs@2.3.6": (
        "https://registry.npmjs.org/requirejs/-/requirejs-2.3.6.tgz",
        "sha512-ipEzlWQe6RK3jkzikgCupiTbTvm4S0/CAU5GlgptkN5SO6F3u0UD0K18wy6ErDqiCyP4J4YYe1HuAShvsxePLg==",
    ),
    "font-awesome@4.5.0": (
        "https://registry.npmjs.org/font-awesome/-/font-awesome-4.5.0.tgz",
        "sha512-XGGY8CN/NT8e5fKOC/K7CESNQ3+2oYOfZqwZcKgEMtcmTiHtFIH+XZWRoU0HtcdwhtSkpWXLfTIUlTdJ4PhX8A==",
    ),
    "@widgetti/solara-vuetify3-app@5.2.0": (
        "https://registry.npmjs.org/@widgetti/solara-vuetify3-app/-/solara-vuetify3-app-5.2.0.tgz",
        "sha512-9UMyjf9KASR9PucZ7848upx1gqOqlUnG5Hh5or5CTaN/Um+AxAHQGwv8x4fFJzco/OaccsWdtsqb3bmYAnBo+Q==",
    ),
}
APP = "@widgetti/solara-vuetify3-app@5.2.0/dist/"
# the files the page template names, for each major version of ipywidgets
NAMED = [
    "requirejs@2.3.6/require.js",
    "font-awesome@4.5.0/css/font-awesome.min.css",
    APP + "fonts.css",
    *(APP + f"main{major}.css" for major in (7, 8)),
    *(APP + f"solara-vuetify-app{major}.min.js" for major in (7, 8)),
]
# a file a stylesheet names
URL = re.compile(r"url\(([^)]*)\)")
# a script of the application, a chunk it loads on demand, or its license file
APPLICATION = re.compile(r"(\d+\.)?solara-vuetify-app[78]\.min\.js(\.LICENSE\.txt)?")


def unpacked(folder: str, url: str, integrity: str) -> dict[str, bytes]:
    """Every file of the tarball at `url`, by its path under TARGET; refused
    unless the tarball's digest is `integrity`."""
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    algorithm, expected = integrity.split("-", 1)
    found = base64.b64encode(hashlib.new(algorithm, data).digest()).decode()
    if found != expected:
        raise SystemExit(f"{url}: {algorithm}-{found}, not the recorded {integrity}")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            if member.isfile():
                # every member stands under the archive's folder package/
                inner = member.name.split("/", 1)[1]
                files[f"{folder}/{inner}"] = archive.extractfile(member).read()
    return files


def chosen(files: dict[str, bytes]) -> list[str]:
    """The paths of the files the page reads: those NAMED, those their
    stylesheets name, and the application's chunks and license files."""
    paths = set(NAMED)
    for name in NAMED:
        if name.endswith(".css"):
            for found in URL.findall(files[name].decode("utf-8", "replace")):
                target = found.strip("'\" ").split("?")[0].split("#")[0]
                if target and not target.startswith("data:"):
                    paths.add(posixpath.normpath(posixpath.join(posixpath.dirname(name), target)))
    paths |= {p for p in files if p.startswith(APP) and APPLICATION.fullmatch(p[len(APP) :])}
    missing = sorted(paths - files.keys())
    if missing:
        raise SystemExit(f"named and not in the packages: {missing}")
    return sorted(paths)


def head(files: dict[str, bytes], path: str) -> str:
    """The comment at the head of the file `path`, which names its authors
    and its license."""
    return files[path].decode("utf-8").split("*/", 1)[0] + "*/"


def notices(files: dict[str, bytes]) -> str:
    """LICENSES.txt: for each package its folder, its declared license, the
    head comment of its file and the license's text: the MIT License as
    Solara's own distribution holds it, and the SIL Open Font License 1.1 as
    the notice of STIX Two Math beside the graph's bundle holds it. The
    three tarballs hold no license file."""
    solara = metadata.distribution("solara-ui").read_text("licenses/LICENSE")
    # the license's terms, after its title and its copyright line
    mit = solara.split("\n\n", 2)[2]
    stix = WORKBENCH / "bellman_workbench/public/flow/STIX-Two-Math-OFL.txt"
    ofl = stix.read_text(encoding="utf-8")
    ofl = ofl[ofl.index("SIL OPEN FONT LICENSE Version 1.1") :]
    sections = [
        "The license notices of Solara's own interface files, which Bellman Workbench"
        " serves from bellman_workbench/solara-cdn/, written by js/solara-cdn/fetch.py.",
        "requirejs@2.3.6\nlicense: MIT\n"
        + head(files, "requirejs@2.3.6/require.js")
        + "\n\nThe MIT License\n\nCopyright jQuery Foundation and other contributors\n\n"
        + mit,
        "font-awesome@4.5.0\nlicense: OFL-1.1 AND MIT\n"
        + head(files, "font-awesome@4.5.0/css/font-awesome.min.css")
        + "\n\nThe fonts under fonts/ are licensed under the SIL Open Font License 1.1,"
        " and the stylesheet under the MIT License.\n\n"
        + ofl
        + "\n\nThe MIT License\n\n"
        + mit,
        "@widgetti/solara-vuetify3-app@5.2.0\nlicense: MIT\n"
        "A package of Solara's repository, github.com/widgetti/solara, whose license"
        " follows; the notices of the packages its scripts hold stand beside them in"
        " dist/, solara-vuetify-app7.min.js.LICENSE.txt and"
        " solara-vuetify-app8.min.js.LICENSE.txt.\n\n" + solara,
    ]
    return "\n\n".join(sections) + "\n"


def main() -> None:
    files = {}
    for folder, (url, integrity) in PACKAGES.items():
        files.update(unpacked(folder, url, integrity))
    paths = chosen(files)
    if TARGET.exists():
        shutil.rmtree(TARGET)
    for path in paths:
        (TARGET / path).parent.mkdir(parents=True, exist_ok=True)
        (TARGET / path).write_bytes(files[path])
    (TARGET / "LICENSES.txt").write_text(notices(files), encoding="utf-8")
    total = 0
    for path in sorted(found for found in TARGET.rglob("*") if found.is_file()):
        data = path.read_bytes()
        total += len(data)
        row = f"`{path.relative_to(WORKBENCH).as_posix()}` | {len(data):,}"
        print(f"| {row} | `{hashlib.sha256(data).hexdigest()}` |")
    print(f"{len(paths) + 1} files, {total:,} bytes")


if __name__ == "__main__":
    main()
