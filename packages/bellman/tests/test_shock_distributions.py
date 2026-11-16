"""Shock distributions: what a declaration denotes and constructs, the
measure at its written arguments and the numbers that measure gives, the
product law of an indexed shock, and the encoding and the source form of a
declaration."""

import json
import math
import re
from contextlib import nullcontext

import mpmath
import pytest
from application_files import BUFFER_STOCK_CALIBRATION_AT_R_1_04, COPIED_FILES_FOLDER, ROOT
from stage_builders import DEFAULT_ORIGIN, stage_from_text
from stage_texts import (
    CHAIN_CALIBRATION_J1,
    CHAIN_TEXT,
    PSI_IDENTITY,
    TRUNCATED_PSI_LAW,
    TWO_NODES_CALIBRATION,
    UNADMITTED_FAMILY_AFTER_DECISION,
    Y_IDENTITY,
    chain_text_with_law_of_epsilon,
    changed,
    text_with_psi_law,
    two_nodes_text_with_changes,
    two_nodes_text_with_law_of_y,
)

from bellman.display.cards import Textual
from bellman.display.encoding_checks import validate_encoding

# `truncation.mass` computes the standard normal probability of a window of
# the standard-normal variable, and `truncation.standardized_window` the
# window of a truncated lognormal law in that variable; no family of the
# package calls either function
from bellman.distributions import truncation
from bellman.distributions.families import FAMILY_ARGUMENTS, TRUNCATED_LOGNORMAL
from bellman.native.identity import box_identity
from bellman.native.predicates import And, Member
from bellman.refusals import NotConstructed
from bellman.stage.grains import operators_of
from bellman.stage.kernels import kernel
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.syntax.source import to_source
from bellman.syntax.terms import Add, Call, Div, Mul, Neg, Number, Pow, Sub, Sym
from bellman.trellis import connection_report, elaborate_trellis
from bellman.typing.primitive_definitions import primitive_definition
from bellman.typing.typed_expressions import (
    Apply,
    Integral,
    Lambda,
    Measure,
    ProductMeasure,
    format_expression,
)

# the identity of the declaration of ε in the chain stage `CHAIN_TEXT`
EPSILON_IDENTITY = "chain:distribution:ε"


# the truncations of the lognormal law of y, by their ids: the arguments as
# written and as numbers (μ, σ, l, u); the far tail is [e⁹, e¹⁰], whose
# window in the standard-normal variable is [9, 10]
TRUNCATED_LOGNORMAL_WINDOWS = {
    "two-sided": ("0.1, 0.5, 0.5, 2", (0.1, 0.5, 0.5, 2.0)),
    "the-whole-half-line": ("0, 1, 0, inf", (0.0, 1.0, 0.0, math.inf)),
    "one-sided": ("0.2, 0.3, 1, inf", (0.2, 0.3, 1.0, math.inf)),
    "far-tail": (
        "0, 1, 8103.083927575384, 22026.465794806718",
        (0.0, 1.0, math.exp(9), math.exp(10)),
    ),
}

# the truncations of the normal law of y, by their ids: the arguments as
# written and as numbers (μ, σ, l, u); the far tail is l = μ + 9σ, u = μ + 10σ
TRUNCATED_NORMAL_WINDOWS = {
    "symmetric": ("0, 1, -1, 1", (0, 1, -1, 1)),
    "one-sided": ("0, 1, 0, inf", (0, 1, 0, math.inf)),
    "nonstandard": ("2, 0.5, 1, 4", (2, 0.5, 1, 4)),
    "two-infinite-endpoints": ("0, 1, -inf, inf", (0, 1, -math.inf, math.inf)),
    "far-tail": ("0, 1, 9, 10", (0, 1, 9, 10)),
}


# the calibration of the chain stage at J = 2, without the parameters of the
# joint normal law
CHAIN_CALIBRATION_J2 = {
    "J": 2,
    "β": 0.9,
    "Π": [[0.8, 0.1, 0.1], [0.2, 0.6, 0.2], [0.1, 0.1, 0.8]],
}

# the admitted families in the order of the table of families, which the
# message of `not-constructed` lists
FAMILIES = (
    "N",
    "LogNormal",
    "Uniform",
    "TruncatedNormal",
    "TruncatedLogNormal",
    "TypeIExtremeValue",
    "DiscreteMarkov",
    "MarkovChain",
    "Mixture",
    "Categorical",
    "Bernoulli",
)

# [−8, 60] in standard units holds all the mass of the extreme-value law but
# less than 10⁻²⁶, and quadrature over it avoids the overflow of exp(−z) far
# below −8; the quadrature is split at the mode z = 0
EXTREME_VALUE_LOW, EXTREME_VALUE_HIGH = -8, 60


# the two-node stage whose shock y has the parent z
NORMAL_GIVEN_PARENT = two_nodes_text_with_changes(declarations="z : ℝ\nz ~ N(0,1)\ny ~ N(z, 1)\n")

# the chain stage with ε ~ TruncatedLogNormal(0, 1, 0.5, 2) on I_J, and with
# ε ~ TypeIExtremeValue(0, 1)
TRUNCATED_CHAIN_TEXT = chain_text_with_law_of_epsilon("TruncatedLogNormal(0, 1, 0.5, 2)")
EXTREME_VALUE_CHAIN_TEXT = chain_text_with_law_of_epsilon("TypeIExtremeValue(0, 1)")


def text_before(text, block):
    """A stage text cut before the header of the block `block`: its
    declarations and the blocks written before that block."""
    return text[: text.index(f"[id={block}")]


def law_of(stage, shock):
    """The law of the shock `shock` as the record of its declaration holds
    it."""
    record = next(
        record
        for record in stage.definitions.values()
        if record.kind == "distribution" and shock in record.equations[0].subjects
    )
    return record.equations[0].law


def number(term, point=None):
    """The number, as an `mpmath` number, of an arithmetic term of a measure,
    its one bound variable at `point`: a name other than `inf`, `∞` and `pi`
    is the bound variable. A term that reads the variable where `point` is
    None raises LookupError, and a call of a function other than exp raises
    ValueError."""
    if isinstance(term, Number):
        return mpmath.mpf(term.value)
    if isinstance(term, Neg):
        return -number(term.operand, point)
    if isinstance(term, Call):
        if str(term.fun) != "external:exp":
            raise ValueError(f"no number for the call {term}")
        (argument,) = term.args
        return mpmath.exp(number(argument, point))
    if isinstance(term, Sym):
        name = str(term.symbol.name)
        if name in ("inf", "∞"):
            return mpmath.inf
        if name == "external:pi":
            return mpmath.pi
        if point is None:
            raise LookupError(name)
        return mpmath.mpf(point)
    if isinstance(term, Pow):
        return number(term.base, point) ** number(term.exponent, point)
    left, right = number(term.left, point), number(term.right, point)
    return {
        Add: lambda: left + right,
        Sub: lambda: left - right,
        Mul: lambda: left * right,
        Div: lambda: left / right,
    }[type(term)]()


def comparisons_of(condition):
    """The comparisons and memberships of a region's condition, a tuple of
    conditions or a conjunction."""
    if isinstance(condition, tuple):
        return [part for item in condition for part in comparisons_of(item)]
    if isinstance(condition, And):
        return comparisons_of(condition.left) + comparisons_of(condition.right)
    return [condition]


