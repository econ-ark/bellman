"""The acceptance file of unit A of the build of specification 0.6, marginal
blocks and the method `!marginals`: one test for each of the brief's
acceptance items 1 to 5, on the stage file of the specification's §3, the
block file of its §4 and its §4 methods file, which stand under
`fixtures/spec_0_6/`. Item 6, the six named test files and the fast core as at
the base, is verified by the runs the unit's report records. The rulings the
build took are the rows SA of the development repository's decisions file
`SA-marginal-blocks.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import ROOT

from bellman.graphs.initial_diagrams import GRAINS
from bellman.refusals import ConstructionError
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.grains import block_id_of, construction_table, graph_of, wire_table
from bellman.stage.stage_answers import source_spans
from bellman.syntax.source import to_source

FIXTURES = Path(__file__).parent / "fixtures" / "spec_0_6"
ORACLE = ROOT / "applications/portfolio-choice/declaration/stages/cons/cons.bl"
VALUE_BUILDERS = ("cntn_to_dcsn", "dcsn_to_arvl")


def test_item_1_the_marginal_block_binds_at_the_evaluation_and_the_signature_holds_values_alone():
    """The §4 methods file binds on the §3 stage: `!marginals` stands at the
    decision builder's Evaluation; the builder's signature and the stage's
    backward signature hold values alone, the Evaluation writing `V` and
    nothing beside it; the Evaluation records the block's derivative line by
    the coordinate `m_d`, and the Sort of `V` names it; and a representation
    of the stated derivative, written at the Evaluation,
    `cntn_to_dcsn.evaluate.marginal`, stands beside `!marginals` there, a
    binding of another kind (AMD-MB-001 §5.1, D4, D6; decision SD-15;
    AMD-MB-002). The arrival builder `V[<] = V` passes the derivative through
    and takes no marginal block (D3, P1)."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    assert stage.methodize(FIXTURES / "methods_marginals.yml") is stage
    assert str(stage.methods).splitlines() == [
        "policy                    !egm   block methods/cons_egm.bl",
        "cntn_to_dcsn:Evaluation   !marginals   block methods/cons_egm.bl",
    ]
    signature = stage.builder["cntn", "dcsn"].signature()
    assert [str(wire.identity) for wire in signature.outputs] == ["cons:function:dcsn:V"]
    assert [str(wire.identity) for wire in signature.inputs] == ["cons:function:cntn:V"]
    evaluation = [
        row
        for row in construction_table(stage).by_builder("cntn_to_dcsn")
        if row.kind == "Evaluation"
    ]
    assert [entry[0].field for row in evaluation for entry in row.derivatives] == ["m_d"]
    assert [entry[2] for row in evaluation for entry in row.derivatives] == ["cntn_to_dcsn.envelope"]
    assert [c.field for c in wire_table(stage).sort_of(evaluation[0].outputs[0]).derivatives] == ["m_d"]
    card = str(stage.denote())
    backward = card[card.index("  backward\n") : card.index("  forward\n")].splitlines()
    named = [
        line.split()[1] if line.split()[0] in ("in", "out") else line.split()[0]
        for line in backward[1:]
        if line.strip() and not line.strip().startswith("─")
    ]
    assert named == ["𝑉≻", "𝑉≺", "𝑐"]
    stage.methodize(
        {
            "methods": [
                {
                    "on": "cntn_to_dcsn.evaluate.marginal",
                    "method": "!Linear",
                    "settings": {
                        "grid": "!Cartesian",
                        "orders": {"m_d": "n_m"},
                        "bounds": {"m_d": ["m_min", "m_max"]},
                    },
                }
            ]
        }
    )
    assert "cntn_to_dcsn:Evaluation   !Linear" in str(stage.methods)
    assert "cntn_to_dcsn:Evaluation   !marginals   block methods/cons_egm.bl" in str(stage.methods)


