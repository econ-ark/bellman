"""Constraints on the cards and in the syntax: the complementary-slackness
clause on the candidate line and on the first-order condition, the declared
multiplier, the Kuhn–Tucker condition of a clause, the law of motion under
`Where`, the grid line, the refusals of a malformed clause, and feasibility
correspondences."""

import functools
import json
import re

import pytest
from application_files import COPIED_FILES_FOLDER, ROOT
from printed_text import (
    INDENT,
    Unparsed,
    card_section_lines,
    flat,
    is_short_line,
    operations_entries,
    parse_card,
)
from stage_builders import stage_from_text
from stage_graphs import DIRECTIONS
from stage_texts import (
    ARGMAX_DOC_LINE,
    BUDGET_SET_LINE,
    BUFFER_STOCK_READING_L,
    BUFFER_STOCK_WRITING_L,
    BUNDLES,
    CHANGES_TO_READ_L,
    JOINT_CHOICE,
    buffer_stock_text,
    changed,
)

from bellman.native.hypergraphs import copy_native
from bellman.refusal_examples import INVERSE_EULER
from bellman.refusals import ConstructionError
from bellman.stage.boxes import kind_of
from bellman.stage.stage_answers import fields, obligations
from bellman.stage.term_operations import kuhn_tucker, slack
from bellman.syntax import terms
from bellman.syntax.decode import from_json
from bellman.syntax.lower import item_addresses, parse_with_spans, to_json
from bellman.syntax.source import to_source
from bellman.typing import typed_expressions

# the relation that the identification's `signature()` answers, without its
# white space: the saving over Xa, each value that the candidate admits
# there, and the grid line read at that value; one quantifier or two, the
# parentheses of its statement written or not
OVER_THE_ADMITTED_PAIRS = re.compile(r"∀a∈Xa,(∀)?x∈𝑐≻\(a\):\(?f\(a\+x\)=x\)?")


# a methods file that binds a representation of the policy, `!Linear`, at the
# Evaluation that closes the policy builder of `cons_kt`
LINEAR_EVALUATION = {
    "text": "@methods: cons_kt\npolicy.evaluate.method : !Linear\n",
    "origin": "cons_kt.methods.bl",
}


# the terms of the slack and of the Kuhn–Tucker system: the bounded quantity
# x, the bound b, and the left and the right side of a line
X, BOUND, LEFT, RIGHT = (terms.Sym(terms.Constant(name)) for name in ("x", "b", "l", "r"))


ZERO = terms.Number(0)


# the malformed declarations of a multiplier and the malformed clauses, each
# as the stage text that it changes, the text as written and as changed, and
# the rule under which it is refused: the multiplier of `cons_obs.bl`
# written without its clause, with two bounds, at the arrival perch, without
# a mark, bounding the control or a decision state, declared twice, with its
# bound written with the number first, or listed on the header of its block;
# and the clause of the first-order condition of `cons_kt` written as a
# chain that descends, is strict or is mixed, or with its one bound written
# with the number first, whose Kuhn–Tucker condition would take the reversed
# sign
DECLARED_MULTIPLIER = "μ[>]   : ℝ₊ ⟂ a >= 0"


FIRST_ORDER_CLAUSE = "⟂ m_d - c >= 0"


def malformed_multiplier(written, rule, name):
    """A row of `MALFORMED_CLAUSES` that writes the declared multiplier of
    `cons_obs.bl` as `written`."""
    return pytest.param("cons_obs_file_text", DECLARED_MULTIPLIER, written, rule, id=name)


def malformed_clause(written, name):
    """A row of `MALFORMED_CLAUSES` that writes the clause of the
    first-order condition of `cons_kt` as `written`."""
    return pytest.param("cons_kt_text", FIRST_ORDER_CLAUSE, written, "readable-form", id=name)


MALFORMED_CLAUSES = [
    malformed_multiplier("μ[>]   : ℝ₊", "syntax", "multiplier-without-its-clause"),
    malformed_multiplier(
        "μ[>]   : ℝ₊ ⟂ 0 <= a <= 1", "multiplier-declaration", "multiplier-with-two-bounds"
    ),
    malformed_multiplier(
        "μ[<]   : ℝ₊ ⟂ a >= 0", "multiplier-declaration", "multiplier-at-the-arrival-perch"
    ),
    malformed_multiplier(
        "μ      : ℝ₊ ⟂ a >= 0", "multiplier-declaration", "multiplier-without-a-mark"
    ),
    malformed_multiplier(
        "μ[>]   : ℝ₊ ⟂ c >= 0", "multiplier-declaration", "multiplier-bounding-the-control"
    ),
    malformed_multiplier(
        "μ[>]   : ℝ₊ ⟂ m_d >= 0", "multiplier-declaration", "multiplier-bounding-a-decision-state"
    ),
    malformed_multiplier(
        "μ[>]   : ℝ₊ ⟂ a >= 0\n    μ[>]   : ℝ₊ ⟂ a >= 0",
        "multiplier-declaration",
        "multiplier-declared-twice",
    ),
    malformed_multiplier(
        "μ[>]   : ℝ₊ ⟂ 0 <= a", "readable-form", "multiplier-bound-with-the-number-first"
    ),
    pytest.param(
        "cons_obs_file_text",
        "inf) @ !vlu) : !cntn ->",
        "inf) @ !vlu, μ[>] : ℝ₊) : !cntn ->",
        "multiplier-declaration",
        id="multiplier-listed-on-the-header",
    ),
    malformed_clause("⟂ 1 >= a >= 0", "descending-chain"),
    malformed_clause("⟂ 0 < a <= 1", "strict-chain"),
    malformed_clause("⟂ 0 <= a >= 1", "mixed-chain"),
    malformed_clause("⟂ 0 <= a", "one-bound-with-the-number-first"),
]


# the builders of one direction of a stage whose cards have a Where section
# that names the law of motion or its section at a label, by the fixture of
# the stage and the direction. The rows of `tenure` are in the default set,
# since each of its three builder cards has a Where section and no card of
# the consumption stage has one.
DIRECTION_WORDS = {"bwd": "backward", "fwd": "forward"}


def where_row(name, direction, default=False):
    """A row of `WHERE_CARDS`, marked `complete_set` unless it is a row of
    the default set."""
    marks = () if default else pytest.mark.complete_set
    return pytest.param(name, direction, id=f"{name}-{DIRECTION_WORDS[direction]}", marks=marks)


