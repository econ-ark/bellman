"""The grammar of a stage file: what the parser reads, what the lowering makes
of it, and where each refusal of the two is placed."""

import functools
import importlib.util
import json
import re

import pytest
from lark.exceptions import LexError, UnexpectedInput
from stage_builders import stage_from_text
from stage_texts import INPUT_SIDE_WITH_THE_CONTROL, corpus_text

from bellman.refusals import ConstructionError
from bellman.stage import to_source
from bellman.syntax import terms
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.syntax.parse import build_parser
from bellman.syntax.walk import nodes

# a stage whose policy maximizes over a feasible set with a complementarity
# clause; `{rp}` is the set of the argument of Γ, and `{sep}` the sign
# between the control and its feasible set in the binder of the maximization
MAXIMIZATION_STAGE = """@stage: t

b : ℝ₊
Γ(x : {rp}) := (0, x]

[id=pol, (b) -> (c : ℝ₊₊)] {{
    c = argmax_{{cp {sep} Γ(b)}}(u(cp)) ⟂ b >= 0    :: [id=optimality, !doc]
}}

[id=g, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {{
    V[<] = V
}}
"""


INEQUALITY_STAGE = """@stage: t

b : ℝ₊

[id=pol, (V[>] : ℝ @ !vlu, b) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] <= duinv(D_{b}V[>]) ⟂ b >= 0 :: [id=InvEuler]
    c    = c[>]                       :: [id=cons_choice]
}
"""


UNMARKED_STAGE = """@stage: t

c : ℝ₊₊
V : ℝ

[id=policy, (V[>] : ℝ @ !vlu, a) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])  :: [id=InvEuler]
    c    = c[>]                :: [id=cons_choice]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


# UNMARKED_STAGE with each field at the decision perch written with the
# decision perch mark `[~]`
MARKED_STAGE = """@stage: t

c[~] : ℝ₊₊
V : ℝ

[id=policy, (V[>] : ℝ @ !vlu, a) : !cntn -> (c[~] : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])  :: [id=InvEuler]
    c[~] = c[>]                :: [id=cons_choice]
}
[id=dcsn_to_arvl, (V[~]) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V[~]
}
"""


UNMARKED_DISTRIBUTIONS = "@stage: t\n\ny : ℝ\ny ~ N(0, 1)\n(y, z) ~ N(0, 1)\n"


# UNMARKED_DISTRIBUTIONS with the subject `y` written with the decision
# perch mark
MARKED_DISTRIBUTIONS = "@stage: t\n\ny[~] : ℝ\ny[~] ~ N(0, 1)\n(y[~], z) ~ N(0, 1)\n"


# a stage with one line in its block `b`, written with `{selected}` on the
# right of its equation
SELECTION_STAGE = "@stage: t\n\n[id=b, (v) : !cntn -> (w) : !dcsn] {{\n    w = {selected}\n}}\n"


EXTENDED_REAL_STAGE = """@stage: t

V : {ty} @ !vlu
q : ℝ₊

[id=b, (v : {ty} @ !vlu, c) : !cntn -> (w : ℝ₊) : !dcsn] {{
    w = v + c
}}
"""


# an interval `{shape}` written in a declaration, on the input side of a
# block and in the binder of a function
INTERVAL_IN_A_DECLARATION = """@stage: t

p : {shape}
q : ℝ₊
"""


INTERVAL_ON_A_SIDE = """@stage: t

[id=b, (v : {shape} @ !vlu, c) : !cntn -> (w : ℝ₊) : !dcsn] {{
    w = v + c
    c = w - v
}}
"""


INTERVAL_IN_A_BINDER = """@stage: t

k : ℝ₊

[id=b, (v : ℝ₊, c) -> (w : ℝ₊)] {{
    𝑓(x : {shape}) := x + k
    w = 𝑓(v)
}}
"""


# the feasible set of the smooth-ambiguity stage, the consumptions below the
# resources, written by comprehension
COMPREHENSION = "Γ(x : ℝ₊₊) := {c : ℝ₊₊ | c < x}"


# the retiree stage whose state set is defined once by name with the
# parameter ā as its upper endpoint; `{definition}` is the body after `:=`
NAMED_SET = """@stage: retiree

β : (0,1)
r : ℝ
ā : ℝ₊₊
Xa := {definition}

𝑢(c : ℝ₊₊) := log(c)
Γ(x : Xa) := (0, (1+r)*x]

[id=arvl_to_dcsn, (a_r : Xa) : !arvl -> (a_d : Xa) : !dcsn] {{
    a_d = a_r                                                  :: [id=assets]
}}

[id=dcsn_to_cntn, (a_d, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a_rr : Xa) : !cntn] {{
    a_rr = (1+r)*a_d - c                                       :: [id=savings]
}}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {{
    V = 𝑢(c) + β*V[>]                                          :: [id=value]
}}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {{
    V[<] = V                                                   :: [id=value]
}}

