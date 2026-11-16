"""Shock distributions: the conditions on a declaration, the refusal of
arguments outside a family's domain, the obligations that a stage records
and a calibration decides, the factorization of a joint law among them, the
support of a law against the declared set of its shock, and the weights of
a discrete law."""

import pytest
from application_files import BUFFER_STOCK_CALIBRATION_AT_R_1_04, COPIED_FILES_FOLDER, ROOT
from stage_builders import DEFAULT_ORIGIN, stage_from_text
from stage_texts import (
    CHAIN_CALIBRATION_J1,
    CHAIN_TEXT,
    PARENT_CHAIN_TEXT,
    PSI_IDENTITY,
    TRUNCATED_PSI_LAW,
    TWO_NODES_CALIBRATION,
    UNIFORM_ENDPOINTS_TEXT,
    Y_IDENTITY,
    chain_text_with_law_of_epsilon,
    changed,
    corpus_text,
    line_of,
    text_with_psi_law,
    two_nodes_text_with_changes,
    two_nodes_text_with_law_of_y,
)

from bellman.refusals import CONDITIONS, ConstructionError

# the law `TRUNCATED_PSI_LAW` with the endpoints the parameters l_ψ and u_ψ,
# which the pair ENDPOINT_DECLARATIONS declares on the line after the
# declaration of σ_ψ
TRUNCATED_ENDPOINTS = "TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ, l_ψ, u_ψ)"
SIGMA_PSI_DESCRIPTION = ':: ["standard deviation of the log permanent shock"]'
ENDPOINT_DECLARATIONS = (SIGMA_PSI_DESCRIPTION, SIGMA_PSI_DESCRIPTION + "\nl_ψ : ℝ₊\nu_ψ : ℝ₊")


# the calibration of the chain stage at J = 1 with the parameters of the
# joint normal law
JOINT_NORMAL_CALIBRATION = {
    **CHAIN_CALIBRATION_J1,
    "μ_ε": [0.0, 1.0],
    "Σ_ε": [[1.0, 0.5], [0.5, 2.0]],
}


def factorization_of(stage):
    """The sentence of the one obligation `joint-distribution-factorization`
    of `stage`."""
    (item,) = [
        item
        for item in stage.obligations()
        if item.condition == "joint-distribution-factorization"
    ]
    return item.explanation


def support_evidence(stage, shock):
    """The status and the evidence of the obligation `law-support` of the
    shock `shock` of the buffer-stock stage."""
    (item,) = [
        item
        for item in stage.obligations()
        if item.condition == "law-support" and str(item.entries[0]) == f"buffer_stock:shck:{shock}"
    ]
    return item.status, item.evidence


def held(stage, names):
    """The values that `stage` binds to the parameters `names`, and the
    condition and the sentence of each of its obligations."""
    return (
        [stage.par[name].value for name in names],
        [(item.condition, item.explanation) for item in stage.obligations()],
    )


@pytest.fixture(scope="module")
def truncated_endpoints_text(buffer_stock_file_text):
    """The buffer-stock stage text with `ψ ~ TRUNCATED_ENDPOINTS` and the two
    endpoints declared as parameters."""
    return text_with_psi_law(buffer_stock_file_text, TRUNCATED_ENDPOINTS, ENDPOINT_DECLARATIONS)


@pytest.fixture(scope="module")
def algan_ragot_money():
    """The returns stage of the corpus, whose productivity state e_n is drawn
    from the row of a named matrix that the current state selects."""
    path = f"{COPIED_FILES_FOLDER}/AlganRagotMoney/returns.bl"
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


def test_the_factorization_states_independent_components_only_for_a_product_law(
    extreme_value_chain, tuple_argument_chain
):
    """The sentence of `joint-distribution-factorization` states that the
    components of ε are independent draws of the scalar law where the law of
    ε is a product, not where a tuple argument makes it none."""
    product = factorization_of(extreme_value_chain)
    independent = "the components of ε are independent, each with the law TypeIExtremeValue(0, 1)"
    assert independent in product, product
    no_product = factorization_of(tuple_argument_chain)
    assert "the components of ε" not in no_product, no_product


