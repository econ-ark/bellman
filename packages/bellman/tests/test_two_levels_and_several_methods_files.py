"""The two levels of a stage and several methods files: the conditions that a
solution method adds and the graphs and equations that it leaves unchanged,
the operative and the declared levels, the union of a stage file with its
additions, and the additions and refusals files of the case studies."""

import functools
import json
from pathlib import Path

import pytest
from application_files import (
    BUFFER_STOCK_FILE,
    BUFFER_STOCK_METHODS,
    BUFFER_STOCK_PENSION_FOLDER,
    CONS_METHODS,
    CORPUS,
    FIXTURES_FOLDER,
    RETIREMENT_CHOICE_PENSION_FOLDER,
    ROOT,
)
from printed_text import parse_card
from stage_builders import differing_graph_triples, places_of, stage_from_text
from stage_texts import addition_of_text, corpus_text, line_of, methods_addition
from two_sets import one_row_by_default

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.stage import elaborate_stage, load_stage
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.union import union

# the folder of the additions and of the refusals files of the case studies
ADDITIONS = ROOT / "packages/bellman/tests/additions"


# the folder of a retirement choice, written for the tests, with an addition
# that adds a pension balance and two builders
RETIREMENT_WITH_PENSION_FOLDER = ROOT / RETIREMENT_CHOICE_PENSION_FOLDER


# the durables stage `Port2`, whose value builder takes `!vfi`
PORT2 = "applications/durables/declaration/stages/Port2/Port2.bl"


@functools.cache
def recorded_runs():
    """The runs that `additions/expected.json` records: for each stage file of
    a case study and the additions read into it, the places that the
    additions create and the number of places of the stage."""
    return json.loads((ADDITIONS / "expected.json").read_text(encoding="utf-8"))


def run_id(run):
    """The id of a recorded run: the case study, the stage's name and the
    additions in the order read."""
    additions = " + ".join(Path(addition).name for addition in run["additions"])
    return f"{run['study']}: {Path(run['stage']).stem}: {additions}"


def pytest_generate_tests(metafunc):
    """Gives a test that reads `run` one row for each recorded run: the run
    of the consumption stage with its methods file in the default set, every
    other run in the complete set. The file of the runs is read when pytest
    collects the tests, and not when it imports this module."""
    if "run" in metafunc.fixturenames:
        runs = recorded_runs()
        default = next(run for run in runs if run["stage"] == CORPUS["cons"])
        metafunc.parametrize("run", one_row_by_default(runs, default=default), ids=run_id)


def application_stage_file(stage):
    """The stage file `<application>/<stage>/<file>` of an application."""
    application, key, name = stage.split("/")
    return ROOT / "applications" / application / "declaration/stages" / key / name


@pytest.fixture(scope="module")
def stage_with_additions():
    """`stage_with_additions(path, additions)`: the stage of the stage file at
    `path` with the additions read in order, made once for each pair."""

    @functools.cache
    def read(path, additions=()):
        return elaborate_stage(load_stage(path, list(additions)))

    return read


# What a solution method adds, and the two levels of a stage


@pytest.fixture(scope="module")
def cons_with_egm(cons):
    """`cons` with `!egm` and a handler typed on its policy builder, and no
    lines of the method."""
    return copy_native(cons).methodize(
        methods_addition("cons", "policy.method : !egm", 'policy.handler : "test:egm"')
    )


@pytest.fixture(scope="module")
def cons_obs_with_egm(cons_obs):
    """`cons_obs` with `!egm`, its handler and its grid typed on its policy
    builder, whose block writes the grid line."""
    return copy_native(cons_obs).methodize(
        methods_addition(
            "cons_obs",
            "a_min : ℝ₊",
            "a_max : ℝ₊",
            "n_a : ℕ",
            "policy.method : !egm",
            'policy.handler : "cons-port:egm"',
            "policy.grid : !Cartesian(a=(a_min, a_max, n_a))",
        )
    )


@pytest.fixture(scope="module")
def port_with_egm(port):
    """`port` with `!egm` typed on its policy builder, whose block writes the
    maximization and none of the lines of the method."""
    return copy_native(port).methodize(methods_addition("port", "policy.method : !egm"))


@pytest.mark.parametrize(
    "stage_name, bound_name",
    [
        pytest.param("cons", "cons_with_egm", id="cons"),
        pytest.param(
            "cons_obs", "cons_obs_with_egm", id="cons_obs-whose-policy-writes-the-grid-line"
        ),
        pytest.param(
            "port", "port_with_egm", id="port-whose-policy-writes-none-of-the-lines-of-egm"
        ),
    ],
)
def test_egm_on_the_policy_builder_adds_the_condition_egm_eligibility_and_no_other(
    request, stage_name, bound_name
):
    """`!egm` typed on the policy builder adds the condition
    `egm-eligibility` after the obligations of the stage file, and no other
    condition."""
    stage = request.getfixturevalue(stage_name)
    bound = request.getfixturevalue(bound_name)
    assert [item.condition for item in bound.obligations()] == [
        *[item.condition for item in stage.obligations()],
        "egm-eligibility",
    ]


