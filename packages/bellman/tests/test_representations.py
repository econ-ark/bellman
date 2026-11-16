"""Representations of a function: the families and their registry, the data
that a place supplies, authored tables and their grids, and the preparation
of each data source for numerical use."""

import numpy as np
import pytest
from application_files import PERFECT_FORESIGHT_CALIBRATION, PERFECT_FORESIGHT_ORIGIN
from stage_builders import (
    closed_form_check,
    construction_refusal,
    methodized_copy,
    stage_from_text,
)
from stage_texts import (
    EXPLICIT_GRID_SETTINGS,
    GROWTH_LINE,
    RESOURCES_LINE,
    TWO_STATE_GRID_STAGE,
    explicit_policy_with_entries,
    perfect_foresight_text,
)

from bellman.native.hypergraphs import copy_native
from bellman.native.records import MethodOption
from bellman.refusals import ConstructionError
from bellman.stage import admitted_methods, method_types
from bellman.stage.representations import RepresentationFamily, families, register, unregister

# --- the texts and the stages that the tests read ---

# the endogenous grid method at the policy builder of the consumption-savings
# stage with independent income: its grid of savings and its three lines,
# with no representation at the policy builder's Evaluation, and the envelope
# line of the decision value
ENDOGENOUS_GRID_METHOD = """n_a : ℕ
a_min : ℝ₊
a_max : ℝ₊
[id=policy, method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    w[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}
[id=cntn_to_dcsn] {
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}
"""


# the settings and the grid on the decision state w of a representation at
# the policy builder's Evaluation of that stage
POLICY_EVALUATION_GRID = """n_w : ℕ
w_min : ℝ₊
w_max : ℝ₊
policy.evaluate.grid : !Cartesian(w=(w_min, w_max, n_w))
"""


def policy_evaluation_entries(word, grid=True):
    """The entries that type the family `!word` at the policy builder's
    Evaluation of the consumption-savings stage, with the grid on w where
    `grid`."""
    return f"policy.evaluate.method : !{word}\n" + (POLICY_EVALUATION_GRID if grid else "")


# the closed form typed at the Evaluation of the explicit policy builder of
# the perfect-foresight stage
CLOSED_FORM_ENTRY = "policy.evaluate.method : !closed_form"


# the values of the knots K and of the values Y of an authored table of
# three knots, beside the calibration of the perfect-foresight stage
TABLE_CALIBRATION = {**PERFECT_FORESIGHT_CALIBRATION, "K": [0.0, 1.0, 2.0], "Y": [1.0, 2.0, 4.0]}


# the representation of the closed-form decision value by PCHIP on its own
# grid of resources, an addition read with the application's methods.bl,
# which overrides the closed form that `!explicit` generates at that
# Evaluation
PCHIP_ON_ITS_OWN_GRID = """n_m : ℕ
m_lo : Xm
m_hi : Xm
cntn_to_dcsn.evaluate.method : !pchip
cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_lo, m_hi, n_m))
"""


# The perfect-foresight stage whose forward builder `arvl_to_dcsn` defines
# cash on hand m by an authored table on a `!node` line, evaluated at k. The
# builder has one operation, the push-forward through its law of motion,
# whose kernel holds the line of the node, and it closes with no Evaluation;
# so no operation of the builder stands at the Evaluation of the node, the
# place `arvl_to_dcsn.market_resources.evaluate`, and a grid typed there
# discretizes the states of the builder's output perch, (m).
FORWARD_NODE_TEXT = perfect_foresight_text(
    ("@stage: perfect_foresight\n", "@stage: forward_node\n"),
    (GROWTH_LINE, GROWTH_LINE + "K : ℝ × ℝ × ℝ\nY : ℝ × ℝ × ℝ\n"),
    (
        RESOURCES_LINE + "\n",
        "    m = evaluate(K, Y, k)           :: [id=market_resources, !node]\n",
    ),
)


def stage_with_a_node(lines):
    """The perfect-foresight stage with the parameters K and Y of a table, and
    with `lines` in place of the value line of its decision builder."""
    value = "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
    return stage_from_text(
        perfect_foresight_text(
            (GROWTH_LINE, GROWTH_LINE + "K : ℝ × ℝ × ℝ\nY : ℝ × ℝ × ℝ\n"), (value, lines)
        ),
        "perfect_foresight.bl",
    )


# the head and the Evaluation of the node `table` of the decision builder
NODE_HEAD = "cntn_to_dcsn.table"
NODE_EVALUATION = "cntn_to_dcsn.table.evaluate"


def configured_then_calibrated(stage, settings, calibration):
    """A copy of `stage` configured with `settings` and then calibrated with
    `calibration`."""
    version = copy_native(stage)
    version.configure({"settings": settings})
    version.calibrate({"calibration": calibration})
    return version


@pytest.fixture(scope="module")
def authored_table_stage():
    """The perfect-foresight stage whose arrival block reads the authored
    table `W = evaluate(K, Y, k)`, represented by `!Linear` on the grid `KN`
    of its knots."""
    table = stage_from_text(perfect_foresight_text(table=True), PERFECT_FORESIGHT_ORIGIN)
    return methodized_copy(
        table,
        "KN : ℝ × ℝ × ℝ\n"
        "dcsn_to_arvl.table.evaluate.method : !Linear\n"
        "dcsn_to_arvl.table.evaluate.grid : !Cartesian(k=KN)\n",
    )


@pytest.fixture(scope="module")
def pairs_stage(cons_savings_iid):
    """The consumption-savings stage with `!Linear` and no grid at the policy
    builder's Evaluation, under the endogenous grid method."""
    return methodized_copy(
        cons_savings_iid,
        policy_evaluation_entries("Linear", grid=False),
        ENDOGENOUS_GRID_METHOD,
    )


@pytest.fixture(scope="module")
def own_nodes_stage(cons_savings_iid):
    """The consumption-savings stage with `!Linear` on a grid of b at the
    Evaluation of its arrival value."""
    return methodized_copy(
        cons_savings_iid,
        "n_b : ℕ\nb_min : ℝ₊\nb_max : ℝ₊\n"
        "dcsn_to_arvl.evaluate[V[<]].method : !Linear\n"
        "dcsn_to_arvl.evaluate[V[<]].grid : !Cartesian(b=(b_min, b_max, n_b))\n",
    )


@pytest.fixture(scope="module")
def closed_form_utility_stage(cons_savings_iid):
    """The consumption-savings stage with the closed form typed at its declared
    utility function 𝑢."""
    return methodized_copy(cons_savings_iid, "𝑢.method : !closed_form\n")


@pytest.fixture(scope="module")
def two_state_grid_stage():
    """The stage `grids`, whose decision states are m and z."""
    return stage_from_text(TWO_STATE_GRID_STAGE, "grids.bl")


@pytest.fixture(scope="module")
def forward_node_stage():
    """The perfect-foresight stage whose forward builder `arvl_to_dcsn`
    defines cash on hand by an authored table on a `!node` line."""
    return stage_from_text(FORWARD_NODE_TEXT, PERFECT_FORESIGHT_ORIGIN)


@pytest.fixture(scope="module")
def table_node_stage():
    """The perfect-foresight stage whose decision value is defined by the
    authored table alone, on the `!node` line `table`."""
    return stage_with_a_node("    V = evaluate(K, Y, m)    :: [id=table, !node]\n")


