"""Shocks in expectations: conditioning, joint laws and their factorization,
the rows of a Markov matrix, and the edge that draws each shock."""

from operator import attrgetter

import pytest
from application_files import COPIED_FILES_FOLDER, ROOT
from stage_builders import stage_from_text
from stage_texts import (
    CONS_RISKY_ASSET_PORT_TEXT,
    TWO_PARENT_SHOCKS_TEXT,
    Y_IDENTITY,
    changed,
    two_nodes_text_with_changes,
    two_nodes_text_with_joint_normal_law,
)

from bellman.refusals import ConstructionError
from bellman.stage.kernels import compile_kernel, kernel
from bellman.syntax import terms
from bellman.typing import typed_expressions

# --- a forward builder that lists one shock of a joint law ---


@pytest.fixture(scope="module")
def stage_listing_one_shock_of_a_joint_law():
    """The two-node stage with the joint law `(y, z) ~ N(…)`, whose forward
    builder lists `y` alone among its inputs."""
    text = two_nodes_text_with_changes(
        transition="    a = y\n",
        declarations="z : ℝ\nr : [-1,1]\n(y, z) ~ N((0,0),((1,r),(r,1)))\n",
        backward="    V = E_{y,z}(V[>]) :: [id=value]\n",
    )
    listed = (
        "(k_d, c : !ctrl @ [0,1], y, z) : !dcsn",
        "(k_d, c : !ctrl @ [0,1], y) : !dcsn",
    )
    return stage_from_text(changed(text, listed), "one_listed.bl")


def test_the_fields_of_a_stage_hold_both_shocks_of_a_joint_law_drawn_on_the_edge_that_lists_one(
    stage_listing_one_shock_of_a_joint_law,
):
    """Where a forward builder lists one shock of a joint law, the fields of
    the stage hold both shocks, each drawn on the edge of that builder."""
    fields = stage_listing_one_shock_of_a_joint_law.fields()
    assert [identity.field for identity, sort in fields.items() if sort.role == "shock"] == [
        "y",
        "z",
    ]
    assert {identity.field: edge for identity, edge in fields.edges.items()} == {
        "y": ("dcsn", "cntn"),
        "z": ("dcsn", "cntn"),
    }


def test_the_printed_stage_says_both_shocks_of_a_joint_law_are_drawn_where_one_is_listed(
    stage_listing_one_shock_of_a_joint_law,
):
    """Where a forward builder lists one shock of a joint law, the printed
    stage says that both shocks are drawn after the decision, before the
    continuation."""
    printed = str(stage_listing_one_shock_of_a_joint_law)
    assert "y, z drawn after decision, before continuation" in printed


# --- a law that reads a parent shock and a state through an indexed tuple ---


@pytest.fixture(scope="module")
def indexed_law_stage():
    """The stage of `TWO_PARENT_SHOCKS_TEXT`, whose law of θ reads the shock η
    directly and the two-point state s through the tuple `(σ, 0)[s]` indexed by
    s."""
    return stage_from_text(TWO_PARENT_SHOCKS_TEXT)


@pytest.fixture(scope="module")
def indexed_law_expectation(indexed_law_stage):
    """The record that the expectation of the arrival value of that stage
    denotes."""
    return indexed_law_stage.builder.bwd["dcsn_to_arvl", "value:Expectation:1"].denote()


def test_a_law_denotes_a_kernel_reading_its_parent_shock_by_name_and_a_state_by_an_indexed_tuple(
    indexed_law_stage,
):
    """The definition of the law of θ denotes a stochastic kernel given η and
    s, whose LogNormal law reads η by its own variable and s through the tuple
    indexed by s."""
    conditional = indexed_law_stage.definitions.denote(
        "key_selection_reads:distribution:θ"
    ).denoted[0]
    assert conditional.symbol == "P_{θ|η, s}"
    assert isinstance(conditional.mathematical_type.carrier, typed_expressions.StochasticKernelSet)
    assert isinstance(conditional.expression, typed_expressions.Lambda)
    law = conditional.expression.body
    assert (
        isinstance(law, typed_expressions.Apply)
        and typed_expressions.format_expression(law.function) == "LogNormal"
    )
    eta, scale = law.args
    assert isinstance(eta, terms.Sym) and typed_expressions.variable_identity(eta).field == "η"
    assert (
        isinstance(scale, terms.Select)
        and isinstance(scale.sel, terms.Key)
        and scale.sel.at == "s"
    )


