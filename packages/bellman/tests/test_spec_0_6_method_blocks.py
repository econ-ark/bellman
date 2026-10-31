"""The acceptance file of unit B of the build of specification 0.6, method
blocks and the one stage: one test for each of the brief's acceptance items
1 to 4, on the stage file of the specification's §3, the block file of its §4
and the first line of its §4 methods file, which stand under
`fixtures/spec_0_6/`. Items 5 and 6, the five named test files and the fast
core as at the base, are verified by the runs the unit's report records. The
rulings the build took are the rows SB of the development repository's decisions file
`SB-method-blocks-and-the-one-stage.md`.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import pytest
from conftest import ROOT

from bellman.refusal_catalogue import refusal_of
from bellman.refusal_examples import EXAMPLES
from bellman.refusals import ConstructionError, TargetError
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.grains import declared_table

FIXTURES = Path(__file__).parent / "fixtures" / "spec_0_6"
# the buffer-stock stage file written the explicit way, its policy block holding
# the inverse Euler lines and the grid line, as it stood before the application
# moved those lines to a method block (decision MB-S13)
BUFFER_STOCK = FIXTURES / "buffer_stock_explicit.bl"


def test_item_1_methodize_opens_the_policy_builder_with_the_block_and_returns_the_same_stage():
    """`stage.methodize(methods)` returns the stage it is called on; the
    binding prints with its block file; the policy builder reads `V[>]` alone
    and writes `c` (AMD-MB-001 R4); and its card prints the declared argmax line, the
    three method rows, the condition `egm-eligibility`, the method and both
    files."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    assert stage.methodize(FIXTURES / "methods.yml") is stage
    assert str(stage.methods) == "policy   !egm   block methods/cons_egm.bl"
    signature = stage.builder.policy.signature()
    assert [str(wire.identity) for wire in signature.inputs] == ["cons:function:cntn:V"]
    assert [str(wire.identity) for wire in signature.outputs] == ["policy:Evaluation:c:result"]
    card = str(stage.builder.policy.denote())
    assert "\nDeclared\n  𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]\n" in card
    operations = card[card.index("\nOperations\n") : card.index("\nConditions\n")]
    assert [line.split()[1] for line in operations.splitlines() if line[2:3].isdigit()] == [
        "InvEuler:Aggregation",
        "grid:Aggregation",
        "identification:Pullback",
        "Evaluation",
    ]
    assert "  policy            egm-eligibility: the construction satisfies the declared\n" in card
    assert "\nMethod\n  !egm   block methods/cons_egm.bl" in card
    source = card[card.index("\nSource") : card.index("\nDefinitions referenced")]
    # one section for each file, the stage file's first, its lines by
    # number, as the cards of the specification's §8 print them (decisions
    # SC-12 and SC-18)
    assert [
        line.split()[0] if line.startswith("  ") else line
        for line in source.splitlines()[1:]
        if line.startswith("Source") or line[2:3].isdigit()
    ] == ["Source  cons.bl", "21", "Source  cons_egm.bl", "6", "7", "8"]


def test_item_1_the_encoding_of_a_stage_bound_with_blocks_passes_the_schema_check():
    """The encoding of a stage whose methods name a block file passes
    `validate_encoding`: each method entry that names a block file writes it
    under `block`, in the bindings, on the boxes and on their pieces, and the
    schema admits that key (decision SD-16)."""
    from bellman.display.encoding_checks import validate_encoding

    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    stage.methodize(FIXTURES / "methods_marginals.yml")
    document = stage.encoding()
    assert {key: entry["block"] for key, entry in document["bindings"]["methods"].items()} == {
        "policy": "methods/cons_egm.bl",
        "cntn_to_dcsn:Evaluation": "methods/cons_egm.bl",
    }
    assert validate_encoding(document) is document