[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {{
    c = argmax_{{c : Γ(a_d)}}(𝑢(c) + β*V[>])                     :: [id=choice]
}}
"""


# the identities of the three fields of NAMED_SET that a block header types
# by the set Xa
FIELDS_TYPED_BY_XA = ("retiree:arvl:a_r", "retiree:dcsn:a_d", "retiree:cntn:a_rr")


def interval_up_to_a_bar(left, right):
    """The interval from 0 to the parameter ā with the ends `left` and
    `right`, as the lowering writes it."""
    return terms.Interval(
        terms.Range(
            left=left, lower=terms.Number(0), upper=terms.Sym(terms.Constant("ā")), right=right
        )
    )


CLOSED_INTERVAL = interval_up_to_a_bar(terms.Closed(), terms.Closed())


# the node by which the encoding names the set Xa
NAMED_XA = {"__class__": "Named", "name": "Xa"}


# the three intervals that NAMED_SET defines Xa as: the text after `:=` and
# the interval it lowers to
NAMED_SET_FORMS = [
    pytest.param("[0, ā]", CLOSED_INTERVAL, id="closed"),
    pytest.param(
        "(0, ā]", interval_up_to_a_bar(terms.Open(), terms.Closed()), id="open on the left"
    ),
    pytest.param(
        "[0, ā)", interval_up_to_a_bar(terms.Closed(), terms.Open()), id="open on the right"
    ),
]


def inline_form(definition):
    """The stage of `NAMED_SET` with the interval written at each use of `Xa`
    and a comment in place of the definition line, so that every line number
    agrees with the named form."""
    return (
        NAMED_SET.format(definition=definition)
        .replace(f"Xa := {definition}", "# the interval is written at each use")
        .replace(": Xa", f": {definition}")
    )


def assignment_statement(line):
    """The `Statement` item the lowering makes of one definition line written
    after a declaration of ā."""
    return parse_with_spans(f"@stage: t\n\nā : ℝ₊₊\n{line}\n").term.items[2]


def first_item_core(line):
    """The core of the item the lowering makes of one line written after the
    metadata line of a stage file."""
    return parse_with_spans(f"@stage: t\n\n{line}\n").term.items[1].core


def encoding_document(stage):
    """The stage encoding as the JSON document it is written as."""
    return json.loads(json.dumps(stage.encoding(), default=str))


def with_name_read_as(document, name_node, term):
    """The encoding with every occurrence of the node `name_node` replaced by
    the term it is defined as."""
    if isinstance(document, dict):
        if document == name_node:
            return json.loads(json.dumps(term))
        return {key: with_name_read_as(value, name_node, term) for key, value in document.items()}
    if isinstance(document, list):
        return [with_name_read_as(value, name_node, term) for value in document]
    return document


def decision_perch_indices(term):
    """Each `At` node of a term that names the decision perch, in the order
    of the term."""
    return [
        node
        for node in nodes(term)
        if isinstance(node, terms.At) and isinstance(node.side, terms.Decision)
    ]


@pytest.fixture(scope="module")
def named_set_stage():
    """`named_set_stage(definition)`: the stage of `NAMED_SET` that defines
    Xa as `definition`, elaborated once for each definition."""
    return functools.cache(
        lambda definition: stage_from_text(NAMED_SET.format(definition=definition))
    )


@pytest.fixture(scope="module")
def inline_set_stage():
    """`inline_set_stage(definition)`: the stage of `inline_form(definition)`,
    elaborated once for each definition."""
    return functools.cache(lambda definition: stage_from_text(inline_form(definition)))


# the names that would collide with the spelling of an identity, each as the
# stage text that writes it, the address the refusal names and a phrase of
# its message
COLLIDING_NAMES = {
    "a field named result": (
        "@stage: t\n[id=b, (x : ℝ) : !dcsn -> (result : ℝ) : !dcsn] {\n    result = x\n}\n",
        "b",
        "the field 'result'",
    ),
    "a block named merged": (
        "@stage: t\n[id=merged, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        "merged",
        "the block id 'merged'",
    ),
    "a field named declared": (
        "@stage: t\n[id=b, (x : ℝ) : !dcsn -> (declared : ℝ) : !dcsn] {\n    declared = x\n}\n",
        "b",
        "the field 'declared'",
    ),
    "a statement named merged": (
        "@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x :: [id=merged]\n}\n",
        "b.merged",
        "the statement id 'merged'",
    ),
    "a stage name with a colon": (
        "@stage: t:u\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        "1",
        "the stage name 't:u'",
    ),
}


# a stage with the shock `z_1`, whose name holds the underscore that joins
# the subjects of a distribution in the spelling of an identity
SHOCK_WITH_AN_UNDERSCORE = (
    "@stage: t\nz_1 : ℝ\nz_1 ~ N(0,1)\n"
    "[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (k_d : ℝ) : !dcsn] {\n    k_d = k\n}\n"
    "[id=dcsn_to_cntn, (k_d, z_1) : !dcsn -> (a : ℝ) : !cntn] {\n    a = k_d + z_1\n}\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = E_{z_1}(V[>])\n}\n"
    "[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n"
)


# a stage with two distribution declarations, of `a_b` and of `(a, b)`, whose
# subjects joined by `_` spell one identity; the constructor of identities
# sees one declaration at a time, and the check of the declarations sees both
DECLARATIONS_JOINING_ALIKE = (
    "@stage: t\na_b : ℝ\na : ℝ\nb : ℝ\na_b ~ N(0,1)\n(a, b) ~ N((0,0), ((1,0),(0,1)))\n"
    "[id=blk, (k : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = k\n}\n"
)


@pytest.mark.parametrize(
    "rp",
    [
        pytest.param("ℝ₊", id="the nonnegative reals written ℝ₊"),
        pytest.param("R_{+}", id="the nonnegative reals written R_{+}"),
        pytest.param("R+", id="the nonnegative reals written R+"),
    ],
)
def test_a_maximization_over_a_feasible_set_with_a_complementarity_clause_encodes_each_construct(
    rp,
):
    """The encoding of the parsed term of a stage that defines a feasible set,
    maximizes over it and adds a complementarity clause holds the classes
    `CorrDef`, `In` and `Slack`."""
    term, _ = parse_with_spans(MAXIMIZATION_STAGE.format(rp=rp, sep=":"))
    classes = set(
        re.findall(r'"__class__": "(\w+)"', json.dumps(to_json(term), ensure_ascii=False))
    )
    assert [name for name in ("CorrDef", "In", "Slack") if name not in classes] == []


def test_a_complementarity_sign_in_place_of_the_colon_of_a_binder_is_refused_by_the_parser():
    """The parser refuses `⟂` between the control and its feasible set in the
    binder of a maximization, since membership there is written with a
    colon and `⟂` writes a complementarity clause alone."""
    with pytest.raises(UnexpectedInput):
        parse_with_spans(MAXIMIZATION_STAGE.format(rp="ℝ₊", sep="⟂"))


def test_an_inequality_line_with_a_complementarity_clause_lowers_to_an_inequality_in_the_clause():
    """The line `c[>] <= ... ⟂ b >= 0` lowers to a complementarity clause
    around an inequality whose relation is `<=`."""
    term, _ = parse_with_spans(INEQUALITY_STAGE)
    block = [item for item in term.items if isinstance(item, terms.Block)][0]
    core = block.body[0].core
    assert isinstance(core, terms.Slack) and isinstance(core.core, terms.Inequality)
    assert isinstance(core.core.op, terms.Le)


def test_an_inequality_line_with_a_complementarity_clause_prints_back_as_it_is_written():
    """The printer writes the term of the line `c[>] <= ... ⟂ b >= 0` back as
    the line is written."""
    term, _ = parse_with_spans(INEQUALITY_STAGE)
    block = [item for item in term.items if isinstance(item, terms.Block)][0]
    assert to_source(block.body[0].core) == "c[>] <= duinv(D_{b}V[>]) ⟂ b >= 0"


def test_fields_written_with_the_decision_perch_mark_lower_to_the_term_of_the_unmarked_fields():
    """A stage that writes each field at the decision perch with `[~]` lowers
    to the term of the same stage written without the mark."""
    assert parse_with_spans(MARKED_STAGE).term == parse_with_spans(UNMARKED_STAGE).term


def test_distribution_subjects_written_with_the_decision_perch_mark_lower_to_the_unmarked_term():
    """Distribution declarations whose subject is written with `[~]` lower to
    the term of the same declarations written without the mark."""
    assert (
        parse_with_spans(MARKED_DISTRIBUTIONS).term
        == parse_with_spans(UNMARKED_DISTRIBUTIONS).term
    )


def test_a_name_written_with_the_decision_perch_mark_in_a_line_lowers_to_the_bare_name():
    """The name `w[~]` on the left of a line of a block lowers to the
    constant `w`, which carries no perch."""
    term, _ = parse_with_spans(
        "@stage: t\n\n[id=b, (v) : !cntn -> (w) : !dcsn] {\n    w[~] = v\n}\n"
    )
    block = [item for item in term.items if isinstance(item, terms.Block)][0]
    lhs = block.body[0].core.lhs
    assert lhs == terms.Sym(terms.Constant("w"))
    assert not isinstance(lhs.symbol, terms.Variable)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(MARKED_STAGE, id="fields of the headers and the lines of blocks"),
        pytest.param(MARKED_DISTRIBUTIONS, id="subjects of distribution declarations"),
    ],
)
def test_a_text_written_with_the_decision_perch_mark_lowers_to_no_index_of_the_decision_perch(
    text,
):
    """No node of the term of a text that writes names with `[~]` names the
    decision perch as an index: a name is at the arrival or the continuation
    perch, or it is the bare name of the decision perch."""
    assert decision_perch_indices(parse_with_spans(text).term) == []


@pytest.mark.parametrize(
    ("block", "line", "side", "symbol"),
    [
        # block and line count from 0; a Variable is written with its name,
        # its perch and its shift in time, 0
        # the line `V[<] = V[~]` of the block `dcsn_to_arvl`
        pytest.param(
            1,
            0,
            "lhs",
            terms.Variable("V", terms.At(terms.Arrival()), 0),
            id="the arrival mark",
        ),
        # the line `c[~] = c[>]` of the block `policy`
        pytest.param(
            0,
            1,
            "rhs",
            terms.Variable("c", terms.At(terms.Continuation()), 0),
            id="the continuation mark",
        ),
    ],
)
def test_a_name_written_with_the_arrival_or_the_continuation_mark_lowers_to_the_name_at_that_perch(
    block, line, side, symbol
):
    """A name written with `[<]` or `[>]` in a stage that also writes the
    decision perch mark lowers to the variable at the arrival or the
    continuation perch."""
    term, _ = parse_with_spans(MARKED_STAGE)
    core = [item for item in term.items if isinstance(item, terms.Block)][block].body[line].core
    assert getattr(core, side) == terms.Sym(symbol)


def test_a_decision_perch_mark_before_a_selector_of_a_key_lowers_to_the_unmarked_selection():
    """`v[~][keep]` lowers to the term of `v[keep]`."""
    marked, _ = parse_with_spans(SELECTION_STAGE.format(selected="v[~][keep]"))
    bare, _ = parse_with_spans(SELECTION_STAGE.format(selected="v[keep]"))
    assert marked == bare


@pytest.mark.parametrize(
    "mark",
    [
        pytest.param("~", id="the decision perch mark"),
        pytest.param(">", id="the continuation mark"),
    ],
)
def test_a_perch_mark_after_a_selector_of_a_key_is_refused_by_the_lowering_with_the_text_to_write(
    mark,
):
    """The lowering refuses `v[keep][~]` and `v[keep][>]` at the mark, says
    that the mark follows the first selector, and gives the text to write
    with the mark first, in its own words and not in those of the parser
    library."""
    with pytest.raises(ValueError) as caught:
        parse_with_spans(SELECTION_STAGE.format(selected=f"v[keep][{mark}]"))
    # line 4 of the stage text, the column of the mark after `w = v[keep][`
    assert (caught.value.line, caught.value.column) == (4, 17)
    assert f"perch mark `{mark}` follows the first selector" in str(caught.value)
    assert caught.value.write == f"write one perch mark first, as `v[{mark}][keep]`"
    assert "Error trying to process rule" not in str(caught.value)


def test_the_span_of_a_line_written_with_the_decision_perch_mark_starts_at_its_first_name():
    """The span of the line `c[~] = c[>]` of the policy block starts at the
    `c` of `c[~]`."""
    _, spans = parse_with_spans(MARKED_STAGE, "marked.bl")
    span = spans["policy.cons_choice"]
    assert (span.line, span.column) == (8, 5)
    assert MARKED_STAGE.splitlines()[span.line - 1][span.column - 1 :].startswith("c[~] = c[>]")


@pytest.mark.parametrize(
    "ty",
    [
        pytest.param("ℝ̄", id="the extended real line"),
        pytest.param("ℝ_{-∞}", id="the reals with minus infinity"),
        pytest.param("ℝ_{+∞}", id="the reals with plus infinity"),
        pytest.param("ℝ_{±∞}", id="the reals with both infinities"),
    ],
)
def test_each_spelling_of_the_reals_with_an_infinity_lowers_to_the_named_set_of_that_spelling(ty):
    """The set of each row, which types `V` in a declaration and `v` on the
    input side of a block, lowers in both places to the named set of its
    spelling."""
    term, _ = parse_with_spans(EXTENDED_REAL_STAGE.format(ty=ty))
    domains = [
        node
        for node in nodes(term)
        if isinstance(node, terms.Domain) and node.space != terms.Named("ℝ₊")
    ]
    assert domains == [terms.Domain(terms.Named(ty))] * 2


def test_the_infinity_glyph_and_the_word_inf_lower_to_one_term():
    """The set `[-∞, ∞)` lowers to the term of `[-inf, inf)`."""
    glyph, _ = parse_with_spans(EXTENDED_REAL_STAGE.format(ty="[-∞, ∞)"))
    word, _ = parse_with_spans(EXTENDED_REAL_STAGE.format(ty="[-inf, inf)"))
    assert to_json(glyph) == to_json(word)


@pytest.mark.parametrize(
    ("shape", "left", "right"),
    [
        pytest.param("(0, 1)", terms.Open(), terms.Open(), id="open"),
        pytest.param("(0, 1]", terms.Open(), terms.Closed(), id="open on the left"),
        pytest.param("[0, 1)", terms.Closed(), terms.Open(), id="open on the right"),
        pytest.param("[0, 1]", terms.Closed(), terms.Closed(), id="closed"),
    ],
)
@pytest.mark.parametrize(
    "template",
    [
        pytest.param(INTERVAL_IN_A_DECLARATION, id="in a declaration"),
        pytest.param(INTERVAL_ON_A_SIDE, id="on the side of a block"),
        pytest.param(INTERVAL_IN_A_BINDER, id="in the binder of a function"),
    ],
)
def test_each_shape_of_an_interval_lowers_to_the_range_of_its_ends_in_each_position(
    template, shape, left, right
):
    """An interval from 0 to 1 with each pair of open and closed ends lowers
    to the one range with those ends, in a declaration, on the side of a
    block and in the binder of a function."""
    term, _ = parse_with_spans(template.format(shape=shape))
    ranges = [node for node in nodes(term) if isinstance(node, terms.Range)]
    assert ranges == [terms.Range(left, terms.Number(0), terms.Number(1), right)]


def test_a_feasible_set_written_by_comprehension_lowers_to_a_correspondence_with_a_comprehension():
    """`Γ(x : ℝ₊₊) := {c : ℝ₊₊ | c < x}` lowers to the definition of the
    correspondence Γ whose body is the comprehension of the `c` in ℝ₊₊ with
    `c < x`."""
    assert first_item_core(COMPREHENSION) == terms.CorrDef(
        "Γ",
        (terms.Coordinate("x", None, (terms.Domain(terms.Named("ℝ₊₊")),)),),
        terms.Comprehension(
            terms.Subject((terms.Coordinate("c", None, ()),)),
            terms.Named("ℝ₊₊"),
            (
                terms.Rel(
                    terms.Sym(terms.Constant("c")), terms.Lt(), terms.Sym(terms.Constant("x"))
                ),
            ),
        ),
    )


def test_a_feasible_set_written_by_comprehension_prints_back_as_it_is_written():
    """The printer writes the term of `Γ(x : ℝ₊₊) := {c : ℝ₊₊ | c < x}` back as
    the line is written."""
    assert to_source(first_item_core(COMPREHENSION)) == "Γ(x : ℝ₊₊) := {c : ℝ₊₊ | c < x}"


def test_the_printed_feasible_set_written_by_comprehension_lowers_to_the_same_term():
    """The text that the printer writes of the term of a feasible set written
    by comprehension lowers to that term."""
    term = first_item_core(COMPREHENSION)
    assert first_item_core(to_source(term)) == term


def test_a_function_whose_body_is_a_pair_lowers_to_a_function_with_a_tuple_body():
    """`𝑓(x : ℝ₊₊) := (0, x)` lowers to the definition of a function whose
    body is a tuple, and not to a correspondence over an interval."""
    pair = first_item_core("𝑓(x : ℝ₊₊) := (0, x)")
    assert isinstance(pair, terms.FuncDef) and isinstance(pair.body, terms.Tuple)


@pytest.mark.parametrize(
    ("line", "interval", "annotation"),
    [
        pytest.param(
            'Xa := [0, ā] :: ["assets"]',
            CLOSED_INTERVAL,
            terms.Annotation((terms.Tag('"assets"'),)),
            id="closed, with an annotation",
        ),
        pytest.param(
            "Xa := (0, ā]",
            interval_up_to_a_bar(terms.Open(), terms.Closed()),
            None,
            id="open on the left",
        ),
        pytest.param(
            "Xa := [0, ā)",
            interval_up_to_a_bar(terms.Closed(), terms.Open()),
            None,
            id="open on the right",
        ),
    ],
)
def test_a_definition_line_of_an_interval_lowers_to_the_assignment_of_the_interval_to_its_name(
    line, interval, annotation
):
    """The line `Xa := ...` with an interval whose upper end is the parameter
    ā lowers to the assignment of that interval to the set Xa, with the
    annotation of the line."""
    statement = assignment_statement(line)
    assert statement.core == terms.Assignment(terms.Constant("Xa"), terms.Space(interval))
    assert statement.annot == annotation


@pytest.mark.parametrize(
    ("line", "printed"),
    [
        pytest.param(
            'Xa := [0, ā] :: ["assets"]', "Xa := [0, ā]", id="closed, with an annotation"
        ),
        pytest.param("Xa := (0, ā]", "Xa := (0, ā]", id="open on the left"),
        pytest.param("Xa := [0, ā)", "Xa := [0, ā)", id="open on the right"),
    ],
)
def test_a_definition_line_of_an_interval_prints_back_as_it_is_written(line, printed):
    """The printer writes the assignment that a line `Xa := ...` lowers to
    back as the line is written before its annotation."""
    assert to_source(assignment_statement(line).core) == printed


@pytest.mark.parametrize(
    "definition", [pytest.param(form.values[0], id=form.id) for form in NAMED_SET_FORMS]
)
def test_each_field_typed_by_a_named_interval_keeps_the_name_as_its_set(
    definition, named_set_stage
):
    """The record of each field that a header types by the set Xa, defined as
    an interval, holds the name Xa as its set."""
    fields = named_set_stage(definition).fields()
    assert {identity: fields[identity].domain for identity in FIELDS_TYPED_BY_XA} == {
        identity: terms.Named("Xa") for identity in FIELDS_TYPED_BY_XA
    }


@pytest.mark.parametrize(("definition", "interval"), NAMED_SET_FORMS)
def test_each_field_typed_by_an_interval_written_at_its_use_keeps_the_interval_as_its_set(
    definition, interval, inline_set_stage
):
    """The record of each field that a header types by an interval written in
    the header holds that interval as its set."""
    # the interval stands at the four uses of Xa: Γ and the three fields
    assert inline_form(definition).count(definition) == 4
    fields = inline_set_stage(definition).fields()
    assert {identity: fields[identity].domain for identity in FIELDS_TYPED_BY_XA} == {
        identity: interval for identity in FIELDS_TYPED_BY_XA
    }


@pytest.mark.parametrize(("definition", "interval"), NAMED_SET_FORMS)
def test_the_encoding_of_a_stage_defines_a_named_interval_as_a_set_whose_term_is_the_interval(
    definition, interval, named_set_stage
):
    """The encoding of a stage that defines Xa as an interval holds the
    definition `retiree:set:Xa` of the kind `set`, whose equation is the
    term of the interval."""
    definitions = {
        entry["identity"]: entry
        for entry in encoding_document(named_set_stage(definition))["definitions"]
    }
    assert definitions["retiree:set:Xa"]["kind"] == "set"
    assert definitions["retiree:set:Xa"]["equations"][0]["term"] == to_json(interval)


def test_only_the_stage_that_names_an_interval_holds_a_definition_of_the_set_in_its_encoding(
    named_set_stage, inline_set_stage
):
    """The encoding of the retiree stage that defines Xa as `[0, ā]` holds the
    definition of the set Xa, where the encoding of the stage that writes
    `[0, ā]` at each use, with no definition line, holds none."""
    named = encoding_document(named_set_stage("[0, ā]"))["definitions"]
    assert "retiree:set:Xa" in {entry["identity"] for entry in named}
    definitions = encoding_document(inline_set_stage("[0, ā]"))["definitions"]
    assert "retiree:set:Xa" not in {entry["identity"] for entry in definitions}


def test_a_named_interval_encodes_as_the_interval_written_at_each_use_once_the_name_is_read(
    named_set_stage, inline_set_stage
):
    """The sections of the encoding of the stage that defines Xa as `[0, ā]`
    equal those of the stage that writes `[0, ā]` at each use, once each
    occurrence of the name is read as the interval and the definition of Xa
    is left out."""
    named = encoding_document(named_set_stage("[0, ā]"))
    inline = encoding_document(inline_set_stage("[0, ā]"))
    definition = next(
        entry for entry in named["definitions"] if entry["identity"] == "retiree:set:Xa"
    )
    resolved = with_name_read_as(named, NAMED_XA, definition["equations"][0]["term"])
    resolved["definitions"] = [
        entry for entry in resolved["definitions"] if entry["identity"] != "retiree:set:Xa"
    ]
    # `derived` names the set by its identity and quotes the headers as
    # written, and `provenance` digests the text; every other section agrees
    sections = (
        "definitions",
        "initial_diagrams",
        "builders",
        "bindings",
        "obligations",
        "diagnostics",
    )
    assert {section: resolved[section] for section in sections} == {
        section: inline[section] for section in sections
    }


def test_an_interval_open_at_both_ends_after_the_assignment_sign_lowers_to_a_pair():
    """`Xa := (0, ā)` lowers to the assignment of the pair `(0, ā)` to Xa,
    since the grammar reads `(a, b)` after `:=` as a tuple, as it does in the
    body of a correspondence."""
    statement = assignment_statement("Xa := (0, ā)")
    assert statement.core == terms.Assignment(
        terms.Constant("Xa"), terms.Tuple((terms.Number(0), terms.Sym(terms.Constant("ā"))))
    )


def test_a_set_defined_by_a_pair_is_refused_at_its_definition_line():
    """The elaboration refuses the retiree stage that defines Xa as `(0, ā)`
    under `not-constructed` at the definition line, and its message names
    the definition and the pair."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(NAMED_SET.format(definition="(0, ā)"))
    error = refused.value
    # line 6 of NAMED_SET is the definition line `Xa := ...`
    assert (error.rule, error.line) == ("not-constructed", 6)
    assert "definition 'Xa'" in error.message and "(0, ā)" in error.message


def test_the_printer_refuses_a_named_set_whose_interval_is_open_at_both_ends():
    """The printer has no spelling for the assignment of an interval open at
    both ends to a name, which the grammar would read as a tuple."""
    open_open = terms.Interval(
        terms.Range(
            left=terms.Open(), lower=terms.Number(0), upper=terms.Number(1), right=terms.Open()
        )
    )
    with pytest.raises(NotImplementedError, match="tuple"):
        to_source(terms.Assignment(terms.Constant("Xa"), terms.Space(open_open)))


def test_a_control_listed_at_the_arrival_perch_on_the_continuation_side_is_refused():
    """The control `c` listed as `c : !arvl` on the input side of the block
    `cntn_to_dcsn` of cons.bl, which is marked `: !cntn`, is refused under
    `field-perch` at the block, with a message that says that a control is
    at the decision perch wherever it is listed."""
    text = corpus_text("cons")
    assert text.count(INPUT_SIDE_WITH_THE_CONTROL) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            text.replace(
                INPUT_SIDE_WITH_THE_CONTROL,
                INPUT_SIDE_WITH_THE_CONTROL.replace(", c)", ", c : !arvl)"),
            ),
            "cons.bl",
        )
    assert refused.value.rule == "field-perch"
    assert refused.value.address == "cntn_to_dcsn"
    phrases = (
        "c on the input side of block 'cntn_to_dcsn'",
        "a control placed at the arvl perch",
        "a control is at the decision perch wherever it is listed",
    )
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []


