"""The acceptance file of AMD-SG-036, the truncated lognormal law (the second
layer of the tests, `packages/bellman/README.md` §8): one test per item of
its §6, on the buffer-stock stage with its permanent shock ψ declared by the
family, and on the two-node and chain stages of
`test_continuous_distributions.py` where a literal law is enough.

The rule. `ψ ~ TruncatedLogNormal(μ, σ, l, u)` is the lognormal law whose
logarithm has mean μ and standard deviation σ > 0, conditional on the
interval [l, u] of the draw itself, with 0 ≤ l < u, `0` and `inf` admitted;
the family is spelled as `TruncatedNormal(μ, σ, l, u)` is (CDC, 20 October
2026). The declaration denotes the law as written and its measure at the
written arguments; its builders are constructed; its arguments outside the
domain are refused under `distribution-domain`; and the condition
`law-support` is decided at calibration from the endpoints. The independent
calculations use `mpmath` on the terms of the retained measure, through the
readers of `test_continuous_distributions.py`.

Not checked here: the comparator's quadrature of the family, which
`packages/meaning-map-training/tests/test_stage_compare.py` compares; the
documents; and the corpus stages' recordings, whose one named difference,
the renamed condition, `test_snapshot.py` and `test_snapshot.py` compare.
"""

import json
import math

import mpmath
import pytest
from conftest import ROOT, stage_from_text
from test_continuous_distributions import (
    CHAIN_J1,
    EPSILON,
    agree,
    drawn,
    flat,
    indexed,
    number,
    region,
    second_object,
)

from bellman.display.encoding_checks import validate_encoding
from bellman.distributions import truncation
from bellman.distributions.families import FAMILY_ARGUMENTS, TRUNCATED_LOGNORMAL
from bellman.refusals import CONDITIONS, ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.typing import typed_expressions as S
from bellman.typing.primitive_definitions import primitive_definition

BUFFER_STOCK = ROOT / "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
LOGNORMAL_LINE = "ψ ~ LogNormal(-(σ_ψ^2)/2, σ_ψ)"
# the law of ψ in the items below: the mean-one location of the file, the
# file's σ_ψ, and the draw conditioned on [0.5, 2]; `to_source` writes the
# location without the file's parentheses
LAW = "TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ, 0.5, 2)"
WRITTEN = "TruncatedLogNormal(-σ_ψ^2/2, σ_ψ, 0.5, 2)"
PSI = "buffer_stock:distribution:ψ"
CALIBRATION = {
    "β": 0.96,
    "ρ": 2.0,
    "R": 1.04,
    "Γ": 1.03,
    "σ_ψ": 0.1,
    "σ_ξ": 0.1,
    "μ_ξ": -0.005,
    "p_zero": 0.005,
}


def text_with(law, **changes):
    """The buffer-stock stage text with ψ's law replaced by `law`, and any
    other fragment replaced as `changes` says; a fragment the text does not
    hold exactly once is refused."""
    text = BUFFER_STOCK.read_text(encoding="utf-8")
    assert text.count(LOGNORMAL_LINE) == 1
    text = text.replace(LOGNORMAL_LINE, "ψ ~ " + law)
    for old, new in changes.items():
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


def stage_with(law, **changes):
    """The stage of `text_with`, elaborated."""
    return stage_from_text(text_with(law, **changes), "buffer_stock.bl")


def law_of(stage, name):
    """The retained law of the shock `name`, as the record holds it."""
    record = next(
        d
        for d in stage.definitions.values()
        if d.kind == "distribution" and name in d.equations[0].subjects
    )
    return record.equations[0].law


def support_evidence(version):
    """The `law-support` obligation of ψ in a calibrated version: its status
    and its evidence."""
    item = next(
        item
        for item in version.obligations()
        if item.condition == "law-support" and str(item.entries[0]) == "buffer_stock:shck:ψ"
    )
    return item.status, item.evidence


