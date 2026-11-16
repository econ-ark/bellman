"""Derived parameters as a stage file writes them: a declared set on a
definition and its calibration, min and max, definitions by cases, the words
of a conditional, the refusals of a definition, and the records, cards and
kernel comments that print a definition."""

import math

import pytest
from application_files import (
    PERFECT_FORESIGHT_CALIBRATION,
    PERFECT_FORESIGHT_FILE,
    RETURN_IMPATIENCE_FAILING_CALIBRATION,
    ROOT,
)
from stage_builders import (
    calibration_refusal_sentence,
    methodized_copy,
    stage_from_text,
    undecided_memberships,
)
from stage_texts import (
    BETA_AND_R_DECLARATIONS,
    CONDITIONAL_PLACE,
    GROWTH_LINE,
    HUMAN_WEALTH_DEFINITION,
    HUMAN_WEALTH_RIGHT_SIDE_BY_CASES,
    IF_THEN_ELSE_REFUSAL,
    RESOURCES_LINE,
    changed,
    perfect_foresight_text,
    two_nodes_text_with_parameter_sets,
)

from bellman.factory.recipe import declared_parameters
from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import EXPLICIT_POLICY, TWO_NODES
from bellman.refusals import ConstructionError
from bellman.stage.sources import load_calibration
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.source import to_source

# the definition of q without a declared set, in place of the line of the
# stage file that begins `q : `
Q_WITHOUT_A_SET = {"q : ": "q := (β*R)^(1/ρ)/R"}


# the definition of the utility function in the perfect-foresight text of
# the module `bellman.refusal_examples`, which the fixture
# `derived_parameter_stages` reads
UTILITY = "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)                :: [id=util]"


# two definitions by cases on declared sets: human wealth in place of its
# definition, and q after the growth factor
CASES_ON_SETS = (
    (HUMAN_WEALTH_DEFINITION, f"h : (0, inf] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}"),
    (GROWTH_LINE, GROWTH_LINE + "q : (0, 3) := if β < R then 1 else 2\n"),
)


def perfect_foresight_file_text(replacements):
    """The text of the perfect-foresight stage file with the one line that
    begins with each key of `replacements` replaced by its value."""
    text = (ROOT / PERFECT_FORESIGHT_FILE).read_text(encoding="utf-8")
    for start, line in replacements.items():
        (old,) = [row for row in text.split("\n") if row.startswith(start)]
        text = text.replace(old, line)
    return text


def right_side(definition):
    """The right side of the one definition that a text writes, with or
    without a declared set, as the parser reads it."""
    term, _ = parse_with_spans(definition + "\n", "t.bl")
    item = term.items[0]
    return item.declaration.value if hasattr(item, "declaration") else item.core.value


def two_nodes_stage_with_lines(lines):
    """The symbolic two-node stage of the module `bellman.refusal_examples`
    with `lines`, each ending in a line break, declared after its two
    parameters β and R."""
    return stage_from_text(
        changed(TWO_NODES, (BETA_AND_R_DECLARATIONS, BETA_AND_R_DECLARATIONS + lines))
    )


@pytest.fixture(scope="module")
def patience_factor_text():
    """The perfect-foresight stage file with β declared on (0,1) and q
    defined on the declared set (0,1)."""
    return perfect_foresight_file_text({"β : ": "β : (0,1)", "q : ": "q : (0,1) := (β*R)^(1/ρ)/R"})


@pytest.fixture(scope="module")
def patience_factor_stage(patience_factor_text):
    """The symbolic stage of `patience_factor_text`; a test that binds it
    binds a copy."""
    return stage_from_text(patience_factor_text)


@pytest.fixture(scope="module")
def patience_factor_without_a_set():
    """The perfect-foresight stage file with β declared on (0,1) and q
    defined without a declared set; a test that binds it binds a copy."""
    return stage_from_text(perfect_foresight_file_text({"β : ": "β : (0,1)", **Q_WITHOUT_A_SET}))


@pytest.fixture(scope="module")
def cases_on_sets_text():
    """The perfect-foresight text with the two definitions `CASES_ON_SETS`."""
    return perfect_foresight_text(*CASES_ON_SETS)


@pytest.fixture(scope="module")
def cases_on_sets_stage(derived_parameter_stages):
    """The symbolic stage of `cases_on_sets_text`; a test that binds it
    binds a copy."""
    return derived_parameter_stages.stage(*CASES_ON_SETS)


@pytest.fixture(scope="module")
def min_and_max_stage(derived_parameter_stages):
    """The perfect-foresight stage with definitions that call min, max, log and
    exp, and a parameter on a set whose bound calls min."""
    lines = (
        "θ_min : (0, 1]",
        "ξ_u : ℝ₊",
        "x := min(ξ_u, θ_min*(1 - ξ_u))",
        "y := max(θ_min, ξ_u, 1/R)",
        "z := -min(ξ_u)*log(exp(2))",
        "q : (0, 3) := max(β, R)",
        "b : ℝ₊₊ @ (0, min(R, 2))",
    )
    return derived_parameter_stages.stage(
        (GROWTH_LINE, GROWTH_LINE + "".join(line + "\n" for line in lines))
    )


@pytest.fixture(scope="module")
def law_kernel_reading_q():
    """The kernel of the law of motion of the perfect-foresight stage file
    where q is defined on ℝ₊₊ and the law reads q."""
    stage = stage_from_text(
        perfect_foresight_file_text({"q : ": "q : ℝ₊₊ := R/Γ", "    m = ": "    m = q*k + 1"})
    )
    return stage.builder["arvl", "dcsn"]["Pushforward"].kernel()


@pytest.fixture(scope="module")
def explicit_policy_kernel(cases_on_sets_stage):
    """The kernel of the explicit policy's consumption line, which reads h."""
    stage = methodized_copy(
        cases_on_sets_stage, {"text": EXPLICIT_POLICY, "origin": "explicit_policy.bl"}
    )
    return stage.builder.policy.primitives["consumption:Aggregation"].kernel()


def test_a_definition_with_a_declared_set_defines_a_derived_parameter_that_carries_the_set(
    patience_factor_stage,
):
    """A definition on a declared set defines a derived parameter of the
    stage, whose record holds the set."""
    record = patience_factor_stage.par["q"]
    assert "q" in list(patience_factor_stage.par)
    assert record.derived and to_source(record.domain) == "(0, 1)"


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("patience_factor_text", id="a power on an interval"),
        pytest.param("cases_on_sets_text", id="two definitions by cases on intervals"),
    ],
)
def test_a_definition_with_a_declared_set_is_no_declared_parameter(text, request):
    """The declared parameters of a text, which a calibration supplies, leave
    out each derived parameter defined on a declared set."""
    assert declared_parameters(request.getfixturevalue(text), "t.bl") == ("β", "ρ", "R", "Γ")


@pytest.mark.parametrize(
    "second, first",
    [
        pytest.param(
            "x := if a ≤ b then ∞ else 1",
            "x := if a <= b then inf else 1",
            id="at most and the infinity",
        ),
        pytest.param(
            "x : ℝ̄ <- if a ≥ b then 1 else 2",
            "x : ℝ̄ := if a >= b then 1 else 2",
            id="at least after the left arrow",
        ),
    ],
)
def test_a_second_spelling_of_a_relation_or_of_the_infinity_is_read_as_the_first(second, first):
    """A definition written with the second spelling of a relation, of the
    infinity or of `:=` is read as the term of the first spelling."""
    assert (
        parse_with_spans(second + "\n", "t.bl").term == parse_with_spans(first + "\n", "t.bl").term
    )


