"""The applications and the lesson that the documentation shows, checked
against the package: the stage, the methods and the example page of the
buffer-stock application, the module and the notebook of the perfect-foresight
application, and lesson 04 of the tutorials."""

import inspect
import json
import math

import mpmath
import numpy
import pytest
from application_files import (
    BUFFER_STOCK_FILE,
    BUFFER_STOCK_METHODS,
    BUFFER_STOCK_PAGE,
    BUFFER_STOCK_SETTINGS,
)
from stage_builders import closed_form_check

from bellman.refusals import ConstructionError

# --- the buffer-stock application ---

# the spacing of the floating-point numbers at one
EPS = numpy.finfo(float).eps


def declared_value(expression, values):
    """The value of `expression`, an expression as the stage prints it, at
    `values`, a mapping from names to numbers or functions: the printed text
    read as a Python expression with the power `^` as `**`, and log and exp
    those of mpmath, so that values given at fifty digits are evaluated at
    fifty digits."""
    names = {"log": mpmath.log, "exp": mpmath.exp, **values}
    return eval(expression.replace("^", "**"), {"__builtins__": {}}, names)


def transitory_law(stage, values=None):
    """The law of the transitory draw ξ as the Expectation of the arrival
    value builder's `kernels()` record prints it, a mixture of an atom and a
    lognormal draw, with its arguments evaluated at `values`, by default the
    values `stage.par` answers: the pair of the atom's weight and point, and
    the pair of the draw's weight and the location and scale of its
    LogNormal. A law of another form does not unpack into these pairs."""
    record = stage.builder["dcsn", "arvl"].kernels()
    (expectation,) = [piece for piece in record.pieces if piece.kind == "Expectation"]
    law = expectation.kernel.split("\n", 1)[0].partition("ξ ~ ")[2]
    if values is None:
        values = {name: stage.par[name].value for name in stage.par}
    families = {
        "Mixture": lambda *parts: parts,
        "LogNormal": lambda *arguments: arguments,
    }
    (atom_weight, atom), (weight, (location, scale)) = declared_value(law, {**values, **families})
    return (atom_weight, atom), (weight, (location, scale))


def transitory_mean(law):
    """The exact mean of `law`, a law as `transitory_law` gives it: the
    atom's weight times its point, plus the draw's weight times the mean
    exp(μ + σ²/2) of its LogNormal(μ, σ)."""
    (atom_weight, atom), (weight, (location, scale)) = law
    return atom_weight * atom + weight * mpmath.exp(location + scale**2 / 2)


def transitory_quadrature(law, nodes):
    """The points and the probabilities that Gauss–Hermite quadrature with
    `nodes` nodes gives `law`, a law as `transitory_law` gives it: the
    atom's point with the atom's weight, and the points exp(μ + σ·z) at the
    standard normal nodes z with the draw's weight times the weights of the
    rule, divided by √(2π). At σ = 0 every point of the draw is exp(μ)."""
    (atom_weight, atom), (weight, (location, scale)) = law
    standard, weights = numpy.polynomial.hermite_e.hermegauss(nodes)
    points = numpy.concatenate(([atom], numpy.exp(location + scale * standard)))
    drawn = weight * weights / math.sqrt(2 * math.pi)
    return points, numpy.concatenate(([atom_weight], drawn))


def primitive_values(stage):
    """The values of the parameters of `stage` that no definition derives, as
    numbers of mpmath at the working precision."""
    return {
        name: mpmath.mpf(stage.par[name].value)
        for name in stage.par
        if not stage.par[name].derived
    }


def defined_location(stage, primitive):
    """The value of μ_ξ by the definition that `stage.par` prints, at the
    values `primitive` of the other parameters."""
    definition = str(stage.par["μ_ξ"]).partition(":= ")[2]
    return declared_value(definition, primitive)


@pytest.fixture(scope="module")
def specified_buffer_stock(buffer_stock_application):
    """The stage of the buffer-stock application at its baseline calibration,
    with its methods and its settings bound, which the tests read and do not
    bind further."""
    return buffer_stock_application.stage(buffer_stock_application.calibration)


def test_the_files_of_the_buffer_stock_application_make_a_specified_stage(
    specified_buffer_stock,
):
    """The stage file, the methods file, the calibration and the settings file
    of the buffer-stock application make a specified stage."""
    stage = specified_buffer_stock
    assert repr(stage) == "ElaboratedStage('buffer_stock', specified)"