WHERE_CARDS = [
    where_row("tenure", "bwd", default=True),
    where_row("tenure", "fwd", default=True),
    where_row("retiree_death", "bwd"),
    where_row("keeper_saving", "bwd"),
    where_row("adjuster_saving", "bwd"),
    where_row("adjuster_cons_with_egm_lines", "bwd"),
    where_row("adjuster_cons_with_clause_on_candidate_line", "bwd"),
    where_row("ret_choice", "bwd"),
    where_row("ret_choice", "fwd"),
    where_row("house_choice", "bwd"),
    where_row("house_choice", "fwd"),
    where_row("young_choice", "bwd"),
    where_row("young_choice", "fwd"),
    where_row("old_choice", "bwd"),
    where_row("old_choice", "fwd"),
    where_row("worker_ageing", "bwd"),
    where_row("worker_ageing", "fwd"),
    where_row("entrepreneur_death", "bwd"),
    where_row("entrepreneur_ageing", "bwd"),
    where_row("entrepreneur_ageing", "fwd"),
    where_row("fecundity", "bwd"),
    where_row("fecundity", "fwd"),
]


# the columns of a row of `Signature`: the word `in` or `out` at column two,
# the name at column seven, where its short line starts as well
WIRE = 7


# the feasible set of a joint choice that is the product `[0, z] × ℝ₊`
PRODUCT_LINE = "Γ(z : ℝ₊) := [0, z] × ℝ₊"


# the annotation that an author writes on the line of a feasible set
ANNOTATION = ' :: [id=feasible, "the authored set"]'


# the stage of a joint choice of the coordinates of `u` whose feasible set is
# the product, which the binder of the maximization statement names at the
# decision state
ON_A_PRODUCT = (
    JOINT_CHOICE.replace("@stage: joint_choice", "@stage: joint_choice\n" + PRODUCT_LINE)
    .replace("x : ℝ", "x : ℝ₊")
    .replace("x_d : ℝ", "x_d : ℝ₊")
    .replace("u : ℝ × ℝ", "u : ℝ₊ × ℝ₊")
    .replace("argmax_{u}", "argmax_{u : Γ(x_d)}")
)


# the same stage with three coordinates of `u` and the budget set
# `BUDGET_SET_LINE`
ON_A_BUDGET_SET = ON_A_PRODUCT.replace(PRODUCT_LINE, BUDGET_SET_LINE).replace(
    "u : ℝ₊ × ℝ₊", "u : ℝ₊ × ℝ₊ × ℝ₊"
)


def annotated(text):
    """`text` with `ANNOTATION` on the line of its feasible set."""
    return text.replace("\n[id=arvl", ANNOTATION + "\n[id=arvl", 1)


def unused(text):
    """`text` with the bare binder `argmax_{u}`, so that no line names the
    feasible set."""
    return text.replace("argmax_{u : Γ(x_d)}", "argmax_{u}")


def indexed(body):
    """The stage of a product with its feasible set unused and written as
    `body`, after the declarations of the integers `J` and `κ`."""
    feasible = "J : ℕ\nκ : ℤ\nΓ(z : ℝ₊) := " + body
    return unused(ON_A_PRODUCT.replace(PRODUCT_LINE, feasible))


FEASIBLE_SETS = {
    "product": ON_A_PRODUCT,
    "comprehension": ON_A_BUDGET_SET,
    "comprehension-with-an-inequality": ON_A_BUDGET_SET.replace("= z}", "= z, q[3] <= z}"),
    "comprehension-at-a-state-named-q": ON_A_BUDGET_SET.replace("x_d", "q"),
    "annotated-product": annotated(ON_A_PRODUCT),
    "annotated-comprehension": annotated(ON_A_BUDGET_SET),
    "integer-range": indexed("{0, …, J} × ℝ₊"),
    "list-of-integers": indexed("{0, κ} ⊂ ℤ × ℝ₊"),
    "unused-product": unused(ON_A_PRODUCT),
    "comprehension-on-a-bounded-base": unused(
        ON_A_BUDGET_SET.replace("q : ℝ₊ × ℝ₊ × ℝ₊", "q : [0, z] × ℝ₊ × ℝ₊")
    ),
    "interval-and-labels": unused(ON_A_PRODUCT.replace("[0, z] × ℝ₊", "(0, z) × {low, high}")),
}


# the stages whose maximization statement names the feasible set
NAMED_FEASIBLE_SETS = [
    "product",
    "comprehension",
    "comprehension-with-an-inequality",
    "comprehension-at-a-state-named-q",
]


# declarations whose body decides what they define: a tuple or a formula after
# `:=` defines a function, an interval or a comprehension a correspondence
DECLARATIONS = [
    pytest.param("f(z : ℝ) := (z, z + 1)", terms.FuncDef, id="tuple"),
    pytest.param("Γ(z : ℝ) := (0, z]", terms.CorrDef, id="interval-open-below"),
    pytest.param("Γ(z : ℝ) := [0, z)", terms.CorrDef, id="interval-open-above"),
    pytest.param("Γ(z : ℝ) := [0, z]", terms.CorrDef, id="closed-interval"),
    pytest.param("Γ(z : ℝ) := {q : ℝ | q < z}", terms.CorrDef, id="comprehension"),
    pytest.param("f(z : ℝ) := z + 1", terms.FuncDef, id="formula"),
]


def operations_of(card):
    """The section `Operations` of a printed card, as one text."""
    return "\n".join(card_section_lines(card, "Operations"))


def cards_with_a_where_section(stage, direction):
    """Each builder of one direction of a stage whose card has a Where
    section, with its card, as pairs `(builder, card)`; `direction` is `bwd`
    or `fwd`."""
    graph = getattr(stage.builder, direction)
    cards = [(graph[name], str(graph[name])) for name in graph.list()]
    return [(builder, card) for builder, card in cards if card_section_lines(card, "Where")]


def signature_wires(lines):
    """The wires of a `Signature` section, one per row, `(word, name,
    carrier)`: the word `in` or `out`, carried down to the rows under it, the
    name five columns after the word, where every further name under the
    word stands, and the carrier after ` : `; a deeper line continues the
    carrier of the row above, and a line opening with `: ` gives the carrier
    of a name too long for its column. The short line and the words of the
    directions on the stage's card are no rows."""
    found, word, name_at = [], None, None
    for line in lines:
        body = line.strip()
        if not body or is_short_line(line) or body in DIRECTIONS:
            continue
        at = len(line) - len(line.lstrip(" "))
        label = re.match(r"(in|out)(?: {2,}(?=\S)|$)", body)
        if label is not None and (name_at is None or at < name_at):
            word, name_at = label.group(1), at + WIRE - INDENT
        elif name_at is None or at != name_at:
            if found and body.startswith(": "):
                found[-1][2] = body[2:]
            elif found:
                found[-1][2] = (found[-1][2] + " " + body).strip()
            else:
                raise Unparsed(f"a row of `Signature` opens with `in` or `out`: {line!r}")
            continue
        name, colon, carrier = line[name_at:].partition(" : ")
        found.append([word, name.strip(), carrier.strip()])
    return [tuple(entry) for entry in found]


def first_statement(text):
    """The statement that the first line of a stage text after its header
    parses to."""
    parsed = parse_with_spans(text).term
    return next(item.core for item in parsed.items if isinstance(item, terms.Statement))