def test_a_quadrature_typed_at_an_expectation_adds_no_condition(port, port_with_one_node_count):
    """A quadrature typed at the expectation of `port` leaves the
    obligations of the stage as they were."""
    quadrature = port_with_one_node_count
    assert quadrature.obligations() == port.obligations()


def test_egm_on_the_policy_block_of_cons_obs_is_held_by_the_policy_builder_alone(
    cons_obs_with_egm,
):
    """Of the places of the backward builders graph of `cons_obs` with
    `!egm`, the policy builder alone holds `!egm`."""
    methodized = cons_obs_with_egm
    assert [
        place for place, held in methodized.builder.bwd.methods.items() if held.word == "!egm"
    ] == ["policy"]


def test_egm_adds_its_condition_and_its_section_to_the_policy_card_of_cons_obs(
    cons_obs, cons_obs_with_egm
):
    """The policy card of `cons_obs` with `!egm` is the card of the stage
    file with `egm-eligibility` after its conditions and, after them, a
    section `Method` that holds the grid of savings."""
    before = parse_card(str(cons_obs.builder.policy))
    after = parse_card(str(cons_obs_with_egm.builder.policy))
    assert after["sections"]["Operations"] == before["sections"]["Operations"]
    held = before["sections"]["Conditions"]
    assert after["sections"]["Conditions"][: len(held)] == held
    assert "egm-eligibility" in "".join(after["sections"]["Conditions"][len(held) :])
    last = before["order"].index("Conditions") + 1
    assert after["order"] == before["order"][:last] + ["Method"] + before["order"][last:]
    assert "!Cartesian(a=(a_min, a_max, n_a))" in "".join(after["sections"]["Method"])


def test_egm_on_a_policy_block_that_writes_none_of_its_lines_keeps_the_declared_lines(
    port_with_egm,
):
    """`!egm` typed on the policy builder of `port`, whose block writes the
    maximization and none of the method's lines, leaves the declared lines
    at the operative level."""
    bound = port_with_egm
    assert str(bound.methods["policy"]) == "!egm"
    assert list(bound.builder.policy.list()) == list(bound.declared.policy.list())


# a solution method typed on a builder with no rows of its own, with its grid
# where the method needs one, and a representation typed at the Evaluation of
# the decision builder
CHOICES_OF_METHODS = {
    "egm-on-the-policy-builder": ("policy", "egm", "Linear"),
    "vfi-on-the-decision-builder": ("cntn_to_dcsn", "vfi", "pchip"),
}


@pytest.fixture(scope="module")
def configured_choice(cons):
    """`configured_choice(choice)`: `cons` with the methods of a choice of
    `CHOICES_OF_METHODS` bound and configured, made once for each choice."""

    @functools.cache
    def bound(choice):
        target, solver, representation = CHOICES_OF_METHODS[choice]
        grid = (
            "a_min : ℝ₊\na_max : ℝ₊\nn_a : ℕ\npolicy.grid : !Cartesian(a=(a_min, a_max, n_a))\n"
            if solver == "egm"
            else ""
        )
        text = (
            f"@methods: cons\n{target}.method : !{solver}\n{grid}"
            "m_min : ℝ₊\nm_max : ℝ₊\nn_m : ℕ\n"
            f"cntn_to_dcsn.evaluate.method : !{representation}\n"
            "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))\n"
        )
        settings = {"n_m": 8, "m_min": 0.1, "m_max": 10.0, "n_a": 8, "a_min": 0.1, "a_max": 10.0}
        methodized = copy_native(cons).methodize({"text": text, "origin": "cons.methods.bl"})
        return methodized.configure({"settings": settings})

    return bound


@pytest.mark.parametrize("choice", list(CHOICES_OF_METHODS))
def test_a_method_choice_leaves_the_graphs_of_the_stage_unchanged(cons, configured_choice, choice):
    """A solution method on a builder and a representation at an Evaluation
    leave every graph of `cons` as the stage file gives it."""
    version = configured_choice(choice)
    assert differing_graph_triples(version, cons) == []


@pytest.mark.parametrize("kind", ["Pullback", "Aggregation", "Evaluation"])
@pytest.mark.parametrize("choice", list(CHOICES_OF_METHODS))
def test_a_method_choice_leaves_the_equation_and_the_types_of_each_primitive_unchanged(
    cons, configured_choice, choice, kind
):
    """A solution method on a builder and a representation at an Evaluation
    leave the equation and the types of the inputs and outputs of each
    primitive of the decision builder as the stage file gives them."""
    version = configured_choice(choice)
    before = cons.builder.bwd["cntn_to_dcsn", kind].denote()
    after = version.builder.bwd["cntn_to_dcsn", kind].denote()
    assert after.expression == before.expression
    assert tuple(w.mathematical_type for w in after.inputs + after.outputs) == tuple(
        w.mathematical_type for w in before.inputs + before.outputs
    )