@pytest.fixture(scope="module")
def summand_node_stage():
    """The perfect-foresight stage whose `!node` line `table` adds the
    authored table to the discounted continuation value."""
    return stage_with_a_node(
        "    W = β*V[>] + evaluate(K, Y, m)    :: [id=table, !node]\n"
        "    V = 𝑢(c) + W                      :: [id=value]\n"
    )


@pytest.fixture
def nodal_family():
    """A representation family registered for the duration of one test,
    `!nodal`, which accepts only its own nodes and so samples a function on
    its grid, the endogenous grid method's pairs included; removed at the
    test's end where the test has not removed it."""
    family = register(
        RepresentationFamily(
            "nodal",
            {},
            ("own nodes",),
            derivatives=(),
            stored="The values at the nodes of its grid.",
        )
    )
    yield family
    if "nodal" in families():
        unregister("nodal")


@pytest.fixture
def spline_family():
    """A representation family registered for the duration of one test,
    `!spline`, whose argument `degree`, a positive integer, is required."""
    family = register(
        RepresentationFamily(
            "spline",
            {
                "degree": MethodOption(
                    "positive integer", required=True, description="The degree of the spline."
                )
            },
            ("own nodes",),
            derivatives=(),
            stored="The coefficients of the spline.",
        )
    )
    yield family
    unregister(family.word)


@pytest.fixture
def kinked_record():
    """The record of the family `kinked`, with the typed argument `n_knots`,
    not registered; removed from the registry at the test's end where the
    test has registered it."""
    yield RepresentationFamily(
        "kinked",
        {"n_knots": MethodOption("positive integer", description="The number of knots.")},
        ("table", "own nodes"),
        derivatives=(1,),
        stored="The values at the knots.",
    )
    if "kinked" in families():
        unregister("kinked")


@pytest.fixture
def kinked_family(kinked_record):
    """The family `kinked`, registered for the duration of one test."""
    return register(kinked_record)


# --- the registry of representation families ---


def test_the_registry_holds_the_three_base_families_first_in_order():
    """The registry of representation families begins with `Linear`, `pchip`
    and `closed-form`, in this order."""
    assert list(families())[:3] == ["Linear", "pchip", "closed-form"]


@pytest.mark.parametrize(
    "tag", ["!Linear", "!pchip", "!closed_form"], ids=["Linear", "pchip", "closed-form"]
)
def test_each_base_family_is_a_representation_row_of_the_method_table_with_no_keywords(tag):
    """Each base family is a row of the method table of the kind
    `representation`, with no keyword arguments."""
    assert method_types[tag].kind == "representation" and dict(method_types[tag].keywords) == {}


@pytest.mark.parametrize(
    ("word", "sources"),
    [
        pytest.param("Linear", ("table", "pairs", "own nodes"), id="Linear"),
        pytest.param("pchip", ("table", "pairs", "own nodes"), id="pchip"),
        pytest.param("closed-form", ("expression",), id="closed-form"),
    ],
)
def test_each_base_family_accepts_its_data_sources(word, sources):
    """`Linear` and `pchip` accept a table, the pairs of the endogenous grid
    method or their own nodes, and the closed form accepts an expression."""
    assert families()[word].sources == sources


def test_the_closed_form_reads_no_grid():
    """The closed form reads no grid, in the method table as in the
    registry."""
    assert method_types["!closed_form"].grid is None and families()["closed-form"].grid is None


@pytest.mark.parametrize(
    ("family_name", "stage_name", "place"),
    [
        pytest.param(
            "nodal_family",
            "cons_savings_iid",
            "policy.evaluate",
            id="nodal-at-the-policy-builder",
        ),
        pytest.param(
            "kinked_family",
            "cons",
            "cntn_to_dcsn.evaluate",
            id="kinked-at-the-decision-builder",
        ),
    ],
)
def test_a_registered_family_is_a_row_of_the_method_table_admitted_at_an_evaluation(
    request, family_name, stage_name, place
):
    """A family registered after the package is imported is a row of the
    method table, admitted at the Evaluation of a builder."""
    family = request.getfixturevalue(family_name)
    stage = request.getfixturevalue(stage_name)
    assert f"!{family.word}" in method_types
    assert f"!{family.word}" in admitted_methods(stage, place)


def test_register_returns_the_family_it_adds_last_in_the_order_of_registration(kinked_record):
    """`register` returns the family it is given, which the registry then
    lists last."""
    assert register(kinked_record) is kinked_record
    assert list(families())[-1] == "kinked"


def test_the_row_of_a_registered_family_holds_its_typed_arguments_its_places_and_its_grid(
    kinked_family,
):
    """The row of the method table for a registered family holds the family's
    typed arguments as its keywords, its places as its admission and the grid
    `output`."""
    row = method_types["!kinked"]
    assert (row.kind, dict(row.keywords), row.admits, row.grid) == (
        "representation",
        {"n_knots": kinked_family.parameters["n_knots"]},
        kinked_family.admits,
        "output",
    )


def test_a_family_is_refused_a_second_registration_while_its_word_is_registered(nodal_family):
    """A second registration of a registered family is refused, since its
    word already names a registered family."""
    with pytest.raises(ValueError, match="already names a registered"):
        register(nodal_family)


@pytest.mark.parametrize(
    ("word", "method"),
    [
        pytest.param("egm", "!egm", id="word-of-a-method"),
        pytest.param(
            "golden-section", "!golden_section", id="word-of-a-method-written-with-a-hyphen"
        ),
    ],
)
def test_a_family_whose_word_names_a_method_is_refused(word, method):
    """A family whose word names a method of the method table, as the method
    is written or with a hyphen for its underscore, is refused at its
    registration."""
    with pytest.raises(ValueError, match=f"names the method {method}"):
        register(RepresentationFamily(word, {}, ("own nodes",), derivatives=(), stored="nodes"))


def test_the_registry_is_a_view_that_refuses_an_assignment(kinked_family):
    """The registry that `families()` gives refuses the assignment of a
    family to a word."""
    with pytest.raises(TypeError):
        families()["other"] = kinked_family


def test_unregister_removes_a_family_with_its_row_and_refuses_its_word_a_second_time(
    kinked_record, cons
):
    """`unregister` returns the family it removes, whose row and admission go
    with it, and refuses the family's word a second time."""
    register(kinked_record)
    assert "!kinked" in admitted_methods(cons, "cntn_to_dcsn.evaluate")
    assert unregister("kinked") is kinked_record
    assert "!kinked" not in method_types and "!kinked" not in admitted_methods(
        cons, "cntn_to_dcsn.evaluate"
    )
    with pytest.raises(KeyError, match="names no registered"):
        unregister("kinked")


def test_register_refuses_a_record_that_is_no_family():
    """`register` refuses a record that is no representation family."""
    with pytest.raises(TypeError):
        register("Linear")


def test_a_family_that_accepts_its_own_nodes_reads_a_grid():
    """A family that accepts its own nodes and reads no grid is refused."""
    with pytest.raises(ValueError, match="accepts its own nodes reads a grid"):
        RepresentationFamily(
            "gridless", {}, ("own nodes",), derivatives=(), stored="nodes", grid=None
        )


def test_a_family_accepts_at_least_one_of_the_four_data_sources():
    """A family that accepts none of the four data sources is refused."""
    with pytest.raises(ValueError, match="at least one data source"):
        RepresentationFamily("fitted", {}, ("weights",), derivatives=(), stored="weights")