def test_the_input_of_an_expectation_is_the_value_composed_with_the_law_of_motion(
    indexed_law_expectation,
):
    """The input of the expectation of the arrival value is the value composed
    with the law of motion, 𝑉∘𝑔, a measurable map."""
    assert indexed_law_expectation.inputs[0].name == "𝑉∘𝑔"
    assert isinstance(
        indexed_law_expectation.inputs[0].mathematical_type.carrier,
        typed_expressions.MeasurableMapSet,
    )


def test_the_kernel_of_an_expectation_denotes_each_law_it_integrates_as_the_law_s_definition_does(
    indexed_law_expectation,
):
    """The kernel of the expectation of the arrival value denotes the laws of
    s, η and θ, the law of θ reading η by name and s through the tuple
    indexed by s, as the law's own definition does."""
    laws = {str(item.identity): item for item in indexed_law_expectation.kernel.denoted}
    assert set(laws) == {
        "key_selection_reads:distribution:s",
        "key_selection_reads:distribution:η",
        "key_selection_reads:distribution:θ",
    }
    theta = laws["key_selection_reads:distribution:θ"]
    assert isinstance(theta.expression, typed_expressions.Lambda)
    conditional_call = theta.expression.body
    assert isinstance(conditional_call, typed_expressions.Apply)
    assert typed_expressions.format_expression(conditional_call.function) == "LogNormal"
    assert typed_expressions.format_expression(conditional_call.args[0]) == "η"
    scale = conditional_call.args[1]
    assert (
        isinstance(scale, terms.Select)
        and isinstance(scale.sel, terms.Key)
        and scale.sel.at == "s"
    )


def test_an_expectation_binds_one_variable_for_each_shock_under_the_shock_s_name(
    indexed_law_expectation,
):
    """The output of the expectation of the arrival value is `E_{s, θ, η}[…]`,
    one bound variable for each of the three shocks, named by its field."""
    output = indexed_law_expectation.outputs[0].expression
    assert isinstance(output, typed_expressions.Lambda) and isinstance(output.body, terms.Operator)
    assert output.body.head == "E"
    assert {typed_expressions.variable_identity(sub.name).field for sub in output.body.subs} == {
        "s",
        "θ",
        "η",
    }


def test_an_integrand_evaluates_the_value_at_the_law_of_motion_of_the_state_and_shocks_by_name(
    indexed_law_expectation,
):
    """The integrand of the expectation of the arrival value evaluates the
    value at the law of motion of the tuple `(k, s, θ)`, the state and two
    shocks named by their fields, with no component of a joint variable."""
    value = indexed_law_expectation.outputs[0].expression.body.args[0]
    assert isinstance(value, typed_expressions.Apply) and isinstance(
        value.args[0], typed_expressions.Apply
    )
    point = value.args[0].args[0]
    assert isinstance(point, terms.Tuple)
    assert [typed_expressions.variable_identity(item).field for item in point.items] == [
        "k",
        "s",
        "θ",
    ]


def test_the_law_of_motion_takes_the_entry_of_a_tuple_indexed_by_a_state_at_the_state_s_value():
    """The compiled law of motion `m = R*k + (1, 2)[s]*θ` takes the first
    entry of the tuple where s is `lo` and the second where s is `hi`."""
    calibrated = stage_from_text(TWO_PARENT_SHOCKS_TEXT).calibrate(
        {"β": 0.9, "γ": 2, "R": 1, "P": 0.3, "σ": 0.5}
    )
    law_of_motion = compile_kernel(calibrated, "arvl_to_dcsn:Pushforward")
    values = kernel(calibrated, "arvl_to_dcsn:Pushforward").parameter_values
    # the arguments are (k, s, θ) and then the parameter R = 1: with k = 2 and
    # θ = 3, m = 1*2 + 1*3 = 5 at s = lo and m = 1*2 + 2*3 = 8 at s = hi
    assert (
        law_of_motion(2.0, "lo", 3.0, *values),
        law_of_motion(2.0, "hi", 3.0, *values),
    ) == (5, 8)