def test_item_2_the_binding_leaves_the_declared_builders_and_the_initial_diagrams_as_they_were():
    """Before the binding `stage.declared.policy` is `stage.builder.policy`;
    after it, the declared policy builder and the two initial diagrams are the
    objects they were, and the declared builder's card is the card printed
    before the binding, byte for byte."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    declared, operative = stage.declared.policy, stage.builder.policy
    assert declared == operative and declared.box is operative.box
    card = str(declared.denote())
    backward, forward = stage.initial.backward.graph, stage.initial.forward.graph
    stage.methodize(FIXTURES / "methods.yml")
    assert stage.declared.policy.box is declared.box
    assert stage.builder.policy.box is not declared.box
    assert (stage.initial.backward.graph, stage.initial.forward.graph) == (backward, forward)
    assert stage.initial.backward.graph is backward and stage.initial.forward.graph is forward
    assert str(stage.declared.policy.denote()) == card


def test_item_2_the_binding_leaves_the_other_cards_and_the_policy_s_declared_type():
    """The cards of the builders the block does not open, the decision
    builder and the forward builder at the policy, are byte-identical before
    and after the binding, and the policy is typed once, on its declared
    output, `𝑐(m_d) ∈ Γ(m_d)` on the opened builder's out line and its
    Evaluation (§4.2; the review of unit B, finding 1; decision SA-14)."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    pairs = (("cntn", "dcsn"), ("dcsn", "cntn"))
    before = [str(stage.builder[pair].denote()) for pair in pairs]
    stage.methodize(FIXTURES / "methods.yml")
    assert [str(stage.builder[pair].denote()) for pair in pairs] == before
    card = str(stage.builder.policy.denote()).splitlines()
    assert "  out  𝑐   : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)" in card
    assert "     rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)" in card


def test_item_2_a_bound_stage_keeps_its_declared_rows_through_a_pickle_round_trip():
    """A bound stage read back from its pickle holds the declared policy rows
    of the stage file and the conditions in their order (the review of unit
    B, finding 4; decision SA-17)."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    rows = [row.identity for row in declared_table(stage).by_builder("policy")]
    stage.methodize(FIXTURES / "methods.yml")
    obligations, card = str(stage.obligations()), str(stage.declared.policy.denote())
    back = pickle.loads(pickle.dumps(stage))
    assert [row.identity for row in declared_table(back).by_builder("policy")] == rows
    assert str(back.obligations()) == obligations
    assert str(back.declared.policy.denote()) == card


def test_item_3_a_later_solution_binding_on_the_opened_builder_replaces_its_block():
    """A later handler on the opened builder replaces the method that named
    the block, and the block with it: the builder is the declared one again
    and `egm-eligibility` is no longer listed; a later `!egm` without a block
    is placed on the builder as declared, without the block it replaces, and
    is refused there, leaving the stage as it was (the review of unit B,
    finding 3; decision SA-16)."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    stage.methodize(FIXTURES / "methods.yml")
    stage.methodize({"methods": [{"on": "policy", "handler": "hark"}]})
    assert "block" not in str(stage.methods)
    assert stage.builder.policy.box is stage.declared.policy.box
    assert all(item.condition != "egm-eligibility" for item in stage.obligations())
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    stage.methodize(FIXTURES / "methods.yml")
    with pytest.raises(TargetError, match="grid line"):
        stage.methodize({"methods": [{"on": "policy", "method": "!egm"}]})
    assert str(stage.methods) == "policy   !egm   block methods/cons_egm.bl"