def domain_of(body):
    """The product that the body of a feasible set ranges over: the body
    itself where it is a product, the base of a comprehension otherwise."""
    return body if isinstance(body, terms.Product) else body.base


@pytest.fixture(scope="module")
def inverse_euler_example():
    """The example stage of the package whose candidate line, with its
    clause, inverts the Euler equation on the saving `a ∈ ℝ₊`."""
    return stage_from_text(INVERSE_EULER, "t.bl")


@pytest.fixture(scope="module")
def cons_kt_with_a_linear_evaluation(cons_kt):
    """A copy of `cons_kt` methodized with `LINEAR_EVALUATION`, which binds
    the representation `!Linear` at the Evaluation of the policy builder."""
    return copy_native(cons_kt).methodize(LINEAR_EVALUATION)


@pytest.fixture(scope="module")
def two_bound_clause_text(cons_kt_text):
    """`cons_kt` with the clause of its first-order condition written with
    two bounds, `⟂ 0 <= m_d - c <= 1`."""
    return changed(cons_kt_text, (FIRST_ORDER_CLAUSE, "⟂ 0 <= m_d - c <= 1"))


@pytest.fixture(scope="module")
def constraint_texts(cons_obs_file_text, two_bound_clause_text):
    """The stage texts whose syntax round-trips through its JSON encoding, by
    the row ids of that test."""
    return {
        "declared-multiplier": cons_obs_file_text,
        "two-bound-clause": two_bound_clause_text,
        "annotated-product": FEASIBLE_SETS["annotated-product"],
        "annotated-comprehension": FEASIBLE_SETS["annotated-comprehension"],
    }


@pytest.fixture(scope="module")
def worker_saving_with_its_methods(worker_saving):
    """A copy of the pension worker's saving stage methodized with its
    methods file, whose two first-order conditions carry the clauses of the
    two controls."""
    return copy_native(worker_saving).methodize(
        ROOT / "applications/pension-retirement/declaration/stages/worker_saving/methods.bl"
    )


@pytest.fixture(scope="module")
def feasible_set_reads_the_field():
    """The buffer-stock stage whose feasible set `Γ_c` reads the
    continuation field `L[>]`, which the header of the policy block lists."""
    return stage_from_text(BUFFER_STOCK_READING_L, "buffer_stock.bl")


@pytest.fixture(scope="module")
def value_block_also_writes_the_field():
    """The same stage, whose value block and arrival block also write the
    field `L` as they write the value."""
    return stage_from_text(changed(BUFFER_STOCK_WRITING_L, *CHANGES_TO_READ_L), "buffer_stock.bl")


@pytest.fixture(scope="module")
def no_line_reads_the_field():
    """The buffer-stock stage whose policy block lists `L[>]` in its header,
    and whose feasible set and other lines do not read it."""
    _, listed = CHANGES_TO_READ_L
    return stage_from_text(changed(buffer_stock_text(), listed), "buffer_stock.bl")


@pytest.fixture(scope="module")
def cons_without_the_maximization_statement(cons_with_egm_lines_text):
    """`cons.bl` with the policy lines of the candidate line and without its
    maximization statement, so that no line names a feasibility
    correspondence."""
    return stage_from_text(
        changed(cons_with_egm_lines_text, (ARGMAX_DOC_LINE, "")), "cons_law_image.bl"
    )


@pytest.fixture(scope="module")
def mckenzie():
    """The accumulation stage of `mckenzie-1976`, whose feasible set holds
    the terminal stocks at which the utility, which the file leaves
    undefined, exceeds `-inf`."""
    path = f"{COPIED_FILES_FOLDER}/mckenzie-1976/accumulation.bl"
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


@pytest.fixture(scope="module")
def bundles():
    """The stage `BUNDLES`, whose maximization statement binds its own
    letter `cp` over the correspondence `Γ(k_d)`."""
    return stage_from_text(BUNDLES, "bundles.bl")


@pytest.fixture(scope="module")
def feasible_set_stage():
    """`feasible_set_stage(name)`: the stage of the text
    `FEASIBLE_SETS[name]`, elaborated once for the module."""
    return functools.cache(lambda name: stage_from_text(FEASIBLE_SETS[name], f"{name}.bl"))


@pytest.fixture(scope="module")
def feasible_set_encoding():
    """`feasible_set_encoding(name)`: the encoding of the stage of the text
    `FEASIBLE_SETS[name]` cut before its block `dcsn_to_cntn`, which holds
    the feasible set and the arrival block and is small."""

    def encoding(name):
        text = FEASIBLE_SETS[name]
        return stage_from_text(text[: text.index("[id=dcsn_to_cntn")], f"{name}.bl").encoding()

    return functools.cache(encoding)


def test_the_policy_builder_of_the_candidate_line_lists_its_operations_in_order(
    cons_with_egm_lines,
):
    """The policy builder of the candidate line with its clause holds the
    candidate and the grid line as two Aggregations, the identification as a
    Pullback, and the Evaluation, in this order."""
    policy = cons_with_egm_lines.builder.policy
    assert [str(key) for key in policy.primitives.list()] == [
        "InvEuler:Aggregation",
        "endoggrid:Aggregation",
        "cons_choice:Pullback",
        "Evaluation",
    ]


@pytest.mark.parametrize(
    "name, key, correspondence",
    [
        pytest.param(
            "cons_with_egm_lines", "InvEuler:Aggregation", "𝑐≻ : Xa ⇉ ℝ₊₊", id="cons-candidate"
        ),
        pytest.param(
            "cons_with_egm_lines",
            "endoggrid:Aggregation",
            "𝑚_d≻ : Xa ⇉ Xm",
            id="cons-cash-on-hand",
        ),
        pytest.param(
            "inverse_euler_example",
            "InvEuler:Aggregation",
            "𝑐≻ : ℝ₊ ⇉ ℝ₊₊",
            id="example-candidate",
        ),
        pytest.param(
            "inverse_euler_example", "grid:Aggregation", "𝑚≻ : ℝ₊ ⇉ ℝ₊", id="example-cash-on-hand"
        ),
    ],
)
def test_with_its_clause_a_candidate_and_its_cash_on_hand_are_typed_as_correspondences(
    request, name, key, correspondence
):
    """The candidate and the cash on hand at each saving of a candidate line
    with its clause are typed as correspondences of the saving, `⇉`, on the
    card of the operation that writes each and in its signature, and no
    operation of the policy builder types them as functions."""
    policy = request.getfixturevalue(name).builder.policy
    operation = policy[key]
    assert flat("out " + correspondence) in flat(str(operation))
    assert flat("out " + correspondence) in flat(str(operation.signature()))
    signatures = flat(
        "".join(str(policy[str(other)].signature()) for other in policy.primitives.list())
    )
    assert flat(correspondence.replace("⇉", "→")) not in signatures


