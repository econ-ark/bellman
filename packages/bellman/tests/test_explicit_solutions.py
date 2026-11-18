"""Explicit solutions written in a methods file: the method type `!explicit`,
the kernels its lines compile, the closed form it generates at the
Evaluation, the refusals of what is no explicit solution, and the derived
parameters of the perfect-foresight stage."""

import math
from types import SimpleNamespace

import numpy as np
import pytest
from application_files import (
    CONS_PORT,
    CORPUS,
    PERFECT_FORESIGHT_CALIBRATION,
    PERFECT_FORESIGHT_FILE,
    PERFECT_FORESIGHT_FOLDER,
    PERFECT_FORESIGHT_ORIGIN,
    ROOT,
)
from stage_builders import methodized_copy, stage_from_file, stage_from_text
from stage_texts import (
    EXPLICIT_GRID_SETTINGS,
    changed,
    explicit_policy_with_entries,
    line_of,
    perfect_foresight_text,
)

from bellman.native.hypergraphs import copy_native
from bellman.refusals import ConstructionError
from bellman.stage import method_types

# the solution methods whose block reads the continuation value, which a
# refusal of a line of an explicit block names as the methods under which
# such a line is written
CONTINUATION_VALUE_METHODS = "!egm or !time_iteration, whose block reads the continuation value"


# each addition appended to the stage that the fixture of the first column
# names, with what makes it no explicit solution: the builder at which it is
# refused, the line of the addition at which it is refused, and the phrases of
# the refusal's message. An addition is read after its line `@methods: <the
# stage's name>`, so the entry or the block header stands on line 2 and the
# first line of a block on line 3; a refusal stands at the line at fault, or at
# the typing entry where no line is at fault.
EXPLICIT_REFUSALS = [
    pytest.param(
        "perfect_foresight",
        "policy.method : !explicit\n",
        "policy",
        2,
        (
            "no addition appends a line to the block",
            "`[id=policy, policy.method : !explicit]`",
        ),
        id="an-entry-without-a-block",
    ),
    pytest.param(
        "perfect_foresight",
        "arvl_to_dcsn.method : !explicit\n",
        "arvl_to_dcsn",
        2,
        ("is a forward builder", "policy builder or on a backward value builder"),
        id="a-forward-builder",
    ),
    pytest.param(
        "perfect_foresight",
        "[id=policy, policy.method : !explicit] {\n"
        "    c^(-ρ) = β*R*D_{a}V[>]    :: [id=euler]\n}\n",
        "policy",
        3,
        ("`policy.euler`", "states a relation", CONTINUATION_VALUE_METHODS),
        id="a-relation",
    ),
    pytest.param(
        "perfect_foresight",
        "[id=policy, policy.method : !explicit] {\n"
        "    c = (β*D_{a}V[>])^(-1/ρ)    :: [id=inverse]\n}\n",
        "policy",
        3,
        ("reads V[>], a value input", CONTINUATION_VALUE_METHODS),
        id="the-derivative-of-a-value-input",
    ),
    pytest.param(
        "perfect_foresight",
        "[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit] {\n"
        "    V = 𝑢(c)/(1-β)    :: [id=stationary]\n}\n",
        "cntn_to_dcsn",
        3,
        ("reads c, a control input of the builder's header", CONTINUATION_VALUE_METHODS),
        id="a-control-read-by-a-value-builder",
    ),
    pytest.param(
        "perfect_foresight",
        "[id=policy, policy.method : !explicit] {\n"
        "    κ = 1 - (R*β)^(1/ρ)/R    :: [id=mpc]\n"
        "    c = argmax_{cp : Γ_c(m)}(κ*𝑢(cp))    :: [id=chosen]\n}\n",
        "policy",
        4,
        ("`policy.chosen`", "applies argmax, an operator", CONTINUATION_VALUE_METHODS),
        id="argmax-on-a-second-line",
    ),
    pytest.param(
        "perfect_foresight",
        "[id=policy, policy.method : !explicit] {\n"
        "    c = solve_{c}(c - (1 - (R*β)^(1/ρ)/R)*(m - 1 + 1/(1 - Γ/R)))    :: [id=solved]\n}\n",
        "policy",
        3,
        ("applies solve, an operator", CONTINUATION_VALUE_METHODS),
        id="solve",
    ),
    pytest.param(
        "perfect_foresight",
        "[id=policy, policy.method : !explicit] {\n    c = D_{m}(m^2)    :: [id=slope]\n}\n",
        "policy",
        3,
        ("applies D, an operator", CONTINUATION_VALUE_METHODS),
        id="a-derivative-operator",
    ),
    # an expectation integrates over a shock, so it writes no explicit
    # function; the buffer-stock stage has two shocks. The block also writes
    # the borrowing bound L[<], which the addition writes as zero, a line that
    # an explicit block admits
    pytest.param(
        "buffer_stock",
        "[id=dcsn_to_arvl, dcsn_to_arvl.method : !explicit] {\n"
        "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * 𝑢(R*k/(Γ*ψ) + ξ))    :: [id=closed]\n"
        "    L[<] = 0    :: [id=closed_bound]\n}\n",
        "dcsn_to_arvl",
        3,
        ("applies E, an operator", CONTINUATION_VALUE_METHODS),
        id="an-expectation-over-two-shocks",
    ),
    pytest.param(
        "perfect_foresight",
        "[id=policy, policy.method : !explicit] {\n"
        "    c[>] = (1 - (R*β)^(1/ρ)/R)*(a + 1)    :: [id=candidate]\n"
        "    c = c[>]    :: [id=identification]\n}\n",
        "policy",
        3,
        ("defines c[>], a field at another perch", "write the line under !egm"),
        id="a-field-at-another-perch",
    ),
    pytest.param(
        "perfect_foresight",
        "[id=policy, policy.method : !explicit] {\n    κ = 1 - (R*β)^(1/ρ)/R    :: [id=mpc]\n}\n",
        "policy",
        2,
        (
            "no line the addition appends writes c",
            "write a line `c = <expression>` in the block",
        ),
        id="an-output-that-no-line-writes",
    ),
]


