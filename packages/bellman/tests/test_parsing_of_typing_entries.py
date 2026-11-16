"""The parsing of typing entries: what the parser reads of the typing entries
of a methods file and of a block header, what the lowering makes of them,
and where each refusal of the two is placed."""

import pytest
from application_files import COPIED_FILES_FOLDER, ROOT, STAGE_FILES
from lark.exceptions import UnexpectedInput

from bellman.refusals import ConstructionError
from bellman.stage import to_source
from bellman.syntax import terms
from bellman.syntax.decode import from_json
from bellman.syntax.lower import parse_with_spans, to_json
from bellman.syntax.walk import nodes

# the constructors that the typing entries add to the parsed term
TYPING_ENTRY_CONSTRUCTORS = (
    terms.Path,
    terms.Term,
    terms.Handler,
    terms.Method,
    terms.Grid,
    terms.Tagged,
)


def bare_path(*segments):
    """A `Path` of bare segments, `bare_path("policy", "method")`."""
    return terms.Path(tuple(terms.Segment(name, ()) for name in segments))


def method_word(word, *keywords):
    """The method `!word`, with the keyword arguments `keywords`."""
    return terms.Method(terms.Word(word, tuple(keywords)))


def spaced_factor(coordinate, lower, upper, count, spacing=None):
    """The factor of a grid on `coordinate` from the setting `lower` to the
    setting `upper` with `count` points, and the spacing word `spacing`."""
    return terms.Spaced(
        coordinate, terms.Name(lower), terms.Name(upper), terms.Name(count), spacing
    )


def typing_entry(subject, classifier):
    """The typing entry that types `subject` by `classifier`."""
    return terms.Typer(terms.Declaration(subject, (classifier,), None))


def printed_line(typing):
    """The line that the printer writes of a typing entry: its subject, a
    colon, and its quoted program or its first classifier."""
    if isinstance(typing, terms.Handler):
        return f'{to_source(typing.subject)} : "{typing.program}"'
    return f"{to_source(typing.subject)} : {to_source(typing.classifiers[0])}"


# the value at the arrival perch, `V[<]`; a Variable is written with its name,
# its perch and its shift in time, 0
V_ARRIVAL = terms.Sym(terms.Variable("V", terms.At(terms.Arrival()), 0))