def test_the_stage_lists_the_location_of_the_transitory_draw_last_as_a_derived_parameter(
    specified_buffer_stock,
):
    """`stage.par` lists μ_ξ, the location of the lognormal transitory draw,
    after the declared parameters, as derived by its printed definition."""
    stage = specified_buffer_stock
    assert list(stage.par)[-1] == "μ_ξ" and stage.par["μ_ξ"].derived
    assert str(stage.par["μ_ξ"]).endswith(":= -log(1 - p_zero) - σ_ξ^2/2")


def test_the_calibration_of_the_buffer_stock_stage_holds_no_value_of_the_derived_location(
    specified_buffer_stock,
):
    """The calibration that the buffer-stock stage keeps holds no value of
    the derived parameter μ_ξ."""
    stage = specified_buffer_stock
    assert "μ_ξ" not in stage.bindings.calibration


def test_the_transitory_draw_has_mean_one_at_fifty_digits_under_the_printed_definition(
    specified_buffer_stock,
):
    """The law of ξ that the arrival value builder prints has mean one to 45
    digits, with μ_ξ evaluated at fifty digits by its printed definition."""
    stage = specified_buffer_stock
    with mpmath.workdps(50):
        primitive = primitive_values(stage)
        exact = defined_location(stage, primitive)
        law = transitory_law(stage, {**primitive, "μ_ξ": exact})
        assert abs(transitory_mean(law) - 1) < mpmath.mpf(10) ** -45


def test_the_stage_computes_the_derived_location_from_its_definition_to_rounding(
    specified_buffer_stock,
):
    """The value of μ_ξ that `stage.par` answers is the value of its printed
    definition at the other parameters, to four units of rounding."""
    stage = specified_buffer_stock
    location = stage.par["μ_ξ"].value
    with mpmath.workdps(50):
        primitive = primitive_values(stage)
        exact = defined_location(stage, primitive)
        p, s = primitive["p_zero"], primitive["σ_ξ"]
        assert abs(location - exact) <= 4 * EPS * (abs(mpmath.log(1 - p)) + s**2 / 2)


def test_the_transitory_draw_has_mean_one_to_rounding_at_the_values_of_the_stage(
    specified_buffer_stock,
):
    """The law of ξ that the arrival value builder prints has mean one to two
    units of rounding at the values that `stage.par` answers."""
    law = transitory_law(specified_buffer_stock)
    assert abs(transitory_mean(law) - 1) <= 2 * EPS


@pytest.mark.parametrize(
    "multiple", [1, 2], ids=["nodes-of-the-settings", "twice-the-nodes-of-the-settings"]
)
def test_gauss_hermite_quadrature_of_the_transitory_draw_keeps_its_mass_and_its_mean(
    specified_buffer_stock, multiple
):
    """Gauss–Hermite quadrature of the law of ξ, at the seven nodes of the
    settings file and at twice as many, keeps the mass and the mean of the law
    at one to four units of rounding."""
    stage = specified_buffer_stock
    nodes = stage.settings["n_ξ_nodes"].value
    assert nodes == 7
    points, probabilities = transitory_quadrature(transitory_law(stage), multiple * nodes)
    assert abs(probabilities.sum() - 1) <= 4 * EPS
    assert abs(probabilities @ points - 1) <= 4 * EPS


def test_at_zero_scale_every_quadrature_point_of_the_lognormal_draw_is_one_over_one_minus_p_zero(
    buffer_stock_application,
):
    """At σ_ξ = 0 quadrature puts every point of the lognormal part of ξ at
    1/(1 − p_zero), so that the mean of the law is one."""
    calibration = buffer_stock_application.calibration
    zero_scale = buffer_stock_application.stage({**calibration, "σ_ξ": 0.0})
    nodes = zero_scale.settings["n_ξ_nodes"].value
    p_zero = zero_scale.par["p_zero"].value
    points, probabilities = transitory_quadrature(transitory_law(zero_scale), nodes)
    positive = numpy.unique(points[1:])
    assert positive.size == 1 and positive[0] == pytest.approx(1 / (1 - p_zero), rel=4 * EPS)
    assert abs(probabilities @ points - 1) <= 4 * EPS