def test_item_1_the_declaration_constructs_both_builders_and_denotes_the_law_and_its_measure():
    """The buffer-stock stage with `ψ ~ TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ,
    0.5, 2)` elaborates and calibrates; its forward and backward builders
    graphs are built. The record holds the law as written, and the
    declaration denotes two objects: the law as written, a probability
    measure on ℝ₊₊, and under `P_ψ` its measure at the written arguments, a
    quotient of two integrals against Lebesgue measure whose regions hold
    the endpoints and the parameter. The encoding passes the checks and
    writes the two objects as `semantic.Apply` and `semantic.Measure`."""
    stage = stage_with(LAW)
    assert to_source(law_of(stage, "ψ")) == WRITTEN
    assert "dcsn_to_cntn" in str(stage.builder.fwd.list())
    assert "cntn_to_dcsn" in str(stage.builder.bwd.list())
    first, second = stage.definitions.denote(PSI).denoted
    assert S.format_expression(first.expression, width=None) == (
        "TruncatedLogNormal(−σ_ψ²/2, σ_ψ, 0.5, 2)"
    )
    assert str(first.mathematical_type) == "probability measure on ℝ₊₊"
    assert (second.symbol, second.mathematical_type, second.identity) == (
        "P_ψ",
        first.mathematical_type,
        first.identity,
    )
    assert isinstance(second.expression, S.Measure)
    assert isinstance(second.expression.body, T.Div)
    printed = flat(second.expression)
    assert "measure on (0, ∞)" in printed and "Lebesgue" in printed, printed
    assert "0.5 ≤ exp(−σ_ψ²/2 + σ_ψ · z)" in printed and "exp(−σ_ψ²/2 + σ_ψ · z) ≤ 2" in printed
    assert "∈ B" in printed
    encoding = validate_encoding(json.loads(json.dumps(stage.encoding())))
    stored = [entry["identity"] for entry in encoding["definitions"]]
    card = encoding["derived"]["definitions"][stored.index(PSI)]
    denoted = [item["fields"]["expression"]["node"] for item in card["value"]["fields"]["denoted"]]
    assert denoted == ["semantic.Apply", "semantic.Measure"]
    calibrated = stage.calibrate(CALIBRATION)
    assert "dcsn_to_cntn" in str(calibrated.builder.fwd.list())


# the truncations of item 2, (μ, σ, l, u): two-sided, the whole half-line,
# one-sided, and the far tail [e⁹, e¹⁰], whose window in the standard-normal
# variable is [9, 10]
TRUNCATIONS = (
    ("0.1, 0.5, 0.5, 2", (0.1, 0.5, 0.5, 2.0)),
    ("0, 1, 0, inf", (0.0, 1.0, 0.0, math.inf)),
    ("0.2, 0.3, 1, inf", (0.2, 0.3, 1.0, math.inf)),
    ("0, 1, 8103.083927575384, 22026.465794806718", (0.0, 1.0, math.exp(9), math.exp(10))),
)


