"""The acceptance file of the brief "additional continuous shock
distributions" (Bellman-SYM specification 0.5; the second layer of the
tests, `packages/bellman/README.md` §8): one test for each of the brief's
acceptance items 1 to 6, the first five through the public calls of
construction, binding, denotation, export and connection, and the sixth on
the executed notebook. Every stage text is written here, since no corpus
stage declares the three families.

The rule. `y ~ Uniform(a, b)` is the uniform law on [a, b], with finite
a < b; `y ~ TruncatedNormal(μ, σ, l, u)` is the normal law of mean μ and
standard deviation σ conditioned on [l, u], with finite μ, finite σ > 0 and
extended-real l < u; `y ~ TypeIExtremeValue(μ, s)` is the maximum type-I
extreme-value law, whose cumulative distribution is exp(−exp(−(x − μ)/s)),
with finite μ and finite s > 0. A declaration of a scalar family the table
of definitions holds denotes two objects: the law as written, the family's
rule applied to the written arguments, and the measure at those arguments,
the rule's Lambda with them substituted. On a subject declared on a finite
index set, `ε : I_J → ℝ`, both are the finite product `⊗_{i ∈ I_J}` of the
scalar law, the conditionally independent components of ε. Invalid
arguments and subjects are refused under `distribution-domain` at the
declaration's file position; an argument that reads an unbound parameter
keeps its condition as the obligation `distribution-parameters-in-domain`,
decided at calibration.

The independent calculations use `math` and `mpmath` on the terms of the
retained measure: `number` below reads the arithmetic nodes of a term and
nothing of the package's own evaluation.

Not checked here: the documents that item 6 updates at merge; and the corpus
stages' printed snapshot and recorded encodings, whose named differences
(the family list of the `not-constructed` message and the second denoted
object of `N` and `LogNormal` declarations) `test_snapshot.py` and
`sym/test_corpus.py` compare.
"""

import json
import math
from typing import NamedTuple

import mpmath
import pytest
from conftest import NO_LAW, ROOT, stage_from_text, two_nodes

from bellman.display.encoding_checks import validate_encoding
from bellman.native import predicates as P
from bellman.refusals import ConstructionError, NotConstructed
from bellman.syntax import terms as T
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.syntax.source import to_source
from bellman.trellis import connection_report, elaborate_trellis
from bellman.typing import typed_expressions as S

ORIGIN = "t.bl"
Y = "two_nodes:distribution:y"
EPSILON = "chain:distribution:ε"
# the parameters of the two-node stage, bound in every calibration below
CALIBRATION = {"β": 0.96, "R": 1.03}
# the admitted families in the order of `FAMILY_ARGUMENTS`, which the
# `not-constructed` message lists
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

# The three scalar laws of item 1 on the shock y of the two-node stage: the
# parameter declarations, the law as written, valid values of the
# parameters, and a fragment the printed measure holds.
LAWS = {
    "Uniform": (
        "a_y : ℝ\nb_y : ℝ\n",
        "Uniform(a_y, b_y)",
        {"a_y": 0.0, "b_y": 1.0},
        "1/(b_y − a_y)",
    ),
    "TruncatedNormal": (
        "μ_y : ℝ\nσ_y : ℝ₊₊\nl_y : ℝ\nu_y : ℝ\n",
        "TruncatedNormal(μ_y, σ_y, l_y, u_y)",
        {"μ_y": 0.0, "σ_y": 1.0, "l_y": -1.0, "u_y": 2.0},
        "μ_y + σ_y · z",
    ),
    "TypeIExtremeValue": (
        "μ_y : ℝ\ns_y : ℝ₊₊\n",
        "TypeIExtremeValue(μ_y, s_y)",
        {"μ_y": 0.0, "s_y": 1.0},
        "exp(−z − exp(−z))",
    ),
}

# The chain stage of `tests/test_finite_indexed_data.py` (`CHAIN`), with
# the identifier of its line `x_n = x` written `same`: the state e_n is
# drawn from the row of Π at e_c and the vector ε on I_J from one joint
# normal law; the decision value is the component of ε at e_n.
CHAIN = """@stage: chain
J   : ℕ
I_J := {0, …, J}
β   : (0,1)
Π   : I_J × I_J → [0, 1]
μ_ε : I_J → ℝ
Σ_ε : I_J × I_J → ℝ
e_n : I_J
e_n ~ Categorical(Π[e_c])
ε   : I_J → ℝ
ε   ~ N(μ_ε, Σ_ε)

[id=arvl_to_dcsn, (e_c : I_J, e_n, ε) : !arvl -> (x : ℝ, e_d : I_J) : !dcsn] {
    x   = ε[e_n]    :: [id=draw]
    e_d = e_n       :: [id=state]
}

[id=dcsn_to_cntn, (x, e_d) : !dcsn -> (x_n : ℝ, e_nxt : I_J) : !cntn] {
    x_n   = x      :: [id=same]
    e_nxt = e_d    :: [id=state]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = x + β*V[>]    :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{e_n, ε}(V)    :: [id=value]
}
"""
# the calibrations of the chain at J = 1 and J = 2 without the parameters of
# the joint normal law, and the first with them
CHAIN_J1 = {"J": 1, "β": 0.9, "Π": [[0.9, 0.1], [0.2, 0.8]]}
CHAIN_J2 = {"J": 2, "β": 0.9, "Π": [[0.8, 0.1, 0.1], [0.2, 0.6, 0.2], [0.1, 0.1, 0.8]]}
NORMAL_J1 = {**CHAIN_J1, "μ_ε": [0.0, 1.0], "Σ_ε": [[1.0, 0.5], [0.5, 2.0]]}