@pytest.mark.parametrize(
    ("marked", "perch"),
    [
        pytest.param("c[>]", "cntn", id="the continuation mark"),
        pytest.param("c[<]", "arvl", id="the arrival mark"),
    ],
)
def test_a_control_written_with_the_mark_of_a_perch_other_than_the_decision_perch_is_refused(
    marked, perch
):
    """The control `c` written `c[>]` or `c[<]` on the input side of the block
    `cntn_to_dcsn` of cons.bl is refused under `field-perch` at the block as
    a control placed at the perch of its mark, since a mark names the field
    at that perch, even where the mark names the perch of the side."""
    text = corpus_text("cons")
    assert text.count(INPUT_SIDE_WITH_THE_CONTROL) == 1
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            text.replace(
                INPUT_SIDE_WITH_THE_CONTROL,
                INPUT_SIDE_WITH_THE_CONTROL.replace(", c)", f", {marked})"),
            ),
            "cons.bl",
        )
    assert refused.value.rule == "field-perch"
    assert refused.value.address == "cntn_to_dcsn"
    phrases = (
        f"{marked} on the input side of block 'cntn_to_dcsn'",
        f"a control placed at the {perch} perch",
    )
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []


# the input side `INPUT_SIDE_WITH_THE_CONTROL` of the header of the decision
# builder of `cons.bl` with no perch written after its input tuple
HEADER_WITHOUT_PERCH = "(V[>] : [-inf, inf) @ !vlu, c) ->"