# --- an expectation written in an alias of the policy builder ---

# the first-order condition of the portfolio stage `port`, whose expectation
# the stages below write in the alias `q`
FIRST_ORDER_CONDITION = "    ς = solve_{ς}(E_{φ}((φ - R)*w_d*D_{k_next}V[>]))  :: [id=foc]"

# the alias `q`, the residual of the first-order condition
RESIDUAL_ALIAS = "    q = E_{φ}((φ - R)*w_d*D_{k_next}V[>])          :: [id=residual]\n"

# the values of the parameters that the policy builder of `port` reads
PORT_CALIBRATION = {"R": 1.03, "φ_mean": 1.08, "σ_φ": 0.2}


def port_with_the_residual_alias(solve_line):
    """The calibrated stage `port` with its first-order condition written as
    the alias `q` followed by `solve_line`."""
    text = changed(
        CONS_RISKY_ASSET_PORT_TEXT, (FIRST_ORDER_CONDITION, RESIDUAL_ALIAS + solve_line)
    )
    return stage_from_text(text).calibrate(PORT_CALIBRATION)


@pytest.fixture(scope="module")
def residual_alias_port():
    """The calibrated stage `port` whose policy builder solves
    `ς = solve_{ς}(q)` for the alias `q`."""
    return port_with_the_residual_alias("    ς = solve_{ς}(q)   :: [id=foc]")


@pytest.fixture(scope="module")
def residual_aggregation(residual_alias_port):
    """The record that the aggregation of the integrand of the alias `q`
    denotes."""
    return residual_alias_port.builder.bwd["policy", "residual:Aggregation:1"].denote()


@pytest.fixture(scope="module")
def residual_expectation(residual_alias_port):
    """The record that the expectation of the alias `q` denotes."""
    return residual_alias_port.builder.bwd["policy", "residual:Expectation:1"].denote()


def test_an_expectation_in_an_alias_is_a_piece_of_its_own_reading_the_aggregation_of_its_integrand(
    residual_alias_port, residual_aggregation, residual_expectation
):
    """The expectation of the alias `q`, a piece of its own on the alias's
    occurrence with no piece of the policy builder merged from it, reads the
    result of the aggregation of the alias's integrand."""
    assert residual_expectation.inputs[0].identity == residual_aggregation.outputs[0].identity
    assert "policy:Expectation" not in list(residual_alias_port.builder.bwd.primitives.list())
    assert [str(wire.identity) for wire in residual_expectation.inputs] == [
        "policy.residual:Aggregation:1:result"
    ]
    assert [str(wire.identity) for wire in residual_expectation.outputs] == [
        "policy.residual:Expectation:1:result"
    ]


def test_the_kernel_of_an_expectation_in_an_alias_denotes_the_declared_law_of_its_shock(
    residual_expectation,
):
    """The kernel of the expectation of the alias `q` is the shock probability
    distribution `P_φ`, which denotes the law of φ by the fields of its
    identity, a probability measure."""
    assert residual_expectation.kernel.kind == "shock probability distribution"
    assert residual_expectation.kernel.symbol == "P_φ"
    [law] = residual_expectation.kernel.denoted
    assert (law.identity.kind, law.identity.subjects) == ("distribution", ("φ",))
    assert isinstance(law.mathematical_type.carrier, typed_expressions.ProbabilityMeasureSet)


def test_the_printed_expectation_of_an_alias_writes_its_operand_directly_after_its_head(
    residual_expectation,
):
    """The printed output of the expectation of the alias `q` begins
    `(w_d, ς) ↦ E_{φ}[`, its operand directly after its head."""
    printed = typed_expressions.format_expression(
        residual_expectation.outputs[0].expression, width=None
    )
    assert printed.startswith("(w_d, ς) ↦ E_{φ}[")


