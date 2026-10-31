"""Capture the legacy numerical reference of the portfolio–consumption notebook (spec 0.3c, P02).

The reference is the notebook's H = 5 result on the YAML stage path, recorded
once before the migration to `.bl` stages. The program:

1. compares the notebook and helper with the accepted P01 preflight record
   and stops on any difference;
2. executes a copy of the notebook through the N01 read-only runner, with a
   reviewed final cell appended to the copy that writes the five
   configurations' result arrays and an index into the kernel's working
   directory (inside the temporary root — the only writable place);
3. requires every setup and solve cell to have completed in source order;
4. writes exactly two files into the requested output directory: the NumPy
   archive and its JSON manifest with per-array provenance and the complete
   N01 execution record.

`--compare A B` compares two capture directories: archives exactly, and
manifests through a view that replaces temporary paths and the probe uuid
with tokens.

The notebook's first cell, a markdown cell, lost its last two lines, a
citation of an unpublished research note, on 28 September 2026, after the
capture; step 1 therefore stops on the notebook as it now stands, and the
reference, which is read and never regenerated, is not captured again.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np

SCHEMA_VERSION = 1
ARCHIVE_NAME = "port_cons_h5.npz"
MANIFEST_NAME = "port_cons_h5.manifest.json"
# the accepted P01 preflight record, a copy beside the reference files
PREFLIGHT = "applications/cons-port/reference/legacy/preflight.json"
RUNNER = "applications/readonly_notebook_execution.py"
REQUIRED_HORIZON = 5
EXPRESSION_ROLES = ("vfi_maximand", "inv_euler", "cntn_to_dcsn_transition",
                    "marginal_bellman", "dcsn_to_cntn_transition", "utility")
CONFIGURATIONS = (
    ("cons_only", "nest_co"),
    ("beginning_egm", "nest_br"),
    ("beginning_vfi", "nest_bv"),
    ("end_returns", "nest_er"),
    ("port_only", "nest_po"),
)
# Every code cell before the first figure cell must have completed: the setup,
# the five solves, and the semiconjugacy check. The figure cells save PNG files
# into the repository's figures/ directory, which the N01 sandbox refuses; their
# refusal is recorded in the manifest, not treated as a capture failure.
FIGURE_CELL_MARKERS = ("display_semiconj_plots(", "display_dual_plots(")
KERNEL_OUTPUT_DIRNAME = "_legacy_reference"
VFI_STRUCTURAL_ONLY_REASON = (
    "The beginning-of-period-returns run with the VFI consumption operator is recorded but "
    "excluded from numerical equality assertions: under the current inputs its values are of "
    "order 1e40, because the helper binds the consumption stage with the portfolio methods file "
    "to borrow !vfi, whose evaluate node starts the grid at k_min = 1e-10, so the candidate "
    "consumption range linspace(1e-6, m_d - 1e-6) is negative at the bottom of the grid and, "
    "with rho = 6, c^(-5) explodes (spec 0.3c section 7.3)."
)

# Reviewed Python source appended to the copied notebook only. It reads the
# five result objects the notebook already holds and writes them, with an
# index, under the kernel's working directory, which lies inside the N01
# temporary root. Nothing else is imported or computed.
FINAL_CELL_SOURCE = '''\
# spec 0.3c P02: serialize the five configurations' results (reviewed final cell)
import json as _json, os as _os
import numpy as _np
_out = _os.path.join(_os.getcwd(), "_legacy_reference")
_os.makedirs(_out, exist_ok=True)
_arrays, _index, _unserialized = {}, {}, []
_nests = [("cons_only", "nest_co", nest_co), ("beginning_egm", "nest_br", nest_br),
          ("beginning_vfi", "nest_bv", nest_bv), ("end_returns", "nest_er", nest_er),
          ("port_only", "nest_po", nest_po)]

def _is_valuefn(obj):
    return hasattr(obj, "grid") and hasattr(obj, "values") and hasattr(obj, "policy")

def _record(key, value, cfg, h, path, category):
    arr = _np.asarray(value)
    if arr.dtype == object:
        _unserialized.append({"key": key, "path": path, "repr": repr(value)[:200]})
        return
    _arrays[key] = arr
    _index[key] = {"configuration": cfg, "horizon": h, "result_object_path": path,
                   "value_category": category, "shape": list(arr.shape), "dtype": str(arr.dtype)}

def _walk(vf, key, cfg, h, path):
    _record(key + "/grid", vf.grid, cfg, h, path + ".grid", "ValueFn.grid: numpy.ndarray")
    _record(key + "/values", vf.values, cfg, h, path + ".values", "ValueFn.values: numpy.ndarray")
    if vf.dvalues is not None:
        _record(key + "/dvalues", vf.dvalues, cfg, h, path + ".dvalues", "ValueFn.dvalues: numpy.ndarray")
    for name, item in sorted((vf.policy or {}).items()):
        p = path + ".policy[" + repr(name) + "]"
        if _is_valuefn(item):
            _walk(item, key + "/policy/" + name, cfg, h, p)
        elif item is None:
            _unserialized.append({"key": key + "/policy/" + name, "path": p, "repr": "None"})
        else:
            _record(key + "/policy/" + name, item, cfg, h, p, "ValueFn.policy[" + repr(name) + "]: " + type(item).__name__)

_solution_keys = {}
for _cfg, _var, _nest in _nests:
    assert len(_nest["solutions"]) == H + 1, (_cfg, len(_nest["solutions"]))
    _solution_keys[_cfg] = [sorted(s.keys()) for s in _nest["solutions"]]
    for _h, _sol in enumerate(_nest["solutions"]):
        for _field, _vf in sorted(_sol.items()):
            _path = _var + "[\\"solutions\\"][" + str(_h) + "][" + repr(_field) + "]"
            if _vf is None:
                _unserialized.append({"key": _cfg + "/h" + str(_h) + "/" + _field, "path": _path, "repr": "None"})
                continue
            _walk(_vf, _cfg + "/h" + str(_h) + "/" + _field, _cfg, _h, _path)

_np.savez(_os.path.join(_out, "arrays.npz"), **_arrays)
with open(_os.path.join(_out, "index.json"), "w", encoding="utf-8") as _f:
    _json.dump({"H": H, "recipe": dict(recipe), "settings": settings,
                "base_params": {k: v for k, v in base_params.items()},
                "solution_keys": _solution_keys, "unserialized": _unserialized,
                "arrays": _index}, _f, indent=1, default=str, sort_keys=True)
print("LEGACY_REFERENCE_WRITTEN", len(_arrays))
'''


class CaptureError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_runner(repository: Path):
    spec = importlib.util.spec_from_file_location("readonly_notebook_execution", repository / RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_cells(notebook: Path) -> list[dict]:
    raw = json.loads(notebook.read_text(encoding="utf-8"))
    cells = []
    for i, c in enumerate(raw["cells"]):
        src = c.get("source", "")
        src = "".join(src) if isinstance(src, list) else src
        cells.append({"index": i, "id": c.get("id"), "type": c["cell_type"],
                      "first_line": src.split("\n", 1)[0] if src else "", "source": src})
    return cells


def check_against_preflight(repository: Path, notebook_relative: str, helper_relative: str) -> dict:
    """Stop unless the notebook and helper are the accepted P01 versions."""
    preflight = json.loads((repository / PREFLIGHT).read_text(encoding="utf-8"))
    accepted = next(nb for nb in preflight["notebooks"]["acceptance"] if nb["path"] == notebook_relative)
    notebook = repository / notebook_relative
    current_sha = sha256_file(notebook)
    if current_sha != accepted["sha256"]:
        raise CaptureError(f"the notebook digest {current_sha} differs from the accepted P01 record {accepted['sha256']}")
    current = [{k: c[k] for k in ("index", "id", "type", "first_line")} for c in raw_cells(notebook)]
    recorded = [{k: c[k] for k in ("index", "id", "type", "first_line")} for c in accepted["cells"]]
    if current != recorded:
        raise CaptureError("the notebook's cell inventory differs from the accepted P01 record")
    helper_record = next(e for e in preflight["acceptance_inputs"] if e["path"] == helper_relative)
    helper_sha = sha256_file(repository / helper_relative)
    if helper_sha != helper_record["sha256"]:
        raise CaptureError(f"the helper digest {helper_sha} differs from the accepted P01 record")
    return {"preflight_path": PREFLIGHT, "notebook_sha256": current_sha, "helper_sha256": helper_sha,
            "preflight_head": preflight["git"]["head"]}


def source_inventory(repository: Path, notebook_relative: str) -> dict:
    app = Path("applications/cons-port")
    syntax = app / "syntax"
    stages = ("cons", "port", "noport", "disc")

    def entry(rel: Path) -> dict:
        return {"path": str(rel), "sha256": sha256_file(repository / rel)}

    return {
        "notebook": entry(Path(notebook_relative)),
        "helper": entry(app / "code" / "ffp_utils.py"),
        "calibration": entry(syntax / "calibration.yaml"),
        "settings": entry(syntax / "settings.yaml"),
        "methods": {s: entry(syntax / "stages" / s / f"{s}_stage_methods.yml") for s in stages},
        "legacy_stages": {s: entry(syntax / "stages" / s / f"{s}_stage.yaml") for s in stages},
    }


def producing_cells(cells: list[dict]) -> dict:
    """Map each configuration's result variable to the cell that fills it."""
    out = {}
    for configuration, variable in CONFIGURATIONS:
        marker = f'{variable}["solutions"].append('
        matches = [c for c in cells if marker in c["source"]]
        if len(matches) != 1:
            raise CaptureError(f"expected exactly one cell appending to {variable}['solutions'], found {len(matches)}")
        out[configuration] = {"variable": variable, "cell_index": matches[0]["index"], "cell_id": matches[0]["id"]}
    return out


