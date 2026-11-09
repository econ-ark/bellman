"""The backend of Bellman Workbench without Solara, on the corpus stage
`cons.bl` and on `entrepreneur_death.bl`, whose forward graph the
construction refuses (model interface specification 0.3, §2.2 rules 1 to
4, §2.4, §2.5, §6, and the behavior of `bellman_workbench.model`).

The test named `test_item_5_*` closes acceptance item 5 of stage A: the
collection the editor shows equals the lesson's. The layers the editor
opens are the package's `layers_to_open`, whose values
`packages/bellman/tests/cat/test_model_explorer.py` asserts. The test
named `test_item_2_*` closes acceptance item 2 of stage P: the module
defines no function the package answers, and it imports from the
package's three namespaces and `bellman.refusals` alone. The tests named
`test_a1_item_2_*` close the claims of unit A1's acceptance item 2 that
live in this module: the counts of `cons.bl` are counts of the object, and
every query is total on a stage with a refused direction. The other tests
assert what each function of the module answers on the corpus and on the
temporary copies of two applications. The fixtures (`cons`,
`entrepreneur_death`, the folders) and the helper `edited` are those of
`workbench_support.py`.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import inspect
import json
import os
from pathlib import Path

import pytest
from workbench_support import (
    CONS,
    ENTREPRENEUR_DEATH_PATH,
    PORT,
    WORKER_SAVING,
    added_edits,
    applied,
    bound_as_the_recipe_binds,
    changed_lines,
    decision_fields,
    edited,
    stage_files,
    tree_entries,
)

from bellman.display import graphviz_layout
from bellman.stage import (
    ROLE_WORD,
    box_attributes,
    elaborate_stage,
    elaborate_text,
    load_stage,
    source_spans,
    to_model_explorer,
    write_model_explorer,
)
from bellman_workbench import model

ROOT = Path(__file__).resolve().parents[3]
CONS_PATH = "applications/portfolio-choice/declaration/stages/cons/cons.bl"
# the stage the construction refuses whole under `not-constructed`
OLD_ENTREPRENEUR_PATH = ("applications/cagetti-denardi-2006/declaration/stages/"
                         "old_entrepreneur/old_entrepreneur.bl")
# the stage whose shocks ν and Ψ are drawn from distributions, Ψ's given ν
SA_SAVINGS_PATH = (
    "applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl"
)
# the stage whose distributions of ψ and ξ read the parameters σ_ψ, σ_ξ, μ_ξ
# and p_zero
BUFFER_STOCK_PATH = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
# the stage whose policy declares the multiplier μ in a block body
CONS_OBS_PATH = "applications/portfolio-choice/declaration/stages/cons_obs/cons_obs.bl"

# the ids of the backward graph's nodes of cons.bl, in node order
BACKWARD_IDS = (
    "GraphInputs",
    "cntn_to_dcsn:Pullback",
    "cntn_to_dcsn:Aggregation",
    "cntn_to_dcsn:Evaluation",
    "dcsn_to_arvl:Pullback",
    "dcsn_to_arvl:Aggregation",
    "dcsn_to_arvl:Evaluation",
    "policy:Pullback",
    "policy.optimality:Aggregation",
    "policy.optimality:Argmax",
    "policy:Evaluation",
    "GraphOutputs",
)

# the counts of the object for cons.bl: five blocks, three backward and two
# forward; five builders over the two graphs; twenty wires, seventeen in the
# backward graph and three in the forward
CONS_COUNTS = {
    "blocks": 5,
    "blocks_backward": 3,
    "blocks_forward": 2,
    "builders": 5,
    "wires": 14,
    "wires_backward": 11,
    "wires_forward": 3,
}


# --- acceptance item 5 of stage A ---


CORPUS = (
    CONS_PATH,
    "applications/portfolio-choice/declaration/stages/port/port.bl",
    "applications/epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl",
    "applications/consumption-savings-iid/declaration/stages/cons_savings_iid/cons_savings_iid.bl",
)


@pytest.mark.parametrize("path", CORPUS)
def test_item_5_collection_equals_the_lessons(path):
    """The collection of each corpus stage, elaborated from its text, equals,
    as JSON character for character,
    `dataclasses.asdict(to_model_explorer(elaborate_stage(load_stage(path))))`,
    the lesson's stage."""
    text = (ROOT / path).read_text(encoding="utf-8")
    expected = dataclasses.asdict(to_model_explorer(elaborate_stage(load_stage(str(ROOT / path)))))
    assert json.dumps(
        model.collection(elaborate_text(text, path)), ensure_ascii=False
    ) == json.dumps(expected, ensure_ascii=False)


@pytest.mark.parametrize("stage_name", ["tenure", "joined", "unjoined"])
def test_forward_display_names_the_native_measure_boundaries_of_tenure(stage_name):
    path = ROOT / "applications/durables/declaration/stages/tenure/tenure.bl"
    source = path.read_text(encoding="utf-8").replace("@stage: tenure", f"@stage: {stage_name}", 1)
    original = model.collection(elaborate_text(source, str(path)))
    snapshot = json.dumps(original, ensure_ascii=False)
    display = model.forward_display_collection(original)

    assert json.dumps(original, ensure_ascii=False) == snapshot
    assert [g for g in display["graphs"] if g["id"] != "forward"] == [
        g for g in original["graphs"] if g["id"] != "forward"
    ]
    before = next(g for g in original["graphs"] if g["id"] == "forward")
    after = next(g for g in display["graphs"] if g["id"] == "forward")
    native = {n["id"]: n for n in before["nodes"]}
    drawn = {n["id"]: n for n in after["nodes"]}
    expected = {
        "GraphInputs": ("Input measure", "outputsMetadata", [f"{stage_name}:measure:arvl"]),
        "GraphOutputs": (
            "Output measures",
            "inputsMetadata",
            [f"{stage_name}:measure:cntn:keep", f"{stage_name}:measure:cntn:adjust"],
        ),
    }
    assert list(native) == list(drawn)
    for node_id, node in native.items():
        shown = drawn[node_id]
        if node_id not in expected:
            assert shown == node
            continue
        title, side, measures = expected[node_id]
        assert shown["label"] == title
        assert [port["id"] for port in shown[side]] == measures
        assert all(
            {"key": "role", "value": "measure"} in port["attrs"] for port in shown[side]
        )
        assert "finite measures over the state spaces" in shown["description"]
        assert {k: v for k, v in shown.items() if k not in {"label", "description"}} == {
            k: v for k, v in node.items() if k != "label"
        }


def test_forward_boundary_display_names_only_native_ports():
    def port(id_, role, perch, field=None):
        attrs = [{"key": "role", "value": role}, {"key": "perch", "value": perch}]
        if field is not None:
            attrs.append({"key": "field", "value": field})
        return {"id": id_, "attrs": attrs}

    occurrence = "periods[0]/keeper_cons"
    entry = {
        "id": f"{occurrence}/GraphInputs",
        "namespace": occurrence,
        "inputsMetadata": [port(f"{occurrence}/joined:keeper_cons:dcsn:w_d", "state", "dcsn", "w_d")],
    }
    continuation = {
        "id": f"{occurrence}/GraphOutputs",
        "namespace": occurrence,
        "outputsMetadata": [port(f"{occurrence}/unjoined:keeper_cons:cntn:a", "state", "cntn", "a")],
    }
    mixed = {
        **entry,
        "inputsMetadata": [
            port(f"{occurrence}/joined:measure:dcsn", "measure", "dcsn"),
            *entry["inputsMetadata"],
        ],
    }
    assert model.forward_boundary_display(entry) is None
    assert model.forward_boundary_display(continuation) is None
    title, explanation = model.forward_boundary_display(mixed)
    assert title == "Input measure"
    assert "finite measures over the state spaces" in explanation

    operator = {**mixed, "id": f"{occurrence}/dcsn_to_cntn:Pushforward"}
    assert model.forward_boundary_display(operator) is None


# --- acceptance item 2 of stage P ---


def test_item_2_the_backend_defines_no_function_the_package_answers():
    """`model.py` defines no function whose name a namespace of the package
    exports or that `factory/elaboration.py` or `factory/model_explorer.py`
    answers, and every import statement in it, at module level or inside a
    function, imports from the package `bellman` only the three namespaces
    and `bellman.refusals` (spec 0.3 §6 and §12, P item 2)."""
    import bellman.period
    import bellman.stage
    import bellman.trellis
    from bellman.factory import elaboration, model_explorer

    public = (
        set(bellman.stage.__all__) | set(bellman.period.__all__) | set(bellman.trellis.__all__)
    )
    defined = {
        name
        for name, value in vars(model).items()
        if inspect.isfunction(value) and value.__module__ == model.__name__
    }
    assert not defined & public
    answered = {
        name
        for module in (elaboration, model_explorer)
        for name, value in vars(module).items()
        if inspect.isfunction(value) and not name.startswith("_")
    }
    assert not defined & answered
    accepted = {"bellman.stage", "bellman.period", "bellman.trellis", "bellman.refusals"}
    for statement in ast.walk(ast.parse(Path(model.__file__).read_text(encoding="utf-8"))):
        # the modules a statement imports; a relative import names a module
        # of the Workbench and none of the package
        if isinstance(statement, ast.ImportFrom):
            modules = [statement.module] if statement.level == 0 else []
        elif isinstance(statement, ast.Import):
            modules = [alias.name for alias in statement.names]
        else:
            continue
        for module in modules:
            # the package `bellman` itself or one of its modules, which
            # `bellman_workbench` and the viewer's `model_explorer` are not
            if module == "bellman" or module.startswith("bellman."):
                assert isinstance(statement, ast.ImportFrom) and module in accepted, module


# --- acceptance item 2 of unit A1 ---


def test_a1_item_2_counts_of_cons_are_the_objects(cons):
    """The counts of `cons.bl` are counts of the object: five blocks, three
    in the backward initial diagram and two in the forward; five builders,
    the three of the backward graph (`cntn_to_dcsn`, `dcsn_to_arvl`,
    `policy`) and the two of the forward; fourteen wires as distinct wire
    identities, eleven in the backward graph and three in the forward, the
    file declaring values alone (AMD-MB-001). The specification's sentence
    "5 blocks, 3 builders, 20 wires", written when the file held marginal fields,
    counts the builders of the backward graph alone; `builders` counts
    both graphs, and the page prints what it needs from the record."""
    found = model.counts(cons)
    assert found == CONS_COUNTS
    assert len(cons.builder.bwd.list().names) == 3
    assert len(cons.builder.fwd.list().names) == 2
    assert model.counts(cons, model.collection(cons)) == found
    assert (
        model.elaborate_buffer((ROOT / CONS_PATH).read_text(encoding="utf-8"), CONS_PATH).counts
        == found
    )


def test_a1_item_2_refused_direction_is_total(entrepreneur_death):
    """On `entrepreneur_death.bl`, whose forward graph the construction
    refuses, `elaborate_buffer` answers the stage with no diagnostic,
    `loop_state` names `constructed, forward refused`, `counts` answers
    the backward graph's blocks, builders and wires with 0 forward wires
    and raises nothing, `refused_directions` names the forward refusal at
    line 17 under `not-constructed`, the collection holds the refusing
    node `forward:refused`, and every sheet of `stage_sheets` prints."""
    assert entrepreneur_death.stage is not None and entrepreneur_death.diagnostics == ()
    assert model.loop_state(entrepreneur_death) == "constructed, forward refused"
    stage = entrepreneur_death.stage
    found = model.counts(stage)
    print(found)
    assert found["wires_forward"] == 0 and found["blocks_forward"] == 2
    assert found["builders"] == 2 and found["wires"] == found["wires_backward"] == 10
    assert found["blocks"] == 4 and found["blocks_backward"] == 2
    assert set(model.refused_directions(stage)) == {"forward"}
    forward = next(g for g in model.collection(stage)["graphs"] if g["id"] == "forward")
    assert [node["id"] for node in forward["nodes"]] == ["forward:refused"]
    sheets = model.stage_sheets(stage)
    assert set(sheets) == {"view", "definitions", "fields", "obligations", "diagnostics"}
    assert all(sheets.values())
    assert "ready_for_interpretation   False" in sheets["diagnostics"]


