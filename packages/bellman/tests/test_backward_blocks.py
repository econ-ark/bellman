"""Backward blocks: the derivatives of values that their lines read and
state, the fields that their headers list, the states that their lines read,
and the values that their headers list and no line reads."""

import functools

import pytest
from application_files import FIXTURES_FOLDER, ROOT, SAVING_STAGE_FILES, WORKER_CONS_FILE
from printed_text import flat
from stage_builders import methodized_copy, stage_from_text
from stage_texts import DISC_WITH_K_NEXT_TEXT, changed, corpus_text

from bellman.refusals import ConstructionError
from bellman.stage import inventory, to_source
from bellman.stage.grains import construction_table
from bellman.stage.kernels import compile_kernel, kernel
from bellman.syntax.lower import parse_with_spans
from bellman.trellis import connection_report, derivative_missing, elaborate_trellis

# a consumption stage whose policy block reads one derivative term of the
# continuation value, written `TERM`: its first line inverts the marginal
# utility at that term, and its second line forms the grid of resources
CONSUMPTION_READING_A_TERM = (
    "@stage: t\n"
    "𝑢(c : ℝ₊₊) := c^(1-2)/(1-2)\n"
    "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)\n"
    "𝑑𝑢 := D_{c}(𝑢)\n"
    "[id=arvl_to_dcsn, (m[<] : ℝ₊) : !arvl -> (m : ℝ₊) : !dcsn] {\n    m = m[<]\n}\n"
    "[id=dcsn_to_cntn, (m, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n"
    "    a = m - c\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = 𝑢(c) + V[>]  :: [id=value]\n}\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
    "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
    "    c[>] = 𝑑𝑢𝑖𝑛𝑣(TERM)  :: [id=InvEuler]\n"
    "    m[>] = a + c[>]     :: [id=grid]\n"
    "    c = c[>]            :: [id=identification]\n}\n"
)


# the two forward blocks of `CONSUMPTION_READING_A_TERM`, each as written and
# as changed to carry a discrete state `k` on {0, 1} from the arrival perch to
# the continuation perch, so that the continuation perch has a discrete
# coordinate
DISCRETE_STATE = (
    (
        "(m[<] : ℝ₊) : !arvl -> (m : ℝ₊) : !dcsn] {\n    m = m[<]\n}",
        "(m[<] : ℝ₊, k[<] : {0, 1}) : !arvl -> (m : ℝ₊, k : {0, 1}) : !dcsn] {\n"
        "    m = m[<]\n    k = k[<]\n}",
    ),
    (
        "(m, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n    a = m - c\n}",
        "(m, c : !ctrl @ ℝ₊₊, k) : !dcsn -> (a : ℝ₊, k[>] : {0, 1}) : !cntn] {\n"
        "    a = m - c\n    k[>] = k\n}",
    ),
)


def consumption_text(term):
    """The text of `CONSUMPTION_READING_A_TERM` with `term` in place of
    `TERM`."""
    return CONSUMPTION_READING_A_TERM.replace("TERM", term)


def parsed_term(term):
    """The term that the parser makes of the consumption stage that reads
    `term`."""
    return parse_with_spans(consumption_text(term), "t.bl")[0]


@pytest.mark.parametrize(
    "term, parenthesized",
    [
        pytest.param("D_{a}V[>]", "D_{a}(V[>])", id="the continuation value"),
        pytest.param("D_{m}V", "D_{m}(V)", id="the decision value"),
        pytest.param("D_{a}V[<]", "D_{a}(V[<])", id="the arrival value"),
    ],
)
def test_a_derivative_term_on_a_field_is_read_as_the_call_on_the_field_in_parentheses(
    term, parenthesized
):
    """A derivative term written on a field parses to the term of the call
    with the field in parentheses."""
    assert parsed_term(term) == parsed_term(parenthesized)


def test_a_derivative_term_keeps_the_mark_of_its_field():
    """The term `D_{a}V[>]`, on the continuation value, parses to another
    term than `D_{a}(V)`, on the decision value."""
    assert parsed_term("D_{a}V[>]") != parsed_term("D_{a}(V)")


@pytest.mark.parametrize(
    "term, changes, phrases",
    [
        pytest.param("D_{q}V[>]", (), ["'q'", "cntn", " a"], id="a name that is no state"),
        pytest.param("D_{k}V[>]", DISCRETE_STATE, ["'k'", "discrete"], id="a discrete state"),
        pytest.param("D_{c}V[>]", (), ["'c'"], id="the control"),
    ],
)
def test_a_derivative_term_that_names_no_continuous_state_of_its_perch_is_refused(
    term, changes, phrases
):
    """A derivative term whose subscript is no continuous state of the perch
    at which its value is read is refused under `derivative-coordinate`,
    where the same stage reading `D_{a}V[>]` elaborates."""
    accepted = changed(consumption_text("D_{a}V[>]"), *changes)
    assert stage_from_text(accepted).name == "t"
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed(consumption_text(term), *changes))
    assert (refused.value.rule, refused.value.address) == (
        "derivative-coordinate",
        "policy.InvEuler",
    )
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []


def test_a_kernel_evaluates_its_line_at_the_derivative_term_given_as_an_argument():
    """The compiled kernel of the grid line of the policy evaluates the
    inverse Euler line at the value given for its argument `D_{a}(V≻)`,
    differentiating nothing."""
    reading = stage_from_text(consumption_text("D_{a}V[>]"))
    grid = reading.dcsn.builder.policy.primitives["grid:Aggregation"]
    assert [name for name, _ in grid.kernel().arguments] == ["V≻", "a", "D_{a}(V≻)"]
    # V≻ = 0, a = 1 and D_{a}(V≻) = 4: c≻ = 4^(-1/2) = 0.5 and
    # m≻ = a + c≻ = 1.5
    assert grid.compile_kernel()(0.0, 1.0, 4.0) == (4.0**-0.5, 1 + 4.0**-0.5)


def test_a_derivative_of_a_value_that_the_block_does_not_list_is_refused_as_an_unlisted_read():
    """The policy line that reads `D_{m}V`, the derivative of the decision
    value, which the policy header does not list, is refused under
    `signature-complete`, where the same stage reading `D_{a}V[>]`, of the
    continuation value that the header lists, elaborates."""
    assert stage_from_text(consumption_text("D_{a}V[>]")).name == "t"
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(consumption_text("D_{m}V"))
    assert refused.value.rule == "signature-complete"