def test_the_factorization_states_the_components_conditionally_independent_given_a_parent(
    parent_chain,
):
    """The sentence of `joint-distribution-factorization` for
    `ε ~ TypeIExtremeValue(η, 1)` states that the components of ε are
    conditionally independent given η, each with that law."""
    said = factorization_of(parent_chain)
    phrase = "the components of ε are conditionally independent given "
    assert phrase in said, said
    clause = said.split(phrase, 1)[1]
    assert clause.startswith("η") and "each with the law TypeIExtremeValue(η, 1)" in clause, said


def test_an_expectation_over_a_parent_inside_one_over_its_indexed_shock_is_refused():
    """With ε ~ TypeIExtremeValue(η, 1), the order E_{e_n, ε}(E_{η}(V)) is
    refused under `conditional-not-declared` at the line `dcsn_to_arvl.value`,
    since it needs the law of η given ε, where the order of
    `PARENT_CHAIN_TEXT` elaborates."""
    stage_from_text(PARENT_CHAIN_TEXT, "chain.bl")
    reversed_order = changed(PARENT_CHAIN_TEXT, ("E_{η}(E_{e_n, ε}(V))", "E_{e_n, ε}(E_{η}(V))"))
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(reversed_order, "chain.bl")
    error = refusal.value
    assert (error.rule, error.address) == ("conditional-not-declared", "dcsn_to_arvl.value")
    assert "needs the distribution of η given" in error.message, error.message


def test_a_normal_law_on_an_indexed_shock_takes_a_mean_vector_and_a_covariance_matrix():
    """The joint normal law `N(μ_ε, Σ_ε)` on ε : I_J → ℝ calibrates with a
    mean vector and a covariance matrix, where `N(0, 1)` on ε, with scalar
    arguments, is refused at calibration under `distribution-domain`."""
    joint = stage_from_text(CHAIN_TEXT, "chain.bl")
    assert joint.calibrate(JOINT_NORMAL_CALIBRATION).par["J"].value == 1
    scalar = stage_from_text(chain_text_with_law_of_epsilon("N(0, 1)"), "chain.bl")
    with pytest.raises(ConstructionError) as refusal:
        scalar.calibrate(CHAIN_CALIBRATION_J1)
    assert refusal.value.rule == "distribution-domain"


# the refusals of a truncated lognormal law of ψ: the law, the rule, and
# phrases of the message
TRUNCATED_LOGNORMAL_REFUSALS = [
    pytest.param(
        "TruncatedLogNormal(σ_ψ, 0, inf)",
        "readable-form",
        ("a call of 3 arguments", "4 arguments"),
        id="three-arguments",
    ),
    pytest.param(
        "TruncatedLogNormal(0, σ_ψ, 0, inf, 1)",
        "readable-form",
        ("a call of 5 arguments",),
        id="five-arguments",
    ),
    pytest.param(
        "TruncatedLogNormal(0, 0, 0, inf)",
        "distribution-domain",
        ("σ = 0", "not positive"),
        id="zero-sigma",
    ),
    pytest.param(
        "TruncatedLogNormal(0, -1, 0, inf)",
        "distribution-domain",
        ("σ = -1", "not positive"),
        id="negative-sigma",
    ),
    pytest.param(
        "TruncatedLogNormal(0, 1, -1, 1)",
        "distribution-domain",
        ("l = -1", "negative", "0 for no lower bound"),
        id="negative-lower-endpoint",
    ),
    pytest.param(
        "TruncatedLogNormal(0, 1, -inf, 1)",
        "distribution-domain",
        ("l = -inf", "negative"),
        id="lower-endpoint-minus-inf",
    ),
    pytest.param(
        "TruncatedLogNormal(0, 1, 2, 2)",
        "distribution-domain",
        ("l = 2 and u = 2", "not in order"),
        id="equal-endpoints",
    ),
    pytest.param(
        "TruncatedLogNormal(0, 1, 2, 1)",
        "distribution-domain",
        ("not in order",),
        id="reversed-endpoints",
    ),
    pytest.param(
        "TruncatedLogNormal(0, 1, inf, inf)",
        "distribution-domain",
        ("not in order",),
        id="both-endpoints-inf",
    ),
    pytest.param(
        "TruncatedLogNormal(inf, 1, 0, inf)",
        "distribution-domain",
        ("μ = inf", "not finite"),
        id="infinite-mu",
    ),
    pytest.param(
        "TruncatedLogNormal(0, inf, 0, inf)",
        "distribution-domain",
        ("σ = inf", "not finite"),
        id="infinite-sigma",
    ),
    pytest.param(
        "TruncatedLogNormal((0, 1), 1, 0, inf)",
        "distribution-domain",
        ("not a real number",),
        id="a-tuple-argument",
    ),
    pytest.param(
        "Mixture((p_zero, 1), (1 - p_zero, TruncatedLogNormal(0, 1, 2, 1)))",
        "distribution-domain",
        ("TruncatedLogNormal component of the Mixture declaration", "not in order"),
        id="a-mixture-component",
    ),
]