@pytest.mark.parametrize(
    "choice, conditions",
    [
        ("egm-on-the-policy-builder", ["egm-eligibility", "evaluation-domain"]),
        ("vfi-on-the-decision-builder", ["evaluation-domain"]),
    ],
    ids=("egm-on-the-policy-builder", "vfi-on-the-decision-builder"),
)
def test_a_method_choice_adds_the_condition_of_its_method_and_of_its_representation(
    cons, configured_choice, choice, conditions
):
    """A method choice adds to the obligations of `cons` the condition of its
    solution method, if any, and `evaluation-domain`, that the
    representation is evaluated where its nodes support the function."""
    version = configured_choice(choice)
    assert [item.condition for item in version.obligations()] == [
        *[item.condition for item in cons.obligations()],
        *conditions,
    ]


def test_the_declared_decision_builder_answers_no_method_that_an_addition_types(cons):
    """After an addition types `!vfi` on the decision builder, the declared
    builder answers no method and prints its card as before, while the
    operative builder answers and prints `!vfi`."""
    stage = copy_native(cons)
    before = str(stage.declared["cntn", "dcsn"].denote())
    stage.methodize(methods_addition("cons", "cntn_to_dcsn.method : !vfi"))
    declared, operative = stage.declared["cntn", "dcsn"], stage.builder["cntn", "dcsn"]
    assert list(declared.methods) == [] and str(operative.methods) == "cntn_to_dcsn   !vfi"
    assert str(declared.denote()) == before
    assert "!vfi" in str(operative.denote())


def test_the_declared_policy_builder_answers_no_method_of_the_methods_file(cons, cons_sources):
    """After the methods file of `cons` is read, the declared level answers no
    method and prints the policy card as before, while the operative policy
    builder answers `!egm` and prints its condition."""
    stage = copy_native(cons)
    before = str(stage.declared.policy.denote())
    stage.methodize(cons_sources["methods"])
    assert list(stage.declared.methods) == []
    assert str(stage.builder.policy.methods).startswith(
        'policy   !egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"'
    )
    assert str(stage.declared.policy.denote()) == before
    assert "egm-eligibility" in str(stage.builder.policy.denote())


def test_a_method_that_the_stage_file_types_stands_at_both_levels():
    """A stage file that types `!vfi` on its decision builder is its own
    declared version: one box stands at both levels and answers
    `cntn_to_dcsn   !vfi` at both."""
    inline = stage_from_text(
        corpus_text("cons").replace(
            "@stage: cons\n", "@stage: cons\ncntn_to_dcsn.method : !vfi\n"
        ),
        "cons.bl",
    )
    declared, operative = inline.declared["cntn", "dcsn"], inline.builder["cntn", "dcsn"]
    assert declared.box is operative.box
    assert str(declared.methods) == str(operative.methods) == "cntn_to_dcsn   !vfi"


# the entries and the lines of the addition of the buffer-stock case study,
# with the declarations of the settings that its grids read
BUFFER_STOCK_ADDITION = """@methods: buffer_stock
n_ψ_nodes : ℕ
n_ξ_nodes : ℕ
a_min : ℝ₊
a_max : ℝ₊
n_a : ℕ
k_min : ℝ₊
k_max : ℝ₊
n_k : ℕ

[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))
    | evaluate.method : !Linear] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}

[id=cntn_to_dcsn] {
    D_{m}V = 𝑑𝑢(c)                                  :: [id=marginal]
}

[id=dcsn_to_arvl
    | E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)
    | evaluate.method : !Linear
    | evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))] {
    D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)    :: [id=marginal]
}
"""


@pytest.fixture(scope="module")
def buffer_stock_with_egm(buffer_stock):
    """The buffer-stock stage with `BUFFER_STOCK_ADDITION`."""
    return copy_native(buffer_stock).methodize(addition_of_text(BUFFER_STOCK_ADDITION))


def test_the_buffer_stock_addition_binds_each_entry_at_its_place_with_its_components(
    buffer_stock_with_egm,
):
    """The buffer-stock addition binds each of its entries at the place that
    it writes, with the components that it types there."""
    stage = buffer_stock_with_egm
    assert list(stage.methods) == [
        "dcsn_to_arvl.E_ψ_ξ",
        "dcsn_to_arvl.evaluate",
        "policy",
        "policy.evaluate",
    ]
    assert str(stage.methods["policy"]) == "!egm   !Cartesian(a=(a_min, a_max, n_a))"
    assert (
        str(stage.methods["dcsn_to_arvl.E_ψ_ξ"]) == "!gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)"
    )
    assert str(stage.methods["dcsn_to_arvl.evaluate"]) == (
        "!Linear   !Cartesian(k=(k_min, k_max, n_k))"
    )
    assert str(stage.methods["policy.evaluate"]) == "!Linear"