def test_item_2_the_retained_measure_agrees_with_independent_calculations():
    """The measure each literal declaration denotes, read from its terms: a
    quotient of two integrals against Lebesgue measure, whose regions hold
    the written endpoints l and u of the draw and whose image is
    exp(μ + σ·z). The normalizing mass, the standard normal probability of
    the window [(ln l − μ)/σ, (ln u − μ)/σ], computed in the tail form of
    `truncation.mass`, agrees with `mpmath.ncdf` at 40 digits and with
    `mpmath.quad` of the retained density, and is positive; the mean of the
    draw by quadrature of the image against the retained density agrees
    with exp(μ + σ²/2)·(Φ(z_u − σ) − Φ(z_l − σ))/Z. With the endpoints 0 and
    inf the law is `LogNormal(μ, σ)`: the mass is one and the mean
    exp(μ + σ²/2). At the far tail the mass is about 1.1285·10⁻¹⁹, where the
    difference of two values of `math.erf` gives 0.0."""
    for written, (mu, sigma, low, high) in TRUNCATIONS:
        measure = second_object(drawn(f"TruncatedLogNormal({written})"))
        assert isinstance(measure, S.Measure) and isinstance(measure.body, T.Div), written
        above, below = measure.body.left, measure.body.right
        assert isinstance(above, S.Integral) and isinstance(below, S.Integral), written
        assert S.format_expression(below.measure) == "Lebesgue"
        (left, right), image = region(below.binding[1])
        assert (float(left), float(right)) == (low, high), written
        assert region(above.binding[1])[0] == (left, right), written
        assert "∈ B" in flat(above.binding[1]) and "∈ B" not in flat(below.binding[1])
        # the image is exp(μ + σ·z): its logarithm at z = 0 is μ, and at
        # z = 1 is μ + σ
        m = mpmath.log(number(image, 0))
        s = mpmath.log(number(image, 1)) - m
        assert agree(m, mu) and agree(s, sigma), written
        z_low, z_high = truncation.standardized_window(mu, sigma, low, high)
        mass = truncation.mass(z_low, z_high)
        assert mass > 0, written
        lowest = -40 if math.isinf(z_low) else z_low
        highest = 40 if math.isinf(z_high) else z_high
        with mpmath.workdps(40):
            exact = mpmath.ncdf(z_high) - mpmath.ncdf(z_low)
            retained = mpmath.quad(lambda z: number(below.body, z), [lowest, highest])
            drawn_mean = mpmath.quad(
                lambda z: number(image, z) * number(below.body, z), [lowest, highest]
            ) / exact
        assert agree(mass, exact), (written, mass, exact)
        assert agree(retained, exact), (written, retained)
        closed = (
            math.exp(mu + sigma * sigma / 2)
            * truncation.mass(z_low - sigma, z_high - sigma)
            / mass
        )
        assert agree(drawn_mean, closed), (written, drawn_mean, closed)
        if (low, high) == (0.0, math.inf):
            assert mass == 1.0 and agree(drawn_mean, math.exp(mu + sigma * sigma / 2))
    # the last truncation is the far tail, the window [9, 10]
    assert math.isclose(mass, 1.1285e-19, rel_tol=1e-4), mass
    assert 0.5 * (math.erf(10 / math.sqrt(2)) - math.erf(9 / math.sqrt(2))) == 0.0


# the refusals of item 3: the law, the rule, and words of the message
REFUSED = (
    ("TruncatedLogNormal(σ_ψ, 0, inf)", "readable-form", ("a call of 3 arguments", "4 arguments")),
    ("TruncatedLogNormal(0, σ_ψ, 0, inf, 1)", "readable-form", ("a call of 5 arguments",)),
    ("TruncatedLogNormal(0, 0, 0, inf)", "distribution-domain", ("σ = 0", "not positive")),
    ("TruncatedLogNormal(0, -1, 0, inf)", "distribution-domain", ("σ = -1", "not positive")),
    (
        "TruncatedLogNormal(0, 1, -1, 1)",
        "distribution-domain",
        ("l = -1", "negative", "0 for no lower bound"),
    ),
    ("TruncatedLogNormal(0, 1, -inf, 1)", "distribution-domain", ("l = -inf", "negative")),
    ("TruncatedLogNormal(0, 1, 2, 2)", "distribution-domain", ("l = 2 and u = 2", "not in order")),
    ("TruncatedLogNormal(0, 1, 2, 1)", "distribution-domain", ("not in order",)),
    ("TruncatedLogNormal(0, 1, inf, inf)", "distribution-domain", ("not in order",)),
    ("TruncatedLogNormal(inf, 1, 0, inf)", "distribution-domain", ("μ = inf", "not finite")),
    ("TruncatedLogNormal(0, inf, 0, inf)", "distribution-domain", ("σ = inf", "not finite")),
    ("TruncatedLogNormal((0, 1), 1, 0, inf)", "distribution-domain", ("not a real number",)),
    (
        "Mixture((p_zero, 1), (1 - p_zero, TruncatedLogNormal(0, 1, 2, 1)))",
        "distribution-domain",
        ("TruncatedLogNormal component of the Mixture declaration", "not in order"),
    ),
)
# the endpoints as parameters, declared on the line after σ_ψ's
DESCRIBED = ':: ["standard deviation of the log permanent shock"]'
ENDPOINTS = {DESCRIBED: DESCRIBED + "\nl_ψ : ℝ₊\nu_ψ : ℝ₊"}