@pytest.mark.parametrize("law, rule, phrases", TRUNCATED_LOGNORMAL_REFUSALS)
def test_a_truncated_lognormal_with_arguments_the_family_does_not_take_is_refused(
    buffer_stock_file_text, law, rule, phrases
):
    """A truncated lognormal law of ψ with other than four arguments, or with
    an argument outside the family's domain, is refused under its rule with a
    message that names the fault."""
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(text_with_psi_law(buffer_stock_file_text, law), "buffer_stock.bl")
    message = refusal.value.message
    assert refusal.value.rule == rule, message
    assert [phrase for phrase in phrases if phrase not in message] == [], message


@pytest.mark.parametrize(
    "text, origin, identity, sentence",
    [
        pytest.param(
            "truncated_endpoints_text",
            "buffer_stock.bl",
            PSI_IDENTITY,
            "the parameters of the TruncatedLogNormal declaration buffer_stock:distribution:ψ "
            "of ψ lie in the family's domain: σ > 0 and 0 ≤ l < u, with μ = -σ_ψ^2/2 and "
            "σ = σ_ψ finite, l = l_ψ and u = u_ψ",
            id="truncated-lognormal-endpoints",
        ),
        pytest.param(
            "uniform_text",
            DEFAULT_ORIGIN,
            Y_IDENTITY,
            "the parameters of the Uniform declaration two_nodes:distribution:y of y lie in "
            "the family's domain: a < b, with a = a_y and b = b_y, both finite",
            id="uniform-endpoints",
        ),
    ],
)
def test_a_family_condition_on_named_parameters_is_retained_in_the_familys_words(
    request, text, origin, identity, sentence
):
    """A declaration whose arguments name parameters retains the family's
    condition on them as the one obligation
    `distribution-parameters-in-domain`, whose sentence states the condition
    in the written terms."""
    stage = stage_from_text(request.getfixturevalue(text), origin)
    (retained,) = [
        item
        for item in stage.obligations()
        if item.condition == "distribution-parameters-in-domain"
    ]
    assert [str(entry) for entry in retained.entries] == [identity]
    assert retained.explanation == sentence


