"""The grids of a stage: the grid entry of a place and the shapes of its
factors, the settings that a grid names, the construction of a grid at the
bound settings, the requirements of a grid, the realized grids that the
kernels of a builder hold, the exact comparison of two grids, and the bounds
of a grid decided at the calibration."""

import pickle
from fractions import Fraction

import numpy
import pytest
from application_files import (
    BUFFER_STOCK_BASELINE_CALIBRATION,
    BUFFER_STOCK_METHODS,
    BUFFER_STOCK_SETTINGS,
    ROOT,
)
from stage_builders import method_argument, stage_from_text
from stage_texts import (
    EGM_STAGE,
    GRID_STAGE,
    GRID_VALUES,
    SAVINGS_GRID_SETTINGS,
    SAVINGS_GRID_VALUES,
    TWO_STATE_GRID_STAGE,
    ZERO_DRAW_PROBABILITY_LINE,
    buffer_stock_text,
    buffer_stock_text_with_changes,
    changed,
)

from bellman.native.records import Refusal
from bellman.refusal_examples import INVERSE_EULER, TWO_NODES
from bellman.refusals import ConstructionError
from bellman.stage import method_types, to_source
from bellman.stage.grids import RealizedGrid, same_grid
from bellman.stage.representations import supports_equal
from bellman.stage.sources import load_settings

# The stage texts of the grid stage are `GRID_STAGE` and
# `TWO_STATE_GRID_STAGE`; the fixture `grid_stage_with_one_addition` unions one
# of them with a methods file whose first line is its header and whose next
# seven lines declare the settings of `GRID_VALUES`: two points of the
# control's feasible set (n_c = 2), m from 1 to 2 in two points and z from -1
# to 1 in two points.

# the entry that types value function iteration at the backward decision
# builder `cntn_to_dcsn` of the grid stage
VFI = "cntn_to_dcsn.method : !vfi\n"


# the fibred grid of the methodization page: each state m of the base
# B = {1, 2} paired with n_c points of the feasible set Γ_c(m) = [0, m]
FIBRED = "!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))"


# a grid of each of the other two constructors, each with a requirement that
# it satisfies: evenly spaced points of m, the points P, and no points
SPACED_GRID = "!Cartesian(m=(m_lo, m_hi, n_m), require=!UniformCartesian)"


LISTED_GRID = "!Points(nodes=P, require=!UniformCartesian)"


EMPTY_GRID = "!Points(require=!Empty)"


# the entries of a product of factors of m and z at the `!vfi` builder and of
# the points P at its Evaluation, the declaration of P on pairs, and the
# settings that list the four points of the product in another order
PRODUCT_AND_POINTS_ON_M_AND_Z = (
    VFI + "cntn_to_dcsn.grid : !Cartesian(m=(m_lo, m_hi, n_m), z=(z_lo, z_hi, n_z))\n"
    "cntn_to_dcsn.evaluate.method : !Linear\n"
    "cntn_to_dcsn.evaluate.grid : !Points(nodes=P)\n"
)


P_ON_FOUR_PAIRS = "P : X2 × X2 × X2 × X2\n"


PRODUCT_IN_ANOTHER_ORDER = {
    **GRID_VALUES,
    "P": [[2.0, 1.0], [1.0, -1.0], [2.0, -1.0], [1.0, 1.0]],
}


# the declaration of P on a product of four nonnegative reals
P_ON_FOUR_REALS = "P : ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊\n"


# the entries of `!vfi` at the builder with the fibred grid, and the same
# entries with a feasible factor written without `!Fibred` at the builder's
# Evaluation
VFI_ON_FIBRED = VFI + f"cntn_to_dcsn.grid : {FIBRED}\n"


FIBRED_AND_A_FAMILY = (
    VFI_ON_FIBRED + "cntn_to_dcsn.evaluate.method : !Linear\n"
    "cntn_to_dcsn.evaluate.grid : !Cartesian(c=(Γ_c, n_c))\n"
)


# the inverse Euler stage `INVERSE_EULER` of `bellman.refusal_examples`, named
# `grids` as the methods file of `grid_stage_with_one_addition` is, with the
# base A and the feasible set Γ_c that a fibred grid at its policy reads
INVERSE_EULER_WITH_A_FIBRE = changed(
    INVERSE_EULER, ("@stage: t\n", "@stage: grids\nA := {1, 2}\nΓ_c(x : ℝ₊) := [0, x]\n")
)


# A choice of two controls, c on [0, m] and h on [0, m - c], whose joint
# feasible set is coupled, in the form of the durables application's
# adjuster_cons stage.
TWO_CONTROL_GRID_STAGE = """@stage: grids
B := {1, 2}
Xm := ℝ₊
Γ_c(m : Xm) := [0, m]
Γ_h(x : ℝ₊) := [0, x]
𝑢(c : ℝ₊, h : ℝ₊) := c + h
[id=dcsn_to_cntn, (m : Xm, c : ℝ₊ @ !ctrl, h : ℝ₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m - c - h
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c, h) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c, h) + V[>]
}
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊ @ !ctrl, h : ℝ₊ @ !ctrl) : !dcsn] {
    (c, h) = argmax_{c : Γ_c(m), h : Γ_h(m - c)}(𝑢(c, h) + V[>]) :: [id=optimality]
}
"""