@pytest.mark.parametrize(
    "header",
    [
        pytest.param(
            INPUT_SIDE_WITH_THE_CONTROL.replace(", c)", ", c : !cntn)"),
            id="control-marked-at-the-continuation",
        ),
        pytest.param(
            INPUT_SIDE_WITH_THE_CONTROL.replace(", c)", ", c : !dcsn)"),
            id="control-marked-at-the-decision",
        ),
        pytest.param(HEADER_WITHOUT_PERCH, id="no-perch-written"),
        pytest.param(
            HEADER_WITHOUT_PERCH.replace(", c)", ", c : !cntn)"),
            id="no-perch-and-control-marked-at-the-continuation",
        ),
        pytest.param(
            HEADER_WITHOUT_PERCH.replace(", c)", ", c : !dcsn)"),
            id="no-perch-and-control-marked-at-the-decision",
        ),
    ],
)
def test_a_backward_header_gives_the_decision_builder_one_signature_however_it_writes_the_perches(
    header, cons
):
    """The decision builder of `cons.bl` has the same signature whether its
    header writes the perch of its input tuple and of its control or leaves
    either out."""
    source = corpus_text("cons")
    assert source.count(INPUT_SIDE_WITH_THE_CONTROL) == 1
    rewritten = stage_from_text(source.replace(INPUT_SIDE_WITH_THE_CONTROL, header), "cons.bl")
    assert rewritten.dcsn.builder.bwd.signature() == cons.dcsn.builder.bwd.signature()