# a stage with no control whose decision builder states the derivative of its
# value as an expectation of a derivative term of the continuation value times
# a parameter, the form of the portfolio stages; the line states the
# derivative of the value that the block writes and has no unknown
COMPOSITE_DERIVATIVE = (
    "@stage: t\n"
    "R : ℝ₊₊\n"
    "θ : ℝ₊₊\n"
    "θ ~ LogNormal(0, 1)\n"
    "[id=arvl_to_dcsn, (k : ℝ₊) : !arvl -> (k_d : ℝ₊) : !dcsn] {\n    k_d = k\n}\n"
    "[id=dcsn_to_cntn, (k_d, θ) : !dcsn -> (m : ℝ₊₊) : !cntn] {\n    m = k_d*R + θ\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V        = E_{θ}(V[>])          :: [id=value]\n"
    "    D_{k_d}V = E_{θ}(D_{m}V[>]*R)   :: [id=marginal]\n}\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
)


# a portfolio stage of the form of the applications: the share ς is the
# control, two shocks are drawn on the way to the continuation perch, and the
# derivative line of the decision builder integrates a derivative term of the
# continuation value over both
PORTFOLIO_SHARE = (
    "@stage: t\n"
    "R : ℝ₊₊\n"
    "Ψ : ℝ₊₊\n"
    "θ : ℝ₊₊\n"
    "Ψ ~ LogNormal(0, 1)\n"
    "θ ~ LogNormal(0, 1)\n"
    "[id=arvl_to_dcsn, (k : ℝ₊) : !arvl -> (k_d : ℝ₊) : !dcsn] {\n    k_d = k\n}\n"
    "[id=dcsn_to_cntn, (k_d, ς : !ctrl @ [0, 1], Ψ, θ) : !dcsn -> (m_next : ℝ₊₊) : !cntn] {\n"
    "    m_next = k_d*(ς*Ψ + (1 - ς)*R) + θ\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, ς) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V        = E_{Ψ,θ}(V[>])                                 :: [id=value]\n"
    "    D_{k_d}V = E_{Ψ,θ}(D_{m_next}V[>]*(ς*Ψ + (1 - ς)*R))   :: [id=marginal]\n}\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
    "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (ς : [0, 1] @ !ctrl) : !dcsn] {\n"
    "    ς = solve_{ς}(E_{Ψ,θ}(D_{m_next}V[>]*(Ψ - R)))   :: [id=foc]\n}\n"
)


# a methods file that types a quadrature at the operator head `E_Ψ_θ`, which
# names every expectation over Ψ and θ of the stage; each count of nodes is a
# declared setting, since the entry of a method writes no number
GAUSS_HERMITE_METHODS = {
    "text": "@methods: t\nn_Ψ_nodes : ℕ\nn_θ_nodes : ℕ\n"
    "E_Ψ_θ.method : !gauss_hermite(n_Ψ=n_Ψ_nodes, n_θ=n_θ_nodes)\n",
    "origin": "t.methods.bl",
}


@pytest.fixture(scope="module")
def composite_derivative():
    """The stage of `COMPOSITE_DERIVATIVE`."""
    return stage_from_text(COMPOSITE_DERIVATIVE)


@pytest.fixture(scope="module")
def portfolio_with_quadrature():
    """The stage of `PORTFOLIO_SHARE`, methodized by `GAUSS_HERMITE_METHODS`
    and configured with seven nodes for each of its two shocks."""
    stage = stage_from_text(PORTFOLIO_SHARE)
    stage.methodize(GAUSS_HERMITE_METHODS)
    stage.configure({"settings": {"n_Ψ_nodes": 7, "n_θ_nodes": 7}})
    return stage


def evaluations_of_the_decision_builder(stage):
    """The rows of the Evaluations of the decision builder `cntn_to_dcsn` in
    the construction table of a stage."""
    return [
        row
        for row in construction_table(stage).primitive_rows
        if row.kind == "Evaluation" and row.builder == "cntn_to_dcsn"
    ]


def test_the_policy_builder_of_cons_maps_the_continuation_value_alone_to_the_policy(cons):
    """The signature of the policy builder of `cons.bl`, whose decision
    builder states the derivative of its value by a line, is `𝑉≻` ↦ `𝑐(m_d)`,
    with no derivative among its inputs."""
    text = corpus_text("cons")
    # the file types no field with the retired words `!mrgnvl` and
    # `!sndmrgnvl`, which the package refuses, and states the derivative of
    # its value by the line of its decision builder
    assert "!mrgnvl" not in text and "!sndmrgnvl" not in text
    assert "    D_{m_d}V = 𝑑𝑢(c)" in text
    signature = str(cons.dcsn.builder.policy.signature())
    assert signature.splitlines()[0].split()[:2] == ["in", "𝑉≻"]
    assert signature.splitlines()[1].split()[1].startswith("𝑐(m_d)")
    assert "dV" not in signature


@pytest.mark.parametrize(
    "stage_name, field, address, right_side, line",
    [
        pytest.param(
            "cons",
            "m_d",
            "cntn_to_dcsn.marginal",
            "𝑑𝑢(c)",
            "D_{m_d}(V) = 𝑑𝑢(c)",
            id="cons",
        ),
        pytest.param(
            "composite_derivative",
            "k_d",
            "cntn_to_dcsn.marginal",
            "E_{θ}(D_{m}V[>]*R)",
            "D_{k_d}(V) = E_{θ}(D_{m}V[>]*R)",
            id="an expectation of a derivative term times a parameter",
        ),
    ],
)
def test_the_evaluation_of_a_builder_records_its_derivative_line_as_a_stated_derivative(
    stage_name, field, address, right_side, line, request
):
    """The one Evaluation of the decision builder records the derivative line
    of the stage as a stated derivative, with the coordinate of its left
    side, its address, its right side and the line."""
    rows = evaluations_of_the_decision_builder(request.getfixturevalue(stage_name))
    assert [len(row.outputs) for row in rows] == [1]
    ((coordinate, term, recorded_at, source, _value),) = rows[0].derivatives
    assert (coordinate.field, recorded_at) == (field, address)
    # a bare field name prints in parentheses, since the printer cannot tell
    # it from the name of a function; a marked field prints bare, `D_{m}V[>]`
    assert (to_source(term), source) == (right_side, line)