# The stage `TWO_NODES` of `bellman.refusal_examples`, whose decision value
# is the sum of two authored nodes, `first` and `second`, each the
# expectation E_{y,z} of the discounted continuation value. Its backward
# decision builder is typed in its header: value function iteration on a
# grid of evenly spaced points of the decision state k_d and of points of the
# feasible set Γ of the control c; linear interpolation at the node `first`
# on a grid of a node set of k_d and of the quadrature nodes of the shock y;
# and Gauss-Hermite quadrature for the expectation, with one node count for
# each shock.
TWO_NODES_STAGE_TEXT = changed(
    TWO_NODES,
    (
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {",
        "[id=cntn_to_dcsn, method : !vfi(tol=tol_v), "
        "(V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn\n"
        "    | grid : !Cartesian(k_d=(k_min, k_max, n_k), c=(Γ, n_c))\n"
        "    | first.evaluate.method : !Linear"
        " | first.evaluate.grid : !Cartesian(k_d=K_nodes, y=E_y_z)\n"
        "    | E_y_z.method : !gauss_hermite(n_y=n_y_nodes, n_z=n_z_nodes)] {",
    ),
)


TWO_NODES_SETTINGS = """@methods: two_nodes
tol_v : ℝ₊₊          :: ["tolerance of value function iteration"]
k_min : ℝ            :: ["lower bound of the capital grid"]
k_max : ℝ            :: ["upper bound of the capital grid"]
n_k : ℕ              :: ["number of points of the capital grid"]
n_c : ℕ              :: ["number of candidate shares"]
n_y_nodes : ℕ        :: ["quadrature nodes of the first shock"]
n_z_nodes : ℕ        :: ["quadrature nodes of the second shock"]
K_nodes : ℝ × ℝ × ℝ  :: ["the nodes of the first node's capital grid"]
"""


TWO_NODES_VALUES = {
    "tol_v": 1e-6,
    "k_min": -1.0,
    "k_max": 2.0,
    "n_k": 12,
    "n_c": 5,
    "n_y_nodes": 7,
    "n_z_nodes": 5,
    "K_nodes": [-0.5, 0.5, 1.5],
}


# A stage `two` whose decision value V of the two states x_d and y_d states a
# derivative line in each state. The header of its backward decision builder
# types the value and each derivative apart, each by an entry of its own; the
# settings that the grid of D_{x_d}V names are declared by the methods file
# `TWO_DERIVATIVES_SETTINGS`.
TWO_DERIVATIVES = """@stage: two
β : (0,1)
[id=arvl_to_dcsn, (x : ℝ, y : ℝ) : !arvl -> (x_d : ℝ, y_d : ℝ) : !dcsn] {
    x_d = x
    y_d = y
}
[id=dcsn_to_cntn, (x_d, y_d) : !dcsn -> (a : ℝ, b : ℝ) : !cntn] {
    a = x_d
    b = y_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn
    | evaluate[V].method : !Linear
    | evaluate[D_{x_d}V].method : !pchip
    | evaluate[D_{x_d}V].grid : !Cartesian(x_d=(x_min, x_max, n_x), y_d=(y_min, y_max, n_y))
    | evaluate[D_{y_d}V].method : !Linear] {
    V = β*V[>]
    D_{x_d}V = β*D_{a}V[>]
    D_{y_d}V = β*D_{b}V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


TWO_DERIVATIVES_SETTINGS = (
    "@methods: two\nx_min : ℝ\nx_max : ℝ\nn_x : ℕ\ny_min : ℝ\ny_max : ℝ\nn_y : ℕ\n"
)


# the stage `two` without the grid entry of D_{x_d}V, and a grid entry with no
# method word at the Evaluation of its backward decision builder
TWO_DERIVATIVES_WITHOUT_A_GRID = changed(
    TWO_DERIVATIVES,
    (
        "    | evaluate[D_{x_d}V].grid : "
        "!Cartesian(x_d=(x_min, x_max, n_x), y_d=(y_min, y_max, n_y))\n",
        "",
    ),
)


GRID_WITHOUT_A_METHOD = "cntn_to_dcsn.evaluate.grid : !Cartesian(x_d=(x_min, x_max, n_x))\n"


GRID_WITHOUT_A_METHOD_ADDITION = {
    "text": TWO_DERIVATIVES_SETTINGS + GRID_WITHOUT_A_METHOD,
    "origin": "methods.bl",
}


# the stage file of the portfolio-choice application with no portfolio share
NOPORT = "applications/portfolio-choice/declaration/stages/noport/noport.bl"


# the methods file that types linear interpolation, with the handler
# "factory", on a grid of wealth at the Evaluation of the backward decision
# builder of noport.bl, and declares the three settings that its factor names
NOPORT_GRID = {
    "text": "@methods: noport\n"
    "wealth_min : ℝ\nwealth_max : ℝ\nwealth_points : ℕ\n"
    "cntn_to_dcsn.evaluate.method : !Linear\n"
    'cntn_to_dcsn.evaluate.handler : "factory"\n'
    "cntn_to_dcsn.evaluate.grid : !Cartesian(k_d=(wealth_min, wealth_max, wealth_points))\n",
    "origin": "noport.methods.bl",
}


# the declaration of the lower bound of the savings grid in the methods file
# of the buffer-stock application, and the same declaration on the reals, a
# set wider than the set of savings, so that the check of the grid alone
# decides the bound; the two texts have one length, so that the columns of
# the file stay aligned
LOWER_BOUND_ON_XA = "a_min : Xa "


LOWER_BOUND_ON_THE_REALS = "a_min : ℝ  "


# the grid stage on the set Xm := [m_Low, inf), whose lower end is a parameter,
# and the settings that list the points 0.5, 1 and 2 of m
LOWER_BOUNDED_GRID_STAGE = changed(GRID_STAGE, ("Xm := ℝ₊\n", "m_Low : ℝ₊\nXm := [m_Low, inf)\n"))


THREE_LISTED_VALUES = {**GRID_VALUES, "P": [0.5, 1.0, 2.0]}


# the entries of `!vfi` at the builder `cntn_to_dcsn` with a grid of the
# points P, and with a grid of evenly spaced points of m
VFI_ON_THE_POINTS_P = VFI + "cntn_to_dcsn.grid : !Points(nodes=P)\n"


VFI_ON_SPACED_POINTS = VFI + "cntn_to_dcsn.grid : !Cartesian(m=(m_lo, m_hi, n_m))\n"


# the declaration of P on a product of three reals


P_ON_THREE_REALS = "P : ℝ × ℝ × ℝ\n"


# a realized grid (constructor, coordinates, points) of three points on m,
# one of them the integer 2**53 + 1, which no floating-point number equals
GRID_WITH_A_LARGE_INTEGER = RealizedGrid("Points", ("m",), ((0.0,), (1,), (2**53 + 1,)))


def buffer_stock_with_a_borrowing_limit(methods):
    """The buffer-stock stage with the methods file `methods` read into it, on
    the set of savings `Xa := [a_Art, inf)` of a borrowing limit
    `a_Art : (-inf, 0]` that the stage declares."""
    text = buffer_stock_text_with_changes(
        ("Xa := ℝ", "Xa := [a_Art, inf)"),
        (ZERO_DRAW_PROBABILITY_LINE, ZERO_DRAW_PROBABILITY_LINE + "a_Art : (-inf, 0]\n"),
    )
    stage = stage_from_text(text, "buffer_stock.bl")
    return stage.methodize({"text": methods, "origin": "methods.bl"})


def calibration_at(limit):
    """The baseline calibration of the buffer-stock stage with the borrowing
    limit `a_Art` at `limit`."""
    return {"calibration": {**BUFFER_STOCK_BASELINE_CALIBRATION, "a_Art": limit}}


@pytest.fixture(scope="module")
def buffer_stock_methods():
    """The text of the methods file of the buffer-stock application."""
    return (ROOT / BUFFER_STOCK_METHODS).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def buffer_stock_settings():
    """The settings file of the buffer-stock application as a mapping: 960
    points from 0.001 to 20 for the savings a and for the assets k."""
    return load_settings(ROOT / BUFFER_STOCK_SETTINGS)


@pytest.fixture(scope="module")
def noport_text():
    """The text of the stage file noport.bl."""
    return (ROOT / NOPORT).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def noport_with_a_grid(noport_text):
    """The stage of noport.bl with the methods file `NOPORT_GRID` read into
    it; the tests only query it."""
    return stage_from_text(noport_text, NOPORT).methodize(NOPORT_GRID)


@pytest.fixture(scope="module")
def fibred_stage(grid_stage_with_one_addition):
    """The grid stage with the fibred grid `FIBRED` at its `!vfi` builder,
    configured at `GRID_VALUES`; the tests only query it."""
    return grid_stage_with_one_addition(VFI_ON_FIBRED).configure(GRID_VALUES)


@pytest.fixture(scope="module")
def stage_with_a_grid_and_a_family(grid_stage_with_one_addition):
    """The grid stage with the entries `FIBRED_AND_A_FAMILY`, configured at
    `GRID_VALUES`; the tests only query it."""
    return grid_stage_with_one_addition(FIBRED_AND_A_FAMILY).configure(GRID_VALUES)


@pytest.fixture(scope="module")
def stage_with_a_derived_share(grid_stage_with_one_addition):
    """The grid stage on the feasible set Γ_c(m) = [0, s*m] of the derived
    parameter s := q/2, with the fibred grid at its `!vfi` builder,
    calibrated at q = 4 and configured at `GRID_VALUES`; the tests only query
    it."""
    text = changed(
        GRID_STAGE, ("Γ_c(m : Xm) := [0, m]\n", "q : ℝ₊₊\ns := q/2\nΓ_c(m : Xm) := [0, s*m]\n")
    )
    stage = grid_stage_with_one_addition(VFI_ON_FIBRED, text=text)
    stage.calibrate({"calibration": {"q": 4.0}})
    return stage.configure({"settings": GRID_VALUES})


@pytest.fixture(scope="module")
def two_nodes_with_grids(stage_with_one_addition):
    """The stage `TWO_NODES_STAGE_TEXT` with the methods file
    `TWO_NODES_SETTINGS`; the tests only query it."""
    return stage_with_one_addition(TWO_NODES_STAGE_TEXT, TWO_NODES_SETTINGS)


@pytest.fixture(scope="module")
def configured_two_nodes(stage_with_one_addition):
    """The stage `TWO_NODES_STAGE_TEXT` configured at `TWO_NODES_VALUES`; the
    tests only query it."""
    stage = stage_with_one_addition(TWO_NODES_STAGE_TEXT, TWO_NODES_SETTINGS)
    return stage.configure({"settings": TWO_NODES_VALUES})


@pytest.fixture(scope="module")
def two_derivatives_typed_apart(stage_with_one_addition):
    """The stage `TWO_DERIVATIVES` with the methods file of its settings; the
    tests only query it."""
    return stage_with_one_addition(TWO_DERIVATIVES, TWO_DERIVATIVES_SETTINGS)


@pytest.mark.parametrize(
    ("grid", "declarations"),
    [
        pytest.param(FIBRED, "", id="a fibred grid"),
        pytest.param(SPACED_GRID, "", id="evenly spaced points with a requirement"),
        pytest.param(LISTED_GRID, P_ON_FOUR_REALS, id="listed points with a requirement"),
        pytest.param(EMPTY_GRID, "", id="no points"),
    ],
)
def test_the_methods_of_a_stage_print_a_grid_of_each_constructor_as_it_is_written(
    grid_stage_with_one_addition, grid, declarations
):
    """The methods of the stage print a grid of each of the three
    constructors, typed at the `!vfi` builder, after the method word as the
    methods file writes it."""
    stage = grid_stage_with_one_addition(VFI + f"cntn_to_dcsn.grid : {grid}\n", declarations)
    assert str(stage.methods["cntn_to_dcsn"]) == f"!vfi   {grid}"


@pytest.mark.parametrize(
    ("place", "word", "grid"),
    [
        pytest.param(
            "cntn_to_dcsn",
            "!vfi",
            "!Cartesian(k_d=(k_min, k_max, n_k), c=(Γ, n_c))",
            id="evenly spaced points of a state and points of a feasible set",
        ),
        pytest.param(
            "cntn_to_dcsn.first.evaluate",
            "!Linear",
            "!Cartesian(k_d=K_nodes, y=E_y_z)",
            id="a node set of a state and the quadrature nodes of a shock",
        ),
    ],
)
def test_a_factor_of_each_of_the_four_shapes_is_held_in_the_grid_of_its_place_as_written(
    two_nodes_with_grids, place, word, grid
):
    """The methods of `TWO_NODES_STAGE_TEXT` hold at each place the method word
    and the grid that the header of its block writes."""
    components = two_nodes_with_grids.methods[place]
    assert (components.word, to_source(components.grid)) == (word, grid)


def test_a_quadrature_typed_in_the_header_of_a_block_is_held_at_its_expectation(
    two_nodes_with_grids,
):
    """The entry `E_y_z.method` in the header of `cntn_to_dcsn` is held at
    the place `cntn_to_dcsn.E_y_z` of the expectation E_{y,z} of the block."""
    held = two_nodes_with_grids.methods["cntn_to_dcsn.E_y_z"]
    assert str(held) == "!gauss_hermite(n_y=n_y_nodes, n_z=n_z_nodes)"


def test_the_row_of_a_method_names_the_states_on_which_its_grid_lies():
    """The rows of the method table name the states on which the grid of a
    method lies: the continuation states for `!egm`, the states of the output
    perch for `!Linear`, and none for a quadrature."""
    assert (
        method_types["!egm"].grid,
        method_types["!Linear"].grid,
        method_types["!gauss-hermite"].grid,
    ) == ("cntn", "output", None)
    assert "on the states of the continuation perch" in str(method_types["!egm"])


def test_the_grid_of_the_endogenous_grid_method_is_held_at_the_policy_with_its_handler(
    egm_stage_with_savings_grid_settings,
):
    """The policy of `EGM_STAGE` holds the method `!egm`, its handler and the
    grid of savings with its spacing word, as its header writes them."""
    egm = egm_stage_with_savings_grid_settings.methods["policy"]
    assert (egm.word, egm.handler, to_source(egm.grid)) == (
        "!egm",
        "cons-port:egm",
        "!Cartesian(a=(a_min, a_max, n_a, !expmult(nest=grid_phi)))",
    )


def test_the_grid_of_the_endogenous_grid_method_stands_at_the_policy_and_not_at_its_evaluation(
    egm_stage_with_savings_grid_settings,
):
    """The methods hold the grid of savings of `!egm` at the policy and no
    grid at the policy's Evaluation, since the pairs that the method computes
    give its points."""
    policy_grid = to_source(egm_stage_with_savings_grid_settings.methods["policy"].grid)
    assert policy_grid == "!Cartesian(a=(a_min, a_max, n_a, !expmult(nest=grid_phi)))"
    assert egm_stage_with_savings_grid_settings.methods["policy.evaluate"].grid is None


def test_the_evaluation_of_a_value_holds_the_grid_and_the_keyword_of_its_header(
    egm_stage_with_savings_grid_settings,
):
    """The Evaluation of the decision value of `EGM_STAGE` holds `!Linear`,
    its grid of resources and its keyword `extrap`, as the header writes
    them."""
    value = egm_stage_with_savings_grid_settings.methods["cntn_to_dcsn.evaluate"]
    assert (value.word, to_source(value.grid)) == ("!Linear", "!Cartesian(m=(m_min, m_max, n_m))")
    assert method_argument(value, "extrap") == '"clamp"'


def test_a_place_typed_in_a_methods_file_holds_its_method_its_grid_and_its_handler(
    noport_with_a_grid,
):
    """The Evaluation of the backward decision builder of noport.bl holds the
    method, the grid and the handler that `NOPORT_GRID` types there."""
    held = noport_with_a_grid.methods["cntn_to_dcsn.evaluate"]
    assert str(held) == (
        '!Linear   !Cartesian(k_d=(wealth_min, wealth_max, wealth_points))   "factory"'
    )
    assert (held.word, held.handler) == ("!Linear", "factory")


def test_a_keyword_that_the_row_of_a_method_does_not_list_is_kept_for_its_handler(
    noport_text,
):
    """The keyword `vendor_flag`, which the row of `!Linear` does not list, is
    admitted and held as written for the handler."""
    assert "vendor_flag" not in method_types["!Linear"].keywords
    stage = stage_from_text(noport_text, "noport.bl").methodize(
        {
            "text": '@methods: noport\ncntn_to_dcsn.evaluate.method : !Linear(vendor_flag="on")\n',
            "origin": "noport.methods.bl",
        }
    )
    assert str(stage.methods["cntn_to_dcsn.evaluate"]) == '!Linear(vendor_flag="on")'


def test_a_smolyak_grid_is_refused_as_a_constructor_reserved_by_name_and_not_built():
    """A grid constructor `!Smolyak` is refused under `syntax` as a word that
    is reserved by name and not built."""
    with pytest.raises(ConstructionError, match="reserved by name and not built") as refused:
        stage_from_text(changed(EGM_STAGE, ("!Cartesian(a=", "!Smolyak(a=")))
    assert refused.value.rule == "syntax"


def test_each_function_that_an_evaluation_types_apart_has_a_place_with_its_own_entries(
    two_derivatives_typed_apart,
):
    """The methods of the stage `two` hold one place for the value and for
    each derivative that its Evaluation represents, each with the method and
    the grid of its own entries."""
    methods = two_derivatives_typed_apart.methods
    assert list(methods) == [
        "cntn_to_dcsn.evaluate[V]",
        "cntn_to_dcsn.evaluate[D_{x_d}V]",
        "cntn_to_dcsn.evaluate[D_{y_d}V]",
    ]
    assert str(methods["cntn_to_dcsn.evaluate[D_{x_d}V]"]) == (
        "!pchip   !Cartesian(x_d=(x_min, x_max, n_x), y_d=(y_min, y_max, n_y))"
    )
    assert str(methods["cntn_to_dcsn.evaluate[D_{y_d}V]"]) == "!Linear"


def test_the_places_of_a_stage_list_the_evaluation_and_each_function_that_it_represents(
    two_derivatives_typed_apart,
):
    """The places of the stage `two` list the Evaluation of its backward
    decision builder, then a place for the value and for each derivative."""
    listed = [
        row["address"]
        for row in two_derivatives_typed_apart.places()
        if row["address"].startswith("cntn_to_dcsn.evaluate")
    ]
    assert listed == [
        "cntn_to_dcsn.evaluate",
        "cntn_to_dcsn.evaluate[V]",
        "cntn_to_dcsn.evaluate[D_{x_d}V]",
        "cntn_to_dcsn.evaluate[D_{y_d}V]",
    ]


def test_the_signature_of_an_evaluation_prints_the_method_and_the_grid_of_each_function(
    two_derivatives_typed_apart,
):
    """The signature of the Evaluation of the stage `two` prints the method of
    the value and of each derivative, and the grid of D_{x_d}V, each marked
    with the function that it types."""
    builder = two_derivatives_typed_apart.builder["cntn", "dcsn"]
    evaluation = builder.primitives["cntn_to_dcsn:Evaluation"]
    assert str(evaluation.signature()).splitlines()[2:] == [
        "method     !Linear  [V]",
        "method     !pchip  [D_{x_d}V]",
        "grid       !Cartesian(x_d=(x_min, x_max, n_x), y_d=(y_min, y_max, n_y))",
        "           [D_{x_d}V]",
        "method     !Linear  [D_{y_d}V]",
    ]


def test_a_grid_without_a_method_is_admitted_on_the_coordinates_of_its_place_alone():
    """A grid entry with no method word at the Evaluation of the stage `two`
    is held there on the coordinate x_d, and a factor keyed by a name that is
    no coordinate of the place is refused under `grid-coordinate`."""
    stage = stage_from_text(TWO_DERIVATIVES_WITHOUT_A_GRID, "two.bl")
    stage.methodize(GRID_WITHOUT_A_METHOD_ADDITION)
    assert str(stage.methods["cntn_to_dcsn.evaluate"]) == "!Cartesian(x_d=(x_min, x_max, n_x))"
    absent = changed(GRID_WITHOUT_A_METHOD, ("x_d=", "absent="))
    with pytest.raises(ConstructionError) as refused:
        stage.methodize({"text": TWO_DERIVATIVES_SETTINGS + absent, "origin": "methods.bl"})
    assert (refused.value.rule, refused.value.address) == (
        "grid-coordinate",
        "cntn_to_dcsn.evaluate",
    )


def test_a_grid_typed_at_an_evaluation_leaves_the_method_typed_at_one_of_its_derivatives():
    """A grid entry with no method word, held at the Evaluation of the stage
    `two`, leaves the place of D_{x_d}V with the method `!pchip` of its own
    entry."""
    stage = stage_from_text(TWO_DERIVATIVES_WITHOUT_A_GRID, "two.bl")
    stage.methodize(GRID_WITHOUT_A_METHOD_ADDITION)
    grid = to_source(stage.methods["cntn_to_dcsn.evaluate"].grid)
    assert grid == "!Cartesian(x_d=(x_min, x_max, n_x))"
    assert str(stage.methods["cntn_to_dcsn.evaluate[D_{x_d}V]"]).startswith("!pchip")


def test_a_grid_typed_at_a_builder_is_held_at_the_builder_and_at_no_place_of_its_evaluation(
    fibred_stage,
):
    """The methods of the stage hold the fibred grid typed at the `!vfi`
    builder at the builder's address, with no entry at its Evaluation."""
    assert to_source(fibred_stage.methods["cntn_to_dcsn"].grid) == FIBRED
    assert "cntn_to_dcsn.evaluate" not in fibred_stage.methods


def test_the_signature_of_a_builder_prints_the_method_and_the_grid_typed_at_it(
    fibred_stage,
):
    """The signature of the `!vfi` builder ends with its method and its
    fibred grid."""
    assert str(fibred_stage.builder["cntn", "dcsn"].signature()).splitlines()[-2:] == [
        "method     !vfi",
        f"grid       {FIBRED}",
    ]


def test_a_configured_setting_of_a_grid_prints_its_value_and_the_place_that_reads_it(
    noport_text,
):
    """A configured setting of the grid of wealth prints its value, its set,
    the place, the method and the constructor of the grid that read it."""
    stage = stage_from_text(noport_text, NOPORT).methodize(NOPORT_GRID)
    stage.configure({"wealth_points": 3, "wealth_min": 0.5, "wealth_max": 2.0})
    assert [str(stage.settings[name]) for name in ("wealth_min", "wealth_points")] == [
        "wealth_min = 0.5 : ℝ, read at cntn_to_dcsn.evaluate by !Linear for its grid !Cartesian",
        "wealth_points = 3 : ℕ, read at cntn_to_dcsn.evaluate by !Linear for its grid !Cartesian",
    ]


def test_the_settings_list_the_counts_of_a_grid_as_read_by_it_and_a_tolerance_by_no_grid(
    configured_two_nodes,
):
    """The settings of `TWO_NODES_STAGE_TEXT` list each count of the grid as
    read at `cntn_to_dcsn` for its grid `!Cartesian`, and the tolerance of
    the method as read there by no grid."""
    rows = {
        (row["name"], row["read at"], row["grid"]) for row in configured_two_nodes.settings.list()
    }
    assert ("n_c", "cntn_to_dcsn", "!Cartesian") in rows
    assert ("n_k", "cntn_to_dcsn", "!Cartesian") in rows
    assert ("tol_v", "cntn_to_dcsn", "") in rows


@pytest.mark.parametrize(
    ("name", "value", "words"),
    [
        pytest.param("n_c", 1, "count 1", id="a count of one"),
        pytest.param("K_nodes", [0.5, -0.5, 1.5], "strictly increasing", id="nodes out of order"),
    ],
)
def test_configure_refuses_a_count_of_one_and_a_node_set_out_of_order_under_grid_bounds(
    stage_with_one_addition, name, value, words
):
    """`configure` refuses under `grid-bounds` each value of a setting of the
    grid of `TWO_NODES_STAGE_TEXT` that no grid admits, where the values of
    `TWO_NODES_VALUES` are admitted."""
    stage = stage_with_one_addition(TWO_NODES_STAGE_TEXT, TWO_NODES_SETTINGS)
    stage.configure({"settings": TWO_NODES_VALUES})
    with pytest.raises(ConstructionError, match=words) as refused:
        stage.configure({"settings": {**TWO_NODES_VALUES, name: value}})
    assert refused.value.rule == "grid-bounds"


def test_a_setting_of_the_grid_of_the_endogenous_grid_method_is_read_at_the_policy(
    stage_with_one_addition,
):
    """The setting `grid_phi`, the argument of the spacing word of the grid
    of savings, prints as read at the policy by `!egm` for its grid
    `!Cartesian`."""
    stage = stage_with_one_addition(EGM_STAGE, SAVINGS_GRID_SETTINGS)
    stage.configure({"settings": SAVINGS_GRID_VALUES})
    assert str(stage.settings["grid_phi"]) == (
        "grid_phi = 3.0 : ℝ₊₊, read at policy by !egm for its grid !Cartesian"
    )


def test_a_setting_of_a_fibred_grid_is_listed_as_read_at_its_builder_by_its_method(
    fibred_stage,
):
    """The settings of the stage list the count n_c of the fibre as read at
    `cntn_to_dcsn` by `!vfi` for its grid `!Fibred`."""
    assert [
        (row["read at"], row["by"], row["grid"])
        for row in fibred_stage.settings.list()
        if row["name"] == "n_c"
    ] == [("cntn_to_dcsn", "!vfi", "!Fibred")]


@pytest.mark.parametrize(
    ("grid", "declarations", "settings", "points"),
    [
        pytest.param(SPACED_GRID, "", {}, ((1,), (2,)), id="two evenly spaced points from 1 to 2"),
        pytest.param(
            LISTED_GRID,
            P_ON_FOUR_REALS,
            {"P": [3.0, 1.0, 2.0, 1.0]},
            ((3,), (1,), (2,)),
            id="listed points in their order with a repeated point held once",
        ),
        pytest.param(EMPTY_GRID, "", {}, (), id="no points"),
    ],
)
def test_the_kernels_of_a_builder_hold_the_points_that_the_constructor_of_its_grid_gives(
    grid_stage_with_one_addition, grid, declarations, settings, points
):
    """At the bound settings, the kernels of the `!vfi` builder hold the
    points that the constructor of its grid gives."""
    stage = grid_stage_with_one_addition(VFI + f"cntn_to_dcsn.grid : {grid}\n", declarations)
    stage.configure({**GRID_VALUES, **settings})
    assert stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"].points == points


def test_the_kernels_of_a_builder_hold_under_its_address_the_joint_grid_of_its_fibred_grid(
    fibred_stage,
):
    """The kernels of the `!vfi` builder hold under its address alone its
    fibred grid on the base B = {1, 2} with two points of the feasible set
    [0, m] at each state m, the joint grid of the four pairs (m, c)."""
    grids = fibred_stage.builder["cntn", "dcsn"].kernels().grids
    assert list(grids) == ["cntn_to_dcsn"]
    joint = grids["cntn_to_dcsn"]
    assert (joint.word, joint.coordinates) == ("Fibred", ("m", "c"))
    assert joint.points == ((1, 0), (1, 1), (2, 0), (2, 2))


def test_a_fibred_grid_whose_feasible_set_reads_a_derived_parameter_is_built_at_its_value(
    stage_with_a_derived_share,
):
    """The fibred grid on the feasible set [0, s*m] is built at the value
    s = 2 that the calibration q = 4 gives to s := q/2."""
    grid = stage_with_a_derived_share.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    assert (grid.coordinates, grid.points) == (("m", "c"), ((1, 0), (1, 2), (2, 0), (2, 4)))


def test_the_calibration_keeps_the_declared_parameter_alone_once_a_grid_reads_a_derived_one(
    stage_with_a_derived_share,
):
    """The bound calibration of the stage holds q alone after its grid is
    built at s = 2, the value of the derived parameter s := q/2."""
    grid = stage_with_a_derived_share.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    assert grid.points == ((1, 0), (1, 2), (2, 0), (2, 4))
    assert dict(stage_with_a_derived_share.bindings.calibration) == {"q": 4.0}


def test_a_feasible_factor_written_without_fibred_is_a_family_of_grids_and_no_one_grid(
    grid_stage_with_one_addition,
):
    """The kernels hold, in place of a `!Cartesian` grid with a factor of m
    and a feasible factor of c, the report under `grid-requirement` that it
    is a family of grids of c and no one grid."""
    stage = grid_stage_with_one_addition(
        VFI + "cntn_to_dcsn.grid : !Cartesian(m=(m_lo, m_hi, n_m), c=(Γ_c, n_c))\n"
    )
    stage.configure(GRID_VALUES)
    (indexed,) = stage.builder["cntn", "dcsn"].kernels().grids.values()
    assert indexed.diagnostic["rule"] == "grid-requirement"
    words = "a family of grids of the control c, one at each state, and no one grid"
    assert words in indexed.reason


@pytest.mark.parametrize(
    "entries",
    [
        pytest.param(
            "cntn_to_dcsn.evaluate.method : !Linear\n"
            "cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_lo, m_hi, n_m), "
            "require=!UniformCartesian)\n",
            id="a grid of the evaluation",
        ),
        pytest.param(
            VFI + "cntn_to_dcsn.grid : !Fibred(base=!Cartesian(m=(m_lo, m_hi, n_m)), "
            "fibre=!Cartesian(c=(Γ_c, n_c)))\n",
            id="the base of a fibred grid of the builder",
        ),
    ],
)
def test_a_grid_that_names_no_factor_for_a_state_is_admitted_and_reported_by_its_construction(
    grid_stage_with_one_addition, entries
):
    """`configure` admits a grid on the states (m, z) whose factors name m
    alone, and the kernels hold in its place the report that no factor names
    z."""
    stage = grid_stage_with_one_addition(entries, text=TWO_STATE_GRID_STAGE)
    stage.configure(GRID_VALUES)
    (report,) = stage.builder["cntn", "dcsn"].kernels().grids.values()
    assert report.diagnostic["rule"] == "grid-requirement"
    assert "no factor for the coordinate z" in report.reason


def test_the_construction_reports_the_joint_sampling_of_a_fibre_of_two_controls_as_unsupported(
    grid_stage_with_one_addition,
):
    """The kernels hold, in place of a fibred grid of the two controls c and
    h, whose feasible sets are coupled, the report that their joint sampling
    is unsupported."""
    stage = grid_stage_with_one_addition(
        VFI + "cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), "
        "fibre=!Cartesian(c=(Γ_c, n_c), h=(Γ_h, n_c)))\n",
        text=TWO_CONTROL_GRID_STAGE,
    )
    stage.configure(GRID_VALUES)
    (unsupported,) = stage.builder["cntn", "dcsn"].kernels().grids.values()
    assert "joint sampling is unsupported" in unsupported.reason


@pytest.mark.parametrize(
    ("admitted_grid", "points", "refused_grid", "phrases"),
    [
        pytest.param(
            "!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)), "
            "require=!NonCartesian)",
            ((1, 0), (1, 1), (2, 0), (2, 2)),
            "!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)), require=!Cartesian)",
            ["does not satisfy !Cartesian", "{1, 2} × {0, 1, 2}, holds (1, 2)"],
            id="four pairs that miss the pair (1, 2)",
        ),
        pytest.param(
            "!Fibred(base=!Points, fibre=!Cartesian(c=(Γ_c, n_c)), require=!Empty)",
            (),
            "!Fibred(base=!Points, fibre=!Cartesian(c=(Γ_c, n_c)), require=!NonCartesian)",
            ["does not satisfy !NonCartesian", "it holds no point"],
            id="an empty base",
        ),
    ],
)
def test_an_outer_requirement_of_a_fibred_grid_is_decided_on_its_joint_grid(
    grid_stage_with_one_addition, admitted_grid, points, refused_grid, phrases
):
    """`configure` admits a fibred grid whose joint grid satisfies its outer
    requirement, and refuses under `grid-requirement` one whose joint grid
    does not satisfy it."""
    stage = grid_stage_with_one_addition(VFI + f"cntn_to_dcsn.grid : {admitted_grid}\n")
    stage.configure(GRID_VALUES)
    assert stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"].points == points
    stage = grid_stage_with_one_addition(VFI + f"cntn_to_dcsn.grid : {refused_grid}\n")
    with pytest.raises(ConstructionError) as refused:
        stage.configure(GRID_VALUES)
    error = refused.value
    assert (error.rule, error.address, error.file) == (
        "grid-requirement",
        "cntn_to_dcsn",
        "methods.bl",
    )
    assert [phrase for phrase in phrases if phrase not in error.message] == []


def test_a_requirement_inside_the_fibre_of_a_fibred_grid_is_decided_on_each_fibre(
    grid_stage_with_one_addition,
):
    """`configure` admits `!UniformCartesian` inside the fibre, which three
    points of [0, m] satisfy at each state, and refuses `!NonCartesian`
    there, which the fibre at m = 1 does not satisfy."""
    stage = grid_stage_with_one_addition(
        VFI + "cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), "
        "fibre=!Cartesian(c=(Γ_c, n_c), require=!UniformCartesian))\n"
    )
    stage.configure({**GRID_VALUES, "n_c": 3})
    assert stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"].points == (
        (1, 0),
        (1, 0.5),
        (1, 1),
        (2, 0),
        (2, 1),
        (2, 2),
    )
    stage = grid_stage_with_one_addition(
        VFI + "cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), "
        "fibre=!Cartesian(c=(Γ_c, n_c), require=!NonCartesian))\n"
    )
    with pytest.raises(ConstructionError) as refused:
        stage.configure(GRID_VALUES)
    assert (refused.value.rule, refused.value.address, refused.value.file) == (
        "grid-requirement",
        "cntn_to_dcsn",
        "methods.bl",
    )
    assert "its fibre at the base state m = 1 does not satisfy !NonCartesian" in (
        refused.value.message
    )