@pytest.mark.parametrize(
    "stage, name, printed",
    [
        pytest.param(
            "patience_factor_stage",
            "q",
            "q : (0, 1) := (β*R)^(1/ρ)/R, unbound",
            id="a power on an interval",
        ),
        pytest.param(
            "min_and_max_stage",
            "y",
            "y := max(θ_min, ξ_u, 1/R), unbound",
            id="a call of max without a set",
        ),
        pytest.param(
            "min_and_max_stage",
            "q",
            "q : (0, 3) := max(β, R), unbound",
            id="a call of max on an interval",
        ),
        pytest.param(
            "min_and_max_stage",
            "b",
            "b : ℝ₊₊ @ (0, min(R, 2)), unbound",
            id="a declared parameter whose bound calls min",
        ),
        pytest.param(
            "cases_on_sets_stage",
            "q",
            "q : (0, 3) := if β < R then 1 else 2, unbound",
            id="a definition by cases on an interval",
        ),
    ],
)
def test_the_record_of_a_parameter_prints_its_declared_set_and_its_definition(
    stage, name, printed, request
):
    """The record of a parameter prints its declared set and its definition
    as the file writes them, before calibration."""
    assert str(request.getfixturevalue(stage).par[name]) == printed


@pytest.mark.parametrize(
    "stage, name, printed",
    [
        pytest.param(
            "patience_factor_stage",
            "q",
            "q     (0, 1) := (β*R)^(1/ρ)/R  unbound",
            id="a power on an interval",
        ),
        pytest.param(
            "cases_on_sets_stage",
            "q",
            "q     (0, 3) := if β < R then 1 else 2                unbound",
            id="a definition by cases on an interval",
        ),
        pytest.param(
            "patience_factor_stage",
            "h",
            "h     1/(1 - Γ/R)              unbound",
            id="a definition without a set",
        ),
    ],
)
def test_a_row_of_the_parameter_table_prints_the_declared_set_before_the_definition(
    stage, name, printed, request
):
    """A row of the parameter table prints a derived parameter's declared set,
    where it has one, before its definition."""
    table = str(request.getfixturevalue(stage).par)
    (row,) = [line for line in table.split("\n") if line.startswith(f"{name} ")]
    assert row.startswith(printed)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("β", id="a declared parameter"),
        pytest.param("q", id="a derived parameter on a set"),
        pytest.param("h", id="a derived parameter without a set"),
    ],
)
def test_each_row_of_the_parameter_list_holds_the_set_and_the_definition_of_its_record(
    name, patience_factor_stage
):
    """A row of `stage.par.list()` holds the set of its record under
    `domain` and the definition under `definition`, each a term or None."""
    rows = {row["name"]: row for row in patience_factor_stage.par.list()}
    record = patience_factor_stage.par[name]
    assert (rows[name]["domain"], rows[name]["definition"]) == (record.domain, record.definition)


def test_a_row_of_the_parameter_list_holds_a_definition_as_a_term(patience_factor_stage):
    """The definition that a row of `stage.par.list()` holds prints as the
    file writes it."""
    rows = {row["name"]: row for row in patience_factor_stage.par.list()}
    assert to_source(rows["q"]["definition"]) == "(β*R)^(1/ρ)/R"


def test_a_derived_parameter_whose_definition_declares_no_set_has_none(patience_factor_stage):
    """The record of a derived parameter whose definition declares no set
    holds no set and holds its definition."""
    record = patience_factor_stage.par["h"]
    assert record.domain is None and to_source(record.definition) == "1/(1 - Γ/R)"


def test_the_parameter_list_prints_as_the_parameter_table(patience_factor_stage):
    """`stage.par.list()` prints as the table `stage.par` prints."""
    assert str(patience_factor_stage.par.list()) == str(patience_factor_stage.par)


def test_the_header_of_the_parameter_table_writes_no_definition_sign(patience_factor_stage):
    """The first line of the parameter table, which names its columns,
    holds no `:=`."""
    assert ":=" not in str(patience_factor_stage.par).split("\n")[0]


@pytest.mark.parametrize(
    "stage, printed",
    [
        pytest.param(
            "patience_factor_stage", "q : (0, 1) := (β*R)^(1/ρ)/R", id="a power on an interval"
        ),
        pytest.param(
            "cases_on_sets_stage",
            "q : (0, 3) := if β < R then 1 else 2",
            id="a definition by cases on an interval",
        ),
    ],
)
def test_the_sheet_of_a_stage_prints_a_definition_with_its_declared_set(stage, printed, request):
    """The sheet of a stage, `stage.view()`, prints a derived parameter's
    declared set before its definition."""
    assert printed in request.getfixturevalue(stage).view()


@pytest.mark.parametrize(
    "stage, printed",
    [
        pytest.param(
            "patience_factor_stage",
            "q  ∈ (0, 1),  := (β · R)^(1/ρ)/R",
            id="a power on an interval",
        ),
        pytest.param(
            "cases_on_sets_stage",
            "  q  ∈ (0, 3),  := if β < R then 1 else 2\n",
            id="a definition by cases on an interval",
        ),
    ],
)
def test_the_card_of_a_definition_prints_its_declared_set(stage, printed, request):
    """The card of the record of q in the definitions table prints the set
    that its definition declares, then the definition."""
    definitions = request.getfixturevalue(stage).definitions
    assert printed in str(definitions.denote("perfect_foresight:derived:q"))


# the row of the explicit policy prints a set closed at the infinity
@pytest.mark.parametrize(
    "kernel, definition",
    [
        pytest.param("law_kernel_reading_q", "q : ℝ₊₊ := R/Γ", id="a law of motion"),
        pytest.param(
            "explicit_policy_kernel",
            f"h : (0, inf] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
            id="an explicit policy",
        ),
    ],
)
def test_the_comment_line_of_a_kernel_prints_the_definition_it_reads_with_its_set(
    kernel, definition, request
):
    """A kernel that reads a derived parameter names it in a comment line
    with its declared set and its definition."""
    assert f"# derived parameter: {definition}\n" in request.getfixturevalue(kernel).python


def test_the_parameter_table_lists_the_parameters_in_the_order_of_the_file(cases_on_sets_stage):
    """The parameter table lists the declared parameters, then the derived
    parameters in the order of the file."""
    assert list(cases_on_sets_stage.par) == ["β", "ρ", "R", "Γ", "q", "h", "R_n"]


def test_a_declared_set_is_no_argument_of_a_derived_parameter_that_a_line_differentiates():
    """A value line that differentiates q by c prints the same with and
    without a declared set on q, and writes q as no function of c."""
    texts = [
        perfect_foresight_file_text({"    V = ": "    V = 𝑢(c) + β*V[>] + D_{c}(q)", **definition})
        for definition in (Q_WITHOUT_A_SET, {"q : ": "q : ℝ₊₊ := (β*R)^(1/ρ)/R"})
    ]
    differentiated = [
        str(stage_from_text(text).builder["cntn", "dcsn"].denote()) for text in texts
    ]
    assert differentiated[0] == differentiated[1] and "q(c)" not in differentiated[1]


def test_calibration_holds_a_derived_parameter_to_its_declared_set(patience_factor_stage):
    """Calibration admits a value of q inside its declared set, refuses one
    outside it with the values that q reads and what to write, and holds a
    definition of q without a set to no set."""
    bound = copy_native(patience_factor_stage).calibrate(PERFECT_FORESIGHT_CALIBRATION)
    # βR = 1 at this calibration, so that q = (βR)^(1/ρ)/R = 1/R = 1/1.04
    assert bound.par["q"].value == pytest.approx(0.9615384615384615)
    assert undecided_memberships(bound) == []
    sentence = calibration_refusal_sentence(
        patience_factor_stage, RETURN_IMPATIENCE_FAILING_CALIBRATION
    )
    words = ("derived parameter 'q'", "(β*R)^(1/ρ)/R", "(0, 1)", "β = 0.99", "R = 0.9", "ρ = 2.0")
    assert [word for word in words if word not in sentence] == []
    # the parameters that the definition reads stand in the order of the file
    assert sentence.endswith(
        "lies outside the declared set (0, 1) at β = 0.99, ρ = 2.0, R = 0.9; a derived "
        "parameter's value lies in the set its definition declares; write values of β, ρ and R "
        "at which q lies in (0, 1)"
    ), sentence
    # q := 1, defined without a set, takes the value 1, outside (0, 1)
    constant = stage_from_text(
        perfect_foresight_file_text({"β : ": "β : (0,1)", "q : ": "q := 1"})
    )
    assert (
        copy_native(constant).calibrate(RETURN_IMPATIENCE_FAILING_CALIBRATION).par["q"].value == 1
    )


