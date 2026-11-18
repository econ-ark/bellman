"""The table of types: one row for each object of a stage, each form of a set
and each limit on a type, and the type in which each form is read; and the
conditions that the declared sets of a stage settle."""

import inspect
from collections import Counter

import pytest
from application_files import (
    BUFFER_STOCK_FILE,
    PERFECT_FORESIGHT_FILE,
    PERFECT_FORESIGHT_FOLDER,
    ROOT,
)
from refusal_rules import every_rule, problem_lines
from stage_builders import declared_set_of, stage_from_text
from stage_texts import changed

from bellman.refusals import ConstructionError
from bellman.semantic_rules import resolve
from bellman.stage import elaborate_stage, load_stage
from bellman.syntax import terms
from bellman.typing import typed_expressions
from bellman.typing.type_table import LIMITS, OBJECTS, SET_FORMS, WITH_A_SET

# the declaration folder of the perfect-foresight application, whose stage
# file `PERFECT_FORESIGHT_FILE` and gridded methods file hold most of the
# lines of `OBJECTS`, with its calibration file and values for the three
# settings of its grid of savings, which the application's module supplies
# and no file of its folder holds
PERFECT_FORESIGHT = "applications/consumption-perfect-foresight-crra/declaration"


METHODS_FILE = f"{PERFECT_FORESIGHT_FOLDER}/methods.egm.bl"


CALIBRATION_FILE = f"{PERFECT_FORESIGHT}/calibration/perfect_foresight.yml"


GRID_OF_SAVINGS = {"n_a": 50, "a_min": -40.0, "a_max": 60.0}


@pytest.fixture(scope="module")
def perfect_foresight_stage():
    """The perfect-foresight stage with its gridded methods file read, its
    calibration file bound and the settings of its grid given values."""
    stage = elaborate_stage(load_stage(ROOT / PERFECT_FORESIGHT_FILE))
    stage.methodize(ROOT / METHODS_FILE)
    stage.calibrate(ROOT / CALIBRATION_FILE)
    return stage.configure(GRID_OF_SAVINGS)


@pytest.fixture(scope="module")
def buffer_stock_stage():
    """The symbolic buffer-stock stage."""
    return elaborate_stage(load_stage(ROOT / BUFFER_STOCK_FILE))


# the fixture of the stage on which the expression of a row of `OBJECTS` is
# evaluated, by the file that holds the row's line
STAGE_FIXTURE_BY_FILE = {
    PERFECT_FORESIGHT_FILE: "perfect_foresight_stage",
    METHODS_FILE: "perfect_foresight_stage",
    BUFFER_STOCK_FILE: "buffer_stock_stage",
}


def written_constructors():
    """The names of the constructors of a set expression that a file writes:
    the classes of `bellman.syntax.terms` under `setexpr`. The typed
    expressions define further classes under it in their own module, and no
    file writes one of those."""
    return {
        name
        for name, held in vars(terms).items()
        if inspect.isclass(held) and held is not terms.setexpr and issubclass(held, terms.setexpr)
    }


def stage_record(text, methods=None):
    """The source record of a stage text, with one methods file where
    `methods` gives its text."""
    return {
        "stage": {"text": text, "origin": "t.bl"},
        "calibration": {},
        "settings": {},
        "methods": [] if methods is None else [{"text": methods, "origin": "methods.bl"}],
    }


def smallest_record(name, written):
    """The source record of the smallest stage text that writes the set
    `written` in the type of an object named `name` in `OBJECTS`: a
    parameter on its own line, a derived parameter defined from one
    parameter, a setting in a methods file, a field on the header of one
    block, a shock declared by its role word, and the argument of a
    function."""
    if name == "setting":
        return stage_record("@stage: t\n", f"@methods: t\nx : {written}\n")
    items = {
        "parameter": f"x : {written}\n",
        "derived parameter": f"β : (0,1)\nx : {written} := 2*β\n",
        "field": (
            f"[id=arvl_to_dcsn, (x : {written}) : !arvl -> (m : ℝ) : !dcsn] {{\n    m = 1\n}}\n"
        ),
        "shock": f"x : {written} @ !shck\n",
        "function": f"𝑓(x : {written}) := 1\n",
    }
    return stage_record("@stage: t\n" + items[name])