def test_item_2_the_bound_value_builders_are_the_oracle_s_graph():
    """The oracle: the two value builders of the bound stage are compared,
    operation by operation (kind, inputs, outputs, rule), wire by wire
    (identity, perch, role) and box for box at each of the five grains, with
    the graph the present
    `applications/portfolio-choice/declaration/stages/cons/cons.bl`
    elaborates to, with no difference: the oracle writes the derivative
    line `D_{m_d}V = 𝑑𝑢(c)` in its stage file and the block file states the
    same line, each recorded at the decision builder's Evaluation
    (AMD-MB-001 §4.1, D4). The present file's methods file binds `!egm` on an
    argmax-only policy block, which `methodize` refuses, and no line of it
    names a block, so the graph is the one it elaborates to. The policy
    builder is not compared: the block opens it in the bound stage, and the
    present file writes the maximization alone (unit B's item 1). The
    declared sets are not compared, since they are each file's own
    declarations: the §3 file declares `V` in ℝ and `dV` in ℝ₊₊ and the
    arrival state `m` alone, and the present file declares [−∞, ∞), (0, ∞]
    and the second arrival state `l` (decision SA-8)."""
    bound = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    bound.methodize(FIXTURES / "methods_marginals.yml")
    present = elaborate_stage(load_stage(ORACLE))

    def operations(stage):
        return {
            (row.builder, index): (
                row.kind,
                tuple(map(str, row.inputs)),
                tuple(map(str, row.outputs)),
                tuple(to_source(term) for term in row.equations),
            )
            for builder in VALUE_BUILDERS
            for index, row in enumerate(construction_table(stage).by_builder(builder))
        }

    def wires(stage):
        table = wire_table(stage)
        return {
            str(identity): (table.sort_of(identity).perch, table.sort_of(identity).role)
            for builder in VALUE_BUILDERS
            for row in construction_table(stage).by_builder(builder)
            for identity in (*row.inputs, *row.outputs)
        }

    ours, theirs = operations(bound), operations(present)
    assert set(ours) == set(theirs)
    differences = {key: (theirs[key][3], ours[key][3]) for key in ours if ours[key] != theirs[key]}
    assert differences == {}
    assert wires(bound) == wires(present)

    def boxes(stage, grain):
        return [
            (
                box.name,
                [str(s.identity) for s in box.dom.inside],
                [str(s.identity) for s in box.cod.inside],
            )
            for box in graph_of(stage, "builders", "backward", grain).boxes
            if getattr(box, "identity", None) is not None and block_id_of(box) in VALUE_BUILDERS
        ]

    # box for box and wire for wire at each of the five grains
    assert all(boxes(bound, grain) == boxes(present, grain) for grain in GRAINS)