def test_item_3_a_later_block_replaces_the_earlier_and_the_explicit_writing_binds_as_today():
    """A second `methodize` with another block for `policy` replaces the
    first block's rows: the second block's two explicit lines, the candidate
    and the cash on hand, stand as one Aggregation at the builder grain, as
    the fold merges compatible pointwise lines; the buffer-stock stage file
    written the explicit way, whose policy block writes the grid line, binds `!egm` at
    `policy:Evaluation`, and its card gains the `Method` section and nothing
    else; a binding of another kind stands beside one at its box, and a line
    the block adds is the target of a later line of the same source
    (decision SD-15)."""
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    stage.methodize(FIXTURES / "methods.yml")
    assert stage.methodize(FIXTURES / "methods_interior.yml") is stage
    assert str(stage.methods) == "policy   !egm   block methods/cons_egm_interior.bl"
    rows = [
        box.name for box in stage.builder.policy.box.arg.boxes if box.name.startswith("policy")
    ]
    assert rows == ["policy.cash:Aggregation", "policy.on_grid:Pullback", "policy:Evaluation"]
    buffer_stock = elaborate_stage(load_stage(BUFFER_STOCK))
    before = str(buffer_stock.builder.policy.denote()).splitlines()
    assert (
        buffer_stock.methodize({"methods": [{"on": "policy", "method": "!egm"}]}) is buffer_stock
    )
    assert str(buffer_stock.methods) == "policy:Evaluation   !egm"
    after = str(buffer_stock.builder.policy.denote()).splitlines()
    at = after.index("Method")
    assert after[at - 1 : at + 2] == [
        "",
        "Method",
        "  !egm   handler                                             policy:Evaluation",
    ]
    assert after[: at - 1] + after[at + 2 :] == before
    # a binding of another kind stands beside it at the box, and a later
    # binding of one kind replaces the earlier (decision SD-15)
    buffer_stock.methodize({"methods": [{"on": "policy", "method": "!Linear"}]})
    buffer_stock.methodize({"methods": [{"on": "policy", "method": "!pchip"}]})
    assert str(buffer_stock.methods) == "policy:Evaluation   !egm\npolicy:Evaluation   !pchip"
    # a line a block adds is the target of a later line of the same source
    block = str(FIXTURES / "methods" / "cons_egm.bl")
    stage.methodize(
        {
            "stage": "cons",
            "methods": [
                {"on": "policy", "method": "!egm", "block": block},
                {"on": "policy.identification", "method": "!Linear"},
            ],
        }
    )
    assert (
        str(stage.methods)
        == f"policy              !egm   block {block}\npolicy:Evaluation   !Linear"
    )


@pytest.mark.parametrize(
    ("header", "words"),
    [
        ("(V[>] : ℝ₊₊ @ !vlu)", ("`V[>]`", "ℝ₊₊", "ℝ")),
        ("(V[>], W[>] : ℝ @ !vlu)", ("`W[>]`",)),
    ],
    ids=["a field declared with another set", "an added input"],
)
def test_item_4_a_header_that_declares_a_field_anew_or_adds_a_value_input_is_refused(
    header, words, tmp_path
):
    """A method block's header that gives a field the stage file declares
    another set, or that adds an input the builder does not have, is
    refused under `block-header-mismatch`: a block's inputs are among the
    builder's own, there being no extended signature (the review of unit
    B, finding 2; decision SA-15; AMD-MB-001 §5.1)."""
    text = (FIXTURES / "methods" / "cons_egm.bl").read_text(encoding="utf-8")
    (tmp_path / "egm.bl").write_text(
        text.replace("(V[>])", header, 1), encoding="utf-8"
    )
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    source = {"methods": [{"on": "policy", "method": "!egm", "block": str(tmp_path / "egm.bl")}]}
    with pytest.raises(ConstructionError) as refused:
        stage.methodize(source)
    assert refused.value.rule == "block-header-mismatch"
    assert all(word in refused.value.message for word in words)
    assert repr(stage) == "ElaboratedStage('cons', symbolic)"


@pytest.mark.parametrize(
    ("rule", "words"),
    [
        ("block-header-mismatch", ("(V[>]) : !cntn -> (c) : !dcsn", "no other field")),
        ("block-name-undefined", ("calls '𝑑𝑢𝑖𝑛𝑣'",)),
    ],
)
def test_item_4_the_two_refusals_of_a_method_block_refuse_at_methodize_and_stand_in_the_catalogue(
    rule, words, tmp_path
):
    """A block whose header does not match its builder and a line calling a
    function neither file defines are refused at `methodize`, under their
    rules, with the two signatures or the name, from the examples of the
    catalogue; a refused binding leaves the stage symbolic. The refusal of
    `!marginals` until unit A, which this test asserted, ends with unit A
    (decision SA-11)."""
    example = EXAMPLES[rule]
    error = refusal_of(example)
    assert isinstance(error, ConstructionError)
    assert (error.rule, error.address, error.file) == (rule, example.address, "egm.bl")
    assert all(word in error.message for word in words)
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    (tmp_path / "egm.bl").write_text(example.files["egm.bl"], encoding="utf-8")
    (tmp_path / "methods.yml").write_text(
        "methods:\n  - on: policy\n    method: !egm\n    block: egm.bl\n", encoding="utf-8"
    )
    with pytest.raises(ConstructionError) as refused:
        stage.methodize(tmp_path / "methods.yml")
    assert (refused.value.rule, refused.value.message) == (rule, error.message)
    assert repr(stage) == "ElaboratedStage('cons', symbolic)"