# one id for each limit of `LIMITS`, the ids standing in the order of the
# table; the test of the rules of the table checks that each row has one
LIMIT_IDS = (
    "at-most-one-set-other-than-an-interval",
    "several-sets-with-a-number-in-common",
    "several-sets-on-one-declared-name",
    "several-sets-on-a-line-of-its-own",
    "union-and-difference-of-sets-of-numbers",
    "union-and-difference-in-parameters-and-settings",
    "no-union-as-the-value-of-a-named-set",
    "no-union-or-difference-inside-the-value-of-a-named-set",
    "declared-definition-reads-a-name",
    "conditional-as-a-whole-right-side",
    "infinity-only-as-a-whole-branch",
    "if-then-else-are-no-names",
    "infinite-branch-in-a-set-that-holds-it",
)


# the forms of a set


def test_the_table_of_set_forms_has_one_row_for_each_constructor_of_a_set_expression():
    """The rows of `SET_FORMS` name each constructor of a set expression that
    a file writes once, and name no other constructor."""
    count_by_constructor = Counter(form.constructor for form in SET_FORMS)
    written = written_constructors()
    problems = [
        f"the constructor {name} has no row"
        for name in sorted(written - set(count_by_constructor))
    ]
    problems += [
        f"the row {name} names no constructor of a set expression that a file writes"
        for name in sorted(set(count_by_constructor) - written)
    ]
    problems += [
        f"the constructor {name} has {count} rows"
        for name, count in count_by_constructor.items()
        if count > 1
    ]
    assert not problems, problem_lines(problems)


@pytest.mark.parametrize("form", SET_FORMS, ids=lambda form: form.constructor)
def test_the_example_of_each_set_form_lowers_to_a_set_of_its_constructor(form):
    """The declaration that a row of `SET_FORMS` gives as its example lowers
    to a set of the row's constructor."""
    assert type(declared_set_of(form.example)).__name__ == form.constructor


def test_each_row_of_the_set_forms_names_only_objects_whose_declaration_writes_a_set():
    """Each object in whose type a row of `SET_FORMS` says that its form is
    read is an object of `WITH_A_SET`, one whose declaration writes a
    set."""
    problems = [
        f"{row.constructor}: {', '.join(sorted(set(row.read_in) - set(WITH_A_SET)))} is no "
        f"object whose type holds a set"
        for row in SET_FORMS
        if set(row.read_in) - set(WITH_A_SET)
    ]
    assert not problems, problem_lines(problems)


# each form of a set in the type of each object whose declaration writes one
FORMS_IN_EACH_TYPE = [
    pytest.param(form, name, id=f"{form.constructor}-in-a-{name.replace(' ', '-')}")
    for form in SET_FORMS
    for name in WITH_A_SET
]


@pytest.mark.parametrize("form, name", FORMS_IN_EACH_TYPE)
def test_each_set_form_is_read_in_the_type_of_exactly_the_objects_that_its_row_names(form, name):
    """The set of the example of a row of `SET_FORMS`, written in the
    smallest stage text that declares an object of the row's kind with it,
    is read where the row names that kind and refused where it does not;
    the test fails where a read raises a refusal or a refusal is missing."""
    declared, colon, written = form.example.partition(" : ")
    assert colon and declared.isidentifier(), f"{form.example!r} is no declaration of one name"
    record = smallest_record(name, written)
    if name in form.read_in:
        elaborate_stage(record)
    else:
        with pytest.raises(ConstructionError):
            elaborate_stage(record)


# the limits of the language on a type