# a header: the text of a block, and the entries of its annotation; the role
# `Value(0)` is the role word `!vlu`
HEADERS = [
    (
        "the block's method and grid, and the Evaluation's method in a group",
        "[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))\n"
        "    | evaluate.method : !Linear] {\n"
        "    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]\n}\n",
        (
            terms.KeyValue("id", "policy"),
            typing_entry(bare_path("policy", "method"), method_word("egm")),
            typing_entry(
                bare_path("policy", "grid"),
                terms.Grid(terms.Cartesian((spaced_factor("a", "a_min", "a_max", "n_a"),))),
            ),
            typing_entry(bare_path("evaluate", "method"), method_word("Linear")),
        ),
    ),
    (
        "a relative subject beside the signature, the handler and a spacing word in groups",
        "[id=policy, method : !egm,\n    (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn\n"
        '    | handler : "cons-port:egm"\n'
        "    | grid : !Cartesian(a=(a_min, a_max, n_a, !expmult))] {\n    c = c[>]\n}\n",
        (
            terms.KeyValue("id", "policy"),
            typing_entry(bare_path("method"), method_word("egm")),
            terms.Typer(
                terms.Signature(
                    source=terms.Subject(
                        (
                            terms.Coordinate(
                                "V",
                                terms.At(terms.Continuation()),
                                (
                                    terms.Domain(terms.Named("ℝ")),
                                    terms.Role(terms.Value(0)),
                                ),
                            ),
                        )
                    ),
                    source_types=(terms.Infoset(terms.Continuation()),),
                    target=terms.Subject(
                        (
                            terms.Coordinate(
                                "c",
                                None,
                                (terms.Domain(terms.Named("ℝ₊₊")), terms.Role(terms.Control())),
                            ),
                        )
                    ),
                    target_types=(terms.Infoset(terms.Decision()),),
                )
            ),
            terms.Typer(terms.Handler(bare_path("handler"), "cons-port:egm")),
            typing_entry(
                bare_path("grid"),
                terms.Grid(
                    terms.Cartesian(
                        (spaced_factor("a", "a_min", "a_max", "n_a", terms.Word("expmult", ())),)
                    )
                ),
            ),
        ),
    ),
    (
        "keyword arguments, and the Evaluation refined by the object it stores",
        "[id=dcsn_to_arvl\n    | E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)\n"
        "    | evaluate[D_{a_ret}V[<]].method : !Linear"
        " | evaluate[D_{a_ret}V[<]].grid : !Cartesian(a_ret=(a_ret_min, a_ret_max, n_a_ret))\n"
        '    | evaluate[D_{a_ret}V[<]].handler : "dcsmm:interp_as_3"\n'
        "    | evaluate[V[<]].method : !pchip"
        " | evaluate[V].grid : !Cartesian(m=(w_min, w_max, n_w))] {\n"
        "    D_{a_ret}V[<] = R*D_{w}V    :: [id=marginal]\n}\n",
        (
            terms.KeyValue("id", "dcsn_to_arvl"),
            typing_entry(
                bare_path("E_ψ_ξ", "method"),
                method_word(
                    "gauss_hermite",
                    terms.Keyword("n_ψ", terms.Name("n_ψ_nodes")),
                    terms.Keyword("n_ξ", terms.Name("n_ξ_nodes")),
                ),
            ),
            typing_entry(
                terms.Path(
                    (
                        terms.Segment(
                            "evaluate",
                            (
                                terms.Term(
                                    terms.Operator("D", (terms.Var("a_ret"),), (V_ARRIVAL,))
                                ),
                            ),
                        ),
                        terms.Segment("method", ()),
                    )
                ),
                method_word("Linear"),
            ),
            typing_entry(
                terms.Path(
                    (
                        terms.Segment(
                            "evaluate",
                            (
                                terms.Term(
                                    terms.Operator("D", (terms.Var("a_ret"),), (V_ARRIVAL,))
                                ),
                            ),
                        ),
                        terms.Segment("grid", ()),
                    )
                ),
                terms.Grid(
                    terms.Cartesian((spaced_factor("a_ret", "a_ret_min", "a_ret_max", "n_a_ret"),))
                ),
            ),
            terms.Typer(
                terms.Handler(
                    terms.Path(
                        (
                            terms.Segment(
                                "evaluate",
                                (
                                    terms.Term(
                                        terms.Operator("D", (terms.Var("a_ret"),), (V_ARRIVAL,))
                                    ),
                                ),
                            ),
                            terms.Segment("handler", ()),
                        )
                    ),
                    "dcsmm:interp_as_3",
                )
            ),
            typing_entry(
                terms.Path(
                    (
                        terms.Segment("evaluate", (terms.Term(V_ARRIVAL),)),
                        terms.Segment("method", ()),
                    )
                ),
                method_word("pchip"),
            ),
            typing_entry(
                terms.Path(
                    (terms.Segment("evaluate", (terms.Key("V"),)), terms.Segment("grid", ()))
                ),
                terms.Grid(terms.Cartesian((spaced_factor("m", "w_min", "w_max", "n_w"),))),
            ),
        ),
    ),
    (
        "a tag with keyword arguments beside the signature",
        "[id=b, capital(order=2), (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        (
            terms.KeyValue("id", "b"),
            terms.Tagged(terms.Word("capital", (terms.Keyword("order", terms.Literal(2)),))),
            terms.Typer(
                terms.Signature(
                    source=terms.Subject(
                        (terms.Coordinate("x", None, (terms.Domain(terms.Named("ℝ")),)),)
                    ),
                    source_types=(terms.Infoset(terms.Arrival()),),
                    target=terms.Subject(
                        (terms.Coordinate("y", None, (terms.Domain(terms.Named("ℝ")),)),)
                    ),
                    target_types=(terms.Infoset(terms.Decision()),),
                )
            ),
        ),
    ),
]