@pytest.mark.parametrize(
    "stage_name",
    [
        pytest.param("cons", id="cons"),
        pytest.param(
            "composite_derivative", id="an expectation of a derivative term times a parameter"
        ),
    ],
)
def test_a_derivative_line_is_listed_under_marginal_reading_and_not_as_a_retained_relation(
    stage_name, request
):
    """The obligations of the stage list its derivative line under
    `marginal-reading`, whose explanation names the envelope conditions, and
    list no `retained-relation`."""
    stage = request.getfixturevalue(stage_name)
    conditions = {item.condition for item in stage.obligations()}
    assert "retained-relation" not in conditions
    listed = [item for item in stage.obligations() if item.condition == "marginal-reading"]
    assert [entry.address for item in listed for entry in item.entries] == [
        "cntn_to_dcsn.marginal"
    ]
    assert "envelope conditions" in listed[0].explanation


def test_the_kernel_of_a_derivative_line_evaluates_its_right_side_differentiating_nothing(cons):
    """The compiled kernel of the piece `marginal:Derivative:1` of the
    decision builder of `cons.bl`, whose arguments are those of the value
    line, `V≻`, `m_d` and `c`, then the parameter `ρ`, evaluates the right
    side `𝑑𝑢(c)` of the derivative line."""
    piece = kernel(cons, "marginal:Derivative:1")
    assert [name for name, _ in piece.arguments] == ["V≻", "m_d", "c"]
    assert (piece.outputs, piece.parameters) == (("D_{m_d}V",), ("ρ",))
    # V≻ = 0, m_d = 2 and c = 0.5, then ρ = 2: 𝑑𝑢(c) = c^(-ρ) = 0.5^(-2)
    assert compile_kernel(cons, "marginal:Derivative:1")(0.0, 2.0, 0.5, 2.0) == 0.5 ** (-2.0)


@pytest.mark.parametrize(
    "stage_name, integrated",
    [
        pytest.param("cons", (), id="cons"),
        pytest.param("portfolio_with_quadrature", ("Ψ", "θ"), id="the portfolio stage"),
    ],
)
def test_the_piece_of_a_derivative_line_is_the_last_piece_of_the_kernels_of_its_builder(
    stage_name, integrated, request
):
    """The last piece of the kernels of the decision builder is the piece
    `marginal:Derivative:1` of its derivative line, integrated over the
    shocks of the expectation of its right side."""
    builder = request.getfixturevalue(stage_name).builder["cntn", "dcsn"]
    last = builder.kernels().pieces[-1]
    assert (last.name, last.integrated) == ("marginal:Derivative:1", integrated)


def test_a_quadrature_typed_at_an_operator_head_is_the_method_of_the_value_expectation(
    portfolio_with_quadrature,
):
    """The quadrature that the methods file types at the operator head
    `E_Ψ_θ` is the method of the expectation of the value line of the
    portfolio stage."""
    method = portfolio_with_quadrature.methods["E_Ψ_θ"]
    assert str(method) == "!gauss_hermite(n_Ψ=n_Ψ_nodes, n_θ=n_θ_nodes)"
    builder = portfolio_with_quadrature.builder["cntn", "dcsn"]
    assert list(builder.primitives["value:Expectation:1"].methods) == ["E_Ψ_θ"]


def test_the_kernel_of_a_derivative_line_under_one_expectation_computes_its_integrand(
    portfolio_with_quadrature,
):
    """The piece of the derivative line of the portfolio stage, whose right
    side is one expectation over Ψ and θ, computes the integrand of that
    expectation, a function of the two shocks among its other arguments."""
    piece = kernel(portfolio_with_quadrature, "marginal:Derivative:1")
    assert [name for name, _ in piece.arguments] == ["ς", "Ψ", "θ", "D_{m_next}V[>]"]
    assert piece.integrated == ("Ψ", "θ") and "integrated over Ψ, θ" in str(piece)
    integrand = compile_kernel(portfolio_with_quadrature, "marginal:Derivative:1")
    # ς = 0.5, Ψ = 1.2, θ = 1 and D_{m_next}V[>] = 3, then R = 1.1: the
    # integrand is D_{m_next}V[>]*(ς*Ψ + (1 - ς)*R)
    assert integrand(0.5, 1.2, 1.0, 3.0, 1.1) == pytest.approx(3.0 * (0.5 * 1.2 + 0.5 * 1.1))


# a consumption stage that declares no arrival perch, so that its decision
# perch is the first perch of the stage, and whose policy line reads a
# derivative of the continuation value, written `TERM`
CONSUMPTION_ENTERED_AT_DECISION = (
    "@stage: cons\n"
    "ρ : (1, inf)\n"
    "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)\n"
    "𝑑𝑢 := D_{c}(𝑢)\n"
    "𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)\n"
    "[id=dcsn_to_cntn, (m : ℝ₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {\n"
    "    a = m - c\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = 𝑢(c) + V[>]\n}\n"
    "[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {\n"
    "    c = 𝑑𝑢𝑖𝑛𝑣(TERM)\n}\n"
)


# a discounting stage that declares no arrival perch, whose decision value
# `V` is the value it exports
DISCOUNTING_ENTERED_AT_DECISION = (
    "@stage: disc\n"
    "β : (0,1)\n"
    "[id=dcsn_to_cntn, (k : ℝ₊) : !dcsn -> (k_next : ℝ₊) : !cntn] {\n"
    "    k_next = k\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = β*V[>]\n}\n"
)


# a discounting stage that keeps its arrival block, `V[<] = V`, and states
# the derivative of its decision value: the stated derivative passes through
# the arrival builder, whose line is an identity of the value and whose law
# between the perches, `k_d = k`, is the identity in the coordinate
DISCOUNTING_STATING_ITS_DERIVATIVE = (
    "@stage: disc\n"
    "β : (0,1)\n"
    "𝑤(k : ℝ₊) := k^(-2)\n"
    "[id=arvl_to_dcsn, (k : ℝ₊) : !arvl -> (k_d : ℝ₊) : !dcsn] {\n"
    "    k_d = k\n}\n"
    "[id=dcsn_to_cntn, (k_d) : !dcsn -> (k_next : ℝ₊) : !cntn] {\n"
    "    k_next = k_d\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = β*V[>]\n"
    "    D_{k_d}V = β*𝑤(k_d)\n}\n"
    "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n"
    "    V[<] = V\n}\n"
)