# --- the buffer elaborated ---


def test_elaborate_buffer_answers_the_stage_and_its_counts(cons_text):
    """An elaborated buffer carries the stage, no diagnostic, the digest of
    the text and the counts of the stage."""
    result = model.elaborate_buffer(cons_text, CONS_PATH, revision=3)
    assert result.stage is not None
    assert result.diagnostics == ()
    assert result.revision == 3
    assert result.digest == result.stage.provenance["sha256"]
    assert result.counts == model.counts(result.stage)
    assert result.seconds > 0


def test_elaborate_buffer_syntax_refusal_at_line_18_column_15(cons_text):
    """The line `a = m_d - - c` is refused under the rule `syntax` at line
    18, column 15, ending at column 18, the end of the token `- c` the
    parser could not read, with no address, no action and the package's
    sentence, under the operation `parse`; no term exists, so the counts
    are empty."""
    result = model.elaborate_buffer(edited(cons_text, 18, "    a = m_d - - c"), CONS_PATH)
    assert result.stage is None
    assert result.counts == {}
    (diagnostic,) = result.diagnostics
    assert (diagnostic.file, diagnostic.line, diagnostic.column) == (CONS_PATH, 18, 15)
    assert (diagnostic.end_line, diagnostic.end_column, diagnostic.address) == (18, 18, None)
    assert (diagnostic.rule, diagnostic.kind, diagnostic.operation) == ("syntax", "refusal", "parse")
    assert diagnostic.message.startswith(
        "the file writes `- c` here, and the language admits `(`, a name, a number or `inf`"
    )
    assert diagnostic.write is None


def test_elaborate_buffer_name_refusal_at_line_35(cons_text):
    """The line `c = q[>]`, written in place of the policy's line 30, is
    refused under `name-in-scope` at the name `q[>]`, from 30:14 to 30:18,
    at the address `policy.cons_choice`; the term parsed, so the counts
    hold its five blocks."""
    line = "    c      = q[>]                    :: [id=cons_choice]"
    result = model.elaborate_buffer(edited(cons_text, 30, line), CONS_PATH)
    (diagnostic,) = result.diagnostics
    assert (diagnostic.line, diagnostic.column, diagnostic.end_line, diagnostic.end_column) == (
        30,
        14,
        30,
        18,
    )
    assert diagnostic.rule == "name-in-scope"
    assert diagnostic.address == "policy.cons_choice"
    assert diagnostic.message.startswith(
        "the line mentions q[>], which the stage does not declare"
    )
    assert result.counts == {"blocks": 5}


def test_loop_state_answers_the_four_states(cons_text, entrepreneur_death):
    """`loop_state` names `constructed` for `cons.bl`, `not parsed` for the
    syntax refusal at line 17, `parsed, refused` for the name refusal at
    line 30 and for `old_entrepreneur.bl`, refused whole under
    `not-constructed`, and `constructed, forward refused` for
    `entrepreneur_death.bl`; every answer is one of `LOOP_STATES`. No
    corpus stage has its backward graph alone refused, so that state is
    asserted as a name of `LOOP_STATES` only."""
    states = {
        "constructed": model.elaborate_buffer(cons_text, CONS_PATH),
        "not parsed": model.elaborate_buffer(
            edited(cons_text, 17, "    a = m_d - - c"), CONS_PATH
        ),
        "parsed, refused": model.elaborate_buffer(
            edited(cons_text, 30, "    c      = q[>]                    :: [id=cons_choice]"),
            CONS_PATH,
        ),
        "constructed, forward refused": entrepreneur_death,
    }
    for expected, elaboration in states.items():
        assert model.loop_state(elaboration) == expected
        assert expected in model.LOOP_STATES
    whole = model.elaborate_buffer(
        (ROOT / OLD_ENTREPRENEUR_PATH).read_text(encoding="utf-8"), OLD_ENTREPRENEUR_PATH
    )
    assert whole.stage is None and whole.diagnostics[0].rule == "not-constructed"
    assert model.loop_state(whole) == "parsed, refused"
    assert whole.counts == {"blocks": 5}
    assert "constructed, backward refused" in model.LOOP_STATES


def test_refused_directions_of_entrepreneur_death(cons, entrepreneur_death):
    """`refused_directions` is empty for `cons.bl` and names the forward
    refusal of `entrepreneur_death.bl` at line 17, columns 1 to 165, under
    the rule `not-constructed`, with the package's sentence and the
    address `<file>:17`."""
    assert model.refused_directions(cons) == {}
    found = model.refused_directions(entrepreneur_death.stage)
    print(found)
    (refusal,) = found.values()
    assert list(found) == ["forward"]
    assert (refusal.line, refusal.column, refusal.end_line, refusal.end_column) == (
        17,
        1,
        17,
        165,
    )
    assert refusal.rule == "not-constructed"
    assert refusal.file == ENTREPRENEUR_DEATH_PATH
    assert refusal.address == f"{ENTREPRENEUR_DEATH_PATH}:17"
    assert refusal.message.startswith("the forward measures are not constructed")


def test_input_digests_name_the_text_and_the_bound_sources(cons, cons_text, pension_folder):
    """`input_digests` of the symbolic stage holds the digest of the text
    alone, equal to the stage's provenance digest; a calibrated version
    adds the calibration's digest from its provenance."""
    found = model.input_digests(cons, cons_text)
    assert found == {"text": cons.provenance["sha256"]}
    values = {"β": 0.95, "ρ": 2.0, "r_f": 0.02, "r_p": 0.03, "χ_s": 0.1, "μ_w": 0.0, "σ_w": 0.2}
    origin = str(pension_folder / WORKER_SAVING)
    text = Path(origin).read_text(encoding="utf-8")
    bound = elaborate_text(text, origin).calibrate(values)
    digests = model.input_digests(bound, text)
    assert set(digests) == {"text", "calibration"}
    assert digests["calibration"] == bound.provenance["sources"]["calibration"]["sha256"]


# --- the view ---


def test_piece_of_a_field_diagram_node(cons):
    """In a field diagram a block's piece carries the block's printed record,
    the exporter's rows (kind, header, statements, lines) and the block as
    its address; a field's piece carries its rows (kind, perch, role, set,
    lines), no card, no kernel and no block; a user's click on a field goes
    to the header line its `lines` row names."""
    collection = model.collection(cons)
    block = model.piece(cons, "backward initial diagram", "policy", collection)
    assert block.kind == "block"
    assert block.attributes["kind"] == "block" and block.attributes["lines"] == "cons.bl 29–30"
    assert "policy" in block.card
    assert block.kernel == "" and block.block == "policy"
    field = model.piece(cons, "backward initial diagram", "cons:dcsn:c", collection)
    assert field.kind == "field"
    assert field.attributes["kind"] == "field" and field.attributes["perch"] == "dcsn"
    assert field.attributes["role"] == "control" and field.attributes["set"] == "ℝ₊₊"
    assert field.card == "" and field.kernel == "" and field.block == ""
    # the header that first lists c is dcsn_to_cntn's, line 16
    assert field.attributes["lines"] == "cons.bl 16"
    assert model.header_line_of(field.attributes) == 16
    with pytest.raises(KeyError):
        model.piece(cons, "backward initial diagram", "none", collection)


def test_edge_overlays_equal_the_second_file(cons, tmp_path):
    """`edge_overlays` answers the `EdgeOverlaysData` named `perches` with
    the three overlays arrival, decision and continuation, equal to the
    second file `write_model_explorer` writes."""
    overlays = model.edge_overlays(cons)
    assert overlays["name"] == "perches" and overlays["type"] == "edge_overlays"
    assert [overlay["name"] for overlay in overlays["overlays"]] == [
        "arrival",
        "decision",
        "continuation",
    ]
    _, overlays_path = write_model_explorer(cons, tmp_path / "model-explorer")
    assert overlays == json.loads(Path(overlays_path).read_text(encoding="utf-8"))


# --- the folder ---


def test_open_folder_refuses_a_file(model_folder):
    """A path that is no folder is refused."""
    with pytest.raises(ValueError):
        model.open_folder(model_folder / CONS)


def test_folder_tree_roles_and_hidden_names(scratch_folder):
    """The tree names cons.bl as a stage and the addition methods.bl of its
    stage folder as methods, and leaves out model-explorer/, __pycache__/ and
    names beginning with "."."""
    (scratch_folder / "model-explorer").mkdir()
    (scratch_folder / "model-explorer" / "cons.graph.json").write_text("{}")
    (scratch_folder / "__pycache__").mkdir()
    (scratch_folder / ".hidden.yml").write_text("a: 1\n")
    folder = model.open_folder(scratch_folder)
    tree = model.folder_tree(folder)
    entries = tree_entries(tree)
    roles = {path: entry["role"] for path, entry in entries.items()}
    assert roles[CONS] == "stage"
    assert roles["declaration/stages/cons/methods.bl"] == "methods"
    assert roles["declaration/stages/cons/cons.md"] == "other"
    assert "model-explorer" not in roles
    assert "__pycache__" not in roles
    assert ".git" not in roles
    assert ".hidden.yml" not in roles
    assert all(entry["children"] == [] for entry in entries.values() if entry["kind"] == "file")
    assert model.HIDDEN_NAMES == ("model-explorer", ".bellman", "__pycache__")


def test_folder_roles_of_a_registry(pension_folder):
    """A registry's trellis, period, recipe and stage files take the roles
    trellis, period, recipe and stage."""
    tree = model.folder_tree(model.open_folder(pension_folder))
    roles = {path: entry["role"] for path, entry in tree_entries(tree).items()}
    assert roles["declaration/trellis.yml"] == "trellis"
    assert roles["declaration/period.yml"] == "period"
    assert roles["declaration/spec.yml"] == "recipe"
    assert roles[WORKER_SAVING] == "stage"


def test_git_marks_after_a_change_and_a_new_file(scratch_folder):
    """A clean copy has no mark; a changed file carries ` M` and a new file
    `??`, the tree carries the same marks, and the summary counts the
    tracked file alone (specification §2.1)."""
    folder = model.open_folder(scratch_folder)
    assert folder.git_root == scratch_folder.resolve()
    assert model.git_marks(folder) == {}
    assert model.git_summary(folder) == "git: 0 modified"
    (scratch_folder / CONS).write_text("@stage: cons\n", encoding="utf-8")
    (scratch_folder / "new.bl").write_text("@stage: new\n", encoding="utf-8")
    assert model.git_marks(folder) == {CONS: " M", "new.bl": "??"}
    assert model.git_summary(folder) == "git: 1 modified"
    marks = {path: entry["git"] for path, entry in tree_entries(model.folder_tree(folder)).items()}
    assert marks[CONS] == " M" and marks["new.bl"] == "??" and marks[PORT] == ""