def changed(text, *changes):
    """`text` with each `(written, replacement)` pair applied; a written
    fragment the text does not hold exactly once is refused, so that no
    change is lost."""
    for written, replacement in changes:
        assert text.count(written) == 1, written
        text = text.replace(written, replacement)
    return text


def drawn(law, parameters=""):
    """The two-node stage with `y ~ law`, the declarations `parameters`
    written before it."""
    return two_nodes(declarations=f"{parameters}y ~ {law}\nz : ℝ\nz ~ N(0,1)\n")


def indexed(law, parent=False, value="E_{e_n, ε}(V)"):
    """The chain stage with `ε ~ law` in place of the joint normal law and
    without its two parameters; with `parent`, the scalar shock η ~ N(0, 1)
    declared before ε; and with the arrival value `V[<] = value`."""
    shock = "η   : ℝ\nη   ~ N(0, 1)\n" if parent else ""
    return changed(
        CHAIN,
        ("μ_ε : I_J → ℝ\nΣ_ε : I_J × I_J → ℝ\n", ""),
        ("ε   : I_J → ℝ\nε   ~ N(μ_ε, Σ_ε)", f"{shock}ε   : I_J → ℝ\nε   ~ {law}"),
        ("E_{e_n, ε}(V)", value),
    )


def line_of(text, written):
    """The line of `text` that holds the first `written`, counted from 1."""
    return text[: text.index(written)].count("\n") + 1


def number(term, point=None):
    """The number, as an `mpmath` number, of an arithmetic term of a
    retained measure, its one bound variable at `point`: a name other than
    `inf`, `∞` and `pi` is the bound variable. A term that reads the
    variable where `point` is None raises LookupError."""
    if isinstance(term, T.Number):
        return mpmath.mpf(term.value)
    if isinstance(term, T.Neg):
        return -number(term.operand, point)
    if isinstance(term, T.Call):
        assert str(term.fun) == "external:exp", term
        (argument,) = term.args
        return mpmath.exp(number(argument, point))
    if isinstance(term, T.Sym):
        name = str(term.symbol.name)
        if name in ("inf", "∞"):
            return mpmath.inf
        if name == "external:pi":
            return mpmath.pi
        if point is None:
            raise LookupError(name)
        return mpmath.mpf(point)
    if isinstance(term, T.Pow):
        return number(term.base, point) ** number(term.exponent, point)
    left, right = number(term.left, point), number(term.right, point)
    return {
        T.Add: lambda: left + right,
        T.Sub: lambda: left - right,
        T.Mul: lambda: left * right,
        T.Div: lambda: left / right,
    }[type(term)]()


def conditions(condition):
    """The comparisons and memberships of a region's condition, a tuple of
    conditions or a conjunction."""
    if isinstance(condition, tuple):
        return [part for item in condition for part in conditions(item)]
    if isinstance(condition, P.And):
        return conditions(condition.left) + conditions(condition.right)
    return [condition]


def region(comprehension):
    """The endpoints of a region `{z ∈ ℝ | image ∈ B ∧ l ≤ image ∧ image ≤ u}`
    in increasing order, the numbers its comparisons compare the image with,
    and the image, the term of the bound variable that a membership or a
    comparison reads."""
    bounds, images = [], []
    for part in conditions(comprehension.conds):
        sides = (part.subject,) if isinstance(part, P.Member) else (part.left, part.right)
        for side in sides:
            try:
                bounds.append(number(side))
            except LookupError:
                images.append(side)
    return tuple(sorted(bounds)), images[0]


def location_and_scale(image):
    """The location m and the scale s of an affine image m + s·z."""
    m = number(image, 0)
    return m, number(image, 1) - m


def upper_tail(x):
    """The standard normal probability of (x, ∞), in floating point."""
    return 0.5 * math.erfc(float(x) / math.sqrt(2))


def second_object(text, origin=ORIGIN):
    """The measure the declaration of y in `text` denotes as its second
    object."""
    return stage_from_text(text, origin).definitions.denote(Y).denoted[1].expression


def agree(computed, expected):
    """Whether two numbers agree to a relative error of 10⁻⁹."""
    return math.isclose(float(computed), float(expected), rel_tol=1e-9)