def test_the_places_of_the_buffer_stock_stage_include_its_policy_and_arrival_places(
    buffer_stock_with_egm,
):
    """The places of the buffer-stock stage with its addition include the
    policy builder with its Evaluation and the object it stores, and the
    expectation of the arrival block with its two occurrences in the block's
    lines and the arrival builder's Evaluation with its two objects."""
    addresses = places_of(buffer_stock_with_egm)
    assert {
        "policy",
        "policy.evaluate",
        "policy.evaluate[c]",
        "dcsn_to_arvl.E_ψ_ξ",
        "dcsn_to_arvl.value.E_ψ_ξ",
        "dcsn_to_arvl.marginal.E_ψ_ξ",
        "dcsn_to_arvl.evaluate",
        "dcsn_to_arvl.evaluate[V[<]]",
        "dcsn_to_arvl.evaluate[D_{k}V[<]]",
    } <= set(addresses)


def test_an_expectation_typed_at_the_head_of_a_block_is_held_by_its_box_and_its_builder(
    buffer_stock_with_egm,
):
    """An expectation typed at the head of the arrival block is held by the
    box of the expectation in the block's value line and by the arrival
    builder."""
    arrival = buffer_stock_with_egm.builder["dcsn", "arvl"]
    expectation = arrival.primitives["value:Expectation:1"]
    assert list(expectation.methods) == ["dcsn_to_arvl.E_ψ_ξ"]
    assert list(arrival.methods) == ["dcsn_to_arvl.E_ψ_ξ", "dcsn_to_arvl.evaluate"]


def test_the_policy_signature_prints_the_typed_components_at_the_operative_level_alone(
    buffer_stock_with_egm,
):
    """The signature of the operative policy builder prints the method and
    the grid after its fields, and the signature of the declared policy
    builder prints no component that the addition types."""
    stage = buffer_stock_with_egm
    printed = str(stage.builder.policy.signature()).splitlines()
    assert printed[-2:] == [
        "method     !egm",
        "grid       !Cartesian(a=(a_min, a_max, n_a))",
    ]
    assert "method" not in str(stage.declared.policy.signature())


def test_the_lines_of_egm_form_the_operative_rows_beside_the_declared_maximization_and_condition(
    buffer_stock_with_egm,
):
    """With `!egm` and its lines typed on the buffer-stock policy builder, the
    operative builder holds the rows of the lines and the declared builder
    the maximization, and the method's condition stands among the
    obligations."""
    stage = buffer_stock_with_egm
    # the candidate line `c[>] = …` is an alias that the fold folds into the
    # row of the line `m[>] = a + c[>]`, so the three lines of the method form
    # two rows and the Evaluation
    assert [key for key in stage.builder.policy.list()] == [
        "g_cntn_to_dcsn:Aggregation",
        "cons_choice:Pullback",
        "Evaluation",
    ]
    assert [key for key in stage.declared.policy.list()] == [
        "Pullback",
        "optimality:Aggregation",
        "optimality:Argmax",
        "Evaluation",
    ]
    assert [c.condition for c in stage.obligations() if c.condition == "egm-eligibility"]


def test_an_appended_derivative_line_stands_in_the_operative_value_builder_alone(
    buffer_stock_with_egm,
):
    """The derivative line that the buffer-stock addition appends to the
    decision builder forms no box and is printed by the operative builder
    and not by the declared one."""
    stage = buffer_stock_with_egm
    operative, declared = stage.builder["cntn", "dcsn"], stage.declared["cntn", "dcsn"]
    assert [key for key in operative.list()] == ["Pullback", "Aggregation", "Evaluation"]
    assert "D_{m}𝑉(m) = 𝑑𝑢(𝑐(m))" in str(operative.denote())
    assert [key for key in declared.list()] == ["Pullback", "Aggregation", "Evaluation"]
    assert "D_{m}𝑉(m)" not in str(declared.denote())


def test_a_block_of_the_initial_diagram_lists_the_derivative_line_an_addition_appends(
    buffer_stock,
):
    """The block of the decision builder of buffer-stock with the methods
    file of the application lists the appended derivative line, whose card
    prints it at its line in the methods file, beside the stage file's own
    line at its line in the stage file."""
    methods_text = (ROOT / BUFFER_STOCK_METHODS).read_text(encoding="utf-8")
    stage = copy_native(buffer_stock).methodize(
        addition_of_text(methods_text, BUFFER_STOCK_METHODS)
    )
    block = stage.initial.backward["cntn_to_dcsn"]
    assert list(block.list().names) == ["cntn_to_dcsn.value", "cntn_to_dcsn.marginal"]
    number = line_of(methods_text, "D_{m}V = 𝑑𝑢(c)")
    appended = f"Source  methods.bl\n  {number}  D_{{m}}V = 𝑑𝑢(c)"
    assert appended in str(block["marginal"].denote())
    card = str(block.denote())
    # the value line stands on line 35 of buffer_stock.bl
    assert "Source  buffer_stock.bl\n  35  V = 𝑢(c) + β*V[>]" in card and appended in card
    assert "D_{m}V" not in str(stage.declared["cntn", "dcsn"].denote())