@pytest.mark.parametrize("p_zero", [0.0, 1.0], ids=["zero", "one"])
def test_p_zero_is_refused_at_each_bound_of_its_declared_set_and_accepted_inside_it(
    buffer_stock_application, specified_buffer_stock, p_zero
):
    """A calibration that sets p_zero to a bound of its declared set (0, 1)
    is refused, where the baseline calibration, inside the set, is accepted."""
    calibration = buffer_stock_application.calibration
    # the stage of the baseline calibration holds its value of p_zero
    assert specified_buffer_stock.par["p_zero"].value == calibration["p_zero"]
    with pytest.raises(ValueError, match=r"lies outside the declared set \(0, 1\)"):
        buffer_stock_application.stage({**calibration, "p_zero": p_zero})


def test_a_calibration_that_supplies_the_derived_location_is_refused_at_its_definition(
    buffer_stock_application, specified_buffer_stock, text_of
):
    """A calibration that gives μ_ξ a value, even the value of its definition,
    is refused under `derived-parameter` at the line of the stage file that
    defines μ_ξ."""
    calibration = buffer_stock_application.calibration
    location = specified_buffer_stock.par["μ_ξ"].value
    lines = text_of(BUFFER_STOCK_FILE).split("\n")
    line = next(n for n, written in enumerate(lines, 1) if written.startswith("μ_ξ :="))
    with pytest.raises(ConstructionError) as refused:
        buffer_stock_application.stage({**calibration, "μ_ξ": location})
    assert (refused.value.rule, refused.value.address) == (
        "derived-parameter",
        f"{BUFFER_STOCK_FILE}:{line}",
    )
    assert "which the stage defines as `-log(1 - p_zero) - σ_ξ^2/2`" in refused.value.message


def test_the_derived_location_owns_one_condition_established_at_calibration(
    specified_buffer_stock,
):
    """The one obligation that the derived μ_ξ owns, that the arithmetic of
    its definition is defined, is established at calibration."""
    stage = specified_buffer_stock
    owned = [
        item
        for item in stage.obligations()
        if item.entries and str(item.entries[0]) == "buffer_stock:derived:μ_ξ"
    ]
    assert [(item.condition, item.status) for item in owned] == [
        ("arithmetic-definedness", "established")
    ]


def test_the_printed_law_of_the_transitory_draw_names_the_derived_location_alone(
    specified_buffer_stock,
):
    """The kernels record of the arrival value builder writes the law of ξ
    with the name μ_ξ, without its value or its definition, so that a handler
    reads the value in `stage.par`."""
    record = specified_buffer_stock.builder["dcsn", "arvl"].kernels()
    (expectation,) = [piece for piece in record.pieces if piece.kind == "Expectation"]
    assert "LogNormal(μ_ξ, σ_ξ)" in expectation.kernel and expectation.parameters == ()
    assert "μ_ξ" not in record.parameters and "log(1 - p_zero)" not in str(record)


def test_the_methods_file_of_the_buffer_stock_application_binds_its_four_methods_as_written(
    specified_buffer_stock,
):
    """The buffer-stock stage holds the four methods of its methods file at
    their places, each printed as the file writes it."""
    stage = specified_buffer_stock
    assert [(str(place), str(method)) for place, method in stage.methods.items()] == [
        ("dcsn_to_arvl.E_ψ_ξ", "!gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)"),
        ("dcsn_to_arvl.evaluate", "!Linear   !Cartesian(k=(k_min, k_max, n_k))"),
        ("policy", "!egm   !Cartesian(a=(a_min, a_max, n_a))"),
        ("policy.evaluate", "!Linear"),
    ]


@pytest.mark.parametrize(
    "quoted",
    [BUFFER_STOCK_FILE, BUFFER_STOCK_METHODS, BUFFER_STOCK_SETTINGS],
    ids=["stage-file", "methods-file", "settings-file"],
)
def test_the_example_page_of_the_buffer_stock_application_quotes_its_file_as_it_stands(
    text_of, quoted
):
    """The example page of the buffer-stock application quotes the whole text
    of each of its three files."""
    assert text_of(quoted) in text_of(BUFFER_STOCK_PAGE)


# --- the module of the perfect-foresight application ---