@pytest.mark.parametrize("written", COLLIDING_NAMES)
def test_a_name_that_would_collide_with_the_spelling_of_an_identity_is_refused_where_it_is_written(
    written,
):
    """A name that holds the colon that separates the parts of an identity, or
    that is one of the words `result`, `declared` and `merged` that the last
    part of an identity reserves, is refused under `identity-collision` at
    its address."""
    source, address, named = COLLIDING_NAMES[written]
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(source)
    error = refused.value
    assert (error.rule, error.address) == ("identity-collision", address)
    assert named in error.message
    assert str(error).endswith(f"(address {address!r}; rule identity-collision)")


def test_a_shock_name_with_an_underscore_is_refused_only_where_two_declarations_join_alike():
    """The shock `z_1` is admitted with its identity, and two distribution
    declarations of `a_b` and of `(a, b)`, whose subjects joined by `_` spell
    one identity, are refused under `identity-collision` at the second."""
    stage = stage_from_text(SHOCK_WITH_AN_UNDERSCORE)
    assert "t:shck:z_1" in {str(identity) for identity in stage.fields()}
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(DECLARATIONS_JOINING_ALIKE)
    error = refused.value
    # the address "6" is the sixth item of the file, the declaration of (a, b)
    assert (error.rule, error.address) == ("identity-collision", "6")
    assert "spelled 'a_b' joined" in error.message
    assert str(error).endswith("(address '6'; rule identity-collision)")


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(
            "@stage: t\n[id=a.b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
            id="a dot in a block id",
        ),
        pytest.param(
            "@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y.z : ℝ) : !dcsn] {\n    y.z = x\n}\n",
            id="a dot in a field name",
        ),
    ],
)
def test_a_dot_in_a_block_id_or_a_field_name_is_refused_as_syntax_and_not_as_a_collision(text):
    """A block id or a field name that holds a dot is refused under `syntax`,
    since the grammar admits no dot there, and not under
    `identity-collision`."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text)
    assert refused.value.rule == "syntax"
    assert "identity-collision" not in str(refused.value)


@pytest.mark.parametrize(
    ("selected", "column", "remedy"),
    [
        # the column of the mark after `w = v[keep][`, and of the second mark
        # after `w = v[<][`
        pytest.param("v[keep][~]", 17, "v[~][keep]", id="the decision perch mark after a key"),
        pytest.param("v[<][>]", 14, "v[>]", id="a second perch mark"),
    ],
)
def test_a_perch_mark_after_a_selector_is_refused_as_syntax_at_its_column_with_the_text_to_write(
    selected, column, remedy
):
    """The elaboration refuses a perch mark written after a selector under
    `syntax` at the mark, with a caret under it and the text to write, in
    its own words and not in those of the parser library."""
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(SELECTION_STAGE.format(selected=selected), "selectors.bl")
    error = refused.value
    assert (
        error.rule,
        error.file,
        error.line,
        error.column,
        error.end_line,
        error.end_column,
    ) == (
        "syntax",
        "selectors.bl",
        4,
        column,
        4,
        column + 1,
    )
    assert "perch mark" in error.message and "first selector" in error.message
    assert error.write == f"write one perch mark first, as `{remedy}`"
    assert error.write not in error.message
    assert "\n" + " " * (column + 3) + "^" in error.message
    assert "VisitError" not in str(error) and "Error trying to process rule" not in str(error)


@pytest.mark.parametrize(
    "retired",
    [
        pytest.param(False, id="the grammar of the language"),
        pytest.param(True, id="the grammar that also reads a bound after a comma"),
    ],
)
def test_the_parser_builds_in_strict_mode_with_no_conflict_and_no_collision_of_terminals(retired):
    """The parser built with `strict=True` and no other change of its options
    finds no conflict of its tables and no two terminals of equal priority
    that collide, for the grammar of the language and for the grammar that
    also reads a bound after a comma, a spelling that the package reads only
    to refuse it with the sets to write; the build raises, and the test
    fails, where Lark finds a conflict or a collision."""
    if importlib.util.find_spec("interegular") is None:
        # Lark refuses every strict build at the lexer without interegular,
        # after the check of its tables; the test skips with that result
        with pytest.raises(LexError) as refused:
            build_parser(strict=True, retired=retired)
        assert "interegular" in str(refused.value), refused.value
        pytest.skip(
            "the tables of the strict build have no conflict, and the check of its "
            "terminals needs the library interegular, which is not installed"
        )
    build_parser(strict=True, retired=retired)