@pytest.mark.parametrize(
    "law, changes, values, evidence",
    [
        pytest.param(
            TRUNCATED_PSI_LAW,
            (),
            BUFFER_STOCK_CALIBRATION_AT_R_1_04,
            "calibration σ_ψ = 0.1; the support [0.5, 2] lies within ℝ₊₊",
            id="two-sided",
        ),
        pytest.param(
            "TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ, 0, inf)",
            (),
            BUFFER_STOCK_CALIBRATION_AT_R_1_04,
            "calibration σ_ψ = 0.1; the support (0, inf) lies within ℝ₊₊",
            id="open-at-both-endpoints",
        ),
        pytest.param(
            "TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ, 0, 2)",
            (),
            BUFFER_STOCK_CALIBRATION_AT_R_1_04,
            "calibration σ_ψ = 0.1; the support (0, 2] lies within ℝ₊₊",
            id="open-at-a-lower-endpoint-zero",
        ),
        pytest.param(
            TRUNCATED_ENDPOINTS,
            (ENDPOINT_DECLARATIONS,),
            {**BUFFER_STOCK_CALIBRATION_AT_R_1_04, "l_ψ": 0.5, "u_ψ": 2.0},
            "calibration σ_ψ = 0.1, l_ψ = 0.5, u_ψ = 2.0; the support [0.5, 2] lies within ℝ₊₊",
            id="endpoints-as-parameters",
        ),
    ],
)
def test_calibration_establishes_the_support_of_a_truncated_lognormal_with_its_values(
    buffer_stock_file_text, law, changes, values, evidence
):
    """Calibration establishes the condition `law-support` of a truncated
    lognormal law of ψ, giving as evidence the values the law reads and its
    support [l, u], open at a lower endpoint 0 and at an upper endpoint inf,
    within the declared set ℝ₊₊."""
    stage = stage_from_text(
        text_with_psi_law(buffer_stock_file_text, law, *changes), "buffer_stock.bl"
    )
    assert support_evidence(stage.calibrate(values), "ψ") == ("established", (evidence,))


@pytest.mark.parametrize(
    "text, origin, declared, valid, refused, fault",
    [
        pytest.param(
            "truncated_endpoints_text",
            "buffer_stock.bl",
            "ψ ~ ",
            {**BUFFER_STOCK_CALIBRATION_AT_R_1_04, "l_ψ": 0.5, "u_ψ": 2.0},
            {**BUFFER_STOCK_CALIBRATION_AT_R_1_04, "l_ψ": 2.0, "u_ψ": 1.0},
            "not in order",
            id="truncated-lognormal-endpoints-reversed",
        ),
        pytest.param(
            "truncated_endpoints_text",
            "buffer_stock.bl",
            "ψ ~ ",
            {**BUFFER_STOCK_CALIBRATION_AT_R_1_04, "l_ψ": 0.5, "u_ψ": 2.0},
            {**BUFFER_STOCK_CALIBRATION_AT_R_1_04, "l_ψ": 0.5, "u_ψ": 2.0, "σ_ψ": 0.0},
            "not positive",
            id="truncated-lognormal-zero-sigma",
        ),
        pytest.param(
            "uniform_text",
            DEFAULT_ORIGIN,
            "y ~ ",
            {**TWO_NODES_CALIBRATION, "a_y": 0.0, "b_y": 1.0},
            {**TWO_NODES_CALIBRATION, "a_y": 1.0, "b_y": 0.0},
            "are not in order",
            id="uniform-endpoints-reversed",
        ),
    ],
)
def test_a_calibration_outside_a_familys_domain_is_refused_leaving_the_stage_as_it_was(
    request, text, origin, declared, valid, refused, fault
):
    """After a calibration inside the domain, a calibration whose values put
    the family's arguments outside it is refused under `distribution-domain`
    at the declaration's line, naming the calibration values, with the stage
    left holding the values of the earlier calibration."""
    text = request.getfixturevalue(text)
    stage = stage_from_text(text, origin)
    stage.calibrate(valid)
    before = held(stage, valid)
    with pytest.raises(ConstructionError) as refusal:
        stage.calibrate(refused)
    error = refusal.value
    address = f"{origin}:{line_of(text, declared)}"
    assert (error.rule, error.address) == ("distribution-domain", address)
    phrases = ("with the calibration values", fault)
    assert [phrase for phrase in phrases if phrase not in error.message] == [], error.message
    assert held(stage, valid) == before
    assert before[0] == list(valid.values())


def test_every_declaration_records_the_condition_law_support_as_required(buffer_stock_file_text):
    """Before calibration the buffer-stock stage records `law-support` for
    each of its two declarations, required, with the sentence that the
    distribution gives probability only to values in the declared set."""
    stage = stage_from_text(
        text_with_psi_law(buffer_stock_file_text, TRUNCATED_PSI_LAW), "buffer_stock.bl"
    )
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


def test_the_conditions_a_stage_states_hold_law_support_and_none_on_a_laws_provider():
    """`bellman.refusals.CONDITIONS`, the conditions that a stage states and
    its construction does not discharge, holds `law-support` and no
    condition `law-support-and-provider`, since the numerical routine that
    provides a law to a solver is no condition of the stage."""
    assert "law-support" in CONDITIONS and "law-support-and-provider" not in CONDITIONS