def test_register_refuses_an_argument_of_a_kind_that_configuration_does_not_check():
    """`register` refuses a family whose typed argument is of a kind,
    `matrix`, that configuration does not check."""
    with pytest.raises(ValueError, match="configure checks the kinds"):
        register(
            RepresentationFamily(
                "odd",
                {"shape": MethodOption("matrix")},
                ("own nodes",),
                derivatives=(),
                stored="nodes",
            )
        )


# --- the data source that each place supplies ---


@pytest.mark.parametrize(
    ("stage_name", "place", "source"),
    [
        pytest.param(
            "authored_table_stage", "dcsn_to_arvl.table.evaluate", "table", id="authored-table"
        ),
        pytest.param(
            "pairs_stage", "policy.evaluate", "pairs", id="pairs-of-the-endogenous-grid-method"
        ),
        pytest.param(
            "perfect_foresight_explicit",
            "policy.evaluate",
            "expression",
            id="expression-of-an-explicit-policy-builder",
        ),
        pytest.param(
            "closed_form_utility_stage", "𝑢", "expression", id="expression-of-a-declared-function"
        ),
        pytest.param(
            "own_nodes_stage",
            "dcsn_to_arvl.evaluate[V[<]]",
            "own nodes",
            id="own-nodes-of-the-family",
        ),
    ],
)
def test_a_representation_reads_the_data_source_that_its_place_supplies(
    request, stage_name, place, source
):
    """A representation reads the data that its place supplies: an authored
    table, the pairs of the endogenous grid method, the expression of an
    explicit policy builder or of a declared function, or its own nodes."""
    assert request.getfixturevalue(stage_name).methods[place].source == source


@pytest.mark.usefixtures("spline_family")
def test_a_typing_entry_is_refused_without_the_required_argument_of_its_family(cons_savings_iid):
    """The family `!spline`, whose argument `degree` is required, is refused
    where its typing entry gives no degree and accepted where it gives one."""
    refused = construction_refusal(
        lambda: methodized_copy(cons_savings_iid, "dcsn_to_arvl.evaluate.method : !spline\n")
    )
    assert refused.rule == "method-admission" and "degree" in refused.message
    methodized_copy(cons_savings_iid, "d : ℤ\ndcsn_to_arvl.evaluate.method : !spline(degree=d)\n")


@pytest.mark.usefixtures("spline_family")
def test_configuration_checks_the_value_of_a_typed_argument_of_a_family(cons_savings_iid):
    """Configuration refuses the degree 0 of the family `!spline`, whose
    degree is a positive integer, and accepts the degree 3."""
    typed = methodized_copy(
        cons_savings_iid, "d : ℤ\ndcsn_to_arvl.evaluate.method : !spline(degree=d)\n"
    )
    assert construction_refusal(
        lambda: copy_native(typed).configure({"settings": {"d": 0}})
    ).rule == ("method-option-value")
    copy_native(typed).configure({"settings": {"d": 3}})


@pytest.mark.parametrize(
    ("stage_name", "additions", "phrase"),
    [
        pytest.param(
            "authored_table_stage",
            ("dcsn_to_arvl.table.evaluate.method : !closed_form\n",),
            "accepts no table",
            id="evaluation-of-an-authored-table",
        ),
        pytest.param(
            "table_node_stage",
            (f"{NODE_EVALUATION}.method : !closed_form\n",),
            "accepts no table",
            id="evaluation-of-a-node-defined-by-a-table",
        ),
        pytest.param(
            "cons_savings_iid",
            ("cntn_to_dcsn.evaluate.method : !closed_form\n",),
            "supplies none",
            id="evaluation-that-closes-the-decision-builder",
        ),
        pytest.param(
            "cons_savings_iid",
            (policy_evaluation_entries("closed_form", grid=False), ENDOGENOUS_GRID_METHOD),
            "!egm selects policy pairs",
            id="policy-evaluation-under-the-endogenous-grid-method",
        ),
    ],
)
def test_the_closed_form_is_refused_at_a_place_that_supplies_no_expression(
    request, closed_form_utility_stage, stage_name, additions, phrase
):
    """The closed form, which reads the expression of a declared function, is
    refused under `representation-source` at a place that supplies a table,
    the pairs of the endogenous grid method, or no data."""
    assert closed_form_utility_stage.methods["𝑢"].source == "expression"
    stage = request.getfixturevalue(stage_name)
    refused = construction_refusal(lambda: methodized_copy(stage, *additions))
    assert refused.rule == "representation-source" and phrase in refused.message


def test_the_places_of_a_stage_hold_the_head_and_the_evaluation_of_a_node(two_nodes_stage):
    """The places of the two-node stage hold the head of the node `first` and
    its Evaluation."""
    assert {"cntn_to_dcsn.first", "cntn_to_dcsn.first.evaluate"} <= {
        row["address"] for row in two_nodes_stage.places()
    }


def test_a_node_takes_a_representation_at_its_head_or_at_its_evaluation_but_not_at_both(
    two_nodes_stage,
):
    """A representation typed at a node's head or at its Evaluation reads the
    node's own nodes, and one typed at both is refused under
    `component-typed-twice`."""
    places = ("cntn_to_dcsn.first", "cntn_to_dcsn.first.evaluate")
    assert {
        place: methodized_copy(two_nodes_stage, f"{place}.method : !Linear\n")
        .methods[place]
        .source
        for place in places
    } == {"cntn_to_dcsn.first": "own nodes", "cntn_to_dcsn.first.evaluate": "own nodes"}
    refused = construction_refusal(
        lambda: methodized_copy(
            two_nodes_stage,
            "cntn_to_dcsn.first.method : !Linear\ncntn_to_dcsn.first.evaluate.method : !pchip\n",
        )
    )
    assert (
        refused.rule == "component-typed-twice"
        and "the node `cntn_to_dcsn.first`" in refused.message
    )


def test_the_kernel_of_a_closed_form_line_takes_the_continuation_value_as_a_supplied_argument(
    cons_savings_iid,
):
    """The closed form of the decision value's line reads its expression, and
    the kernel of the line takes the continuation value V[>] as a supplied
    argument, beside a representation of the arrival value."""
    opaque = methodized_copy(
        cons_savings_iid,
        "cntn_to_dcsn.value.method : !closed_form\ndcsn_to_arvl.evaluate.method : !Linear\n",
    )
    assert opaque.methods["cntn_to_dcsn.value"].source == "expression"
    kernel = opaque.builder["cntn", "dcsn"].primitives["cntn_to_dcsn:Aggregation"].kernel()
    assert "V≻" in dict(kernel.arguments)


# --- selections with the endogenous grid method ---


@pytest.mark.usefixtures("nodal_family")
def test_a_family_of_own_nodes_keeps_its_grid_with_the_endogenous_grid_method_and_after_it(
    cons_savings_iid,
):
    """`!nodal` reads its own nodes on its grid under `!egm`, whether the two
    additions are read together or the representation first, and still once
    `!egm` is removed."""
    nodal_egm = (policy_evaluation_entries("nodal"), ENDOGENOUS_GRID_METHOD)
    combined = methodized_copy(cons_savings_iid, *nodal_egm)
    successive = methodized_copy(cons_savings_iid, policy_evaluation_entries("nodal"))
    successive = methodized_copy(successive, *nodal_egm)
    assert str(combined.methods) == str(successive.methods)
    assert (
        combined.methods["policy.evaluate"].source,
        str(combined.methods["policy.evaluate"]),
    ) == ("own nodes", "!nodal   !Cartesian(w=(w_min, w_max, n_w))")
    successive = methodized_copy(successive, policy_evaluation_entries("nodal"))
    assert successive.methods["policy.evaluate"].source == "own nodes"