def test_git_outside_a_repository(tmp_path):
    """A folder no repository holds has no git root, no marks and the
    summary `git: not a repository`."""
    (tmp_path / "plain").mkdir()
    folder = model.open_folder(tmp_path / "plain")
    assert folder.git_root is None
    assert model.git_marks(folder) == {}
    assert model.git_summary(folder) == "git: not a repository"


def test_git_commit_records_the_named_files_only(scratch_folder):
    """A path-limited commit records the named file and leaves another
    changed file unrecorded; a push without a destination answers git's
    sentence and raises nothing."""
    folder = model.open_folder(scratch_folder)
    (scratch_folder / CONS).write_text("@stage: cons\n", encoding="utf-8")
    (scratch_folder / PORT).write_text("@stage: port\n", encoding="utf-8")
    result = model.git_commit(folder, "cons changed", [CONS])
    assert result.ok, result.sentence
    assert model.git_marks(folder) == {PORT: " M"}
    assert not model.git_commit(folder, "nothing", []).ok
    pushed = model.git_push(folder)
    assert not pushed.ok and pushed.sentence


# --- the file on disk ---


def test_read_file_and_save_file_round_trip(scratch_folder):
    """A file read and saved with its digest is written, and read back as
    written."""
    folder = model.open_folder(scratch_folder)
    read = model.read_file(folder, CONS)
    assert read.digest == hashlib.sha256(read.text.encode("utf-8")).hexdigest()
    text = read.text + "# one more line\n"
    saved = model.save_file(folder, CONS, text, read.digest)
    assert saved.saved and saved.reason is None and saved.text is None
    assert model.read_file(folder, CONS) == model.FileText(text, saved.digest)


def test_save_file_renames_a_temporary_file_and_leaves_none_behind(scratch_folder):
    """A save writes a temporary file in the file's folder and renames it
    over the file: after the save the folder holds the file with the new
    text and no file whose name begins with `.cons.bl.`, and the file's
    inode differs from the one before the save, since the temporary file
    took its place."""
    folder = model.open_folder(scratch_folder)
    path = scratch_folder / CONS
    before = path.stat().st_ino
    read = model.read_file(folder, CONS)
    saved = model.save_file(folder, CONS, read.text + "# renamed over\n", read.digest)
    assert saved.saved
    assert path.read_text(encoding="utf-8") == read.text + "# renamed over\n"
    assert [p.name for p in path.parent.iterdir() if p.name.startswith(".cons.bl.")] == []
    assert path.stat().st_ino != before


def test_save_file_with_a_stale_digest_writes_nothing(scratch_folder):
    """A save whose expected digest is not the file's writes nothing and
    answers the text on disk with its digest."""
    folder = model.open_folder(scratch_folder)
    read = model.read_file(folder, CONS)
    other = read.text + "# written by another tool\n"
    (scratch_folder / CONS).write_text(other, encoding="utf-8")
    result = model.save_file(folder, CONS, read.text + "# mine\n", read.digest)
    assert not result.saved
    assert result.reason == "the file changed on disk"
    assert (
        result.text == other and result.digest == hashlib.sha256(other.encode("utf-8")).hexdigest()
    )
    assert (scratch_folder / CONS).read_text(encoding="utf-8") == other


def test_save_file_after_utime_keeps_the_mismatch(scratch_folder):
    """A file whose contents changed and whose modification time was put
    back still meets the mismatch: contents decide, not times."""
    folder = model.open_folder(scratch_folder)
    path = scratch_folder / CONS
    before = path.stat()
    read = model.read_file(folder, CONS)
    path.write_text(read.text + "# changed\n", encoding="utf-8")
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert path.stat().st_mtime_ns == before.st_mtime_ns
    result = model.save_file(folder, CONS, read.text, read.digest)
    assert not result.saved and result.reason == "the file changed on disk"


def test_save_file_of_a_new_file_takes_digest_none(scratch_folder):
    """A file that does not exist yet is written with expected digest None,
    with its newlines as given, and a second save with None meets the
    mismatch."""
    folder = model.open_folder(scratch_folder)
    first = model.save_file(folder, "fresh.bl", "@stage: fresh\r\n", None)
    assert first.saved
    assert model.read_file(folder, "fresh.bl").text == "@stage: fresh\r\n"
    second = model.save_file(folder, "fresh.bl", "@stage: fresh\n", None)
    assert not second.saved and second.text == "@stage: fresh\r\n"


# --- blocks and boxes ---


def test_block_at_reads_the_packages_spans(cons_text):
    """`block_at` on the span table the package's `source_spans` answers:
    the policy block's span runs from line 29 to line 31, line 30 lies in
    `policy`, line 12 in `arvl_to_dcsn` and line 2 in no block."""
    spans = source_spans(cons_text, CONS_PATH)
    assert (spans["policy"].line, spans["policy"].end_line) == (29, 31)
    assert model.block_at(spans, 30) == "policy"
    assert model.block_at(spans, 2) is None
    assert model.block_at(spans, 12) == "arvl_to_dcsn"


def test_nodes_of_block_lists_the_nodes_born_in_a_block(cons):
    """The backward graph of `cons.bl` holds the twelve nodes of
    `BACKWARD_IDS` in node order; `nodes_of_block` lists the four nodes of
    the policy block in that order, and the one node of the block
    `arvl_to_dcsn` in the forward graph."""
    collection = model.collection(cons)
    backward = next(graph for graph in collection["graphs"] if graph["id"] == "backward")
    assert [node["id"] for node in backward["nodes"]] == list(BACKWARD_IDS)
    assert model.nodes_of_block(collection, "backward", "policy") == [
        "policy:Pullback",
        "policy.optimality:Aggregation",
        "policy.optimality:Argmax",
        "policy:Evaluation",
    ]
    assert model.nodes_of_block(collection, "forward", "arvl_to_dcsn") == [
        "arvl_to_dcsn:Pushforward"
    ]


def test_piece_of_the_pullback(cons):
    """The piece of `cntn_to_dcsn:Pullback` carries the printed card, the
    printed kernel, the box's attributes, its address, its block and its
    printed signature."""
    handle = cons.builder.bwd.primitives["cntn_to_dcsn:Pullback"]
    found = model.piece(cons, "backward", "cntn_to_dcsn:Pullback")
    assert found.kind == "box"
    assert found.card == str(handle.denote())
    assert found.kernel == str(handle.kernel()) == "𝑔 of dcsn_to_cntn: 𝑔(m_d, c) = m_d - c"
    assert found.attributes == box_attributes(cons, "backward", handle.box)
    assert found.attributes["kind"] == "Pullback"
    assert (found.address, found.block) == ("cntn_to_dcsn", "cntn_to_dcsn")
    assert found.signature == str(handle.signature())
    line = model.piece(cons, "backward", "policy.optimality:Argmax")
    assert (line.address, line.block) == ("policy.optimality", "policy")
    forward = model.piece(cons, "forward", "arvl_to_dcsn:Pushforward")
    assert forward.direction == "forward" and forward.block == "arvl_to_dcsn"
    with pytest.raises(KeyError):
        model.piece(cons, "backward", "none:Pullback")


# the branching stages of three applications, each with a pullback of one
# branch: the durables model's tenure choice, whose branch `keep` writes
# three of the five fields the law of motion defines; the retirement
# model's choice, whose branch `work` writes one of two; and the
# Cagetti–De Nardi old agent's choice, whose branch `retiree` writes one of
# three and reads no `θ`
BRANCH_BOXES = (
    ("applications/durables/declaration/stages/tenure/tenure.bl", "cntn_to_dcsn:Pullback:keep"),
    (
        "applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl",
        "policy:Pullback:work",
    ),
    (
        "applications/cagetti-denardi-2006/declaration/stages/old_choice/old_choice.bl",
        "cntn_to_dcsn:Pullback:retiree",
    ),
)


def test_k_the_kernel_of_a_box_of_one_branch_is_that_branch_s_part_of_the_law_of_motion():
    """Unit K, Task 14 (usability walkthrough §4 item 14 and §5, "Check a
    kernel"; decision K-I203): the package prints, for a pullback of one
    branch, the law of motion of the whole block, a component for each
    field of every branch and `unused d`, and gives under `section` the
    kernel of the branch's section; the piece's kernel, which Details
    prints, is that section's kernel, whose rule names the map the box's
    rule names. A box of no branch, the aggregation of tenure.bl and the
    push-forward of its whole block, has no section and prints the
    package's kernel."""
    for path, node_id in BRANCH_BOXES:
        stage = elaborate_text((ROOT / path).read_text(encoding="utf-8"), path)
        kernel = stage.builder.bwd.primitives[node_id].kernel()
        found = model.piece(stage, "backward", node_id)
        assert kernel.section is not None, node_id
        assert found.kernel == str(kernel.section), node_id
        assert "unused d" in str(kernel) and "unused d" not in found.kernel
        rule, *_ = (value for key, value in found.attributes.items() if key.startswith("rule"))
        assert found.kernel.split(": ", 1)[1].split("(")[0] in rule
    stage = elaborate_text((ROOT / BRANCH_BOXES[0][0]).read_text(encoding="utf-8"), "tenure.bl")
    for direction, node_id in (
        ("backward", "cntn_to_dcsn:Aggregation"),
        ("forward", "dcsn_to_cntn:Pushforward"),
    ):
        graph = stage.builder.bwd if direction == "backward" else stage.builder.fwd
        kernel = graph.primitives[node_id].kernel()
        assert kernel.section is None
        assert model.piece(stage, direction, node_id).kernel == str(kernel)


def test_piece_source_lines_and_definitions_of_the_aggregation(cons):
    """The piece of `cntn_to_dcsn:Aggregation` quotes line 21 of `cons.bl`
    with its text as the file writes it, and names the definitions its
    record holds with their declaration lines, among them 𝑢 at line 8 and
    ρ at line 6; the law of motion 𝑔≻ is declared by the block at line 17.
    The derivative line 22 stands at the Evaluation (AMD-MB-001 D4), whose
    piece quotes it and names 𝑑𝑢 at line 9."""
    found = model.piece(cons, "backward", "cntn_to_dcsn:Aggregation")
    print(found.source_lines, found.definitions)
    assert [line for line, _ in found.source_lines] == [21]
    assert found.source_lines[0][1].startswith("V        = 𝑢(c) + V[>]")
    lines = {name: line for name, _, line in found.definitions}
    assert lines["𝑢"] == 8 and lines["ρ"] == 6
    assert ("𝑔≻", "cons:g:dcsn_to_cntn", 17) in found.definitions
    assert all(identity.startswith("cons:") for _, identity, _ in found.definitions)
    evaluation = model.piece(cons, "backward", "cntn_to_dcsn:Evaluation")
    assert [line for line, _ in evaluation.source_lines] == [22]
    assert evaluation.source_lines[0][1].startswith("D_{m_d}V = 𝑑𝑢(c)")
    assert {name: line for name, _, line in evaluation.definitions}["𝑑𝑢"] == 9


def test_piece_definitions_name_a_set_with_category_codes_once():
    """A set marked `!categories` denotes two objects, the set and its
    category map, under one identity; the piece of a box that reads it names
    the set once, at the line of its definition, so that the Details panel
    lists it once."""
    text = (
        "@stage: household_status\n"
        "β : (0,1)\n"
        "HouseholdStatus := {i : ℤ | i >= 0, i <= 1} :: [!categories, newborn=0, old=1]\n"
        "n : HouseholdStatus\n"
        "n_next : HouseholdStatus\n"
        "[id=dcsn_to_cntn, (n) : !dcsn -> (n_next) : !cntn] { n_next = 1 }\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] "
        "{ V = 100 - 120*n + β*V[>] }\n"
    )
    found = model.piece(elaborate_text(text, "t.bl"), "forward", "dcsn_to_cntn:Pushforward")
    named = [(name, line) for name, _, line in found.definitions if name == "HouseholdStatus"]
    assert named == [("HouseholdStatus", 3)]