def test_the_identification_relates_the_policy_and_the_candidate_over_the_admitted_pairs(
    cons_with_egm_lines,
):
    """The set of policies that the identification's `signature()` answers
    reads the grid line at each value that the candidate admits at each
    saving, `f(a + x) = x`, in place of reading the policy at the cash on
    hand at each saving, `f(𝑚_d≻(a))`."""
    relation = flat(str(cons_with_egm_lines.builder.policy["cons_choice:Pullback"].signature()))
    assert OVER_THE_ADMITTED_PAIRS.search(relation), relation
    assert "f(𝑚_d≻(a))" not in relation


def test_a_clause_on_an_inequality_keeps_the_sign_that_the_candidate_line_writes(
    cons_with_egm_lines,
):
    """The rule of the Aggregation of the inequality candidate line of
    `cons.bl` keeps the sign `≤` that the line writes, with the clause read
    at the saving."""
    card = str(cons_with_egm_lines.builder.policy)
    assert "     rule: 𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) ⟂ a ≥ 0\n" in card


def test_a_first_order_condition_with_its_clause_forms_one_aggregation_read_at_the_point(cons_kt):
    """The first-order condition with its clause, `𝑑𝑢(c) = D_{a}V[>] ⟂ m_d -
    c >= 0`, forms one Aggregation after the Pullback, whose rule reads the
    condition and its clause at the decision state with the policy on `Xm`,
    with no Where section."""
    policy = cons_kt.builder.policy
    assert [str(key) for key in policy.primitives.list()] == [
        "Pullback",
        "euler:Aggregation",
        "Evaluation",
    ]
    printed = "\n".join(card_section_lines(str(policy), "Operations"))
    assert flat("𝑑𝑢(𝑐(m_d))") in flat(printed)
    assert flat("⟂ m_d − 𝑐(m_d) ≥ 0") in flat(printed)
    clause = next(line for line in printed.splitlines() if "⟂" in line)
    assert clause.rstrip().endswith("on Xm") and card_section_lines(str(policy), "Where") == []


def test_the_stage_cons_kt_records_its_arithmetic_aggregation_marginal_and_range_conditions(
    cons_kt,
):
    """The conditions that `cons_kt` records are those of its arithmetic,
    its aggregations, the reading of its marginal value and its ranges."""
    assert [item.condition for item in obligations(cons_kt)] == [
        "arithmetic-definedness",
        "aggregation-admissibility",
        "marginal-reading",
        "aggregation-admissibility",
        "range-compatibility",
        "range-compatibility",
    ]


def test_a_representation_bound_at_the_evaluation_changes_no_rule_of_the_policy_builder(
    cons_kt, cons_kt_with_a_linear_evaluation
):
    """Binding the representation `!Linear` at the Evaluation leaves the
    section `Operations` of the policy builder's card as it prints before
    the binding."""
    methodized = cons_kt_with_a_linear_evaluation
    # the representation is bound at the Evaluation
    assert [box for box, method in methodized.methods.items() if method.word == "!Linear"] == [
        "policy.evaluate"
    ]
    printed = "\n".join(card_section_lines(str(cons_kt.builder.policy), "Operations"))
    assert "\n".join(card_section_lines(str(methodized.builder.policy), "Operations")) == printed


def test_a_representation_bound_at_the_evaluation_adds_the_condition_evaluation_domain(
    cons_kt, cons_kt_with_a_linear_evaluation
):
    """Binding the representation `!Linear` at the Evaluation adds one
    condition to those of the stage, `evaluation-domain`: that the
    representation is evaluated only where its data support the policy."""
    assert [item.condition for item in obligations(cons_kt_with_a_linear_evaluation)] == [
        *(item.condition for item in obligations(cons_kt)),
        "evaluation-domain",
    ]


def test_with_a_multiplier_the_candidate_and_cash_on_hand_are_functions_on_admitted_pairs(
    cons_obs,
):
    """The Aggregation of the multiplier spelling, whose input is `𝑉≻`,
    types its two outputs, the candidate and the cash on hand at each
    saving, as functions on the set of admitted pairs."""
    aggregation = str(cons_obs.builder.policy.primitives["endoggrid:Aggregation"])
    assert "𝑉≻" in aggregation
    assert aggregation.count("{a, μ ∈ Xa × ℝ₊ | a ≥ 0 ∧ μ · a = 0} → ") == 2


def test_with_a_multiplier_the_identification_quantifies_once_over_the_admitted_pairs(cons_obs):
    """The relation of the identification of the multiplier spelling
    quantifies once over the set of admitted pairs, `∀ (a, μ) ∈ {…}, x ∈
    …`, and over neither of its factors alone."""
    relation = typed_expressions.format_expression(
        cons_obs.builder.policy.primitives["cons_choice:Pullback"].denote().expression, width=None
    )
    assert "∀ (a, μ) ∈ {a, μ ∈ Xa × ℝ₊ | a ≥ 0 ∧ μ · a = 0}, x ∈ " in relation
    assert "∈ Xa × ℝ₊:" not in relation and "μ ∈ ℝ₊:" not in relation


def test_a_declared_multiplier_is_a_field_of_the_continuation_perch_with_its_own_role(cons_obs):
    """The multiplier `μ[>]` that the policy block of `cons_obs.bl` declares
    is a field of the continuation perch with the role `multiplier`."""
    assert fields(cons_obs)["cons_obs:cntn:μ"].role == "multiplier"


def test_a_declared_multiplier_has_a_definition_that_prints_its_line(cons_obs):
    """The definitions of `cons_obs` list one multiplier, `μ`, whose
    denotation prints its declaration as the file writes it."""
    assert [str(i) for i in cons_obs.definitions.list()["multiplier"]] == ["cons_obs:multiplier:μ"]
    assert "μ[>]   : ℝ₊ ⟂ a >= 0" in str(cons_obs.definitions.denote("cons_obs:multiplier:μ"))


def test_a_declared_multiplier_forms_no_operation_of_the_policy_builder(cons_obs):
    """The policy builder of `cons_obs` holds the Aggregation of the
    candidate and the grid line, the identification and the Evaluation, and
    no operation of the declaration of the multiplier."""
    # the stage declares the multiplier, a field of its continuation perch
    assert fields(cons_obs)["cons_obs:cntn:μ"].role == "multiplier"
    policy = cons_obs.builder.policy
    assert [str(k) for k in policy.primitives.list()] == [
        "endoggrid:Aggregation",
        "cons_choice:Pullback",
        "Evaluation",
    ]


def test_the_policy_builder_card_prints_the_line_of_a_declared_multiplier_once(cons_obs):
    """The card of the policy builder of `cons_obs` prints the line that
    declares the multiplier once, under `Source`."""
    assert str(cons_obs.builder.policy).count("μ[>]   : ℝ₊ ⟂ a >= 0") == 1