# the entries and the derivative line of the addition to the durables stage
# `Port2`, whose value builder takes `!vfi` and gains a derivative line
PORT2_ADDITION = """@methods: Port2
n_Ψ_nodes : ℕ
n_θ_nodes : ℕ
k_min : ℝ₊
k_max : ℝ₊
n_k : ℕ

[id=cntn_to_dcsn] {
    D_{k_d}V = E_{Ψ,θ}(D_{m_next}V[>]*(ς*Ψ + (1-ς)*R))   :: [id=marginal]
}

cntn_to_dcsn.method : !vfi
cntn_to_dcsn.handler : "cons-port:share_search"
cntn_to_dcsn.grid : !Cartesian(k_d=(k_min, k_max, n_k, !expmult))
cntn_to_dcsn.value.E_Ψ_θ.method : !gauss_hermite(n_Ψ=n_Ψ_nodes, n_θ=n_θ_nodes)
cntn_to_dcsn.marginal.E_Ψ_θ.method : !gauss_hermite(n_Ψ=n_Ψ_nodes, n_θ=n_θ_nodes)
cntn_to_dcsn.evaluate[V].method : !Linear
cntn_to_dcsn.evaluate[V].grid : !Cartesian(k_d=(k_min, k_max, n_k, !expmult))
"""


@pytest.fixture(scope="module")
def port2_with_vfi():
    """The durables stage `Port2` with `PORT2_ADDITION`."""
    port2 = stage_from_text((ROOT / PORT2).read_text(encoding="utf-8"), PORT2)
    return port2.methodize(addition_of_text(PORT2_ADDITION, "methods.Port2.bl"))


def test_vfi_with_no_rows_leaves_the_declared_lines_at_the_operative_level(port2_with_vfi):
    """`!vfi` with its handler and grid typed on the value builder of `Port2`,
    with no rows of its own, leaves the declared lines at the operative
    level."""
    port2 = port2_with_vfi
    assert str(port2.methods["cntn_to_dcsn"]) == (
        '!vfi   !Cartesian(k_d=(k_min, k_max, n_k, !expmult))   "cons-port:share_search"'
    )
    assert list(port2.builder["cntn", "dcsn"].list()) == list(
        port2.declared["cntn", "dcsn"].list()
    )


def test_a_derivative_line_of_an_addition_is_an_object_that_the_evaluation_stores(
    port2_with_vfi,
):
    """The derivative line that the addition to `Port2` writes adds its
    derivative to the objects that the Evaluation of the value builder
    stores."""
    assert "cntn_to_dcsn.evaluate[D_{k_d}V]" in places_of(port2_with_vfi)


# The union of a stage file with its additions, the case studies and the
# declared level


def test_an_addition_read_into_one_stage_file_under_two_spellings_of_its_path_binds_alike():
    """An addition's lines record the positions of their own file and not the
    path of the stage file, so one stage file read under two spellings of its
    path binds the same places, rows and cards."""
    folder = ROOT / FIXTURES_FOLDER
    plain, roundabout = folder / "cons.bl", folder / ".." / folder.name / "cons.bl"
    bound = [
        elaborate_stage(load_stage(str(path))).methodize(str(CONS_METHODS))
        for path in (plain, roundabout)
    ]
    assert bound[0].provenance["origin"] != bound[1].provenance["origin"]
    assert str(bound[0].methods) == str(bound[1].methods)
    assert list(bound[0].bindings.blocks) == list(bound[1].bindings.blocks) == ["policy"]
    assert [row.kind for row in bound[0].bindings.blocks["policy"].rows] == [
        row.kind for row in bound[1].bindings.blocks["policy"].rows
    ]
    assert str(bound[0].builder.policy.denote()) == str(bound[1].builder.policy.denote())


def test_the_additions_of_a_case_study_create_the_places_that_its_run_records(
    stage_with_additions, run
):
    """The stage file of a case study, read with its additions, lists the
    places of the stage file alone and the places that the run records as
    created, in the number that the run records."""
    source = ROOT / run["stage"]
    stage = stage_with_additions(source, tuple(ROOT / name for name in run["additions"]))
    alone = stage_with_additions(source)
    assert "additions" in stage.provenance and "additions" not in alone.provenance
    found, before = places_of(stage), places_of(alone)
    assert sorted(set(found) - set(before)) == sorted(run["created"])
    assert len(found) == run["places"]