def trellis_of_two_periods(
    order, term, representation=None, discounting=DISCOUNTING_ENTERED_AT_DECISION
):
    """The trellis of two periods, each holding the consumption stage that
    reads `term` and the discounting stage `discounting` in the order of the
    pair `order`: within a period the continuation of the first stage joins
    the state of the first perch of the second, and between the periods the
    continuation of the second stage joins the state of the first perch of
    the first. With `representation`, that method and its grid are typed at
    the Evaluation of the value builder of the discounting stage."""
    consumption = stage_from_text(CONSUMPTION_ENTERED_AT_DECISION.replace("TERM", term), "cons.bl")
    discounting_stage = stage_from_text(discounting, "disc.bl")
    if representation is not None:
        discounting_stage.methodize(
            {
                "text": (
                    f"@methods: disc\ncntn_to_dcsn.evaluate.method : {representation}\n"
                    "k_min : ℝ\nk_max : ℝ\nn_k : ℕ\n"
                    "cntn_to_dcsn.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))\n"
                ),
                "origin": "disc.methods.bl",
            }
        )
    stages = {"cons": consumption, "disc": discounting_stage}
    within = {"cons.a": "disc.k"} if order[0] == "cons" else {"disc.k_next": "cons.m"}
    between = {"k_next": "m"} if order[0] == "cons" else {"a": "k"}
    period = {"stages": {key: stages[key] for key in order}, "connectors": [within]}
    return elaborate_trellis({"periods": [period, dict(period)], "inter_connectors": [between]})


@pytest.fixture(scope="module")
def two_stage_trellis():
    """`two_stage_trellis(order, term, ...)`: the trellis of
    `trellis_of_two_periods`, built once for the module for each set of
    arguments; the tests only query it, and no query changes it."""
    return functools.cache(trellis_of_two_periods)


ORDERS = [
    pytest.param(("cons", "disc"), id="consumption first"),
    pytest.param(("disc", "cons"), id="discounting first"),
]


@pytest.mark.parametrize("order", ORDERS)
def test_every_route_of_the_two_stage_trellis_is_certified(order, two_stage_trellis):
    """Each route of the trellis of two periods of the consumption stage that
    reads `D_{a}V[>]` and the discounting stage, which declare no arrival
    perch, is certified."""
    routes = connection_report(two_stage_trellis(order, "D_{a}V[>]")).routes
    assert routes
    assert [route.status for route in routes] == ["certified"] * len(routes)


@pytest.mark.parametrize("order", ORDERS)
def test_derivative_missing_reports_a_derivative_read_that_no_later_stage_states_or_evaluates(
    order, two_stage_trellis
):
    """In the trellis of two periods of the consumption stage that reads
    `D_{a}V[>]` and the discounting stage, `derivative_missing` reports the
    reading at the consumption stage of the first period, unless the
    discounting stage represents its value by `!pchip` or states the
    derivative of its value."""
    found = derivative_missing(two_stage_trellis(order, "D_{a}V[>]"))
    assert [item.rule for item in found] == ["derivative-missing"]
    [item] = found
    # the line `V = β*V[>]` of the discounting stage passes the value through,
    # so the reading of the consumption stage of the second period passes to
    # the consumption stage of the first period, whose decision value carries
    # no derivative; the reading of the first period falls to the terminal data
    assert item.address == "periods[0].stages['cons']"
    phrases = ["stage 'cons'", "pass-through of disc", "`D_{a}V[>]`"]
    assert [phrase for phrase in phrases if phrase not in item.message] == []
    assert item.candidates == ("cons:function:dcsn:V", "m")
    # `!pchip` evaluates the first derivative of the value that it represents
    pchip = two_stage_trellis(order, "D_{a}V[>]", representation="!pchip")
    assert derivative_missing(pchip) == ()
    # the derivative that the discounting stage states of its decision value
    # passes through its arrival builder
    stating = two_stage_trellis(order, "D_{a}V[>]", discounting=DISCOUNTING_STATING_ITS_DERIVATIVE)
    assert derivative_missing(stating) == ()


@pytest.mark.parametrize("order", ORDERS)
def test_derivative_missing_reports_a_second_derivative_read_that_linear_does_not_evaluate(
    order, two_stage_trellis
):
    """The second derivative `D_{a}D_{a}V[>]` that the consumption stage
    reads of the value of the discounting stage is reported under
    `derivative-missing` where `!Linear`, which evaluates the first
    derivative alone, represents that value, and not where `!pchip` does."""
    # the term is written `D_{a}(D_{a}V[>])`, since the grammar admits no
    # nested call after the subscript of a derivative on a field
    term = "D_{a}(D_{a}V[>])"
    found = derivative_missing(two_stage_trellis(order, term, representation="!Linear"))
    assert [item.rule for item in found] == ["derivative-missing"]
    [item] = found
    assert "`D_{a}D_{a}V[>]`" in item.message
    # the value of the discounting stage, represented by `!Linear`, evaluates
    # no second derivative and passes the requirement through to the
    # consumption stage of the first period, which is reported
    assert item.candidates == ("cons:function:dcsn:V", "m", "m")
    assert derivative_missing(two_stage_trellis(order, term, representation="!pchip")) == ()


HOUSING_RENTING = ROOT / "applications/housing-renting/declaration/stages"


# the folder of the stage files that the tests keep as fixtures
FIXTURE_STAGES = ROOT / FIXTURES_FOLDER


# the methods file of the worker's consumption stage of the retirement-choice
# application
WORKER_CONS_METHODS = ROOT / WORKER_CONS_FILE.replace("worker_cons.bl", "methods.bl")


@pytest.fixture(scope="module")
def stage_files():
    """The texts of the stage files that the tests change, by the name of the
    file that each test gives its stage: the keeper's consumption stage of
    the durables application, kept with an arrival block whose law between
    the perches is the identity; the keeper's saving stage of the
    housing-frictions application; the discounting stage of the durables
    application, kept with its arrival block, so that the name `a` stands for
    a state at the arrival perch and at the continuation perch; the renter's
    consumption stage of the housing-renting application; the consumption
    stage of the fixture folder; and the corpus stage `cons_savings_iid.bl`."""
    return {
        "keeper_cons.bl": (FIXTURE_STAGES / "keeper_cons_with_arrival.bl").read_text(
            encoding="utf-8"
        ),
        "keeper_saving.bl": (ROOT / SAVING_STAGE_FILES["keeper_saving"]).read_text(
            encoding="utf-8"
        ),
        "disc.bl": (FIXTURE_STAGES / "disc_with_arrival.bl").read_text(encoding="utf-8"),
        "renter_cons.bl": (HOUSING_RENTING / "renter_cons" / "renter_cons.bl").read_text(
            encoding="utf-8"
        ),
        "cons.bl": (FIXTURE_STAGES / "cons.bl").read_text(encoding="utf-8"),
        "cons_savings_iid.bl": corpus_text("cons_savings_iid"),
    }