# the two solution methods that iterate on the continuation value, each with
# the fixture of a stage whose methods file writes a policy block under that
# method that reads the derivative of the continuation value, and the path of
# that methods file
ITERATING_METHODS = [
    pytest.param(
        "!egm",
        "cons_savings_iid",
        (ROOT / CORPUS["cons_savings_iid"]).parent / "methods.bl",
        id="egm",
    ),
    pytest.param(
        "!time_iteration",
        "cons_port_portfolio_stage",
        CONS_PORT / "stages" / "port" / "methods.bl",
        id="time-iteration",
    ),
]


@pytest.fixture(scope="module")
def calibrated_explicit_stage(perfect_foresight_explicit):
    """A copy of the perfect-foresight stage with the explicit solution of
    its policy builder, calibrated at the baseline calibration."""
    return copy_native(perfect_foresight_explicit).calibrate(
        {"calibration": PERFECT_FORESIGHT_CALIBRATION}
    )


@pytest.fixture(scope="module")
def cons_port_portfolio_stage():
    """The symbolic portfolio stage of the cons-port application, whose
    methods file solves its policy builder by `!time_iteration`."""
    return stage_from_file(CONS_PORT / "stages" / "port" / "port.bl")


@pytest.fixture(scope="module")
def perfect_foresight_files():
    """The texts of the stage file and of the methods file of the
    perfect-foresight application, as the repository holds them."""
    folder = ROOT / PERFECT_FORESIGHT_FOLDER
    return SimpleNamespace(
        stage=(ROOT / PERFECT_FORESIGHT_FILE).read_text(encoding="utf-8"),
        methods=(folder / "methods.bl").read_text(encoding="utf-8"),
    )


@pytest.fixture(scope="module")
def calibrated_perfect_foresight(derived_parameter_stages):
    """The perfect-foresight stage whose derived parameters are h and R_n,
    calibrated at the baseline calibration; no test of the file binds it
    further."""
    stage = derived_parameter_stages.stage()
    stage.calibrate({"calibration": derived_parameter_stages.calibration})
    return stage


@pytest.fixture(scope="module")
def buffer_stock_without_transitory_spread(derived_parameter_stages):
    """The buffer-stock stage calibrated at its baseline calibration with
    σ_ξ = 0, the standard deviation of the logarithm of the positive
    transitory draw."""
    stage = derived_parameter_stages.buffer_stock()
    stage.calibrate(
        {"calibration": {**derived_parameter_stages.buffer_stock_calibration, "σ_ξ": 0.0}}
    )
    return stage