def flat(expression):
    """The printed form of an expression on one line."""
    return " ".join(S.format_expression(expression).split())


def test_item_1_each_scalar_law_constructs_its_builders_and_denotes_the_law_and_its_measure():
    """For each of the three families on the shock y of the two-node stage,
    its arguments named parameters: the stage elaborates and calibrates at
    valid values; its forward and backward builders graphs are built, not
    held as refusals; a period of two occurrences of the stage, the
    continuation state a of the first written into the arrival state k of
    the second, certifies its route. The declaration denotes the law as
    written and, under the symbol `P_y` with the same type and identity, a
    measure on ℝ against Lebesgue measure that names every parameter. The
    declaration prints to source as written and its printed text parses to
    an equal core; the annotated AST round-trips through `to_json` and
    `from_json`; the stage's encoding passes the encoding checks and writes
    the declaration's two objects as `semantic.Apply` and
    `semantic.Measure`."""
    for family, (parameters, law, values, fragment) in LAWS.items():
        text = drawn(law, parameters)
        stage = stage_from_text(text)
        version = stage.calibrate({**CALIBRATION, **values})
        assert "dcsn_to_cntn" in str(version.builder.fwd.list()), family
        assert "cntn_to_dcsn" in str(version.builder.bwd.list()), family
        report = connection_report(
            elaborate_trellis(
                {
                    "periods": [
                        {"stages": {"S": stage, "T": stage}, "connectors": [{"S.a": "T.k"}]}
                    ],
                    "inter_connectors": [],
                }
            )
        )
        (route,) = report.selection.routes
        assert route.status == "certified", (family, route.obligations)
        assert [d.rule for d in report.selection.diagnostics] == [], family

        first, second = stage.definitions.denote(Y).denoted
        assert S.format_expression(first.expression) == law
        assert isinstance(second.expression, S.Measure), family
        assert (second.symbol, second.mathematical_type, second.identity) == (
            "P_y",
            first.mathematical_type,
            first.identity,
        )
        printed = flat(second.expression)
        assert "Lebesgue" in printed and fragment in printed, printed
        assert all(name in printed for name in values), printed

        term, _ = parse_with_spans(text, ORIGIN)
        # before the declaration: `@stage`, β, R, y : ℝ and the parameters
        declaration = term.items[4 + parameters.count("\n")]
        printed = to_source(declaration.core)
        assert printed == f"y ~ {law}"
        reparsed = parse_with_spans("@stage: x\n" + printed + "\n").term.items[1]
        assert to_json(reparsed.core) == to_json(declaration.core)
        assert from_json(json.loads(json.dumps(to_json(term)))) == term

        encoding = validate_encoding(json.loads(json.dumps(stage.encoding())))
        stored = [entry["identity"] for entry in encoding["definitions"]]
        card = encoding["derived"]["definitions"][stored.index(Y)]
        denoted = [item["fields"]["expression"] for item in card["value"]["fields"]["denoted"]]
        assert [expression["node"] for expression in denoted] == [
            "semantic.Apply",
            "semantic.Measure",
        ], family


# the truncations of item 2, (μ, σ, l, u): symmetric, one-sided, nonstandard,
# with two infinite endpoints, and the far tail l = μ + 9σ, u = μ + 10σ
TRUNCATIONS = (
    ("0, 1, -1, 1", (0, 1, -1, 1)),
    ("0, 1, 0, inf", (0, 1, 0, math.inf)),
    ("2, 0.5, 1, 4", (2, 0.5, 1, 4)),
    ("0, 1, -inf, inf", (0, 1, -math.inf, math.inf)),
    ("0, 1, 9, 10", (0, 1, 9, 10)),
)