def test_no_backward_builder_but_the_policy_builder_reads_a_declared_multiplier(cons_obs):
    """No backward builder of `cons_obs` other than the policy builder reads
    the multiplier: the decision builder reads `𝑉≻` on the saving alone, and
    no other backward card names `μ`."""
    # the stage declares the multiplier, a field of its continuation perch
    assert fields(cons_obs)["cons_obs:cntn:μ"].role == "multiplier"
    backward = cons_obs.builder.bwd
    decision = parse_card(str(backward["cntn_to_dcsn"]))["sections"]["Signature"]
    assert ("in", "𝑉≻", "Xa → [−∞, ∞)") in signature_wires(decision)
    named = [name for name in backward.list() if name != "policy" and "μ" in str(backward[name])]
    assert named == []


def test_a_declared_multiplier_is_no_wire_of_the_policy_builder(cons_obs):
    """The multiplier of `cons_obs` is neither an input nor an output of the
    policy builder's `signature()`."""
    # the stage declares the multiplier, a field of its continuation perch
    assert fields(cons_obs)["cons_obs:cntn:μ"].role == "multiplier"
    policy = cons_obs.builder.policy
    wires = [str(w.identity) for w in policy.signature().inputs + policy.signature().outputs]
    assert "cons_obs:cntn:μ" not in wires


def test_the_declaration_of_a_multiplier_parses_to_a_declaration_with_its_clause(
    cons_obs_file_text,
):
    """The line `μ[>] : ℝ₊ ⟂ a >= 0` of `cons_obs.bl` parses to a
    declaration that holds its clause, whose source prints as the file
    writes it."""
    term, _ = parse_with_spans(cons_obs_file_text, "cons_obs.bl")
    declaration = dict(item_addresses(term))["policy.slackness"]
    assert isinstance(declaration, terms.Declare)
    assert isinstance(declaration.declaration, terms.Complementary)
    assert to_source(declaration.declaration) == "μ[>] : ℝ₊ ⟂ a >= 0"


def test_a_two_bound_clause_parses_to_a_chain_and_prints_as_written(two_bound_clause_text):
    """The clause `⟂ 0 <= m_d - c <= 1` on a first-order condition parses to
    a chain, whose source prints as the file writes it and whose formatted
    expression is `0 ≤ m_d − c ≤ 1`."""
    core = dict(item_addresses(parse_with_spans(two_bound_clause_text, "t.bl").term))[
        "policy.euler"
    ].core
    assert isinstance(core.bound, terms.Between)
    assert to_source(core) == "𝑑𝑢(c) = D_{a}V[>] ⟂ 0 <= m_d - c <= 1"
    assert typed_expressions.format_expression(core.bound) == "0 ≤ m_d − c ≤ 1"


@pytest.mark.parametrize(
    "name",
    ["declared-multiplier", "two-bound-clause", "annotated-product", "annotated-comprehension"],
)
def test_a_constraint_round_trips_through_the_json_encoding_of_its_syntax(constraint_texts, name):
    """The parsed term of a stage text with a declared multiplier, a clause
    of two bounds or an annotated feasible set, written to JSON text and read
    back, is the term that was written."""
    parsed = parse_with_spans(constraint_texts[name], "t.bl").term
    assert from_json(json.loads(json.dumps(to_json(parsed)))) == parsed


@pytest.mark.parametrize(
    "bound, expected",
    [
        pytest.param(terms.Rel(X, terms.Ge(), ZERO), X, id="lower-bound-zero"),
        pytest.param(terms.Rel(X, terms.Le(), BOUND), terms.Sub(BOUND, X), id="upper-bound"),
        pytest.param(
            terms.Between(ZERO, terms.Le(), X, terms.Le(), BOUND),
            (X, terms.Sub(BOUND, X)),
            id="two-bounds",
        ),
    ],
)
def test_slack_gives_the_distance_of_the_bounded_quantity_from_each_bound(bound, expected):
    """The slack of a lower bound `x ≥ 0` is `x`, of an upper bound `x ≤ b`
    is `b − x`, and of a chain `0 ≤ x ≤ b` is the pair of the two."""
    assert slack(bound) == expected


@pytest.mark.parametrize(
    "core, bound, system",
    [
        pytest.param(
            terms.Equation(LEFT, RIGHT),
            terms.Rel(X, terms.Ge(), ZERO),
            "l − r ≥ 0 ∧ x ≥ 0 ∧ (l − r) · x = 0",
            id="equation-lower-bound",
        ),
        pytest.param(
            terms.Equation(LEFT, RIGHT),
            terms.Rel(X, terms.Le(), BOUND),
            "l − r ≤ 0 ∧ b − x ≥ 0 ∧ (l − r) · (b − x) = 0",
            id="equation-upper-bound",
        ),
        pytest.param(
            terms.Equation(LEFT, RIGHT),
            terms.Between(ZERO, terms.Le(), X, terms.Le(), BOUND),
            "x ≥ 0 ∧ b − x ≥ 0 ∧ (l − r) · x ≤ 0 ∧ (l − r) · (b − x) ≥ 0",
            id="equation-two-bounds",
        ),
        pytest.param(
            terms.Inequality(LEFT, terms.Le(), RIGHT),
            terms.Rel(X, terms.Ge(), ZERO),
            "l − r ≤ 0 ∧ x ≥ 0 ∧ (l − r) · x = 0",
            id="inequality-lower-bound",
        ),
    ],
)
def test_kuhn_tucker_pairs_the_residual_with_the_slack_of_each_kind_of_bound(core, bound, system):
    """The Kuhn–Tucker system of a line `l = r` or `l ≤ r` and its bound
    signs the residual `l − r` by the kind of the bound and sets its product
    with the slack to zero, or, for a chain, signs the product with the slack
    of each bound."""
    assert typed_expressions.format_expression(kuhn_tucker(core, bound), width=None) == system


@pytest.mark.parametrize("text, written, malformed, rule", MALFORMED_CLAUSES)
def test_a_malformed_multiplier_declaration_or_clause_is_refused_under_its_rule(
    request, text, written, malformed, rule
):
    """A declaration of a multiplier or a clause that breaks a rule of the
    clause is refused under that rule."""
    stage_text = request.getfixturevalue(text)
    assert stage_text.count(written) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(stage_text.replace(written, malformed), "malformed.bl")
    assert refused.value.rule == rule


@pytest.mark.parametrize("name, direction", WHERE_CARDS)
def test_on_a_card_with_a_where_section_only_a_pullback_writes_the_law_of_motion(
    request, name, direction
):
    """On each card of the builders of one direction of a stage that has a
    Where section, no operation other than a Pullback writes the law of
    motion `𝑔≻(…)`."""
    cards = cards_with_a_where_section(request.getfixturevalue(name), direction)
    # the direction has what the claim is about, a card with a Where section
    assert cards
    written = []
    for builder, card in cards:
        # the kind of each entry, read from the builder and not from the
        # printed key
        kinds = {
            str(key): kind_of(builder.primitives[str(key)].box)
            for key in builder.primitives.list()
        }
        for entry in operations_entries(card_section_lines(card, "Operations")[1:]):
            if kinds.get(entry["key"]) != "Pullback" and "𝑔≻(" in "\n".join(entry["lines"]):
                written.append((card.splitlines()[0], entry["key"]))
    assert written == []


