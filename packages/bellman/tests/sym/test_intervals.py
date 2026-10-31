"""Interval regression tests: every bracket shape, every position.

Half-open intervals close ( with ] or [ with ), so they are the one
place the surface mixes bracket kinds. The newline postlexer once
counted parentheses alone, and an open-closed interval leaked depth
and swallowed every newline after it (fixed 27 Aug 2026: one
combined depth over both kinds). Each case here ends with a further
statement on the next line, so a swallowed newline fails the parse.

A named set may be defined as an interval other than the open-open one,
`Xa := [0, ā]` (15 Oct 2026): the tests at the end check the three admitted
forms, the equality of the stage encoding with the inline form, and the
pair reading of `(a, b)` after `:=`.
"""

import json

import pytest

from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.lower import ToAst, parse_with_spans, to_json
from bellman.syntax.parse import build_parser
from bellman.syntax.source import to_source

SHAPES = ["(0, 1)", "(0, 1]", "[0, 1)", "[0, 1]"]

DECLARATION = """@stage: t

p : {shape}
q : ℝ₊
"""

SIDE = """@stage: t

[id=b, (v : {shape} @ !vlu, c) : !cntn -> (w : ℝ₊) : !dcsn] {{
    w = v + c
    c = w - v
}}
"""

BINDER = """@stage: t

k : ℝ₊

[id=b, (v : ℝ₊, c) -> (w : ℝ₊)] {{
    𝑓(x : {shape}) := x + k
    w = 𝑓(v)
}}
"""


def test_every_interval_shape_parses_in_every_position():
    for position, template in (("declaration", DECLARATION), ("signature side", SIDE), ("function binder", BINDER)):
        for shape in SHAPES:
            assert parse_with_spans(template.format(shape=shape)).term is not None, (position, shape)


def test_a_correspondence_body_by_comprehension_is_its_term_and_prints_back_while_a_pair_stays_a_tuple():
    # the strict feasible set of the smooth-ambiguity stage (AMD-SG-009 §6)
    from bellman.syntax.source import to_source
    from bellman.syntax.lower import ToAst
    from bellman.syntax.parse import build_parser
    from bellman.syntax.terms import (Comprehension, Constant, Coordinate, CorrDef, Domain, FuncDef, Lt, Named, Rel,
                                   Subject, Sym, Tuple)

    def parse(text):
        return ToAst().transform(build_parser().parse(f"@stage: t\n\n{text}\n")).items[1].core
    written = "Γ(x : ℝ₊₊) := {c : ℝ₊₊ | c < x}"
    term = parse(written)
    assert term == CorrDef("Γ", (Coordinate("x", None, (Domain(Named("ℝ₊₊")),)),),
                           Comprehension(Subject((Coordinate("c", None, ()),)), Named("ℝ₊₊"),
                                         (Rel(Sym(Constant("c")), Lt(), Sym(Constant("x"))),)))
    assert to_source(term) == written
    assert parse(to_source(term)) == term
    pair = parse("𝑓(x : ℝ₊₊) := (0, x)")
    assert isinstance(pair, FuncDef) and isinstance(pair.body, Tuple)


# --- a named set defined as an interval ---

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

CLOSED = T.Interval(
    T.Range(left=T.Closed(), lower=T.Number(0), upper=T.Sym(T.Constant("ā")), right=T.Closed())
)
NAMED_XA = {"__class__": "Named", "name": "Xa"}


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
    return ToAst().transform(build_parser().parse(f"@stage: t\n\nā : ℝ₊₊\n{line}\n")).items[2]


def encoding(stage):
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