def test_item_2_the_retained_measures_agree_with_independent_calculations():
    """The measure each literal declaration denotes, read from its terms.
    `Uniform(0, 2)`: an integral against Lebesgue measure over the region
    with the endpoints 0 and 2 of the density 1/2, whose mass over [a, b] is
    (b − a)/(b − a) = 1 and whose mean is (a + b)/2 = 1. Each
    `TruncatedNormal`: the quotient of two integrals against Lebesgue
    measure, whose regions hold the written endpoints and whose image is
    μ + σ·z; the normalizing mass Z, the standard normal probability of the
    window, computed in upper-tail form with `math.erfc`, agrees with
    `mpmath.ncdf` at 40 digits and with `mpmath.quad` of the retained
    density, and is positive; at the far tail Z ≈ 1.1285·10⁻¹⁹, where the
    difference of two values of `math.erf` gives 0.0. `TypeIExtremeValue(1.5,
    2)`: the density exp(−z − exp(−z)) of the image 1.5 + 2·z; its right
    tail is the heavier, the density at z = 3 exceeding that at z = −3; its
    mass is 1, its cumulative distribution at the location is exp(−1) and at
    x = 4 is exp(−exp(−(4 − 1.5)/2)), and its mean is 1.5 + 2γ, γ Euler's
    constant, so that the location is not the mean."""
    measure = second_object(drawn("Uniform(0, 2)"))
    assert isinstance(measure, S.Measure) and isinstance(measure.body, S.Integral)
    integral = measure.body
    assert S.format_expression(integral.measure) == "Lebesgue"
    (a, b), image = region(integral.binding[1])
    assert (a, b) == (0, 2) and number(image, 1.25) == 1.25
    density = number(integral.body)
    assert density == 0.5
    assert density * (b - a) == 1
    mean = mpmath.quad(lambda x: x * number(integral.body, x), [a, b])
    assert agree(mean, (a + b) / 2) and agree(mean, 1)

    for written, (mu, sigma, low, high) in TRUNCATIONS:
        measure = second_object(drawn(f"TruncatedNormal({written})"))
        assert isinstance(measure, S.Measure) and isinstance(measure.body, T.Div), written
        above, below = measure.body.left, measure.body.right
        assert isinstance(above, S.Integral) and isinstance(below, S.Integral), written
        assert S.format_expression(below.measure) == "Lebesgue"
        (left, right), image = region(below.binding[1])
        assert (left, right) == (low, high) and region(above.binding[1])[0] == (low, high), written
        assert "∈ B" in flat(above.binding[1]) and "∈ B" not in flat(below.binding[1])
        m, s = location_and_scale(image)
        assert (m, s) == (mu, sigma), written
        lower, upper = (left - m) / s, (right - m) / s
        mass = upper_tail(lower) - upper_tail(upper)
        with mpmath.workdps(40):
            exact = mpmath.ncdf(upper) - mpmath.ncdf(lower)
            retained = mpmath.quad(lambda z: number(below.body, z), [lower, upper])
        assert mass > 0, written
        assert agree(mass, exact), (written, mass, exact)
        assert agree(retained, exact), (written, retained)
    # the last truncation is the far tail [9, 10]
    assert math.isclose(mass, 1.1285e-19, rel_tol=1e-4), mass
    assert 0.5 * (math.erf(10 / math.sqrt(2)) - math.erf(9 / math.sqrt(2))) == 0.0

    measure = second_object(drawn("TypeIExtremeValue(1.5, 2)"))
    assert isinstance(measure, S.Measure) and isinstance(measure.body, S.Integral)
    integral = measure.body
    assert S.format_expression(integral.measure) == "Lebesgue"
    assert flat(integral.body) == "exp(−z − exp(−z))"
    assert "1.5 + 2 · z ∈ B" in flat(integral.binding[1])
    _, image = region(integral.binding[1])
    m, s = location_and_scale(image)
    assert (m, s) == (1.5, 2)

    def density(z):
        return number(integral.body, z)

    assert density(3) > density(-3)
    # [−8, 60] in standard units holds all the mass but less than 10⁻²⁶, and
    # quadrature over it avoids the overflow of exp(−z) far below −8
    lowest, highest = -8, 60
    assert agree(mpmath.quad(density, [lowest, 0, highest]), 1)
    # x = m is z = 0, and x = 4 is z = (4 − m)/s
    assert agree(mpmath.quad(density, [lowest, 0]), mpmath.exp(-1))
    at_4 = mpmath.quad(density, [lowest, (4 - m) / s])
    assert agree(at_4, mpmath.exp(-mpmath.exp(-(4 - 1.5) / 2)))
    mean = m + s * mpmath.quad(lambda z: z * density(z), [lowest, 0, highest])
    assert agree(mean, 1.5 + 2 * mpmath.euler) and mean > m