@pytest.mark.parametrize(
    ("requirement", "phrases"),
    [
        pytest.param("!Bogus", ["is no predicate word"], id="a word that is no predicate"),
        pytest.param(
            "(!Empty, !Cartesian)",
            ["contradict each other"],
            id="the empty and the cartesian grid",
        ),
        pytest.param(
            "(!Cartesian, !NonCartesian)",
            ["!Cartesian and !NonCartesian", "contradict each other"],
            id="the cartesian and the non-cartesian grid",
        ),
    ],
)
def test_a_requirement_that_is_no_predicate_word_or_contradicts_another_is_refused_where_written(
    grid_stage_with_one_addition, requirement, phrases
):
    """A grid that requires a word that is no predicate word, or two
    predicate words that contradict each other, is refused under
    `grid-requirement` at the line of its entry."""
    with pytest.raises(ConstructionError) as refused:
        grid_stage_with_one_addition(
            VFI + f"cntn_to_dcsn.grid : !Points(nodes=B, require={requirement})\n"
        )
    error = refused.value
    # the grid entry is line 10 of the methods file: its header, the seven
    # settings of `GRID_VALUES` and the method entry stand before it
    assert (error.rule, error.address, error.file, error.line) == (
        "grid-requirement",
        "cntn_to_dcsn",
        "methods.bl",
        10,
    )
    assert [phrase for phrase in phrases if phrase not in error.message] == []