def test_piece_ports_of_a_box(cons):
    """The ports of `cntn_to_dcsn:Aggregation` are its one input, the
    pulled-back value at the perch `cntn` of type `Xm → [−∞, ∞)` with the
    role `value`, and its one output, the value at no perch, each row with
    the four keys label, perch, type and role."""
    found = model.piece(cons, "backward", "cntn_to_dcsn:Aggregation")
    (input_row,) = found.ports["inputs"]
    assert set(input_row) == {"label", "perch", "type", "role"}
    assert (input_row["perch"], input_row["type"], input_row["role"]) == (
        "cntn",
        "Xm → [−∞, ∞)",
        "value",
    )
    assert input_row["label"] == "𝑉≻(𝑔(m_d, 𝑐(m_d)))"
    assert [row["perch"] for row in found.ports["outputs"]] == [""]
    assert [row["type"] for row in found.ports["outputs"]] == ["Xm → [−∞, ∞)"]


def test_piece_of_a_layer(cons):
    """The piece of the layer `policy___group___` carries the policy
    builder's printed card and signature, the layer's rows from the
    collection (inputs, outputs, feasible set, parameter), the address and
    the block `policy`, and no kernel."""
    found = model.piece(cons, "backward", "policy___group___")
    handle = cons.builder.bwd["policy"]
    assert found.kind == "layer"
    assert found.card == str(handle.denote())
    assert found.signature == str(handle.signature())
    assert set(found.attributes) == {"inputs", "outputs", "feasible set", "parameter"}
    assert found.attributes["feasible set"] == "Γ(x : ℝ₊₊) := (0, x]"
    assert found.attributes["parameter"] == "ρ : [1, inf), unbound"
    assert (found.address, found.block) == ("policy", "policy")
    assert found.kernel == ""
    forward = model.piece(cons, "forward", "dcsn_to_cntn___group___")
    assert forward.card == str(cons.builder.fwd["dcsn_to_cntn"].denote())


def test_piece_of_the_inputs_and_outputs_nodes(cons):
    """The pieces of `GraphInputs` and `GraphOutputs` carry the graph's
    printed `signature()` and the node's own row, `inputs` or `outputs`;
    no card, no kernel, no block."""
    for direction, word in (("backward", "bwd"), ("forward", "fwd")):
        signature = str(getattr(cons.builder, word).signature())
        inputs = model.piece(cons, direction, "GraphInputs")
        outputs = model.piece(cons, direction, "GraphOutputs")
        assert inputs.signature == outputs.signature == signature
        assert list(inputs.attributes) == ["inputs"] and list(outputs.attributes) == ["outputs"]
        assert inputs.card == inputs.kernel == inputs.block == ""
    # the policy header of `cons.bl` lists `dV[>]`, which no line of the
    # block reads, so the backward graph takes 𝑉≻ alone (AAS, 17 October 2026)
    assert model.piece(cons, "backward", "GraphInputs").attributes["inputs"] == (
        "𝑉≻ : Xa → [−∞, ∞)"
    )


def test_piece_of_the_refusing_node(entrepreneur_death):
    """The piece of `forward:refused` on `entrepreneur_death.bl` carries the
    refusal's sentence as its card, its position and rule as attributes
    beside the whole text under `refusal`, and the refusal's address; a box
    of the refused graph and a node of the constructed graph the graph
    does not hold are refused with a KeyError."""
    stage = entrepreneur_death.stage
    found = model.piece(stage, "forward", "forward:refused")
    assert found.kind == "refusal"
    assert found.card.startswith("the forward measures are not constructed")
    assert (found.attributes["line"], found.attributes["column"]) == (17, 1)
    assert found.attributes["rule"] == "not-constructed"
    assert found.attributes["refusal"].startswith(f"{ENTREPRENEUR_DEATH_PATH}:17:1-17:165:")
    assert found.address == f"{ENTREPRENEUR_DEATH_PATH}:17"
    with pytest.raises(KeyError):
        model.piece(stage, "forward", "arvl_to_dcsn:Pushforward")
    with pytest.raises(KeyError):
        model.piece(stage, "backward", "backward:refused")


def test_block_record_of_each_direction(cons):
    """`block_record` answers the printed record of a backward block and
    of a forward block from the initial diagram that holds it, and refuses
    a name neither holds."""
    assert model.block_record(cons, "policy") == str(cons.initial.backward["policy"].denote())
    assert model.block_record(cons, "dcsn_to_cntn") == str(
        cons.initial.forward["dcsn_to_cntn"].denote()
    )
    with pytest.raises(KeyError):
        model.block_record(cons, "none")


def test_boxes_reading_lines_8_and_18(cons):
    """`boxes_reading` at line 17 of `cons.bl`, the law of motion
    `a = m_d - c`, names the backward boxes whose kernels or records read
    that law, the pullback among them, and the forward push-forward of
    `dcsn_to_cntn`; at line 8, the declaration of 𝑢, it names the boxes
    whose records name 𝑢, the aggregation of `cntn_to_dcsn` among them; a
    line that declares nothing and heads no block, line 2, names none."""
    at_18 = model.boxes_reading(cons, 17)
    at_8 = model.boxes_reading(cons, 8)
    print(at_18, at_8)
    assert "cntn_to_dcsn:Pullback" in at_18 and "dcsn_to_cntn:Pushforward" in at_18
    assert "cntn_to_dcsn:Aggregation" in at_8
    assert "arvl_to_dcsn:Pushforward" not in at_18
    assert model.boxes_reading(cons, 2) == []
    assert model.boxes_reading(cons, 20) == ["cntn_to_dcsn:Aggregation"]


def test_stage_sheets_print_the_five_sheets(cons):
    """`stage_sheets` answers the printed `view()`, definitions table,
    `fields()`, `obligations()` and `diagnostics()` of the stage."""
    sheets = model.stage_sheets(cons)
    assert sheets["view"] == str(cons.view())
    assert sheets["definitions"] == str(cons.definitions.list())
    assert sheets["fields"] == str(cons.fields())
    assert sheets["obligations"] == str(cons.obligations())
    assert sheets["diagnostics"] == str(cons.diagnostics())
    assert "ready_for_interpretation   True" in sheets["diagnostics"]


def test_occurrences_of_c(cons_text):
    """The whole-word occurrences of `c` in cons.bl: the control's
    declaration in the transition header and its uses, and none inside
    `cp`, `cons` or `m_d`."""
    found = model.occurrences(cons_text, "c")
    assert found[:4] == [(8, 3), (8, 15), (9, 4), (9, 16)]
    assert (16, 25) in found and (17, 15) in found and (20, 47) in found
    assert (22, 19) in found and (29, 53) in found and (30, 5) in found
    assert len(found) == 11
    lines = cons_text.split("\n")
    assert all(lines[line - 1][column - 1] == "c" for line, column in found)
    assert (1, 9) not in found
    assert model.occurrences(cons_text, "m_d") == [
        (12, 48),
        (13, 5),
        (16, 20),
        (17, 9),
        (22, 8),
        (30, 29),
    ]


# --- the name under the cursor (unit B) ---


def test_name_at_reads_the_word_under_the_cursor(cons_text):
    """The name under the cursor is the run of letters, digits and
    underscores that holds the column or ends just before it, the column in
    code points: `ρ` at line 6, `𝑢` at line 8; a number and a space are no
    name."""
    assert model.name_at(cons_text, 6, 1) == "ρ" and model.name_at(cons_text, 6, 2) == "ρ"
    assert model.name_at(cons_text, 8, 1) == "𝑢"
    assert model.name_at(cons_text, 6, 6) is None
    assert model.name_at(cons_text, 2, 1) is None and model.name_at(cons_text, 99, 1) is None


def test_name_report_lists_the_occurrences_the_declaration_first_and_the_boxes_that_depend_on_it(
    cons, cons_text
):
    """The reference view of specification §3.2 on cons.bl: the parameter `ρ`
    is declared at line 6, written four times, the declaration first, and
    six boxes depend on it: the aggregation of `cntn_to_dcsn` and the
    aggregation of the policy's optimality line, whose kernels' `parameters`
    hold it, and the evaluation of `cntn_to_dcsn`, the pullback of
    `dcsn_to_arvl`, the argmax of the optimality line and the policy's
    evaluation, whose kernels hold no `ρ` and whose records each reach it
    the same way, through the definitions of the values their wires carry,
    which call 𝑢 or 𝑑𝑢; the field `m_d` is declared by the header at line 12 and
    read by the kernels of both graphs; the function `𝑢` is declared at
    line 8."""
    collection = model.collection(cons)
    rho = model.name_report(cons, collection, cons_text, "ρ")
    assert rho.declaration == 6 and rho.occurrences[0] == (6, 1) and len(rho.occurrences) == 4
    assert rho.boxes == [
        ("cntn_to_dcsn:Aggregation", "backward"),
        ("cntn_to_dcsn:Evaluation", "backward"),
        ("dcsn_to_arvl:Pullback", "backward"),
        ("policy.optimality:Aggregation", "backward"),
        ("policy.optimality:Argmax", "backward"),
        ("policy:Evaluation", "backward"),
    ]
    field = model.name_report(cons, collection, cons_text, "m_d")
    assert field.declaration == 12 and field.occurrences[0] == (12, 48)
    assert ("dcsn_to_cntn:Pushforward", "forward") in field.boxes
    assert ("cntn_to_dcsn:Aggregation", "backward") in field.boxes
    assert model.name_report(cons, collection, cons_text, "𝑢").declaration == 8


def test_name_report_of_a_word_the_stage_declares_nowhere(cons, cons_text):
    """A word the stage declares nowhere, `argmax_` at line 30, lists its one
    occurrence in the text and no declaration and no box (Review Focus 5)."""
    report = model.name_report(cons, model.collection(cons), cons_text, "argmax_")
    assert report == model.NameReport("argmax_", None, [(30, 14)], [])


def test_name_report_matches_a_field_a_kernel_writes_with_its_perch_mark(cons, cons_text):
    """A kernel writes a field of another perch than the decision perch with
    that perch's mark: the field `a` of cons.bl, declared by the header at
    line 16, lists among the boxes that depend on it the push-forward of
    `dcsn_to_cntn` and the pullback of `cntn_to_dcsn`, whose kernels are
    the law of motion `𝑔(m_d, c) = m_d - c` with its output written `a≻`."""
    report = model.name_report(cons, model.collection(cons), cons_text, "a")
    assert report.declaration == 16
    assert ("dcsn_to_cntn:Pushforward", "forward") in report.boxes
    assert ("cntn_to_dcsn:Pullback", "backward") in report.boxes


