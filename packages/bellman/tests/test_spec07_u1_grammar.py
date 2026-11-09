"""The acceptance file of unit U1 of the build of specification 0.7, the
grammar and the lowering of the typing entries: one test for each of the
four acceptance items of §U1 of the implementation specification, named
`test_item_<n>_<claim>`; then the exact-term fixtures, one specimen of each
new spelling taken from the case studies of the specification, lowered and
compared with the term written by hand; the normalization fixture, that a
printed entry re-parses to its term; and the negative fixtures, each
asserting the phase that refuses a form, the parser or the lowering, and the
line and the column of the refusal. The decisions of the derivation stand in
the decision record of the grammar folder of the specification's
implementation.
"""
from __future__ import annotations

import pathlib
import subprocess

import pytest
from conftest import ROOT
from lark.exceptions import LexError, UnexpectedInput

from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.syntax.parse import build_parser
from bellman.syntax.source import to_source
from bellman.syntax.walk import nodes

# the constructors the typing entries add to the parsed AST
NEW_CONSTRUCTORS = (T.Path, T.Term, T.Handler, T.Method, T.Grid, T.Tagged)


def lowered(text, name="t.bl"):
    """The FILE a text lowers to, with its span table, the JSON encoding
    checked to decode back to the same term."""
    term, spans = parse_with_spans(text, name)
    assert from_json(to_json(term)) == term
    return term, spans


def path(*segments):
    """A `Path` of bare segments, `path("policy", "method")`."""
    return T.Path(tuple(T.Segment(name, ()) for name in segments))


def method(word, *keywords):
    return T.Method(T.Word(word, tuple(keywords)))


def spaced(coordinate, lower, upper, count, spacing=None):
    return T.Spaced(coordinate, T.Name(lower), T.Name(upper), T.Name(count), spacing)


def typer(subject, classifier):
    return T.Typer(T.Declaration(subject, (classifier,), None))


V_ARRIVAL = T.Sym(T.Variable("V", T.At(T.Arrival()), 0))
V_CONTINUATION = T.Sym(T.Variable("V", T.At(T.Continuation()), 0))

# --- the exact-term fixtures: one specimen of each new spelling ---

