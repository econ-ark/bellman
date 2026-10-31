"""The legacy numerical reference for the portfolio–consumption notebook (spec 0.3c, P02).

The reference is the one-time record of the notebook's H = 5 results on the
YAML stage path before the migration to `.bl` stages. These tests read the
two reference files; they never regenerate them.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[4]
REFERENCE_DIR = REPO / "applications" / "cons-port" / "reference" / "legacy"
ARCHIVE = REFERENCE_DIR / "port_cons_h5.npz"
MANIFEST = REFERENCE_DIR / "port_cons_h5.manifest.json"

CONFIGURATIONS = ("cons_only", "beginning_egm", "beginning_vfi", "end_returns", "port_only")
EXPRESSION_ROLES = ("vfi_maximand", "inv_euler", "cntn_to_dcsn_transition",
                    "marginal_bellman", "dcsn_to_cntn_transition", "utility")
REQUIRED_MANIFEST_KEYS = (
    "schema_version", "horizon", "configurations", "seeds", "expressions",
    "arrays", "sources", "vfi_structural_only_reason", "notebook_execution",
    "resolved_arguments", "archive",
)


@pytest.fixture(scope="module")
def manifest() -> dict:
    assert MANIFEST.is_file(), f"reference manifest missing: {MANIFEST}"
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def archive():
    assert ARCHIVE.is_file(), f"reference archive missing: {ARCHIVE}"
    return np.load(ARCHIVE, allow_pickle=False)


def test_reference_files_exist():
    assert ARCHIVE.is_file(), f"reference archive missing: {ARCHIVE}"
    assert MANIFEST.is_file(), f"reference manifest missing: {MANIFEST}"


def test_manifest_has_every_required_key(manifest):
    missing = [k for k in REQUIRED_MANIFEST_KEYS if k not in manifest]
    assert not missing, f"manifest lacks {missing}"
    assert manifest["schema_version"] == 1
    assert manifest["horizon"] == 5
    assert tuple(manifest["configurations"]) == CONFIGURATIONS
    assert manifest["seeds"] == {"sim_seed": 42}
    assert set(manifest["expressions"]) == set(EXPRESSION_ROLES)
    assert all(isinstance(v, str) and v for v in manifest["expressions"].values())


def test_every_archive_key_is_described_by_the_manifest(manifest, archive):
    described = manifest["arrays"]
    assert sorted(archive.files) == sorted(described)
    for key in archive.files:
        record = described[key]
        assert list(archive[key].shape) == record["shape"], key
        assert str(archive[key].dtype) == record["dtype"], key
        assert record["configuration"] in CONFIGURATIONS, key
        assert 0 <= record["horizon"] <= 5, key
        assert record["result_object_path"].startswith("nest_"), key
        assert "producing_cell" in record and "value_category" in record, key


def test_every_configuration_and_horizon_has_values(manifest):
    for configuration in CONFIGURATIONS:
        for h in range(6):
            keys = [k for k, r in manifest["arrays"].items()
                    if r["configuration"] == configuration and r["horizon"] == h and k.endswith("/values")]
            assert keys, f"no value array for {configuration} h={h}"


def test_sources_are_digested(manifest):
    sources = manifest["sources"]
    for name in ("notebook", "helper", "calibration", "settings"):
        assert Path(sources[name]["path"]).suffix, name
        assert len(sources[name]["sha256"]) == 64, name
    assert len(sources["methods"]) == 4
    assert len(sources["legacy_stages"]) == 4


def test_vfi_configuration_is_marked_structural_only(manifest):
    assert "1e40" in manifest["vfi_structural_only_reason"] or "VFI" in manifest["vfi_structural_only_reason"]


# ---------------------------------------------------------------------------
# P03: independent validation of the frozen reference. These tests read the
# two files and the accepted P01 preflight record; they never invoke the
# legacy solver or the capture program.
# ---------------------------------------------------------------------------

# The P01 preflight record, copied byte for byte beside the two reference
# files on 28 September 2026 from the evidence of spec 0.3, which stays in the
# internal folder (RH60). The manifest names the path it had when the
# reference was captured, a record that is not changed.
PREFLIGHT = REFERENCE_DIR / "preflight.json"
ARCHIVE_SHA256 = "1fa1264cfe37297c59a9cf209374d5a340157393fdc675f9552ac8b668ea0ecc"
# The notebook the reference was captured from has the digest the manifest
# records. On 28 September 2026 its first cell, a markdown cell, lost its last
# two lines, which cited a research note of the internal folder (RH60); no
# code cell and no output changed, and this was the notebook's digest since. On 7 October 2026 AAS's kernel
# saved the notebook again, its metadata and kernel version alone (commit c5fc2eef7), and this is its digest
# since (SD-38).
NOTEBOOK_SHA256 = "2f08245f7530b3720bb764fa5f950f8764203ea510ade91464e1ad20846a164e"
# The helper the reference was captured with has the digest the manifest
# records. On 29 September 2026 its insertion of the archived dolo and dolang
# on the import path and its imports of dolo moved inside the functions that
# use them, through the new function _legacy_library, and its import of
# extract_raw_equations, which no function used, was removed, so that the
# module imports without the archived packages; no function computes anything
# else, and this is the helper's digest since.
HELPER_SHA256 = "8a4ba1f07abb028aeb89291ffabc794c80d8d47fa358b654f1ab59bcc6b10fe4"
EXPECTED_EXPRESSIONS = {
    "vfi_maximand": "(c**(1-rho))/(1-rho) + V_cont(m_d - c)",
    "inv_euler": "(dV_cont(a))**(-1/rho)",
    "cntn_to_dcsn_transition": "a + c",
    "marginal_bellman": "c**(-rho)",
    "dcsn_to_cntn_transition": "m_d - c",
    "utility": "(c**(1-rho))/(1-rho)",
}
EXPECTED_SOURCE_PATHS = {
    "notebook": "applications/cons-port/notebooks/port-cons/solve_port_cons_ffp.ipynb",
    "helper": "applications/cons-port/code/ffp_utils.py",
    "calibration": "applications/cons-port/syntax/calibration.yaml",
    "settings": "applications/cons-port/syntax/settings.yaml",
}
# The folder `syntax/` that the manifest records moved whole to
# `reference/legacy/syntax/` on 2 October 2026 (the model folder layout); the
# manifest is a record and keeps the paths of its time.
RECORDED_SYNTAX = "applications/cons-port/syntax/"
PRESENT_SYNTAX = "applications/cons-port/reference/legacy/syntax/"
CANONICAL_PROFILE = (
    "(version 1)\n(deny default)\n(import \"system.sb\")\n(allow process*)\n(allow file-read*)\n"
    "(allow file-write* (subpath \"<temporary-root>\"))\n"
    "(allow network* (local unix-socket (subpath \"<temporary-root>\")) (remote unix-socket (subpath \"<temporary-root>\")))\n"
)


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _present(recorded: str) -> Path:
    """The file a path that the manifest records names, at the place it
    stands in the repository now."""
    if recorded.startswith(RECORDED_SYNTAX):
        return REPO / (PRESENT_SYNTAX + recorded[len(RECORDED_SYNTAX):])
    return REPO / recorded


@pytest.fixture(scope="module")
def preflight() -> dict:
    return json.loads(PREFLIGHT.resolve().read_text(encoding="utf-8"))


def test_the_test_does_not_import_the_capture_program():
    """The reference is read, never regenerated: this module imports nothing
    from the capture program and calls no function named capture."""
    import ast
    import sys
    assert not any(name.endswith("capture_legacy_reference") for name in sys.modules)
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all("capture_legacy_reference" not in a.name for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert "capture_legacy_reference" not in (node.module or "")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "capture"


def test_the_helper_imports_without_the_archived_packages():
    """The helper the reference was captured with imports in an environment
    that holds neither the archived dolo and dolang nor HARK: it imports them
    only inside the functions that use them. It is imported in a separate
    process, so that the import leaves this one unchanged."""
    import subprocess
    import sys
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import ffp_utils; "
            "print(sorted({name.split('.')[0] for name in sys.modules} & {'dolo', 'dolang', 'HARK'}))")
    held = subprocess.run([sys.executable, "-c", code, str((REPO / EXPECTED_SOURCE_PATHS["helper"]).parent)],
                          capture_output=True, text=True, check=True)
    assert held.stdout.strip() == "[]"


def test_archive_digest_is_frozen():
    assert _sha256(ARCHIVE) == ARCHIVE_SHA256


def test_manifest_records_the_archive_it_describes(manifest):
    assert manifest["archive"]["sha256"] == ARCHIVE_SHA256
    assert manifest["archive"]["path"] == "applications/cons-port/reference/legacy/port_cons_h5.npz"
    assert manifest["archive"]["count"] == len(manifest["arrays"])
    assert manifest["archive"]["keys"] == sorted(manifest["arrays"])


def test_arrays_and_manifest_records_correspond_both_ways(manifest, archive):
    records = manifest["arrays"]
    assert set(archive.files) == set(records), "an archive entry lacks a record or a record lacks an entry"
    for key, record in records.items():
        assert list(archive[key].shape) == record["shape"], key
        assert str(archive[key].dtype) == record["dtype"], key
        assert np.isfinite(archive[key]).all() or record["configuration"] == "beginning_vfi", key


def test_exact_configuration_horizon_seed_and_expressions(manifest):
    assert manifest["configurations"] == list(CONFIGURATIONS)
    assert manifest["horizon"] == 5
    assert manifest["seeds"] == {"sim_seed": 42}
    assert manifest["settings_as_loaded"]["sim_seed"] == 42
    assert manifest["expressions"] == EXPECTED_EXPRESSIONS
    assert manifest["required_cells"]["all_completed"] is True
    assert manifest["resolved_arguments"]["horizon"] == 5
    assert manifest["resolved_arguments"]["notebook"] == EXPECTED_SOURCE_PATHS["notebook"]


def test_source_paths_and_digests_reproduce(manifest, preflight):
    sources = manifest["sources"]
    for name, path in EXPECTED_SOURCE_PATHS.items():
        assert sources[name]["path"] == path
        recorded = {"notebook": NOTEBOOK_SHA256, "helper": HELPER_SHA256}.get(name, sources[name]["sha256"])
        assert _sha256(_present(path)) == recorded, f"{name} changed since the reference was captured"
    # the edit of the notebook's first cell changed no cell's index, id, type
    # or first line: its cells are those the preflight accepted
    accepted = next(nb for nb in preflight["notebooks"]["acceptance"]
                    if nb["path"] == EXPECTED_SOURCE_PATHS["notebook"])
    cells = json.loads((REPO / EXPECTED_SOURCE_PATHS["notebook"]).read_text(encoding="utf-8"))["cells"]
    assert [{"index": index, "id": cell.get("id"), "type": cell["cell_type"],
             "first_line": "".join(cell["source"]).split("\n", 1)[0]}
            for index, cell in enumerate(cells)] == accepted["cells"]
    for stage in ("cons", "port", "noport", "disc"):
        methods = sources["methods"][stage]
        assert methods["path"] == f"applications/cons-port/syntax/stages/{stage}/{stage}_stage_methods.yml"
        assert _sha256(_present(methods["path"])) == methods["sha256"], methods["path"]
        legacy = sources["legacy_stages"][stage]
        assert legacy["path"] == f"applications/cons-port/syntax/stages/{stage}/{stage}_stage.yaml"
        assert _sha256(_present(legacy["path"])) == legacy["sha256"], legacy["path"]


def test_embedded_execution_record_is_the_read_only_run(manifest):
    import hashlib
    execution = manifest["notebook_execution"]
    assert execution["status"] == "completed" and execution["failures"] == []
    assert execution["probe"]["exception_class"] == "PermissionError"
    assert execution["probe"]["exists_after"] is False
    assert execution["probe"]["execution_count"] == 1
    profile = execution["sandbox"]["profile"]
    root = execution["temporary_root"]
    assert profile.replace(root, "<temporary-root>") == CANONICAL_PROFILE
    assert execution["sandbox"]["profile_sha256"] == hashlib.sha256(profile.encode()).hexdigest()
    assert execution["sandbox"]["canonical_profile_sha256"] == hashlib.sha256(CANONICAL_PROFILE.encode()).hexdigest()
    assert execution["sandbox"]["command"][:2] == ["/usr/bin/sandbox-exec", "-f"]
    assert execution["kernel"]["transport"] == "ipc"
    assert execution["source_notebook_unchanged"] is True and execution["repository_unchanged"] is True
    assert execution["source_notebook_sha256_before"] == manifest["sources"]["notebook"]["sha256"]
    overlay = {e["path"]: e for e in execution["overlay"]}
    assert overlay["applications/cons-port/notebooks/port-cons/solve_port_cons_ffp.ipynb"]["kind"] == "copied-notebook"
    for link in ("applications/cons-port/code", "applications/cons-port/syntax", "packages", "docs"):
        assert overlay[link]["kind"] == "symlink", link
    assert execution["working_directory"] == f"{root}/overlay/applications/cons-port/notebooks/port-cons"
    assert Path(execution["kernel_working_directory"]).name == "port-cons"
    cells = execution["cells"]
    assert [c["index"] for c in cells] == list(range(len(cells)))
    last = manifest["required_cells"]["last_index"]
    assert all(c["status"] == "ok" for c in cells if c["index"] <= last and c["cell_type"] == "code")
    execution_counts = [c["execution_count"] for c in cells if c["cell_type"] == "code" and c["index"] <= last]
    assert execution_counts == sorted(execution_counts) and execution_counts[0] == 2
    assert manifest["final_cell"]["sha256"] == execution["final_cell_sha256"]


def test_provenance_matches_the_accepted_notebook_inventory(manifest, preflight):
    accepted = next(nb for nb in preflight["notebooks"]["acceptance"]
                    if nb["path"] == EXPECTED_SOURCE_PATHS["notebook"])
    assert accepted["sha256"] == manifest["sources"]["notebook"]["sha256"]
    by_index = {c["index"]: c for c in accepted["cells"]}
    for configuration, producer in manifest["producing_cells"].items():
        cell = by_index[producer["cell_index"]]
        assert cell["type"] == "code" and cell["id"] == producer["cell_id"], configuration
    seen_paths = set()
    for key, record in manifest["arrays"].items():
        assert record["configuration"] in CONFIGURATIONS, key
        assert 0 <= record["horizon"] <= 5 and f"/h{record['horizon']}/" in key, key
        producer = manifest["producing_cells"][record["configuration"]]
        assert record["producing_cell"] == {"index": producer["cell_index"], "id": producer["cell_id"],
                                            "variable": producer["variable"]}, key
        assert record["result_object_path"].startswith(f'{producer["variable"]}["solutions"][{record["horizon"]}]'), key
        assert record["value_category"].startswith("ValueFn."), key
        assert record["result_object_path"] not in seen_paths, f"duplicate provenance: {record['result_object_path']}"
        seen_paths.add(record["result_object_path"])


def test_every_configuration_has_all_six_horizons_of_both_fields(manifest):
    for configuration in CONFIGURATIONS:
        for h in range(6):
            for field in ("k", "m"):
                prefix = f"{configuration}/h{h}/{field}/"
                keys = {k[len(prefix):] for k in manifest["arrays"] if k.startswith(prefix)}
                assert {"grid", "values", "dvalues"} <= keys, (configuration, h, field, keys)
    assert manifest["unserialized"] == []