def test_a_calibration_that_supplies_a_value_for_a_derived_parameter_on_a_set_is_refused(
    patience_factor_stage,
):
    """A calibration that supplies a value for q, defined on a declared set,
    is refused under `derived-parameter`."""
    with pytest.raises(ConstructionError) as refused:
        copy_native(patience_factor_stage).calibrate({**PERFECT_FORESIGHT_CALIBRATION, "q": 0.5})
    assert refused.value.rule == "derived-parameter"


def test_a_declared_set_of_a_derived_parameter_bounds_a_product_of_two_parameters():
    """A derived parameter β*R on the set (1, inf) is admitted where the
    product exceeds one and refused where it does not."""
    assert TWO_NODES.count(BETA_AND_R_DECLARATIONS) == 1
    product = two_nodes_stage_with_lines("q : (1, inf) := β*R\n")
    assert undecided_memberships(copy_native(product).calibrate({"β": 2.0, "R": 3.0})) == []
    with pytest.raises(ValueError, match="derived parameter 'q'"):
        copy_native(product).calibrate({"β": 0.5, "R": 1.0})


def test_a_declared_set_whose_bound_no_calibration_decides_leaves_the_membership_open():
    """A declared set whose bound is an expectation leaves the membership of
    the derived parameter's value open after calibration."""
    open_set = two_nodes_stage_with_lines("q : (0, E_{y}(y^2)) := β*R\n")
    assert undecided_memberships(copy_native(open_set).calibrate({"β": 2.0, "R": 3.0})) == [
        "The value 6.0 of q must belong to (0, E_{y}(y^2))."
    ]


# q is defined on a set that reads h, before h is defined
CHAINED = "q : (0, h) := 2*β*R\nh : (0, 10) := β*R\n"


def test_of_two_derived_values_outside_their_sets_the_one_that_the_others_set_reads_is_refused():
    """Where the set of q reads h, which the file defines after q, and both
    values lie outside their sets, calibration refuses h."""
    stage = two_nodes_stage_with_lines(CHAINED)
    # β = 4 and R = 3 give h = 12, outside (0, 10), and q = 24, outside (0, 12)
    with pytest.raises(ValueError, match="derived parameter 'h'"):
        copy_native(stage).calibrate({"β": 4.0, "R": 3.0})


def test_the_refusal_of_a_set_that_reads_a_derived_parameter_gives_that_parameters_value():
    """The refusal of a value outside a set that reads h names q and gives
    the value of h and its definition."""
    stage = two_nodes_stage_with_lines(CHAINED)
    # β = 1 and R = 3 give h = 3, inside (0, 10), and q = 6, outside (0, 3)
    sentence = calibration_refusal_sentence(stage, {"β": 1.0, "R": 3.0})
    phrases = (
        "derived parameter 'q'",
        "lies outside the declared set (0, h) at β = 1.0, R = 3.0, where h = 3.0 (the derived "
        "parameter h := β*R); ",
    )
    assert [phrase for phrase in phrases if phrase not in sentence] == []


def test_the_refusal_names_the_condition_of_the_declared_set_that_the_value_breaks():
    """The refusal names the condition of the declared set of q that the value
    breaks, at the value of h that the condition reads."""
    conditioned = two_nodes_stage_with_lines("h := β/R\nq : (0, 1) @ (0, 1/h) := β*R\n")
    assert (
        "at β = 1.2, R = 0.5: the value 0.6 does not satisfy the condition q < 1/h of the "
        "declared set at h = 2.4 (the derived parameter h := β/R); "
    ) in calibration_refusal_sentence(conditioned, {"β": 1.2, "R": 0.5})


@pytest.mark.parametrize(
    "definition",
    [
        pytest.param("q : (0,1) := β*b", id="before a derived value outside its set"),
        pytest.param("q := 1/b", id="before a definition without a value"),
    ],
)
def test_a_declared_parameter_outside_its_set_is_refused_before_any_derived_parameter(definition):
    """A calibration at which β lies outside its declared set is refused at
    β, before a derived parameter that reads it and that the file writes
    first."""
    ordered = stage_from_text(
        two_nodes_text_with_parameter_sets(f"{definition}\nβ : (0,1)\nb : ℝ")
    )
    with pytest.raises(ValueError, match="parameter 'β'"):
        copy_native(ordered).calibrate({"β": 2.0, "b": 0.0, "R": 1.0})


@pytest.mark.parametrize(
    "stage, addition, domain, printed",
    [
        pytest.param(
            "patience_factor_without_a_set",
            "κ : (0,1) := 1 - q\n",
            "(0, 1)",
            "κ : (0, 1) := 1 - q, unbound",
            id="a formula on an interval",
        ),
        pytest.param(
            "cases_on_sets_stage",
            "κ : (0, 3) \\/ {5} := if q < R then 1 else 5\n",
            "(0, 3) \\/ {5}",
            "κ : (0, 3) \\/ {5} := if q < R then 1 else 5, unbound",
            id="a definition by cases on a union",
        ),
    ],
)
def test_an_addition_defines_a_derived_parameter_on_a_declared_set_and_no_setting(
    stage, addition, domain, printed, request
):
    """A methods file that defines κ on a declared set defines a derived
    parameter whose record holds the set, and κ is no setting."""
    added = methodized_copy(request.getfixturevalue(stage), addition)
    assert to_source(added.par["κ"].domain) == domain
    assert str(added.par["κ"]) == printed
    assert "κ" not in added.settings


def test_calibration_holds_a_derived_parameter_of_an_addition_to_its_declared_set(
    patience_factor_without_a_set,
):
    """A value of κ, defined in a methods file, outside its declared set is
    refused at κ, where q declares no set."""
    added = methodized_copy(patience_factor_without_a_set, "κ : (0,1) := 1 - q\n")
    with pytest.raises(ValueError, match="derived parameter 'κ'"):
        copy_native(added).calibrate(RETURN_IMPATIENCE_FAILING_CALIBRATION)


def test_an_addition_read_after_calibration_is_judged_at_the_values_bound(
    patience_factor_without_a_set,
):
    """A methods file read into a calibrated stage refuses a value of κ
    outside its declared set at the values that the stage binds."""
    bound = copy_native(patience_factor_without_a_set).calibrate(
        RETURN_IMPATIENCE_FAILING_CALIBRATION
    )
    with pytest.raises(ValueError, match="derived parameter 'κ'"):
        methodized_copy(bound, "κ : (0,1) := 1 - q\n")


def test_a_value_outside_the_set_of_q_is_refused_at_q_before_a_definition_that_reads_q(
    patience_factor_stage,
):
    """Where q and κ := 1 - q both declare a set, a value of q outside its
    set is refused at q."""
    added = methodized_copy(patience_factor_stage, "κ : (0,1) := 1 - q\n")
    with pytest.raises(ValueError, match="derived parameter 'q'"):
        added.calibrate(RETURN_IMPATIENCE_FAILING_CALIBRATION)


def test_a_declared_set_that_reads_a_setting_is_refused(patience_factor_without_a_set):
    """The declared set of a derived parameter that reads a setting is refused,
    since calibration judges it before a setting has a value."""
    with pytest.raises(ConstructionError) as refused:
        methodized_copy(patience_factor_without_a_set, "n : ℝ₊₊\nκ : (0, n) := 1 - q\n")
    assert refused.value.rule == "derived-parameter"
    assert "declares the set `(0, n)`, which reads n, a setting" in refused.value.message