@pytest.mark.parametrize(
    "psi_law, shock",
    [
        # ψ is truncated, and the row reads ξ, the file's mixture of a point
        # mass at 0 and a lognormal law
        pytest.param(TRUNCATED_PSI_LAW, "ξ", id="mixture-of-a-point-mass-and-a-lognormal"),
        pytest.param(
            f"Mixture((p_zero, 1), (1 - p_zero, {TRUNCATED_PSI_LAW}))",
            "ψ",
            id="mixture-with-a-truncated-component",
        ),
    ],
)
def test_the_support_condition_of_a_law_other_than_a_truncated_lognormal_stays_required(
    buffer_stock_file_text, psi_law, shock
):
    """At calibration the condition `law-support` of the law of `shock`, a law
    other than a truncated lognormal, stays required, with no evidence."""
    stage = stage_from_text(text_with_psi_law(buffer_stock_file_text, psi_law), "buffer_stock.bl")
    calibrated = stage.calibrate(BUFFER_STOCK_CALIBRATION_AT_R_1_04)
    assert support_evidence(calibrated, shock) == ("required", ())


def test_calibration_refuses_a_truncated_lognormal_whose_support_leaves_the_declared_set(
    buffer_stock_file_text,
):
    """With ψ declared on [0.9, 1.1], a calibration of `ψ ~ TRUNCATED_PSI` is
    refused, since the support [0.5, 2] lies outside the declared set."""
    text = text_with_psi_law(
        buffer_stock_file_text, TRUNCATED_PSI_LAW, ("ψ : ℝ₊₊\n", "ψ : [0.9, 1.1]\n")
    )
    narrow = stage_from_text(text, "buffer_stock.bl")
    outside = r"\[0\.5, 2\], which lies outside the declared set \[0\.9, 1\.1\]"
    with pytest.raises(ValueError, match=outside):
        narrow.calibrate(BUFFER_STOCK_CALIBRATION_AT_R_1_04)


def test_the_support_of_a_law_is_decided_at_the_value_of_a_derived_parameter_it_reads():
    """The support of `ξ ~ TruncatedLogNormal(0, 0.1, 0.5, w)` is decided at
    the value of the derived parameter w := 2*Γ, which the evidence of an
    established `law-support` and the refusal of a support outside [0, 2]
    each name, where the derived parameter r := R - 1, whose name is a letter
    of the law's printed text, is named by neither."""
    text = (
        "@stage: t\nΓ : ℝ₊₊\nR : ℝ₊₊\nw := 2*Γ\nr := R - 1\nξ : [0, 2]\n"
        "ξ ~ TruncatedLogNormal(0, 0.1, 0.5, w)\n"
        "[id=arvl_to_dcsn, (k : ℝ, ξ) : !arvl -> (m : ℝ) : !dcsn] {\n    m = k + ξ\n}\n"
    )
    stage = stage_from_text(text)
    # Γ = 0.9 gives w = 1.8, within [0, 2]; Γ = 1.02 gives w = 2.04, outside
    stage.calibrate({"calibration": {"Γ": 0.9, "R": 1.04}})
    (support,) = [item for item in stage.obligations() if item.condition == "law-support"]
    assert support.status == "established"
    assert support.evidence[0] == "calibration w = 1.8; the support [0.5, 1.8] lies within [0, 2]"
    with pytest.raises(ValueError) as refusal:
        stage_from_text(text).calibrate({"calibration": {"Γ": 1.02, "R": 1.04}})
    assert "calibration w = 2.04 gives the distribution of ξ the support [0.5, 2.04]" in str(
        refusal.value
    )


def domain_refusal(law, *phrases, case):
    """A row of the refusals of the declaration `y ~ law` of the two-node
    stage under `distribution-domain`, whose message holds each of
    `phrases`."""
    return pytest.param(
        two_nodes_text_with_law_of_y(law), "distribution-domain", phrases, "y ~ ", id=case
    )