def test_item_3_an_indexed_shock_denotes_the_finite_product_of_its_scalar_law():
    """`ε ~ TypeIExtremeValue(0, 1)` on `ε : I_J → ℝ` denotes the product
    `⊗_{i ∈ I_J} TypeIExtremeValue(0, 1)` over the declared index set and,
    as its second object, the product of the measure over the same binding.
    The stage calibrates at J = 1 and at J = 2 without a change of its text;
    its encoding passes the checks and writes `semantic.ProductMeasure`; its
    factorization obligation states that the components of ε are
    conditionally independent, each with the scalar law. Under the product,
    the probability of the rectangle [−1, 1] × [0, 2] of two coordinates is
    (F(1) − F(−1))·(F(2) − F(0)), F(x) = exp(−exp(−x)), which `mpmath.quad`
    of the two-dimensional density over the rectangle, standardized by the
    location and scale of the retained image, gives too: the check verifies
    the product's stated meaning on rectangles on the retained scalar
    density. With the
    common parent η ~ N(0, 1) and `ε ~ TypeIExtremeValue(η, 1)`, the law is
    `P_{ε|η}`, a Lambda over η whose body is the product, and the
    factorization states the components' independence given η; an
    expectation over η outside one over ε elaborates, and the reversed
    order is refused under `conditional-not-declared`. The joint normal law
    on I_J keeps its meaning: it is no product and calibrates, and a scalar
    `N(0, 1)` on ε stays refused at calibration under `distribution-domain`."""
    stage = stage_from_text(indexed("TypeIExtremeValue(0, 1)"), "chain.bl")
    first, second = stage.definitions.denote(EPSILON).denoted
    product = first.expression
    assert isinstance(product, S.ProductMeasure)
    assert S.format_expression(product.binding[1]) == "I_J"
    assert S.format_expression(product.body) == "TypeIExtremeValue(0, 1)"
    assert flat(product) == "⊗_{i ∈ I_J} TypeIExtremeValue(0, 1)"
    assert isinstance(second.expression, S.ProductMeasure)
    assert second.expression.binding == product.binding
    measure = second.expression.body
    assert isinstance(measure, S.Measure) and isinstance(measure.body, S.Integral)
    for values in (CHAIN_J1, CHAIN_J2):
        assert stage.calibrate(values).par["J"].value == values["J"]
    encoding = validate_encoding(json.loads(json.dumps(stage.encoding())))
    assert '"semantic.ProductMeasure"' in json.dumps(encoding)
    (factorization,) = [
        item
        for item in stage.obligations()
        if item.condition == "joint-distribution-factorization"
    ]
    said = factorization.explanation
    assert "the components of ε are independent, each with the law TypeIExtremeValue(0, 1)" in (
        said
    ), said

    integral = measure.body
    _, image = region(integral.binding[1])
    m, s = location_and_scale(image)

    def density(z):
        return number(integral.body, z)

    def coordinate(low, high):
        return mpmath.quad(density, [(low - m) / s, (high - m) / s])

    def F(x):
        return mpmath.exp(-mpmath.exp(-x))

    rectangle = coordinate(-1, 1) * coordinate(0, 2)
    assert agree(rectangle, (F(1) - F(-1)) * (F(2) - F(0)))
    joint = mpmath.quad(
        lambda u, w: density(u) * density(w),
        [(-1 - m) / s, (1 - m) / s],
        [(0 - m) / s, (2 - m) / s],
    )
    assert agree(joint, rectangle)

    parent = stage_from_text(
        indexed("TypeIExtremeValue(η, 1)", parent=True, value="E_{η}(E_{e_n, ε}(V))"), "chain.bl"
    )
    first, second = parent.definitions.denote(EPSILON).denoted
    assert first.symbol == "P_{ε|η}"
    assert isinstance(first.expression, S.Lambda)
    assert isinstance(first.expression.body, S.ProductMeasure)
    assert S.format_expression(first.expression.body.body) == "TypeIExtremeValue(η, 1)"
    assert isinstance(second.expression, S.Lambda)
    assert isinstance(second.expression.body, S.ProductMeasure)
    (factorization,) = [
        item
        for item in parent.obligations()
        if item.condition == "joint-distribution-factorization"
    ]
    said = factorization.explanation
    phrase = "the components of ε are conditionally independent given "
    assert phrase in said, said
    clause = said.split(phrase, 1)[1]
    assert clause.startswith("η") and "each with the law TypeIExtremeValue(η, 1)" in clause, said
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            indexed("TypeIExtremeValue(η, 1)", parent=True, value="E_{e_n, ε}(E_{η}(V))"),
            "chain.bl",
        )
    error = refused.value
    assert (error.rule, error.address) == ("conditional-not-declared", "dcsn_to_arvl.value")
    assert "needs the distribution of η given" in error.message, error.message

    joint = stage_from_text(CHAIN, "chain.bl")
    (law,) = joint.definitions.denote(EPSILON).denoted
    assert not isinstance(law.expression, S.ProductMeasure)
    assert S.format_expression(law.expression) == "N(μ_ε, Σ_ε)"
    assert joint.calibrate(NORMAL_J1).par["J"].value == 1
    with pytest.raises(ConstructionError) as scalar_normal:
        stage_from_text(indexed("N(0, 1)"), "chain.bl").calibrate(CHAIN_J1)
    assert scalar_normal.value.rule == "distribution-domain"


class Refused(NamedTuple):
    """The refusal of an item 4 case: the text is refused when it is
    elaborated, under `rule`, at the file position of the line that holds
    `at`, the declaration; the message holds each of `words`."""

    rule: str
    words: tuple
    at: str = "y ~ "


class Bound(NamedTuple):
    """The item 4 case of the parameters a_y and b_y: the condition a < b is
    retained and decided at calibration."""


class Admitted(NamedTuple):
    """An item 4 text that elaborates and calibrates."""


def domain(law, *words, case):
    """An item 4 case of the law `law` on y, refused under
    `distribution-domain` with a message that holds each of `words`."""
    return pytest.param(drawn(law), Refused("distribution-domain", words), id=case)