@pytest.mark.parametrize(
    "representation_first",
    [
        pytest.param(False, id="read-together"),
        pytest.param(True, id="representation-read-first"),
    ],
)
def test_a_family_that_reads_the_pairs_refuses_a_grid_under_the_endogenous_grid_method(
    cons_savings_iid, pairs_stage, representation_first
):
    """`!Linear` at the policy builder's Evaluation reads the pairs of `!egm`
    with no grid, and with a grid it is refused, whether the two additions
    are read together or the representation first."""
    assert pairs_stage.methods["policy.evaluate"].source == "pairs"
    linear_egm = (policy_evaluation_entries("Linear"), ENDOGENOUS_GRID_METHOD)
    stage = cons_savings_iid
    if representation_first:
        stage = methodized_copy(cons_savings_iid, policy_evaluation_entries("Linear"))
    refused = construction_refusal(lambda: methodized_copy(stage, *linear_egm))
    assert refused.rule == "grid-coordinate" and "reads the policy pairs" in refused.message


def test_linear_without_a_grid_reads_its_own_nodes_once_the_endogenous_grid_method_is_removed(
    pairs_stage,
):
    """`!Linear` with no grid at the policy builder's Evaluation reads the
    pairs under `!egm`, and its own nodes once `!egm` is removed."""
    assert pairs_stage.methods["policy.evaluate"].source == "pairs"
    bare = methodized_copy(pairs_stage, policy_evaluation_entries("Linear", grid=False))
    assert bare.methods["policy.evaluate"].source == "own nodes"


def test_a_version_keeps_the_family_it_was_bound_with_after_the_family_is_removed(
    nodal_family, cons_savings_iid
):
    """After `!nodal` is removed from the registry, a version bound with it
    still reads its own nodes, and configures as bound."""
    kept = methodized_copy(
        cons_savings_iid, policy_evaluation_entries("nodal"), ENDOGENOUS_GRID_METHOD
    )
    unregister(nodal_family.word)
    assert "!nodal" not in method_types and kept.methods["policy.evaluate"].source == "own nodes"
    kept.configure(
        {"settings": {"n_w": 5, "w_min": 0.1, "w_max": 5.0, "n_a": 5, "a_min": 0.0, "a_max": 5.0}}
    )


def test_a_family_removed_from_the_registry_is_refused_in_a_new_binding(
    nodal_family, cons_savings_iid
):
    """A binding that names `!nodal` is accepted while the family is
    registered, and refused by the parser once it is removed."""
    nodal_egm = (policy_evaluation_entries("nodal"), ENDOGENOUS_GRID_METHOD)
    methodized_copy(cons_savings_iid, *nodal_egm)
    unregister(nodal_family.word)
    assert (
        construction_refusal(lambda: methodized_copy(cons_savings_iid, *nodal_egm)).rule
        == "syntax"
    )


def test_a_family_registered_again_binds_with_its_grid_at_the_evaluation_of_an_explicit_policy(
    nodal_family, perfect_foresight
):
    """`!nodal`, removed and registered again, is a row of the method table
    that binds with its grid at the Evaluation of the explicit policy builder,
    whose block writes c."""
    unregister(nodal_family.word)
    register(nodal_family)
    assert "!nodal" in method_types
    again = methodized_copy(
        perfect_foresight,
        EXPLICIT_GRID_SETTINGS
        + explicit_policy_with_entries(
            "policy.evaluate.method : !nodal | policy.evaluate.grid : !Cartesian(m=(lo, hi, n))"
        ),
    )
    held = again.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == ("!nodal", "own nodes", None)


# --- authored tables and their grids ---


def test_configuration_compares_an_authored_table_with_its_grid_exactly(authored_table_stage):
    """A calibrated table beside a grid of its knots owes the comparison of
    their finite supports, which configuration establishes for an equal
    support, `-0.0` and `0.0` being one point, and refuses for another."""
    table = copy_native(authored_table_stage)
    table.calibrate({"calibration": TABLE_CALIBRATION})
    support = [
        (item.condition, item.status)
        for item in table.obligations()
        if item.condition == "table-grid-support"
    ]
    assert support == [("table-grid-support", "required")]
    table.configure({"settings": {"KN": [-0.0, 1.0, 2.0]}})
    assert [
        item.status for item in table.obligations() if item.condition == "table-grid-support"
    ] == ["established"]
    refused = construction_refusal(
        lambda: copy_native(table).configure({"settings": {"KN": [0.0, 1.0, 3.0]}})
    )
    assert refused.rule == "representation-source" and "exactly the table's finite support" in (
        refused.message
    )


# an authored table on the two decision states of the stage `grids`, read at
# the tuple (m, z), and its representation
TABLE_ON_TWO_COORDINATES = (
    "K2 : X2 × X2 × X2 × X2\nY2 : ℝ × ℝ × ℝ × ℝ\n[id=cntn_to_dcsn] {\n"
    "    W = evaluate(K2, Y2, (m, z))    :: [id=table]\n}\n"
    "cntn_to_dcsn.table.evaluate.method : !Linear\n"
)


@pytest.mark.parametrize(
    ("grid", "declared", "settings"),
    [
        pytest.param(
            "!Cartesian(z=ZN, m=MN)",
            "MN : ℝ × ℝ\nZN : ℝ × ℝ\n",
            {"MN": [1.0, 2.0], "ZN": [-1.0, 1.0]},
            id="cartesian-grid-with-its-factors-in-another-order",
        ),
        pytest.param(
            "!Points(nodes=P2)",
            "P2 : X2 × X2 × X2 × X2\n",
            {"P2": [[2.0, 1.0], [2.0, -1.0], [1.0, 1.0], [1.0, -1.0]]},
            id="points-grid-with-the-knots-in-reverse-order",
        ),
    ],
)
def test_a_table_on_two_coordinates_beside_a_grid_on_them_is_compared_exactly(
    two_state_grid_stage, grid, declared, settings
):
    """A table read at the tuple `(m, z)` beside a grid on m and z, a
    Cartesian grid whatever the order of its factors or a grid of points, is
    admitted, and configuration establishes an equal support and refuses a
    different one."""
    knots = [[1.0, -1.0], [1.0, 1.0], [2.0, -1.0], [2.0, 1.0]]
    bound = copy_native(two_state_grid_stage).methodize(
        {
            "text": f"@methods: grids\n{declared}{TABLE_ON_TWO_COORDINATES}"
            f"cntn_to_dcsn.table.evaluate.grid : {grid}\n",
            "origin": "table.bl",
        }
    )
    assert bound.methods["cntn_to_dcsn.table.evaluate"].source == "table"
    different = copy_native(bound)
    bound.configure({"settings": {"K2": knots, "Y2": [1.0, 2.0, 3.0, 4.0], **settings}})
    assert [
        item.status for item in bound.obligations() if item.condition == "table-grid-support"
    ] == ["established"]
    # the last node of each factor, or the last point, becomes 9
    changed = {
        name: [*value[:-1], [9.0, 9.0] if name == "P2" else 9.0]
        for name, value in settings.items()
    }
    with pytest.raises(ConstructionError) as refused:
        different.configure({"settings": {"K2": knots, "Y2": [1.0, 2.0, 3.0, 4.0], **changed}})
    assert refused.value.rule == "representation-source"
    assert "exactly the table's finite support" in refused.value.message