def test_the_pension_worker_card_writes_the_law_once_under_where(worker_saving_with_its_methods):
    """The card of the pension worker's policy builder states the outputs of
    the law of motion once, under Where, read at the policy, whose controls
    print bare at the point of several coordinates."""
    where = "\n".join(
        card_section_lines(str(worker_saving_with_its_methods.builder.policy), "Where")
    )
    assert flat(where) == flat("Where (y_f, y_p) = 𝑔≻(m_f, m_p, w_d, 𝑐, 𝑐_p)")


def test_the_first_clause_of_the_pension_worker_reads_the_controls_with_no_projection(
    worker_saving_with_its_methods,
):
    """The first clause on the card of the pension worker's policy builder
    bounds `m_f − 𝑐 − 𝑐_p`, written in the decision state and the controls,
    and the card writes no coordinate of the law's outputs by a projection
    `[1]`."""
    card = str(worker_saving_with_its_methods.builder.policy)
    assert flat("⟂ m_f − 𝑐 − 𝑐_p ≥ 0") in flat(operations_of(card)) and "[1]" not in card


def test_the_two_conditions_of_the_pension_worker_form_one_aggregation(
    worker_saving_with_its_methods,
):
    """The two first-order conditions of the pension worker's methods file
    form one Aggregation, `euler_financial:Aggregation`, and no operation of
    the kind Inversion or Solution."""
    policy = worker_saving_with_its_methods.builder.policy
    keys = [str(key) for key in policy.primitives.list()]
    assert [key for key in keys if key.startswith("euler")] == ["euler_financial:Aggregation"]
    assert not any(key.endswith(("Inversion", "Solution")) for key in keys)


def test_the_pension_worker_card_prints_each_clause_once_in_one_conjunction(
    worker_saving_with_its_methods,
):
    """The operations of the pension worker's policy builder print each of
    the two clauses once, within one conjunction `∧` of the two
    conditions."""
    operations = operations_of(str(worker_saving_with_its_methods.builder.policy))
    assert operations.count("⟂") == 2 and "∧" in operations


def test_the_two_bound_clause_of_the_pension_worker_reads_the_controls_bare_at_the_point(
    worker_saving_with_its_methods,
):
    """The two-bound clause on the pension deposit prints the controls bare,
    `⟂ 0 ≤ 𝑐_p ≤ w_d`, at the point of several coordinates that the region
    note names, `on (m_f, m_p, w_d) ∈ ℝ₊₊ × Xp × ℝ₊₊`."""
    operations = operations_of(str(worker_saving_with_its_methods.builder.policy))
    assert flat("⟂ 0 ≤ 𝑐_p ≤ w_d") in flat(operations)
    assert flat("on (m_f, m_p, w_d) ∈ ℝ₊₊ × Xp × ℝ₊₊") in flat(operations)


def test_the_durables_card_names_the_law_outputs_once_and_its_residuals_read_them(
    adjuster_cons_with_clause_on_candidate_line,
):
    """The card of the policy builder of the durables adjuster with the
    clause names the outputs of the law of motion once, under Where, and its
    operations read the membership of the first residual and the housing
    derivative through those names."""
    card = str(adjuster_cons_with_clause_on_candidate_line.builder.policy)
    assert flat("\n".join(card_section_lines(card, "Where"))) == flat(
        "Where (a_nxt_adj, h_nxt_adj, z_nxt_adj) = 𝑔≻(m, z_d, c, h_choice)"
    )
    operations = flat(operations_of(card))
    assert flat("c ∈ 𝑐≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)") in operations
    assert flat("D_{h_nxt_adj}𝑉≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)") in operations


@pytest.mark.parametrize(
    "name, inputs",
    [
        pytest.param(
            "feasible_set_reads_the_field",
            "in   (𝑉≻, 𝐿≻) : Xa → ℝ × ℝ",
            id="feasible-set-reads-it",
        ),
        pytest.param(
            "value_block_also_writes_the_field",
            "in   (𝑉≻, 𝐿≻) : Xa → ℝ × ℝ",
            id="value-block-also-writes-it",
        ),
        pytest.param("no_line_reads_the_field", "in   𝑉≻ : Xa → ℝ", id="no-line-reads-it"),
    ],
)
def test_the_policy_signature_lists_a_header_field_only_where_the_feasible_set_reads_it(
    request, name, inputs
):
    """`signature()` of the policy builder lists the field `𝐿≻` of its
    header beside `𝑉≻` among its inputs where the feasible set reads it, and
    leaves it out where no line reads it."""
    stage = request.getfixturevalue(name)
    assert flat(str(stage.dcsn.builder.policy.signature())) == flat(
        inputs + "\nout  𝑐(m) : 𝒫({c ∈ (Xm → ℝ₊₊) | c(m) ∈ Γ_c(m)})"
    )


@pytest.mark.parametrize(
    "name, unread",
    [
        pytest.param("feasible_set_reads_the_field", [], id="feasible-set-reads-it"),
        pytest.param("value_block_also_writes_the_field", [], id="value-block-also-writes-it"),
        pytest.param(
            "no_line_reads_the_field",
            [("unread-input", "policy", ("buffer_stock:cntn:L",))],
            id="no-line-reads-it",
        ),
    ],
)
def test_a_header_field_is_an_unread_input_unless_the_feasible_set_reads_it(request, name, unread):
    """`diagnostics()` answers a diagnostic under `unread-input` at the
    policy block for the field `L[>]` of its header where no line reads it,
    and none where the feasible set reads it."""
    diagnostics = request.getfixturevalue(name).diagnostics()["unread_inputs"]
    assert [(item.rule, item.address, item.candidates) for item in diagnostics] == unread


def test_the_evaluation_holds_the_type_rules_and_definition_of_the_identification(
    cons_with_egm_lines,
):
    """The Evaluation of the policy builder of `cons.bl` holds the type and
    the definition of the identification, the Pullback whose output is the
    policy, and its rules before any rule of its own."""
    policy = cons_with_egm_lines.builder.policy
    identification = policy["cons_choice:Pullback"].denote().outputs[0]
    evaluation = policy["Evaluation"].denote().outputs[0]
    assert identification.mathematical_type == evaluation.mathematical_type
    assert evaluation.rules[: len(identification.rules)] == identification.rules
    assert identification.definition == evaluation.definition