def region(comprehension):
    """The endpoints of a region `{z ∈ ℝ | image ∈ B ∧ l ≤ image ∧ image ≤ u}`
    in increasing order, the numbers its comparisons compare the image with,
    and the image, the term of the bound variable that a membership or a
    comparison reads."""
    bounds, images = [], []
    for part in comparisons_of(comprehension.conds):
        sides = (part.subject,) if isinstance(part, Member) else (part.left, part.right)
        for side in sides:
            try:
                bounds.append(number(side))
            except LookupError:
                images.append(side)
    return tuple(sorted(bounds)), images[0]


def location_and_scale(image):
    """The location m and the scale s of an affine image m + s·z."""
    location = number(image, 0)
    return location, number(image, 1) - location


def density_and_image(integral):
    """The density of an integral of a measure as a function of its bound
    variable z, and the location m and the scale s of its image m + s·z."""
    _, image = region(integral.binding[1])
    location, scale = location_and_scale(image)
    return (lambda z: number(integral.body, z)), location, scale


def measure_of(text, origin=DEFAULT_ORIGIN):
    """The measure, the second object, that the declaration of y in the stage
    text `text` denotes."""
    return stage_from_text(text, origin).definitions.denote(Y_IDENTITY).denoted[1].expression


def agree(computed, expected):
    """Whether two numbers agree to a relative error of 10⁻⁹."""
    return math.isclose(float(computed), float(expected), rel_tol=1e-9)


def flat(expression):
    """The printed form of an expression on one line."""
    return " ".join(format_expression(expression).split())


def definition_lists(value):
    """The `definitions` list of every record that an encoded value holds,
    each as the pairs of its entries' symbols and identities."""
    found = []
    if isinstance(value, dict):
        fields = value.get("fields")
        if isinstance(fields, dict) and isinstance(fields.get("definitions"), list):
            found.append(
                [
                    (entry["fields"]["symbol"], entry["fields"]["identity"])
                    for entry in fields["definitions"]
                ]
            )
        for item in value.values():
            found += definition_lists(item)
    elif isinstance(value, list):
        for item in value:
            found += definition_lists(item)
    return found


@pytest.fixture(scope="module")
def truncated_psi_text(buffer_stock_file_text):
    """The buffer-stock stage text with `ψ ~ TRUNCATED_PSI`."""
    return text_with_psi_law(buffer_stock_file_text, TRUNCATED_PSI_LAW)


@pytest.fixture(scope="module")
def truncated_psi_stage(truncated_psi_text):
    """The stage of `truncated_psi_text`, which the tests read and do not
    calibrate."""
    return stage_from_text(truncated_psi_text, "buffer_stock.bl")


@pytest.fixture(scope="module")
def calibrated_truncated_psi_stage(truncated_psi_text):
    """The stage of `truncated_psi_text` calibrated by
    `BUFFER_STOCK_CALIBRATION_AT_R_1_04`."""
    stage = stage_from_text(truncated_psi_text, "buffer_stock.bl")
    return stage.calibrate(BUFFER_STOCK_CALIBRATION_AT_R_1_04)


@pytest.fixture(scope="module")
def truncated_mixture_stage(buffer_stock_file_text):
    """The buffer-stock stage whose ψ is drawn from a mixture of a point mass
    at 1 and the truncated lognormal law `TRUNCATED_PSI_LAW`."""
    mixture = f"Mixture((p_zero, 1), (1 - p_zero, {TRUNCATED_PSI_LAW}))"
    return stage_from_text(text_with_psi_law(buffer_stock_file_text, mixture), "buffer_stock.bl")


@pytest.fixture(scope="module")
def truncated_normal_text():
    """The two-node stage text with
    `y ~ TruncatedNormal(μ_y, σ_y, l_y, u_y)`."""
    return two_nodes_text_with_law_of_y(
        "TruncatedNormal(μ_y, σ_y, l_y, u_y)", "μ_y : ℝ\nσ_y : ℝ₊₊\nl_y : ℝ\nu_y : ℝ\n"
    )


@pytest.fixture(scope="module")
def extreme_value_text():
    """The two-node stage text with `y ~ TypeIExtremeValue(μ_y, s_y)`."""
    return two_nodes_text_with_law_of_y("TypeIExtremeValue(μ_y, s_y)", "μ_y : ℝ\ns_y : ℝ₊₊\n")


@pytest.fixture(scope="module")
def uniform_stage(uniform_text):
    """The stage of `uniform_text`, calibrated at a_y = 0 and b_y = 1."""
    calibration = {**TWO_NODES_CALIBRATION, "a_y": 0.0, "b_y": 1.0}
    return stage_from_text(uniform_text).calibrate(calibration)


@pytest.fixture(scope="module")
def truncated_normal_stage(truncated_normal_text):
    """The stage of `truncated_normal_text`, calibrated at the standard normal
    law truncated to [−1, 2]."""
    calibration = {**TWO_NODES_CALIBRATION, "μ_y": 0.0, "σ_y": 1.0, "l_y": -1.0, "u_y": 2.0}
    return stage_from_text(truncated_normal_text).calibrate(calibration)


@pytest.fixture(scope="module")
def extreme_value_stage(extreme_value_text):
    """The stage of `extreme_value_text`, calibrated at the location 0 and the
    scale 1."""
    calibration = {**TWO_NODES_CALIBRATION, "μ_y": 0.0, "s_y": 1.0}
    return stage_from_text(extreme_value_text).calibrate(calibration)


@pytest.fixture(scope="module")
def unadmitted_family_after_decision_stage():
    """The stage `UNADMITTED_FAMILY_AFTER_DECISION`, whose shock ε is drawn
    from the family `Weird`, outside the table of families."""
    return stage_from_text(UNADMITTED_FAMILY_AFTER_DECISION, "no_law.bl")


@pytest.fixture(scope="module")
def calibrated_truncated_chain():
    """The stage of `TRUNCATED_CHAIN_TEXT`, calibrated at J = 1."""
    stage = stage_from_text(TRUNCATED_CHAIN_TEXT)
    return stage.calibrate(CHAIN_CALIBRATION_J1)


@pytest.fixture(scope="module")
def truncated_chain():
    """The stage of `TRUNCATED_CHAIN_TEXT`."""
    return stage_from_text(TRUNCATED_CHAIN_TEXT)


@pytest.fixture(scope="module")
def lognormal_chain():
    """The chain stage with ε ~ LogNormal(0, 1) on I_J."""
    return stage_from_text(chain_text_with_law_of_epsilon("LogNormal(0, 1)"), "chain.bl")


@pytest.fixture(scope="module")
def joint_normal_chain():
    """The chain stage as written, with the joint normal law of ε on I_J."""
    return stage_from_text(CHAIN_TEXT, "chain.bl")


@pytest.fixture(scope="module")
def hafiscal():
    """The HAFiscal stage of the corpus, whose employment state z is drawn
    from a `Categorical` law."""
    path = f"{COPIED_FILES_FOLDER}/HAFiscal/HAFiscal.bl"
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


@pytest.fixture(scope="module")
def truncated_lognormal_measures():
    """The measure that `y ~ TruncatedLogNormal(...)` of the two-node stage
    denotes, for each truncation of `TRUNCATED_LOGNORMAL_WINDOWS` by its
    id."""
    return {
        window: measure_of(two_nodes_text_with_law_of_y(f"TruncatedLogNormal({written})"))
        for window, (written, _) in TRUNCATED_LOGNORMAL_WINDOWS.items()
    }