# Grids that the record of their constructor does not admit. Each row gives
# the stage text, the typing entries and the declarations of the methods
# file, the settings that `configure` binds beside `GRID_VALUES`, so that a
# refusal of the configured values is reached, the rule, the place and the
# file that the refusal names, and the phrases of its message. The entries of
# a builder that `!egm` methodizes stand in the stage text once the methods
# file is unioned with it, so that their refusal names the stage file.
REFUSED_GRIDS = [
    pytest.param(
        INVERSE_EULER_WITH_A_FIBRE,
        "policy.method : !egm\n"
        "policy.grid : !Fibred(base=!Points(nodes=A), fibre=!Cartesian(c=(Γ_c, n_c)))\n",
        "",
        {},
        ("grid-coordinate", "policy", "grids.bl"),
        [
            "on the states of the continuation perch",
            "a place of any other coordinate domain refuses",
        ],
        id="a fibred grid at the grid of the endogenous grid method",
    ),
    pytest.param(
        GRID_STAGE,
        f"cntn_to_dcsn.evaluate.method : !Linear\ncntn_to_dcsn.evaluate.grid : {FIBRED}\n",
        "",
        {},
        ("grid-coordinate", "cntn_to_dcsn.evaluate", "methods.bl"),
        ["reads a grid on (m)", "constructs pairs on (m, c)"],
        id="a fibred grid at the evaluation of a function of the states alone",
    ),
    pytest.param(
        GRID_STAGE,
        VFI + "cntn_to_dcsn.grid : !Fibred(base=!Cartesian(c=(Γ_c, n_c)), "
        "fibre=!Cartesian(c=(Γ_c, n_c)))\n",
        "",
        {},
        ("grid-coordinate", "cntn_to_dcsn", "methods.bl"),
        ["the base of !Fibred is !Points or a !Cartesian term without feasible-control factors"],
        id="a base of feasible factors",
    ),
    pytest.param(
        GRID_STAGE,
        VFI + "cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), fibre=!Points(nodes=B))\n",
        "",
        {},
        ("grid-coordinate", "cntn_to_dcsn", "methods.bl"),
        ["the fibre of !Fibred is a !Cartesian term whose factors are feasible-control factors"],
        id="a fibre of listed points",
    ),
    pytest.param(
        GRID_STAGE,
        VFI + "cntn_to_dcsn.grid : !Points(nodes=Z)\n",
        "",
        {},
        ("grid-setting-declared", "cntn_to_dcsn", "methods.bl"),
        ["'Z' as its points", "no setting a methods file declares and no set the stage defines"],
        id="points that no file declares",
    ),
    pytest.param(
        TWO_STATE_GRID_STAGE,
        "cntn_to_dcsn.evaluate.method : !Linear\ncntn_to_dcsn.evaluate.grid : !Points(nodes=P)\n",
        "P : ℝ × ℝ × ℝ\n",
        {},
        ("grid-coordinate", "cntn_to_dcsn.evaluate", "methods.bl"),
        ["whose points have 1 coordinate each", "the coordinates (m, z)", "`X2 := ℝ × ℝ`"],
        id="points of one coordinate at a place of two",
    ),
    pytest.param(
        GRID_STAGE,
        VFI + "cntn_to_dcsn.grid : !Points(nodes=Q)\n",
        "Q : ℝ × ℝ\n",
        {"Q": [-1.0, 1.0]},
        ("grid-bounds", "cntn_to_dcsn", "grids.bl"),
        ["the point (-1.0,)", "lies outside the declared set Xm"],
        id="a configured point outside the declared set",
    ),
]


