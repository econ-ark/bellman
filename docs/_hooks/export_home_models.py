"""Export the homepage diagrams: python docs/_hooks/export_home_models.py."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/_assets/home-model"
MODELS = {
    "housing": ("housing-frictions", "house_choice", 11, 24),
    "pensions": ("pension-retirement", "retire_choice", 6, 15),
    "buffer-stock": ("buffer-stock", "buffer_stock", 26, 32),
}


def export_models():
    """Export current stage declarations without numerical bindings."""
    sys.path.insert(0, str(ROOT / "packages/bellman"))
    from bellman.stage import elaborate_stage, layers_to_open, load_stage, to_model_explorer

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, (application, stage_name, first, last) in MODELS.items():
        source_path = f"applications/{application}/declaration/stages/{stage_name}/{stage_name}.bl"
        source = ROOT / source_path
        text = source.read_text(encoding="utf-8")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        excerpt = "".join(text.splitlines(keepends=True)[first - 1:last])
        if not excerpt.startswith("[id=") or not excerpt.rstrip().endswith("}"):
            raise ValueError(f"Review the forward excerpt of {source_path}.")
        stage = elaborate_stage(load_stage(str(source)))
        collection = to_model_explorer(stage)
        graph = "forward initial diagram"
        data = {
            "collection": asdict(collection),
            "graph": graph,
            "layers": list(layers_to_open(collection, graph, 1)),
            "source_path": source_path,
            "source_sha256": digest,
        }
        record = {
            "path": source_path,
            "sha256": digest,
            "text": text,
            "excerpts": {"forward": {
                "start_line": first, "end_line": last, "text": excerpt,
            }},
        }
        for filename, value in ((f"{name}.json", data), (f"{name}-source.json", record)):
            (OUTPUT / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Exported {name}: {source_path}, lines {first}–{last}.")


if __name__ == "__main__":
    export_models()