def test_the_aggregation_of_the_integrand_of_an_alias_reads_the_shock_and_the_state_by_name(
    residual_aggregation,
):
    """The output of the aggregation of the integrand of `q` is
    `(φ − R) · w_d · D_{k_next}V[>](…)`, which reads φ and w_d by their
    names."""
    formula = residual_aggregation.outputs[0].expression.body
    assert isinstance(formula, terms.Mul) and isinstance(formula.left, terms.Mul)
    assert isinstance(formula.left.left, terms.Sub)
    assert typed_expressions.variable_identity(formula.left.left.left).field == "φ"
    assert typed_expressions.variable_identity(formula.left.right).field == "w_d"


def test_the_compiled_aggregation_of_the_integrand_of_an_alias_evaluates_the_integrand(
    residual_alias_port,
):
    """The compiled aggregation of the integrand of `q` gives
    `(φ − R) · w_d · D_{k_next}V[>]` at a point."""
    residual = kernel(residual_alias_port, "policy.residual:Aggregation:1").parameter_values
    integrand = compile_kernel(residual_alias_port, "policy.residual:Aggregation:1")
    # the arguments are (V≻, w_d, ς, φ, D_{k_next}(V≻)) and then the parameter
    # R = 1.03: (1.2 - 1.03) * 2 * 4 = 1.36
    assert integrand(0.0, 2.0, 0.3, 1.2, 4.0, *residual) == pytest.approx(1.36)


@pytest.fixture(scope="module")
def solve_reading_the_alias_twice():
    """The record that the aggregation of `ς = solve_{ς}(q + q)` denotes, on
    the calibrated stage `port` with the alias `q`."""
    stage = port_with_the_residual_alias("    ς = solve_{ς}(q + q)   :: [id=foc]")
    return stage.builder.bwd["policy", "foc:Aggregation"].denote()


def test_two_reads_of_an_alias_share_its_one_expectation(solve_reading_the_alias_twice):
    """The solve `ς = solve_{ς}(q + q)` reads one expectation of `q`, whose
    term its residual adds to itself."""
    assert [str(wire.identity) for wire in solve_reading_the_alias_twice.inputs] == [
        "policy.residual:Expectation:1:result"
    ]
    residual_line, _ = solve_reading_the_alias_twice.outputs[0].rules
    shared_formula = residual_line.statement.right
    assert isinstance(shared_formula, terms.Add)
    assert shared_formula.left == shared_formula.right


def test_the_aggregation_of_a_solve_denotes_the_set_of_policies_at_which_its_residual_vanishes(
    solve_reading_the_alias_twice,
):
    """The aggregation of a solve denotes the set of policies at which its
    residual vanishes, written as the residual line `r₁ = …` followed by the
    head `ς = solve_{ς}(r₁)`."""
    assert isinstance(solve_reading_the_alias_twice.expression.body, terms.Comprehension)
    _, head = solve_reading_the_alias_twice.outputs[0].rules
    assert typed_expressions.format_expression(head.statement, width=None) == "ς = solve_{ς}(r₁)"


def test_an_expectation_written_again_beside_an_alias_is_a_second_expectation():
    """The solve `ς = solve_{ς}(q - E_{φ}(…))`, whose second term writes the
    integrand of `q` again, reads two expectations, whose two different terms
    its residual subtracts."""
    stage = port_with_the_residual_alias(
        "    ς = solve_{ς}(q - E_{φ}((φ - R)*w_d*D_{k_next}V[>]))   :: [id=foc]"
    )
    twice_aggregation = stage.builder.bwd["policy", "foc:Aggregation"].denote()
    assert [str(wire.identity) for wire in twice_aggregation.inputs] == [
        "policy.residual:Expectation:1:result",
        "policy.foc:Expectation:1:result",
    ]
    twice_formula = twice_aggregation.outputs[0].rules[0].statement.right
    assert isinstance(twice_formula, terms.Sub)
    assert twice_formula.left != twice_formula.right


# --- a law that reads a row of a matrix ---