@pytest.mark.parametrize(
    "name, policies",
    [
        pytest.param(
            "cons_with_egm_lines",
            "𝒫({c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)})",
            id="named-correspondence",
        ),
        pytest.param(
            "cons_without_the_maximization_statement",
            "𝒫({c ∈ (Xm → ℝ₊₊) | 𝑔(m_d, c(m_d)) ∈ Xa})",
            id="image-of-the-law",
        ),
    ],
)
def test_the_policy_is_feasible_by_the_named_correspondence_or_by_the_image_of_the_law(
    request, name, policies
):
    """The set of policies that the identification outputs bounds the policy
    by the correspondence that the maximization statement names, with the
    decision state free in the condition, or, where no statement names one,
    by the image of the law of motion."""
    identification = request.getfixturevalue(name).builder.policy["cons_choice:Pullback"]
    carrier = identification.denote().outputs[0].mathematical_type.carrier
    assert typed_expressions.format_expression(carrier, width=None) == policies


def test_a_feasible_set_whose_condition_reads_minus_infinity_bounds_the_policy(mckenzie):
    """The policy builder of the accumulation stage of `mckenzie-1976`
    bounds its policy by the feasible set `Γ(x : Xk) := {y : Xk | 𝑢(x, y) >
    -inf}`, typed `Xk ⇉ Xk`, whose condition its card reads against `−∞`."""
    signature = flat("\n".join(card_section_lines(str(mckenzie.builder.policy), "Signature")))
    assert flat("out 𝑦 : Xk → Xk, 𝑦(k_d) ∈ Γ(k_d)") in signature
    card = flat(str(mckenzie.definitions.denote("accumulation:correspondence:Γ")))
    assert flat("Γ : Xk ⇉ Xk") in card and flat("> −∞}") in card


def test_a_binder_with_its_own_letter_gives_the_feasibility_of_the_policy(bundles):
    """The output of the Evaluation of `bundles` is the result of the
    control `c`, the set of policies `c` with `c(k_d) ∈ Γ(k_d)`, although
    the binder `cp : Γ(k_d)` of the maximization statement names its own
    letter."""
    evaluation = bundles.builder.policy["Evaluation"].denote().outputs[0]
    assert str(evaluation.identity) == "policy:Evaluation:c:result"
    carrier = typed_expressions.format_expression(evaluation.mathematical_type.carrier, width=None)
    assert carrier == "𝒫({c ∈ (ℝ → ℝ₊₊) | c(k_d) ∈ Γ(k_d)})"


def test_a_correspondence_denotes_its_interval_at_each_argument(bundles):
    """The correspondence `Γ(k : ℝ) := (0,1]` of `bundles` is typed `ℝ ⇉
    ℝ₊₊` and denotes the map `k ↦ (0, 1]`."""
    [correspondence] = bundles.definitions.denote("bundles:correspondence:Γ").denoted
    assert str(correspondence.mathematical_type) == "ℝ ⇉ ℝ₊₊"
    assert str(correspondence.expression) == "k ↦ (0, 1]"


def test_the_maximization_statement_binds_its_own_letter_over_the_correspondence(bundles):
    """The maximization statement of `bundles` is an argmax with one
    subscript, which binds the letter `cp` over `Γ(k_d)`."""
    objective = bundles.definitions["policy.objective"].equations[0].rhs
    assert isinstance(objective, terms.Operator) and objective.head == "argmax"
    assert len(objective.subs) == 1 and isinstance(objective.subs[0], terms.In)
    binder = objective.subs[0]
    assert (binder.var, typed_expressions.format_expression(binder.set, width=None)) == (
        "cp",
        "Γ(k_d)",
    )


def test_the_pullback_at_the_policy_writes_the_law_out_and_no_where_section(bundles):
    """The pullback of the decision builder of `bundles` writes the law of
    motion at the policy out, `𝑉≻ ∘ 𝑔≻(·, 𝑐)`, with no `where` entry and no
    Where section, and its rule reads the policy at the decision state."""
    pullback = bundles.dcsn.builder.bwd["pullback"]
    assert pullback.denote().where == ()
    printed = str(pullback)
    assert "out  𝑉≻ ∘ 𝑔≻(·, 𝑐)" in printed and "Where" not in printed
    assert "(𝑉≻ ∘ 𝑔≻(·, 𝑐))(k_d) = 𝑉≻(𝑔≻(k_d, 𝑐(k_d)))" in printed


@pytest.mark.parametrize(
    "name, body, written, factors",
    [
        pytest.param("product", terms.Product, "[0, z] × ℝ₊", 2, id="product"),
        pytest.param(
            "comprehension",
            terms.Comprehension,
            "{q : ℝ₊ × ℝ₊ × ℝ₊ | q[1] + q[2] = z}",
            3,
            id="comprehension",
        ),
    ],
)
def test_a_feasible_set_written_as_a_product_or_a_comprehension_keeps_its_factors(
    feasible_set_stage, name, body, written, factors
):
    """The definition of a correspondence `Γ(z : ℝ₊)` written as a product
    or a comprehension holds a body of that kind, its argument `z`, its set
    as written and every factor of its domain."""
    core = feasible_set_stage(name).definitions["joint_choice:correspondence:Γ"].equations[0]
    assert isinstance(core, terms.CorrDef)
    assert isinstance(core.body, body)
    assert core.params[0].stem == "z"
    assert to_source(core.body) == written
    assert len(domain_of(core.body).factors) == factors


def test_a_comprehension_holds_its_budget_identity_as_an_equation(feasible_set_stage):
    """The condition `q[1] + q[2] = z` of the budget set is held as a
    relation of the kind `Eq`."""
    definition = feasible_set_stage("comprehension").definitions["joint_choice:correspondence:Γ"]
    assert isinstance(definition.equations[0].body.conds[0].op, terms.Eq)


@pytest.mark.parametrize(
    "name, binder",
    [
        pytest.param("product", "Γ(x_d)", id="product"),
        pytest.param("comprehension", "Γ(x_d)", id="comprehension"),
        pytest.param("comprehension-with-an-inequality", "Γ(x_d)", id="with-an-inequality"),
        pytest.param("comprehension-at-a-state-named-q", "Γ(q)", id="at-a-state-named-q"),
    ],
)
def test_the_maximization_of_a_joint_choice_binds_the_correspondence_at_its_state(
    feasible_set_stage, name, binder
):
    """The binder of the maximization statement of a joint choice ranges
    over the correspondence applied to the decision state, by the name that
    the file gives that state."""
    choice = feasible_set_stage(name).definitions["policy.choice"].equations[0].rhs
    assert isinstance(choice.subs[0], terms.In)
    assert to_source(choice.subs[0].set) == binder


@pytest.mark.parametrize("name", NAMED_FEASIBLE_SETS)
def test_the_policy_builder_of_a_joint_choice_has_one_output(feasible_set_stage, name):
    """The policy builder of a joint choice of the coordinates of `u` has
    one output, the policy of `u`."""
    assert len(feasible_set_stage(name).builder.policy.signature().outputs) == 1