@pytest.mark.parametrize("law, rule, words", REFUSED + (("calibration", None, ()),))
def test_item_3_arguments_outside_the_domain_are_refused_when_written_and_at_calibration(
    law, rule, words
):
    """A call of three or of five arguments is refused under `readable-form`,
    the message naming "4 arguments". Refused under `distribution-domain`,
    at the declaration: σ zero or negative; a negative lower endpoint, `-inf`
    included, the message offering 0 for no lower bound; endpoints equal,
    reversed or both infinite; an infinite μ or σ; a tuple argument; and an
    invalid component of a mixture, the refusal naming the component. With
    the endpoints l_ψ and u_ψ as parameters the condition is retained as the
    obligation `distribution-parameters-in-domain` in the family's words; a
    calibration with the endpoints in order decides it, and one with them
    reversed, or with σ_ψ = 0, is refused under `distribution-domain` with
    the calibration values."""
    if law != "calibration":
        with pytest.raises(ConstructionError) as refused:
            stage_with(law)
        assert refused.value.rule == rule, refused.value.message
        for word in words:
            assert word in refused.value.message, (word, refused.value.message)
        return
    stage = stage_with("TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ, l_ψ, u_ψ)", **ENDPOINTS)
    (retained,) = [
        item
        for item in stage.obligations()
        if item.condition == "distribution-parameters-in-domain"
    ]
    assert [str(entry) for entry in retained.entries] == [PSI]
    assert retained.explanation == (
        "the parameters of the TruncatedLogNormal declaration buffer_stock:distribution:ψ of ψ "
        "lie in the family's domain: σ > 0 and 0 ≤ l < u, with μ = -σ_ψ^2/2 and σ = σ_ψ "
        "finite, l = l_ψ and u = u_ψ"
    )
    # a calibration with the endpoints in order is admitted; the retained
    # obligation is a sentence, which `calibrated_obligations` leaves as it
    # stands, as for the other three families
    valid = stage.calibrate({**CALIBRATION, "l_ψ": 0.5, "u_ψ": 2.0})
    assert support_evidence(valid) == (
        "established",
        ("calibration σ_ψ = 0.1, l_ψ = 0.5, u_ψ = 2.0; the support [0.5, 2] lies within ℝ₊₊",),
    )
    for values, word in (
        ({"l_ψ": 2.0, "u_ψ": 1.0}, "not in order"),
        ({"l_ψ": 0.5, "u_ψ": 2.0, "σ_ψ": 0.0}, "not positive"),
    ):
        with pytest.raises(ConstructionError) as refused:
            stage.calibrate({**CALIBRATION, **values})
        assert refused.value.rule == "distribution-domain"
        assert "with the calibration values" in refused.value.message
        assert word in refused.value.message, refused.value.message


def test_item_4_the_support_condition_is_recorded_for_every_law_and_decided_at_calibration():
    """`law-support` is a condition and `law-support-and-provider` is none.
    Every declaration records it, required, with the sentence of the fold.
    At calibration the truncated law's condition is established with the
    values and the support as evidence; the support is open at a lower
    endpoint 0 and at an upper endpoint inf; a declared set that excludes
    the support refuses the calibration; the lognormal's condition and that
    of a mixture with a truncated component stay required."""
    assert "law-support" in CONDITIONS and "law-support-and-provider" not in CONDITIONS
    stage = stage_with(LAW)
    recorded = {
        str(item.entries[0]): item
        for item in stage.obligations()
        if item.condition == "law-support"
    }
    assert set(recorded) == {"buffer_stock:shck:ψ", "buffer_stock:shck:ξ"}
    assert all(item.status == "required" for item in recorded.values())
    assert recorded["buffer_stock:shck:ξ"].explanation == (
        "The distribution of ξ gives probability only to values in the declared shock set."
    )
    calibrated = stage.calibrate(CALIBRATION)
    assert support_evidence(calibrated) == (
        "established",
        ("calibration σ_ψ = 0.1; the support [0.5, 2] lies within ℝ₊₊",),
    )
    assert [
        item.status for item in calibrated.obligations()
        if item.condition == "law-support" and str(item.entries[0]) == "buffer_stock:shck:ξ"
    ] == ["required"]
    whole = stage_with("TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ, 0, inf)").calibrate(CALIBRATION)
    assert support_evidence(whole) == (
        "established",
        ("calibration σ_ψ = 0.1; the support (0, inf) lies within ℝ₊₊",),
    )
    lower = stage_with("TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ, 0, 2)").calibrate(CALIBRATION)
    assert support_evidence(lower) == (
        "established",
        ("calibration σ_ψ = 0.1; the support (0, 2] lies within ℝ₊₊",),
    )
    narrow = stage_with(LAW, **{"ψ : ℝ₊₊\n": "ψ : [0.9, 1.1]\n"})
    outside = r"\[0\.5, 2\], which lies outside the declared set \[0\.9, 1\.1\]"
    with pytest.raises(ValueError, match=outside):
        narrow.calibrate(CALIBRATION)
    mixed = stage_with(f"Mixture((p_zero, 1), (1 - p_zero, {LAW}))").calibrate(CALIBRATION)
    assert support_evidence(mixed) == ("required", ())