# the method type


def test_the_method_type_explicit_is_a_solution_of_a_builder_with_a_block_and_no_grid():
    """The row of `!explicit` among the method types is a solution method
    typed at a builder, which takes a block, no keyword argument and no
    grid."""
    row = method_types["!explicit"]
    assert (row.kind, row.takes_block, row.admits, dict(row.keywords), row.grid) == (
        "solution",
        True,
        ("builder",),
        {},
        None,
    )


# the two levels and the compiled kernel of an explicit policy builder


def test_the_line_of_an_explicit_block_stands_in_place_of_the_maximization(
    perfect_foresight_explicit,
):
    """The kernels of the explicit policy builder at the operative level are
    the aggregation of the block's one line and the Evaluation."""
    pieces = perfect_foresight_explicit.builder.policy.kernels().pieces
    assert [piece.key for piece in pieces] == ["consumption:Aggregation", "Evaluation"]


def test_the_declared_level_of_an_explicit_policy_builder_keeps_the_maximization(
    perfect_foresight_explicit,
):
    """The declared policy builder of the stage with an explicit policy lists
    the maximization of the stage file."""
    names = perfect_foresight_explicit.declared.policy.list().names
    assert "policy.optimality:Argmax" in names


def test_the_kernel_of_an_explicit_line_reads_a_derived_parameter_through_its_definition(
    calibrated_explicit_stage,
):
    """The kernel of the explicit consumption line computes the derived
    parameter h from its definition, with the four declared parameters alone
    as its arguments."""
    consumption = calibrated_explicit_stage.builder.policy.primitives["consumption:Aggregation"]
    kernel = consumption.kernel()
    assert kernel.parameters == ("β", "ρ", "R", "Γ")
    assert "    h = 1/(1 - Γ/R)\n" in kernel.python and "(m - 1 + h)" in kernel.python


def test_the_compiled_kernel_of_an_explicit_line_gives_the_consumption_function(
    calibrated_explicit_stage,
):
    """At the baseline calibration the compiled kernel of the explicit
    consumption line gives κ(m - 1 + h), with κ = 1 - (Rβ)^(1/ρ)/R = 0.04/1.04
    and h = 1/(1 - Γ/R) = 52."""
    consumption = calibrated_explicit_stage.builder.policy.primitives["consumption:Aggregation"]
    kernel = consumption.kernel()
    resources = np.array([0.0, 1.0, 10.0])
    # the compiled function takes the resources m, then the parameter values
    assert np.allclose(
        consumption.compile_kernel()(resources, *kernel.parameter_values),
        0.04 / 1.04 * (resources - 1 + 52),
    )


# the closed form that `!explicit` generates at the Evaluation


def test_explicit_gives_the_evaluation_of_its_builder_a_generated_closed_form(
    perfect_foresight_explicit,
):
    """The method of the Evaluation of the explicit policy builder is
    `!closed_form`, read from the expression and generated from the entry
    `policy.method`."""
    held = perfect_foresight_explicit.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == (
        "!closed_form",
        "expression",
        "policy.method",
    )


def test_the_listing_of_the_methods_prints_the_closed_form_as_generated(
    perfect_foresight_explicit,
):
    """`stage.methods` prints the closed form at the Evaluation of the
    explicit policy builder as generated from `policy.method`."""
    listing = str(perfect_foresight_explicit.methods)
    assert "policy.evaluate   !closed_form   generated from policy.method" in listing


def test_the_signature_of_the_evaluation_prints_its_closed_form_as_generated(
    perfect_foresight_explicit,
):
    """The signature of the Evaluation of the explicit policy builder prints
    its method as the closed form generated from `policy.method`."""
    evaluation = perfect_foresight_explicit.builder.policy.primitives["policy:Evaluation"]
    assert "method     !closed_form  generated from policy.method" in str(evaluation.signature())


def test_an_authored_representation_at_the_evaluation_replaces_the_generated_closed_form(
    perfect_foresight,
):
    """`!Linear` with a grid of m typed at the Evaluation of an explicit
    policy builder is the Evaluation's method, sampled on its own nodes."""
    tabulated = methodized_copy(
        perfect_foresight,
        EXPLICIT_GRID_SETTINGS
        + explicit_policy_with_entries(
            "policy.evaluate.method : !Linear | policy.evaluate.grid : !Cartesian(m=(lo, hi, n))"
        ),
    )
    held = tabulated.methods["policy.evaluate"]
    assert (held.word, held.source, held.generated_from) == ("!Linear", "own nodes", None)


