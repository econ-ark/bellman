"""Copy native Workbench assets for the homepage's isolated model frame."""

import hashlib
import json
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[2]
WORKBENCH = ROOT / "packages/bellman-workbench/bellman_workbench"
FOLDERS = ("flow", "fonts", "codicons", "vscode-elements", "brand")
GRAPHS = {"backward initial diagram", "forward initial diagram", "backward", "forward"}
SOURCE_DISPLAY_FILES = (
    "packages/bellman-workbench/js/codemirror/src/hidden_types.js",
    "packages/bellman-workbench/bellman_workbench/public/codemirror/bellman-workbench.js",
)


def check_source_display(record, native_sha256, name):
    """Check native file digests and source ranges measured in UTF-16 units."""
    display = record.get("display")
    if not isinstance(display, dict) or display.get("native_sha256") != native_sha256:
        raise ValueError(f"The {name} source display changed; run python docs/_hooks/export_home_models.py.")
    lines = re.split(r"\r\n?|\n", record["text"])
    for kind in ("types", "notes"):
        ranges = display.get(kind)
        if not isinstance(ranges, list):
            raise ValueError(f"The {name} source display needs {kind} ranges.")
        previous = (0, 0)
        for span in ranges:
            if not isinstance(span, dict):
                raise ValueError(f"The {name} source display has an invalid {kind} range.")
            line, first, last = (span.get(key) for key in ("line", "from", "to"))
            if (
                any(type(value) is not int for value in (line, first, last))
                or not 1 <= line <= len(lines)
                or not 0 <= first < last
                or (line, first) < previous
            ):
                raise ValueError(f"The {name} source display has an invalid {kind} range.")
            encoded = lines[line - 1].encode("utf-16-le")
            if last * 2 > len(encoded):
                raise ValueError(f"The {name} source display has an invalid {kind} range.")
            try:
                text = encoded[first * 2:last * 2].decode("utf-16-le")
            except UnicodeDecodeError as error:
                raise ValueError(f"The {name} source display splits a Unicode character.") from error
            if kind == "notes" and span.get("text") != text:
                raise ValueError(f"The {name} note differs from its recorded source range.")
            previous = (line, last)


def on_pre_build(config):
    """Check the recorded source, four diagrams and their opening layers."""
    examples = Path(config["docs_dir"]) / "_assets/home-model"
    native_sha256 = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in SOURCE_DISPLAY_FILES
    }
    for name in ("housing", "pensions", "buffer-stock"):
        data = json.loads((examples / f"{name}.json").read_text(encoding="utf-8"))
        record = json.loads((examples / f"{name}-source.json").read_text(encoding="utf-8"))
        source = (ROOT / record["path"]).read_bytes()
        digest = hashlib.sha256(source).hexdigest()
        if record["sha256"] != digest or data["source_sha256"] != digest or record["text"].encode("utf-8") != source:
            raise ValueError("Homepage model source changed; run python docs/_hooks/export_home_models.py.")
        if data["source_path"] != record["path"]:
            raise ValueError(f"The {name} diagram and source name different stage files.")
        excerpt = record["excerpts"]["forward"]
        if excerpt["text"] != "".join(record["text"].splitlines(keepends=True)[excerpt["start_line"] - 1:excerpt["end_line"]]):
            raise ValueError(f"The {name} source excerpt differs from its recorded lines.")
        check_source_display(record, native_sha256, name)
        graphs = data["collection"]["graphs"]
        if len(graphs) != len(GRAPHS) or {graph["id"] for graph in graphs} != GRAPHS:
            raise ValueError(f"The {name} collection must contain both initial and both operator diagrams.")
        if data["graph"] not in GRAPHS:
            raise ValueError(f"The {name} opening diagram is missing from its collection.")
        layers = data["layers"]
        if not isinstance(layers, dict) or set(layers) != GRAPHS:
            raise ValueError(f"The {name} collection needs opening layers for each diagram.")
        for graph in graphs:
            namespaces = {
                node["namespace"].split("/")[0]
                for node in graph["nodes"] if node.get("namespace")
            }
            opened = layers[graph["id"]]
            if (
                not isinstance(opened, list)
                or any(not isinstance(layer, str) for layer in opened)
                or len(opened) != len(set(opened))
                or set(opened) != namespaces
            ):
                raise ValueError(f"The {name} {graph['id']} opening layers differ from its namespaces.")


def on_post_build(config):
    """Copy native bundles, fonts and licences without rebuilding them."""
    destination = Path(config["site_dir"]) / "_assets/workbench"
    for folder in FOLDERS:
        shutil.copytree(WORKBENCH / "public" / folder, destination / folder, dirs_exist_ok=True)
    css = (WORKBENCH / "brand.css").read_text(encoding="utf-8")
    css = css.replace('url("static/assets/', 'url("').replace("url('static/assets/", "url('")
    (destination / "graph.css").write_text(css, encoding="utf-8")
    for stylesheet in (destination / "graph.css", destination / "flow/base.css", destination / "codicons/codicon.css"):
        for url in re.findall(r"url\(\s*[\"']?([^\"')]+)", stylesheet.read_text(encoding="utf-8")):
            if not url.startswith(("data:", "http:", "https:", "#")):
                target = stylesheet.parent / url.split("?")[0].split("#")[0]
                if not target.is_file():
                    raise FileNotFoundError(f"Homepage stylesheet asset is missing: {target}")