# a line at file level, and the item it lowers to
LINES = [
    (
        "a method with a keyword argument, routed by its path",
        "cntn_to_dcsn.method : !vfi(tol=tol_v)\n",
        terms.Declare(
            terms.Declaration(
                bare_path("cntn_to_dcsn", "method"),
                (method_word("vfi", terms.Keyword("tol", terms.Name("tol_v"))),),
                None,
            ),
            None,
        ),
    ),
    (
        "a handler binding",
        'dcsn_to_cntn.handler : "cons-port:transition"\n',
        terms.Declare(
            terms.Handler(bare_path("dcsn_to_cntn", "handler"), "cons-port:transition"), None
        ),
    ),
    (
        "a grid on the Evaluation of a node whose second factor lists the nodes of an expectation",
        "cntn_to_dcsn.risk_ce.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m), ν=E_ν)\n",
        terms.Declare(
            terms.Declaration(
                bare_path("cntn_to_dcsn", "risk_ce", "evaluate", "grid"),
                (
                    terms.Grid(
                        terms.Cartesian(
                            (
                                spaced_factor("m_d", "m_min", "m_max", "n_m"),
                                terms.Listed("ν", "E_ν"),
                            )
                        )
                    ),
                ),
                None,
            ),
            None,
        ),
    ),
    (
        "a control's factor, its feasible set with a count",
        "policy.grid : !Cartesian(ς=(Γ_ς, n_ς))\n",
        terms.Declare(
            terms.Declaration(
                bare_path("policy", "grid"),
                (terms.Grid(terms.Cartesian((terms.Feasible("ς", "Γ_ς", terms.Name("n_ς")),))),),
                None,
            ),
            None,
        ),
    ),
    (
        "a spacing word with its own argument",
        "cntn_to_dcsn.evaluate.grid : "
        "!Cartesian(m=(m_min, m_max, n_m, !expmult(nest=grid_phi)))\n",
        terms.Declare(
            terms.Declaration(
                bare_path("cntn_to_dcsn", "evaluate", "grid"),
                (
                    terms.Grid(
                        terms.Cartesian(
                            (
                                spaced_factor(
                                    "m",
                                    "m_min",
                                    "m_max",
                                    "n_m",
                                    terms.Word(
                                        "expmult",
                                        (terms.Keyword("nest", terms.Name("grid_phi")),),
                                    ),
                                ),
                            )
                        )
                    ),
                ),
                None,
            ),
            None,
        ),
    ),
    (
        "a branch label as a segment",
        "dcsn_to_cntn.repay.grid : !Cartesian(a=(a_min, a_max, n_a))\n",
        terms.Declare(
            terms.Declaration(
                bare_path("dcsn_to_cntn", "repay", "grid"),
                (terms.Grid(terms.Cartesian((spaced_factor("a", "a_min", "a_max", "n_a"),))),),
                None,
            ),
            None,
        ),
    ),
    (
        "a definition's method",
        "𝑑𝑢𝑖𝑛𝑣.method : !analytic_inverse\n",
        terms.Declare(
            terms.Declaration(
                bare_path("𝑑𝑢𝑖𝑛𝑣", "method"), (method_word("analytic_inverse"),), None
            ),
            None,
        ),
    ),
    (
        "the five value forms of a keyword argument",
        "dcsn_to_cntn.method : !monte_carlo(n_paths=n_sim, seed=12, "
        'label="draws", shape=(n_a, n_b), spacing=!expmult(nest=phi))\n',
        terms.Declare(
            terms.Declaration(
                bare_path("dcsn_to_cntn", "method"),
                (
                    method_word(
                        "monte_carlo",
                        terms.Keyword("n_paths", terms.Name("n_sim")),
                        terms.Keyword("seed", terms.Literal(12)),
                        terms.Keyword("label", terms.Quoted("draws")),
                        terms.Keyword(
                            "shape", terms.Values((terms.Name("n_a"), terms.Name("n_b")))
                        ),
                        terms.Keyword(
                            "spacing",
                            terms.Nested(
                                terms.Word("expmult", (terms.Keyword("nest", terms.Name("phi")),))
                            ),
                        ),
                    ),
                ),
                None,
            ),
            None,
        ),
    ),
    (
        "a typing entry with a trailing annotation",
        'cntn_to_dcsn.method : !vfi :: ["value function iteration"]\n',
        terms.Declare(
            terms.Declaration(bare_path("cntn_to_dcsn", "method"), (method_word("vfi"),), None),
            terms.Annotation((terms.Tag('"value function iteration"'),)),
        ),
    ),
]