def test_a_selection_without_explicit_generates_no_closed_form(perfect_foresight_explicit):
    """`methodize` with an empty addition, which replaces the selection of the
    explicit stage, leaves no method, the generated closed form included."""
    assert "policy.evaluate" in perfect_foresight_explicit.methods
    assert dict(methodized_copy(perfect_foresight_explicit, "").methods) == {}


def test_the_evaluation_of_an_explicit_value_builder_takes_a_generated_closed_form(
    perfect_foresight,
):
    """The method of the Evaluation of a backward value builder typed
    `!explicit` is generated from the entry `cntn_to_dcsn.method`."""
    value = methodized_copy(
        perfect_foresight,
        "[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit] {\n"
        "    V = (1 - (R*β)^(1/ρ)/R)^(-ρ)*(m - 1 + h)^(1-ρ)/(1-ρ)    :: [id=closed_value]\n}\n",
    )
    assert value.methods["cntn_to_dcsn.evaluate"].generated_from == "cntn_to_dcsn.method"


# the refusals of what is no explicit solution


@pytest.mark.parametrize(("stage", "addition", "builder", "line", "phrases"), EXPLICIT_REFUSALS)
def test_an_addition_that_is_no_explicit_solution_is_refused_where_it_breaks_the_rule(
    request, stage, addition, builder, line, phrases
):
    """`methodize` refuses under `explicit-solution` an addition that types
    `!explicit` at a forward builder or without a block, a line of an
    explicit block that states a relation, reads a value input or a control,
    applies an operator or defines a field at another perch, and a block
    that writes no output, at the builder and the line at fault, with a
    message that names its cause."""
    with pytest.raises(ConstructionError) as refused:
        methodized_copy(request.getfixturevalue(stage), addition)
    error = refused.value
    assert (error.rule, error.address, error.file, error.line) == (
        "explicit-solution",
        builder,
        "addition-1.bl",
        line,
    )
    assert [phrase for phrase in phrases if phrase not in error.message] == []


@pytest.mark.parametrize(("word", "stage", "methods"), ITERATING_METHODS)
def test_an_iterating_method_refuses_a_formula_alone_and_binds_lines_that_read_the_marginal_value(
    request, perfect_foresight, word, stage, methods
):
    """A policy block under `!egm` or `!time_iteration` whose one line writes
    consumption by a formula alone is refused at its typing entry, naming
    `!explicit`, while a methods file whose policy block under the same
    method reads the derivative of the continuation value binds."""
    with pytest.raises(ConstructionError) as refused:
        methodized_copy(
            perfect_foresight,
            f"[id=policy, policy.method : {word}] {{\n"
            "    c = (1 - (R*β)^(1/ρ)/R)*(m - 1 + h)    :: [id=consumption]\n}\n",
        )
    error = refused.value
    assert (error.rule, error.address, error.file, error.line) == (
        "explicit-solution",
        "policy",
        "addition-1.bl",
        2,
    )
    phrases = (f"builder under {word}", "type !explicit")
    assert [phrase for phrase in phrases if phrase not in error.message] == []
    bound = copy_native(request.getfixturevalue(stage)).methodize(methods)
    assert bound.methods["policy"].word == word


def test_an_explicit_line_that_compiles_to_no_kernel_is_refused_at_its_builder(
    perfect_foresight,
):
    """An explicit consumption line `c = log(m)`, whose kernel the compiler
    refuses, is refused at the policy builder under `explicit-solution` with
    a message that names the refusal of the compiler."""
    with pytest.raises(ConstructionError) as refused:
        methodized_copy(
            perfect_foresight,
            "[id=policy, policy.method : !explicit] {\n    c = log(m)    :: [id=consumption]\n}\n",
        )
    error = refused.value
    assert (error.rule, error.address) == ("explicit-solution", "policy")
    phrases = ("has no executable compiled kernel", "under kernel-form")
    assert [phrase for phrase in phrases if phrase not in error.message] == []