# a header: the text of a block, and the entries of its annotation
HEADERS = [
    (
        "the block's method and grid, and the Evaluation's method in a group",
        "[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))\n"
        "    | evaluate.method : !Linear] {\n    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]\n}\n",
        (
            T.KeyValue("id", "policy"),
            typer(path("policy", "method"), method("egm")),
            typer(path("policy", "grid"), T.Grid(T.Cartesian((spaced("a", "a_min", "a_max", "n_a"),)))),
            typer(path("evaluate", "method"), method("Linear")),
        ),
    ),
    (
        "a relative subject beside the signature, the handler and a spacing word in groups",
        "[id=policy, method : !egm,\n    (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn\n"
        '    | handler : "cons-port:egm"\n'
        "    | grid : !Cartesian(a=(a_min, a_max, n_a, !expmult))] {\n    c = c[>]\n}\n",
        (
            T.KeyValue("id", "policy"),
            typer(path("method"), method("egm")),
            T.Typer(T.Signature(
                source=T.Subject((T.Coordinate("V", T.At(T.Continuation()),
                                               (T.Domain(T.Named("ℝ")), T.Role(T.Value(0)))),)),
                source_types=(T.Infoset(T.Continuation()),),
                target=T.Subject((T.Coordinate("c", None, (T.Domain(T.Named("ℝ₊₊")), T.Role(T.Control()))),)),
                target_types=(T.Infoset(T.Decision()),),
            )),
            T.Typer(T.Handler(path("handler"), "cons-port:egm")),
            typer(path("grid"), T.Grid(T.Cartesian((spaced("a", "a_min", "a_max", "n_a", T.Word("expmult", ())),)))),
        ),
    ),
    (
        "keyword arguments, and the Evaluation refined by the object it stores",
        "[id=dcsn_to_arvl\n    | E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)\n"
        "    | evaluate[D_{a_ret}V[<]].method : !Linear"
        " | evaluate[D_{a_ret}V[<]].grid : !Cartesian(a_ret=(a_ret_min, a_ret_max, n_a_ret))\n"
        '    | evaluate[D_{a_ret}V[<]].handler : "dcsmm:interp_as_3"\n'
        "    | evaluate[V[<]].method : !pchip | evaluate[V].grid : !Cartesian(m=(w_min, w_max, n_w))] {\n"
        "    D_{a_ret}V[<] = R*D_{w}V    :: [id=marginal]\n}\n",
        (
            T.KeyValue("id", "dcsn_to_arvl"),
            typer(path("E_ψ_ξ", "method"),
                  method("gauss_hermite", T.Keyword("n_ψ", T.Name("n_ψ_nodes")), T.Keyword("n_ξ", T.Name("n_ξ_nodes")))),
            typer(T.Path((T.Segment("evaluate", (T.Term(T.Operator("D", (T.Var("a_ret"),), (V_ARRIVAL,))),)),
                          T.Segment("method", ()))), method("Linear")),
            typer(T.Path((T.Segment("evaluate", (T.Term(T.Operator("D", (T.Var("a_ret"),), (V_ARRIVAL,))),)),
                          T.Segment("grid", ()))),
                  T.Grid(T.Cartesian((spaced("a_ret", "a_ret_min", "a_ret_max", "n_a_ret"),)))),
            T.Typer(T.Handler(T.Path((T.Segment("evaluate", (T.Term(T.Operator("D", (T.Var("a_ret"),), (V_ARRIVAL,))),)),
                                      T.Segment("handler", ()))), "dcsmm:interp_as_3")),
            typer(T.Path((T.Segment("evaluate", (T.Term(V_ARRIVAL),)), T.Segment("method", ()))), method("pchip")),
            typer(T.Path((T.Segment("evaluate", (T.Key("V"),)), T.Segment("grid", ()))),
                  T.Grid(T.Cartesian((spaced("m", "w_min", "w_max", "n_w"),)))),
        ),
    ),
    (
        "a tag with keyword arguments beside the signature",
        "[id=b, capital(order=2), (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        (
            T.KeyValue("id", "b"),
            T.Tagged(T.Word("capital", (T.Keyword("order", T.Literal(2)),))),
            T.Typer(T.Signature(
                source=T.Subject((T.Coordinate("x", None, (T.Domain(T.Named("ℝ")),)),)),
                source_types=(T.Infoset(T.Arrival()),),
                target=T.Subject((T.Coordinate("y", None, (T.Domain(T.Named("ℝ")),)),)),
                target_types=(T.Infoset(T.Decision()),),
            )),
        ),
    ),
]