def test_each_row_of_the_table_of_limits_has_an_id_and_names_a_rule_of_the_refusal_catalogue():
    """Each row of `LIMITS`, which holds at least one row, has an id in
    `LIMIT_IDS` and names a rule of the three vocabularies of refusals."""
    assert LIMITS, "the table holds no limit"
    # LIMIT_IDS holds as many ids as LIMITS holds rows, since the next test
    # pairs them in order and would leave out a row without an id; a limit
    # added to the package makes this test fail until LIMIT_IDS has an id for
    # it
    assert len(LIMIT_IDS) == len(LIMITS), "LIMIT_IDS holds one id for each row of LIMITS"
    rules = every_rule()
    problems = [
        f"{row.line!r}: {row.rule} is no rule of the refusal catalogue"
        for row in LIMITS
        if row.rule not in rules
    ]
    assert not problems, problem_lines(problems)


@pytest.mark.parametrize(
    "limit", [pytest.param(limit, id=name) for limit, name in zip(LIMITS, LIMIT_IDS)]
)
def test_each_line_that_breaks_a_limit_on_a_type_is_refused_under_the_rule_of_its_row(limit):
    """The line that a row of `LIMITS` gives, written alone after
    `@stage: t`, is refused under the rule of the row."""
    assert "\n" not in limit.line, f"{limit.line!r} holds more than one line"
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(stage_record(f"@stage: t\n{limit.line}\n"))
    assert refused.value.rule == limit.rule


# the objects of a stage


def test_each_object_whose_declaration_writes_a_set_is_one_row_of_the_table_of_objects():
    """Each name of `WITH_A_SET` is the name of exactly one row of `OBJECTS`,
    which holds at least one row."""
    assert OBJECTS, "the table holds no object"
    object_names = [row.name for row in OBJECTS]
    problems = [
        f"{name} of WITH_A_SET is the name of no one row of OBJECTS"
        for name in WITH_A_SET
        if object_names.count(name) != 1
    ]
    assert not problems, problem_lines(problems)


@pytest.mark.parametrize("row", OBJECTS, ids=lambda row: row.name.replace(" ", "-"))
def test_the_record_that_each_row_of_the_table_of_objects_names_is_a_class_of_the_package(row):
    """The record that a row of `OBJECTS` names, as its module, a colon and
    its qualified name, resolves to a class of the package."""
    assert inspect.isclass(resolve(row.record)), f"{row.record} is no class of the package"


@pytest.mark.parametrize("row", OBJECTS, ids=lambda row: row.name.replace(" ", "-"))
def test_the_line_that_each_row_of_the_table_of_objects_quotes_is_a_line_of_the_file_it_names(
    row,
):
    """The line that a row of `OBJECTS` quotes is a line of the row's file,
    read without its annotation."""
    lines = (ROOT / row.file).read_text(encoding="utf-8").splitlines()
    # a line of the file is compared without its annotation, which a row
    # leaves out
    assert row.line in [line.partition("::")[0].rstrip() for line in lines]


@pytest.mark.parametrize("row", OBJECTS, ids=lambda row: row.name.replace(" ", "-"))
def test_the_expression_that_each_row_of_the_table_of_objects_gives_evaluates_on_its_stage(
    row, request
):
    """The expression that a row of `OBJECTS` gives evaluates on the stage
    that the row's file states; the test fails where the expression
    raises."""
    assert row.file in STAGE_FIXTURE_BY_FILE, f"no stage of this test is built from {row.file}"
    stage = request.getfixturevalue(STAGE_FIXTURE_BY_FILE[row.file])
    # the expression is text of the package's own table, in which `stage`
    # names the stage
    eval(row.read_by, {"stage": stage})


# the conditions that the declared sets of the explicit consumption stage
# settle: the stage `cons` with the lines of its policy block written in the
# stage file (the fixtures `cons_with_egm_lines` and
# `cons_with_egm_lines_text`), whose feasibility correspondence is `Γ(x : ℝ₊₊)
# := (0, x]` and whose control c is declared on ℝ₊₊


# the feasibility correspondence of the explicit consumption stage
FEASIBLE_SET = "Γ(x : ℝ₊₊) := (0, x]"


@pytest.fixture(scope="module")
def stage_with_a_feasible_set_from_minus_ten_to_ten(cons_with_egm_lines_text):
    """The explicit consumption stage with the feasible set [−10, 10], which
    reaches below the declared set ℝ₊₊ of the control."""
    text = changed(cons_with_egm_lines_text, (FEASIBLE_SET, "Γ(x : ℝ₊₊) := [-10, 10]"))
    return stage_from_text(text, "unrestricted_correspondence.bl")