def write_archive(path: Path, arrays: dict) -> None:
    """A .npz whose bytes depend only on its arrays (fixed zip timestamps, sorted keys)."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        for key in sorted(arrays):
            buffer = io.BytesIO()
            np.lib.format.write_array(buffer, np.ascontiguousarray(arrays[key]), allow_pickle=False)
            info = zipfile.ZipInfo(key + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, buffer.getvalue())


def capture(repository: Path, notebook_relative: str, execution_dir: Path, output_dir: Path, horizon: int) -> dict:
    if horizon != REQUIRED_HORIZON:
        raise CaptureError(f"this reference is defined for horizon {REQUIRED_HORIZON} only")
    repository = repository.resolve()
    runner = load_runner(repository)
    notebook = repository / notebook_relative
    helper_relative = "applications/cons-port/code/ffp_utils.py"
    preflight_check = check_against_preflight(repository, notebook_relative, helper_relative)
    sources_before = source_inventory(repository, notebook_relative)
    cells = raw_cells(notebook)
    producers = producing_cells(cells)
    figure_cells = [c["index"] for c in cells if any(m in c["source"] for m in FIGURE_CELL_MARKERS)]
    if not figure_cells:
        raise CaptureError("no figure cell found; the required-cell boundary cannot be placed")
    last_required = min(figure_cells) - 1
    solve_cells = [p["cell_index"] for p in producers.values()]
    if max(solve_cells) > last_required:
        raise CaptureError("a solve cell follows the first figure cell; the required-cell boundary is wrong")

    output_dir = output_dir if output_dir.is_absolute() else repository / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in (ARCHIVE_NAME, MANIFEST_NAME):
        if (output_dir / name).exists():
            raise CaptureError(f"{output_dir / name} exists; the reference is generated once and never regenerated")

    execution = runner.execute_notebook_readonly(repository, notebook_relative, execution_dir,
                                                 final_cell_source=FINAL_CELL_SOURCE)

    statuses = {c["index"]: c for c in execution["cells"]}
    required = [statuses[i] for i in range(last_required + 1) if statuses[i]["cell_type"] == "code"]
    failed = [c for c in required if c["status"] != "ok"]
    if failed:
        raise CaptureError("required cells did not complete: " + ", ".join(f"{c['index']} ({c['ename']})" for c in failed))
    final_index = execution["final_cell"]["index"]
    if statuses[final_index]["status"] != "ok":
        raise CaptureError(f"the final serializing cell failed: {statuses[final_index]['ename']}: {statuses[final_index]['evalue']}")
    later = [c for c in execution["cells"] if c["index"] > last_required and c["index"] != final_index and c["cell_type"] == "code"]
    figure_refusals = [c for c in later if c["index"] in figure_cells]
    appendix = [c for c in later if c["index"] not in figure_cells]

    kernel_out = Path(execution["working_directory"]) / KERNEL_OUTPUT_DIRNAME
    with np.load(kernel_out / "arrays.npz", allow_pickle=False) as loaded:
        arrays = {k: loaded[k] for k in loaded.files}
    index = json.loads((kernel_out / "index.json").read_text(encoding="utf-8"))
    if index["H"] != REQUIRED_HORIZON:
        raise CaptureError(f"the notebook ran with H = {index['H']}, not {REQUIRED_HORIZON}")
    if tuple(index["recipe"]) != EXPRESSION_ROLES and sorted(index["recipe"]) != sorted(EXPRESSION_ROLES):
        raise CaptureError(f"the recipe has unexpected roles: {sorted(index['recipe'])}")
    if index["settings"].get("sim_seed") != 42:
        raise CaptureError(f"sim_seed is {index['settings'].get('sim_seed')!r}, not 42")

    sources_after = source_inventory(repository, notebook_relative)
    if sources_after != sources_before:
        raise CaptureError("an input digest changed during the capture")

    array_records = {}
    for key, record in index["arrays"].items():
        producer = producers[record["configuration"]]
        array_records[key] = {
            **record,
            "producing_cell": {"index": producer["cell_index"], "id": producer["cell_id"], "variable": producer["variable"]},
        }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "legacy numerical reference for spec 0.3c section 7.3; generated once, never regenerated",
        "horizon": REQUIRED_HORIZON,
        "configurations": [c for c, _ in CONFIGURATIONS],
        "producing_cells": producers,
        "seeds": {"sim_seed": index["settings"]["sim_seed"]},
        "expressions": {role: index["recipe"][role] for role in EXPRESSION_ROLES},
        "settings_as_loaded": index["settings"],
        "calibration_as_loaded": index["base_params"],
        "solution_keys": index["solution_keys"],
        "unserialized": index["unserialized"],
        "arrays": array_records,
        "archive": {"path": str(Path("applications/cons-port/reference/legacy") / ARCHIVE_NAME),
                    "count": len(arrays), "keys": sorted(arrays)},
        "sources": sources_before,
        "preflight": preflight_check,
        "vfi_structural_only_reason": VFI_STRUCTURAL_ONLY_REASON,
        "required_cells": {"last_index": last_required, "all_completed": True,
                           "note": "every code cell up to and including this index completed in source order"},
        "figure_cells": {
            "note": ("these cells save PNG files into the repository's figures/ directory; the N01 sandbox "
                     "refuses that write, so they end in PermissionError on the read-only path. The migrated "
                     "notebook (A08) must write figures under the temporary root or not at all."),
            "cells": [{k: c[k] for k in ("index", "id", "status", "ename", "evalue")} for c in figure_refusals],
        },
        "appendix_cells_after_required": {
            "note": "cells after the figure cells (the HARK appendix); their outcome is recorded, not required",
            "cells": [{k: c[k] for k in ("index", "id", "status", "ename", "evalue")} for c in appendix],
        },
        "final_cell": {"sha256": execution["final_cell_sha256"], "index": final_index,
                       "kernel_output_directory": str(kernel_out)},
        "resolved_arguments": {
            "repository": str(repository), "notebook": notebook_relative,
            "execution_dir": str(execution_dir.resolve()), "output_dir": str(output_dir), "horizon": REQUIRED_HORIZON,
        },
        "notebook_execution": execution,
    }
    write_archive(output_dir / ARCHIVE_NAME, arrays)
    manifest["archive"]["sha256"] = sha256_file(output_dir / ARCHIVE_NAME)
    (output_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                                            encoding="utf-8")
    return manifest


def canonical_manifest_view(manifest: dict) -> dict:
    """The manifest with temporary paths and the probe uuid replaced by tokens."""
    execution = manifest["notebook_execution"]
    root = execution["temporary_root"]
    repository = manifest["resolved_arguments"]["repository"]
    probe_uuid = execution["probe"]["path"].rsplit("-", 1)[-1]
    text = json.dumps(manifest, sort_keys=True)
    text = (text.replace(root, "<temporary-root>").replace(repository, "<repository>")
                .replace(probe_uuid, "<probe-uuid>"))
    view = json.loads(text)
    # execution artefacts that legitimately differ between equivalent runs
    view["notebook_execution"] = {"canonical_comparison": view["notebook_execution"]["canonical_comparison"]}
    view["resolved_arguments"].pop("output_dir")
    view["final_cell"].pop("kernel_output_directory")
    return view


def compare(dir_a: Path, dir_b: Path) -> dict:
    with np.load(dir_a / ARCHIVE_NAME, allow_pickle=False) as a, np.load(dir_b / ARCHIVE_NAME, allow_pickle=False) as b:
        keys_equal = sorted(a.files) == sorted(b.files)
        unequal = [k for k in a.files if k in b.files and not np.array_equal(a[k], b[k], equal_nan=True)]
    ma = json.loads((dir_a / MANIFEST_NAME).read_text(encoding="utf-8"))
    mb = json.loads((dir_b / MANIFEST_NAME).read_text(encoding="utf-8"))
    va, vb = canonical_manifest_view(ma), canonical_manifest_view(mb)
    differing = sorted(k for k in set(va) | set(vb) if va.get(k) != vb.get(k))
    return {
        "archive_keys_equal": keys_equal,
        "archive_arrays_unequal": unequal,
        "archive_bytes_equal": sha256_file(dir_a / ARCHIVE_NAME) == sha256_file(dir_b / ARCHIVE_NAME),
        "manifest_view_differences": differing,
        "canonical_comparison_equal": va["notebook_execution"] == vb["notebook_execution"],
        "profile_digests": [ma["notebook_execution"]["sandbox"]["profile_sha256"], mb["notebook_execution"]["sandbox"]["profile_sha256"]],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository")
    parser.add_argument("--notebook")
    parser.add_argument("--execution-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--horizon", type=int, default=REQUIRED_HORIZON)
    parser.add_argument("--compare", nargs=2, metavar=("DIR_A", "DIR_B"))
    args = parser.parse_args(argv)
    if args.compare:
        report = compare(Path(args.compare[0]), Path(args.compare[1]))
        print(json.dumps(report, indent=2))
        ok = report["archive_keys_equal"] and not report["archive_arrays_unequal"] and not report["manifest_view_differences"]
        return 0 if ok else 1
    for name in ("repository", "notebook", "execution_dir", "output_dir"):
        if getattr(args, name) is None:
            parser.error(f"--{name.replace('_', '-')} is required")
    try:
        manifest = capture(Path(args.repository), args.notebook, Path(args.execution_dir), Path(args.output_dir), args.horizon)
    except CaptureError as error:
        print(f"capture failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps({k: manifest[k] for k in ("horizon", "configurations", "seeds", "expressions", "archive")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