@pytest.mark.parametrize(
    "lines, rule",
    [
        pytest.param(
            "q : (0,1)\nq := (β*R)^(1/ρ)/R",
            "one-name-one-meaning",
            id="a declaration beside the definition",
        ),
        pytest.param("q : (0,1) @ !shck := (β*R)^(1/ρ)/R", "readable-form", id="as a shock"),
        pytest.param("q : (0,1) @ !ctrl := (β*R)^(1/ρ)/R", "readable-form", id="as a control"),
        pytest.param("q : (0,1) @ !dcsn := (β*R)^(1/ρ)/R", "readable-form", id="as a state"),
        pytest.param("(q, s) : (0,1) := (β*R)^(1/ρ)/R", "readable-form", id="two names"),
        # `inf` is a number word and no name, so these values are numbers
        pytest.param("q : (0,1) := inf", "readable-form", id="the infinity"),
        pytest.param("q : (0,1) := -inf", "readable-form", id="the negative infinity"),
        pytest.param("q : (0,1) := 2*inf", "readable-form", id="twice the infinity"),
        pytest.param("q : (0,1) := 2*m", "derived-parameter", id="a field"),
        # the value is one real number, which lies in no set of labels, no
        # product and no set of functions
        pytest.param(
            "q : {low, high} := (β*R)^(1/ρ)/R", "derived-parameter", id="a set of labels"
        ),
        pytest.param("q : Xa × Xm := (β*R)^(1/ρ)/R", "derived-parameter", id="a product of sets"),
        pytest.param(
            "q : {1, …, 2} → ℝ := (β*R)^(1/ρ)/R", "derived-parameter", id="a set of functions"
        ),
        pytest.param("q : Foo := (β*R)^(1/ρ)/R", "name-in-scope", id="an undefined set"),
        pytest.param(
            "q : (0, n) := (β*R)^(1/ρ)/R", "name-in-scope", id="an interval to an undefined name"
        ),
        pytest.param("q : (0, 𝑢) := (β*R)^(1/ρ)/R", "well-typed", id="an interval to a function"),
    ],
)
def test_a_definition_on_a_declared_set_in_a_form_that_the_language_does_not_read_is_refused(
    lines, rule
):
    """A definition of q on a declared set that stands beside a declaration
    of q, carries a role, defines several names, writes a number, reads a
    field, declares a set of no numbers, or names in its set an undefined
    name or a function is refused under its rule."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(perfect_foresight_file_text({"β : ": "β : (0,1)", "q : ": lines}))
    assert refused.value.rule == rule


def test_a_definition_whose_value_reads_a_shock_is_refused_as_one_that_reads_a_field():
    """A definition on a declared set whose value reads the shock y is
    refused under `derived-parameter` with a sentence that names a shock."""
    with pytest.raises(ConstructionError) as refused:
        two_nodes_stage_with_lines("q : (0,1) := β*y\n")
    assert refused.value.rule == "derived-parameter" and "a shock" in refused.value.message


def test_two_definitions_that_read_each_other_are_refused_as_a_cycle():
    """Two derived parameters on declared sets whose definitions read each
    other are refused under `definition-order`."""
    with pytest.raises(ConstructionError) as refused:
        two_nodes_stage_with_lines("q : (0,1) := p\np : (0,1) := q\n")
    assert refused.value.rule == "definition-order"


@pytest.mark.parametrize(
    "value, words, write",
    [
        # the advice of a value that reads a name: the forms of a definition
        pytest.param(
            "sqrt(β)",
            "defines no derived parameter",
            "Write the value of q from declared parameters, finite numbers and derived "
            "parameters, with signs, sums, differences, products, quotients, powers, log, exp, "
            "min and max, or by cases with `if … then … else …`",
            id="a call of sqrt",
        ),
        pytest.param(
            "𝑢",
            "defines no derived parameter",
            "Write the value of q from declared parameters, finite numbers and derived "
            "parameters, with signs, sums, differences, products, quotients, powers, log, exp, "
            "min and max, or by cases with `if … then … else …`",
            id="a function",
        ),
        pytest.param(
            "2",
            "the calibration file supplies its value, `q: 2`",
            "Write `q : (0, 1)` here, and `q: 2` in the calibration file",
            id="a number",
        ),
    ],
)
def test_a_declared_value_that_is_no_definition_is_refused_with_advice_on_what_to_write(
    value, words, write
):
    """A declaration on a set whose value defines no derived parameter is
    refused under `readable-form`, with the forms of a definition where the
    value reads a name and with the calibration file where it is a number."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            perfect_foresight_file_text({"β : ": "β : (0,1)", "q : ": f"q : (0,1) := {value}"})
        )
    assert refused.value.rule == "readable-form" and words in refused.value.message
    assert ("calibration file" in refused.value.message) == (value == "2")
    assert refused.value.write == write


def test_a_membership_that_reads_q_is_decided_at_calibration_naming_the_definition_of_q():
    """The condition β < 1/q of the declared set of β is decided at the value
    of q, and a refusal names the definition of q."""
    # q declares no set here: where its definition declares one, as the
    # stage file does, a value of q outside it is refused at q first
    text = perfect_foresight_file_text({"β : ": "β : (0,1) @ (0, 1/q)", **Q_WITHOUT_A_SET})
    stage = stage_from_text(text)
    assert undecided_memberships(copy_native(stage).calibrate(PERFECT_FORESIGHT_CALIBRATION)) == []
    sentence = calibration_refusal_sentence(stage, RETURN_IMPATIENCE_FAILING_CALIBRATION)
    phrases = ("parameter 'β'", "β < 1/q", "(the derived parameter q := (β*R)^(1/ρ)/R); ")
    assert [phrase for phrase in phrases if phrase not in sentence] == []


def test_a_membership_that_no_value_decides_stays_open_in_a_stage_with_a_derived_parameter():
    """A condition of a declared set whose bound is an expectation stays
    open after calibration in a stage that defines a derived parameter."""
    undecided = stage_from_text(
        two_nodes_text_with_parameter_sets("β : ℝ₊₊ @ (0, E_{y}(y^2))\nh := β*R")
    )
    assert undecided_memberships(copy_native(undecided).calibrate({"β": 2.0, "R": 3.0})) == [
        "The value 2.0 of β must belong to ℝ₊₊ @ (0, E_{y}(y^2))."
    ]


def test_the_declared_set_of_a_setting_that_reads_a_derived_parameter_is_judged_at_its_value():
    """Configuration admits a value of the setting tol below q and refuses
    one above it under `setting-outside-set`, naming the value of q."""
    stage = stage_from_text(perfect_foresight_file_text({}))
    bounded = methodized_copy(stage, "tol : (0, 1) @ (0, q)\n").calibrate(
        PERFECT_FORESIGHT_CALIBRATION
    )
    copy_native(bounded).configure({"tol": 0.5})
    with pytest.raises(ConstructionError) as refused:
        copy_native(bounded).configure({"tol": 0.97})
    assert refused.value.rule == "setting-outside-set"
    assert "the condition tol < q of the declared set at q = 0.96" in refused.value.message


def test_a_definition_may_call_min_max_log_and_exp_and_no_other_function(
    min_and_max_stage, derived_parameter_stages
):
    """Definitions that call min and max of one argument or more, log and
    exp define derived parameters, where a definition that calls sqrt is
    refused under `derived-parameter` with the calls that it may make."""
    assert all(min_and_max_stage.par[name].derived for name in ("x", "y", "z", "q"))
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, "h := 1/sqrt(R)"))
    error = refused.value
    # the definition of h stands on line 8
    assert (error.rule, error.file, error.line) == (
        "derived-parameter",
        derived_parameter_stages.origin,
        8,
    )
    words = (
        "calls sqrt",
        "none of log, exp, min and max",
        "the calls `min` and `max`, each of one argument or more",
        "its right side may be a conditional, `if … then … else …`",
    )
    assert [word for word in words if word not in error.message] == [], error.message
    assert error.write


def test_a_parameter_declared_on_a_set_whose_bound_calls_min_is_no_derived_parameter(
    min_and_max_stage,
):
    """A parameter declared on a set whose bound calls min is a declared
    parameter."""
    assert not min_and_max_stage.par["b"].derived