# the refusals of a declaration: the stage text, the rule, phrases of the
# message, and the start of the line of the declaration that is refused
DECLARATION_REFUSALS = [
    pytest.param(
        two_nodes_text_with_law_of_y("Uniform(1)"),
        "readable-form",
        ("`Uniform` takes 2 arguments",),
        "y ~ ",
        id="uniform-of-one-argument",
    ),
    domain_refusal(
        "Uniform(1, 0)", "are not in order", "a < b", case="uniform-endpoints-reversed"
    ),
    domain_refusal("Uniform(1, 1)", "are not in order", "a < b", case="uniform-endpoints-equal"),
    domain_refusal("Uniform(0, inf)", "which is not finite", case="uniform-infinite-endpoint"),
    domain_refusal(
        "TruncatedNormal(0, 0, -1, 1)", "which is not positive", case="truncation-zero-sigma"
    ),
    domain_refusal(
        "TruncatedNormal(0, -1, -1, 1)", "which is not positive", case="truncation-negative-sigma"
    ),
    domain_refusal(
        "TruncatedNormal(0, 1, 1, -1)", "are not in order", "l < u", case="truncation-reversed"
    ),
    domain_refusal(
        "TruncatedNormal(0, 1, inf, inf)",
        "are not in order",
        "l < u",
        case="truncation-both-endpoints-infinite",
    ),
    domain_refusal(
        "TruncatedNormal(0, 1, 2, 2)", "are not in order", "l < u", case="truncation-equal"
    ),
    domain_refusal(
        "TruncatedNormal(inf, 1, -1, 1)", "which is not finite", case="truncation-infinite-mu"
    ),
    domain_refusal(
        "TypeIExtremeValue(0, 0)", "which is not positive", case="extreme-value-zero-scale"
    ),
    domain_refusal(
        "Uniform(0/0, 1)", "has no number", "a division by zero", "0/0", case="division-by-zero"
    ),
    domain_refusal(
        "Uniform(0, 10^400)",
        "has no number",
        "a power beyond the floating-point range",
        case="an-overflowing-power",
    ),
    domain_refusal("Uniform(0, inf - inf)", "is not a number", case="not-a-number"),
    domain_refusal("Uniform((0, 1), 2)", "is not a real number", case="a-tuple-argument"),
    pytest.param(
        two_nodes_text_with_changes(declarations="z : ℝ\n(y, z) ~ Uniform(0, 1)\n"),
        "distribution-domain",
        ("one real subject",),
        "(y, z) ~",
        id="a-tuple-subject",
    ),
    pytest.param(
        two_nodes_text_with_law_of_y("Uniform(μ, 1)", "J : ℕ\nI_J := {0, …, J}\nμ : I_J → ℝ\n"),
        "distribution-domain",
        ("declared on", "a collection", "μ"),
        "y ~ ",
        id="a-parameter-declared-on-a-collection",
    ),
    domain_refusal(
        "Mixture((0.5, 0), (0.5, Uniform(1, 0)))",
        "component",
        "are not in order",
        case="a-uniform-component",
    ),
    domain_refusal("Mixture((0.5, 0), (0.5, N(0, -1)))", "component", case="a-normal-component"),
    pytest.param(
        two_nodes_text_with_changes(
            declarations="z : ℝ\n(y, z) ~ Mixture((0.5, N((0, 0), ((1, 0), (0, -1)))), "
            "(0.5, N((1, 1), ((1, 0), (0, 1)))))\n"
        ),
        "distribution-domain",
        ("N component of the Mixture declaration", "not positive semidefinite"),
        "(y, z) ~",
        id="a-joint-normal-component",
    ),
    domain_refusal(
        "Mixture((0.5, 0), (0.5, LogNormal(0, -1)))", "component", case="a-lognormal-component"
    ),
]


