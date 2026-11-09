"""Copy native Workbench assets for the homepage's isolated model frame."""

import hashlib
import json
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[2]
WORKBENCH = ROOT / "packages/bellman-workbench/bellman_workbench"
FOLDERS = ("flow", "fonts", "codicons", "vscode-elements", "brand")


def on_pre_build(config):
    """Refuse diagrams whose recorded stage source has changed."""
    examples = Path(config["docs_dir"]) / "_assets/home-model"
    for name in ("housing", "pensions", "buffer-stock"):
        data = json.loads((examples / f"{name}.json").read_text(encoding="utf-8"))
        record = json.loads((examples / f"{name}-source.json").read_text(encoding="utf-8"))
        source = (ROOT / record["path"]).read_bytes()
        digest = hashlib.sha256(source).hexdigest()
        if record["sha256"] != digest or data["source_sha256"] != digest or record["text"].encode("utf-8") != source:
            raise ValueError("Homepage model source changed; run python docs/_hooks/export_home_models.py.")
        excerpt = record["excerpts"]["forward"]
        if excerpt["text"] != "".join(record["text"].splitlines(keepends=True)[excerpt["start_line"] - 1:excerpt["end_line"]]):
            raise ValueError(f"The {name} source excerpt differs from its recorded lines.")


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