# definitions by cases: each relation, nested branches, the two infinities
# as whole branches, and min, log and exp in a branch
DEFINITIONS_BY_CASES = [
    pytest.param("if a < 0 then -1 else 1", id="less than"),
    pytest.param("if a <= b then 1 else 2", id="at most"),
    pytest.param("if a = b then 1 else 2", id="equal to"),
    pytest.param("if a >= b then 1 else 2", id="at least"),
    pytest.param("if a > b then 1 else 2", id="greater than"),
    pytest.param("if a < 0 then -1 else if a = 0 then 0 else 1", id="nested"),
    pytest.param(
        "if p_zero = 0 then θ_min else min(ξ_u, θ_min*(1 - p_zero*ξ_u)/(1 - p_zero))",
        id="the lowest income of the buffer-stock model",
    ),
    pytest.param(
        "if Γ*ψ_min < R then -ξ_min*Γ*ψ_min/(R - Γ*ψ_min) else -inf",
        id="the natural borrowing limit",
    ),
    pytest.param(
        "if a >= b then inf else if a + 1 > b^2 then log(a) else exp(-b)",
        id="nested with the infinity, log and exp",
    ),
]


@pytest.mark.parametrize("cases", DEFINITIONS_BY_CASES)
def test_a_definition_by_cases_prints_as_it_is_read(cases):
    """The right side of a definition by cases prints as the file writes it."""
    assert to_source(right_side(f"x := {cases}")) == cases


@pytest.mark.parametrize(
    "declared",
    [
        pytest.param("ℝ̄", id="on the extended reals"),
        pytest.param("(0, 3) \\/ [5, inf]", id="on a union"),
        pytest.param("ℝ₊₊ @ (0, R)", id="on a set with a condition"),
    ],
)
@pytest.mark.parametrize("cases", DEFINITIONS_BY_CASES)
def test_a_definition_by_cases_printed_after_a_declared_set_is_read_as_the_same_term(
    cases, declared
):
    """The printed right side of a definition by cases, written after a
    declared set, is read as the term that it prints."""
    printed = right_side(f"x := {cases}")
    assert right_side(f"x : {declared} := {to_source(printed)}") == printed


def test_a_definition_by_cases_with_a_declared_set_must_read_a_parameter(
    cases_on_sets_stage, derived_parameter_stages
):
    """A definition by cases on a declared set that reads β defines a
    derived parameter, and one whose test and branches read no parameter is
    refused under `readable-form`, as `ρ : ℝ := 2` is."""
    record = cases_on_sets_stage.par["q"]
    assert record.derived and to_source(record.domain) == "(0, 3)"
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage(
            (GROWTH_LINE, GROWTH_LINE + "w : (0, 3) := if 1 < 2 then 1 else 2\n")
        )
    error = refused.value
    assert (error.rule, error.line) == ("readable-form", 8)
    assert error.message == (
        "the declaration of w carries the value if 1 < 2 then 1 else 2, a definition by cases "
        "that reads no parameter; a definition that declares a set reads at least one parameter "
        "or derived parameter, by cases as otherwise, and a value that reads none is one number, "
        "which the calibration file supplies"
    )
    assert error.write == (
        "Write `w : (0, 3)` here and the number in the calibration file, or a test and branches "
        "that read a parameter"
    )


@pytest.mark.parametrize(
    "subject, names",
    [
        pytest.param("(a, b) : ℝ", "a, b", id="two names"),
        pytest.param("x : ℝ @ !ctrl", "x", id="a control"),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param("if β < R then 1 else 2", id="reading a parameter"),
        pytest.param("if 1 < 2 then 1 else 2", id="reading no parameter"),
    ],
)
def test_a_conditional_on_a_declaration_that_defines_no_derived_parameter_has_no_advice(
    subject, names, value, derived_parameter_stages
):
    """A conditional on a declaration of several names, or of a name with a
    role, is refused under `readable-form` without advice."""
    declaration = f"{subject} := {value}"
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage((GROWTH_LINE, GROWTH_LINE + declaration + "\n"))
    error = refused.value
    assert (error.rule, error.line) == ("readable-form", 8)
    # each phrase is untrue of such a declaration, whether its conditional
    # reads a parameter or none: `a, b : ℝ` is no line that the parser reads,
    # and `x : ℝ` declares a parameter
    untrue = (
        "reads no parameter",
        "a test and branches that read a parameter",
        "in the calibration file",
    )
    assert [phrase for phrase in untrue if phrase in error.message + (error.write or "")] == []
    assert error.message == (
        f"the declaration of {names} carries the value {value}; a declaration states the set a "
        "name lies in, and the calibration file supplies the value of each name"
    )
    assert error.write is None


# the places at which a stage file writes a name, each as the fragment of
# the perfect-foresight text that a test replaces and its replacement, in
# which `{word}` stands for the word written as the name
PLACES = (
    ("a declaration", GROWTH_LINE, GROWTH_LINE + "{word} : ℝ₊₊\n"),
    ("a definition", GROWTH_LINE, GROWTH_LINE + "{word} := 2*R\n"),
    ("a definition with a set", GROWTH_LINE, GROWTH_LINE + "{word} : (0, 9) := 2*R\n"),
    ("a named set", GROWTH_LINE, GROWTH_LINE + "{word} := [0, 1]\n"),
    ("the name of a function", GROWTH_LINE, GROWTH_LINE + "{word}(x : ℝ) := x^2\n"),
    ("an argument of a function", GROWTH_LINE, GROWTH_LINE + "𝑓({word} : ℝ) := {word}^2\n"),
    ("the binder of a set", GROWTH_LINE, GROWTH_LINE + "H := {{word} : ℝ | {word} >= 0}\n"),
    ("the subject of a law", GROWTH_LINE, GROWTH_LINE + "{word} ~ N(0, 1)\n"),
    ("a subscript", GROWTH_LINE, GROWTH_LINE + "w : (0, E_{{word}}({word}^2))\n"),
    ("a field of a header", "(k : Xa) : !arvl", "({word} : Xa) : !arvl"),
    ("the id of a header", "[id=arvl_to_dcsn,", "[id={word},"),
    ("a formula", GROWTH_LINE, GROWTH_LINE + "w := 1 + {word}\n"),
    ("a formula in parentheses", GROWTH_LINE, GROWTH_LINE + "w := ({word})\n"),
    ("an endpoint of a set", GROWTH_LINE, GROWTH_LINE + "w : (0, {word})\n"),
    ("the name of a set", GROWTH_LINE, GROWTH_LINE + "w : {word}\n"),
    ("a test", GROWTH_LINE, GROWTH_LINE + "w := if {word} < R then 1 else 0\n"),
    ("a line of a block", "    m = R_n*k + 1 ", "    m = R_n*k + {word} "),
)


@pytest.mark.parametrize(
    "word, written, replacement",
    [
        pytest.param(word, written, template.replace("{word}", word), id=f"{word} as {place}")
        for word in ("if", "then", "else")
        for place, written, template in PLACES
    ],
)
def test_if_then_or_else_written_as_a_name_is_refused_at_the_word(
    word, written, replacement, derived_parameter_stages
):
    """A stage file that writes `if`, `then` or `else` as a name is refused
    under `syntax` at the word, with one sentence and advice."""
    assert derived_parameter_stages.text.count("(k : Xa) : !arvl") == 1
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage((written, replacement))
    error = refused.value
    assert (error.rule, error.file) == ("syntax", derived_parameter_stages.origin)
    assert error.parts.why == f"the file writes `{word}` as a name; {IF_THEN_ELSE_REFUSAL}"
    assert error.parts.why in error.message
    assert error.write == f"Write another name in place of `{word}`"
    assert error.end_column - error.column == len(word)