# a line at file level, and the item it lowers to
LINES = [
    ("a method with a keyword argument, routed by its path",
     "cntn_to_dcsn.method : !vfi(tol=tol_v)\n",
     T.Declare(T.Declaration(path("cntn_to_dcsn", "method"),
                             (method("vfi", T.Keyword("tol", T.Name("tol_v"))),), None), None)),
    ("a handler binding", 'dcsn_to_cntn.handler : "cons-port:transition"\n',
     T.Declare(T.Handler(path("dcsn_to_cntn", "handler"), "cons-port:transition"), None)),
    ("a grid on a node's Evaluation, a factor the expectation operator's nodes",
     "cntn_to_dcsn.risk_ce.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m), ν=E_ν)\n",
     T.Declare(T.Declaration(path("cntn_to_dcsn", "risk_ce", "evaluate", "grid"),
                             (T.Grid(T.Cartesian((spaced("m_d", "m_min", "m_max", "n_m"), T.Listed("ν", "E_ν")))),),
                             None), None)),
    ("a control's factor, its feasible set with a count",
     "policy.grid : !Cartesian(ς=(Γ_ς, n_ς))\n",
     T.Declare(T.Declaration(path("policy", "grid"),
                             (T.Grid(T.Cartesian((T.Feasible("ς", "Γ_ς", T.Name("n_ς")),))),), None), None)),
    ("a spacing word with its own argument",
     "cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_min, m_max, n_m, !expmult(nest=grid_phi)))\n",
     T.Declare(T.Declaration(path("cntn_to_dcsn", "evaluate", "grid"),
                             (T.Grid(T.Cartesian((spaced("m", "m_min", "m_max", "n_m",
                                                         T.Word("expmult", (T.Keyword("nest", T.Name("grid_phi")),))),))),),
                             None), None)),
    ("a branch label as a segment", "dcsn_to_cntn.repay.grid : !Cartesian(a=(a_min, a_max, n_a))\n",
     T.Declare(T.Declaration(path("dcsn_to_cntn", "repay", "grid"),
                             (T.Grid(T.Cartesian((spaced("a", "a_min", "a_max", "n_a"),))),), None), None)),
    ("a definition's method", "𝑑𝑢𝑖𝑛𝑣.method : !analytic_inverse\n",
     T.Declare(T.Declaration(path("𝑑𝑢𝑖𝑛𝑣", "method"), (method("analytic_inverse"),), None), None)),
    ("the five value forms of a keyword argument",
     'dcsn_to_cntn.method : !monte_carlo(n_paths=n_sim, seed=12, label="draws", shape=(n_a, n_b), spacing=!expmult(nest=phi))\n',
     T.Declare(T.Declaration(path("dcsn_to_cntn", "method"),
                             (method("monte_carlo",
                                     T.Keyword("n_paths", T.Name("n_sim")),
                                     T.Keyword("seed", T.Literal(12)),
                                     T.Keyword("label", T.Quoted("draws")),
                                     T.Keyword("shape", T.Values((T.Name("n_a"), T.Name("n_b")))),
                                     T.Keyword("spacing", T.Nested(T.Word("expmult", (T.Keyword("nest", T.Name("phi")),))))),),
                             None), None)),
    ("a typing entry with a trailing annotation",
     'cntn_to_dcsn.method : !vfi :: ["value function iteration"]\n',
     T.Declare(T.Declaration(path("cntn_to_dcsn", "method"), (method("vfi"),), None),
               T.Annotation((T.Tag('"value function iteration"'),)))),
]

# the methods file of the buffer-stock stage, as the case study writes it
BUFFER_STOCK = """@methods: buffer_stock

n_a : ℕ              :: ["number of points of the savings grid"]
a_min : Xa           :: ["lower bound of the savings grid"]
a_max : Xa           :: ["upper bound of the savings grid"]
n_k : ℕ              :: ["number of points of the asset grid"]
k_min : Xa           :: ["lower bound of the asset grid"]
k_max : Xa           :: ["upper bound of the asset grid"]
n_ψ_nodes : ℕ        :: ["quadrature nodes of the permanent shock"]
n_ξ_nodes : ℕ        :: ["quadrature nodes of the transitory shock"]

[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))
    | evaluate.method : !Linear] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}

[id=cntn_to_dcsn] {
    D_{m}V = 𝑑𝑢(c)                                  :: [id=marginal]
}

[id=dcsn_to_arvl
    | E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)
    | evaluate.method : !Linear
    | evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))] {
    D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)    :: [id=marginal]
}
"""


# --- the acceptance items ---


def test_item_1_every_header_spelling_of_the_sheet_lowers_to_its_constructor():
    for case in HEADERS:
        _, text, entries = case
        term, _ = lowered("@methods: t\n" + text)
        assert term.items[1].tag == T.Annotation(entries)


def test_item_1_every_file_level_spelling_of_the_sheet_lowers_to_its_constructor():
    for case in LINES:
        _, text, item = case
        term, _ = lowered("@methods: t\n" + text)
        assert term.items[1] == item
        typing = item.declaration
        if isinstance(typing, T.Handler):
            printed = f'{to_source(typing.subject)} : "{typing.program}"'
        else:
            printed = f"{to_source(typing.subject)} : {to_source(typing.classifiers[0])}"
        term, _ = lowered("@methods: t\n" + printed + "\n")
        assert term.items[1].declaration == typing