@pytest.fixture(scope="module")
def keeper_cons(stage_files):
    """The stage of the keeper's consumption stage with its arrival block."""
    return stage_from_text(stage_files["keeper_cons.bl"], "keeper_cons.bl")


@pytest.fixture(scope="module")
def owner_cons(read_only_stage_from_file):
    """The stage of `owner_cons.bl` of the housing-renting application, whose
    value line reads the decision state `H_d`."""
    return read_only_stage_from_file(HOUSING_RENTING / "owner_cons" / "owner_cons.bl")


@pytest.fixture(scope="module")
def discounting_reading_no_value():
    """The discounting stage `DISC_WITH_K_NEXT_TEXT` whose value line `V = β`
    reads no value input."""
    return stage_from_text(
        changed(DISC_WITH_K_NEXT_TEXT, ("    V = β*V[>]\n", "    V = β\n")), "disc.bl"
    )


@pytest.fixture(scope="module")
def discounting_with_an_unread_value():
    """The discounting stage `DISC_WITH_K_NEXT_TEXT` whose value header also
    lists a value `W[>]` that no line reads."""
    header = "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn"
    listing = "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, W[>] : ℝ @ !vlu) : !cntn"
    return stage_from_text(changed(DISC_WITH_K_NEXT_TEXT, (header, listing)), "disc.bl")


@pytest.mark.parametrize(
    "stage_name, builder, printed",
    [
        pytest.param(
            "owner_cons",
            "cntn_to_dcsn",
            "in   𝑉≻ : ℝ₊ × ℝ₊ × ℝ₊₊ → [−∞, ∞)\nout  𝑉 : ℝ₊₊ × ℝ₊ × ℝ₊₊ → [−∞, ∞)",
            id="a value line that reads the decision state H_d",
        ),
        pytest.param(
            "cons_savings_iid",
            "cntn_to_dcsn",
            "in   𝑉≻ : ℝ₊ → ℝ\nout  𝑉 : ℝ₊ → ℝ",
            id="the value builder of cons_savings_iid",
        ),
        pytest.param(
            "cons_savings_iid",
            "policy",
            "in   𝑉≻ : ℝ₊ → ℝ\nout  𝑐(w) : 𝒫({c ∈ (ℝ₊ → ℝ₊₊) | c(w) ∈ Γ(w)})",
            id="a policy whose !doc line reads the value",
        ),
        pytest.param(
            "cons",
            "cntn_to_dcsn",
            "in   𝑉≻ : Xa → [−∞, ∞)\nout  𝑉 : Xm → [−∞, ∞)",
            id="the value builder of cons",
        ),
        pytest.param(
            "discounting_reading_no_value",
            "cntn_to_dcsn",
            "in   𝑉≻ : ℝ₊ → ℝ\nout  𝑉 : ℝ₊ → ℝ",
            id="a value line that reads no value input",
        ),
    ],
)
def test_the_signature_of_a_backward_builder_lists_the_values_of_its_header_and_no_state(
    stage_name, builder, printed, request
):
    """The printed signature of a backward builder lists the values that the
    header of its block lists, and no state."""
    stage = request.getfixturevalue(stage_name)
    assert flat(str(stage.builder.bwd[builder].signature())) == flat(printed)


@pytest.mark.parametrize(
    "stage_name, expected",
    [
        pytest.param("cons_savings_iid", [], id="every listed value read"),
        pytest.param("discounting_reading_no_value", [], id="no listed value read"),
        pytest.param(
            "discounting_with_an_unread_value",
            [("unread-input", "cntn_to_dcsn", ("disc:cntn:W",))],
            id="one of two listed values unread",
        ),
    ],
)
def test_a_listed_value_that_no_line_reads_is_a_diagnostic_where_another_listed_value_is_read(
    stage_name, expected, request
):
    """The stage records as a diagnostic a value that a backward header lists
    and no line of its block reads, where the lines read another value that
    the header lists."""
    diagnostics = request.getfixturevalue(stage_name).diagnostics()["unread_inputs"]
    assert [(item.rule, item.address, item.candidates) for item in diagnostics] == expected


# the header of the value block of `keeper_cons.bl`, its output side, and the
# value line of that block
KEEPER_VALUE_HEADER = "(V[>] : ℝ @ !vlu, c) ->"


KEEPER_VALUE_OUTPUT = "(V : ℝ @ !vlu) : !dcsn"


KEEPER_VALUE_LINE = "    V = 𝑢(c, h_d) + β*V[>]                             :: [id=value]"


# the output side of the value block of `keeper_cons.bl` listing the decision
# state `h_d`, with a line, of the id `alien`, that defines it
KEEPER_STATE_OUTPUT = (
    (KEEPER_VALUE_OUTPUT, "(V : ℝ @ !vlu, h_d : ℝ₊₊ @ !state) : !dcsn"),
    (
        KEEPER_VALUE_LINE,
        "    h_d = 1                                         :: [id=alien]\n" + KEEPER_VALUE_LINE,
    ),
)


# the policy header of `renter_cons.bl`, and the value header of the
# discounting stage with its arrival block
RENTER_POLICY_HEADER = "[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn ->"


DISCOUNTING_VALUE_HEADER = "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn ->"