def test_each_function_of_the_perfect_foresight_module_takes_its_listed_arguments_in_order():
    """Each of the twelve functions of the module of the perfect-foresight
    application, which its notebook imports, takes the arguments listed here,
    in their order."""
    check = closed_form_check()
    # the Bellman and the Euler residual take a `policy`, so that the check
    # near the limit reads the converged policy, and the gridded route its
    # `initial` pairs, so that an infeasible extrapolation can be provoked
    assert {
        name: tuple(inspect.signature(getattr(check, name)).parameters)
        for name in (
            "closed_form_stage",
            "gridded_stage",
            "parameters",
            "piece",
            "kernel_text",
            "closed_form",
            "value_kernels",
            "bellman_residual",
            "euler_residual",
            "interpolate",
            "gridded_route",
            "comparison",
        )
    } == {
        "closed_form_stage": ("calibration",),
        "gridded_stage": ("n_a", "a_min", "a_max", "calibration"),
        "parameters": ("stage",),
        "piece": ("record", "key", "values"),
        "kernel_text": ("record", "key"),
        "closed_form": ("stage",),
        "value_kernels": ("stage",),
        "bellman_residual": ("stage", "m", "policy"),
        "euler_residual": ("stage", "m", "policy"),
        "interpolate": ("m", "knots", "values"),
        "gridded_route": ("stage", "tolerance", "iterations", "initial"),
        "comparison": ("n_a", "a_min", "a_max", "m", "tolerance", "calibration"),
    }


def test_the_path_constants_of_the_perfect_foresight_module_name_the_files_of_its_application():
    """The path constants of the module name the application's declaration
    folder, its stage file, the two methods files beside it and its
    calibration, each of the four files standing."""
    check = closed_form_check()
    folder = check.DECLARATION / "stages" / "perfect_foresight"
    assert (
        check.DECLARATION,
        check.STAGE,
        check.METHODS,
        check.GRIDDED_METHODS,
        check.CALIBRATION,
    ) == (
        check.FOLDER / "declaration",
        folder / "perfect_foresight.bl",
        folder / "methods.bl",
        folder / "methods.egm.bl",
        check.DECLARATION / "calibration" / "perfect_foresight.yml",
    )
    assert all(
        path.is_file()
        for path in (
            check.STAGE,
            check.METHODS,
            check.GRIDDED_METHODS,
            check.CALIBRATION,
        )
    )


def test_the_closed_form_record_of_the_perfect_foresight_module_holds_its_nine_fields():
    """The record of the closed form of the perfect-foresight stage holds
    exactly its nine fields."""
    check = closed_form_check()
    form = check.closed_form(check.closed_form_stage())
    assert set(vars(form)) == {
        "return_patience",
        "κ",
        "h",
        "limit",
        "consumption",
        "value",
        "marginal",
        "arrival_value",
        "arrival_marginal",
    }


def test_the_record_of_the_gridded_route_has_an_evaluation_that_does_not_extrapolate_by_default():
    """The record of the gridded route holds its knots, its consumption, its
    iterations and `evaluate(m, extrapolate=False)`."""
    check = closed_form_check()
    # gridded_stage(n_a, a_min, a_max): a grid of five points of a, from -40
    # to 60
    route = check.gridded_route(check.gridded_stage(5, -40.0, 60.0))
    assert {"knots", "consumption", "iterations", "evaluate"} <= set(vars(route))
    assert tuple(inspect.signature(route.evaluate).parameters) == ("m", "extrapolate")
    assert inspect.signature(route.evaluate).parameters["extrapolate"].default is False


# --- the notebook of the perfect-foresight application ---

# the notebook of the perfect-foresight application, committed with the
# outputs of its execution
PERFECT_FORESIGHT_NOTEBOOK = (
    "applications/consumption-perfect-foresight-crra/code/closed-form-and-grid.ipynb"
)


# the intended refusal of each cell tagged `raises-exception`: the cell's id,
# the class of the exception and the condition that its message names
INTENDED_REFUSALS = {
    "discount-factor-above-the-return-impatience-bound": (
        "7297042b",
        "ValueError",
        "does not satisfy the condition β < R^(ρ - 1)",
    ),
    "growth-factor-outside-its-declared-set": (
        "3c9d3030",
        "ValueError",
        "lies outside the declared set (0, R)",
    ),
    "consumption-at-the-natural-borrowing-limit": (
        "66c54820",
        "ValueError",
        "total wealth m - L = 0.0 is not positive",
    ),
}