@pytest.mark.parametrize(
    ("stage_name", "place", "source"),
    [
        pytest.param("table_node_stage", NODE_HEAD, "table", id="head-of-a-node-table"),
        pytest.param(
            "table_node_stage", NODE_EVALUATION, "table", id="evaluation-of-a-node-table"
        ),
        pytest.param(
            "table_node_stage",
            "cntn_to_dcsn.evaluate",
            "own nodes",
            id="evaluation-that-closes-the-builder-of-a-node-table",
        ),
        pytest.param(
            "summand_node_stage",
            NODE_HEAD,
            "own nodes",
            id="head-of-a-node-with-a-table-as-one-term",
        ),
        pytest.param(
            "summand_node_stage",
            NODE_EVALUATION,
            "own nodes",
            id="evaluation-of-a-node-with-a-table-as-one-term",
        ),
    ],
)
def test_only_the_places_of_a_node_that_a_table_alone_defines_read_the_table_as_their_data(
    request, stage_name, place, source
):
    """A representation reads the authored table at the head and at the
    Evaluation of a node whose line defines its name by the table alone, and
    its own nodes at the Evaluation that closes that builder and at the
    places of a node of which the table is one term."""
    held = methodized_copy(request.getfixturevalue(stage_name), f"{place}.method : !Linear\n")
    assert held.methods[place].source == source


def test_the_methods_answer_an_entry_at_a_node_s_evaluation_by_its_address_and_by_its_box(
    table_node_stage,
):
    """The methods of a stage answer the entries typed at a node's Evaluation
    by the address `<node>.evaluate` and by the node's Evaluation box, and
    hold nothing at the node's head."""
    typed = methodized_copy(
        table_node_stage,
        f"P : ℝ × ℝ × ℝ\n{NODE_EVALUATION}.method : !Linear\n"
        f"{NODE_EVALUATION}.grid : !Points(nodes=P)\n",
    )
    assert typed.methods["cntn_to_dcsn.table:Evaluation"] is typed.methods[NODE_EVALUATION]
    assert NODE_HEAD not in typed.methods


@pytest.mark.parametrize(
    ("stage_name", "nodes", "grid", "source", "settings", "statuses", "different"),
    [
        pytest.param(
            "table_node_stage",
            "P : ℝ × ℝ × ℝ",
            "!Points(nodes=P)",
            "table",
            {"P": [0.0, 1.0, 2.0]},
            ["established"],
            {"P": [0.0, 1.0, 3.0]},
            id="points-grid-beside-a-node-table",
        ),
        pytest.param(
            "table_node_stage",
            "KN : ℝ × ℝ × ℝ",
            "!Cartesian(m=KN)",
            "table",
            {"KN": [0.0, 1.0, 2.0]},
            ["established"],
            {"KN": [0.0, 1.0, 3.0]},
            id="cartesian-grid-beside-a-node-table",
        ),
        # five points beside a table of three knots that is one term of the
        # node's line, so that no comparison is made and no support refused
        pytest.param(
            "summand_node_stage",
            "KN : ℝ × ℝ × ℝ × ℝ × ℝ",
            "!Cartesian(m=KN)",
            "own nodes",
            {"KN": [0.0, 0.5, 1.0, 1.5, 2.0]},
            [],
            None,
            id="five-point-grid-beside-a-table-that-is-one-term-of-a-node",
        ),
    ],
)
def test_a_grid_at_a_node_s_evaluation_is_compared_only_with_a_table_that_alone_defines_the_node(
    request, stage_name, nodes, grid, source, settings, statuses, different
):
    """A grid typed at a node's Evaluation is compared exactly with the knots
    of an authored table that alone defines the node, an equal support being
    established and a different one refused, and with no table of which the
    node's line holds one term."""
    typed = methodized_copy(
        request.getfixturevalue(stage_name),
        f"{nodes}\n{NODE_EVALUATION}.method : !Linear\n{NODE_EVALUATION}.grid : {grid}\n",
    )
    assert typed.methods[NODE_EVALUATION].source == source
    typed.calibrate({"calibration": TABLE_CALIBRATION})
    other = copy_native(typed)
    typed.configure({"settings": settings})
    assert [
        item.status for item in typed.obligations() if item.condition == "table-grid-support"
    ] == statuses
    if different is not None:
        with pytest.raises(ConstructionError) as refused:
            other.configure({"settings": different})
        assert refused.value.rule == "representation-source"
        assert "exactly the table's finite support" in refused.value.message


def test_a_representation_at_a_node_s_head_and_a_grid_at_its_evaluation_are_one_assignment(
    table_node_stage,
):
    """The representation typed at a node's line and the grid typed at its
    Evaluation are read as one assignment at the Evaluation, whose grid is
    compared with the table's knots at configuration."""
    split = methodized_copy(
        table_node_stage,
        f"P : ℝ × ℝ × ℝ\n{NODE_HEAD}.method : !Linear\n"
        f"{NODE_EVALUATION}.grid : !Points(nodes=P)\n",
    )
    assert split.methods[NODE_HEAD].source == "table"
    assert str(split.methods["cntn_to_dcsn.table:Evaluation"]) == "!Points(nodes=P)"
    split.calibrate({"calibration": TABLE_CALIBRATION})
    different = copy_native(split)
    split.configure({"settings": {"P": [0.0, 1.0, 2.0]}})
    assert [
        item.status for item in split.obligations() if item.condition == "table-grid-support"
    ] == ["established"]
    with pytest.raises(ConstructionError) as refused:
        different.configure({"settings": {"P": [0.0, 1.0, 3.0]}})
    assert (refused.value.rule, refused.value.address) == (
        "representation-source",
        NODE_EVALUATION,
    )
    assert "exactly the table's finite support" in refused.value.message


# --- declared functions and the closed form at an explicit policy builder ---


def test_a_representation_takes_a_grid_only_at_a_function_or_alias_that_names_a_coordinate(
    cons_savings_iid,
):
    """A representation is typed with a grid at the declared function 𝑢 and at
    the alias `𝑑𝑢 := D_{c}(𝑢)`, which has the coordinate of 𝑢, and without one
    at the inverse `𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)`, which names no coordinate, so that a
    grid written there is refused."""
    declared = "c_min : ℝ\nc_max : ℝ\nn_c : ℕ\n"
    entries = (
        "".join(
            f"{name}.method : !Linear\n{name}.grid : !Cartesian(c=(c_min, c_max, n_c))\n"
            for name in ("𝑢", "𝑑𝑢")
        )
        + "𝑑𝑢𝑖𝑛𝑣.method : !Linear\n"
    )
    version = copy_native(cons_savings_iid).methodize(
        {
            "text": "@methods: cons_savings_iid\n" + declared + entries,
            "origin": "functions.methods.bl",
        }
    )
    assert {place: str(held) for place, held in version.methods.items()} == {
        "𝑢": "!Linear   !Cartesian(c=(c_min, c_max, n_c))",
        "𝑑𝑢": "!Linear   !Cartesian(c=(c_min, c_max, n_c))",
        "𝑑𝑢𝑖𝑛𝑣": "!Linear",
    }
    with pytest.raises(ConstructionError) as refused:
        copy_native(cons_savings_iid).methodize(
            {
                "text": "@methods: cons_savings_iid\n"
                + declared
                + "𝑑𝑢𝑖𝑛𝑣.method : !Linear\n𝑑𝑢𝑖𝑛𝑣.grid : !Cartesian(c=(c_min, c_max, n_c))\n",
                "origin": "functions.methods.bl",
            }
        )
    assert (refused.value.rule, refused.value.address) == ("grid-coordinate", "𝑑𝑢𝑖𝑛𝑣")