@pytest.fixture(scope="module")
def truncated_normal_measures():
    """The measure that `y ~ TruncatedNormal(...)` of the two-node stage
    denotes, for each truncation of `TRUNCATED_NORMAL_WINDOWS` by its id."""
    return {
        window: measure_of(two_nodes_text_with_law_of_y(f"TruncatedNormal({written})"))
        for window, (written, _) in TRUNCATED_NORMAL_WINDOWS.items()
    }


@pytest.fixture(scope="module")
def uniform_measure():
    """The measure that `y ~ Uniform(0, 2)` of the two-node stage denotes."""
    return measure_of(two_nodes_text_with_law_of_y("Uniform(0, 2)"))


@pytest.fixture(scope="module")
def extreme_value_measure():
    """The measure that `y ~ TypeIExtremeValue(1.5, 2)` of the two-node stage
    denotes."""
    return measure_of(two_nodes_text_with_law_of_y("TypeIExtremeValue(1.5, 2)"))


@pytest.mark.parametrize(
    "stage, written",
    [
        pytest.param(
            "truncated_psi_stage",
            "TruncatedLogNormal(-σ_ψ^2/2, σ_ψ, 0.5, 2)",
            id="truncated-lognormal",
        ),
        pytest.param(
            "truncated_mixture_stage",
            "Mixture((p_zero, 1), (1 - p_zero, TruncatedLogNormal(-σ_ψ^2/2, σ_ψ, 0.5, 2)))",
            id="mixture-with-a-truncated-component",
        ),
    ],
)
def test_the_record_of_a_declaration_holds_the_law_that_the_file_writes(request, stage, written):
    """The record of the declaration of ψ holds the law of the stage text,
    which `to_source` prints without the parentheses of the location."""
    assert to_source(law_of(request.getfixturevalue(stage), "ψ")) == written


# the stages by their fixtures, each with the refusal that the listing of its
# forward builders graph raises, or none
FORWARD_GRAPHS = [
    pytest.param("truncated_psi_stage", nullcontext(), id="truncated-lognormal"),
    pytest.param(
        "calibrated_truncated_psi_stage", nullcontext(), id="truncated-lognormal-calibrated"
    ),
    pytest.param(
        "truncated_mixture_stage", nullcontext(), id="mixture-with-a-truncated-component"
    ),
    pytest.param(
        "buffer_stock", nullcontext(), id="lognormal-and-mixture-of-the-buffer-stock-file"
    ),
    pytest.param("uniform_stage", nullcontext(), id="uniform-calibrated"),
    pytest.param("truncated_normal_stage", nullcontext(), id="truncated-normal-calibrated"),
    pytest.param("extreme_value_stage", nullcontext(), id="extreme-value-calibrated"),
    pytest.param(
        "calibrated_truncated_chain", nullcontext(), id="indexed-truncated-lognormal-calibrated"
    ),
    # the printed refusal lists the admitted families and ends with its rule
    pytest.param(
        "unadmitted_family_after_decision_stage",
        pytest.raises(
            NotConstructed,
            match=re.escape(f"the families {', '.join(FAMILIES)}") + r".*; rule not-constructed\)",
        ),
        id="a-family-outside-the-table",
    ),
]


@pytest.mark.parametrize("stage, refusal", FORWARD_GRAPHS)
def test_the_forward_builders_graph_is_constructed_only_for_a_law_of_the_table_of_families(
    request, stage, refusal
):
    """The forward builders graph of a stage whose shocks are drawn from
    families of the table of families is constructed, its listing holding the
    two forward builders, where a shock drawn from a family outside the table,
    `Weird` in `UNADMITTED_FAMILY_AFTER_DECISION`, has it refused under
    `not-constructed` with a message that lists the admitted families in the
    order of the table."""
    stage = request.getfixturevalue(stage)
    with refusal:
        assert list(stage.builder.fwd.list()) == ["arvl_to_dcsn", "dcsn_to_cntn"]


@pytest.mark.parametrize(
    "stage",
    [
        pytest.param("truncated_psi_stage", id="truncated-lognormal"),
        pytest.param("uniform_stage", id="uniform-calibrated"),
        pytest.param("truncated_normal_stage", id="truncated-normal-calibrated"),
        pytest.param("extreme_value_stage", id="extreme-value-calibrated"),
        pytest.param("truncated_mixture_stage", id="mixture-with-a-truncated-component"),
        pytest.param("unadmitted_family_after_decision_stage", id="a-family-outside-the-table"),
    ],
)
def test_the_backward_builders_graph_is_constructed_whatever_the_family_of_the_law(request, stage):
    """The backward builders graph of a stage is constructed whether its shock
    is drawn from a scalar family that the table of definitions defines, from
    a mixture, or from a family outside the table of families."""
    assert "cntn_to_dcsn" in str(request.getfixturevalue(stage).builder.bwd.list())


# the scalar declarations by their stage fixtures: the identity of the
# declaration, the symbol of its law, the law as printed, its type, the
# symbol of its measure, and the kind of the measure's body, a quotient of
# two integrals for a truncation and one integral otherwise
SCALAR_DENOTATIONS = [
    pytest.param(
        "truncated_psi_stage",
        PSI_IDENTITY,
        "ψ",
        "TruncatedLogNormal(−σ_ψ²/2, σ_ψ, 0.5, 2)",
        "probability measure on ℝ₊₊",
        "P_ψ",
        Div,
        id="truncated-lognormal",
    ),
    pytest.param(
        "buffer_stock",
        PSI_IDENTITY,
        "ψ",
        "LogNormal(−σ_ψ²/2, σ_ψ)",
        "probability measure on ℝ₊₊",
        "P_ψ",
        Integral,
        id="lognormal",
    ),
    pytest.param(
        "uniform_stage",
        Y_IDENTITY,
        "y",
        "Uniform(a_y, b_y)",
        "probability measure on ℝ",
        "P_y",
        Integral,
        id="uniform",
    ),
    pytest.param(
        "truncated_normal_stage",
        Y_IDENTITY,
        "y",
        "TruncatedNormal(μ_y, σ_y, l_y, u_y)",
        "probability measure on ℝ",
        "P_y",
        Div,
        id="truncated-normal",
    ),
    pytest.param(
        "extreme_value_stage",
        Y_IDENTITY,
        "y",
        "TypeIExtremeValue(μ_y, s_y)",
        "probability measure on ℝ",
        "P_y",
        Integral,
        id="extreme-value",
    ),
    pytest.param(
        "two_nodes_stage",
        Y_IDENTITY,
        "y",
        "N(0, 1)",
        "probability measure on ℝ",
        "P_y",
        Integral,
        id="normal",
    ),
]


@pytest.mark.parametrize(
    "stage, identity, symbol, law, law_type, measure_symbol, body_kind", SCALAR_DENOTATIONS
)
def test_a_scalar_declaration_denotes_two_objects_the_law_as_written_and_its_measure(
    request, stage, identity, symbol, law, law_type, measure_symbol, body_kind
):
    """A declaration of one real shock by a scalar family of the table of
    definitions denotes two objects: the law as written, and its measure,
    under the symbol P with the shock as index, with the law's type and
    identity."""
    first, second = request.getfixturevalue(stage).definitions.denote(identity).denoted
    assert (first.symbol, format_expression(first.expression, width=None)) == (symbol, law)
    assert str(first.mathematical_type) == law_type
    assert (second.symbol, second.mathematical_type, second.identity) == (
        measure_symbol,
        first.mathematical_type,
        first.identity,
    )
    assert isinstance(second.expression, Measure)
    assert isinstance(second.expression.body, body_kind)