def test_item_1_the_buffer_stock_methods_file_lowers_with_the_positions_of_its_entries():
    term, spans = lowered(BUFFER_STOCK, "methods.bl")
    assert term.items[0] == T.Metadata("methods", "buffer_stock")
    kinds = [type(node).__name__ for node in nodes(term)]
    assert (kinds.count("Method"), kinds.count("Grid"), kinds.count("Handler")) == (4, 2, 0)
    # the eight settings are declarations as a stage file writes them
    assert all(isinstance(item.declaration, T.Declaration) and isinstance(item.declaration.subject, T.Subject)
               for item in term.items[1:9])
    # the span table names each entry under its block and its subject as
    # written, at the entry's line and column
    entries = {address: (span.line, span.column) for address, span in spans.items()
               if ".method" in address or ".grid" in address}
    assert entries == {
        "policy.policy.method": (12, 13), "policy.policy.grid": (12, 36), "policy.evaluate.method": (13, 7),
        "dcsn_to_arvl.E_ψ_ξ.method": (24, 7), "dcsn_to_arvl.evaluate.method": (25, 7),
        "dcsn_to_arvl.evaluate.grid": (26, 7),
    }


def test_item_2_every_stage_file_of_the_corpus_lowers_to_a_term_without_the_new_constructors():
    """No stage file under applications/ or under the test corpus carries a
    new spelling: each lowers as before, to a term holding none of the
    constructors the typing entries add; its equality with the recorded
    term is the corpus test's claim. The additions beside the stage files,
    whose first line is `@methods:`, carry the new constructors and are read
    by the acceptance files of the later units."""
    # the tracked files alone: a checkout may hold an ignored scratch folder under applications/
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--", "applications/**/*.bl", "packages/bellman/tests/corpus/**/*.bl"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    texts = {ROOT / f: (ROOT / f).read_text(encoding="utf-8") for f in sorted(tracked)}
    stage_files = [src for src, text in texts.items() if text.startswith("@stage:")]
    assert len(stage_files) > 80
    for src in stage_files:
        term, _ = parse_with_spans(texts[src], str(src))
        assert not any(isinstance(node, NEW_CONSTRUCTORS) for node in nodes(term)), src


@pytest.mark.parametrize("text, column, word", [
    ("[id=policy, (V[>]) : !cntn @ !egm -> (c) : !dcsn] {\n    c = V[>]\n}\n", 30, "!egm"),
    ("evaluate[value] : !Linear @ K_grid\n", 19, "!Linear"),
    ("policy[evaluate][method] : !Linear\n", 28, "!Linear"),
], ids=["a method word on a side", "an iterated key with a set", "an iterated key subject"])
def test_item_3_the_three_spellings_the_reader_refused_stay_refused_with_the_same_diagnostic(text, column, word):
    with pytest.raises(ConstructionError) as refused:
        parse_with_spans("@stage: t\n" + text, "t.bl")
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", 2, column)
    assert f"`{word}` here, which is no word-type of the language" in error.message


def test_item_4_the_grammar_builds_under_strict_mode():
    """The strict certificate: the parser the package ships, built with
    `strict=True` and no other change of its options, finds no shift/reduce
    or reduce/reduce conflict and, under `interegular`, no collision
    between terminals of equal priority. Without `interegular` Lark refuses
    every strict build at the lexer, and the test records the weaker result
    instead of claiming the certificate."""
    try:
        build_parser(strict=True)
    except LexError as error:
        assert "interegular" in str(error), error
        pytest.skip("not strict-certified under this interpreter: the parser-table half passed, and "
                    "the lexer-collision half needs interegular, which is not installed")


# --- normalization: a printed entry re-parses to its term ---




# --- the negative fixtures: the phase and the position of each refusal ---