def test_item_5_the_primitive_definition_defines_the_law_and_a_mixture_may_hold_it():
    """The table of definitions defines `TruncatedLogNormal` on the bindings
    (m, s, l, u) as a probability measure on (0, ∞): the quotient of the
    standard normal mass of the z with exp(m + s·z) in B and in [l, u] by
    the mass of the z with exp(m + s·z) in [l, u]. The family stands fifth
    in the table of families, after `TruncatedNormal`, and takes four
    arguments. A truncated component of a `Mixture` is recorded as written,
    the mixture's forward builder is constructed, and the component is
    pushed forward from (0, ∞) into ℝ as a lognormal component is."""
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
    assert list(FAMILY_ARGUMENTS)[:6] == [
        "N",
        "LogNormal",
        "Uniform",
        "TruncatedNormal",
        "TruncatedLogNormal",
        "TypeIExtremeValue",
    ]
    assert FAMILY_ARGUMENTS[TRUNCATED_LOGNORMAL].in_words() == "4 arguments"
    mixed = stage_with(f"Mixture((p_zero, 1), (1 - p_zero, {LAW}))")
    assert to_source(law_of(mixed, "ψ")) == f"Mixture((p_zero, 1), (1 - p_zero, {WRITTEN}))"
    assert "dcsn_to_cntn" in str(mixed.builder.fwd.list())
    assert "Pushforward" in str(mixed.builder.fwd.denote())
    [law] = mixed.definitions.denote(PSI).denoted
    assert S.format_expression(law.expression, width=None) == (
        "Mixture((p_zero, 1), (1 − p_zero, TruncatedLogNormal(−σ_ψ²/2, σ_ψ, 0.5, 2)))"
    )


def test_item_6_an_indexed_shock_takes_the_product_of_the_law():
    """`ε ~ TruncatedLogNormal(0, 1, 0.5, 2)` on `ε : I_J → ℝ` denotes the
    product `⊗_{i ∈ I_J} TruncatedLogNormal(0, 1, 0.5, 2)` over the declared
    index set and, as its second object, the product of the measure over
    the same binding; the stage calibrates at J = 1 and its forward builder
    is constructed, as for the other real-parameter families."""
    stage = stage_from_text(indexed("TruncatedLogNormal(0, 1, 0.5, 2)"))
    first, second = stage.definitions.denote(EPSILON).denoted
    assert isinstance(first.expression, S.ProductMeasure)
    assert flat(first.expression) == "⊗_{i ∈ I_J} TruncatedLogNormal(0, 1, 0.5, 2)"
    assert isinstance(second.expression, S.ProductMeasure)
    assert isinstance(second.expression.body, S.Measure)
    assert "0.5 ≤ exp(0 + 1 · z)" in flat(second.expression)
    version = stage.calibrate(CHAIN_J1)
    assert "dcsn_to_cntn" in str(version.builder.fwd.list())