@pytest.mark.parametrize(
    "word, addition",
    [
        pytest.param(word, template.replace("{word}", word), id=f"{word} as {place}")
        for word in ("if", "then", "else")
        for place, template in (
            ("a declaration", "{word} : ℝ₊₊\n"),
            ("a formula", "κ := 1 - {word}\n"),
        )
    ],
)
def test_if_then_or_else_written_as_a_name_in_a_methods_file_is_refused(
    word, addition, derived_parameter_stages
):
    """`methodize` refuses a methods file that writes `if`, `then` or `else` as
    a name, under `syntax` at its line."""
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage().methodize(
            {"text": f"@methods: perfect_foresight\n{addition}", "origin": "m.bl"}
        )
    error = refused.value
    assert (error.rule, error.file, error.line) == ("syntax", "m.bl", 2)
    assert f"the file writes `{word}` as a name; {IF_THEN_ELSE_REFUSAL}" in error.message


def test_a_name_that_begins_with_if_then_or_else_is_a_name(derived_parameter_stages):
    """`iffy`, `thenar` and `elsewhere` are names of derived parameters, where
    the same lines with `if` in place of `iffy` are refused under `syntax`."""
    names = "iffy := 3*R\nthenar := 2*R\nelsewhere := thenar + iffy\n"
    named = derived_parameter_stages.stage((GROWTH_LINE, GROWTH_LINE + names))
    assert str(named.par["elsewhere"]) == "elsewhere := thenar + iffy, unbound"
    assert named.par["elsewhere"].derived
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage((GROWTH_LINE, GROWTH_LINE + names.replace("iffy", "if")))
    assert refused.value.rule == "syntax"


# the reasons with which the parser stops at a conditional out of its place
AT_GAMMA = "the file writes `Γ` here"
AN_OPERAND = "the language admits `(`, `-`, a name, a number or `inf` at this place"


# each conditional out of its place, with the column where the parser stops
CONDITIONALS_OUT_OF_PLACE = [
    pytest.param(
        (HUMAN_WEALTH_DEFINITION, "h := 1 + if Γ < R then 1 else 2"), 13, AT_GAMMA, id="in a sum"
    ),
    pytest.param(
        (HUMAN_WEALTH_DEFINITION, "h := (if Γ < R then 1 else 2)"), 10, AT_GAMMA, id="in brackets"
    ),
    pytest.param(
        (HUMAN_WEALTH_DEFINITION, "h : (0, 3) := 1 + if Γ < R then 1 else 2"),
        22,
        AT_GAMMA,
        id="in a sum after a declared set",
    ),
    pytest.param(
        (HUMAN_WEALTH_DEFINITION, "h := min(R, if Γ < R then 1 else 2)"),
        16,
        AT_GAMMA,
        id="in a call",
    ),
    pytest.param(
        (UTILITY, "𝑢(c : ℝ₊₊) := if c < 1 then c else 1    :: [id=util]"),
        18,
        "the file writes `c` here",
        id="in the body of a function",
    ),
    pytest.param(
        (RESOURCES_LINE, "    m = if k < 0 then 1 else R_n*k + 1   :: [id=market_resources]"),
        12,
        "the file writes `k` here",
        id="in a line of a block",
    ),
    # a conditional always has both branches
    pytest.param(
        (HUMAN_WEALTH_DEFINITION, "h := if Γ < R then 1"),
        21,
        "the language admits `else` at this place",
        id="without else",
    ),
    # the word at the start of a right side is the first word of a
    # conditional, and no name
    pytest.param((HUMAN_WEALTH_DEFINITION, "h := if + 1"), 9, AN_OPERAND, id="if before a sign"),
    pytest.param((HUMAN_WEALTH_DEFINITION, "h := if"), 13, AN_OPERAND, id="if alone"),
    pytest.param(
        (HUMAN_WEALTH_DEFINITION, "h := if(R)"),
        11,
        "the language admits `=` or a comparison",
        id="if called as a function",
    ),
]


@pytest.mark.parametrize("change, column, why", CONDITIONALS_OUT_OF_PLACE)
def test_a_conditional_out_of_its_place_is_refused_with_the_advice_on_where_it_stands(
    change, column, why, derived_parameter_stages
):
    """A conditional out of its place or its form is refused under `syntax` at
    the column where the parser stops, with advice on where it stands."""
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage(change)
    error = refused.value
    assert (error.rule, error.file) == ("syntax", derived_parameter_stages.origin)
    assert error.column == column and why in error.parts.why, error.parts.why
    assert error.write == CONDITIONAL_PLACE


@pytest.mark.parametrize(
    "line, why",
    [
        pytest.param(
            "x := 2*R +   # add the premium if any", "the line ends here", id="in a comment"
        ),
        pytest.param(
            'β2 : (0,1)   :: ["a second discount factor, if any"] :: ["again"]',
            'the file writes `:: ["again"]` here',
            id="in an explanation in double quotes",
        ),
        pytest.param(
            "β2 : (0,1)   :: ['a second discount factor, if any'] :: ['again']",
            "the file writes `:: ['again']` here",
            id="in an explanation in single quotes",
        ),
        pytest.param(
            "x := 2*R   :: [id=if] :: [id=b]",
            "the file writes `:: [id=b]` here",
            id="as the id of an annotation",
        ),
    ],
)
def test_the_word_if_in_a_comment_or_in_a_quoted_text_writes_no_conditional(
    line, why, derived_parameter_stages
):
    """A refused line that holds `if` in a comment, a quoted explanation or
    an annotation receives the advice that it receives without the word, and
    not the advice on where a conditional stands."""
    refusals = []
    for written in (line, line.replace("if any", "at most").replace("id=if", "id=a")):
        with pytest.raises(ConstructionError) as refused:
            derived_parameter_stages.stage((GROWTH_LINE, GROWTH_LINE + written + "\n"))
        refusals.append(refused.value)
    error, without_the_word = refusals
    assert (error.rule, error.file, error.line) == ("syntax", derived_parameter_stages.origin, 8)
    assert why in error.parts.why, error.parts.why
    assert "stands as the whole right side of a definition" not in (error.write or "")
    assert error.write == without_the_word.write


@pytest.mark.parametrize(
    "reading, read",
    [
        pytest.param("if d < R then 1 else 2", "d < R", id="less than"),
        pytest.param("if d = R then 1 else 2", "d = R", id="equal to"),
        pytest.param("if R >= d then 1 else 2", "R >= d", id="on the right side"),
        pytest.param("d + R", "d + R", id="in arithmetic"),
    ],
)
def test_a_label_in_the_test_of_a_definition_by_cases_is_refused_as_it_is_in_arithmetic(
    reading, read, derived_parameter_stages
):
    """A label of a finite set on either side of a test is refused under
    `well-typed`, as the label in arithmetic is."""
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage(
            (GROWTH_LINE, GROWTH_LINE + f"d : {{work, retire}}\nw := {reading}\n")
        )
    error = refused.value
    # the definition of w stands on line 9, after the declaration of d
    assert (error.rule, error.line) == ("well-typed", 9)
    assert (
        f"`d` is a label, a member of a finite set of names, and `{read}` reads it as a "
        "number; a label carries no arithmetic"
    ) in error.message