@pytest.fixture(scope="module")
def stage_with_a_feasible_set_on_an_argument_up_to_infinity(cons_with_egm_lines_text):
    """The explicit consumption stage whose feasible set (0, x] reads an
    argument declared on [0, inf], so that the set may reach infinity."""
    text = changed(cons_with_egm_lines_text, (FEASIBLE_SET, "Γ(x : [0,inf]) := (0, x]"))
    return stage_from_text(text, "extended_correspondence.bl")


def test_the_aggregation_into_the_decision_perch_outputs_a_function_into_its_declared_range(
    cons_with_egm_lines,
):
    """The aggregation of the builder `cntn_to_dcsn` of the explicit
    consumption stage outputs a function from Xm into [−∞, ∞), the set that
    its header declares for V."""
    aggregation = cons_with_egm_lines.dcsn.builder.bwd["Aggregation"].denote()
    assert aggregation.outputs[0].type == "Xm → [−∞, ∞)"


def test_finite_real_arithmetic_is_a_condition_of_the_policy_and_not_of_the_builder_into_decision(
    cons_with_egm_lines,
):
    """The explicit consumption stage records the condition
    `finite-real-arithmetic` at the maximization line of its policy and
    records none at the value line of the builder `cntn_to_dcsn`."""
    conditions = tuple(cons_with_egm_lines.obligations())
    # the condition of a line of a block stands at that line, where the
    # declared sets of the operands of a sum allow `inf - inf`
    assert not any(
        item.condition == "finite-real-arithmetic" and str(item.entries[0]) == "cntn_to_dcsn.value"
        for item in conditions
    )
    assert any(
        item.condition == "finite-real-arithmetic" and str(item.entries[0]) == "policy.optimality"
        for item in conditions
    )


@pytest.mark.parametrize(
    "stage_fixture, expected",
    [
        pytest.param("cons_with_egm_lines", [], id="within-the-control-set"),
        pytest.param(
            "stage_with_a_feasible_set_from_minus_ten_to_ten",
            [("[−10, 10]", "ℝ₊₊")],
            id="from-minus-ten-to-ten",
        ),
        pytest.param(
            "stage_with_a_feasible_set_on_an_argument_up_to_infinity",
            [("(0, x]", "ℝ₊₊")],
            id="on-an-argument-up-to-infinity",
        ),
    ],
)
def test_a_range_compatibility_is_recorded_where_the_feasible_set_may_leave_the_control_set(
    stage_fixture, expected, request
):
    """The maximization statement of the policy records the condition
    `range-compatibility` between its feasible set and the declared set of
    the control only where the feasible set may leave that set."""
    conditions = tuple(request.getfixturevalue(stage_fixture).obligations())
    # the stage records conditions at the maximization statement
    assert any(
        item.condition == "finite-real-arithmetic" and str(item.entries[0]) == "policy.optimality"
        for item in conditions
    )
    # the entries of the condition: the line, the feasible set and the
    # declared set of the control, then the formula
    recorded = [
        tuple(map(typed_expressions.format_expression, item.entries[1:3]))
        for item in conditions
        if item.condition == "range-compatibility" and str(item.entries[0]) == "policy.optimality"
    ]
    assert recorded == expected