ITEM_4 = [
    pytest.param(
        drawn("Uniform(1)"),
        Refused("readable-form", ("`Uniform` takes 2 arguments",)),
        id="uniform-of-one-argument",
    ),
    domain("Uniform(1, 0)", "are not in order", "a < b", case="uniform-endpoints-reversed"),
    domain("Uniform(1, 1)", "are not in order", "a < b", case="uniform-endpoints-equal"),
    domain("Uniform(0, inf)", "which is not finite", case="uniform-infinite-endpoint"),
    domain("TruncatedNormal(0, 0, -1, 1)", "which is not positive", case="truncation-zero-sigma"),
    domain(
        "TruncatedNormal(0, -1, -1, 1)", "which is not positive", case="truncation-negative-sigma"
    ),
    domain(
        "TruncatedNormal(0, 1, 1, -1)", "are not in order", "l < u", case="truncation-reversed"
    ),
    domain(
        "TruncatedNormal(0, 1, inf, inf)",
        "are not in order",
        "l < u",
        case="truncation-both-endpoints-infinite",
    ),
    domain("TruncatedNormal(0, 1, 2, 2)", "are not in order", "l < u", case="truncation-equal"),
    domain("TruncatedNormal(inf, 1, -1, 1)", "which is not finite", case="truncation-infinite-mu"),
    domain("TypeIExtremeValue(0, 0)", "which is not positive", case="extreme-value-zero-scale"),
    domain(
        "Uniform(0/0, 1)", "has no number", "a division by zero", "0/0", case="division-by-zero"
    ),
    domain(
        "Uniform(0, 10^400)",
        "has no number",
        "a power beyond the floating-point range",
        case="an-overflowing-power",
    ),
    domain("Uniform(0, inf - inf)", "is not a number", case="not-a-number"),
    domain("Uniform((0, 1), 2)", "is not a real number", case="a-tuple-argument"),
    pytest.param(
        two_nodes(declarations="z : ℝ\n(y, z) ~ Uniform(0, 1)\n"),
        Refused("distribution-domain", ("one real subject",), "(y, z) ~"),
        id="a-tuple-subject",
    ),
    pytest.param(
        drawn("Uniform(μ, 1)", "J : ℕ\nI_J := {0, …, J}\nμ : I_J → ℝ\n"),
        Refused("distribution-domain", ("declared on", "a collection", "μ")),
        id="a-parameter-declared-on-a-collection",
    ),
    domain(
        "Mixture((0.5, 0), (0.5, Uniform(1, 0)))",
        "component",
        "are not in order",
        case="a-uniform-component",
    ),
    domain("Mixture((0.5, 0), (0.5, N(0, -1)))", "component", case="a-normal-component"),
    pytest.param(
        two_nodes(
            declarations="z : ℝ\n(y, z) ~ Mixture((0.5, N((0, 0), ((1, 0), (0, -1)))), "
            "(0.5, N((1, 1), ((1, 0), (0, 1)))))\n"
        ),
        Refused(
            "distribution-domain",
            ("N component of the Mixture declaration", "not positive semidefinite"),
            "(y, z) ~",
        ),
        id="a-joint-normal-component",
    ),
    domain(
        "Mixture((0.5, 0), (0.5, LogNormal(0, -1)))", "component", case="a-lognormal-component"
    ),
    pytest.param(drawn("Uniform(a_y, b_y)", "a_y : ℝ\nb_y : ℝ\n"), Bound(), id="bound-endpoints"),
    pytest.param(drawn("TruncatedNormal(0, 1, 9, 10)"), Admitted(), id="a-far-tail-truncation"),
]