def test_name_report_reads_a_shocks_declaration_from_the_record_of_its_distribution():
    """A shock's declaration is the first line the card of its distribution
    quotes, the distribution's own line, never a header that reads it: in
    sa_savings.bl, `Ψ ~ LogNormal(ν, σ_Ψ)` at line 14 for `Ψ`, which the
    header of `dcsn_to_cntn` at line 18 lists as an input, and `ν ~
    N(κ_1, σ_ν^2)` at line 12 for `ν`, not their typing lines 13 and 11;
    each is listed first among the occurrences."""
    text = (ROOT / SA_SAVINGS_PATH).read_text(encoding="utf-8")
    stage = elaborate_text(text, SA_SAVINGS_PATH)
    collection = model.collection(stage)
    shock = model.name_report(stage, collection, text, "Ψ")
    assert shock.declaration == 14 and shock.occurrences[0] == (14, 1)
    # the header at line 18 reads Ψ and is not its declaration
    assert shock.declaration != 18 and (18, 48) in shock.occurrences[1:]
    other = model.name_report(stage, collection, text, "ν")
    assert other.declaration == 12 and other.occurrences[0] == (12, 1)


def test_name_report_reads_a_multiplier_s_declaration_from_its_card():
    """A multiplier declared in a block body, `μ[>] : ℝ₊ ⟂ a >= 0` at line
    32 of cons_obs.bl, which no header lists, is declared at the first line
    the card of its definition quotes, its record's address being the
    block line `policy.slackness`, and is listed first."""
    text = (ROOT / CONS_OBS_PATH).read_text(encoding="utf-8")
    stage = elaborate_text(text, CONS_OBS_PATH)
    report = model.name_report(stage, model.collection(stage), text, "μ")
    assert report.declaration == 32 and report.occurrences[0] == (32, 5)


def test_name_report_reads_the_definitions_a_box_s_record_names_by_identity():
    """A box contains a definition where the package's record of the box,
    `denote().definitions`, names it by identity: in buffer_stock.bl the
    parameter `σ_ψ`, read by the distribution of `ψ` at line 16, lists the
    expectation of `dcsn_to_arvl`, whose kernel prints that distribution
    and whose `parameters` are empty; in sa_savings.bl the shock `Ψ`, whose
    distribution the records name by the symbol `P_{Ψ|ν}`, lists the two
    expectations and the extension whose kernels print its distribution,
    and `ν` lists those of its own."""
    text = (ROOT / BUFFER_STOCK_PATH).read_text(encoding="utf-8")
    stage = elaborate_text(text, BUFFER_STOCK_PATH)
    sigma = model.name_report(stage, model.collection(stage), text, "σ_ψ")
    assert ("dcsn_to_arvl.value:Expectation:1", "backward") in sigma.boxes
    text = (ROOT / SA_SAVINGS_PATH).read_text(encoding="utf-8")
    stage = elaborate_text(text, SA_SAVINGS_PATH)
    collection = model.collection(stage)
    shock = model.name_report(stage, collection, text, "Ψ")
    assert {
        ("cntn_to_dcsn.risk_ce:Expectation:1", "backward"),
        ("policy.objective:Expectation:2", "backward"),
        ("dcsn_to_cntn:DistributionExtension:Ψ", "forward"),
    } <= set(shock.boxes)
    other = model.name_report(stage, collection, text, "ν")
    assert {
        ("cntn_to_dcsn.ambiguity_ce:Expectation:1", "backward"),
        ("policy.objective:Expectation:1", "backward"),
        ("dcsn_to_cntn:DistributionExtension:ν", "forward"),
    } <= set(other.boxes)


# --- the classification table (unit T) ---


def test_t_item_1_the_three_tables_list_the_fields_of_cons(cons, cons_text):
    """On cons.bl the three tables list the fields of each perch with the
    sets and the role words the stage's fields table prints, in its order
    (unit T, item 1): m, l, V[<]; m_d, c, V; a, V[>], the stage declaring
    values alone since AMD-MB-001 retired the marginal fields. The row of c
    names line 16, where its first header lists it, and its three listings,
    the bare one of line 20 writing no component."""
    groups = model.classification(cons, source_spans(cons_text, CONS_PATH))
    assert [(group.perch, group.branch) for group in groups] == [
        ("arvl", None),
        ("dcsn", None),
        ("cntn", None),
    ]
    assert [[(r.field, r.set, r.role, r.line) for r in group.rows] for group in groups] == [
        [
            ("m", "Xm", "state", 12),
            ("l", "ℝ₊", "state", 12),
            ("V[<]", "ℝ", "!vlu", 25),
        ],
        [
            ("m_d", "Xm", "state", 12),
            ("c", "ℝ₊₊", "!ctrl", 16),
            ("V", "[-inf, inf)", "!vlu", 20),
        ],
        [
            ("a", "Xa", "state", 16),
            ("V[>]", "[-inf, inf)", "!vlu", 20),
        ],
    ]
    for group in groups:
        assert [row.identity for row in group.rows] == [
            str(identity) for identity, sort in cons.fields().items() if sort.perch == group.perch
        ]
    c = next(row for row in groups[1].rows if row.identity == "cons:dcsn:c")
    assert c.stem == "c"
    assert [
        (listing.at.line, listing.name, listing.role is not None, listing.domain is not None)
        for listing in c.listings
    ] == [(16, "c", True, True), (20, "c", False, False), (29, "c", True, True)]


def test_t_the_side_that_takes_a_new_field_and_the_completions_of_cons(cons, cons_text):
    """The side each role class takes a new field into (unit T, rule 4;
    T-R6): the arrival state into `(m : Xm, l : ℝ₊)` on line 12 after `l : ℝ₊`,
    the decision state into `(m_d : Xm)` and, by its name alone, into the
    decision block's inputs after `c : !ctrl @ ℝ₊₊` (AAS, L-D1), the
    control into those inputs, the continuation state into `(a : Xa)`, and
    the values into the backward blocks; the roles each box offers; the
    completions of a set cell, the file's sets and then the primitive sets'
    glyphs; and the role words of a role cell, from the package's
    vocabulary."""
    groups = model.classification(cons, source_spans(cons_text, CONS_PATH))

    def where(target):
        last = None if target.last is None else (target.last.end_line, target.last.end_column)
        return (target.at.line, target.at.column, last, target.bare, target.name_alone)

    # a table of one group declares a new field of each class on one side,
    # and lists a decision state by its name on a second side (L-D1)
    assert [
        {kind: [where(t) for t in targets] for kind, targets in group.targets.items()}
        for group in groups
    ] == [
        {
            "state": [(12, 19, (12, 34), False, False)],
            "value": [(25, 34, (25, 50), False, False)],
        },
        {
            "state": [(12, 47, (12, 56), False, False), (16, 19, (16, 40), False, True)],
            "control": [(16, 19, (16, 40), False, False)],
            "value": [(20, 61, (20, 84), False, False)],
        },
        {
            "state": [(16, 53, (16, 60), False, False)],
            "value": [(20, 19, (20, 48), False, False)],
        },
    ]
    assert [model.add_roles(group) for group in groups] == [
        ("state", "!vlu"),
        ("state", "!ctrl", "!vlu"),
        ("state", "!vlu"),
    ]
    assert model.set_completions(cons) == (
        "Xm",
        "Xa",
        "ℝ",
        "ℝ₊",
        "ℝ₊₊",
        "ℤ",
        "ℕ",
        "ℝ̄",
        "ℝ_{+∞}",
        "ℝ_{-∞}",
        "ℝ_{±∞}",
    )
    assert model.ROLE_CHOICES == ("state", "!ctrl", "!vlu")
    assert set(model.ROLE_CLASS) == set(ROLE_WORD) - {"shock"}


def test_t_the_tables_are_total_when_the_forward_graph_is_refused(entrepreneur_death):
    """On entrepreneur_death.bl, whose forward builders graph is refused,
    the tables are read and every field of the arrival and decision tables
    is paired with its listings; the boxes of those two tables offer the
    values alone, since no builder joins the forward perches."""
    text = (ROOT / ENTREPRENEUR_DEATH_PATH).read_text(encoding="utf-8")
    groups = model.classification(
        entrepreneur_death.stage, source_spans(text, ENTREPRENEUR_DEATH_PATH)
    )
    assert [group.perch for group in groups[:2]] == ["arvl", "dcsn"]
    assert [sorted(group.targets) for group in groups[:2]] == [["value"], ["value"]]
    assert all(row.listings for group in groups[:2] for row in group.rows)
    assert [row.field for row in groups[0].rows] == ["a_ed", "θ_ed", "V[<]"]


def test_t_item_2_a_set_cell_rewrites_every_declaration_and_nothing_else(cons, cons_text):
    """The set of V[>] changed to ℝ rewrites `[-inf, inf)` on lines 20 and
    29, where its two headers declare it, and nothing else (unit T, item 2;
    rule 3); the text elaborates, and the row prints ℝ."""
    groups = model.classification(cons, source_spans(cons_text, CONS_PATH))
    edits = model.classification_edits(
        groups, {"kind": "set", "identity": "cons:cntn:V", "value": "ℝ"}
    )
    assert edits == (
        model.Replacement(20, 27, 20, 38, "ℝ"),
        model.Replacement(29, 21, 29, 32, "ℝ"),
    )
    after = applied(cons_text, edits)
    assert changed_lines(cons_text, after) == [20, 29]
    assert after.split("\n")[19] == (
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> "
        "(V : [-inf, inf) @ !vlu) : !dcsn] {"
    )
    found = model.elaborate_buffer(after, CONS_PATH)
    again = model.classification(found.stage, source_spans(after, CONS_PATH))
    assert [row.set for row in again[2].rows if row.identity == "cons:cntn:V"] == ["ℝ"]


def test_t_a_field_declared_with_two_sets_is_rewritten_in_both():
    """`c` of cons_savings_iid.bl is declared ℝ₊ on line 24 and ℝ₊₊ on
    line 33: its row prints the meet, ℝ₊₊, and an edit rewrites both
    declarations, so that no header keeps a set the object does not
    produce (rule 3)."""
    path = (
        "applications/consumption-savings-iid/declaration/stages/cons_savings_iid/"
        "cons_savings_iid.bl"
    )
    text = (ROOT / path).read_text(encoding="utf-8")
    stage = model.elaborate_buffer(text, path).stage
    groups = model.classification(stage, source_spans(text, path))
    row = next(row for row in groups[1].rows if row.stem == "c")
    assert (row.set, row.line) == ("ℝ₊₊", 24)
    edits = model.classification_edits(
        groups, {"kind": "set", "identity": row.identity, "value": "ℝ"}
    )
    assert edits == (
        model.Replacement(24, 35, 24, 37, "ℝ"),
        model.Replacement(33, 47, 33, 50, "ℝ"),
    )


def test_t_a_role_cell_rewrites_or_writes_the_role_word(cons, cons_text):
    """A role chosen in a cell (rule 3, T-R5): `state` for V[>] writes
    `!state` in place of `!vlu` on lines 20 and 29; `!ctrl` for m, whose
    header writes no role word, is written after its set on line 12;
    `state` for m writes nothing."""
    groups = model.classification(cons, source_spans(cons_text, CONS_PATH))

    def edits(identity, kind, value):
        change = {"kind": kind, "identity": identity, "value": value}
        return model.classification_edits(groups, change)

    assert edits("cons:cntn:V", "role", "state") == (
        model.Replacement(20, 41, 20, 45, "!state"),
        model.Replacement(29, 35, 29, 39, "!state"),
    )
    assert edits("cons:arvl:m", "role", "!ctrl") == (
        model.Replacement(12, 26, 12, 26, " @ !ctrl"),
    )
    assert edits("cons:arvl:m", "role", "state") == ()