@pytest.mark.parametrize(
    "stage, identity, phrases",
    [
        pytest.param(
            "truncated_psi_stage",
            PSI_IDENTITY,
            (
                "measure on (0, ∞)",
                "Lebesgue",
                "0.5 ≤ exp(−σ_ψ²/2 + σ_ψ · z)",
                "exp(−σ_ψ²/2 + σ_ψ · z) ≤ 2",
                "∈ B",
            ),
            id="truncated-lognormal",
        ),
        pytest.param(
            "uniform_stage",
            Y_IDENTITY,
            ("Lebesgue", "1/(b_y − a_y)", "a_y", "b_y"),
            id="uniform",
        ),
        pytest.param(
            "truncated_normal_stage",
            Y_IDENTITY,
            ("Lebesgue", "μ_y + σ_y · z", "μ_y", "σ_y", "l_y", "u_y"),
            id="truncated-normal",
        ),
        pytest.param(
            "extreme_value_stage",
            Y_IDENTITY,
            ("Lebesgue", "exp(−z − exp(−z))", "μ_y", "s_y"),
            id="extreme-value",
        ),
        pytest.param("two_nodes_stage", Y_IDENTITY, ("0 + 1^(1/2) · z ∈ B",), id="normal"),
    ],
)
def test_the_measure_of_a_scalar_declaration_prints_its_definition_at_the_written_arguments(
    request, stage, identity, phrases
):
    """The printed measure of a scalar declaration holds parts of the
    family's definition with the written arguments in place of its
    variables, every named parameter among them."""
    denoted = request.getfixturevalue(stage).definitions.denote(identity).denoted
    printed = flat(denoted[1].expression)
    assert [phrase for phrase in phrases if phrase not in printed] == [], printed


@pytest.mark.parametrize(
    "text, origin, cut, identity",
    [
        # the block arvl_to_dcsn of the buffer-stock stage reads ψ
        pytest.param(
            "truncated_psi_text",
            "buffer_stock.bl",
            "dcsn_to_cntn",
            PSI_IDENTITY,
            id="truncated-lognormal",
        ),
        # the block dcsn_to_cntn of the two-node stage reads y
        pytest.param("uniform_text", DEFAULT_ORIGIN, "cntn_to_dcsn", Y_IDENTITY, id="uniform"),
        pytest.param(
            "truncated_normal_text",
            DEFAULT_ORIGIN,
            "cntn_to_dcsn",
            Y_IDENTITY,
            id="truncated-normal",
        ),
        pytest.param(
            "extreme_value_text",
            DEFAULT_ORIGIN,
            "cntn_to_dcsn",
            Y_IDENTITY,
            id="extreme-value",
        ),
    ],
)
def test_the_encoding_writes_the_two_objects_of_a_scalar_declaration_as_apply_and_measure(
    request, text, origin, cut, identity
):
    """The checked encoding of a stage text cut before the block `cut`, which
    keeps the declaration and the block that reads its shock, writes the two
    objects of the declaration as `semantic.Apply` and `semantic.Measure`."""
    alone = stage_from_text(text_before(request.getfixturevalue(text), cut), origin)
    encoding = validate_encoding(json.loads(json.dumps(alone.encoding())))
    stored = [entry["identity"] for entry in encoding["definitions"]]
    card = encoding["derived"]["definitions"][stored.index(identity)]
    denoted = [item["fields"]["expression"]["node"] for item in card["value"]["fields"]["denoted"]]
    assert denoted == ["semantic.Apply", "semantic.Measure"]


@pytest.mark.parametrize(
    "stage, identity, symbol, law_type, law",
    [
        pytest.param(
            "buffer_stock",
            "buffer_stock:distribution:ξ",
            "ξ",
            "probability measure on ℝ₊",
            "Mixture((p_zero, 0), (1 − p_zero, LogNormal(μ_ξ, σ_ξ)))",
            id="mixture",
        ),
        pytest.param(
            "truncated_mixture_stage",
            PSI_IDENTITY,
            "ψ",
            "probability measure on ℝ₊₊",
            "Mixture((p_zero, 1), (1 − p_zero, TruncatedLogNormal(−σ_ψ²/2, σ_ψ, 0.5, 2)))",
            id="mixture-with-a-truncated-component",
        ),
        # the vector and matrix parameters of a joint law are held as written
        pytest.param(
            "port",
            "port:distribution:Ψ_θ",
            "(Ψ, θ)",
            "probability measure on ℝ₊₊ × ℝ₊₊",
            "LogNormal((μ_Ψ, μ_θ), ((σ_Ψ², ρ_ζ · σ_Ψ · σ_θ), (ρ_ζ · σ_Ψ · σ_θ, σ_θ²)))",
            id="joint-lognormal-of-a-tuple-subject",
        ),
        pytest.param(
            "joint_normal_chain",
            EPSILON_IDENTITY,
            "ε",
            "probability measure on I_J → ℝ",
            "N(μ_ε, Σ_ε)",
            id="joint-normal-on-an-index-set",
        ),
        pytest.param(
            "tuple_argument_chain",
            EPSILON_IDENTITY,
            "ε",
            "probability measure on I_J → ℝ",
            "LogNormal((0, 1), 1)",
            id="tuple-argument-on-an-index-set",
        ),
    ],
)
def test_a_declaration_that_is_no_scalar_law_of_a_defined_family_denotes_its_law_alone(
    request, stage, identity, symbol, law_type, law
):
    """A mixture, a joint law of a tuple subject, and a law on an indexed
    shock that is no product of a scalar law denote one object, the law as
    the file writes it."""
    (denoted,) = request.getfixturevalue(stage).definitions.denote(identity).denoted
    assert isinstance(denoted.expression, Apply)
    assert (denoted.symbol, str(denoted.mathematical_type)) == (symbol, law_type)
    assert format_expression(denoted.expression, width=None) == law


def test_the_card_of_a_lognormal_declaration_prints_its_law_with_no_sentence_or_indicator(
    buffer_stock,
):
    """The card of `ψ ~ LogNormal(-(σ_ψ^2)/2, σ_ψ)` prints the law under
    `Defines`, with no textual item, which is a sentence printed in place of
    an expression, and no indicator function."""
    answer = buffer_stock.definitions.denote(PSI_IDENTITY)
    assert not any(isinstance(item.expression, Textual) for item in answer.denoted)
    card = str(answer)
    assert re.search(r"^Defines\n  ψ\s+~\s+", card, re.M) and "(−σ_ψ²/2, σ_ψ)" in card
    assert "indicator" not in card


def test_the_forward_card_of_a_mixture_with_a_truncated_component_extends_by_its_law(
    truncated_mixture_stage,
):
    """The card of the forward builders graph of the stage whose ψ is a
    mixture with a truncated lognormal component extends the measure by P_ψ
    on ℝ₊₊, the declared set of ψ, before the law of motion pushes the
    measure forward."""
    card = str(truncated_mixture_stage.builder.fwd.denote())
    phrases = (
        "DistributionExtension:ψ",
        "μ≺⊗P_ψ(B) = ∫_{k ∈ Xa} [P_ψ({ψ ∈ ℝ₊₊ | (k, ψ) ∈ B})] μ≺(dk)",
        "Pushforward",
    )
    assert [phrase for phrase in phrases if phrase not in card] == [], card