@pytest.mark.parametrize("text, expected", ITEM_4)
def test_item_4_invalid_arguments_and_subjects_are_refused_at_the_declaration(text, expected):
    """Each `Refused` text is refused when it is elaborated, under its rule
    at the declaration's file position: one argument of `Uniform` under
    `readable-form`; under `distribution-domain`, endpoints reversed or
    equal, finite or infinite, an infinite endpoint of `Uniform` and an
    infinite μ of a truncation, a zero or negative σ and a zero scale, an
    argument whose names are all valued and which has no number, a division
    by zero or an overflowing power, NaN, a tuple argument, a tuple subject,
    a parameter declared on a collection, and an invalid `Uniform`, `N` or
    `LogNormal` component of a mixture, a joint normal with a covariance that
    is not positive semidefinite among them, the refusal naming the
    component. With the
    parameters a_y and b_y the condition a < b is retained as the
    obligation `distribution-parameters-in-domain`; a calibration with
    a_y = 1 and b_y = 0, and one whose b_y, declared on ℝ × ℝ, is a list,
    are refused under `distribution-domain` at the declaration, after which
    the unbound stage and an earlier calibrated version are unchanged. The
    far-tail truncation [9, 10] elaborates and calibrates."""
    if isinstance(expected, Admitted):
        assert stage_from_text(text).calibrate(CALIBRATION).par["β"].value == 0.96
        return
    line = line_of(text, "y ~ " if isinstance(expected, Bound) else expected.at)
    address = f"{ORIGIN}:{line}"
    if isinstance(expected, Refused):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(text)
        error = refused.value
        assert (error.rule, error.address, error.line) == (expected.rule, address, line), str(
            error
        )
        for word in expected.words:
            assert word in error.message, (word, error.message)
        return
    stage = stage_from_text(text)
    (retained,) = [
        item
        for item in stage.obligations()
        if item.condition == "distribution-parameters-in-domain"
    ]
    assert [str(entry) for entry in retained.entries] == [Y]
    assert "Uniform" in retained.explanation
    assert "lie in the family's domain" in retained.explanation, retained.explanation
    valid = stage.calibrate({**CALIBRATION, "a_y": 0.0, "b_y": 1.0})

    def held():
        return (
            [stage.par[name].value for name in ("a_y", "b_y")],
            [(item.condition, item.explanation) for item in stage.obligations()],
            [valid.par[name].value for name in ("a_y", "b_y")],
        )

    before = held()
    with pytest.raises(ConstructionError) as reversed_endpoints:
        stage.calibrate({**CALIBRATION, "a_y": 1.0, "b_y": 0.0})
    error = reversed_endpoints.value
    assert (error.rule, error.address) == ("distribution-domain", address)
    assert "with the calibration values" in error.message, error.message
    assert "are not in order" in error.message, error.message
    # a parameter declared on a product set takes a tuple, no real number:
    # refused when the stage is read, as a parameter on a collection is
    with pytest.raises(ConstructionError) as paired:
        stage_from_text(changed(text, ("b_y : ℝ\n", "b_y : ℝ × ℝ\n")))
    error = paired.value
    assert (error.rule, error.address) == ("distribution-domain", address)
    assert "declared on ℝ × ℝ" in error.message and "a product set" in error.message, error.message
    assert held() == before
    assert before[2] == [0.0, 1.0]


def test_item_5_existing_families_mixtures_factorization_and_unknown_providers_keep_their_meaning(
    cons_savings_iid,
):
    """The corpus stage `cons_savings_iid` elaborates and keeps its
    obligation on the mixture's weights. The intended difference: the
    declaration `y ~ N(0, 1)` of the two-node stage denotes the law as
    written and, as its second object, the normal measure on ℝ at the
    written arguments, `B ↦ ∫_{z ∈ {z ∈ ℝ | 0 + 1^(1/2) · z ∈ B}} …`. The
    factorization obligation of the two separate declarations is the
    sentence of `tests/test_behaviour.py` unchanged. The stage `NO_LAW`,
    whose shock is written with the family `Weird`, has its forward builders
    graph refused under `not-constructed`, the message listing the ten
    admitted families in the table's order. An indexed `ε ~ LogNormal(0, 1)`
    on `ε : I_J → ℝ` now denotes the product of the scalar law, and
    `ε ~ LogNormal((0, 1), 1)`, whose tuple argument is no scalar law, denotes
    the law as written alone, no product, with no sentence on its components.

    A variable the family's definition binds is primed where a written
    argument or the conditioning point reads a name it shares: the measure
    of `y ~ N(z, 1)`, z a parent, integrates over `z′`, that of
    `y ~ Uniform(x, x + 1)`, x a parameter, over `x′`, and the index of the
    product of `ε ~ TypeIExtremeValue(i, 1)`, i a parameter, is `i′`. The
    measure at the written parameters stands on the declaration's own record
    alone: the records that read the declaration, the card of y given its
    parent z and every record of the stage's encoding, list it by its law,
    once."""
    conditions = [item.condition for item in cons_savings_iid.obligations()]
    assert "distribution-weights-are-a-probability-vector" in conditions

    independent = stage_from_text(two_nodes())
    first, second = independent.definitions.denote(Y).denoted
    assert S.format_expression(first.expression) == "N(0, 1)"
    assert isinstance(second.expression, S.Measure)
    assert "0 + 1^(1/2) · z ∈ B" in flat(second.expression), flat(second.expression)
    (factorization,) = [
        item
        for item in independent.obligations()
        if item.condition == "joint-distribution-factorization"
    ]
    assert factorization.entries == (Y, "two_nodes:distribution:z", "dcsn_to_cntn")
    assert factorization.explanation == (
        "The joint distribution for dcsn_to_cntn is assumed to be the product of the declared "
        "conditional distributions given their named parents and the source coordinates: y "
        "given (k_d, c) by two_nodes:distribution:y; z given (k_d, c) by "
        "two_nodes:distribution:z; y and z are conditionally independent given (k_d, c)."
    )

    with pytest.raises(NotConstructed) as refused:
        stage_from_text(NO_LAW, "no_law.bl").builder.fwd.list()
    assert refused.value.rule == "not-constructed"
    assert f"the families {', '.join(FAMILIES)};" in refused.value.message, refused.value.message

    lognormal = stage_from_text(indexed("LogNormal(0, 1)"), "chain.bl")
    first, second = lognormal.definitions.denote(EPSILON).denoted
    assert isinstance(first.expression, S.ProductMeasure)
    assert flat(first.expression) == "⊗_{i ∈ I_J} LogNormal(0, 1)"
    assert isinstance(second.expression, S.ProductMeasure)
    assert isinstance(second.expression.body, S.Measure)
    paired = stage_from_text(indexed("LogNormal((0, 1), 1)"), "chain.bl")
    (law,) = paired.definitions.denote(EPSILON).denoted
    assert isinstance(law.expression, S.Apply), flat(law.expression)
    (factorization,) = [
        item
        for item in paired.obligations()
        if item.condition == "joint-distribution-factorization"
    ]
    assert "the components of ε" not in factorization.explanation, factorization.explanation

    parent = stage_from_text(two_nodes(declarations="z : ℝ\nz ~ N(0,1)\ny ~ N(z, 1)\n"))
    card = parent.definitions.denote(Y)
    printed = flat(card.denoted[1].expression)
    assert "z′ ∈ ℝ" in printed and "z + 1^(1/2) · z′" in printed, printed
    assert "z + 1^(1/2) · z ∈" not in printed, printed
    printed = flat(second_object(drawn("Uniform(x, x + 1)", "x : ℝ\n")))
    assert "{x′ ∈ ℝ | x′ ∈ B ∧ x ≤ x′ ∧ x′ ≤ x + 1}" in printed, printed
    named_i = changed(indexed("TypeIExtremeValue(i, 1)"), ("ε   : I_J", "i   : ℝ\nε   : I_J"))
    (product, _) = stage_from_text(named_i, "chain.bl").definitions.denote(EPSILON).denoted
    assert flat(product.expression) == "⊗_{i′ ∈ I_J} TypeIExtremeValue(i, 1)"

    assert [str(item.identity) for item in card.definitions] == ["two_nodes:distribution:z"]
    listed = []

    def lists(value):
        """The `definitions` list of every encoded record, as the pairs of
        its entries' symbols and identities."""
        if isinstance(value, dict):
            held = value.get("fields")
            if isinstance(held, dict) and isinstance(held.get("definitions"), list):
                listed.append(
                    [(d["fields"]["symbol"], d["fields"]["identity"]) for d in held["definitions"]]
                )
            for item in value.values():
                lists(item)
        elif isinstance(value, list):
            for item in value:
                lists(item)

    encoding = json.loads(json.dumps(independent.encoding()))
    lists(encoding["derived"])
    entries = [entry for found in listed for entry in found]
    assert ("y", {"ref": "document", "id": Y}) in entries
    assert all(symbol != "P_y" for symbol, _ in entries), entries
    assert all(found.count(("y", {"ref": "document", "id": Y})) <= 1 for found in listed)
    stored = [entry["identity"] for entry in encoding["definitions"]]
    held = encoding["derived"]["definitions"][stored.index(Y)]["value"]["fields"]["denoted"]
    assert [item["fields"]["symbol"] for item in held] == ["y", "P_y"]