# the refusals file of each case study: its stage, the rule under which its
# first refusal stands, the words of the refusal, and the file whose position
# the refusal names beside the refused item's own
CASE_STUDY_REFUSALS = [
    (
        "benhabib-2019",
        "benhabib-2019/benhabib_bellman/benhabib_bellman.bl",
        "declared-twice",
        ("`method : !egm`", "`policy.method : !vfi`"),
        "refusals.bl",
    ),
    (
        "cagetti-denardi-2006",
        "cagetti-denardi-2006/retiree/retiree.bl",
        "type-conflict",
        ("'V'", "`ℝ @ !vlu`", "`ℝ₊ @ !vlu`"),
        "retiree.bl",
    ),
    ("cons-port", "cons-port/cons/cons.bl", "declared-twice", ("'Xa'",), "cons.bl"),
    (
        "consumption-savings-iid",
        "consumption-savings-iid/cons_savings_iid/cons_savings_iid.bl",
        "declared-twice",
        ("'𝑑𝑢𝑖𝑛𝑣'",),
        "cons_savings_iid.bl",
    ),
    (
        "durables",
        "durables/tenure/tenure.bl",
        "type-conflict",
        ("'a_d'", "`ℝ₊`", "`ℝ₊₊`"),
        "tenure.bl",
    ),
    (
        "epstein-zin-savings",
        "epstein-zin-savings/ez_savings/ez_savings.bl",
        "label-not-in-parent",
        ("`policy.evaluate.method`", "'cntn_to_dcsn'", "'policy'"),
        "ez_savings.bl",
    ),
    (
        "housing-frictions",
        "housing-frictions/house_choice/house_choice.bl",
        "declared-twice",
        ("'choice'", "'policy'"),
        "house_choice.bl",
    ),
    (
        "housing-owner",
        "housing-owner/consumption_choice/consumption_choice.bl",
        "label-not-in-parent",
        ("`cntn_to_dcsn.evaluate[D_{w_d}(V)].method`", "'policy'"),
        "consumption_choice.bl",
    ),
    (
        "housing-renting",
        "housing-renting/tenure_choice/tenure_choice.bl",
        "declared-twice",
        ("'value'", "'dcsn_to_arvl'"),
        "tenure_choice.bl",
    ),
    (
        "pension-retirement",
        "pension-retirement/worker_saving/worker_saving.bl",
        "type-conflict",
        ("'c_p'", "`ℝ₊ @ !ctrl`", "`ℝ₊₊ @ !ctrl`"),
        "worker_saving.bl",
    ),
    (
        "portfolio-choice",
        "portfolio-choice/cons/cons.bl",
        "declared-twice",
        (
            "`grid`",
            "`grid : !Cartesian(a=(a_min, a_max, n_a))`",
            "`policy.grid : !Cartesian(a=(m_min, m_max, n_m))`",
        ),
        "refusals.bl",
    ),
    (
        "retirement-choice",
        "retirement-choice/ret_choice/ret_choice.bl",
        "label-not-in-parent",
        ("`policy.evaluate.method`", "'dcsn_to_arvl'"),
        "ret_choice.bl",
    ),
    (
        "smooth-ambiguity-savings",
        "smooth-ambiguity-savings/sa_savings/sa_savings.bl",
        "type-conflict",
        ("'V[>]'", "`ℝ₊₊ @ !vlu`", "`ℝ @ !vlu`"),
        "sa_savings.bl",
    ),
]


@pytest.mark.parametrize(
    "study, stage, rule, words, other",
    CASE_STUDY_REFUSALS,
    ids=[row[0] for row in CASE_STUDY_REFUSALS],
)
def test_the_refusals_file_of_a_case_study_is_refused_naming_both_positions(
    study, stage, rule, words, other
):
    """The refusals file of a case study, read into its stage file, is refused
    under its rule at its own line, with the words of the refusal and the
    position of the earlier item in its file."""
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(
            load_stage(application_stage_file(stage), [ADDITIONS / study / "refusals.bl"])
        )
    error = refused.value
    assert error.rule == rule
    assert Path(error.file).name == "refusals.bl" and error.line is not None
    assert [word for word in words if word not in error.message] == []
    assert f"{other}:" in error.message