# the text of each scalar law of the two-node stage by its fixture, the law,
# and the position of its declaration among the items of the parsed file:
# `@stage`, β, R, y : ℝ and the parameter declarations stand before it
SCALAR_LAW_DECLARATIONS = [
    pytest.param("uniform_text", "Uniform(a_y, b_y)", 4 + 2, id="uniform"),
    pytest.param(
        "truncated_normal_text",
        "TruncatedNormal(μ_y, σ_y, l_y, u_y)",
        4 + 4,
        id="truncated-normal",
    ),
    pytest.param("extreme_value_text", "TypeIExtremeValue(μ_y, s_y)", 4 + 2, id="extreme-value"),
]


@pytest.mark.parametrize("text, law, position", SCALAR_LAW_DECLARATIONS)
def test_a_scalar_declaration_prints_to_source_as_written(request, text, law, position):
    """`to_source` prints the parsed declaration of y as the stage text
    writes it."""
    term = parse_with_spans(request.getfixturevalue(text), DEFAULT_ORIGIN).term
    assert to_source(term.items[position].core) == f"y ~ {law}"


@pytest.mark.parametrize(
    "text, position",
    [
        # `@stage`, β, R, y : ℝ and the parameter declarations stand before
        # the declaration of y
        pytest.param("uniform_text", 4 + 2, id="uniform"),
        pytest.param("truncated_normal_text", 4 + 4, id="truncated-normal"),
        pytest.param("extreme_value_text", 4 + 2, id="extreme-value"),
    ],
)
def test_the_source_of_a_scalar_declaration_parses_to_an_equal_core(request, text, position):
    """The text that `to_source` prints for the parsed declaration of y
    parses, in a stage of its own, to a core whose JSON form equals the
    declaration's."""
    declaration = parse_with_spans(request.getfixturevalue(text), DEFAULT_ORIGIN).term.items[
        position
    ]
    printed = to_source(declaration.core)
    reparsed = parse_with_spans("@stage: x\n" + printed + "\n").term.items[1]
    assert to_json(reparsed.core) == to_json(declaration.core)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("uniform_text", id="uniform"),
        pytest.param("truncated_normal_text", id="truncated-normal"),
        pytest.param("extreme_value_text", id="extreme-value"),
    ],
)
def test_the_parsed_file_of_a_scalar_law_reads_back_from_its_json_form_unchanged(request, text):
    """The parsed file of the stage text, with its source positions, written
    to JSON by `to_json` and read back by `from_json`, equals the parsed
    file."""
    term = parse_with_spans(request.getfixturevalue(text), DEFAULT_ORIGIN).term
    assert from_json(json.loads(json.dumps(to_json(term)))) == term


@pytest.mark.parametrize(
    "stage",
    [
        pytest.param("uniform_stage", id="uniform"),
        pytest.param("truncated_normal_stage", id="truncated-normal"),
        pytest.param("extreme_value_stage", id="extreme-value"),
    ],
)
def test_a_period_of_two_occurrences_of_a_stage_with_a_scalar_law_certifies_its_route(
    request, stage
):
    """A period of two occurrences of the calibrated stage, the continuation
    state a of the first joined to the arrival state k of the second,
    certifies its one route with no diagnostic."""
    stage = request.getfixturevalue(stage)
    period = {"stages": {"S": stage, "T": stage}, "connectors": [{"S.a": "T.k"}]}
    report = connection_report(elaborate_trellis({"periods": [period], "inter_connectors": []}))
    (route,) = report.selection.routes
    assert route.status == "certified", route.obligations
    assert [diagnostic.rule for diagnostic in report.selection.diagnostics] == []


@pytest.mark.parametrize("window", TRUNCATED_LOGNORMAL_WINDOWS)
def test_the_measure_of_a_truncated_lognormal_holds_its_window_and_its_image(
    truncated_lognormal_measures, window
):
    """The measure of `y ~ TruncatedLogNormal(μ, σ, l, u)` is a quotient of
    two integrals against Lebesgue measure whose regions hold the written
    endpoints l and u, the numerator's alone holding B, and whose image is
    exp(μ + σ·z)."""
    _, (mu, sigma, low, high) = TRUNCATED_LOGNORMAL_WINDOWS[window]
    measure = truncated_lognormal_measures[window]
    assert isinstance(measure, Measure) and isinstance(measure.body, Div)
    above, below = measure.body.left, measure.body.right
    assert isinstance(above, Integral) and isinstance(below, Integral)
    assert format_expression(below.measure) == "Lebesgue"
    (left, right), image = region(below.binding[1])
    assert (float(left), float(right)) == (low, high)
    assert region(above.binding[1])[0] == (left, right)
    assert "∈ B" in flat(above.binding[1]) and "∈ B" not in flat(below.binding[1])
    # the image is exp(μ + σ·z): its logarithm at z = 0 is μ, and at z = 1 is
    # μ + σ
    location = mpmath.log(number(image, 0))
    scale = mpmath.log(number(image, 1)) - location
    assert agree(location, mu) and agree(scale, sigma)


@pytest.mark.parametrize(
    "window, expected",
    [
        pytest.param(
            "two-sided",
            ((math.log(0.5) - 0.1) / 0.5, (math.log(2) - 0.1) / 0.5),
            id="two-sided",
        ),
        pytest.param("the-whole-half-line", (-math.inf, math.inf), id="the-whole-half-line"),
        pytest.param("one-sided", ((math.log(1) - 0.2) / 0.3, math.inf), id="one-sided"),
        pytest.param("far-tail", (9, 10), id="far-tail"),
    ],
)
def test_the_standardized_window_of_a_truncated_lognormal_is_its_log_window_in_sigmas(
    window, expected
):
    """`truncation.standardized_window` gives the window ((ln l − μ)/σ,
    (ln u − μ)/σ) of the standard-normal variable, −∞ at l = 0 and ∞ at
    u = inf."""
    _, (mu, sigma, low, high) = TRUNCATED_LOGNORMAL_WINDOWS[window]
    assert truncation.standardized_window(mu, sigma, low, high) == pytest.approx(expected)


@pytest.mark.parametrize(
    "lower, upper",
    [
        # the windows of the truncations of the lognormal law of y,
        # ((ln l − μ)/σ, (ln u − μ)/σ)
        pytest.param(
            (math.log(0.5) - 0.1) / 0.5,
            (math.log(2) - 0.1) / 0.5,
            id="lognormal-two-sided",
        ),
        pytest.param((math.log(1) - 0.2) / 0.3, math.inf, id="lognormal-one-sided"),
        pytest.param(-math.inf, math.inf, id="the-whole-line"),
        pytest.param(9, 10, id="far-tail"),
        # the windows of the truncations of the normal law of y,
        # ((l − μ)/σ, (u − μ)/σ)
        pytest.param(-1, 1, id="normal-symmetric"),
        pytest.param(0, math.inf, id="normal-one-sided"),
        # (1 − 2)/0.5 and (4 − 2)/0.5
        pytest.param(-2, 4, id="normal-nonstandard"),
        # a window below the mean, whose upper end is negative
        pytest.param(-2, -1, id="below-the-mean"),
    ],
)
def test_truncation_mass_is_the_standard_normal_probability_of_a_window(lower, upper):
    """`truncation.mass` gives a window of the standard-normal variable a
    positive probability, which agrees with the difference of two values of
    `mpmath.ncdf` at 40 digits."""
    mass = truncation.mass(lower, upper)
    with mpmath.workdps(40):
        exact = mpmath.ncdf(upper) - mpmath.ncdf(lower)
    assert mass > 0
    assert agree(mass, exact), (mass, exact)