def test_t_a_field_no_block_header_declares_is_refused(cons_text):
    """The language lets a field be declared at the top level of the file,
    its set written at its first occurrence (Stages, §2), and the table
    writes into block headers alone (T-C22). On cons.bl with `m : Xm`
    on line 7 and m listed bare on line 12, as on cons.bl with m listed
    bare and declared nowhere, the text elaborates and the row of m names
    line 12 and one listing that declares nothing; a set or a role changed
    in its cells is refused with the sentence the page shows."""
    header_13 = "[id=arvl_to_dcsn, (m) : !arvl -> (m_d : Xm) : !dcsn] {"
    on_top = edited(edited(cons_text, 7, "m : Xm"), 12, header_13)
    for text, declared in ((on_top, "Xm"), (edited(cons_text, 12, header_13), "")):
        groups = model.classification(
            model.elaborate_buffer(text, CONS_PATH).stage, source_spans(text, CONS_PATH)
        )
        m = groups[0].rows[0]
        assert (m.field, m.set, m.line) == ("m", declared, 12)
        assert [(x.domain, x.role, x.perch) for x in m.listings] == [(None, None, None)]
        for kind, value in (("set", "ℝ₊"), ("role", "!ctrl")):
            change = {"kind": kind, "identity": m.identity, "value": value}
            with pytest.raises(ValueError, match="^no block header declares m$"):
                model.classification_edits(groups, change)


def test_t_a_set_or_a_role_no_header_declaration_writes_is_refused(cons_text):
    """A set or a role the row shows that no declaration of the field in a
    block header writes is refused, and the other component is rewritten
    where the headers write it (T-C22). On cons.bl with `c : ℝ₊₊` on
    line 7 and `c : !ctrl` on lines 16 and 29, a set change is refused and
    a role change rewrites both role words; with `c : !ctrl` on line 7 and
    `c : ℝ₊₊` on those lines, a role change is refused, `state` included,
    and a set change rewrites both sets. With `!vlu` removed from the two
    declarations of V[>], the elaborator still reads V[>] as a value, a
    role belonging to the name V, which carries `!vlu` on lines 20 and 25,
    and a role change of V[>] is refused."""
    c = {"identity": "cons:dcsn:c"}
    set_on_top = (
        edited(cons_text, 7, "c : ℝ₊₊")
        .replace("c : !ctrl @ ℝ₊₊", "c : !ctrl")
        .replace("c : ℝ₊₊ @ !ctrl", "c : !ctrl")
    )
    groups = model.classification(
        model.elaborate_buffer(set_on_top, CONS_PATH).stage, source_spans(set_on_top, CONS_PATH)
    )
    with pytest.raises(ValueError, match="^the set of c is written outside its block headers$"):
        model.classification_edits(groups, {**c, "kind": "set", "value": "ℝ₊"})
    assert model.classification_edits(groups, {**c, "kind": "role", "value": "!vlu"}) == (
        model.Replacement(16, 29, 16, 34, "!vlu"),
        model.Replacement(29, 57, 29, 62, "!vlu"),
    )
    role_on_top = (
        edited(cons_text, 7, "c : !ctrl")
        .replace("c : !ctrl @ ℝ₊₊", "c : ℝ₊₊")
        .replace("c : ℝ₊₊ @ !ctrl", "c : ℝ₊₊")
    )
    groups = model.classification(
        model.elaborate_buffer(role_on_top, CONS_PATH).stage, source_spans(role_on_top, CONS_PATH)
    )
    for value in ("!vlu", "state"):
        change = {**c, "kind": "role", "value": value}
        with pytest.raises(ValueError, match="^the role of c is written outside its block"):
            model.classification_edits(groups, change)
    assert model.classification_edits(groups, {**c, "kind": "set", "value": "ℝ₊"}) == (
        model.Replacement(16, 29, 16, 32, "ℝ₊"),
        model.Replacement(29, 57, 29, 60, "ℝ₊"),
    )
    unmarked = cons_text.replace("V[>] : [-inf, inf) @ !vlu", "V[>] : [-inf, inf)")
    groups = model.classification(
        model.elaborate_buffer(unmarked, CONS_PATH).stage, source_spans(unmarked, CONS_PATH)
    )
    v = next(row for row in groups[2].rows if row.identity == "cons:cntn:V")
    assert v.role == "!vlu" and [listing.role for listing in v.listings] == [None, None]
    change = {"kind": "role", "identity": v.identity, "value": "!ctrl"}
    with pytest.raises(ValueError, match=r"^the role of V\[>\] is written outside its block"):
        model.classification_edits(groups, change)


def test_t_a_field_with_no_set_takes_one_where_a_header_declares_it(cons, cons_text):
    """The elaborator admits a field declared with no set, and a set
    entered in its cell is written where a block header declares it
    (T-C22): on cons.bl with `c : !ctrl` on lines 16 and 29, the row of c
    prints no set, and ℝ₊₊ is written before `!ctrl` in both
    declarations, a text whose fields table is that of cons.bl."""
    text = cons_text.replace("c : !ctrl @ ℝ₊₊", "c : !ctrl").replace(
        "c : ℝ₊₊ @ !ctrl", "c : !ctrl"
    )
    groups = model.classification(
        model.elaborate_buffer(text, CONS_PATH).stage, source_spans(text, CONS_PATH)
    )
    c = next(row for row in groups[1].rows if row.identity == "cons:dcsn:c")
    assert (c.set, c.role) == ("", "!ctrl")
    change = {"kind": "set", "identity": c.identity, "value": "ℝ₊₊"}
    edits = model.classification_edits(groups, change)
    assert edits == (
        model.Replacement(16, 29, 16, 29, "ℝ₊₊ @ "),
        model.Replacement(29, 57, 29, 57, "ℝ₊₊ @ "),
    )
    again = model.elaborate_buffer(applied(text, edits), CONS_PATH).stage
    assert str(again.fields()) == str(cons.fields())


def test_t_item_3_add_field_writes_the_header_the_rule_names(cons, cons_text):
    """The box `add field` (unit T, item 3; rule 4): `h`, `ℝ₊`, `state` on
    the decision table is appended to the outputs of arvl_to_dcsn on line
    12 and listed by its name on the inputs of dcsn_to_cntn on line 16
    (AAS, L-D1), and the loop then refuses the output no equation of
    arvl_to_dcsn defines, under `output-defined`; on the continuation
    table to the outputs of dcsn_to_cntn on line 16, refused under
    `output-defined`; a control after `c : !ctrl @ ℝ₊₊` on line 16; a
    continuation value into cntn_to_dcsn's inputs, which elaborates. `c`
    on the decision table, declared on line 16, is written nowhere."""
    groups = model.classification(cons, source_spans(cons_text, CONS_PATH))

    def added(perch, field, written, role):
        change = {
            "kind": "add",
            "perch": perch,
            "branch": None,
            "field": field,
            "set": written,
            "role": role,
        }
        return model.classification_edits(groups, change)

    edits = added("dcsn", "h", "ℝ₊", "state")
    assert edits == (
        model.Replacement(12, 56, 12, 56, ", h : ℝ₊"),
        model.Replacement(16, 40, 16, 40, ", h"),
    )
    after = applied(cons_text, edits)
    assert after.split("\n")[11] == (
        "[id=arvl_to_dcsn, (m : Xm, l : ℝ₊) : !arvl -> (m_d : Xm, h : ℝ₊) : !dcsn] {"
    )
    assert model.elaborate_buffer(after, CONS_PATH).diagnostics[0].rule == "output-defined"
    edits = added("cntn", "h", "ℝ₊", "state")
    after = applied(cons_text, edits)
    assert after.split("\n")[15].endswith("-> (a : Xa, h : ℝ₊) : !cntn] {")
    assert model.elaborate_buffer(after, CONS_PATH).diagnostics[0].rule == "output-defined"
    assert added("dcsn", "k", "ℝ₊", "!ctrl") == (
        model.Replacement(16, 40, 16, 40, ", k : ℝ₊ @ !ctrl"),
    )
    edits = added("cntn", "W[>]", "ℝ", "!vlu")
    assert edits == (model.Replacement(20, 48, 20, 48, ", W[>] : ℝ @ !vlu"),)
    assert model.elaborate_buffer(applied(cons_text, edits), CONS_PATH).stage is not None
    with pytest.raises(ValueError, match="^c is already declared on line 16$"):
        added("dcsn", "c", "ℝ₊", "!ctrl")
    with pytest.raises(ValueError, match="^V is already declared on line 20$"):
        added("cntn", "V", "ℝ", "!vlu")


def test_t_the_three_forms_of_a_side_that_takes_a_field(cons_text):
    """A side that takes a new field (T-R6): after the last field of a side
    that lists fields (the test above), inside the parentheses of an empty
    side, the nested `()` of ret_choice.bl's `work` on line 10, and around
    a bare side, `V : !dcsn` on line 26 of ez_savings.bl as it stood with its
    arrival builders, `tests/fixtures/ez_savings_with_arrival.bl` (decision
    MB-V46), which the same edit parenthesizes, the new field carrying the
    table's perch word. On
    cons.bl with the outputs of line 12 written bare, the field so written
    is placed, and listed by its name on the inputs of line 16 (AAS,
    L-D1); the loop refuses it as the output no equation defines, under
    `output-defined`, as on the parenthesized side."""
    work = ROOT / RET_CHOICE_PATH
    ez = Path(__file__).parent / "fixtures/ez_savings_with_arrival.bl"
    work_text, ez_text = (path.read_text(encoding="utf-8") for path in (work, ez))
    work_spans, ez_spans = source_spans(work_text, "ret_choice.bl"), source_spans(ez_text, "ez.bl")
    change = {
        "kind": "add",
        "perch": "dcsn",
        "branch": None,
        "field": "h",
        "set": "ℝ₊",
        "role": "state",
    }
    empty = model.Target(work_spans["dcsn_to_cntn.work.in"], None, False)
    edits = model.classification_edits(
        (model.Group("dcsn", None, (), {"state": (empty,)}),), change
    )
    assert edits == (model.Replacement(10, 21, 10, 21, "h : ℝ₊"),)
    assert applied(work_text, edits).split("\n")[9] == (
        "    [label=work,   (h : ℝ₊) -> (a_w : ℝ₊) : !cntn] { a_w = a_d }"
    )
    bare = model.Target(ez_spans["dcsn_to_arvl.in"], ez_spans["dcsn_to_arvl.in.V"], True)
    edits = model.classification_edits(
        (model.Group("dcsn", None, (), {"state": (bare,)}),), change
    )
    assert applied(ez_text, edits).split("\n")[25] == (
        "[id=dcsn_to_arvl, (V : !dcsn, h : ℝ₊ @ !dcsn) -> (V[<] : ℝ @ !vlu) : !arvl] {"
    )
    text = edited(cons_text, 12, "[id=arvl_to_dcsn, (m : Xm) : !arvl -> m_d : Xm @ !dcsn] {")
    groups = model.classification(
        model.elaborate_buffer(text, CONS_PATH).stage, source_spans(text, CONS_PATH)
    )
    assert [target.bare for target in groups[1].targets["state"]] == [True, False]
    after = applied(text, model.classification_edits(groups, change))
    assert after.split("\n")[11] == (
        "[id=arvl_to_dcsn, (m : Xm) : !arvl -> (m_d : Xm @ !dcsn, h : ℝ₊ @ !dcsn)] {"
    )
    assert after.split("\n")[15] == (
        "[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊, h) : !dcsn -> (a : Xa) : !cntn] {"
    )
    assert model.elaborate_buffer(after, CONS_PATH).diagnostics[0].rule == "output-defined"