# a backward header that lists a state: the file, each change applied to it,
# the address of the refusal, the phrases of its message and phrases that the
# message does not hold
LISTED_STATES = [
    pytest.param(
        "keeper_cons.bl",
        ((KEEPER_VALUE_HEADER, "(V[>] : ℝ @ !vlu, c, h_d : !dcsn) ->"),),
        "cntn_to_dcsn",
        [
            "lists h_d",
            "h_d is a state of the dcsn perch, the perch at which the block's output stands",
            "coordinate of the output function",
            "`(V[>] : ℝ @ !vlu, c) -> (V : ℝ @ !vlu) : !dcsn`",
        ],
        [],
        id="a state of the perch of the output",
    ),
    pytest.param(
        "keeper_cons.bl",
        ((KEEPER_VALUE_HEADER, "(V[>] : ℝ @ !vlu, c, h_nxt_kp : !cntn) ->"),),
        "cntn_to_dcsn",
        [
            "h_nxt_kp is a state of the cntn perch, the perch the block reads its value fields at",
            "through the forward law of motion",
        ],
        ["h_nxt_kp is a state of the dcsn perch"],
        id="a state of the perch of the inputs",
    ),
    pytest.param(
        "keeper_cons.bl",
        KEEPER_STATE_OUTPUT,
        "cntn_to_dcsn",
        [
            "lists h_d on its output side",
            "Remove the state output, `(V[>] : ℝ @ !vlu, c) -> (V : ℝ @ !vlu) : !dcsn`",
        ],
        [],
        id="a state on the output side",
    ),
    pytest.param(
        "keeper_cons.bl",
        (*KEEPER_STATE_OUTPUT, (KEEPER_VALUE_HEADER, "() ->")),
        "cntn_to_dcsn",
        ["lists h_d on its output side"],
        [],
        id="a state on the output side of a header with no input",
    ),
    pytest.param(
        "renter_cons.bl",
        ((RENTER_POLICY_HEADER, "[id=policy, (V[>] : [-inf, inf) @ !vlu, S_d) ->"),),
        "policy",
        ["S_d is a state of the dcsn perch, the perch at which the block's output stands"],
        [],
        id="a policy header with no perch word",
    ),
    pytest.param(
        "disc.bl",
        ((DISCOUNTING_VALUE_HEADER, "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, a[>]) : !cntn ->"),),
        "cntn_to_dcsn",
        ["a[>] is a state of the cntn perch, the perch the block reads its value fields at"],
        [],
        id="the continuation state a[>]",
    ),
    pytest.param(
        "disc.bl",
        ((DISCOUNTING_VALUE_HEADER, "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, a[<]) : !cntn ->"),),
        "cntn_to_dcsn",
        ["a[<] is a state of the arvl perch, a perch the block neither stands at nor reads from"],
        [],
        id="the arrival state a[<]",
    ),
]


@pytest.mark.parametrize("origin, changes, address, phrases, absent", LISTED_STATES)
def test_a_state_listed_on_a_backward_header_is_refused_under_header_coordinate(
    origin, changes, address, phrases, absent, stage_files
):
    """A backward header that lists a state, on either side, is refused under
    `header-coordinate`, with a message that names the state and where it
    stands."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed(stage_files[origin], *changes), origin)
    assert (refused.value.rule, refused.value.address) == ("header-coordinate", address)
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []
    assert [phrase for phrase in absent if phrase in refused.value.message] == []


# a block whose line reads a field that its header does not list: the file,
# the header as written and as changed, the address of the refusal, the
# phrases of its message, and states that the message does not name
UNLISTED_READS = [
    pytest.param(
        "keeper_cons.bl",
        (KEEPER_VALUE_HEADER, "(c) ->"),
        "cntn_to_dcsn.value",
        [
            "reads V[>]",
            "the value fields its lines read",
            "`(c, V[>]) -> (V : ℝ @ !vlu) : !dcsn`",
        ],
        ["w_d", "h_d", "z_d"],
        id="a value block that reads V[>]",
    ),
    pytest.param(
        "cons_savings_iid.bl",
        ("[id=policy, (V[>] : ℝ @ !vlu) : !cntn ->", "[id=policy, () : !cntn ->"),
        "policy.optimality",
        [
            "reads V[>]",
            "the value fields its lines read",
            "`(V[>]) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn`",
        ],
        [],
        id="a policy block whose first line, a !doc line, reads V[>]",
    ),
    pytest.param(
        "keeper_cons.bl",
        ("(w_d, h_d, z_d, c : ℝ₊₊ @ !ctrl) : !dcsn", "(w_d, h_d, c : ℝ₊₊ @ !ctrl) : !dcsn"),
        "dcsn_to_cntn.income_state",
        [
            "reads z_d",
            "every field its lines read",
            "`(w_d, h_d, c : ℝ₊₊ @ !ctrl, z_d) : !dcsn -> ",
        ],
        [],
        id="a forward block that reads the state z_d",
    ),
]


@pytest.mark.parametrize("origin, change, address, phrases, absent", UNLISTED_READS)
def test_a_field_that_a_line_reads_and_its_header_does_not_list_is_refused_with_a_correction(
    origin, change, address, phrases, absent, stage_files
):
    """A block whose line reads a field that its header does not list is
    refused under `signature-complete`, with the header that lists the field
    as the correction: value fields alone on a backward header, every field
    on a forward one."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed(stage_files[origin], change), origin)
    assert (refused.value.rule, refused.value.address) == ("signature-complete", address)
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []
    assert [state for state in absent if state in refused.value.message] == []


@pytest.mark.parametrize(
    "line",
    [
        pytest.param(
            "V        = E_{Ψ,θ}(V[>]) + m_next                   :: [id=value]",
            id="beside the expectation",
        ),
        pytest.param(
            "V = E_{Ψ,θ}(V[>]) ⟂ m_next >= 0       :: [id=value]",
            id="in the bound of a slackness clause",
        ),
    ],
)
def test_a_continuation_state_read_outside_the_expectation_over_its_shocks_is_refused(line):
    """The value line of `port.bl` that reads its continuation state `m_next`
    outside the expectation over Ψ and θ, the shocks of the edge from the
    decision perch to the continuation perch, is refused under
    `shock-observed`."""
    value = "V        = E_{Ψ,θ}(V[>])                            :: [id=value]"
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed(corpus_text("port"), (value, line)), "port.bl")
    assert (refused.value.rule, refused.value.address) == ("shock-observed", "cntn_to_dcsn.value")
    phrases = ["mentions m_next", "E_{Ψ,θ}"]
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []


# the value line of the arrival block of `keeper_cons.bl`, as written and as
# changed to read the continuation state `h_nxt_kp`
KEEPER_ARRIVAL_READ = (
    "V[<]    = V                                        :: [id=value]",
    "V[<]    = V + h_nxt_kp                             :: [id=value]",
)


# the forward block of `keeper_cons.bl` from the arrival perch to the
# decision perch, with the blank line after it
KEEPER_ARRIVAL_TO_DECISION = (
    "[id=arvl_to_dcsn, (w_kp : ℝ₊₊, h_kp : ℝ₊₊, z_kp : ℝ₊₊) : !arvl"
    " -> (w_d : ℝ₊₊, h_d : ℝ₊₊, z_d : ℝ₊₊) : !dcsn] {\n"
    "    w_d = w_kp\n"
    "    h_d = h_kp\n"
    "    z_d = z_kp\n"
    "}\n\n"
)


# the Euler line of the policy block of `keeper_saving.bl`
SAVING_EULER_LINE = "𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ m_d - c >= 0"


# the `!doc` argmax line of the policy block of `keeper_saving.bl` made
# operative, for the two rows whose Euler line becomes an inequality, a line
# that defines no name, even where its left side is one state name
SAVING_ARGMAX_OPERATIVE = (":: [id=optimality, !doc]", ":: [id=optimality]")