def test_truncation_mass_keeps_the_far_tail_that_a_difference_of_two_erf_values_loses():
    """`truncation.mass` gives the window [9, 10] of the standard-normal
    variable the probability 1.1285·10⁻¹⁹."""
    assert math.isclose(truncation.mass(9, 10), 1.1285e-19, rel_tol=1e-4)
    # a check of the premise of the test, not of the package: the plain
    # difference of two values of erf gives the window the probability 0
    assert 0.5 * (math.erf(10 / math.sqrt(2)) - math.erf(9 / math.sqrt(2))) == 0.0


def test_truncation_mass_of_the_whole_line_is_exactly_one():
    """`truncation.mass` gives the whole line, the window of a truncated
    lognormal with the endpoints 0 and inf, the probability one exactly."""
    assert truncation.mass(-math.inf, math.inf) == 1.0


@pytest.mark.parametrize("window", TRUNCATED_LOGNORMAL_WINDOWS)
def test_a_truncated_lognormal_density_integrates_to_the_mass_of_its_window(
    truncated_lognormal_measures, window
):
    """The density of the denominator of the measure, integrated by
    `mpmath.quad` over the window that `truncation.standardized_window`
    gives, agrees with the standard normal probability of the window."""
    _, (mu, sigma, low, high) = TRUNCATED_LOGNORMAL_WINDOWS[window]
    below = truncated_lognormal_measures[window].body.right
    z_low, z_high = truncation.standardized_window(mu, sigma, low, high)
    # an infinite end of the window is integrated to 40 in standard units
    lowest = -40 if math.isinf(z_low) else z_low
    highest = 40 if math.isinf(z_high) else z_high
    with mpmath.workdps(40):
        exact = mpmath.ncdf(z_high) - mpmath.ncdf(z_low)
        retained = mpmath.quad(lambda z: number(below.body, z), [lowest, highest])
    assert agree(retained, exact), retained


@pytest.mark.parametrize("window", TRUNCATED_LOGNORMAL_WINDOWS)
def test_the_mean_of_a_truncated_lognormal_draw_is_its_closed_form(
    truncated_lognormal_measures, window
):
    """The mean of the draw, by quadrature of the image against the density
    over the window, agrees with exp(μ + σ²/2)·(Φ(z_u − σ) − Φ(z_l − σ))/Z,
    which is the lognormal mean exp(μ + σ²/2) at the endpoints 0 and inf."""
    _, (mu, sigma, low, high) = TRUNCATED_LOGNORMAL_WINDOWS[window]
    below = truncated_lognormal_measures[window].body.right
    _, image = region(below.binding[1])
    z_low, z_high = truncation.standardized_window(mu, sigma, low, high)
    mass = truncation.mass(z_low, z_high)
    # an infinite end of the window is integrated to 40 in standard units
    lowest = -40 if math.isinf(z_low) else z_low
    highest = 40 if math.isinf(z_high) else z_high
    with mpmath.workdps(40):
        exact = mpmath.ncdf(z_high) - mpmath.ncdf(z_low)
        drawn_mean = (
            mpmath.quad(lambda z: number(image, z) * number(below.body, z), [lowest, highest])
            / exact
        )
    closed = (
        math.exp(mu + sigma * sigma / 2) * truncation.mass(z_low - sigma, z_high - sigma) / mass
    )
    assert agree(drawn_mean, closed), (drawn_mean, closed)


def test_the_table_of_definitions_defines_the_truncated_lognormal_on_four_bindings():
    """The table of definitions defines `TruncatedLogNormal` on the bindings
    (m, s, l, u) as the measure on (0, ∞) that gives B the standard normal
    mass of the z with exp(m + s·z) in B and in [l, u], divided by the mass
    of the z with exp(m + s·z) in [l, u]."""
    definition = primitive_definition(TRUNCATED_LOGNORMAL)
    assert definition is not None
    expression = definition.equations[0]
    assert [name.identity.field for name, _ in expression.bindings] == ["m", "s", "l", "u"]
    printed = flat(expression)
    assert printed.startswith(
        "(m, s, l, u) ↦ measure on (0, ∞) given by B ↦ ∫_{z ∈ {z ∈ ℝ | exp(m + s · z) ∈ B ∧ "
        "l ≤ exp(m + s · z) ∧ exp(m + s · z) ≤ u}} [exp(−z²/2)/(2 · pi)^(1/2)] Lebesgue(dz)"
        "/∫_{z ∈ {z ∈ ℝ | l ≤ exp(m + s · z) ∧ exp(m + s · z) ≤ u}}"
    ), printed


def test_the_table_of_families_holds_the_truncated_lognormal_fifth_with_four_arguments():
    """The table of families holds `TruncatedLogNormal` fifth, after
    `TruncatedNormal`, taking four arguments."""
    assert list(FAMILY_ARGUMENTS)[:6] == [
        "N",
        "LogNormal",
        "Uniform",
        "TruncatedNormal",
        "TruncatedLogNormal",
        "TypeIExtremeValue",
    ]
    assert FAMILY_ARGUMENTS[TRUNCATED_LOGNORMAL].in_words() == "4 arguments"


def test_the_measure_of_a_uniform_law_integrates_over_its_interval_against_lebesgue_measure(
    uniform_measure,
):
    """The measure of `Uniform(0, 2)` is one integral against Lebesgue measure
    over the region with the endpoints 0 and 2, whose image is the bound
    variable itself."""
    assert isinstance(uniform_measure, Measure) and isinstance(uniform_measure.body, Integral)
    integral = uniform_measure.body
    assert format_expression(integral.measure) == "Lebesgue"
    (a, b), image = region(integral.binding[1])
    # the image of z = 1.25 is 1.25
    assert (a, b) == (0, 2) and number(image, 1.25) == 1.25


def test_the_density_of_a_uniform_law_is_constant_with_mass_one(uniform_measure):
    """The density of `Uniform(0, 2)` is the constant 1/2, whose mass over
    [a, b] = [0, 2] is (b − a)/(b − a) = 1."""
    integral = uniform_measure.body
    (a, b), _ = region(integral.binding[1])
    density = number(integral.body)
    assert density == 0.5
    assert density * (b - a) == 1


def test_the_mean_of_a_uniform_law_is_the_midpoint_of_its_interval(uniform_measure):
    """The mean of `Uniform(0, 2)`, by quadrature of x against its density
    over [a, b] = [0, 2], is (a + b)/2 = 1."""
    integral = uniform_measure.body
    (a, b), _ = region(integral.binding[1])
    mean = mpmath.quad(lambda x: x * number(integral.body, x), [a, b])
    assert agree(mean, (a + b) / 2) and agree(mean, 1)


@pytest.mark.parametrize("window", TRUNCATED_NORMAL_WINDOWS)
def test_the_measure_of_a_truncated_normal_holds_its_window_and_its_image(
    truncated_normal_measures, window
):
    """The measure of `y ~ TruncatedNormal(μ, σ, l, u)` is a quotient of two
    integrals against Lebesgue measure whose regions hold the written
    endpoints l and u, the numerator's alone holding B, and whose image is
    μ + σ·z."""
    _, (mu, sigma, low, high) = TRUNCATED_NORMAL_WINDOWS[window]
    measure = truncated_normal_measures[window]
    assert isinstance(measure, Measure) and isinstance(measure.body, Div)
    above, below = measure.body.left, measure.body.right
    assert isinstance(above, Integral) and isinstance(below, Integral)
    assert format_expression(below.measure) == "Lebesgue"
    (left, right), image = region(below.binding[1])
    assert (left, right) == (low, high) and region(above.binding[1])[0] == (low, high)
    assert "∈ B" in flat(above.binding[1]) and "∈ B" not in flat(below.binding[1])
    assert location_and_scale(image) == (mu, sigma)