def test_a_closed_interval_with_a_parameter_endpoint_defines_a_named_set(elaborate_text):
    statement = assignment_statement("Xa := [0, ā] :: [\"assets\"]")
    assert statement.core == T.Assignment(T.Constant("Xa"), T.Space(CLOSED))
    assert statement.annot == T.Annotation((T.Tag('"assets"'),))
    assert to_source(statement.core) == "Xa := [0, ā]"
    named = elaborate_text(NAMED_SET.format(definition="[0, ā]"))
    inline = elaborate_text(inline_form("[0, ā]"))
    # each field record keeps its set as written: the name, or the interval
    for identity in ("retiree:arvl:a_r", "retiree:dcsn:a_d", "retiree:cntn:a_rr"):
        assert named.fields()[identity].domain == T.Named("Xa")
        assert inline.fields()[identity].domain == CLOSED
    # the named stage defines the set as the interval the inline stage writes
    definitions = {d["identity"]: d for d in encoding(named)["definitions"]}
    assert definitions["retiree:set:Xa"]["kind"] == "set"
    assert definitions["retiree:set:Xa"]["equations"][0]["term"] == to_json(CLOSED)
    assert "retiree:set:Xa" not in {d["identity"] for d in encoding(inline)["definitions"]}


def test_a_named_interval_encodes_as_the_inline_form_once_the_name_is_read(elaborate_text):
    named = encoding(elaborate_text(NAMED_SET.format(definition="[0, ā]")))
    inline = encoding(elaborate_text(inline_form("[0, ā]")))
    definition = next(d for d in named["definitions"] if d["identity"] == "retiree:set:Xa")
    resolved = with_name_read_as(named, NAMED_XA, definition["equations"][0]["term"])
    resolved["definitions"] = [d for d in resolved["definitions"] if d is not definition
                               and d["identity"] != "retiree:set:Xa"]
    # `derived` names the set by its identity and quotes the headers as
    # written, and `provenance` digests the text; every other section agrees
    for section in ("definitions", "initial_diagrams", "builders", "bindings", "obligations",
                    "diagnostics"):
        assert resolved[section] == inline[section], section


@pytest.mark.parametrize("definition, left, right", [("(0, ā]", T.Open(), T.Closed()),
                                                     ("[0, ā)", T.Closed(), T.Open())])
def test_each_half_open_form_defines_a_named_set_and_prints_back(
    definition, left, right, elaborate_text
):
    interval = T.Interval(
        T.Range(left=left, lower=T.Number(0), upper=T.Sym(T.Constant("ā")), right=right)
    )
    statement = assignment_statement(f"Xa := {definition}")
    assert statement.core == T.Assignment(T.Constant("Xa"), T.Space(interval))
    assert to_source(statement.core) == f"Xa := {definition}"
    named = elaborate_text(NAMED_SET.format(definition=definition))
    assert named.fields()["retiree:arvl:a_r"].domain == T.Named("Xa")
    definitions = {d["identity"]: d for d in encoding(named)["definitions"]}
    assert definitions["retiree:set:Xa"]["equations"][0]["term"] == to_json(interval)
    assert inline_form(definition).count(definition) == 4
    assert elaborate_text(inline_form(definition)).fields()["retiree:arvl:a_r"].domain == interval


def test_the_open_open_form_after_the_assignment_sign_is_a_pair_and_is_refused(elaborate_text):
    # the grammar reads `(a, b)` as a tuple in this position, as it does in a
    # correspondence body, so the line defines no set
    statement = assignment_statement("Xa := (0, ā)")
    assert statement.core == T.Assignment(
        T.Constant("Xa"), T.Tuple((T.Number(0), T.Sym(T.Constant("ā"))))
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(NAMED_SET.format(definition="(0, ā)"))
    error = refused.value
    assert (error.rule, error.line) == ("not-constructed", 6)
    assert "definition 'Xa'" in error.message and "(0, ā)" in error.message
    # the printer has no spelling for a named set whose body is open-open
    open_open = T.Interval(
        T.Range(left=T.Open(), lower=T.Number(0), upper=T.Number(1), right=T.Open())
    )
    with pytest.raises(NotImplementedError, match="tuple"):
        to_source(T.Assignment(T.Constant("Xa"), T.Space(open_open)))