@pytest.fixture(scope="module")
def hafiscal_stage():
    """The stage of the copied HAFiscal stage file, whose employment state z
    is drawn from the row of a matrix that the previous state `z_prev`
    selects."""
    path = ROOT / COPIED_FILES_FOLDER / "HAFiscal/HAFiscal.bl"
    return stage_from_text(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "graph",
    [
        pytest.param("initial.backward.graph", id="backward-initial-diagram"),
        pytest.param("builder.bwd.graph", id="backward-builders-graph"),
    ],
)
def test_the_backward_graphs_of_a_stage_whose_laws_read_rows_of_matrices_keep_each_row_s_state(
    hafiscal_stage, graph
):
    """With a backward graph of the HAFiscal stage constructed, the printed
    kernel of the expectation of its arrival value writes the row of the law
    of z that `z_prev` selects and the rows of the laws of ψ and ξ that z
    selects."""
    attrgetter(graph)(hafiscal_stage)
    expectation = hafiscal_stage.builder.bwd.primitives["dcsn_to_arvl.value:Expectation:1"]
    assert str(expectation.kernel()).splitlines()[0] == (
        "distribution of (z, ψ, ξ): "
        "z ~ Categorical(((1 - π_eu, π_eu, 0, 0), (π_ue, 0, 1 - π_ue, 0), "
        "(π_ue, 0, 0, 1 - π_ue), (π_ue, 0, 0, 1 - π_ue))[z_prev]) · "
        "ψ | z ~ LogNormal(-(σ_ψ, 0, 0, 0)[z]^2/2, (σ_ψ, 0, 0, 0)[z]) · "
        "ξ | z ~ LogNormal(-(σ_ξ, 0, 0, 0)[z]^2/2, (σ_ξ, 0, 0, 0)[z])"
    )


def test_the_forward_measure_of_a_stage_is_extended_by_a_categorical_law_of_its_employment_state(
    hafiscal_stage,
):
    """The printed kernel of the extension of the forward measure by the
    employment state z of the HAFiscal stage names the Categorical law."""
    extension = hafiscal_stage.builder.fwd.primitives["arvl_to_dcsn:DistributionExtension:z"]
    assert "Categorical" in str(extension.kernel())


# --- Markov laws and a Bernoulli law ---


@pytest.mark.parametrize(
    ("path", "identity", "expected"),
    [
        pytest.param(
            f"{COPIED_FILES_FOLDER}/ma-stachurski-toda-2020/cons.bl",
            "cons:distribution:z",
            "Z → probability measure on Z",
            id="discrete-markov-law-whose-two-sets-are-one",
        ),
        pytest.param(
            f"{COPIED_FILES_FOLDER}/benhabib-bisin-zhu-2011/generation.bl",
            "generation:distribution:z_q",
            "Rstate → probability measure on Rstate × Ystate",
            id="markov-chain-of-a-pair-whose-two-sets-differ",
        ),
        pytest.param(
            f"{COPIED_FILES_FOLDER}/bloom-2009/unit.bl",
            "unit:distribution:s",
            "Sigma → probability measure on Sigma",
            id="row-of-a-two-state-chain-whose-two-sets-are-one",
        ),
    ],
)
def test_a_markov_law_given_the_preceding_state_is_a_kernel_from_the_set_of_that_state(
    path, identity, expected
):
    """The law of a Markov state given its preceding state has the type of a
    map from the set of the preceding state to probability measures on the
    set of its subjects; the row whose two sets differ tells them apart."""
    stage = stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)
    [distribution] = stage.definitions.denote(identity).denoted
    assert str(distribution.mathematical_type) == expected


def test_a_bernoulli_law_with_a_compound_probability_owes_one_condition_on_its_two_weights():
    """The law `y ~ Bernoulli(1 - χ)` owes one condition that its weights form
    a probability vector, which gives the value 1 the weight `1 - χ` and the
    value 0 the weight `1 - (1 - χ)`."""
    stage = stage_from_text(
        two_nodes_text_with_changes(
            declarations="χ : [0,1]\ny ~ Bernoulli(1 - χ)\nz : ℝ\nz ~ N(0,1)\n"
        )
    )
    weights = [
        item.explanation
        for item in stage.obligations()
        if item.condition == "distribution-weights-are-a-probability-vector"
    ]
    assert len(weights) == 1
    assert (
        "gives its subject the value 1 with probability 1 - χ and the value 0 with probability "
        "1 - (1 - χ)"
    ) in weights[0]