@pytest.mark.parametrize("text, rule, phrases, declared", DECLARATION_REFUSALS)
def test_a_declaration_with_arguments_or_a_subject_its_family_does_not_take_is_refused(
    text, rule, phrases, declared
):
    """A declaration with an argument or a subject outside its family's
    domain, or with a number of arguments the family does not take, is
    refused under its rule at the file position of the declaration, with a
    message that names the fault."""
    line = line_of(text, declared)
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(text)
    error = refusal.value
    assert (error.rule, error.address, error.line) == (rule, f"{DEFAULT_ORIGIN}:{line}", line), (
        str(error)
    )
    assert [phrase for phrase in phrases if phrase not in error.message] == [], error.message


def test_a_parameter_declared_on_a_product_set_is_refused_where_one_on_the_reals_is_not():
    """`Uniform(a_y, b_y)` with b_y declared on ℝ elaborates, and with b_y
    declared on the product set ℝ × ℝ, whose values are tuples and no real
    numbers, is refused under `distribution-domain` at the line of the
    declaration."""
    stage_from_text(UNIFORM_ENDPOINTS_TEXT)
    text = changed(UNIFORM_ENDPOINTS_TEXT, ("b_y : ℝ\n", "b_y : ℝ × ℝ\n"))
    line = line_of(text, "y ~ ")
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(text)
    error = refusal.value
    assert (error.rule, error.address, error.line) == (
        "distribution-domain",
        f"{DEFAULT_ORIGIN}:{line}",
        line,
    ), str(error)
    phrases = ("declared on ℝ × ℝ", "a product set")
    assert [phrase for phrase in phrases if phrase not in error.message] == [], error.message


def test_a_truncated_normal_far_in_the_tail_is_admitted_where_its_endpoints_are_in_order():
    """`TruncatedNormal(0, 1, 9, 10)` elaborates and calibrates, since the
    package checks only that the endpoints of a truncated normal law are in
    order, whatever the probability of the truncation interval, about 10⁻¹⁹
    here, whereas the same endpoints reversed are refused under
    `distribution-domain`."""
    stage = stage_from_text(two_nodes_text_with_law_of_y("TruncatedNormal(0, 1, 9, 10)"))
    assert stage.calibrate(TWO_NODES_CALIBRATION).par["β"].value == 0.96
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(two_nodes_text_with_law_of_y("TruncatedNormal(0, 1, 10, 9)"))
    assert refusal.value.rule == "distribution-domain", refusal.value.message


@pytest.mark.parametrize(
    "stage, identity, phrases",
    [
        pytest.param(
            "cons_savings_iid",
            "cons_savings_iid:distribution:y",
            ("in [0, 1]", "sum to one"),
            id="mixture",
        ),
        pytest.param(
            "cons_portfolio",
            "cons:distribution:Adjust",
            ("value 1 with probability", "in [0, 1]"),
            id="bernoulli",
        ),
        pytest.param(
            "algan_ragot_money",
            "returns:distribution:e_n",
            ("each row of", "sums to one"),
            id="categorical-of-the-rows-of-a-matrix",
        ),
    ],
)
def test_the_weights_of_a_discrete_law_are_recorded_as_one_obligation_in_words(
    request, stage, identity, phrases
):
    """The weights of a mixture, of a Bernoulli law and of a categorical law
    that selects a row of a named matrix stand as one obligation
    `distribution-weights-are-a-probability-vector`, whose sentence states
    the condition on them."""
    stage = request.getfixturevalue(stage)
    recorded = [item for item in stage.obligations() if "weight" in item.condition]
    assert [(item.condition, item.entries) for item in recorded] == [
        ("distribution-weights-are-a-probability-vector", (identity,))
    ]
    said = recorded[0].explanation
    assert [phrase for phrase in phrases if phrase not in said] == [], said


# the line of the consumption-savings stage file that writes the weights of
# the mixture of y, and the same mixture whose second weight is a parameter q
ONE_MINUS_P_ZERO_WEIGHT = "y ~ Mixture((p_zero, 0), (1 - p_zero, LogNormal(μ_y, σ_y)))"
PARAMETER_WEIGHT = "q : [0,1]\ny ~ Mixture((p_zero, 0), (q, LogNormal(μ_y, σ_y)))"