@pytest.mark.parametrize(
    ("text", "entries", "declarations", "settings", "rule_place_and_file", "phrases"),
    REFUSED_GRIDS,
)
def test_a_grid_the_record_of_its_constructor_does_not_admit_is_refused_under_its_rule(
    grid_stage_with_one_addition,
    text,
    entries,
    declarations,
    settings,
    rule_place_and_file,
    phrases,
):
    """A grid that the record of its constructor does not admit is refused
    under its rule, at its place and in its file, with the phrases of its
    reason."""
    with pytest.raises(ConstructionError) as refused:
        grid_stage_with_one_addition(entries, declarations, text=text).configure(
            {**GRID_VALUES, **settings}
        )
    error = refused.value
    assert (error.rule, error.address, error.file) == rule_place_and_file
    assert [phrase for phrase in phrases if phrase not in error.message] == []


def test_the_kernels_of_a_builder_hold_no_grids_before_a_configuration(
    grid_stage_with_one_addition,
):
    """Before its settings are bound, the kernels of a builder whose places
    type two grids hold `None` under `grids`."""
    stage = grid_stage_with_one_addition(FIBRED_AND_A_FAMILY)
    assert stage.builder["cntn", "dcsn"].kernels().grids is None


def test_the_kernels_hold_the_refusal_of_a_grid_that_the_construction_cannot_establish(
    stage_with_a_grid_and_a_family,
):
    """The kernels hold, at the Evaluation whose grid is a family of grids,
    the `Refusal` under `grid-requirement` whose reason says so, at the line
    of its entry."""
    grids = stage_with_a_grid_and_a_family.builder["cntn", "dcsn"].kernels().grids
    family = grids["cntn_to_dcsn.evaluate"]
    assert isinstance(family, Refusal) and family.diagnostic["rule"] == "grid-requirement"
    assert "a family of grids of the control c, one at each state" in family.reason
    # the grid entry of the Evaluation is line 12 of the methods file: its
    # header, the seven settings of `GRID_VALUES` and three entries stand
    # before it
    assert (family.diagnostic["file"], family.diagnostic["line"]) == ("methods.bl", 12)