@pytest.mark.parametrize(
    "stage_fixture, expected",
    [
        pytest.param("cons_with_egm_lines", [], id="within-the-control-set"),
        pytest.param(
            "stage_with_a_feasible_set_from_minus_ten_to_ten",
            [("function-argument-domain-inclusion", ("[−10, 10]", "ℝ₊₊"))],
            id="from-minus-ten-to-ten",
        ),
        pytest.param(
            "stage_with_a_feasible_set_on_an_argument_up_to_infinity",
            [("function-argument-domain-inclusion", ("(0, x]", "ℝ₊₊"))],
            id="on-an-argument-up-to-infinity",
        ),
    ],
)
def test_a_domain_condition_is_recorded_only_where_the_feasible_set_may_leave_the_utility_domain(
    stage_fixture, expected, request
):
    """Of the two domain conditions `binding-domain` and
    `function-argument-domain-inclusion`, the maximization statement of the
    policy records only the second, and only where its feasible set may
    leave the declared domain ℝ₊₊ of the argument of 𝑢."""
    conditions = tuple(request.getfixturevalue(stage_fixture).obligations())
    # the stage records conditions at the maximization statement
    assert any(
        item.condition == "finite-real-arithmetic" and str(item.entries[0]) == "policy.optimality"
        for item in conditions
    )
    # the entries of the condition: the line, the function, its argument, the
    # feasible set and the declared domain of the argument
    recorded = [
        (item.condition, tuple(map(typed_expressions.format_expression, item.entries[-2:])))
        for item in conditions
        if item.condition in {"binding-domain", "function-argument-domain-inclusion"}
        and "policy.optimality" in tuple(map(str, item.entries))
    ]
    assert recorded == expected


def test_the_marginal_line_into_the_decision_perch_records_no_range_compatibility_of_its_own(
    cons_with_egm_lines,
):
    """The marginal line `D_{m_d}V = 𝑑𝑢(c)` of the builder `cntn_to_dcsn` of
    the explicit consumption stage records no condition
    `range-compatibility` of its own."""
    conditions = tuple(cons_with_egm_lines.obligations())
    # the stage records conditions at the marginal line, under the address
    # that the check below reads
    assert any(
        item.condition == "marginal-reading" and str(item.entries[0]) == "cntn_to_dcsn.marginal"
        for item in conditions
    )
    assert not any(
        item.condition == "range-compatibility" and str(item.entries[0]) == "cntn_to_dcsn.marginal"
        for item in conditions
    )


def test_the_line_that_sets_the_control_to_its_candidate_records_no_range_compatibility(
    cons_with_egm_lines,
):
    """The line `c = c[>]` of the policy block of the explicit consumption
    stage records no condition `range-compatibility`, since its right side,
    the candidate c[>], declares no range."""
    conditions = tuple(cons_with_egm_lines.obligations())
    # the stage records a range compatibility at another line, the law of
    # motion `a = m_d - c` of the builder `dcsn_to_cntn`
    assert any(
        item.condition == "range-compatibility" and str(item.entries[0]) == "dcsn_to_cntn.1"
        for item in conditions
    )
    assert not any(
        item.condition == "range-compatibility" and str(item.entries[0]) == "policy.cons_choice"
        for item in conditions
    )


def test_no_condition_of_the_explicit_stage_states_an_inclusion_of_one_set_in_another(
    cons_with_egm_lines,
):
    """No condition of the explicit consumption stage has a formula that
    states an inclusion `⊆`, since a range compatibility is the membership
    of the value that a line writes, at each point."""
    conditions = tuple(cons_with_egm_lines.obligations())
    # the stage records a range compatibility that has a formula
    assert any(
        item.condition == "range-compatibility" and item.predicate is not None
        for item in conditions
    )
    assert not any(
        item.predicate is not None
        and "⊆" in typed_expressions.format_expression(item.predicate, width=None)
        for item in conditions
    )


def test_the_membership_of_the_arrival_value_in_the_reals_is_one_condition_of_its_aggregation(
    cons_with_egm_lines,
):
    """The formula `V≺(m) ∈ ℝ` stands in one condition of the explicit
    consumption stage, the admissibility of the aggregation of
    `dcsn_to_arvl`, and in no separate range compatibility of its line
    `dcsn_to_arvl.value`."""
    # the arrival value is a function of the arrival state m alone: the line
    # `V[<] = V` reads the decision value, which the line `m_d = m` makes a
    # function of m, and no line reads the second arrival state l
    assert [
        str(item.entries[0])
        for item in cons_with_egm_lines.obligations()
        if item.predicate is not None
        and typed_expressions.format_expression(item.predicate, width=None) == "V≺(m) ∈ ℝ"
    ] == ["dcsn_to_arvl:Aggregation"]