def test_an_explicit_entry_in_the_stage_file_is_refused_with_the_block_to_write():
    """A stage file that types `policy.method : !explicit` in an entry,
    beside its own explicit line in the policy block, is refused at the
    policy builder, with the advice to write the block in the methods file."""
    text = perfect_foresight_text(
        ("[id=policy, (V[>]", "policy.method : !explicit\n[id=policy, (V[>]"),
        ("c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])", "c = 0.5*(m - 1 + h)"),
    )
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, PERFECT_FORESIGHT_ORIGIN)
    error = refused.value
    assert (error.rule, error.address) == ("explicit-solution", "policy")
    assert "a block `[id=policy, policy.method : !explicit]`" in error.message
    assert error.write.startswith("Write in the methods file the block")


def test_an_output_that_an_explicit_block_of_a_methods_file_leaves_unwritten_is_refused(
    perfect_foresight_files,
):
    """`methodize` refuses the stage file of the perfect-foresight
    application, changed to carry a second field of value type, written `Θ`,
    with the application's methods file, whose explicit block
    `[id=cntn_to_dcsn]` writes lines for V and D_{m}V and none for Θ, under
    `output-defined` at the typing entry of that block, with a message that
    names the block and the field that no line defines."""
    stage_file, methods_file = "perfect_foresight.bl", "methods.bl"
    text = changed(
        perfect_foresight_files.stage,
        (
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, h[>] : ℝ₊ @ !vlu @ !cnst, c) : !cntn"
            " -> (V : ℝ @ !vlu, h : ℝ₊ @ !vlu @ !cnst) : !dcsn] {\n"
            "    V = 𝑢(c) + β*V[>]               :: [id=value]\n",
            "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, Θ[>] : ℝ @ !vlu, h[>] : ℝ₊ @ !vlu @ !cnst, c)"
            " : !cntn -> (V : ℝ @ !vlu, Θ : ℝ @ !vlu, h : ℝ₊ @ !vlu @ !cnst) : !dcsn] {\n"
            "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
            "    Θ = Θ[>]                        :: [id=limit]\n",
        ),
        (
            "[id=dcsn_to_arvl, (V, h) : !dcsn"
            " -> (V[<] : ℝ @ !vlu, h[<] : ℝ₊ @ !vlu @ !cnst) : !arvl] {\n"
            "    V[<] = Γ^(1-ρ) * V              :: [id=value]\n",
            "[id=dcsn_to_arvl, (V, Θ, h) : !dcsn"
            " -> (V[<] : ℝ @ !vlu, Θ[<] : ℝ @ !vlu, h[<] : ℝ₊ @ !vlu @ !cnst) : !arvl] {\n"
            "    V[<] = Γ^(1-ρ) * V              :: [id=value]\n"
            "    Θ[<] = Θ                        :: [id=limit]\n",
        ),
    )
    methods = perfect_foresight_files.methods
    stage = stage_from_text(text, stage_file)
    with pytest.raises(ConstructionError) as refused:
        methodized_copy(stage, {"text": methods, "origin": methods_file})
    refusal = refused.value
    assert (refusal.rule, refusal.address) == ("output-defined", "cntn_to_dcsn")
    assert (refusal.file, refusal.line) == (
        methods_file,
        line_of(methods, "[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit]"),
    )
    advice = (
        "Write in that block of methods.bl a line that defines Θ: `Θ = …`, or, if block "
        "'cntn_to_dcsn' is not meant to write Θ, remove Θ from the output side of its header"
    )
    assert refusal.message == (
        "the header of block 'cntn_to_dcsn' lists Θ on its output side, and no line defines "
        "Θ in the block `[id=cntn_to_dcsn]` of methods.bl, whose lines stand in place of the "
        f"stage file's lines of the block under !explicit. {advice}"
    )
    assert refusal.write == advice
    (listed,) = refusal.related
    assert (listed.role, listed.file, listed.line) == (
        "listed output",
        stage_file,
        line_of(text, "[id=cntn_to_dcsn,"),
    )


# the derived parameters of the perfect-foresight stage: human wealth
# h := 1/(1 - Γ/R) and the interest factor normalized by growth R_n := R/Γ


def test_stage_par_lists_the_derived_parameters_after_the_declared_parameters(
    derived_parameter_stages,
):
    """`stage.par` of the symbolic perfect-foresight stage lists the derived
    parameters h and R_n after the four declared parameters."""
    assert list(derived_parameter_stages.stage().par) == ["β", "ρ", "R", "Γ", "h", "R_n"]