def test_a_realized_grid_prints_its_constructor_its_coordinates_and_its_points(
    stage_with_a_grid_and_a_family,
):
    """The realized fibred grid prints its constructor, its coordinates, the
    number of its points and the points."""
    grids = stage_with_a_grid_and_a_family.builder["cntn", "dcsn"].kernels().grids
    assert str(grids["cntn_to_dcsn"]) == (
        "!Fibred on (m, c), 4 points: (1, 0), (1, 1), (2, 0), (2, 2)"
    )


def test_the_printed_kernels_of_a_builder_end_with_a_row_for_the_grid_of_each_place(
    stage_with_a_grid_and_a_family,
):
    """The printed kernels of the builder end with a row for its realized
    grid and a row for the grid that is not constructed."""
    record = stage_with_a_grid_and_a_family.builder["cntn", "dcsn"].kernels()
    printed = str(record).splitlines()
    assert printed[-2] == (
        "grids        cntn_to_dcsn  !Fibred on (m, c), 4 points: (1, 0), (1, 1), (2, 0), (2, 2)"
    )
    assert printed[-1].startswith("             cntn_to_dcsn.evaluate  not constructed: stage")


def test_the_grids_of_the_kernels_of_a_builder_are_read_back_equal_from_a_pickle(
    stage_with_a_grid_and_a_family,
):
    """The standard pickle reads back the realized grid of four pairs equal,
    and the refusal with its reason and its diagnostic."""
    grids = stage_with_a_grid_and_a_family.builder["cntn", "dcsn"].kernels().grids
    assert grids["cntn_to_dcsn"].points == ((1, 0), (1, 1), (2, 0), (2, 2))
    back = pickle.loads(pickle.dumps(grids))
    assert back["cntn_to_dcsn"] == grids["cntn_to_dcsn"]
    family, read = grids["cntn_to_dcsn.evaluate"], back["cntn_to_dcsn.evaluate"]
    assert (read.reason, read.diagnostic) == (family.reason, family.diagnostic)


def test_the_kernels_of_a_builder_none_of_whose_places_types_a_grid_hold_no_grid(
    stage_with_a_grid_and_a_family,
):
    """Once the settings are bound and the backward decision builder holds
    its two grids, the kernels of the forward builder `dcsn_to_cntn`, which
    types no grid, hold an empty mapping under `grids`."""
    stage = stage_with_a_grid_and_a_family
    backward = stage.builder["cntn", "dcsn"].kernels().grids
    assert list(backward) == ["cntn_to_dcsn", "cntn_to_dcsn.evaluate"]
    assert stage.builder["dcsn", "cntn"].kernels().grids == {}


def test_two_grids_at_two_places_are_the_same_grid_where_they_hold_the_same_points(
    grid_stage_with_one_addition,
):
    """`same_grid` finds the product of two factors on (m, z) at the builder
    and the same four points, listed in another order, at its Evaluation one
    grid, and finds them two grids once one listed point differs."""
    stage = grid_stage_with_one_addition(
        PRODUCT_AND_POINTS_ON_M_AND_Z, P_ON_FOUR_PAIRS, text=TWO_STATE_GRID_STAGE
    )
    stage.configure(PRODUCT_IN_ANOTHER_ORDER)
    found = stage.builder["cntn", "dcsn"].kernels().grids
    assert found["cntn_to_dcsn"].points == ((1, -1), (1, 1), (2, -1), (2, 1))
    assert same_grid(found["cntn_to_dcsn"], found["cntn_to_dcsn.evaluate"])
    # the point (1, 1) listed as a second (2, 1), so that three points remain
    stage.configure({"P": [[2.0, 1.0], [1.0, -1.0], [2.0, -1.0], [2.0, 1.0]]})
    found = stage.builder["cntn", "dcsn"].kernels().grids
    assert not same_grid(found["cntn_to_dcsn"], found["cntn_to_dcsn.evaluate"])