# a form the parser refuses: the text after the metadata line, and the line
# and column of the token the parser stops at
PARSER_REFUSALS = [
    ("a positional argument", "cntn_to_dcsn.method : !vfi(tol_v)\n", (2, 33)),
    ("an empty argument list", "cntn_to_dcsn.method : !vfi()\n", (2, 28)),
    ("a word-less argument list", "policy.enforcement.method : (initial=k_max, tol=tol_k)\n", (2, 37)),
    ("a computed value", "cntn_to_dcsn.method : !vfi(tol=a+b)\n", (2, 33)),
    ("a hyphen in a word", "E_ψ.method : !gauss-hermite\n", (2, 20)),
    ("a trailing comma before the closing bracket", "[id=x, policy.method : !egm,] {\n    c = a\n}\n", (2, 29)),
    ("a bare tag in a later group", "[id=x | !node] {\n    c = a\n}\n", (2, 9)),
    ("an empty group", "[id=x | ] {\n    c = a\n}\n", (2, 9)),
    ("arguments on a bare word tag", "[id=x, !egm(a=b)] {\n    c = a\n}\n", (2, 12)),
]


def test_a_form_the_grammar_does_not_admit_is_refused_by_the_parser_at_its_token():
    for case in PARSER_REFUSALS:
        _, text, (line, column) = case
        with pytest.raises(UnexpectedInput) as refused:
            parse_with_spans("@methods: t\n" + text, "t.bl")
        assert (refused.value.line, refused.value.column) == (line, column)


# a form the grammar admits and the lowering reads no term from: the text,
# the line and column the refusal names, and the words of its sentence
LOWERING_REFUSALS = [
    ("a path whose last segment names no component", "policy.evaluate : !Linear\n", (2, 1),
     ("`policy.evaluate`", "`evaluate` names no component")),
    ("a word of no grid kind on a grid", "policy.grid : !egm\n", (2, 15), ("`!egm`", "no grid kind")),
    ("a grid with no factor", "policy.grid : !Cartesian\n", (2, 15), ("names no factor",)),
    ("a fourth element that is no spacing word", "policy.grid : !Cartesian(a=(a_min, a_max, n_a, n_b))\n", (2, 1),
     ("`n_b` as its fourth element", "no spacing word")),
    ("a factor of five elements", "policy.grid : !Cartesian(a=(1, 2, 3, 4, 5))\n", (2, 1), ("no shape of a factor",)),
    ("a quoted string as a factor", 'policy.grid : !Cartesian(a="x")\n', (2, 1), ("no shape of a factor",)),
    ("a pair whose first element is no name", "policy.grid : !Cartesian(a=((1, 2), n))\n", (2, 1),
     ("names no set before its count",)),
    ("a bound that is no name and no number", 'policy.grid : !Cartesian(a=("lo", a_max, n_a))\n', (2, 1),
     ("no name of a setting and no number",)),
    ("a quoted string on a method component", 'policy.method : "cons-port:egm"\n', (2, 1),
     ("binds a quoted string to `policy.method`", "handler component alone")),
    ("a word on a handler component", "policy.handler : !egm\n", (2, 1),
     ("`handler` names no component", "bound by a quoted string")),
    ("a set as the type of a method component", "policy.method : ℝ\n", (2, 1), ("typed by `ℝ`", "one !-word")),
    ("two components on a method component", "policy.method : !egm @ !Linear\n", (2, 1),
     ("typed by `!egm @ !Linear`", "one !-word")),
    ("arguments on a role word", "c : !ctrl(x=1)\n", (2, 5), ("`!ctrl` here with arguments", "takes none")),
    ("a perch mark in a path", "[id=b, V[>].method : !egm, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
     (2, 8), ("the path `V[>].method` carries the perch mark", "inside a selector")),
    ("a keyword written twice", "cntn_to_dcsn.method : !vfi(tol=a, tol=b)\n", (2, 27),
     ("`tol` is written twice",)),
    ("a value on a typing entry", "policy.method : !egm <- 2\n", (2, 1), ("carries a value or a condition",)),
]


def test_a_form_the_lowering_reads_no_term_from_is_refused_where_it_is_written():
    for case in LOWERING_REFUSALS:
        _, text, (line, column), words = case
        with pytest.raises(ConstructionError) as refused:
            parse_with_spans("@methods: t\n" + text, "t.bl")
        error = refused.value
        assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", line, column)
        assert all(word in error.message for word in words), (words, error.message)
        for internal in ("Error trying to process rule", "VisitError", "_Path", "_Word", "Select("):
            assert internal not in error.message