def test_the_closed_form_authored_at_an_explicit_policy_binds_from_its_expression_with_no_grid(
    perfect_foresight,
):
    """`!closed_form` typed at the Evaluation of the explicit policy builder
    binds from the authored expression, not as the closed form that
    `!explicit` generates, and is refused there with a grid."""
    authored = methodized_copy(perfect_foresight, explicit_policy_with_entries(CLOSED_FORM_ENTRY))
    held = authored.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == ("!closed_form", "expression", None)
    gridded = EXPLICIT_GRID_SETTINGS + explicit_policy_with_entries(
        f"{CLOSED_FORM_ENTRY} | policy.evaluate.grid : !Cartesian(m=(lo, hi, n))"
    )
    refused = construction_refusal(lambda: methodized_copy(perfect_foresight, gridded))
    assert refused.rule == "grid-coordinate" and "!closed_form reads no grid" in refused.message


def test_the_closed_form_at_an_explicit_policy_configured_from_empty_settings_lists_no_setting(
    perfect_foresight,
):
    """The version with the closed form authored at the Evaluation of the
    explicit policy builder, bound from its expression, lists no setting once
    configured from an empty settings source."""
    authored = methodized_copy(perfect_foresight, explicit_policy_with_entries(CLOSED_FORM_ENTRY))
    held = authored.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == ("!closed_form", "expression", None)
    authored.configure({"settings": {}})
    assert list(authored.settings.list()) == []


# --- the obligations of a representation on its domain ---


def test_an_authored_expression_owes_its_definition_where_the_function_is_evaluated(
    perfect_foresight_explicit,
):
    """The authored expression of the explicit policy builder owes one
    condition: that it is defined at every point at which the represented
    function is evaluated."""
    domain = {
        item.explanation
        for item in perfect_foresight_explicit.obligations()
        if item.condition == "evaluation-domain"
    }
    assert domain == {
        "The authored expression is defined, with its stated conditions, at every "
        "point of the represented function's domain at which the function is "
        "evaluated."
    }


@pytest.mark.usefixtures("nodal_family")
def test_a_family_sampled_from_the_pairs_owes_its_domain_and_the_reconstruction_of_the_pairs(
    cons_savings_iid,
):
    """`!nodal` under `!egm`, which samples the pairs on its grid, owes the
    domain on which it is evaluated and then the reconstruction of the
    pairs."""
    combined = methodized_copy(
        cons_savings_iid, policy_evaluation_entries("nodal"), ENDOGENOUS_GRID_METHOD
    )
    assert [
        item.condition
        for item in combined.obligations()
        if item.condition in ("evaluation-domain", "pair-reconstruction")
    ] == ["evaluation-domain", "pair-reconstruction"]


def test_a_family_of_own_nodes_owes_its_evaluation_inside_its_interval_or_an_extension(
    own_nodes_stage,
):
    """A representation on its own nodes owes a condition on the domain of its
    evaluation that names an identified extension."""
    assert any(
        "identified extension" in item.explanation
        for item in own_nodes_stage.obligations()
        if item.condition == "evaluation-domain"
    )


# --- the preparation of each data source for numerical use ---


def test_preparation_compares_a_table_with_a_grid_configured_before_its_calibration_exactly(
    authored_table_stage,
):
    """Where the grid is configured before the calibration that values the
    table's knots, preparation refuses a different support and builds the
    Linear evaluator of the table from an equal one, `-0.0` and `0.0` being
    one point."""
    check = closed_form_check()
    different = configured_then_calibrated(
        authored_table_stage, {"KN": [0.0, 1.0, 3.0]}, TABLE_CALIBRATION
    )
    with pytest.raises(ValueError) as refused:
        check.prepare_table(different, "dcsn_to_arvl.table.evaluate", "K", "Y")
    assert "exactly the table's finite support" in str(refused.value)
    equal = configured_then_calibrated(
        authored_table_stage, {"KN": [-0.0, 1.0, 2.0]}, TABLE_CALIBRATION
    )
    prepared = check.prepare_table(equal, "dcsn_to_arvl.table.evaluate", "K", "Y")
    assert (prepared.word, prepared.source) == ("!Linear", "table")
    # the line through the knots and values (0, 1), (1, 2) and (2, 4)
    assert prepared.evaluator([0.0, 0.5, 1.5, 2.0]).tolist() == [1.0, 1.5, 3.0, 4.0]


def test_preparation_compares_a_spaced_grid_with_a_table_through_the_exact_nodes_of_the_grid():
    """Preparation refuses a table whose knot is only the nearest
    floating-point number of a node of a spaced grid, and prepares an equal
    table where the nodes are floating-point numbers."""
    check = closed_form_check()
    spaced = methodized_copy(
        stage_from_text(perfect_foresight_text(table=True), PERFECT_FORESIGHT_ORIGIN),
        "k_lo : ℝ\nk_hi : ℝ\nn_k : ℕ\n"
        "dcsn_to_arvl.table.evaluate.method : !Linear\n"
        "dcsn_to_arvl.table.evaluate.grid : "
        "!Cartesian(k=(k_lo, k_hi, n_k))\n",
    )
    # the middle of three nodes from 0.1 to 0.2 is no floating-point number,
    # and the knot 0.15000000000000002 is its nearest one
    inexact = configured_then_calibrated(
        spaced,
        {"k_lo": 0.1, "k_hi": 0.2, "n_k": 3},
        {
            **PERFECT_FORESIGHT_CALIBRATION,
            "K": [0.1, 0.15000000000000002, 0.2],
            "Y": [1.0, 2.0, 4.0],
        },
    )
    with pytest.raises(ValueError) as refused:
        check.prepare_table(inexact, "dcsn_to_arvl.table.evaluate", "K", "Y")
    assert (
        "the node 10808639105689191/72057594037927936 (nearest floating-point number "
        "0.15000000000000002) of the grid and the knot 0.15000000000000002 of the table"
    ) in str(refused.value)
    # the nodes of three nodes from 0 to 1 are floating-point numbers
    exact = configured_then_calibrated(
        spaced,
        {"k_lo": 0.0, "k_hi": 1.0, "n_k": 3},
        {**PERFECT_FORESIGHT_CALIBRATION, "K": [0.0, 0.5, 1.0], "Y": [1.0, 2.0, 4.0]},
    )
    prepared = check.prepare_table(exact, "dcsn_to_arvl.table.evaluate", "K", "Y")
    # the line through the knots and values (0, 1), (0.5, 2) and (1, 4)
    assert prepared.evaluator([0.0, 0.25, 1.0]).tolist() == [1.0, 1.5, 4.0]