def test_l_17_the_pairs_the_headers_write_stand_only_where_no_builder_does(cons, cons_text):
    """Unit L, Task 17 (defect 7 of the UX simulation): `header_pairs`
    reads, for each top-level block header of cons.bl, the pair of perches
    the perch words ending its two sides write, the pair (cntn, dcsn) that
    both cntn_to_dcsn and the policy block write giving no block. Where the
    stage holds its builders, the sides that take a new field are read from
    them, and the pairs given change nothing. A side's perch is read as the
    classification table's text reading reads it (`_side_perch`, R-D57): a
    side typed `: ℝ @ !arvl`, which parses and which the package refuses,
    stands at arvl, and a bare side, whose field's own typing writes the
    perch word, writes no perch of its own and gives no pair."""
    spans = source_spans(cons_text, CONS_PATH)
    pairs = model.header_pairs(spans, cons_text)
    assert pairs == {
        ("arvl", "dcsn"): "arvl_to_dcsn",
        ("dcsn", "cntn"): "dcsn_to_cntn",
        ("dcsn", "arvl"): "dcsn_to_arvl",
    }
    assert model.classification(cons, spans, headers=pairs) == model.classification(cons, spans)
    compound = edited(
        cons_text, 12, "[id=arvl_to_dcsn, (m : Xm) : ℝ @ !arvl -> (m_d : Xm) : !dcsn] {"
    )
    assert model.header_pairs(source_spans(compound, CONS_PATH), compound) == pairs
    bare = edited(
        cons_text,
        25,
        "[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {",
    )
    assert model.header_pairs(source_spans(bare, CONS_PATH), bare) == {
        ("arvl", "dcsn"): "arvl_to_dcsn",
        ("dcsn", "cntn"): "dcsn_to_cntn",
    }


def test_t_the_changes_the_table_refuses(cons, cons_text):
    """An empty set, a word that is no role word, a role the table's
    builders take no field of, an empty name and a change of no kind are
    refused, each with its sentence, and write nothing."""
    groups = model.classification(cons, source_spans(cons_text, CONS_PATH))
    for change, sentence in (
        (
            {"kind": "set", "identity": "cons:cntn:V", "value": " "},
            r"^the set of V\[>\] is empty$",
        ),
        ({"kind": "role", "identity": "cons:cntn:V", "value": "!vl"}, "is no role word"),
        (
            {"kind": "add", "perch": "arvl", "branch": None, "field": "k", "role": "!ctrl"},
            "no header of this stage takes a field of the role !ctrl",
        ),
        (
            {"kind": "add", "perch": "dcsn", "branch": None, "field": " ", "role": "state"},
            "^the field's name is empty$",
        ),
        ({"kind": "move"}, "no change of the kind"),
    ):
        with pytest.raises(ValueError, match=sentence):
            model.classification_edits(groups, change)


def test_t_the_shortcuts_are_the_snippets_of_the_extension(tmp_path):
    """`unicode_shortcuts` reads the VS Code extension's one snippets file
    (unit T, rule 6): sixty-six prefixes in the file's order, each with
    its body; a file that is absent gives none."""
    table = model.unicode_shortcuts()
    assert len(table) == 66
    assert (table["\\Reals"], table["\\PositiveReals"], table["\\StrictlyPositiveReals"]) == (
        "ℝ",
        "ℝ₊",
        "ℝ₊₊",
    )
    assert (table["\\in"], table["\\times"], table["\\leq"], table["_h"]) == ("∈", "×", "≤", "ℎ")
    snippets = json.loads(model.SNIPPETS.read_text(encoding="utf-8"))
    assert list(table) == [entry["prefix"] for entry in snippets.values()]
    assert model.unicode_shortcuts(tmp_path / "absent.json") == {}


RET_CHOICE_PATH = "applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl"


def test_t_item_4_the_continuation_table_of_ret_choice_has_one_group_per_branch():
    """ret_choice.bl branches into `work` and `retire` (unit T, item 4;
    rule 5, T-C12; AMD-MI-002 §5 rule 2, A2-D12): the continuation table
    holds the group `work`, headed `cntn · d = work` by the control `d`
    that selects it, with a_w and the two values that cntn_to_dcsn, the
    builder joining `cntn` and `dcsn`, types on the states of `work`,
    V_w[>]; the group `retire`, headed `cntn · d = retire`,
    with a_r and V_r[>]; and the group `cntn · all branches`,
    empty, since no field is held by every branch and that builder places
    every value on one branch. Each group's box offers a state and the
    values; `add field` under `work` writes a state into line 10 alone and
    a value into the inputs of cntn_to_dcsn on line 14, and under `all
    branches` a state into lines 10 and 11, the nested block of each
    branch, and a value into those inputs once."""
    text = (ROOT / RET_CHOICE_PATH).read_text(encoding="utf-8")
    stage = model.elaborate_buffer(text, RET_CHOICE_PATH).stage
    groups = model.classification(stage, source_spans(text, RET_CHOICE_PATH))
    assert [(g.perch, g.branch, [r.field for r in g.rows]) for g in groups] == [
        ("arvl", None, ["a", "V[<]"]),
        ("dcsn", None, ["a_d", "d", "V"]),
        ("cntn", "work", ["a_w", "V_w[>]"]),
        ("cntn", "retire", ["a_r", "V_r[>]"]),
        ("cntn", "all branches", []),
    ]
    assert [g.heading for g in groups] == [
        None,
        None,
        "cntn · d = work",
        "cntn · d = retire",
        "cntn · all branches",
    ]
    assert [(row.field, row.line) for row in groups[2].rows + groups[3].rows] == [
        ("a_w", 10),
        ("V_w[>]", 14),
        ("a_r", 11),
        ("V_r[>]", 14),
    ]
    assert [model.add_roles(group) for group in groups[2:]] == [
        ("state", "!vlu"),
        ("state", "!vlu"),
        ("state", "!vlu"),
    ]
    change = {
        "kind": "add",
        "perch": "cntn",
        "branch": "work",
        "field": "h",
        "set": "ℝ₊",
        "role": "state",
    }
    edits = model.classification_edits(groups, change)
    assert edits == (model.Replacement(10, 35, 10, 35, ", h : ℝ₊"),)
    after = applied(text, edits)
    assert changed_lines(text, after) == [10]
    assert after.split("\n")[9] == (
        "    [label=work,   () -> (a_w : ℝ₊, h : ℝ₊) : !cntn] { a_w = a_d }"
    )
    value = {**change, "field": "W[>]", "set": "ℝ", "role": "!vlu"}
    assert model.classification_edits(groups, value) == (
        model.Replacement(14, 79, 14, 79, ", W[>] : ℝ @ !vlu"),
    )
    every = {**change, "branch": model.ALL_BRANCHES}
    assert model.classification_edits(groups, every) == (
        model.Replacement(10, 35, 10, 35, ", h : ℝ₊"),
        model.Replacement(11, 35, 11, 35, ", h : ℝ₊"),
    )
    assert model.classification_edits(groups, {**value, "branch": model.ALL_BRANCHES}) == (
        model.Replacement(14, 79, 14, 79, ", W[>] : ℝ @ !vlu"),
    )


def test_t_a_branch_drawn_by_nature_groups_its_fields_and_offers_no_refused_side(
    entrepreneur_death,
):
    """entrepreneur_death.bl draws `survive` or `die` by the shock s, at no
    perch and in no table, and its forward graph is refused: each branch's
    group, headed by its label alone, `cntn · survive`, since no control
    selects it (AMD-MI-002 §5 rule 2, A2-D12), holds the branch's states,
    paired with their nested blocks' listings, and the value the builder
    joining `cntn` and `dcsn` types on those states, W_old[>] under
    `survive` and V_young[>] under `die` (T-C12); the group
    `cntn · all branches` is empty. The boxes offer the value roles alone:
    that builder stands, while the one joining `dcsn` and `cntn`, which a
    state's side needs, is refused (Review Focus 5)."""
    text = (ROOT / ENTREPRENEUR_DEATH_PATH).read_text(encoding="utf-8")
    groups = model.classification(
        entrepreneur_death.stage, source_spans(text, ENTREPRENEUR_DEATH_PATH)
    )
    assert [(g.heading, [r.field for r in g.rows]) for g in groups[2:]] == [
        ("cntn · survive", ["a_ed_oc", "θ_ed_oc", "W_old[>]"]),
        ("cntn · die", ["a_ed_yc", "y_ed_yc", "θ_ed_yc", "V_young[>]"]),
        ("cntn · all branches", []),
    ]
    assert all(row.listings for group in groups for row in group.rows)
    assert [model.add_roles(group) for group in groups[2:]] == [
        ("!vlu",),
        ("!vlu",),
        ("!vlu",),
    ]
    assert not any(row.stem == "s" for group in groups for row in group.rows)