# --- the paths on which an expectation integrates the shocks of its edge ---


def test_a_shock_stays_an_argument_through_a_sibling_input_until_an_expectation_integrates_it():
    """Where one input of a sum is `E_{y}(V[>])` and its sibling input is
    `V[>]`, the expectation of the sum over y and z integrates both shocks,
    since y reaches the sum through the sibling input."""
    joined = stage_from_text(
        two_nodes_text_with_changes(
            backward="    W1 = E_{y}(V[>])\n    W2 = V[>]\n"
            "    V = E_{y,z}(W1 + W2) :: [id=value]\n"
        )
    )
    expectation = joined.builder.bwd.primitives["cntn_to_dcsn.value:Expectation:1"]
    assert str(expectation.kernel()).splitlines()[:2] == [
        "distribution of (y, z): y ~ N(0, 1) · z ~ N(0, 1)",
        "conditioned on none declared; drawn on the edge dcsn_to_cntn; "
        "in cntn_to_dcsn at each point of k_d, integrates y, z; "
        "declared at two_nodes:distribution:y, two_nodes:distribution:z",
    ]


def test_a_term_whose_path_integrates_some_shocks_may_read_a_constant_but_not_a_shock():
    """Beside `E_{y,z}(V[>])`, a term `E_{y}(1)` is accepted, its aggregation
    being the constant 1, while a term `E_{z}(z)` is refused under
    `shock-observed`, since its path integrates z and not y."""
    constant = stage_from_text(
        two_nodes_text_with_changes(backward="    V = E_{y,z}(V[>]) + E_{y}(1) :: [id=value]\n")
    )
    aggregation = constant.builder.bwd.primitives["cntn_to_dcsn.value:Aggregation:2"]
    assert str(aggregation.kernel()).splitlines() == [
        "𝐺 of cntn_to_dcsn, segment cntn_to_dcsn.value:Aggregation:2: 𝐺(V≻, k_d, c) = 1",
        "output 1; unused V≻, k_d, c",
    ]
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            two_nodes_text_with_changes(
                backward="    V = E_{y,z}(V[>]) + E_{z}(z) :: [id=value]\n",
                header="(V[>] : ℝ @ !vlu, z) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
            )
        )
    assert (refused.value.rule, refused.value.address) == ("shock-observed", "cntn_to_dcsn.value")
    assert (
        "from the shock z read in cntn_to_dcsn.value by a path that integrates z and not y"
        in refused.value.message
    )


# --- the factorization of the joint law of an edge ---


def test_a_factorization_states_the_independence_of_separate_laws_and_none_in_a_hierarchy(
    two_nodes_stage,
):
    """The factorization condition of an edge states the product of the
    declared conditional laws, with the conditional independence of laws that
    condition on no other shock, and with no independence of the children of
    one parent shock."""
    [factorization] = [
        item
        for item in two_nodes_stage.obligations()
        if item.condition == "joint-distribution-factorization"
    ]
    assert factorization.entries == (
        Y_IDENTITY,
        "two_nodes:distribution:z",
        "dcsn_to_cntn",
    )
    assert factorization.explanation == (
        "The joint distribution for dcsn_to_cntn is assumed to be the product of the declared "
        "conditional distributions given their named parents and the source coordinates: "
        "y given (k_d, c) by "
        "two_nodes:distribution:y; z given (k_d, c) by two_nodes:distribution:z; "
        "y and z are conditionally independent given (k_d, c)."
    )
    text = two_nodes_text_with_changes(
        declarations="y ~ N(0,1)\nz : ℝ\nz ~ N(y,1)\nw : ℝ\nw ~ N(y,1)\n",
        transition="    a = k_d*(c*z + (1-c)*R) + w\n",
        backward="    V = E_{y,z,w}(V[>]) :: [id=value]\n",
    )
    text = changed(
        text,
        ("(k_d, c : !ctrl @ [0,1], y, z) : !dcsn", "(k_d, c : !ctrl @ [0,1], z, w) : !dcsn"),
        (
            "E_{y,z}(β*V[>]) + E_{y,z}(β*V[>])) :: [id=objective]",
            "E_{y,z,w}(β*V[>]) + E_{y,z,w}(β*V[>])) :: [id=objective]",
        ),
    )
    [factorization] = [
        item
        for item in stage_from_text(text).obligations()
        if item.condition == "joint-distribution-factorization"
    ]
    assert factorization.explanation.endswith(
        "y given (k_d, c) by two_nodes:distribution:y; "
        "z given y and (k_d, c) by two_nodes:distribution:z; "
        "w given y and (k_d, c) by two_nodes:distribution:w."
    )