# the methods file of the buffer-stock stage, as the public page on
# methodization writes it
BUFFER_STOCK_METHODS = """@methods: buffer_stock

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


# a form the parser refuses: the text after the metadata line, and the line
# and column of the token the parser stops at
PARSER_REFUSALS = [
    ("a positional argument", "cntn_to_dcsn.method : !vfi(tol_v)\n", (2, 33)),
    ("an empty argument list", "cntn_to_dcsn.method : !vfi()\n", (2, 28)),
    (
        "a word-less argument list",
        "policy.enforcement.method : (initial=k_max, tol=tol_k)\n",
        (2, 37),
    ),
    ("a computed value", "cntn_to_dcsn.method : !vfi(tol=a+b)\n", (2, 33)),
    ("a hyphen in a word", "E_ψ.method : !gauss-hermite\n", (2, 20)),
    (
        "a trailing comma before the closing bracket",
        "[id=x, policy.method : !egm,] {\n    c = a\n}\n",
        (2, 29),
    ),
    ("a bare tag in a later group", "[id=x | !node] {\n    c = a\n}\n", (2, 9)),
    ("an empty group", "[id=x | ] {\n    c = a\n}\n", (2, 9)),
    ("arguments on a bare word tag", "[id=x, !egm(a=b)] {\n    c = a\n}\n", (2, 12)),
]


# a form the grammar admits and the lowering reads no term from: the text,
# the line and column the refusal names, and the phrases of its message
LOWERING_REFUSALS = [
    (
        "a path whose last segment names no component",
        "policy.evaluate : !Linear\n",
        (2, 1),
        ("`policy.evaluate`", "`evaluate` names no component"),
    ),
    (
        "a word of no grid kind on a grid",
        "policy.grid : !egm\n",
        (2, 15),
        ("`!egm`", "no grid kind"),
    ),
    ("a grid with no factor", "policy.grid : !Cartesian\n", (2, 15), ("names no factor",)),
    (
        "a fourth element that is no spacing word",
        "policy.grid : !Cartesian(a=(a_min, a_max, n_a, n_b))\n",
        (2, 1),
        ("`n_b` as its fourth element", "no spacing word"),
    ),
    (
        "a factor of five elements",
        "policy.grid : !Cartesian(a=(1, 2, 3, 4, 5))\n",
        (2, 1),
        ("no shape of a factor",),
    ),
    (
        "a quoted string as a factor",
        'policy.grid : !Cartesian(a="x")\n',
        (2, 1),
        ("no shape of a factor",),
    ),
    (
        "a pair whose first element is no name",
        "policy.grid : !Cartesian(a=((1, 2), n))\n",
        (2, 1),
        ("names no set before its count",),
    ),
    (
        "a bound that is no name and no number",
        'policy.grid : !Cartesian(a=("lo", a_max, n_a))\n',
        (2, 1),
        ("no name of a setting and no number",),
    ),
    (
        "a quoted string on a method component",
        'policy.method : "cons-port:egm"\n',
        (2, 1),
        ("binds a quoted string to `policy.method`", "handler component alone"),
    ),
    (
        "a word on a handler component",
        "policy.handler : !egm\n",
        (2, 1),
        ("`handler` names no component", "bound by a quoted string"),
    ),
    (
        "a set as the type of a method component",
        "policy.method : ℝ\n",
        (2, 1),
        ("typed by `ℝ`", "one !-word"),
    ),
    (
        "two components on a method component",
        "policy.method : !egm @ !Linear\n",
        (2, 1),
        ("typed by `!egm @ !Linear`", "one !-word"),
    ),
    (
        "arguments on a role word",
        "c : !ctrl(x=1)\n",
        (2, 5),
        ("`!ctrl` here with arguments", "takes none"),
    ),
    (
        "a perch mark in a path",
        "[id=b, V[>].method : !egm, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        (2, 8),
        ("the path `V[>].method` carries the perch mark", "inside a selector"),
    ),
    (
        "a keyword written twice",
        "cntn_to_dcsn.method : !vfi(tol=a, tol=b)\n",
        (2, 27),
        ("`tol` is written twice",),
    ),
    (
        "a value on a typing entry",
        "policy.method : !egm <- 2\n",
        (2, 1),
        ("carries a value or a condition",),
    ),
    (
        "a condition on a typing entry",
        "policy.method : !egm, < 2\n",
        (2, 1),
        ("carries a value or a condition",),
    ),
]


# each text of a methods file that a test of this file lowers: the headers,
# the file-level lines, the one printed line that differs from its written
# line, and the methods file of the buffer-stock stage
METHODS_TEXTS = [
    *(
        pytest.param("@methods: t\n" + text, id=f"the header with {name}")
        for name, text, _ in HEADERS
    ),
    *(pytest.param("@methods: t\n" + text, id=f"the line with {name}") for name, text, _ in LINES),
    pytest.param(
        "@methods: t\ncntn_to_dcsn.method : !vfi\n",
        id="the printed line of a method with no argument",
    ),
    pytest.param(BUFFER_STOCK_METHODS, id="the methods file of the buffer-stock stage"),
]


@pytest.fixture(scope="module")
def buffer_stock_methods():
    """The term and the span table of the methods file of the buffer-stock
    stage, parsed from `BUFFER_STOCK_METHODS` under the file name
    `methods.bl`."""
    return parse_with_spans(BUFFER_STOCK_METHODS, "methods.bl")


@pytest.mark.parametrize(
    ("text", "entries"), [pytest.param(text, entries, id=name) for name, text, entries in HEADERS]
)
def test_each_header_of_a_methods_file_lowers_to_the_entries_of_its_annotation(text, entries):
    """The header of a block of a methods file lowers to the annotation whose
    entries are the id, the typing entries, the tags and the signature that
    it writes, in its order."""
    term, _ = parse_with_spans("@methods: t\n" + text, "t.bl")
    assert term.items[1].tag == terms.Annotation(entries)


@pytest.mark.parametrize(
    ("text", "item"), [pytest.param(text, item, id=name) for name, text, item in LINES]
)
def test_each_typing_entry_at_file_level_lowers_to_its_item(text, item):
    """A typing entry written at the file level of a methods file lowers to the
    item that declares its subject by its method, grid or handler."""
    term, _ = parse_with_spans("@methods: t\n" + text, "t.bl")
    assert term.items[1] == item


@pytest.mark.parametrize("item", [pytest.param(item, id=name) for name, _, item in LINES])
def test_the_typing_of_each_entry_at_file_level_prints_to_a_line_that_lowers_to_the_same_typing(
    item,
):
    """The line that the printer writes of the typing of a file-level entry
    lowers to that typing."""
    typing = item.declaration
    term, _ = parse_with_spans("@methods: t\n" + printed_line(typing) + "\n", "t.bl")
    assert term.items[1].declaration == typing


@pytest.mark.parametrize("text", METHODS_TEXTS)
def test_the_term_of_each_text_of_a_methods_file_reads_back_from_its_json_encoding(text):
    """The term that the lowering makes of a text of a methods file equals the
    term that `from_json` reads from the encoding that `to_json` writes of
    it."""
    term, _ = parse_with_spans(text, "t.bl")
    assert from_json(to_json(term)) == term


def test_the_first_item_of_the_buffer_stock_methods_file_is_its_metadata_line(
    buffer_stock_methods,
):
    """The term of the buffer-stock methods file begins with the metadata line
    `@methods: buffer_stock`."""
    term, _ = buffer_stock_methods
    assert term.items[0] == terms.Metadata("methods", "buffer_stock")


def test_the_buffer_stock_methods_file_lowers_to_four_methods_two_grids_and_no_handler(
    buffer_stock_methods,
):
    """The term of the buffer-stock methods file holds the four methods and the
    two grids that its headers type, and no handler."""
    term, _ = buffer_stock_methods
    kinds = [type(node).__name__ for node in nodes(term)]
    assert (kinds.count("Method"), kinds.count("Grid"), kinds.count("Handler")) == (4, 2, 0)


def test_the_settings_of_the_buffer_stock_methods_file_lower_as_the_declarations_of_a_stage_file(
    buffer_stock_methods,
):
    """The eight settings that the buffer-stock methods file declares, its
    items after the metadata line, lower to declarations of a subject, as a
    stage file writes them."""
    term, _ = buffer_stock_methods
    assert all(
        isinstance(item.declaration, terms.Declaration)
        and isinstance(item.declaration.subject, terms.Subject)
        for item in term.items[1:9]
    )


def test_the_span_table_of_the_buffer_stock_methods_file_places_each_typing_entry_where_written(
    buffer_stock_methods,
):
    """The span table of the buffer-stock methods file names each typing entry
    of a header under its block and its subject as written, at the line and
    column of the entry."""
    _, spans = buffer_stock_methods
    entries = {
        address: (span.line, span.column)
        for address, span in spans.items()
        if ".method" in address or ".grid" in address
    }
    assert entries == {
        "policy.policy.method": (12, 13),
        "policy.policy.grid": (12, 36),
        "policy.evaluate.method": (13, 7),
        "dcsn_to_arvl.E_ψ_ξ.method": (24, 7),
        "dcsn_to_arvl.evaluate.method": (25, 7),
        "dcsn_to_arvl.evaluate.grid": (26, 7),
    }


def test_no_stage_file_lowers_to_a_term_that_holds_a_constructor_of_the_typing_entries():
    """No stage file of the applications or of the test corpus, a file whose
    first line is `@stage:`, lowers to a term that holds a constructor that
    only the typing entries make; a methods file beside a stage file, whose
    first line is `@methods:`, is no stage file and is not read."""
    # every stage file of the applications stands in the one layout that
    # STAGE_FILES reads; the test corpus holds .bl files at any depth
    corpus = sorted((ROOT / COPIED_FILES_FOLDER).rglob("*.bl"))
    texts = {src: src.read_text(encoding="utf-8") for src in [*STAGE_FILES, *corpus]}
    stage_files = [src for src, text in texts.items() if text.startswith("@stage:")]
    assert len(stage_files) > 80
    for src in stage_files:
        term, _ = parse_with_spans(texts[src], str(src))
        assert not any(isinstance(node, TYPING_ENTRY_CONSTRUCTORS) for node in nodes(term)), src


@pytest.mark.parametrize(
    ("text", "column", "word"),
    [
        pytest.param(
            "[id=policy, (V[>]) : !cntn @ !egm -> (c) : !dcsn] {\n    c = V[>]\n}\n",
            30,
            "!egm",
            id="a method word on a side",
        ),
        pytest.param(
            "evaluate[value] : !Linear @ K_grid\n", 19, "!Linear", id="an iterated key with a set"
        ),
        pytest.param(
            "policy[evaluate][method] : !Linear\n", 28, "!Linear", id="an iterated key subject"
        ),
    ],
)
def test_a_method_word_on_a_side_or_typing_a_subject_selected_by_keys_is_refused_as_no_word_type(
    text, column, word
):
    """A method word on the side of a block header, or as the type of a
    subject selected by keys, is refused under `syntax` at the word, which
    the message calls no word-type of the language."""
    with pytest.raises(ConstructionError) as refused:
        parse_with_spans("@stage: t\n" + text, "t.bl")
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", 2, column)
    assert f"`{word}` here, which is no word-type of the language" in error.message


@pytest.mark.parametrize(
    ("text", "line", "column"),
    [pytest.param(text, line, column, id=name) for name, text, (line, column) in PARSER_REFUSALS],
)
def test_a_form_the_grammar_does_not_admit_is_refused_by_the_parser_at_its_token(
    text, line, column
):
    """The parser refuses a typing entry that the grammar does not admit at the
    line and the column of the token where it stops."""
    with pytest.raises(UnexpectedInput) as refused:
        parse_with_spans("@methods: t\n" + text, "t.bl")
    assert (refused.value.line, refused.value.column) == (line, column)


@pytest.mark.parametrize(
    ("text", "line", "column", "phrases"),
    [
        pytest.param(text, line, column, phrases, id=name)
        for name, text, (line, column), phrases in LOWERING_REFUSALS
    ],
)
def test_a_typing_entry_the_lowering_reads_no_term_from_is_refused_where_it_is_written(
    text, line, column, phrases
):
    """The lowering refuses a typing entry that the grammar admits and that
    reads as no term under `syntax`, at its line and column, with a message
    in its own words and none of the words of the parser library."""
    with pytest.raises(ConstructionError) as refused:
        parse_with_spans("@methods: t\n" + text, "t.bl")
    error = refused.value
    assert (error.rule, error.file, error.line, error.column) == ("syntax", "t.bl", line, column)
    assert [phrase for phrase in phrases if phrase not in error.message] == []
    # the words of the parser library and the names of the lowering's own
    # classes, which no message of a refusal shows
    internal = ("Error trying to process rule", "VisitError", "_Path", "_Word", "Select(")
    assert [word for word in internal if word in error.message] == []