def test_t_every_set_written_back_to_itself_leaves_the_fields_of_the_corpus():
    """On every stage file of the applications, at
    `applications/<model>/declaration/stages/<key>/<key>.bl`, that
    elaborates, each row of the three tables has a first listing on the
    line it names, starting with the field as the row writes it, and the
    edits of every set to its own printed set, made at once, give a text
    whose fields table prints as before (unit T, rules 1 to 3, on the
    corpus)."""
    files = stage_files()
    elaborated = 0
    for path in files:
        relpath = str(path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        try:
            stage = elaborate_text(text, relpath)
        except ValueError:  # a stage the construction refuses has no table
            continue
        elaborated += 1
        groups = model.classification(stage, source_spans(text, relpath))
        lines = text.split("\n")
        edits = []
        for group in groups:
            for row in group.rows:
                assert row.listings, (relpath, row.identity)
                first = row.listings[0].at
                written = lines[first.line - 1][first.column - 1 :]
                assert first.line == row.line and written.startswith(row.field), relpath
                if row.set:
                    change = {"kind": "set", "identity": row.identity, "value": row.set}
                    edits.extend(model.classification_edits(groups, change))
        again = elaborate_text(applied(text, edits), relpath)
        assert str(again.fields()) == str(stage.fields()), relpath
    assert elaborated > 30


def test_r_the_tables_read_from_a_text_are_those_its_construction_gives():
    """On every stage file of the applications that elaborates, the tables
    read from the text's parse, with the stage as the last construction,
    equal the tables read from the stage: the same groups with the same
    rows, listings, sets, roles, sides and headings (unit R, R-D57: while
    the construction is refused, the rows are read from the parse of the
    text, so that a text the package accepts reads as it does from its
    stage)."""
    files = stage_files()
    compared = 0
    for path in files:
        relpath = str(path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        try:
            stage = elaborate_text(text, relpath)
        except ValueError:  # a stage the construction refuses has no table
            continue
        spans = source_spans(text, relpath)
        assert model.classification(stage, spans, text) == model.classification(stage, spans), (
            relpath
        )
        compared += 1
    assert compared > 30


# --- unit L: a decision field listed in both blocks that carry the decision
# perch (AAS, L-D1) ---

# a stage that no builder joining `dcsn` and `cntn` holds
BEQUEST_PATH = "applications/retirement-choice/declaration/stages/bequest/bequest.bl"
# a stage whose block joining `dcsn` and `cntn` lists the shock θ, which
# stands in no table, on its inputs
NOPORT_PATH = "applications/portfolio-choice/declaration/stages/noport/noport.bl"


def test_l_a_decision_field_is_declared_and_listed_by_name_in_the_block_that_reads_it(
    cons_text,
):
    """`q`, `ℝ₊`, `state` added in the decision table of cons.bl is
    declared on the outputs of arvl_to_dcsn, line 12, with its set, and in
    the same edit listed by its name alone on the inputs of dcsn_to_cntn,
    line 16, after `c : !ctrl @ ℝ₊₊`, where the side's `!dcsn` stands for
    it (AAS, L-D1); with no set given, both sides take the name alone. The
    loop refuses the text until an equation of arvl_to_dcsn defines q
    (`output-defined`); with `q = m` written there the stage constructs
    with q among its decision fields, where the declaration alone, as
    written before L-D1, is refused as the output no block reads
    (`stage-boundary`). The arrival and continuation tables still write a
    state into one side."""
    edits = added_edits(cons_text, CONS_PATH, "dcsn", "q", "ℝ₊")
    assert edits == (
        model.Replacement(12, 56, 12, 56, ", q : ℝ₊"),
        model.Replacement(16, 40, 16, 40, ", q"),
    )
    after = applied(cons_text, edits)
    assert changed_lines(cons_text, after) == [12, 16]
    assert after.split("\n")[15] == (
        "[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊, q) : !dcsn -> (a : Xa) : !cntn] {"
    )
    assert added_edits(cons_text, CONS_PATH, "dcsn", "q", "") == (
        model.Replacement(12, 56, 12, 56, ", q"),
        model.Replacement(16, 40, 16, 40, ", q"),
    )
    (refusal,) = model.elaborate_buffer(after, CONS_PATH).diagnostics
    assert refusal.rule == "output-defined" and "'cons:dcsn:q'" in refusal.message
    defined = edited(after, 13, "    m_d = m\n    q = m")
    assert "cons:dcsn:q" in decision_fields(defined, CONS_PATH)
    alone = edited(applied(cons_text, edits[:1]), 13, "    m_d = m\n    q = m")
    assert model.elaborate_buffer(alone, CONS_PATH).diagnostics[0].rule == "stage-boundary"
    assert added_edits(cons_text, CONS_PATH, "arvl", "q", "ℝ₊") == (
        model.Replacement(12, 34, 12, 34, ", q : ℝ₊"),
    )
    assert added_edits(cons_text, CONS_PATH, "cntn", "q", "ℝ₊") == (
        model.Replacement(17, 60, 17, 60, ", q : ℝ₊"),
    )


def test_l_a_stage_without_the_decision_block_takes_the_declaration_alone():
    """bequest.bl of the retirement model holds no block joining `dcsn`
    and `cntn`: a decision state added there is declared on the outputs of
    arvl_to_dcsn, line 11, and listed nowhere else (L-D1)."""
    text = (ROOT / BEQUEST_PATH).read_text(encoding="utf-8")
    groups = model.classification(
        model.elaborate_buffer(text, BEQUEST_PATH).stage, source_spans(text, BEQUEST_PATH)
    )
    assert [target.name_alone for target in groups[1].targets["state"]] == [False]
    assert added_edits(text, BEQUEST_PATH, "dcsn", "q", "ℝ₊") == (
        model.Replacement(11, 49, 11, 49, ", q : ℝ₊"),
    )


def test_l_a_name_the_decision_block_already_lists_is_not_written_twice():
    """noport.bl lists the shock θ, which stands in no table, on the inputs
    of dcsn_to_cntn, line 18: θ added as a decision state is declared on
    the outputs of arvl_to_dcsn, line 14, and not written on line 18 a
    second time, while q is written on both lines (L-D1)."""
    text = (ROOT / NOPORT_PATH).read_text(encoding="utf-8")
    assert added_edits(text, NOPORT_PATH, "dcsn", "θ", "ℝ₊₊") == (
        model.Replacement(14, 48, 14, 48, ", θ : ℝ₊₊"),
    )
    assert added_edits(text, NOPORT_PATH, "dcsn", "q", "ℝ₊") == (
        model.Replacement(14, 48, 14, 48, ", q : ℝ₊"),
        model.Replacement(18, 26, 18, 26, ", q"),
    )


def test_l_a_branching_stage_lists_the_decision_field_on_the_branching_block():
    """In ret_choice.bl, whose block joining `dcsn` and `cntn` branches
    into `work` and `retire`, a decision state is declared on the outputs
    of arvl_to_dcsn, line 5, and listed by its name on that block's own
    inputs, line 9, the side `_targets` names for the decision table, which
    holds one group; the nested blocks of lines 10 and 11, whose inputs
    are empty and which read the decision fields of line 9, are unchanged,
    and each continuation group still writes a state into its own branch's
    block alone (L-D1; AMD-MI-002 §5 rule 2). With `h = a` written into
    arvl_to_dcsn, the stage constructs with h among its decision fields."""
    text = (ROOT / RET_CHOICE_PATH).read_text(encoding="utf-8")
    edits = added_edits(text, RET_CHOICE_PATH, "dcsn", "h", "ℝ₊")
    assert edits == (
        model.Replacement(5, 48, 5, 48, ", h : ℝ₊"),
        model.Replacement(9, 51, 9, 51, ", h"),
    )
    after = applied(text, edits)
    assert changed_lines(text, after) == [5, 9]
    assert after.split("\n")[8] == (
        "[id=dcsn_to_cntn, (a_d, d : !ctrl @ {work, retire}, h) : !dcsn -> ()] {"
    )
    defined = edited(after, 6, after.split("\n")[5] + "\n    h = a")
    assert "ret_choice:dcsn:h" in decision_fields(defined, RET_CHOICE_PATH)
    groups = model.classification(
        model.elaborate_buffer(text, RET_CHOICE_PATH).stage, source_spans(text, RET_CHOICE_PATH)
    )
    assert [
        (group.branch, [target.name_alone for target in group.targets["state"]])
        for group in groups[2:]
    ] == [("work", [False]), ("retire", [False]), (model.ALL_BRANCHES, [False, False])]


def test_l_the_three_forms_of_a_side_that_takes_the_name_alone(cons_text):
    """A side that lists a decision field by its name alone (L-D1) takes it
    in the three forms of T-R6: after its last field (the tests above);
    inside the parentheses of an empty side, the nested `()` of
    ret_choice.bl's `work` on line 10, as `h`; and around a bare side,
    `V : !dcsn` on line 26 of ez_savings.bl as it stood with its arrival
    builders, `tests/fixtures/ez_savings_with_arrival.bl` (decision MB-V46),
    which the same edit parenthesizes, as `h : !dcsn`, the name carrying the
    perch word that the side then no longer writes; no set and no role word
    is written."""
    work_text = (ROOT / RET_CHOICE_PATH).read_text(encoding="utf-8")
    ez_text = (Path(__file__).parent / "fixtures/ez_savings_with_arrival.bl").read_text(
        encoding="utf-8"
    )
    work_spans, ez_spans = source_spans(work_text, "ret_choice.bl"), source_spans(ez_text, "ez.bl")
    change = {
        "kind": "add",
        "perch": "dcsn",
        "branch": None,
        "field": "h",
        "set": "ℝ₊",
        "role": "state",
    }
    empty = model.Target(work_spans["dcsn_to_cntn.work.in"], None, False, name_alone=True)
    edits = model.classification_edits(
        (model.Group("dcsn", None, (), {"state": (empty,)}),), change
    )
    assert applied(work_text, edits).split("\n")[9] == (
        "    [label=work,   (h) -> (a_w : ℝ₊) : !cntn] { a_w = a_d }"
    )
    bare = model.Target(
        ez_spans["dcsn_to_arvl.in"], ez_spans["dcsn_to_arvl.in.V"], True, name_alone=True
    )
    edits = model.classification_edits(
        (model.Group("dcsn", None, (), {"state": (bare,)}),), change
    )
    assert applied(ez_text, edits).split("\n")[25] == (
        "[id=dcsn_to_arvl, (V : !dcsn, h : !dcsn) -> (V[<] : ℝ @ !vlu) : !arvl] {"
    )


# --- unit R: the paper button (spec 0.4 §5.5; brief rule 7) ---


def test_r_write_paper_writes_the_cards_the_drawing_and_the_digests_once(scratch_folder):
    """`write_paper` writes `paper/cons.md` and `paper/cons.svg` and answers
    their paths (spec 0.4 §5.5; brief rule 7; review 2; R-D17, R-D37). The
    drawing is the backward builders graph's,
    `stage.builder.bwd.diagram().svg()`. The Markdown opens with the
    heading `cons`, which carries its one footnote; it holds the printed card
    of each builder in a fenced block, backward then forward, then the
    image link to the drawing; the footnote gives the path and the whole
    SHA-256 digest of the stage file and of each binding file. A second
    call, with the text changed, answers the empty tuple and leaves both
    files as they were written."""
    folder = model.open_folder(scratch_folder)
    text = (scratch_folder / CONS).read_text(encoding="utf-8")
    stage = bound_as_the_recipe_binds(scratch_folder, text, CONS)
    bound = ("declaration/spec.yml", "declaration/calibration/portfolio.yml")
    paths = [scratch_folder / name for name in bound]
    source_digests = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    written = model.write_paper(folder, stage, CONS, text, source_digests)
    assert written == ("paper/cons.md", "paper/cons.svg")
    markdown = (scratch_folder / "paper/cons.md").read_text(encoding="utf-8")
    assert (scratch_folder / "paper/cons.svg").read_text(encoding="utf-8") == (
        stage.builder.bwd.diagram().svg()
    )
    assert markdown.startswith("# cons[^digests]\n")
    cards = [
        str(graph[name].denote())
        for graph in (stage.builder.bwd, stage.builder.fwd)
        for name in graph.list().names
    ]
    places = [markdown.index(f"```\n{card}\n```\n") for card in cards]
    assert len(places) == 5 and places == sorted(places)
    link = markdown.index("\n![cons](cons.svg)\n")
    assert link > places[-1]
    body, footnote = markdown.split("\n[^digests]: ")
    assert link < len(body) and footnote.count("\n") == 1 and footnote.endswith(".\n")
    digests = {CONS: hashlib.sha256(text.encode("utf-8")).hexdigest()}
    digests.update({name: source_digests[str(scratch_folder / name)] for name in bound})
    for path, digest in digests.items():
        assert f"`{path}` `{digest}`" in footnote
    before = {name: (scratch_folder / name).read_bytes() for name in written}
    changed = edited(text, 1, "@stage: cons  # changed")
    assert model.write_paper(folder, stage, CONS, changed, source_digests) == ()
    assert {name: (scratch_folder / name).read_bytes() for name in written} == before


def test_r_paper_writes_nothing_where_the_drawing_is_refused(
    scratch_folder, cons, cons_text, tmp_path, monkeypatch
):
    """Where no layout program is found, `write_paper` raises the package's
    refusal, the sentence of `layout_refusal()` whole, and writes nothing:
    `paper/` does not exist (spec 0.4 §5.5; review 2). The search path
    names an empty folder, and the other places `layout_command` reads,
    nvm's and Homebrew's Node and the repository's Node package, are set
    aside."""
    folder = model.open_folder(scratch_folder)
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    monkeypatch.setattr(graphviz_layout, "NVM_NODES", empty)
    monkeypatch.setattr(graphviz_layout, "HOMEBREW_NODES", ())
    monkeypatch.setattr(graphviz_layout, "REPOSITORY_ROOT", empty)
    assert graphviz_layout.layout_command() is None
    with pytest.raises(RuntimeError) as refused:
        model.write_paper(folder, cons, CONS, cons_text, {})
    assert str(refused.value) == graphviz_layout.layout_refusal()
    assert not (scratch_folder / "paper").exists()