def test_preparation_of_the_pairs_of_the_endogenous_grid_method_gives_the_linear_policy(
    perfect_foresight_solutions,
):
    """The pairs that the endogenous grid method selects on 50 savings prepare
    the Linear evaluator of the policy on the knots of the route, within 1e-9
    of the closed-form consumption."""
    check = perfect_foresight_solutions.check
    exact = check.closed_form(perfect_foresight_solutions.closed)
    resources = perfect_foresight_solutions.resources
    held = perfect_foresight_solutions.comparisons[50]
    pairs = check.prepare_pairs(held.gridded, "policy.evaluate", held.route)
    assert (pairs.word, pairs.source) == ("!Linear", "pairs")
    assert np.array_equal(pairs.nodes, held.route.knots)
    difference = pairs.evaluator(resources) - exact.consumption(resources)
    assert np.max(np.abs(difference)) < 1e-9


def test_preparation_of_a_closed_form_gives_the_compiled_kernel_of_its_expression(
    perfect_foresight_solutions,
):
    """The closed form at the policy builder's Evaluation prepares the
    compiled kernel of its expression, with no nodes."""
    check = perfect_foresight_solutions.check
    expression = check.prepare_expression(perfect_foresight_solutions.closed, "policy.evaluate")
    assert (expression.word, expression.source, expression.nodes) == (
        "!closed_form",
        "expression",
        None,
    )
    # the consumption is κ·(m − L), with L = 1 − h the natural borrowing limit,
    # so κ·h at m = 1; at the application's calibration, R = 1.04, Γ = 1.02 and
    # Rβ = 1 with ρ = 2, the marginal propensity to consume is
    # κ = 1 − (Rβ)^(1/ρ)/R = 1 − 1/1.04 and human wealth h = 1/(1 − Γ/R) = 52,
    # so κ·h = (0.04/1.04)·52 = 2
    assert expression.evaluator(np.array([1.0])).tolist() == pytest.approx([2.0])