def test_the_printed_kernel_of_an_expectation_over_separate_laws_writes_their_product(
    two_nodes_stage,
):
    """The printed kernel of an expectation over the shocks y and z, whose laws
    are separate, writes the joint law as the product of the two laws."""
    assert kernel(two_nodes_stage, "cntn_to_dcsn.first:Expectation:1").splitlines()[0] == (
        "distribution of (y, z): y ~ N(0, 1) · z ~ N(0, 1)"
    )


# --- the conditional and the marginal laws of a joint normal law ---


@pytest.fixture(scope="module")
def nested_joint_normal():
    """The joint-normal stage, `(y, z) ~ N((0,0),((1,r),(r,1)))` with the
    decision value `E_{z}(E_{y}(V[>]))`, calibrated at r = 0.5."""
    return stage_from_text(two_nodes_text_with_joint_normal_law()).calibrate(
        {"β": 0.96, "R": 1.03, "r": 0.5}
    )


@pytest.mark.parametrize(
    ("box", "lines"),
    [
        pytest.param(
            "cntn_to_dcsn.value:Expectation:2",
            [
                "distribution of y: y | z ~ N(r*z, 1 - r*r)",
                "conditioned on z; drawn on the edge dcsn_to_cntn; "
                "in cntn_to_dcsn at each point of (k_d, z), integrates y; "
                "declared at two_nodes:distribution:y_z",
                # at r = 0.5, with unit variances: r/1 = 0.5, 1 - r*r/1 = 0.75
                "at the calibration: y | z ~ N(0.5*z, 0.75)",
            ],
            id="inner-expectation-integrates-the-conditional-law",
        ),
        pytest.param(
            "cntn_to_dcsn.value:Expectation:1",
            [
                "distribution of z: z ~ N(0, 1)",
                "conditioned on none declared; drawn on the edge dcsn_to_cntn; "
                "in cntn_to_dcsn at each point of k_d, integrates z; "
                "declared at two_nodes:distribution:y_z",
                "at the calibration: z ~ N(0.0, 1.0)",
            ],
            id="outer-expectation-integrates-the-marginal-law",
        ),
    ],
)
def test_nested_expectations_of_a_joint_normal_law_integrate_a_conditional_inside_a_marginal(
    nested_joint_normal, box, lines
):
    """Each of the two nested expectations of `E_{z}(E_{y}(V[>]))` prints the
    law it integrates: the law of y given z inside, the marginal law of z
    outside."""
    assert kernel(nested_joint_normal, box).splitlines() == lines


def test_an_expectation_over_both_shocks_of_a_joint_normal_law_integrates_the_joint_law():
    """The printed kernel of `E_{y,z}(V[>])` over the shocks of one joint
    normal law writes that joint law."""
    joint = stage_from_text(
        two_nodes_text_with_joint_normal_law(backward="    V = E_{y,z}(V[>]) :: [id=value]\n")
    )
    assert kernel(joint, "cntn_to_dcsn.value:Expectation:1").splitlines()[0] == (
        "distribution of (y, z): (y, z) ~ N((0, 0), ((1, r), (r, 1)))"
    )