@pytest.fixture(scope="module")
def notebook_code_cells(text_of):
    """The code cells of the committed notebook of the perfect-foresight
    application, with the outputs of their execution."""
    cells = json.loads(text_of(PERFECT_FORESIGHT_NOTEBOOK))["cells"]
    return [cell for cell in cells if cell["cell_type"] == "code"]


def test_the_cells_of_the_notebook_were_executed_once_in_order_from_a_fresh_kernel(
    notebook_code_cells,
):
    """Every code cell of the notebook of the perfect-foresight application
    holds an execution count, and the counts run in order from 1."""
    code = notebook_code_cells
    assert [cell["execution_count"] for cell in code] == list(range(1, len(code) + 1))


def test_an_error_output_of_the_notebook_stands_only_in_the_three_cells_tagged_to_raise_one(
    notebook_code_cells,
):
    """The cells of the notebook that hold an error output are exactly the
    three cells tagged `raises-exception`."""
    code = notebook_code_cells
    tagged = {
        cell["id"] for cell in code if "raises-exception" in cell["metadata"].get("tags", [])
    }
    assert tagged == {cell for cell, _, _ in INTENDED_REFUSALS.values()}
    errors = {
        cell["id"]
        for cell in code
        if any(output["output_type"] == "error" for output in cell["outputs"])
    }
    assert errors == tagged


@pytest.mark.parametrize("refusal", INTENDED_REFUSALS)
def test_each_tagged_cell_of_the_notebook_shows_its_intended_refusal(notebook_code_cells, refusal):
    """Each cell of the notebook tagged `raises-exception` holds one error, of
    the intended class, whose message names the condition that the cell
    breaks."""
    cell, name, condition = INTENDED_REFUSALS[refusal]
    (error,) = [
        output
        for held in notebook_code_cells
        if held["id"] == cell
        for output in held["outputs"]
        if output["output_type"] == "error"
    ]
    assert error["ename"] == name
    assert condition in error["evalue"]


# --- lesson 04 ---

LESSON = "tutorials/getting-started/04-parameters-methods-and-settings.ipynb"


@pytest.fixture(scope="module")
def lesson_cells(text_of):
    """The cells of lesson 04, on parameters, methods and settings, with their
    recorded outputs."""
    return json.loads(text_of(LESSON))["cells"]


def calibrating_cell(cells):
    """The index of the first code cell of `cells` that hands `elaborate_stage`
    a record with the calibration `portfolio.yml`; a later cell elaborates and
    calibrates a stage of its own for the second methods file, since a binding
    verb binds the stage it is called on."""
    return next(
        index
        for index, cell in enumerate(cells)
        if cell["cell_type"] == "code"
        and "elaborate_stage" in "".join(cell["source"])
        and "calibration/portfolio.yml" in "".join(cell["source"])
    )


def test_lesson_04_introduces_the_stage_calibrated_by_one_call_after_the_symbolic_stage(
    lesson_cells,
):
    """In lesson 04 the cell that elaborates and calibrates a stage in one call
    stands after the cell that constructs the symbolic `cons_described`, and
    after a sentence that names the symbolic stage."""
    constructed = [cell.get("id") for cell in lesson_cells].index("l4-c-describes-stage")
    index = calibrating_cell(lesson_cells)
    assert index > constructed and lesson_cells[index - 1]["cell_type"] == "markdown"
    assert "symbolic" in "".join(lesson_cells[index - 1]["source"])


def test_lesson_04_records_the_parameters_of_the_stage_that_one_call_calibrates(
    lesson_cells,
):
    """The recorded output of the cell of lesson 04 that elaborates and
    calibrates a stage in one call is the table of parameters, with ρ at 6.0
    beside its description."""
    (output,) = lesson_cells[calibrating_cell(lesson_cells)]["outputs"]
    # the consumption stage of the cons-port application declares ρ in (1, inf)
    assert "".join(output["data"]["text/plain"]) == (
        "name  set       value  describes\nρ     (1, inf)  6.0    relative risk aversion"
    )