# runs of a stage file with additions whose declared level is compared with
# the stage file alone: rows under a solution method, a solution method with
# no rows, two additions in order, a branching stage, a stage whose clauses
# stand in its methods file, and two builders that an addition adds
DECLARED_LEVEL_RUNS = {
    "buffer-stock: buffer_stock: methods.bl": (BUFFER_STOCK_FILE, (BUFFER_STOCK_METHODS,)),
    "cons-port: cons: methods.vfi.bl": (
        "applications/cons-port/declaration/stages/cons/cons.bl",
        ("applications/cons-port/declaration/stages/cons/methods.vfi.bl",),
    ),
    "consumption-savings-iid: cons_savings_iid: methods.bl + methods.additions.bl": (
        "applications/consumption-savings-iid/declaration/stages/cons_savings_iid/"
        "cons_savings_iid.bl",
        (
            "packages/bellman/tests/additions/consumption-savings-iid/methods.bl",
            "packages/bellman/tests/additions/consumption-savings-iid/methods.additions.bl",
        ),
    ),
    "durables: tenure: methods.bl": (
        "applications/durables/declaration/stages/tenure/tenure.bl",
        ("applications/durables/declaration/stages/tenure/methods.bl",),
    ),
    "pension-retirement: worker_saving: methods.bl": (
        "applications/pension-retirement/declaration/stages/worker_saving/worker_saving.bl",
        ("applications/pension-retirement/declaration/stages/worker_saving/methods.bl",),
    ),
    "retirement-choice-pension: choice: pension_choice.bl": (
        f"{RETIREMENT_CHOICE_PENSION_FOLDER}/stage/choice.bl",
        (f"{RETIREMENT_CHOICE_PENSION_FOLDER}/additions/pension_choice.bl",),
    ),
}


# the run whose methods file types `!vfi` on the decision builder alone, which
# changes the backward builders graph at the operative level and neither the
# listing, nor the policy card, nor the forward builders graph
VFI_ON_THE_DECISION_BUILDER = "cons-port: cons: methods.vfi.bl"


@pytest.mark.parametrize(
    "name",
    one_row_by_default(
        [name for name in DECLARED_LEVEL_RUNS if name != VFI_ON_THE_DECISION_BUILDER]
    ),
)
def test_the_declared_level_of_a_stage_with_additions_lists_what_the_stage_file_does(
    stage_with_additions, name
):
    """The declared level of a stage file with additions lists the builders
    and prints the policy card of the stage file elaborated alone."""
    path, addition_files = DECLARED_LEVEL_RUNS[name]
    stage = stage_with_additions(ROOT / path, tuple(ROOT / added for added in addition_files))
    alone = stage_with_additions(ROOT / path)
    assert "additions" in stage.provenance and "additions" not in alone.provenance
    assert str(stage.declared.list()) == str(alone.builder.list())
    assert str(stage.declared.policy.denote()) == str(alone.builder.policy.denote())


# each run with each direction of the builders graphs that its methods change
# at the operative level, the run of the buffer-stock stage in the default set
# and every other run in the complete set
DECLARED_GRAPHS = [
    pytest.param(
        name,
        direction,
        id=f"{name}-{direction}",
        marks=() if name == "buffer-stock: buffer_stock: methods.bl" else pytest.mark.complete_set,
    )
    for name in DECLARED_LEVEL_RUNS
    for direction in ("bwd", "fwd")
    if (name, direction) != (VFI_ON_THE_DECISION_BUILDER, "fwd")
]


@pytest.mark.parametrize("name, direction", DECLARED_GRAPHS)
def test_the_declared_graphs_of_a_stage_with_additions_are_those_of_the_stage_file(
    stage_with_additions, name, direction
):
    """The declared backward and forward builders graphs of a stage file with
    additions have the signature and print the card of those of the stage
    file elaborated alone."""
    path, addition_files = DECLARED_LEVEL_RUNS[name]
    stage = stage_with_additions(ROOT / path, tuple(ROOT / added for added in addition_files))
    alone = stage_with_additions(ROOT / path)
    assert "additions" in stage.provenance and "additions" not in alone.provenance
    assert str(getattr(stage.declared, direction).signature()) == str(
        getattr(alone.builder, direction).signature()
    )
    assert str(getattr(stage.declared, direction).denote()) == str(
        getattr(alone.builder, direction).denote()
    )


def test_two_additions_read_in_order_form_the_union_with_one_file_holding_both():
    """The union of the consumption-savings-iid stage file with its two
    additions read in order is its union with one file that holds both, and
    records each line at its position in its own file."""
    stage = (
        ROOT
        / "applications/consumption-savings-iid/declaration/stages"
        / "cons_savings_iid/cons_savings_iid.bl"
    )
    first = ADDITIONS / "consumption-savings-iid/methods.bl"
    second = ADDITIONS / "consumption-savings-iid/methods.additions.bl"
    parsed = parse_with_spans(stage.read_text(encoding="utf-8"), str(stage))
    two = union(
        parsed,
        [
            parse_with_spans(first.read_text(encoding="utf-8"), str(first)),
            parse_with_spans(second.read_text(encoding="utf-8"), str(second)),
        ],
    )
    # one file holding both additions, the second's line `@methods:` left out
    both = first.read_text(encoding="utf-8") + "".join(
        line
        for line in second.read_text(encoding="utf-8").splitlines(keepends=True)
        if not line.startswith("@methods:")
    )
    one = union(parsed, [parse_with_spans(both, "both.bl")])
    assert two.term == one.term
    assert {span.file for span in two.spans.values()} == {str(stage), str(first), str(second)}