def test_a_joint_normal_covariance_is_admitted_where_singular_and_refused_where_not_semidefinite():
    """A joint normal law is admitted with a zero conditional variance or a
    singular joint covariance, and refused at the calibration, at the line of
    its declaration, where its covariance is not positive semidefinite."""
    # r = 1 gives the conditional law of y given z the variance 1 - 1*1 = 0
    one = stage_from_text(two_nodes_text_with_joint_normal_law()).calibrate(
        {"β": 0.96, "R": 1.03, "r": 1.0}
    )
    assert kernel(one, "cntn_to_dcsn.value:Expectation:2").splitlines()[2] == (
        "at the calibration: y | z ~ N(1.0*z, 0.0)"
    )
    # a singular joint covariance, integrated with no conditioning, elaborates
    stage_from_text(
        two_nodes_text_with_joint_normal_law(
            covariance="((1,0),(0,0))", backward="    V = E_{y,z}(V[>]) :: [id=value]\n"
        )
    )
    # r = 2 gives the covariance ((1, 2), (2, 1)), whose determinant is -3; the
    # law `(y, z) ~ N(…)` is the seventh line of the stage text
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes_text_with_joint_normal_law(r_set="ℝ")).calibrate(
            {"β": 0.96, "R": 1.03, "r": 2.0}
        )
    assert (refused.value.rule, refused.value.address) == ("distribution-domain", "t.bl:7")
    assert "not positive semidefinite" in refused.value.message


# --- the edge that draws the shocks, and refusals ---


@pytest.mark.parametrize(
    ("stage_name", "box", "line"),
    [
        pytest.param(
            "port",
            "cntn_to_dcsn.value:Expectation:1",
            "conditioned on none declared; drawn on the edge dcsn_to_cntn; "
            "in cntn_to_dcsn at each point of k_d, integrates Ψ, θ; "
            "declared at port:distribution:Ψ_θ",
            id="decision-builder-of-port",
        ),
        pytest.param(
            "port",
            "policy.foc:Expectation:1",
            "conditioned on none declared; drawn on the edge dcsn_to_cntn; "
            "in policy at each point of (k_d, ς), integrates Ψ, θ; "
            "declared at port:distribution:Ψ_θ",
            id="policy-builder-of-port",
        ),
        pytest.param(
            "tenure",
            "dcsn_to_arvl.value:Expectation:1",
            "conditioned on none declared; drawn on the edge arvl_to_dcsn; "
            "in dcsn_to_arvl at each point of (a, h, z), integrates ε; "
            "declared at tenure:distribution:ε",
            id="shock-of-the-arrival-edge-of-tenure",
        ),
    ],
)
def test_the_printed_kernel_of_an_expectation_names_the_edge_that_draws_its_shocks(
    request, stage_name, box, line
):
    """The second line of the printed kernel of an expectation names the edge
    of the forward builder that lists the shocks, and names the builder that
    integrates them after the word `in`."""
    stage = request.getfixturevalue(stage_name)
    assert str(stage.builder.bwd.primitives[box].kernel()).splitlines()[1] == line


def test_a_shock_that_bears_the_name_of_a_named_space_is_refused_with_the_line_of_the_space():
    """A shock declared by its law alone under the name of a named space is
    refused under `one-name-one-meaning`, by a message that names the space and
    the line of its definition."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            "@stage: t\nZ := ℝ₊₊\nZ ~ N(0, 1)\n"
            "[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n"
        )
    assert refused.value.rule == "one-name-one-meaning"
    phrases = ("'Z' is a shock", "named space", "t.bl:2")
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []


def test_the_reversed_order_of_the_expectations_is_refused_naming_the_undeclared_conditional(
    corpus_path,
):
    """Where `sa_savings.bl` integrates ν first and Ψ after it, the reverse of
    its written order, the stage is refused under `conditional-not-declared`,
    naming the law of ν given Ψ, which it does not declare."""
    text = corpus_path("sa_savings").read_text(encoding="utf-8")
    reversed_order = text.replace(
        "CE = E_{Ψ}(V[>]^(1-γ))^(1/(1-γ))", "CE = E_{ν}(V[>]^(1-γ))^(1/(1-γ))"
    ).replace("AMB = E_{ν}(CE^(1-η))^(1/(1-η))", "AMB = E_{Ψ}(CE^(1-η))^(1/(1-η))")
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(reversed_order)
    error = refused.value
    assert (error.rule, error.address) == ("conditional-not-declared", "cntn_to_dcsn.risk_ce")
    assert (
        "the expectation over ν on line cntn_to_dcsn.risk_ce needs the distribution of ν given Ψ"
        in error.message
    )