def test_preparation_samples_a_pchip_representation_on_its_own_grid_unless_two_nodes_merge(
    perfect_foresight_solutions,
):
    """Preparation samples the closed-form decision value on the realized grid
    of a PCHIP representation, and refuses a grid whose conversion to
    floating-point numbers merges two exact nodes."""
    check = perfect_foresight_solutions.check
    exact = check.closed_form(perfect_foresight_solutions.closed)
    own = methodized_copy(check.elaborated(), check.source(check.METHODS), PCHIP_ON_ITS_OWN_GRID)
    own.calibrate(check.CALIBRATION)
    own.configure({"settings": {"n_m": 9, "m_lo": -30.0, "m_hi": 50.0}})
    sampled = check.prepare_own_nodes(own, "cntn_to_dcsn.evaluate", check.closed_form(own).value)
    assert (sampled.word, sampled.source) == ("!pchip", "own nodes")
    # nine nodes from -30 to 50, ten apart
    assert sampled.nodes.tolist() == [-30.0, -20.0, -10.0, 0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
    assert np.array_equal(sampled.values, exact.value(sampled.nodes))
    assert np.array_equal(sampled.evaluator(sampled.nodes), sampled.values)
    # three nodes from 1 to 1.0000000000000002, the first two of which have
    # the nearest floating-point number 1.0
    own.configure({"settings": {"n_m": 3, "m_lo": 1.0, "m_hi": 1.0000000000000002}})
    with pytest.raises(ValueError) as merged:
        check.prepare_own_nodes(own, "cntn_to_dcsn.evaluate", check.closed_form(own).value)
    assert (
        "the grid of 'cntn_to_dcsn.evaluate' holds the distinct exact nodes m = 1 and "
        "m = 9007199254740993/9007199254740992, whose nearest floating-point number is the "
        "same, 1.0; numerical preparation converts the exact nodes of a grid to "
        "floating-point numbers and refuses a conversion that merges distinct nodes"
    ) == str(merged.value)


@pytest.mark.usefixtures("nodal_family")
def test_preparation_samples_own_nodes_under_the_endogenous_grid_method_from_reconstructed_pairs(
    perfect_foresight_solutions,
):
    """`!nodal` at the closing Evaluation of the `!egm` policy builder is
    prepared from the Linear reconstruction of the selected pairs, sampled on
    its own grid within 1e-9 of the closed-form consumption."""
    check = perfect_foresight_solutions.check
    exact = check.closed_form(perfect_foresight_solutions.closed)
    written = "\n    | policy.evaluate.method : !Linear]"
    text = check.GRIDDED_METHODS.read_text(encoding="utf-8")
    assert text.count(written) == 1
    text = text.replace(
        written,
        "\n    | policy.evaluate.method : !nodal"
        "\n    | policy.evaluate.grid : !Cartesian(m=(m_lo, m_hi, n_m))]",
    )
    version = check.elaborated()
    version.methodize({"text": text + "n_m : ℕ\nm_lo : Xm\nm_hi : Xm\n", "origin": "nodal.bl"})
    version.calibrate(check.CALIBRATION)
    version.configure(
        {
            "settings": {
                "n_a": 50,
                "a_min": -40.0,
                "a_max": 60.0,
                "n_m": 11,
                "m_lo": -30.0,
                "m_hi": 50.0,
            }
        }
    )
    assert version.methods["policy.evaluate"].source == "own nodes"
    assert "pair-reconstruction" in [item.condition for item in version.obligations()]
    route = check.gridded_route(version)
    reconstructed = check.prepare_own_nodes(
        version, "policy.evaluate", lambda nodes: check.reconstruct(route, nodes)
    )
    assert (reconstructed.word, reconstructed.source, reconstructed.evaluator) == (
        "!nodal",
        "own nodes",
        None,
    )
    # eleven nodes from -30 to 50, eight apart
    assert reconstructed.nodes.tolist() == [-30.0 + 8.0 * n for n in range(11)]
    assert np.max(np.abs(reconstructed.values - exact.consumption(reconstructed.nodes))) < 1e-9


# --- refusals at the line of the entry ---

# each refused addition: the fixture of its stage, its entries, the rule, the
# address and the line of the addition that the refusal names, and phrases
# that its message holds; line 1 of each addition is `@methods: <stage>`, and
# each declaration, typing entry and line of a block after it takes one line,
# so that a block of one line takes three: its header, its line and its brace
REFUSED_ENTRIES = [
    pytest.param(
        "perfect_foresight",
        "n : ℕ\nlo : Xm\nhi : Xm\n[id=policy, policy.method : !explicit "
        "| policy.evaluate.method : !closed_form "
        "| policy.evaluate.grid : !Cartesian(m=(lo, hi, n))] {\n"
        "    c = (1 - (R*β)^(1/ρ)/R)*(m - 1 + 1/(1 - Γ/R))    :: [id=consumption]\n}\n",
        "grid-coordinate",
        "policy.evaluate",
        5,  # the block's header, after three declarations
        ("!closed_form reads no grid", "remove the grid entry"),
        id="closed-form-with-a-grid-at-an-explicit-policy-builder",
    ),
    pytest.param(
        "cons_savings_iid",
        "n_a : ℕ\na_min : ℝ₊\na_max : ℝ₊\n[id=policy, method : !egm "
        "| policy.grid : !Cartesian(a=(a_min, a_max, n_a)) | evaluate.method : !closed_form] {\n"
        "    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]\n"
        "    w[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]\n"
        "    c[~] = c[>]                     :: [id=cons_choice]\n}\n",
        "representation-source",
        "policy.evaluate",
        5,  # the block's header, after three declarations
        ("!egm selects policy pairs", "accepts neither"),
        id="closed-form-at-the-pairs-of-the-endogenous-grid-method",
    ),
    pytest.param(
        "cons_savings_iid",
        "n_a : ℕ\na_min : ℝ₊\na_max : ℝ₊\nn_w : ℕ\nw_min : ℝ₊\nw_max : ℝ₊\n"
        "[id=policy, method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a)) "
        "| evaluate.method : !Linear | evaluate.grid : !Cartesian(w=(w_min, w_max, n_w))] {\n"
        "    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]\n"
        "    w[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]\n"
        "    c[~] = c[>]                     :: [id=cons_choice]\n}\n",
        "grid-coordinate",
        "policy.evaluate",
        8,  # the block's header, after six declarations
        ("reads the policy pairs", "the grid of !egm"),
        id="linear-with-a-grid-at-the-pairs-of-the-endogenous-grid-method",
    ),
    pytest.param(
        "cons_savings_iid",
        "𝑑𝑢.method : !closed_form\n",
        "representation-source",
        "𝑑𝑢",
        2,  # the entry, the one line after `@methods`
        ("complete authored expression", "supplies none"),
        id="closed-form-at-a-function-defined-as-a-derivative",
    ),
    # a grid beside an authored table evaluated at an expression of the
    # place's coordinate, whose knots are points of that expression and not
    # of the coordinate the grid discretizes
    pytest.param(
        "perfect_foresight",
        "K : ℝ × ℝ × ℝ\nY : ℝ × ℝ × ℝ\nKN : ℝ × ℝ × ℝ\n[id=dcsn_to_arvl] {\n"
        "    W = evaluate(K, Y, R*k/Γ + 1)    :: [id=table]\n}\n"
        "dcsn_to_arvl.table.evaluate.method : !Linear\n"
        "dcsn_to_arvl.table.evaluate.grid : !Cartesian(k=KN)\n",
        "representation-source",
        "dcsn_to_arvl.table.evaluate",
        9,  # the grid entry, after three declarations, the block and the method entry
        ("is evaluated at `R*k/Γ + 1`", "!Cartesian(k=KN) discretizes (k)"),
        id="cartesian-grid-beside-a-table-read-at-an-expression",
    ),
    pytest.param(
        "perfect_foresight",
        "K : ℝ × ℝ × ℝ\nY : ℝ × ℝ × ℝ\nP : ℝ × ℝ × ℝ\n[id=dcsn_to_arvl] {\n"
        "    W = evaluate(K, Y, R*k/Γ + 1)    :: [id=table]\n}\n"
        "dcsn_to_arvl.table.evaluate.method : !Linear\n"
        "dcsn_to_arvl.table.evaluate.grid : !Points(nodes=P)\n",
        "representation-source",
        "dcsn_to_arvl.table.evaluate",
        9,  # the grid entry, after three declarations, the block and the method entry
        ("is evaluated at `R*k/Γ + 1`", "!Points(nodes=P) discretizes (k)"),
        id="points-grid-beside-a-table-read-at-an-expression",
    ),
    pytest.param(
        "two_state_grid_stage",
        "MN : ℝ × ℝ\nZN : ℝ × ℝ\nK2 : X2 × X2 × X2 × X2\nY2 : ℝ × ℝ × ℝ × ℝ\n"
        "[id=cntn_to_dcsn] {\n    W = evaluate(K2, Y2, (z, m))    :: [id=table]\n}\n"
        "cntn_to_dcsn.table.evaluate.method : !Linear\n"
        "cntn_to_dcsn.table.evaluate.grid : !Cartesian(m=MN, z=ZN)\n",
        "representation-source",
        "cntn_to_dcsn.table.evaluate",
        10,  # the grid entry, after four declarations, the block and the method entry
        (
            "is evaluated at `(z, m)`",
            "discretizes (m, z)",
            "in the order of the grid's coordinates",
        ),
        id="grid-on-two-coordinates-in-another-order-than-the-table",
    ),
    pytest.param(
        "perfect_foresight",
        "𝑓(x : ℝ₊₊) := log(x)    :: [id=f]\n𝑓.method : !closed_form\n",
        "representation-source",
        "𝑓",
        3,  # the method entry, after the declared function
        ("the declared function '𝑓'", "the call `log(x)` names a function no definition"),
        id="closed-form-at-a-function-that-calls-an-undeclared-function",
    ),
    pytest.param(
        "perfect_foresight",
        "𝑓(x : Xm) := Γ_c(x)    :: [id=f]\n𝑓.method : !closed_form\n",
        "representation-source",
        "𝑓",
        3,  # the method entry, after the declared function
        ("the call `Γ_c(x)` names Γ_c", "whose definition is no expression in closed form"),
        id="closed-form-at-a-function-that-calls-a-correspondence",
    ),
    # the closed form typed at a node's line and a grid typed at the node's
    # Evaluation, the two entries one assignment to the node's function
    pytest.param(
        "perfect_foresight",
        "n : ℕ\nlo : Xm\nhi : Xm\n[id=cntn_to_dcsn] {\n"
        "    W = β*V[>]    :: [id=discounted, !node]\n}\n"
        "cntn_to_dcsn.discounted.method : !closed_form\n"
        "cntn_to_dcsn.discounted.evaluate.grid : !Cartesian(m=(lo, hi, n))\n",
        "grid-coordinate",
        "cntn_to_dcsn.discounted.evaluate",
        9,  # the grid entry, after three declarations, the block and the method entry
        ("!closed_form reads no grid",),
        id="closed-form-at-a-node-with-a-grid-at-its-evaluation",
    ),
    # a grid beside the table of a forward node, which has no Evaluation of
    # its own: the grid discretizes the states of the output perch, (m)
    pytest.param(
        "forward_node_stage",
        "P : ℝ × ℝ × ℝ\narvl_to_dcsn.market_resources.evaluate.method : !Linear\n"
        "arvl_to_dcsn.market_resources.evaluate.grid : !Points(nodes=P)\n",
        "representation-source",
        "arvl_to_dcsn.market_resources.evaluate",
        4,  # the grid entry, after a declaration and the method entry
        ("is evaluated at `k`", "!Points(nodes=P) discretizes (m)"),
        id="grid-beside-the-table-of-a-forward-node",
    ),
]


@pytest.mark.parametrize(
    ("stage_name", "entries", "rule", "address", "line", "phrases"), REFUSED_ENTRIES
)
def test_a_typing_entry_that_its_place_cannot_read_is_refused_at_its_line_in_the_addition(
    request, stage_name, entries, rule, address, line, phrases
):
    """Each refused entry is refused under its rule at its address, at the
    line of the addition that holds it and with an edit to make, by a message
    that holds its phrases."""
    stage = request.getfixturevalue(stage_name)
    with pytest.raises(ConstructionError) as refused:
        copy_native(stage).methodize(
            {"text": f"@methods: {stage.name}\n{entries}", "origin": "entries.bl"}
        )
    error = refused.value
    assert (error.rule, error.address, error.file, error.line) == (
        rule,
        address,
        "entries.bl",
        line,
    )
    assert error.write
    assert [phrase for phrase in phrases if phrase not in error.message] == []