def test_same_grid_refuses_two_constructed_grids_that_share_only_their_first_coordinate(
    grid_stage_with_one_addition, fibred_stage
):
    """`same_grid` refuses to compare the product grid on (m, z) that one
    stage constructs with the fibred grid on (m, c) of another stage."""
    stage = grid_stage_with_one_addition(
        PRODUCT_AND_POINTS_ON_M_AND_Z, P_ON_FOUR_PAIRS, text=TWO_STATE_GRID_STAGE
    )
    stage.configure(PRODUCT_IN_ANOTHER_ORDER)
    product = stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    joint = fibred_stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    with pytest.raises(ValueError, match="common valid context"):
        same_grid(product, joint)


def test_a_spaced_grid_is_not_the_grid_of_the_nearest_floating_point_numbers_to_its_points(
    grid_stage_with_one_addition,
):
    """The middle of three evenly spaced points from 0.1 to 0.2 is their
    exact mean, which no floating-point number equals, so that the grid that
    lists its nearest floating-point number is another grid."""
    spaced = grid_stage_with_one_addition(VFI_ON_SPACED_POINTS)
    spaced.configure({**GRID_VALUES, "m_lo": 0.1, "m_hi": 0.2, "n_m": 3})
    listed = grid_stage_with_one_addition(VFI_ON_THE_POINTS_P, "P : ℝ₊ × ℝ₊ × ℝ₊\n")
    listed.configure({**GRID_VALUES, "P": [0.1, 0.15000000000000002, 0.2]})
    spaced_grid = spaced.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    listed_grid = listed.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    assert [float(point[0]) for point in spaced_grid.points] == [0.1, 0.15000000000000002, 0.2]
    assert not same_grid(spaced_grid, listed_grid)


def test_the_points_of_a_spaced_factor_stay_distinct_where_one_float_is_nearest_to_two(
    grid_stage_with_one_addition,
):
    """Three evenly spaced points from 1 to the next floating-point number,
    1.0000000000000002, stay three exact points, distinct from each other
    and from the grid of the two end points, though only two floating-point
    numbers are nearest to them."""
    realized = {}
    for n_m in (3, 2):
        stage = grid_stage_with_one_addition(VFI_ON_SPACED_POINTS)
        stage.configure({**GRID_VALUES, "m_lo": 1.0, "m_hi": 1.0000000000000002, "n_m": n_m})
        realized[n_m] = stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    assert len({point[0] for point in realized[3].points}) == 3
    assert len({float(point[0]) for point in realized[3].points}) == 2
    assert not same_grid(realized[3], realized[2])


def test_a_listed_grid_keeps_two_integers_that_round_to_one_float_as_two_points(
    grid_stage_with_one_addition,
):
    """The integers 2**53 and 2**53 + 1, which round to one floating-point
    number, are two points of a grid of listed points."""
    stage = grid_stage_with_one_addition(VFI_ON_THE_POINTS_P, "P : ℝ₊ × ℝ₊\n")
    stage.configure({**GRID_VALUES, "P": [2**53, 2**53 + 1]})
    points = stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"].points
    assert points == ((2**53,), (2**53 + 1,))


# each realized grid below is written (constructor, coordinates, points)
@pytest.mark.parametrize(
    ("other", "same"),
    [
        pytest.param(
            RealizedGrid("Cartesian", ("m",), ((2**53 + 1,), (-0.0,), (1.0,))),
            True,
            id="the same points in another order by another constructor with a signed zero",
        ),
        pytest.param(
            RealizedGrid("Points", ("m",), ((0,), (1,), (2**53,))),
            False,
            id="a large integer one less",
        ),
    ],
)
def test_same_grid_compares_the_points_of_two_realized_grids_as_exact_numbers(other, same):
    """`same_grid` finds two realized grids on one coordinate one grid where
    their points are the same exact numbers, whatever their order and their
    constructor."""
    assert same_grid(GRID_WITH_A_LARGE_INTEGER, other) is same


@pytest.mark.parametrize(
    ("other", "error", "words"),
    [
        pytest.param(
            RealizedGrid("Points", ("z",), ((0,),)),
            ValueError,
            "common valid context",
            id="a grid on another coordinate",
        ),
        pytest.param(
            Refusal(
                reason="no grid",
                diagnostic={"stage": "t", "address": "b", "rule": "grid-requirement"},
            ),
            ValueError,
            "valid in no context",
            id="a refused grid",
        ),
        pytest.param(((0,), (1,)), TypeError, None, id="points that are no realized grid"),
    ],
)
def test_same_grid_refuses_a_second_grid_that_is_not_valid_in_the_context_of_the_first(
    other, error, words
):
    """`same_grid` refuses to compare a realized grid with a grid on another
    coordinate, with a refusal or with points that are no realized grid."""
    with pytest.raises(error, match=words):
        same_grid(GRID_WITH_A_LARGE_INTEGER, other)


@pytest.mark.parametrize(
    ("first", "second", "equal"),
    [
        pytest.param(
            [0.0, 1.0, 2.0],
            [2, 1, -0.0, 1.0],
            True,
            id="the same points in another order, one repeated, an integer and a signed zero",
        ),
        pytest.param([0.1], [numpy.float64(0.1)], True, id="a float and the same NumPy float"),
        pytest.param(
            [0.1], [Fraction(1, 10)], False, id="a float and the fraction that it rounds"
        ),
        pytest.param([2**60 + 1], [2**60], False, id="two large integers"),
        pytest.param(
            [2**53 + 1], [float(2**53 + 1)], False, id="an integer and its nearest float"
        ),
        pytest.param([numpy.int64(3)], [3.0], True, id="a NumPy integer and the float it equals"),
        pytest.param(
            [(0.0, 1.0), (1.0, 2.0)],
            numpy.array([[1.0, 2.0], [0.0, 1.0]]),
            True,
            id="pairs and an array of the same pairs in another order",
        ),
        pytest.param([(0.0, 1.0)], [0.0], False, id="points of two dimensions"),
        pytest.param([], (), True, id="two empty sets of points"),
    ],
)
def test_supports_equal_compares_two_finite_supports_as_exact_numbers(first, second, equal):
    """`supports_equal` compares two finite sets of points with no tolerance,
    each coordinate converted to an exact number."""
    assert supports_equal(first, second) is equal


@pytest.mark.parametrize(
    ("coordinate", "words"),
    [
        pytest.param(float("nan"), "is not finite", id="not a number"),
        pytest.param(float("-inf"), "is not finite", id="minus infinity"),
        pytest.param("1.0", "is not a real number", id="a string"),
        pytest.param(True, "is not a real number", id="a truth value"),
        pytest.param(1j, "is not a real number", id="a complex number"),
    ],
)
def test_supports_equal_refuses_a_coordinate_that_is_not_a_finite_real_number(coordinate, words):
    """`supports_equal` refuses a point whose coordinate is not a finite real
    number."""
    with pytest.raises(ValueError, match=words):
        supports_equal([coordinate], [1.0])


@pytest.mark.parametrize(
    ("limit", "lower_bounds", "ends"),
    [
        pytest.param(0.0, {}, (0.001, 20.0), id="the recorded settings at a limit of zero"),
        pytest.param(
            -0.5,
            {"a_min": -0.4, "k_min": -0.4},
            (-0.4, 20.0),
            id="lower bounds between a negative limit and zero",
        ),
    ],
)
def test_a_grid_whose_bounds_lie_in_its_set_at_the_calibration_is_built_on_them(
    buffer_stock_methods, buffer_stock_settings, limit, lower_bounds, ends
):
    """The grid of assets of the buffer-stock stage is built on 960 points
    from the lower bound to the upper bound of its settings, where both lie
    in `[a_Art, inf)` at the calibrated borrowing limit."""
    stage = buffer_stock_with_a_borrowing_limit(buffer_stock_methods)
    stage.calibrate(calibration_at(limit))
    stage.configure({"settings": {**buffer_stock_settings, **lower_bounds}})
    grid = stage.builder["dcsn", "arvl"].kernels().grids["dcsn_to_arvl.evaluate"]
    assert (grid.word, grid.coordinates, len(grid.points)) == ("Cartesian", ("k",), 960)
    assert (float(grid.points[0][0]), float(grid.points[-1][0])) == ends