# the number of cells of the notebook tagged `raises-exception`, written by
# the notebook's author when the notebook is executed; None reads the count
# from the tags alone
RAISES = 11


def test_item_6_the_notebook_is_executed_and_keeps_its_two_reserved_cells():
    """The notebook of the brief stands in the verification folder of the
    internal records, executed: every code cell ran; an error output stands
    only in a cell tagged `raises-exception`, one per such cell; no output
    prints `False`, so every comparison of the notebook held when it was
    executed; and the last four cells are the reserved `### Observation` and
    `### Decision` cells, which record no personal acceptance. The notebook
    is found by its folder name, since no file outside the internal folder
    names a path under it; the test is skipped in a checkout without that
    folder."""
    found = sorted(
        ROOT.glob(
            "*/operations/verification/*/spec_0.5/2026-10-20-continuous-distributions/"
            "continuous-distributions.ipynb"
        )
    )
    if not found:
        pytest.skip("the notebook's folder is not in this checkout")
    (path,) = found
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    code = [cell for cell in cells if cell["cell_type"] == "code"]
    assert code and all(cell["execution_count"] for cell in code)
    refused = [cell for cell in code if "raises-exception" in cell["metadata"].get("tags", [])]
    assert refused and (RAISES is None or len(refused) == RAISES)
    for cell in code:
        errors = [output for output in cell["outputs"] if output["output_type"] == "error"]
        assert len(errors) == (1 if cell in refused else 0), "".join(cell["source"])
        for output in cell["outputs"]:
            shown = "".join(output.get("text", "")) + "".join(
                output.get("data", {}).get("text/plain", "")
            )
            assert "False" not in shown, "".join(cell["source"])
    assert [cell["cell_type"] for cell in cells[-4:]] == ["markdown"] * 4
    assert "".join(cells[-4]["source"]).strip() == "### Observation"
    assert "".join(cells[-2]["source"]).strip() == "### Decision"