def test_mixture_weights_that_do_not_sum_to_one_are_refused_when_calibration_decides_them():
    """Weights that name parameters are retained as an obligation and decided
    at calibration, the weights 0.3 and 0.7 calibrating where 0.3 and 0.5 are
    refused under `distribution-domain` with the declaration named."""
    text = corpus_text("cons_savings_iid")
    assert text.count(ONE_MINUS_P_ZERO_WEIGHT) == 1
    stage = stage_from_text(text.replace(ONE_MINUS_P_ZERO_WEIGHT, PARAMETER_WEIGHT))
    assert [
        item.condition
        for item in stage.obligations()
        if item.condition == "distribution-weights-are-a-probability-vector"
    ]
    values = {"β": 0.96, "γ": 2.0, "R": 1.02, "μ_y": 0.0, "σ_y": 0.1, "p_zero": 0.3, "q": 0.7}
    stage.calibrate(values)  # 0.3 and 0.7 sum to one
    with pytest.raises(ConstructionError) as refusal:
        stage.calibrate({**values, "q": 0.5})
    error = refusal.value
    assert error.rule == "distribution-domain"
    phrases = ("p_zero, q", "the Mixture declaration `y ~ Mixture(", "sum to 0.8", "not to one")
    assert [phrase for phrase in phrases if phrase not in error.message] == [], error.message


def test_a_mixture_weight_written_outside_the_unit_interval_is_refused_at_construction():
    """A mixture whose first weight the file writes as the number 1.5 is
    refused when the stage is elaborated, before any calibration, under
    `distribution-domain`."""
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(
            "@stage: t\ny : ℝ\ny ~ Mixture((1.5, 0), (-0.5, N(0, 1)))\n"
            "[id=b, (x : ℝ, y) : !dcsn -> (w : ℝ) : !dcsn] {\n    w = x + y\n}\n"
        )
    message = refusal.value.message
    assert refusal.value.rule == "distribution-domain"
    phrases = ("the Mixture declaration `y ~ Mixture(", "1.5", "not a probability")
    assert [phrase for phrase in phrases if phrase not in message] == [], message


# a stage whose one block reads the shock z, with the declaration of z written
# in place of DECLARATION, on line 6 of the text
DISCRETE_MARKOV_STAGE = (
    "@stage: t\nz_lo : ℝ\nz_hi : ℝ\nΠ : [0,1]\nz : ℝ\nDECLARATION\n"
    "[id=b, (x : ℝ, z) : !dcsn -> (w : ℝ) : !dcsn] {\n    w = x + z\n}\n"
)


@pytest.mark.parametrize(
    "admitted, refused, counted",
    [
        pytest.param(
            "z ~ DiscreteMarkov(Π, (z_lo, z_hi))",
            "z ~ DiscreteMarkov((z_lo, z_hi))",
            "a call of 1 argument",
            id="one-argument-where-two-are-admitted",
        ),
        pytest.param(
            "z ~ DiscreteMarkov(Π, (z_lo, z_hi), x)",
            "z ~ DiscreteMarkov(Π, (z_lo, z_hi), x, x)",
            "a call of 4 arguments",
            id="four-arguments-where-three-are-admitted",
        ),
    ],
)
def test_a_discrete_markov_call_of_a_number_of_arguments_it_does_not_take_is_refused(
    admitted, refused, counted
):
    """`DiscreteMarkov` with two or with three arguments elaborates, where one
    or four arguments are refused under `readable-form` at the line of the
    declaration, with a message that names the arguments the family takes."""
    stage_from_text(DISCRETE_MARKOV_STAGE.replace("DECLARATION", admitted))
    with pytest.raises(ConstructionError) as refusal:
        stage_from_text(DISCRETE_MARKOV_STAGE.replace("DECLARATION", refused))
    message = refusal.value.message
    assert refusal.value.rule == "readable-form"
    assert refusal.value.address == "t.bl:6"
    phrases = (
        "the DiscreteMarkov declaration `z ~ DiscreteMarkov(",
        counted,
        "`DiscreteMarkov` takes 2 or 3 arguments",
        "the transition probabilities",
        "the chain's states",
        "the previous state",
    )
    assert [phrase for phrase in phrases if phrase not in message] == [], message