def test_a_derived_parameter_of_a_symbolic_stage_prints_its_definition_unbound(
    derived_parameter_stages,
):
    """The entry of h in `stage.par` of the symbolic stage prints its
    definition and no value."""
    assert str(derived_parameter_stages.stage().par["h"]) == "h := 1/(1 - Γ/R), unbound"


# a calibration that supplies a value for h, and one at which h divides by
# zero, Γ = R = 1.04
REFUSED_CALIBRATIONS = [
    pytest.param({"h": 52.0}, id="a-value-for-h"),
    pytest.param({"Γ": 1.04}, id="a-growth-factor-at-which-h-has-no-value"),
]


@pytest.mark.parametrize("values", REFUSED_CALIBRATIONS)
def test_a_refused_calibration_leaves_the_stage_as_it_was(values, derived_parameter_stages):
    """A calibration that supplies h, or at which h has no value, refused by
    `calibrate`, leaves the stage as it was: the stage holds no calibration,
    and its next calibration, at the baseline values, stores those values
    and gives h the value 52, as on a stage that was never refused."""
    stage = derived_parameter_stages.stage()
    with pytest.raises(ConstructionError):
        stage.calibrate({"calibration": {**derived_parameter_stages.calibration, **values}})
    assert stage.bindings.calibration is None
    stage.calibrate({"calibration": derived_parameter_stages.calibration})
    assert dict(stage.bindings.calibration) == derived_parameter_stages.calibration
    assert stage.par["h"].value == pytest.approx(52.0)


def test_calibration_gives_a_derived_parameter_the_value_of_its_definition(
    calibrated_perfect_foresight,
):
    """At the baseline calibration human wealth h has the value
    1/(1 - 1.02/1.04) = 52."""
    assert calibrated_perfect_foresight.par["h"].value == pytest.approx(52.0)


def test_the_stored_calibration_holds_the_declared_parameters_alone(
    calibrated_perfect_foresight, derived_parameter_stages
):
    """The calibration that the calibrated stage stores is the calibration
    given, which supplies the four declared parameters."""
    stored = calibrated_perfect_foresight.bindings.calibration
    assert dict(stored) == derived_parameter_stages.calibration


def test_the_kernel_of_the_law_of_motion_writes_a_derived_parameter_through_its_definition(
    calibrated_perfect_foresight,
):
    """The kernel of the law of motion of resources computes R_n from its
    definition R/Γ, with the declared parameters R and Γ as its arguments."""
    kernel = calibrated_perfect_foresight.builder["arvl", "dcsn"]["Pushforward"].kernel()
    assert kernel.parameters == ("R", "Γ") and "    R_n = R/Γ\n" in kernel.python


def test_the_compiled_law_of_motion_reads_the_value_of_a_derived_parameter(
    calibrated_perfect_foresight,
):
    """At the baseline calibration the compiled law of motion of resources
    gives m = R_n*k + 1 = 1.04/1.02 + 1 at k = 1."""
    law = calibrated_perfect_foresight.builder["arvl", "dcsn"]["Pushforward"]
    kernel = law.kernel()
    # the compiled function takes the savings k, then the parameter values
    assert law.compile_kernel()(np.array([1.0]), *kernel.parameter_values) == pytest.approx(
        [1.04 / 1.02 + 1]
    )


def test_the_card_of_a_derived_parameter_shows_its_definition_with_its_value(
    calibrated_perfect_foresight,
):
    """The card of the definition of h in the calibrated stage shows the
    definition 1/(1 − Γ/R) with the value that `stage.par` holds."""
    stage = calibrated_perfect_foresight
    h = next(identity for identity in stage.definitions if str(identity).endswith(":derived:h"))
    card = str(stage.definitions.denote(h))
    assert "h  := 1/(1 − Γ/R)" in card and f"= {stage.par['h'].value!r}" in card


# a derived parameter that a methods addition defines: the marginal
# propensity to consume κ := 1 - (R*β)^(1/ρ)/R


def test_a_derived_parameter_of_a_methods_addition_is_listed_last_once_the_addition_is_read(
    derived_parameter_stages,
):
    """κ, absent from `stage.par` of the calibrated stage, is listed last once
    `methodize` reads the addition that defines it."""
    stage = derived_parameter_stages.stage()
    stage.calibrate({"calibration": derived_parameter_stages.calibration})
    assert "κ" not in stage.par
    stage.methodize(derived_parameter_stages.addition)
    assert list(stage.par)[-1] == "κ"