def test_item_4_a_function_the_block_file_writes_with_its_argument_is_a_name_it_defines(tmp_path):
    """A function the block file writes with its argument in closed form,
    `𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)`, is a name the block file defines, as
    `𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)` is: the block that calls it binds (decision SD-24).
    The candidate line reads `D_{a}V[>]`, which compiles to no kernel
    (AMD-MB-001, the plan's P3), so the kernel is not asked for."""
    text = (FIXTURES / "methods" / "cons_egm.bl").read_text(encoding="utf-8")
    closed = text.replace("𝑑𝑢     := D_{c}(𝑢)", "𝑑𝑢(c : ℝ₊₊) := c^(-ρ)", 1).replace(
        "𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)", "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)", 1
    )
    assert "D_{c}" not in closed and "Inv(" not in closed
    (tmp_path / "egm.bl").write_text(closed, encoding="utf-8")
    stage = elaborate_stage(load_stage(FIXTURES / "cons.bl"))
    stage.methodize({"methods": [{"on": "policy", "method": "!egm", "block": str(tmp_path / "egm.bl")}]})
    assert str(stage.methods).startswith("policy   !egm   block ")


def test_item_4_an_operator_the_language_writes_as_a_call_is_no_name_the_block_file_defines():
    """`upper_env`, the upper envelope, is an operator of the language that the
    grammar writes as an ordinary call, as it writes `evaluate`
    (`CALL_OPERATORS` of `typing/line_unknowns.py`), and no function a file
    defines: the worker's method block of the retirement model, whose last
    line is `c = upper_env(w[>], c[>], v[>])`, opens the policy builder, and
    the entry binding `!FUES` on `upper_env` stands on that line of the block
    (decision SD-15)."""
    folder = ROOT / "applications/retirement-choice/declaration/stages/worker_cons"
    stage = elaborate_stage(load_stage(folder / "worker_cons.bl"))
    assert stage.methodize(folder / "methods.yml") is stage
    printed = [line.split() for line in str(stage.methods).splitlines()]
    assert ["policy", "!egm", "block", "../../methods/worker_cons_egm.bl"] in printed
    assert ["policy.envelope", "!FUES"] in printed


def test_item_3_a_method_at_a_declared_line_a_block_stands_in_for_is_refused(tmp_path):
    """On the demonstration's portfolio stage, whose policy builder its block
    `foc` opens, an entry naming an occurrence in the declared line
    `policy.objective`, which forms no operation of the opened builder, is
    refused under `method-attachment`, naming the block file and the block's
    own line that holds the operator, `policy.euler.E_Ψ_θ`; the stage keeps
    the bindings it held (decision SC-23)."""
    demonstration = ROOT / "applications/cons-port/declaration"
    (tmp_path / "port_foc.bl").write_text(
        (demonstration / "methods/port_foc.bl").read_text(encoding="utf-8"), encoding="utf-8"
    )
    stage = elaborate_stage(load_stage(demonstration / "stages/port/port.bl"))
    with pytest.raises(TargetError) as refused:
        stage.methodize(
            {
                "methods": [
                    {
                        "on": "policy",
                        "method": "!time-iteration",
                        "block": str(tmp_path / "port_foc.bl"),
                    },
                    {
                        "on": "policy.objective.E_Ψ_θ",
                        "method": "!gauss-hermite",
                        "settings": {"n_nodes": ["n_Ψ_nodes", "n_θ_nodes"]},
                    },
                ]
            }
        )
    assert refused.value.rule == "method-attachment"
    assert "port_foc.bl" in str(refused.value) and "policy.euler.E_Ψ_θ" in str(refused.value)
    assert repr(stage) == "ElaboratedStage('port', symbolic)"