# the consumption stage of the fixture folder with a policy block whose first
# line is an inequality on `a[>]`, where `a` is the continuation state of the
# law of motion: a backward inequality is read at the perch of its left side
# only where that side is a candidate of the policy, so this line is read at
# the decision perch
INEQUALITY_ON_THE_CONTINUATION_STATE = (
    ("Γ(x : ℝ₊₊) := (0, x]\n", "Γ(x : ℝ₊₊) := (0, x]\n𝑑𝑢 := D_{c}(𝑢)\n𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)\n"),
    (
        "[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {\n"
        "    c = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>]) :: [id=optimality]\n}",
        "[id=policy, (V[>]) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
        "    a[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]\n"
        "    m_d[>] = a + a[>]                    :: [id=grid]\n"
        "    c      = a[>]                        :: [id=identification]\n}",
    ),
)


# a backward line that reads a state of its input perch or of a later perch
# other than through the law of motion: the file, each change applied to it,
# the address of the refusal, the phrases of its message and phrases that the
# message does not hold; a line with the id `alien` writes another name
# before the value line
LATER_STATE_READS = [
    pytest.param(
        "keeper_cons.bl",
        (("V = 𝑢(c, h_d) + β*V[>]", "V = 𝑢(c, h_nxt_kp) + β*V[>]"),),
        "cntn_to_dcsn.value",
        [
            "mentions h_nxt_kp, a state of the cntn perch",
            "The forward block 'dcsn_to_cntn' defines it",
            "`h_nxt_kp = h_d`",
            "Write `h_d` in its place",
        ],
        [],
        id="the value line",
    ),
    pytest.param(
        "keeper_cons.bl",
        (
            (
                KEEPER_VALUE_LINE,
                "    V[<] = h_nxt_kp                              :: [id=alien]\n"
                + KEEPER_VALUE_LINE,
            ),
        ),
        "cntn_to_dcsn.alien",
        ["mentions h_nxt_kp, a state of the cntn perch", "`h_nxt_kp = h_d`"],
        [],
        id="a line that writes V[<]",
    ),
    pytest.param(
        "keeper_cons.bl",
        (
            (
                KEEPER_VALUE_LINE,
                "    local_a[<] = h_nxt_kp                        :: [id=alien]\n"
                + KEEPER_VALUE_LINE,
            ),
        ),
        "cntn_to_dcsn.alien",
        ["mentions h_nxt_kp, a state of the cntn perch", "`h_nxt_kp = h_d`"],
        [],
        id="a line that writes a local name marked for the arrival perch",
    ),
    pytest.param(
        "keeper_cons.bl",
        (
            (
                KEEPER_VALUE_LINE,
                "    local = h_nxt_kp                             :: [id=alien]\n"
                + KEEPER_VALUE_LINE,
            ),
        ),
        "cntn_to_dcsn.alien",
        ["mentions h_nxt_kp, a state of the cntn perch", "`h_nxt_kp = h_d`"],
        [],
        id="a line that writes a local name",
    ),
    pytest.param(
        "keeper_cons.bl",
        (
            (
                KEEPER_VALUE_LINE,
                "    local[>] = h_nxt_kp                           :: [id=alias]\n"
                "    V    = 𝑢(c, local[>]) + β*V[>]                :: [id=value]",
            ),
        ),
        "cntn_to_dcsn.alias",
        ["`h_nxt_kp = h_d`. Write `h_d` in its place"],
        [],
        id="a local name marked for the continuation perch",
    ),
    pytest.param(
        "keeper_cons.bl",
        (
            (KEEPER_VALUE_HEADER, "() ->"),
            (
                "V = 𝑢(c, h_d) + β*V[>]                             :: [id=value]",
                "V = h_nxt_kp                                       :: [id=value]",
            ),
        ),
        "cntn_to_dcsn.value",
        [
            "no input perch named in the block's header",
            "`h_nxt_kp = h_d`. Write `h_d` in its place",
        ],
        [],
        id="a value header that lists no input",
    ),
    pytest.param(
        "keeper_cons.bl",
        (KEEPER_ARRIVAL_READ,),
        "dcsn_to_arvl.value",
        [
            "a state of the cntn perch, a perch after the one the block reads its inputs at",
            "reached through 'arvl_to_dcsn' then 'dcsn_to_cntn'",
            "The forward block 'dcsn_to_cntn' defines it at keeper_cons.bl:23:5",
            "`h_nxt_kp = h_d`, whose right side is read in turn through the earlier blocks "
            "of the chain",
        ],
        [],
        id="the arrival value line, two perches before the state",
    ),
    pytest.param(
        "keeper_cons.bl",
        ((KEEPER_ARRIVAL_TO_DECISION, ""), KEEPER_ARRIVAL_READ),
        "dcsn_to_arvl.value",
        ["no forward block from arvl to dcsn", "supplies no arvl-perch expression for h_nxt_kp"],
        ["Write `h_d`"],
        id="the arrival value line with no forward block from the arrival perch",
    ),
    pytest.param(
        "keeper_cons.bl",
        (
            ("h_nxt_kp = h_d", "local_h = h_d\n    h_nxt_kp = local_h"),
            ("V = 𝑢(c, h_d) + β*V[>]", "V = 𝑢(c, h_nxt_kp) + β*V[>]"),
        ),
        "cntn_to_dcsn.value",
        ["`h_nxt_kp = local_h`", "Express it using names in scope at the dcsn perch"],
        ["Write `local_h`"],
        id="a law of motion that writes a local name of its forward block",
    ),
    pytest.param(
        "keeper_saving.bl",
        ((SAVING_EULER_LINE, "𝑢_c(c) + y_f_kp = β*D_{y_f_kp}V[>] ⟂ m_d - c >= 0"),),
        "policy.euler_financial",
        ["`y_f_kp = m_d - c`. Write `m_d - c` in its place"],
        [],
        id="the left side of a relation",
    ),
    pytest.param(
        "keeper_saving.bl",
        ((SAVING_EULER_LINE, "𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ y_f_kp >= 0"),),
        "policy.euler_financial",
        ["`y_f_kp = m_d - c`. Write `m_d - c` in its place"],
        [],
        id="the bound of the slackness clause",
    ),
    pytest.param(
        "keeper_saving.bl",
        ((SAVING_EULER_LINE, "𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ 0 <= c <= y_f_kp"),),
        "policy.euler_financial",
        ["`y_f_kp = m_d - c`. Write `m_d - c` in its place"],
        [],
        id="the upper of two bounds of the slackness clause",
    ),
    pytest.param(
        "keeper_saving.bl",
        (SAVING_ARGMAX_OPERATIVE, (SAVING_EULER_LINE, "y_f_kp >= 0")),
        "policy.euler_financial",
        ["`y_f_kp = m_d - c`"],
        [],
        id="an inequality whose left side is the state",
    ),
    pytest.param(
        "keeper_saving.bl",
        (SAVING_ARGMAX_OPERATIVE, (SAVING_EULER_LINE, "y_f_kp + 0 >= 0")),
        "policy.euler_financial",
        ["`y_f_kp = m_d - c`"],
        [],
        id="an inequality whose left side holds the state",
    ),
    pytest.param(
        "cons.bl",
        INEQUALITY_ON_THE_CONTINUATION_STATE,
        "policy.InvEuler",
        ["`a = m_d - c`"],
        [],
        id="an inequality whose left side is the continuation state a[>]",
    ),
]