@pytest.mark.parametrize("name", list(FEASIBLE_SETS))
def test_every_answer_of_a_stage_with_a_feasible_set_is_resolved(feasible_set_stage, name):
    """No answer of a stage with a feasible set, the stage, its policy
    builder, the card of its correspondence or the correspondence's record,
    holds a reference that is not resolved."""
    stage = feasible_set_stage(name)
    card = stage.definitions.denote("joint_choice:correspondence:Γ")
    answers = {
        "stage": stage.denote(),
        "policy builder": stage.builder.policy.denote(),
        "card": card,
        "record": card.denoted[0],
    }
    assert [answer for answer, held in answers.items() if "UNRESOLVED" in str(held)] == []


@pytest.mark.parametrize(
    "name, phrases",
    [
        pytest.param("comprehension", ["q[1] + q[2] = z", "ℝ₊ × ℝ₊ × ℝ₊"], id="comprehension"),
        pytest.param(
            "comprehension-with-an-inequality",
            ["q[1] + q[2] = z", "ℝ₊ × ℝ₊ × ℝ₊", "q[3] ≤ z"],
            id="with-an-inequality",
        ),
        pytest.param(
            "comprehension-at-a-state-named-q",
            ["q[1] + q[2] = z", "ℝ₊ × ℝ₊ × ℝ₊"],
            id="at-a-state-named-q",
        ),
    ],
)
def test_the_card_of_a_feasible_set_prints_its_domain_and_every_condition(
    feasible_set_stage, name, phrases
):
    """The card of a comprehension prints its domain and each of its
    conditions."""
    printed = str(feasible_set_stage(name).definitions.denote("joint_choice:correspondence:Γ"))
    assert [phrase for phrase in phrases if phrase not in printed] == []


@pytest.mark.parametrize("name", ["annotated-product", "annotated-comprehension"])
def test_the_encoding_of_a_stage_with_a_feasible_set_validates_against_its_schema(
    feasible_set_encoding, encoding_validator, name
):
    """The encoding of a stage with an annotated feasible set, written to
    JSON text and read back, passes the JSON schema of the stage encoding;
    the test fails where `validate` raises."""
    encoding_validator.validate(json.loads(json.dumps(feasible_set_encoding(name))))


@pytest.mark.parametrize("name", ["annotated-product", "annotated-comprehension"])
def test_the_encoding_holds_a_feasible_set_as_the_json_term_of_its_syntax(
    feasible_set_encoding, name
):
    """The record of the correspondence in the encoding of a stage holds the
    JSON encoding of the term that the line of the feasible set parses to."""
    core = first_statement(FEASIBLE_SETS[name])
    encoded = next(
        record
        for record in feasible_set_encoding(name)["definitions"]
        if record["kind"] == "correspondence"
    )
    assert encoded["equations"][0]["term"] == to_json(core)


@pytest.mark.parametrize(
    "name, letter",
    [
        pytest.param("integer-range", "J", id="integer-range"),
        pytest.param("list-of-integers", "κ", id="list-of-integers"),
    ],
)
def test_a_factor_over_the_integers_is_held_as_the_first_factor_of_the_product(
    feasible_set_stage, name, letter
):
    """An integer range `{0, …, J}` or a list of integers `{0, κ} ⊂ ℤ`
    written as a factor is held as the first factor of the product, typed
    over ℤ, with no argument in the type."""
    answer = feasible_set_stage(name).definitions.denote("joint_choice:correspondence:Γ")
    record = answer.denoted[0]
    assert "z" not in str(record.mathematical_type)
    assert "ℤ × ℝ₊" in str(record.mathematical_type)
    factors = record.expression.body.factors
    assert len(factors) == 2 and factors[1] == terms.Named("ℝ₊")
    assert isinstance(factors[0], (terms.IntegerRange, terms.Points))
    assert letter in str(factors[0])


@pytest.mark.parametrize(
    "name, expression",
    [
        pytest.param("unused-product", "[0, z] × ℝ₊", id="product"),
        pytest.param(
            "comprehension-on-a-bounded-base", "[0, z] × ℝ₊ × ℝ₊", id="comprehension-base"
        ),
    ],
)
def test_a_bound_that_reads_the_argument_stands_in_the_expression_and_not_the_type(
    feasible_set_stage, name, expression
):
    """A bound of a feasible set that reads the argument `z`, in a product
    or in the base of a comprehension, stands in the correspondence's
    expression and not in its type, where no line names the feasible set."""
    record = (
        feasible_set_stage(name).definitions.denote("joint_choice:correspondence:Γ").denoted[0]
    )
    assert "z" not in str(record.mathematical_type)
    assert expression in str(record.expression)


@pytest.mark.parametrize("declaration, kind", DECLARATIONS)
def test_a_declaration_is_read_as_a_function_or_a_correspondence_by_its_body(declaration, kind):
    """A declaration `f(z : ℝ) := body` is a function where its body is a
    tuple or a formula, and a correspondence where it is an interval or a
    comprehension."""
    core = first_statement("@stage: declarations\n" + declaration + "\n")
    assert isinstance(core, kind)


@pytest.mark.parametrize(
    "declaration",
    [
        *(row.values[0] for row in DECLARATIONS),
        PRODUCT_LINE + ANNOTATION,
        BUDGET_SET_LINE + ANNOTATION,
    ],
    ids=[*(row.id for row in DECLARATIONS), "annotated-product", "annotated-comprehension"],
)
def test_a_declaration_prints_back_to_the_same_term(declaration):
    """The source that the term of a declaration prints parses back to the
    same term."""
    core = first_statement("@stage: declarations\n" + declaration + "\n")
    assert (
        parse_with_spans("@stage: declarations\n" + to_source(core) + "\n").term.items[1].core
        == core
    )


# the line and the column of each refusal: the line of the feasible set or of
# the declaration, at its first column, and for the comma, at its own column
@pytest.mark.parametrize(
    "text, rule, position",
    [
        pytest.param(
            ON_A_BUDGET_SET.replace("q[2] = z", "q[4] = z"),
            "family-selection",
            (2, 1),
            id="selection-beyond-the-coordinates",
        ),
        pytest.param(
            ON_A_BUDGET_SET.replace("q[2] = z", "q[2] = missing"),
            "name-in-scope",
            (2, 1),
            id="undeclared-name",
        ),
        pytest.param(
            ON_A_BUDGET_SET.replace("q[1] + q[2]", "q[0] + q[2]"),
            "family-selection",
            (2, 1),
            id="selection-before-the-first-coordinate",
        ),
        pytest.param(
            ON_A_PRODUCT.replace("@stage: joint_choice", "@stage: joint_choice\nθ : ℝ, = 1"),
            "syntax",
            (2, 6),
            id="comma-after-a-type",
        ),
    ],
)
def test_a_malformed_feasible_set_or_declaration_is_refused_under_its_rule_at_its_position(
    text, rule, position
):
    """A feasible set with a selection outside its coordinates or a name not
    in scope, or a declaration with a comma after its type, is refused under
    its rule, at the line and the column of the file that the refusal
    names."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, "invalid_set.bl")
    error = refused.value
    assert error.rule == rule
    assert error.file == "invalid_set.bl" and (error.line, error.column) == position