def test_item_4_a_joint_maximization_reads_an_earlier_binder_in_a_later_feasible_set():
    """A binder of a maximization is in scope in the feasible sets of the
    binders written after it: the durables adjuster, whose policy block states
    the joint maximization `(c, h_choice) = argmax_{c : Γ_c(m), h_choice :
    Γ_h(m - c)}(…)` alone, the set of `h_choice` reading `c`, elaborates with
    the declared policy rows Pullback, Aggregation, Argmax and Evaluation, and
    its methods file opens the policy builder with the block `egm` (decision
    MB-U3)."""
    folder = ROOT / "applications/durables/declaration/stages/adjuster_cons"
    stage = elaborate_stage(load_stage(folder / "adjuster_cons.bl"))
    assert [row.kind for row in declared_table(stage).by_builder("policy")] == [
        "Pullback",
        "Aggregation",
        "Argmax",
        "Evaluation",
    ]
    assert stage.methodize(folder / "methods.yml") is stage
    printed = [line.split() for line in str(stage.methods).splitlines()]
    assert ["policy", "!egm", "block", "../../methods/adjuster_cons_egm.bl"] in printed


def test_item_4_a_marginal_block_shares_its_builder_with_another_method():
    """A methods file binds `!marginals` on a value builder beside an entry of
    another method on the same builder, the durables tenure stage's `!Linear`
    on `cntn_to_dcsn`: both stand at the builder's Evaluation and the marginal
    block's derivative lines are recorded there; a second `!marginals` entry on
    the same builder is refused as a duplicate target (decision MB-U4)."""
    from bellman.stage.grains import construction_table

    folder = ROOT / "applications/durables/declaration/stages/tenure"
    stage = elaborate_stage(load_stage(folder / "tenure.bl"))
    assert stage.methodize(folder / "methods.yml") is stage
    printed = [line.split()[:2] for line in str(stage.methods).splitlines()]
    assert ["cntn_to_dcsn:Evaluation", "!marginals"] in printed
    assert ["cntn_to_dcsn:Evaluation", "!Linear"] in printed
    (evaluation,) = [
        row
        for row in construction_table(stage).primitive_rows
        if row.kind == "Evaluation" and row.builder == "cntn_to_dcsn"
    ]
    assert [(coordinate.field, address) for coordinate, _, address, _ in evaluation.derivatives] == [
        ("a_d", "cntn_to_dcsn.marginal_assets"),
        ("h_d", "cntn_to_dcsn.marginal_housing"),
    ]
    block = str(ROOT / "applications/durables/declaration/methods/marginals_tenure.bl")
    entry = {"on": "cntn_to_dcsn", "method": "!marginals", "block": block}
    with pytest.raises(ValueError, match="Duplicate methodization target 'cntn_to_dcsn'"):
        elaborate_stage(load_stage(folder / "tenure.bl")).methodize({"methods": [entry, entry]})


def test_item_4_a_method_choice_on_a_builder_keeps_the_marginal_block_bound_there():
    """A recipe merges a method choice into a methods list entry by entry,
    matching an entry of the same method kind on the same target: the
    durables adjuster's choice of `!vfi` on `cntn_to_dcsn` is added beside the
    `!marginals` entry its methods file writes on that builder, which keeps
    its method and its block (decision MB-U4)."""
    from bellman.trellis import load_recipe

    choice = {
        "methods": [
            {"on": "cntn_to_dcsn", "method": "!vfi", "handler": "fues-durables:make_adjuster_vfi"}
        ]
    }
    syntactic = load_recipe(
        ROOT / "applications/durables/declaration", "spec.two-stages.yml", adjuster_method=choice
    )
    entries = syntactic["periods"][0]["stages"]["adjuster_cons"]["methods"]["methods"]
    assert [
        (entry.get("method"), entry.get("block"), entry.get("handler"))
        for entry in entries
        if entry["on"] == "cntn_to_dcsn"
    ] == [
        ({"__yaml_tag__": "marginals", "value": ""}, "../../methods/marginals_adjuster_cons.bl", None),
        ("!vfi", None, "fues-durables:make_adjuster_vfi"),
    ]