@pytest.mark.parametrize("origin, changes, address, phrases, absent", LATER_STATE_READS)
def test_a_backward_line_that_reads_a_later_state_directly_is_refused_under_input_perch_state(
    origin, changes, address, phrases, absent, stage_files
):
    """A backward line that reads a state of its input perch, or of a later
    perch, other than through the law of motion is refused under
    `input-perch-state`, with a message that quotes the law where the stage
    writes one."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed(stage_files[origin], *changes), origin)
    assert (refused.value.rule, refused.value.address) == ("input-perch-state", address)
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []
    assert [phrase for phrase in absent if phrase in refused.value.message] == []


# two lines written before the Euler line of `keeper_saving.bl`: the
# candidate of the control and the grid of the decision state, each a
# continuation-marked name that a later line reads
SAVING_CANDIDATE_LINES = (
    "    c[>] = 𝑢_c(y_f_kp)                           :: [id=candidate]\n"
    "    m_d[>] = y_f_kp + c[>]                       :: [id=grid]\n"
)


# a line that writes the continuation state `y_f_kp` of `keeper_saving.bl` as
# if it were a candidate, and the Euler line that reads it, in place of the
# Euler line
SAVING_STATE_AS_A_CANDIDATE = (
    "    y_f_kp[>] = y_f_kp[>]                 :: [id=fake_candidate]\n"
    "    𝑢_c(c) = β*D_{y_f_kp}V[>] ⟂ y_f_kp[>] >= 0"
)


def test_a_policy_line_may_read_a_candidate_of_its_block_and_not_a_state_written_as_one(
    stage_files, read_only_stage_from_file
):
    """A policy line may read a continuation-marked candidate that a line of
    its block defines, in `keeper_saving.bl` with two candidate lines and in
    `worker_cons.bl` with its methods file, while a continuation state that a
    policy line writes as a candidate is refused under `input-perch-state`."""
    euler = "    " + SAVING_EULER_LINE
    saving = stage_files["keeper_saving.bl"]
    candidates = changed(saving, (euler, SAVING_CANDIDATE_LINES + euler))
    assert stage_from_text(candidates, "keeper_saving.bl").name == "keeper_saving"
    # the policy block of the methods file defines the candidates c[>], w[>]
    # and v[>], and its last line, `c = upper_env(w[>], c[>], v[>])`, reads
    # them
    worker = methodized_copy(
        read_only_stage_from_file(ROOT / WORKER_CONS_FILE), WORKER_CONS_METHODS
    )
    assert worker.name == "worker_cons"
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed(saving, (euler, SAVING_STATE_AS_A_CANDIDATE)), "keeper_saving.bl")
    assert (refused.value.rule, refused.value.address) == (
        "input-perch-state",
        "policy.fake_candidate",
    )
    assert "`y_f_kp = m_d - c`. Write `m_d - c` in its place" in refused.value.message


def test_a_value_line_that_names_a_state_of_two_perches_by_its_bare_name_is_refused(stage_files):
    """The value line of the discounting stage that mentions `a`, the bare
    name of a state at its arrival perch and at its continuation perch, is
    refused under `name-in-scope` with the two marks that choose between
    them."""
    value = "V  = β*V[>]                     :: [id=value]"
    mentioning = changed(
        stage_files["disc.bl"], (value, "V  = a + β*V[>]                 :: [id=value]")
    )
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(mentioning, "disc.bl")
    assert (refused.value.rule, refused.value.address) == ("name-in-scope", "cntn_to_dcsn.value")
    phrases = [
        "mentions a, a state the stage places at 2 perches, arvl and cntn",
        "Write `a[<]` for the arvl state, `a[>]` for the cntn state",
    ]
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []


def test_the_printed_backward_blocks_and_directions_of_keeper_cons_list_no_state(keeper_cons):
    """The backward and policy directions that the sheet of the backward
    initial diagram of `keeper_cons.bl` prints, and the lines of the backward
    blocks of the printed stage, list values and the control alone."""
    assert inventory.directions(keeper_cons, "backward") == (
        "backward   ≺ V≺  ←  ∼ V  ←  ≻ V≻",
        "policy     ∼ c  ←  ≻ V≻",
    )
    blocks = [line for line in str(keeper_cons).splitlines() if line.strip().startswith("← ")]
    assert [flat(line) for line in blocks] == [
        flat("← cntn_to_dcsn   (V≻) : !cntn, at c -> (V) : !dcsn"),
        flat("← dcsn_to_arvl   (V) : !dcsn -> (V≺) : !arvl"),
        flat("← policy         (V≻) : !cntn -> (c) : !dcsn"),
    ]
    assert not any("h_d" in line for line in blocks)


def test_a_documentary_line_of_a_value_block_reads_a_decision_state_and_adds_no_wire(cons_obs):
    """The value block of `cons_obs.bl` with the `!doc` line `V = 𝑢(m_d)`,
    which reads the decision state `m_d` without listing it, elaborates with
    the signature of the value builder of the file as written."""
    # a state of the perch at which the output of a backward block stands is
    # a coordinate of the output and needs no listing, on a `!doc` line as on
    # an operative one
    value_line = "    V        = 𝑢(c) + V[>]          :: [id=value]\n"
    with_doc = value_line + "    V  = 𝑢(m_d)                     :: [id=note, !doc]\n"
    noted = stage_from_text(
        changed(corpus_text("cons_obs"), (value_line, with_doc)), "cons_obs.bl"
    )
    assert str(noted.builder["cntn", "dcsn"].signature()) == str(
        cons_obs.builder["cntn", "dcsn"].signature()
    )