# the refusals of a derived parameter's definition when the file is read,
# each the definition of h, in place of its definition in the
# perfect-foresight text, and the words of the sentence
DEFINITION_REFUSALS = [
    ("a field", "h := 1/(1 - Γ/m)", ("the derived parameter h", "reads m, a field")),
    ("a set", "h := 1/(1 - Γ/R) + Xm", ("reads Xm, a set of the stage",)),
    ("a function", "h := 1 + 𝑢", ("reads 𝑢, a function of the stage",)),
    ("infinity", "h := 1/(1 - Γ/R) + inf", ("reads inf, which is no finite number",)),
    ("min of a set", "h := min(Γ, Xm)", ("reads Xm, a set of the stage",)),
    # what a test and a branch of a definition by cases read and call
    ("a set in a test", "h := if Xa < R then 1 else 2", ("reads Xa, a set of the stage",)),
    ("a field in a test", "h := if m < R then 1 else 2", ("reads m, a field of the stage",)),
    (
        "a function as a branch",
        "h := if Γ < R then 𝑢 else 2",
        ("reads 𝑢, a function of the stage",),
    ),
    (
        "a call of another function in a branch",
        "h := if Γ < R then 1/sqrt(R) else 2",
        ("calls sqrt", "its right side may be a conditional"),
    ),
    # an infinity is a whole branch and nothing else
    (
        "infinity in the arithmetic of a branch",
        "h := if Γ < R then 1 else 2*inf",
        ("reads inf, which is no finite number",),
    ),
    (
        "infinity in a test",
        "h := if Γ < inf then 1 else 2",
        ("reads inf, which is no finite number",),
    ),
    ("infinity as a whole definition", "h := inf", ("reads inf, which is no finite number",)),
    (
        "an infinite branch on a set that holds the other infinity",
        "h : ℝ_{+∞} := if Γ < R then 1/(1 - Γ/R) else -inf",
        ("writes the branch `-inf`", "its declared set `ℝ_{+∞}` cannot hold -inf"),
    ),
    # log, exp, min and max are the functions of the language: a stage that
    # defines a function of one of those names calls none of that name in a
    # derived parameter's definition
    (
        "a call of min where the stage defines min",
        "h := min(Γ, R)\nmin(a : ℝ, b : ℝ) := a + b",
        (
            "calls min, `min(Γ, R)`, and the stage defines a function named min",
            "would give the one name two meanings",
        ),
    ),
    (
        "a call of log where the stage defines log",
        "h := 1 + log(R)\nlog(a : ℝ₊₊) := 2*a",
        ("calls log, `log(R)`, and the stage defines a function named log",),
    ),
    # also where the stage's function takes another number of arguments
    # than the call gives
    (
        "a call of min where the stage defines min of one argument",
        "h := min(Γ, R)\nmin(a : ℝ) := a",
        ("calls min, `min(Γ, R)`, and the stage defines a function named min",),
    ),
    (
        "a call of log where the stage defines log of two arguments",
        "h := 1 + log(R)\nlog(a : ℝ₊₊, b : ℝ) := a + b",
        ("calls log, `log(R)`, and the stage defines a function named log",),
    ),
    (
        "a number beyond the floating-point range",
        "h := 1/(1 - Γ/R) + 1" + "0" * 400,
        ("writes a number that exceeds the largest finite floating-point number",),
    ),
    (
        "a decimal number beyond the floating-point range",
        "h := 1/(1 - Γ/R) + 1e400",
        (
            "writes a number that exceeds the largest finite floating-point number",
            "has no finite real value",
        ),
    ),
    ("log of two arguments", "h := log(R, Γ)", ("calls log with 2 arguments",)),
    ("a tuple", "h := 1 + (R, Γ)", ("writes `(R, Γ)`, a form no derived parameter",)),
]


@pytest.mark.parametrize("case", DEFINITION_REFUSALS, ids=lambda case: case[0])
def test_a_derived_parameter_is_refused_at_its_definition(case, derived_parameter_stages):
    """A definition that reads a field, a set, a function or an infinity, calls
    a function other than log, exp, min and max or one of them that the stage
    defines, writes a number beyond the floating-point range or another form,
    or writes a branch that its set cannot hold is refused under
    `derived-parameter` at its line."""
    _, definition, words = case
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, definition))
    error = refused.value
    # the definition of h stands on line 8
    assert (error.rule, error.file, error.line) == (
        "derived-parameter",
        derived_parameter_stages.origin,
        8,
    )
    assert [word for word in words if word not in error.message] == [], error.message
    assert error.write


# declared sets that cannot hold the infinity of the second branch of
# `HUMAN_WEALTH_RIGHT_SIDE_BY_CASES`, each with a name: a real set, an interval
# open or finite at that end, a set that holds the other infinity, and a set of
# extended reals with a condition that excludes the infinity
SETS_WITHOUT_THE_INFINITY = (
    ("ℝ", "the reals"),
    ("ℝ₊₊", "the positive reals"),
    ("(0, inf)", "an interval open at infinity"),
    ("(0, 100]", "a finite interval"),
    ("ℝ_{-∞}", "the reals with the negative infinity"),
    ("(0, 1) \\/ (2, inf)", "a union open at infinity"),
    ("ℝ̄ @ (0, inf)", "the extended reals with a condition open at infinity"),
    ("ℝ_{+∞} @ (0, 100]", "the reals with the infinity and a finite condition"),
)


# definitions whose declared set holds each infinity that a branch writes,
# each with a name
DEFINITIONS_ON_SETS_WITH_THE_INFINITY = (
    (f"h : ℝ_{{+∞}} := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}", "the reals with the infinity"),
    (f"h : ℝ̄ := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}", "the extended reals"),
    (f"h : ℝ_{{±∞}} := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}", "the reals with both infinities"),
    (f"h : (0, inf] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}", "an interval closed at infinity"),
    (
        f"h : (0, 1) \\/ [2, inf] := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
        "a union closed at infinity",
    ),
    (
        f"Xh := (0, inf]\nh : Xh := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
        "a named interval closed at infinity",
    ),
    ("h : ℝ_{-∞} := if Γ < R then 1 else -inf", "the negative infinity"),
    ("h : [-inf, inf] := if Γ < R then inf else if Γ = R then 0 else -inf", "both infinities"),
)


# definitions with an infinite branch; `written` is None where one is admitted
INFINITE_BRANCHES = [
    pytest.param(
        f"h := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
        "the set ℝ of a definition that declares none",
        id="refused without a set",
    ),
    *[
        pytest.param(
            f"h : {declared} := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
            f"its declared set `{declared}`",
            id=f"refused on {words}",
        )
        for declared, words in SETS_WITHOUT_THE_INFINITY
    ],
    # a named set is defined on the line before the definition
    pytest.param(
        f"Xe := {{x : ℝ̄ | x < 100}}\nh : Xe := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
        "its declared set `Xe`",
        id="refused on a named set with a bar",
    ),
    pytest.param(
        f"Xh := (0, 100]\nh : Xh := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}",
        "its declared set `Xh`",
        id="refused on a named finite interval",
    ),
    *[
        pytest.param(definition, None, id=f"admitted on {words}")
        for definition, words in DEFINITIONS_ON_SETS_WITH_THE_INFINITY
    ],
]


@pytest.mark.parametrize("definition, written", INFINITE_BRANCHES)
def test_an_infinite_branch_is_admitted_only_where_its_declared_set_can_hold_it(
    definition, written, derived_parameter_stages
):
    """An infinite branch defines a derived parameter where the form of its
    declared set holds that infinity, and is refused with the set to write
    otherwise."""
    if written is None:
        assert (
            derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, definition)).par["h"].derived
        )
    else:
        with pytest.raises(ConstructionError) as refused:
            derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, definition))
        error = refused.value
        # h is defined on line 8, or on line 9 after a named set
        line = 8 + definition.count("\n")
        assert (error.rule, error.file, error.line) == (
            "derived-parameter",
            derived_parameter_stages.origin,
            line,
        )
        phrases = (
            f"the derived parameter h, defined as `{HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}`, writes "
            f"the branch `inf`, and {written} cannot hold inf; ",
            "a branch written `inf` or `-inf` is admitted in a definition whose declared set "
            "holds that infinity",
        )
        assert [phrase for phrase in phrases if phrase not in error.message] == []
        assert error.write.startswith(
            f"Write `h : ℝ_{{+∞}} := {HUMAN_WEALTH_RIGHT_SIDE_BY_CASES}`"
        ), error.write