def test_a_bound_declared_on_the_set_of_savings_is_decided_by_its_own_check_at_the_calibration(
    buffer_stock_methods, buffer_stock_settings
):
    """The check of the setting `a_min : Xa` refuses a lower bound of savings
    of -1 at a borrowing limit of zero under `setting-outside-set`, and
    admits it at a limit of -2."""
    outside = {**buffer_stock_settings, "a_min": -1.0}
    stage = buffer_stock_with_a_borrowing_limit(buffer_stock_methods)
    with pytest.raises(ConstructionError) as refused:
        stage.calibrate(calibration_at(0.0)).configure({"settings": outside})
    assert refused.value.rule == "setting-outside-set"
    assert "the value -1.0 lies outside the declared set [a_Art, inf)" in refused.value.message
    # at a limit below the lower bounds of savings and of assets
    inside = {**outside, "k_min": -1.0}
    stage.calibrate(calibration_at(-2.0)).configure({"settings": inside})


def test_a_bound_declared_on_the_reals_is_decided_by_the_check_of_its_grid_at_the_calibration(
    buffer_stock_methods, buffer_stock_settings
):
    """With `a_min` declared on ℝ, the check of the grid of savings refuses a
    lower bound of -1 at a borrowing limit of zero under `grid-bounds`,
    naming the limit that it read, and admits it at a limit of -2."""
    wide = changed(buffer_stock_methods, (LOWER_BOUND_ON_XA, LOWER_BOUND_ON_THE_REALS))
    outside = {**buffer_stock_settings, "a_min": -1.0}
    stage = buffer_stock_with_a_borrowing_limit(wide)
    with pytest.raises(ConstructionError) as refused:
        stage.calibrate(calibration_at(0.0)).configure({"settings": outside})
    assert (refused.value.rule, refused.value.address) == ("grid-bounds", "policy")
    assert (
        "the factor a=(a_min, a_max, n_a) writes the point -1.0, which lies outside the "
        "declared set Xa of a at a_Art = 0.0"
    ) in refused.value.message
    # at a limit below the lower bounds of savings and of assets
    inside = {**outside, "k_min": -1.0}
    stage.calibrate(calibration_at(-2.0)).configure({"settings": inside})


def test_before_a_calibration_a_bound_is_decided_only_on_a_set_that_reads_no_parameter(
    buffer_stock_methods, buffer_stock_settings
):
    """Before a calibration, `configure` refuses the recorded lower bound of
    assets on `[a_Art, inf)`, whose membership no value decides, and admits
    it on the set `ℝ₊₊` that the stage file declares."""
    stage = buffer_stock_with_a_borrowing_limit(buffer_stock_methods)
    with pytest.raises(ConstructionError) as refused:
        stage.configure({"settings": buffer_stock_settings})
    assert refused.value.rule == "grid-bounds"
    assert (
        "writes the point 0.001, which is not decidably inside the declared set Xa of k;"
    ) in refused.value.message
    # the stage file as written, configured before its calibration and
    # calibrated after it
    stage = stage_from_text(buffer_stock_text(), "buffer_stock.bl")
    stage.methodize({"text": buffer_stock_methods, "origin": "methods.bl"})
    stage.configure({"settings": buffer_stock_settings})
    stage.calibrate({"calibration": BUFFER_STOCK_BASELINE_CALIBRATION})
    grid = stage.builder["dcsn", "arvl"].kernels().grids["dcsn_to_arvl.evaluate"]
    assert len(grid.points) == 960


def test_a_bound_on_a_set_whose_lower_end_has_no_value_at_the_calibration_is_refused():
    """`configure` refuses under `grid-bounds` a bound of a grid on the set
    `[1/k_lo, inf)` at the calibration k_lo = 0, at which the lower end of
    the set has no value and decides no membership."""
    stage = stage_from_text(
        "@stage: t\nXk := [1/k_lo, inf)\nk_lo : ℝ\n"
        "[id=arvl_to_dcsn, (k : Xk) : !arvl -> (m : ℝ) : !dcsn] { m = k }\n"
        "[id=dcsn_to_arvl, (V : ℝ @ !vlu) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] { V[<] = V }\n"
    )
    stage.calibrate({"k_lo": 0.0}).methodize(
        {
            "text": "@methods: t\nn_k : ℕ\nk_min : ℝ\nk_max : ℝ\n"
            "dcsn_to_arvl.evaluate.method : !Linear\n"
            "dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))\n",
            "origin": "methods.bl",
        }
    )
    with pytest.raises(ConstructionError) as refused:
        stage.configure({"n_k": 5, "k_min": 1.0, "k_max": 2.0})
    assert refused.value.rule == "grid-bounds"
    assert "which is not decidably inside the declared set Xk of k" in refused.value.message


@pytest.mark.parametrize(
    "bind",
    [
        pytest.param(lambda stage, methods, settings: stage.configure(settings), id="configure"),
        pytest.param(
            lambda stage, methods, settings: stage.methodize(
                {"text": methods, "origin": "methods.bl"}
            ),
            id="methodize",
        ),
    ],
)
def test_each_binding_decides_the_bounds_of_a_grid_at_the_calibration_bound_then(
    buffer_stock_methods, buffer_stock_settings, bind
):
    """Once the borrowing limit is calibrated anew from -2 to -0.5, the
    binding refuses the lower bound of savings of -1 under `grid-bounds` at
    the new limit, and the stage calibrated back at -2 is configured
    again."""
    wide = changed(buffer_stock_methods, (LOWER_BOUND_ON_XA, LOWER_BOUND_ON_THE_REALS))
    settings = {"settings": {**buffer_stock_settings, "a_min": -1.0, "k_min": -0.4}}
    stage = buffer_stock_with_a_borrowing_limit(wide)
    stage.calibrate(calibration_at(-2.0)).configure(settings)
    # the limit moves above the lower bound of savings, -1, and stays below
    # the lower bound of assets, -0.4
    stage.calibrate(calibration_at(-0.5))
    with pytest.raises(ConstructionError) as refused:
        bind(stage, wide, settings)
    assert refused.value.rule == "grid-bounds"
    assert "lies outside the declared set Xa of a at a_Art = -0.5" in refused.value.message
    # and back below it
    stage.calibrate(calibration_at(-2.0))
    stage.configure(settings)


def test_a_listed_point_is_decided_at_the_calibrated_lower_end_of_its_set(
    grid_stage_with_one_addition,
):
    """A grid of the points 0.5, 1 and 2 on `[m_Low, inf)` is refused under
    `grid-bounds` at m_Low = 0.75 and built at m_Low = 0.25."""
    stage = grid_stage_with_one_addition(
        VFI_ON_THE_POINTS_P, P_ON_THREE_REALS, text=LOWER_BOUNDED_GRID_STAGE
    )
    with pytest.raises(ConstructionError) as refused:
        stage.calibrate({"m_Low": 0.75}).configure(THREE_LISTED_VALUES)
    assert refused.value.rule == "grid-bounds"
    assert (
        "whose coordinate m = 0.5 lies outside the declared set Xm at m_Low = 0.75"
    ) in refused.value.message
    stage = grid_stage_with_one_addition(
        VFI_ON_THE_POINTS_P, P_ON_THREE_REALS, text=LOWER_BOUNDED_GRID_STAGE
    )
    stage.calibrate({"m_Low": 0.25}).configure(THREE_LISTED_VALUES)
    points = stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"].points
    assert [float(point[0]) for point in points] == [0.5, 1.0, 2.0]


def test_before_a_calibration_the_construction_reports_a_listed_point_it_cannot_place(
    grid_stage_with_one_addition,
):
    """Before a calibration, the kernels hold, in place of a grid of listed
    points on `[m_Low, inf)`, the report that its point 0.5 is not decidably
    inside that set."""
    stage = grid_stage_with_one_addition(
        VFI_ON_THE_POINTS_P, P_ON_THREE_REALS, text=LOWER_BOUNDED_GRID_STAGE
    )
    stage.configure(THREE_LISTED_VALUES)
    report = stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    assert "its node m = 0.5 is not decidably inside the declared set Xm" in report.reason