@pytest.mark.parametrize("window", TRUNCATED_NORMAL_WINDOWS)
def test_a_truncated_normal_density_integrates_to_the_mass_of_its_window(
    truncated_normal_measures, window
):
    """The density of the denominator of the measure, integrated by
    `mpmath.quad` over the window [(l − μ)/σ, (u − μ)/σ] that its region and
    its image give, agrees with the standard normal probability of the
    window."""
    below = truncated_normal_measures[window].body.right
    (left, right), image = region(below.binding[1])
    location, scale = location_and_scale(image)
    lower, upper = (left - location) / scale, (right - location) / scale
    with mpmath.workdps(40):
        exact = mpmath.ncdf(upper) - mpmath.ncdf(lower)
        retained = mpmath.quad(lambda z: number(below.body, z), [lower, upper])
    assert agree(retained, exact), retained


def test_the_measure_of_an_extreme_value_law_integrates_its_density_at_an_affine_image(
    extreme_value_measure,
):
    """The measure of `TypeIExtremeValue(1.5, 2)` is one integral against
    Lebesgue measure of the density exp(−z − exp(−z)), whose region holds B
    at the image 1.5 + 2·z."""
    assert isinstance(extreme_value_measure, Measure)
    integral = extreme_value_measure.body
    assert isinstance(integral, Integral)
    assert format_expression(integral.measure) == "Lebesgue"
    assert flat(integral.body) == "exp(−z − exp(−z))"
    assert "1.5 + 2 · z ∈ B" in flat(integral.binding[1])
    _, image = region(integral.binding[1])
    assert location_and_scale(image) == (1.5, 2)


def test_the_extreme_value_density_has_the_heavier_tail_on_the_right(extreme_value_measure):
    """The density of `TypeIExtremeValue(1.5, 2)` at z = 3 exceeds its density
    at z = −3."""
    density, _, _ = density_and_image(extreme_value_measure.body)
    assert density(3) > density(-3)


def test_the_extreme_value_density_integrates_to_one(extreme_value_measure):
    """The density of `TypeIExtremeValue(1.5, 2)` integrates to one."""
    density, _, _ = density_and_image(extreme_value_measure.body)
    assert agree(mpmath.quad(density, [EXTREME_VALUE_LOW, 0, EXTREME_VALUE_HIGH]), 1)


@pytest.mark.parametrize(
    "x", [pytest.param(1.5, id="at-the-location"), pytest.param(4, id="at-four")]
)
def test_the_extreme_value_density_integrates_to_its_cumulative_distribution(
    extreme_value_measure, x
):
    """The density of `TypeIExtremeValue(1.5, 2)` integrated up to x gives the
    cumulative distribution exp(−exp(−(x − 1.5)/2)), which is exp(−1) at the
    location."""
    density, location, scale = density_and_image(extreme_value_measure.body)
    # x is the image of z = (x − location)/scale
    below_x = mpmath.quad(density, [EXTREME_VALUE_LOW, (x - location) / scale])
    assert agree(below_x, mpmath.exp(-mpmath.exp(-(x - 1.5) / 2)))


def test_the_mean_of_an_extreme_value_law_is_its_location_plus_euler_constant_times_scale(
    extreme_value_measure,
):
    """The mean of `TypeIExtremeValue(1.5, 2)`, by quadrature, is 1.5 + 2γ, γ
    Euler's constant, above the location 1.5."""
    density, location, scale = density_and_image(extreme_value_measure.body)
    mean = location + scale * mpmath.quad(
        lambda z: z * density(z), [EXTREME_VALUE_LOW, 0, EXTREME_VALUE_HIGH]
    )
    assert agree(mean, 1.5 + 2 * mpmath.euler) and mean > location


@pytest.mark.parametrize(
    "stage, shock, law",
    [
        pytest.param(
            "cons_savings_iid",
            "y",
            "y ~ Mixture((p_zero, point mass at 0), (1 - p_zero, LogNormal(μ_y, σ_y)))",
            id="mixture",
        ),
        pytest.param("buffer_stock", "ξ", "Mixture", id="mixture-with-a-derived-parameter"),
        pytest.param(
            "truncated_mixture_stage",
            "ψ",
            "TruncatedLogNormal",
            id="mixture-with-a-truncated-component",
        ),
        pytest.param("hafiscal", "z", "Categorical", id="categorical"),
        pytest.param("cons_portfolio", "Adjust", "Bernoulli", id="bernoulli"),
    ],
)
def test_a_mixture_categorical_or_bernoulli_shock_is_drawn_by_one_distribution_extension(
    request, stage, shock, law
):
    """The forward builders graph draws the shock by one distribution
    extension of the block `arvl_to_dcsn`, whose kernel writes the law."""
    stage = request.getfixturevalue(stage)
    extensions = [
        box.name
        for box in operators_of(stage, "forward")
        if box_identity(box).kind == "DistributionExtension"
        and box_identity(box).subjects == (shock,)
    ]
    assert extensions == [f"arvl_to_dcsn:DistributionExtension:{shock}"]
    assert law in kernel(stage, extensions[0])


@pytest.mark.parametrize(
    "stage, law, product",
    [
        pytest.param(
            "truncated_chain",
            "TruncatedLogNormal(0, 1, 0.5, 2)",
            "⊗_{i ∈ I_J} TruncatedLogNormal(0, 1, 0.5, 2)",
            id="truncated-lognormal",
        ),
        pytest.param(
            "extreme_value_chain",
            "TypeIExtremeValue(0, 1)",
            "⊗_{i ∈ I_J} TypeIExtremeValue(0, 1)",
            id="extreme-value",
        ),
        pytest.param(
            "lognormal_chain",
            "LogNormal(0, 1)",
            "⊗_{i ∈ I_J} LogNormal(0, 1)",
            id="lognormal",
        ),
    ],
)
def test_an_indexed_shock_with_a_scalar_law_denotes_the_product_of_the_law_over_its_index(
    request, stage, law, product
):
    """The declaration of ε : I_J → ℝ by a scalar law with real arguments
    denotes the product of that law over the declared index set I_J."""
    first, _ = request.getfixturevalue(stage).definitions.denote(EPSILON_IDENTITY).denoted
    assert isinstance(first.expression, ProductMeasure)
    assert format_expression(first.expression.binding[1]) == "I_J"
    assert format_expression(first.expression.body) == law
    assert flat(first.expression) == product


@pytest.mark.parametrize(
    "stage, body_kind, phrase",
    [
        pytest.param("truncated_chain", Div, "0.5 ≤ exp(0 + 1 · z)", id="truncated-lognormal"),
        pytest.param("extreme_value_chain", Integral, "[exp(−z − exp(−z))]", id="extreme-value"),
        pytest.param("lognormal_chain", Integral, "exp(0 + 1 · z) ∈ B", id="lognormal"),
    ],
)
def test_the_measure_of_an_indexed_shock_is_the_product_of_the_scalar_measure(
    request, stage, body_kind, phrase
):
    """The measure that the declaration of ε : I_J → ℝ by a scalar law
    denotes is the product of the scalar law's measure over the binding of
    the law's product."""
    first, second = request.getfixturevalue(stage).definitions.denote(EPSILON_IDENTITY).denoted
    assert isinstance(second.expression, ProductMeasure)
    assert second.expression.binding == first.expression.binding
    measure = second.expression.body
    assert isinstance(measure, Measure) and isinstance(measure.body, body_kind)
    assert phrase in flat(second.expression)