@pytest.mark.parametrize(
    "definition, advised",
    [
        pytest.param("h := if Γ < R then 1 else -inf", "ℝ_{-∞}", id="the negative infinity"),
        pytest.param(
            "h : ℝ_{+∞} := if Γ < R then inf else if Γ = R then 0 else -inf",
            "ℝ̄",
            id="both infinities",
        ),
    ],
)
def test_the_set_to_write_holds_each_infinity_that_the_definition_writes(
    definition, advised, derived_parameter_stages
):
    """The refusal of a branch written `-inf` advises a set that holds each
    infinity that the definition writes."""
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, definition))
    assert refused.value.rule == "derived-parameter"
    assert "writes the branch `-inf`" in refused.value.message
    assert refused.value.write.startswith(f"Write `h : {advised} := "), refused.value.write


# the refusals of a calibration at a derived parameter's definition: the
# definition of h in place of the one of the perfect-foresight text, the
# values that the calibration changes, and the words of the sentence
CALIBRATION_REFUSALS = [
    (
        "a value for h",
        HUMAN_WEALTH_DEFINITION,
        {"h": 52.0},
        ("the calibration source supplies the value 52.0 for h", "`1/(1 - Γ/R)`"),
    ),
    (
        "a division by zero",
        HUMAN_WEALTH_DEFINITION,
        {"Γ": 1.04},
        ("the divisor `1 - Γ/R` is 0.0 at Γ = 1.04, R = 1.04", "a division by zero has no value"),
    ),
    (
        "a nonpositive logarithm",
        "h := log(1 - Γ/R)",
        {"Γ": 1.06},
        ("the argument `1 - Γ/R` of log is", "log is defined at positive numbers alone"),
    ),
    (
        "a noninteger power of a negative base",
        "h := (1 - Γ/R)^(1/2)",
        {"Γ": 1.06},
        ("which is no integer", "a noninteger exponent requires a positive base"),
    ),
    (
        "an undefined power of zero",
        "h := (1 - Γ/R)^(-1)",
        {"Γ": 1.04},
        ("has the base 0.0 and the exponent -1.0", "defined for a positive exponent alone"),
    ),
    (
        "a value beyond the floating-point range",
        "h := exp(1000*ρ)",
        {},
        ("`exp(1000*ρ)` at ρ = 2.0 exceeds the largest finite floating-point number",),
    ),
    (
        "a positive argument lost to underflow",
        "h := log(exp(-1000*ρ))",
        {},
        ("is 0.0 by floating-point underflow", "which numeric underflow does not supply"),
    ),
    # the branch that a test chooses is evaluated as any definition is, and
    # a zero that floating point rounded from a nonzero result decides no test
    (
        "a division by zero in the chosen branch",
        "h := if Γ < R then 1/(β - β) else 2",
        {},
        ("the divisor `β - β` is 0.0", "a division by zero has no value"),
    ),
    (
        "an underflowed side of a test",
        "h := if exp(-800*R) = 0 then 1 else 2",
        {},
        (
            "the test `exp(-800*R) = 0` reads `exp(-800*R)`, which is 0.0 by floating-point "
            "underflow",
            "such a zero decides no comparison",
        ),
    ),
    # every argument of min is evaluated, whichever is the least
    (
        "an argument of min without a value",
        "h := min(R, 1/(R - Γ))",
        {"Γ": 1.04},
        ("the divisor `R - Γ` is 0.0",),
    ),
]


@pytest.mark.parametrize("case", CALIBRATION_REFUSALS, ids=lambda case: case[0])
def test_a_calibration_is_refused_at_a_definition_that_it_supplies_or_that_has_no_value(
    case, derived_parameter_stages
):
    """A calibration that supplies a value for a derived parameter, or at which
    its definition has no value, is refused under `derived-parameter` at the
    definition, naming the operation."""
    _, definition, values, words = case
    stage = derived_parameter_stages.stage((HUMAN_WEALTH_DEFINITION, definition))
    with pytest.raises(ConstructionError) as refused:
        stage.calibrate({"calibration": {**derived_parameter_stages.calibration, **values}})
    error = refused.value
    # the definition of h stands on line 8
    assert (error.rule, error.address) == (
        "derived-parameter",
        f"{derived_parameter_stages.origin}:8",
    )
    assert [word for word in words if word not in error.message] == [], error.message
    assert error.write


@pytest.mark.parametrize(
    "value, printed, supplied, write",
    [
        pytest.param(
            "inf",
            "inf",
            ".inf",
            "Write `T : ℝ̄` here, and `T: .inf` in the calibration file, where `.inf` is read "
            "as a number and `inf` as a text",
            id="the infinity",
        ),
        pytest.param(
            "-inf",
            "-inf",
            "-.inf",
            "Write `T : ℝ̄` here, and `T: -.inf` in the calibration file, where `-.inf` is read "
            "as a number and `-inf` as a text",
            id="the negative infinity",
        ),
        pytest.param(
            "2", "2", "2", "Write `T : ℝ̄` here, and `T: 2` in the calibration file", id="a number"
        ),
        pytest.param(
            "-3",
            "-3",
            "-3",
            "Write `T : ℝ̄` here, and `T: -3` in the calibration file",
            id="minus 3",
        ),
        # the package prints this float with an exponent and no decimal
        # point, `1e-05`, which the reader of a calibration file returns as a
        # text
        pytest.param(
            "1e-5",
            "1e-05",
            "1.0e-05",
            "Write `T : ℝ̄` here, and `T: 1.0e-05` in the calibration file, where `1.0e-05` is "
            "read as a number and `1e-05` as a text",
            id="a float with an exponent",
        ),
    ],
)
def test_the_advice_to_supply_a_declared_value_writes_a_spelling_that_is_read_as_a_number(
    value, printed, supplied, write, derived_parameter_stages
):
    """A declaration of one name that carries a number or an infinity is
    refused under `readable-form` with the advice to supply the value in the
    calibration file, in a spelling that its reader returns as a number."""
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage((GROWTH_LINE, GROWTH_LINE + f"T : ℝ̄ := {value}\n"))
    error = refused.value
    assert (error.rule, error.line) == ("readable-form", 8)
    assert error.message == (
        f"the declaration of T carries the value {printed}; a stage file declares the set a name "
        f"lies in, `T : ℝ̄`, and the calibration file supplies its value, `T: {supplied}`"
    )
    assert error.write == write


def test_a_declared_value_that_is_no_number_receives_no_advice_on_the_calibration_file(
    derived_parameter_stages,
):
    """A declaration of one name that carries `1/2`, which the reader of a
    calibration file returns as a text, is refused without advice."""
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage((GROWTH_LINE, GROWTH_LINE + "T : ℝ̄ := 1/2\n"))
    error = refused.value
    assert (error.rule, error.line, error.write) == ("readable-form", 8, None)
    assert error.message == (
        "the declaration of T carries the value 1/2; a declaration states the set a name lies "
        "in, and the calibration file supplies the value of each name"
    )


def test_the_reader_of_a_calibration_file_returns_the_advised_spellings_as_numbers(tmp_path):
    """`load_calibration` returns `.inf`, `-.inf` and `1.0e-05` as numbers,
    and `inf`, `1/2` and `1e-05` as texts."""
    path = tmp_path / "calibration.yaml"
    path.write_text(
        "above: .inf\nbelow: -.inf\ntext: inf\nquotient: 1/2\npoint: 1.0e-05\nno_point: 1e-05\n",
        encoding="utf-8",
    )
    assert load_calibration(path) == {
        "above": math.inf,
        "below": -math.inf,
        "text": "inf",
        "quotient": "1/2",
        "point": 1e-05,
        "no_point": "1e-05",
    }


def test_a_derived_parameter_that_reads_a_setting_is_refused_in_its_methods_file(
    derived_parameter_stages,
):
    """A definition in a methods file that reads a setting is refused at its
    line, since a setting takes its value after calibration."""
    addition = {"text": "@methods: perfect_foresight\nn_a : ℕ\nκ := n_a/2\n", "origin": "m.bl"}
    with pytest.raises(ConstructionError) as refused:
        derived_parameter_stages.stage().methodize(addition)
    error = refused.value
    assert (error.rule, error.file, error.line) == ("derived-parameter", "m.bl", 3)
    assert "reads n_a, a setting" in error.message