def test_a_third_addition_that_types_the_policy_method_again_is_refused_at_its_line():
    """A third addition to a buffer-stock stage with a pension, written for
    the tests, that types the method of the policy builder a second time is
    refused under `declared-twice` at its item and line, naming both
    entries."""
    folder = ROOT / BUFFER_STOCK_PENSION_FOLDER
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(
            load_stage(
                folder / "stage/buffer_stock.bl",
                [
                    folder / "additions/pension.bl",
                    folder / "additions/egm.bl",
                    folder / "additions/conflict_slot.bl",
                ],
            )
        )
    error = refused.value
    # the conflicting line is the second item of its file, on its seventh line
    assert (error.rule, error.address, Path(error.file).name) == (
        "declared-twice",
        "2",
        "conflict_slot.bl",
    )
    assert error.line == 7
    phrases = ("egm.bl:", "`policy.method : !egm`", "`policy.method : !vfi`")
    assert [phrase for phrase in phrases if phrase not in error.message] == []


@pytest.fixture(scope="module")
def retirement_with_pension(stage_with_additions):
    """The retirement choice in `RETIREMENT_WITH_PENSION_FOLDER` with the
    addition `pension_choice.bl`."""
    return stage_with_additions(
        RETIREMENT_WITH_PENSION_FOLDER / "stage/choice.bl",
        (RETIREMENT_WITH_PENSION_FOLDER / "additions/pension_choice.bl",),
    )


def test_an_addition_appends_lines_inside_the_branches_under_the_labels_of_the_stage(
    retirement_with_pension,
):
    """The lines that the pension addition appends inside the two
    branches of the forward decision block are places under the stage's
    labels of the branches."""
    found = places_of(retirement_with_pension)
    assert {
        "dcsn_to_cntn.work.pension_if_working",
        "dcsn_to_cntn.retire.pension_if_retiring",
    } <= set(found)


def test_an_addition_adds_the_two_arrival_builders_whole(retirement_with_pension):
    """The pension addition adds the forward and the backward
    arrival builders whole, as places, as builders and in the listing of the
    stage."""
    stage = retirement_with_pension
    found = places_of(stage)
    assert {"arvl_to_dcsn", "dcsn_to_arvl", "dcsn_to_arvl.survival_value"} <= set(found)
    assert set(stage.builder) >= {
        ("arvl", "dcsn"),
        ("dcsn", "arvl"),
        ("dcsn", "cntn"),
        ("cntn", "dcsn"),
    }
    assert "arvl_to_dcsn" in str(stage.list()) and "dcsn_to_arvl" in str(stage.list())


def test_an_addition_adds_its_balance_to_the_domain_of_a_branching_block_and_its_branches(
    retirement_with_pension,
):
    """The pension balance that the pension addition prepends to
    the domain of the branching block and appends to each branch makes the
    three measures of the forward decision builder lie on ℝ₊ × Xp, where the
    stage file alone has them on ℝ₊."""
    signature = str(retirement_with_pension.builder["dcsn", "cntn"].signature())
    assert signature.count("finite measure on ℝ₊ × Xp") == 3


def test_the_two_builders_that_an_addition_adds_whole_are_blocks_of_the_initial_diagrams(
    retirement_with_pension,
):
    """The two builders that the pension addition adds whole are
    blocks of the initial diagrams and list their lines."""
    pension = retirement_with_pension
    assert list(pension.initial.backward["dcsn_to_arvl"].list().names) == [
        "dcsn_to_arvl.survival_value",
        "dcsn_to_arvl.marginal_assets",
        "dcsn_to_arvl.marginal_pension",
    ]
    assert list(pension.initial.forward["arvl_to_dcsn"].list().names) == [
        "arvl_to_dcsn.assets",
        "arvl_to_dcsn.pension",
    ]


def test_a_line_id_written_in_the_stage_file_and_in_an_addition_is_refused():
    """A line id that the retirement choice with a pension and a second
    addition both write is refused under `declared-twice`, naming the line
    and the stage file's position of it."""
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(
            load_stage(
                RETIREMENT_WITH_PENSION_FOLDER / "stage/choice.bl",
                [
                    RETIREMENT_WITH_PENSION_FOLDER / "additions/pension_choice.bl",
                    RETIREMENT_WITH_PENSION_FOLDER / "additions/conflict_line.bl",
                ],
            )
        )
    error = refused.value
    assert (error.rule, error.address, Path(error.file).name) == (
        "declared-twice",
        "cntn_to_dcsn.choice_value",
        "conflict_line.bl",
    )
    assert "choice.bl:" in error.message and "'choice_value'" in error.message