def test_an_indexed_shock_with_a_parent_denotes_a_product_law_given_the_parent(parent_chain):
    """`ε ~ TypeIExtremeValue(η, 1)` on ε : I_J → ℝ, η a parent shock,
    denotes the law `P_{ε|η}`, a function of η whose value is the product of
    `TypeIExtremeValue(η, 1)` over I_J."""
    first, _ = parent_chain.definitions.denote(EPSILON_IDENTITY).denoted
    assert first.symbol == "P_{ε|η}"
    assert isinstance(first.expression, Lambda)
    assert isinstance(first.expression.body, ProductMeasure)
    assert format_expression(first.expression.body.body) == "TypeIExtremeValue(η, 1)"


def test_the_measure_of_an_indexed_shock_with_a_parent_is_a_product_given_the_parent(
    parent_chain,
):
    """The measure that `ε ~ TypeIExtremeValue(η, 1)` on ε : I_J → ℝ denotes
    is a function of the parent η whose value is a product measure."""
    _, second = parent_chain.definitions.denote(EPSILON_IDENTITY).denoted
    assert isinstance(second.expression, Lambda)
    assert isinstance(second.expression.body, ProductMeasure)


@pytest.mark.parametrize(
    "calibrations",
    [
        pytest.param((CHAIN_CALIBRATION_J1,), id="J-is-1"),
        pytest.param((CHAIN_CALIBRATION_J2,), id="J-is-2"),
        pytest.param((CHAIN_CALIBRATION_J1, CHAIN_CALIBRATION_J2), id="J-is-2-after-J-is-1"),
    ],
)
def test_an_indexed_shock_takes_the_size_of_its_index_set_from_its_last_calibration(
    calibrations,
):
    """The chain stage with ε ~ TypeIExtremeValue(0, 1) on I_J, calibrated in
    turn by each of `calibrations` with no change of its text, binds the
    size J that the last of them gives."""
    stage = stage_from_text(EXTREME_VALUE_CHAIN_TEXT, "chain.bl")
    for calibration in calibrations:
        stage.calibrate(calibration)
    assert stage.par["J"].value == calibrations[-1]["J"]


def test_the_encoding_of_an_indexed_shock_writes_its_product_measure():
    """The checked encoding of the chain stage with
    ε ~ TypeIExtremeValue(0, 1) on I_J writes `semantic.ProductMeasure`."""
    stage = stage_from_text(EXTREME_VALUE_CHAIN_TEXT, "chain.bl")
    # the second calibration replaces the first
    stage.calibrate(CHAIN_CALIBRATION_J1)
    stage.calibrate(CHAIN_CALIBRATION_J2)
    encoding = validate_encoding(json.loads(json.dumps(stage.encoding())))
    assert '"semantic.ProductMeasure"' in json.dumps(encoding)


def test_the_product_density_integrates_over_a_rectangle_to_the_product_of_its_sides(
    extreme_value_chain,
):
    """The density of the scalar measure in the product of
    `TypeIExtremeValue(0, 1)`, integrated in two dimensions over the
    rectangle [−1, 1] × [0, 2], equals the product of its integrals over the
    two sides, (F(1) − F(−1))·(F(2) − F(0)), F(x) = exp(−exp(−x))."""
    _, second = extreme_value_chain.definitions.denote(EPSILON_IDENTITY).denoted
    density, location, scale = density_and_image(second.expression.body.body)

    def side(low, high):
        return mpmath.quad(density, [(low - location) / scale, (high - location) / scale])

    def cumulative(x):
        return mpmath.exp(-mpmath.exp(-x))

    rectangle = side(-1, 1) * side(0, 2)
    assert agree(rectangle, (cumulative(1) - cumulative(-1)) * (cumulative(2) - cumulative(0)))
    # the two-dimensional integral equals the product of the integrals over
    # the sides for every density, so that this statement checks the
    # quadrature of the test and no change of the package fails it
    joint = mpmath.quad(
        lambda u, w: density(u) * density(w),
        [(-1 - location) / scale, (1 - location) / scale],
        [(0 - location) / scale, (2 - location) / scale],
    )
    assert agree(joint, rectangle)


@pytest.mark.parametrize(
    "text, present, absent",
    [
        pytest.param(
            NORMAL_GIVEN_PARENT,
            ("z′ ∈ ℝ", "z + 1^(1/2) · z′"),
            ("z + 1^(1/2) · z ∈",),
            id="a-parent-z",
        ),
        pytest.param(
            two_nodes_text_with_law_of_y("Uniform(x, x + 1)", "x : ℝ\n"),
            ("{x′ ∈ ℝ | x′ ∈ B ∧ x ≤ x′ ∧ x′ ≤ x + 1}",),
            ("{x ∈ ℝ | x ∈ B",),
            id="a-parameter-x",
        ),
    ],
)
def test_a_bound_variable_of_a_definition_is_primed_where_an_argument_reads_its_name(
    text, present, absent
):
    """The measure of a declaration binds the variable of the family's
    definition under its name primed where a written argument reads that
    name, so that the argument keeps its own meaning."""
    printed = flat(measure_of(text))
    assert [phrase for phrase in present if phrase not in printed] == [], printed
    assert [phrase for phrase in absent if phrase in printed] == [], printed


def test_the_index_of_a_product_is_primed_where_the_law_reads_a_parameter_of_its_name():
    """The product of `ε ~ TypeIExtremeValue(i, 1)` on I_J, i a parameter,
    binds its index as i′."""
    text = changed(
        chain_text_with_law_of_epsilon("TypeIExtremeValue(i, 1)"),
        ("ε   : I_J", "i   : ℝ\nε   : I_J"),
    )
    product, _ = stage_from_text(text, "chain.bl").definitions.denote(EPSILON_IDENTITY).denoted
    assert flat(product.expression) == "⊗_{i′ ∈ I_J} TypeIExtremeValue(i, 1)"


def test_the_card_of_a_declaration_given_a_parent_lists_the_parents_declaration_once():
    """The card of the declaration of y, given its parent z, lists the
    declaration of z as its one definition."""
    card = stage_from_text(NORMAL_GIVEN_PARENT).definitions.denote(Y_IDENTITY)
    assert [str(item.identity) for item in card.definitions] == ["two_nodes:distribution:z"]


def test_the_measure_of_a_declaration_stands_on_its_own_record_alone(two_nodes_stage):
    """In the encoding of the two-node stage, the record of the declaration of
    y holds its law y and its measure P_y, while every record that lists the
    declaration lists it once, by its law y."""
    encoding = json.loads(json.dumps(two_nodes_stage.encoding()))
    listed = definition_lists(encoding["derived"])
    entries = [entry for found in listed for entry in found]
    reference = ("y", {"ref": "document", "id": Y_IDENTITY})
    assert reference in entries
    assert all(symbol != "P_y" for symbol, _ in entries), entries
    assert all(found.count(reference) <= 1 for found in listed)
    stored = [entry["identity"] for entry in encoding["definitions"]]
    held = encoding["derived"]["definitions"][stored.index(Y_IDENTITY)]["value"]["fields"]
    assert [item["fields"]["symbol"] for item in held["denoted"]] == ["y", "P_y"]