def test_item_3_the_declared_builders_and_the_initial_diagrams_are_the_objects_held_before():
    """`stage.declared` and the two initial diagrams are the objects they
    were before the `!marginals` bindings, and the declared decision
    builder's card is the card printed before them, byte for byte."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    declared = [stage.declared[pair].box for pair in (("cntn", "dcsn"), ("dcsn", "arvl"))]
    card = str(stage.declared["cntn", "dcsn"].denote())
    backward, forward = stage.initial.backward.graph, stage.initial.forward.graph
    stage.methodize(FIXTURES / "methods_marginals.yml")
    after = [stage.declared[pair].box for pair in (("cntn", "dcsn"), ("dcsn", "arvl"))]
    assert all(one is other for one, other in zip(after, declared, strict=True))
    assert stage.builder["cntn", "dcsn"].box is not declared[0]
    assert stage.initial.backward.graph is backward and stage.initial.forward.graph is forward
    assert str(stage.declared["cntn", "dcsn"].denote()) == card


@pytest.mark.parametrize(
    ("on", "block", "words"),
    [
        (
            "cntn_to_dcsn",
            "[id=dcsn_marginal, (c, W[>]) : !cntn -> (V) : !dcsn] {\n"
            "    D_{m_d}V = 𝑑𝑢(c) + W[>]\n}\n",
            (
                "(c, W[>]) : !cntn -> (V) : !dcsn",
                "(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn",
            ),
        ),
        (
            "dcsn_to_arvl",
            "[id=dcsn_marginal, (c) : !cntn -> (V) : !dcsn] {\n    D_{m_d}V = 𝑑𝑢(c)\n}\n",
            (
                "(c) : !cntn -> (V) : !dcsn",
                "(V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl",
            ),
        ),
        (
            "cntn_to_dcsn",
            "[id=dcsn_marginal, (c, m_d) : !cntn -> (V) : !dcsn] {\n    D_{m_d}V = 𝑑𝑢(c)\n}\n",
            (
                "(c, m_d) : !cntn -> (V) : !dcsn",
                "(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn",
            ),
        ),
        (
            "cntn_to_dcsn",
            "[id=dcsn_marginal, (c, a[>]) : !cntn -> (V) : !dcsn] {\n    D_{m_d}V = 𝑑𝑢(c)\n}\n",
            (
                "(c, a[>]) : !cntn -> (V) : !dcsn",
                "(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn",
            ),
        ),
    ],
    ids=[
        "an input the builder does not have",
        "a block that joins other perches",
        "a state of the output perch",
        "a state of the input perch",
    ],
)
def test_item_4_a_marginal_block_whose_header_does_not_match_its_builder_is_refused(
    on, block, words, tmp_path
):
    """A marginal block that reads an input the builder does not have, that
    joins perches other than the builder's, or that lists a state, is
    refused under `block-header-mismatch` with the two signatures, and the
    refused binding leaves the stage symbolic: its header is the builder's
    own restricted to what its lines read, with no extended signature
    (AMD-MB-001 §3, §5.1)."""
    (tmp_path / "marginal.bl").write_text(
        "@stage: cons\n𝑑𝑢 := D_{c}(𝑢)\n\n" + block, encoding="utf-8"
    )
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    source = {
        "methods": [{"on": on, "method": "!marginals", "block": str(tmp_path / "marginal.bl")}]
    }
    with pytest.raises(ConstructionError) as refused:
        stage.methodize(source)
    assert refused.value.rule == "block-header-mismatch"
    assert all(word in refused.value.message for word in words)
    assert repr(stage) == "ElaboratedStage('cons', symbolic)"


def test_item_5_every_row_of_the_bound_builders_has_a_source_line_in_a_file():
    """Every row of the three bound builders has a source line in the stage
    file or the block file: a row realizing lines by those lines, a Pullback
    by the line of the law of motion it composes with, an Evaluation by the
    header fields it writes; no row stands without one, so no row is a
    derivative the package formed; the envelope line stands on the decision
    builder's Evaluation as a stated derivative with its source line, and is
    no row (AMD-MB-001 D4)."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    stage.methodize(FIXTURES / "methods_marginals.yml")
    spans, definitions = source_spans(stage), stage.definitions
    files = {str(FIXTURES / "cons.bl"), str(FIXTURES / "methods" / "cons_egm.bl")}
    rows = [
        row
        for builder in ("policy", *VALUE_BUILDERS)
        for row in construction_table(stage).by_builder(builder)
    ]
    assert len(rows) == 10
    for row in rows:
        if row.kind == "Pullback" and not row.statements:
            addresses = [definitions[row.definition].address]
        elif row.kind == "Evaluation":
            addresses = [
                f"{row.builder}.out.{identity.field}{'[<]' if identity.perch == 'arvl' else ''}"
                for identity in row.outputs
            ]
        else:
            addresses = list(row.statements)
        assert addresses and all(spans[address].file in files for address in addresses), row
    stated = [
        entry[2]
        for row in rows
        if row.kind == "Evaluation" and row.builder == "cntn_to_dcsn"
        for entry in row.derivatives
    ]
    assert stated == ["cntn_to_dcsn.envelope"]
    assert [spans["cntn_to_dcsn.envelope"].file, spans["cntn_to_dcsn.envelope"].line] == [
        str(FIXTURES / "methods" / "cons_egm.bl"),
        11,
    ]