def test_a_derived_parameter_of_a_methods_addition_takes_its_value_at_the_kept_calibration(
    derived_parameter_stages,
):
    """κ, which an addition read after `calibrate` defines, has the value
    1 - (1.04/1.04)^(1/2)/1.04 = 0.04/1.04 at the calibration that the stage
    keeps."""
    stage = derived_parameter_stages.stage()
    stage.calibrate({"calibration": derived_parameter_stages.calibration})
    stage.methodize(derived_parameter_stages.addition)
    assert stage.par["κ"].value == pytest.approx(0.04 / 1.04)


def test_an_addition_whose_derived_parameter_has_no_value_at_the_calibration_is_refused(
    derived_parameter_stages,
):
    """`methodize` of the calibrated stage, which holds the addition that
    defines κ, refuses a replacing addition that defines κ := 1/(R - 1.04),
    which divides by zero at R = 1.04, under `derived-parameter` at the
    line of the definition."""
    stage = derived_parameter_stages.stage()
    stage.calibrate({"calibration": derived_parameter_stages.calibration})
    stage.methodize(derived_parameter_stages.addition)
    with pytest.raises(ConstructionError) as refused:
        stage.methodize(
            {"text": "@methods: perfect_foresight\nκ := 1/(R - 1.04)\n", "origin": "m.bl"}
        )
    assert (refused.value.rule, refused.value.address) == ("derived-parameter", "m.bl:2")


def test_methodize_with_no_addition_returns_the_calibrated_stage_to_its_stage_file(
    derived_parameter_stages,
):
    """After the addition that defines κ and a refused replacing addition,
    `methodize` with no addition leaves `stage.par` without κ, with the
    calibration as it was given."""
    stage = derived_parameter_stages.stage()
    stage.calibrate({"calibration": derived_parameter_stages.calibration})
    stage.methodize(derived_parameter_stages.addition)
    with pytest.raises(ConstructionError):
        stage.methodize(
            {"text": "@methods: perfect_foresight\nκ := 1/(R - 1.04)\n", "origin": "m.bl"}
        )
    stage.methodize([])
    stored = stage.bindings.calibration
    assert "κ" not in stage.par and dict(stored) == derived_parameter_stages.calibration


# the derived log-mean of the positive transitory draw of the buffer-stock
# stage, μ_ξ := -log(1 - p_zero) - σ_ξ^2/2


def test_the_derived_log_mean_gives_the_positive_transitory_draw_its_atom_at_zero_spread(
    buffer_stock_without_transitory_spread, derived_parameter_stages
):
    """At σ_ξ = 0 the positive transitory draw exp(μ_ξ) of the buffer-stock
    stage is 1/(1 - p_zero)."""
    p_zero = derived_parameter_stages.buffer_stock_calibration["p_zero"]
    log_mean = buffer_stock_without_transitory_spread.par["μ_ξ"].value
    assert math.exp(log_mean) == pytest.approx(1 / (1 - p_zero))


def test_the_stored_calibration_of_the_buffer_stock_stage_holds_no_value_of_the_log_mean(
    buffer_stock_without_transitory_spread,
):
    """The calibration that the calibrated buffer-stock stage stores holds no
    value for the derived parameter μ_ξ."""
    assert "μ_ξ" not in buffer_stock_without_transitory_spread.bindings.calibration


def test_a_calibration_at_which_a_derived_scale_is_negative_is_refused_by_its_distribution(
    derived_parameter_stages,
):
    """The variant of the buffer-stock stage whose transitory draw takes the
    derived μ_ξ as its log scale refuses σ_ξ = 0.2 under
    `distribution-domain`, at which μ_ξ = -log(1 - 0.005) - 0.2²/2 =
    -0.0149874581 lies outside σ ≥ 0."""
    variant = derived_parameter_stages.buffer_stock("μ_ξ")
    with pytest.raises(ConstructionError) as refused:
        variant.calibrate(
            {"calibration": {**derived_parameter_stages.buffer_stock_calibration, "σ_ξ": 0.2}}
        )
    assert refused.value.rule == "distribution-domain"
    phrases = ("μ_ξ = -0.0149874581", "σ ≥ 0")
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []
