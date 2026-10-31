"""Source spans of authored `.bl` items (spec 0.3c, task S05).

The Lark parser propagates positions to every parse-tree node and `ToAst`
discards them. `bellman.syntax.lower.parse_with_spans` keeps, for each authored
item — a metadata line, an assignment, a declaration, a function definition, a
law, a block, a statement inside a block — the file name and the start and end
line and column, in a table keyed by the item's address (decision register D06,
"span-table addresses", 5 Sep 2026). The term it returns is the term `ToAst`
returns; no position is stored on any term, and the saved AST JSON is unchanged.
After the items the table holds the components of the block headers (unit T
of the model interface specification 0.3), which the tests of the items read
past.

Every expected number below is derived from the source text, whose line is
cited beside it, and checked by slicing that text at the span. Lengths are
counts of code points, which is how Lark counts columns: a column is 1-based,
and `end_column` is the column just after the item's last character.
"""
from __future__ import annotations

import collections.abc
import json
import pathlib
import types
from dataclasses import fields, is_dataclass

import pytest

import bellman.syntax.lower as lower
from bellman.syntax import terms as T
from bellman.syntax.lower import ToAst, unlowered_parse_nodes, to_json
from bellman.syntax.parse import build_parser
from snapshot.record import recording_path

REPO = pathlib.Path(__file__).resolve().parents[4]
APPLICATIONS = REPO / "applications"
# the stage folders of the portfolio model and of the retirement model
PORTFOLIO = APPLICATIONS / "portfolio-choice" / "declaration" / "stages"
RETIREMENT = APPLICATIONS / "retirement-choice" / "declaration" / "stages"
STAGES = ("cons", "disc", "port", "noport")
CONS_FILE = "applications/portfolio-choice/declaration/stages/cons/cons.bl"

# Names under which a position could be attached to a term; none may appear.
POSITION_NAMES = {"line", "column", "end_line", "end_column", "start_pos",
                  "end_pos", "meta", "span", "spans", "source_span", "pos"}


# --- local helpers ----------------------------------------------------------


def text_at(text: str, span) -> str:
    """The source text a span covers: `column` is the 1-based column of the
    first character and `end_column` the column just after the last one."""
    lines = text.splitlines()
    if span.line == span.end_line:
        return lines[span.line - 1][span.column - 1:span.end_column - 1]
    first = lines[span.line - 1][span.column - 1:]
    middle = lines[span.line:span.end_line - 1]
    last = lines[span.end_line - 1][:span.end_column - 1]
    return "\n".join([first, *middle, last])


def dataclass_nodes(node):
    """Every dataclass instance inside a term, depth first."""
    if is_dataclass(node):
        yield node
        for f in fields(node):
            yield from dataclass_nodes(getattr(node, f.name))
    elif isinstance(node, tuple):
        for x in node:
            yield from dataclass_nodes(x)


def assert_no_positions(term):
    """No position is stored on any term. The generated constructors are
    slotted, so the attributes a term can hold are its ASDL fields and
    nothing else; the assertion reads those slots."""
    for node in dataclass_nodes(term):
        attributes = set(type(node).__slots__)
        assert attributes == {f.name for f in fields(node)}, node
        assert not hasattr(node, "__dict__"), node
        assert not (attributes & POSITION_NAMES), node
        assert not hasattr(node, "meta"), node


def entry_value(annotation, key: str) -> str | None:
    """The value of the first `key=` entry of an Annotation, else None."""
    if annotation is None:
        return None
    for e in annotation.entries:
        if isinstance(e, T.KeyValue) and e.key == key:
            return str(e.value)
    return None


def expected_addresses(term: T.FILE) -> list:
    """The D06 address schema recomputed from the term alone. A top-level item
    is its 1-based position in the file's item list; a block with an `id=`
    header entry is that id (a nested branch block, D02, its `label=`); a
    statement or a declaration inside a block (AMD-SG-035 §5) is
    `<block address>.<id>` when its annotation carries `id=`, otherwise
    `<block address>.<n>`, n its 1-based position in the block body."""
    out = []

    def walk(items, prefix):
        for n, item in enumerate(items, 1):
            if isinstance(item, T.Block):
                head = entry_value(item.tag, "id") or (
                    entry_value(item.tag, "label") if prefix else None)
            elif prefix and isinstance(item, (T.Statement, T.Declare)):
                head = entry_value(item.annot, "id")
            else:
                head = None
            address = prefix + (head or str(n))
            out.append(address)
            if isinstance(item, T.Block):
                walk(item.body, address + ".")

    walk(term.items, "")
    return out


# --- (a) the parser has positions; the term has none ------------------------

def test_parse_tree_carries_positions_and_a_plain_lowering_keeps_none(text_of):
    cons_text = text_of("cons")
    tree = build_parser().parse(cons_text)
    first = tree.children[0]
    # cons.bl line 1 is `@stage: cons`, 12 code points from column 1.
    assert first.data == "metadata"
    assert (first.meta.line, first.meta.column, first.meta.end_line,
            first.meta.end_column) == (1, 1, 1, 13)
    term = ToAst().transform(tree)
    assert isinstance(term, T.FILE)
    assert_no_positions(term)


def test_parse_with_spans_returns_the_term_and_a_table_of_authored_items(text_of):
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    term, spans = cons
    assert isinstance(term, T.FILE)
    assert_no_positions(term)
    # cons.bl has 8 top-level items before the blocks (lines 1, 3, 4, 6, 8, 9,
    # 10 and 11), 5 blocks, and 1 + 1 + 2 + 2 + 4 statements inside the blocks;
    # the 47 components of the block headers follow them (the classification
    # table, unit T of the model interface specification 0.3)
    assert len(spans) == 8 + 5 + 10 + 47
    assert list(spans)[: 8 + 5 + 10] == [
        "1", "2", "3", "4", "5", "6", "7", "8",
        "arvl_to_dcsn", "arvl_to_dcsn.1",
        "dcsn_to_cntn", "dcsn_to_cntn.1",
        "cntn_to_dcsn", "cntn_to_dcsn.value", "cntn_to_dcsn.marginal",
        "dcsn_to_arvl", "dcsn_to_arvl.value", "dcsn_to_arvl.marginal",
        "policy", "policy.optimality", "policy.InvEuler", "policy.endoggrid",
        "policy.cons_choice",
    ]


# --- (b) exact spans in cons.bl ---------------------------------------------

def test_every_span_names_the_file(text_of):
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert {s.file for s in spans.values()} == {CONS_FILE}
    assert all(isinstance(s, lower.SourceSpan) for s in spans.values())


def test_metadata_line_span(text_of):
    # cons.bl line 1: `@stage: cons` — 12 code points, columns 1..12.
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert spans["1"] == lower.SourceSpan(
        file=CONS_FILE, line=1, column=1,
        end_line=1, end_column=13)
    assert text_at(cons_text, spans["1"]) == "@stage: cons"


def test_space_assignment_span(text_of):
    # cons.bl line 3: `Xm := ℝ₊₊` — 9 code points (ℝ, ₊, ₊ are one each).
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert spans["2"] == lower.SourceSpan(
        file=CONS_FILE, line=3, column=1,
        end_line=3, end_column=10)
    assert text_at(cons_text, spans["2"]) == "Xm := ℝ₊₊"


def test_scalar_declaration_span(text_of):
    # cons.bl line 6: `ρ : [1, inf)` — 12 code points.
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert spans["4"] == lower.SourceSpan(
        file=CONS_FILE, line=6, column=1,
        end_line=6, end_column=13)
    assert text_at(cons_text, spans["4"]) == "ρ : [1, inf)"


def test_function_definition_span_includes_its_annotation(text_of):
    # cons.bl line 8: `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]` —
    # 27 code points of definition, 9 spaces, and 12 of `:: [id=util]`: 48.
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert spans["5"] == lower.SourceSpan(
        file=CONS_FILE, line=8, column=1,
        end_line=8, end_column=49)
    assert text_at(cons_text, spans["5"]) == (
        "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]")


def test_block_span_runs_from_opening_bracket_to_closing_brace(text_of):
    # cons.bl lines 21–24: the cntn_to_dcsn block opens with `[` at column 1
    # of line 21 and closes with `}` at column 1 of line 24.
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert spans["cntn_to_dcsn"] == lower.SourceSpan(
        file=CONS_FILE, line=21, column=1,
        end_line=24, end_column=2)
    covered = text_at(cons_text, spans["cntn_to_dcsn"])
    assert covered.startswith("[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c)")
    # the block closes after its last annotated statement; the annotation mark
    # itself is no part of what the span is asserted to cover
    assert covered.endswith("[id=marginal]\n}")
    assert covered == "\n".join(cons_text.splitlines()[20:24])


def test_annotated_statement_span_inside_a_block(text_of):
    # cons.bl line 22: four spaces, then `V  = 𝑢(c) + V[>]` (16 code points),
    # 16 spaces, and `:: [id=value]` (13): the statement runs from column 5
    # to the column after code point 49, which is 50.
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert spans["cntn_to_dcsn.value"] == lower.SourceSpan(
        file=CONS_FILE, line=22, column=5,
        end_line=22, end_column=50)
    assert text_at(cons_text, spans["cntn_to_dcsn.value"]) == (
        "V  = 𝑢(c) + V[>]                :: [id=value]")


def test_unannotated_statement_is_addressed_by_its_position(text_of):
    # cons.bl line 14: four spaces, then `m_d = m` (7 code points).
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert spans["arvl_to_dcsn.1"] == lower.SourceSpan(
        file=CONS_FILE, line=14, column=5,
        end_line=14, end_column=12)
    assert text_at(cons_text, spans["arvl_to_dcsn.1"]) == "m_d = m"
    assert spans["policy"] == lower.SourceSpan(
        file=CONS_FILE, line=31, column=1,
        end_line=36, end_column=2)
    # cons.bl line 35: `c      = c[>]                    :: [id=cons_choice]`, 52 code points after the indent.
    assert spans["policy.cons_choice"] == lower.SourceSpan(
        file=CONS_FILE, line=35, column=5,
        end_line=35, end_column=57)


def test_multi_line_law_span_in_port():
    # port.bl lines 13–15 carry the joint law `(Ψ, θ) ~ LogNormal((μ_Ψ, μ_θ), …)`;
    # its closing `)))` ends line 15, which has 42 code points. The law is the
    # tenth top-level item (metadata, six scalar declarations, the feasible-set
    # definition, the joint declaration, then the law).
    text = (PORTFOLIO / "port" / "port.bl").read_text(encoding="utf-8")
    _, spans = lower.parse_with_spans(
        text, "applications/portfolio-choice/declaration/stages/port/port.bl")
    assert spans["10"] == lower.SourceSpan(
        file="applications/portfolio-choice/declaration/stages/port/port.bl", line=13, column=1,
        end_line=15, end_column=43)
    covered = text_at(text, spans["10"])
    assert covered.startswith("(Ψ, θ) ~ LogNormal((μ_Ψ, μ_θ),")
    assert covered.endswith("(ρ_ζ*σ_Ψ*σ_θ, σ_θ^2)))")
    assert covered.count("\n") == 2


def test_nested_branch_blocks_are_addressed_by_label():
    # ret_choice.bl line 10: four spaces, then
    # `[label=work,   () -> (a_w : ℝ₊) : !cntn] { a_w = a_d }` (54 code
    # points): the nested block runs from column 5 to 59 and its statement
    # `a_w = a_d` from column 48 to 57. D02 names the nested block
    # `dcsn_to_cntn.work`; its statement takes the position form under it.
    path = RETIREMENT / "ret_choice" / "ret_choice.bl"
    text = path.read_text(encoding="utf-8")
    term, spans = lower.parse_with_spans(
        text, "applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl")
    assert spans["dcsn_to_cntn"] == lower.SourceSpan(
        file="applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl",
        line=9, column=1,
        end_line=12, end_column=2)
    assert spans["dcsn_to_cntn.work"] == lower.SourceSpan(
        file="applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl",
        line=10, column=5,
        end_line=10, end_column=59)
    assert text_at(text, spans["dcsn_to_cntn.work.1"]) == "a_w = a_d"
    assert spans["dcsn_to_cntn.work.1"] == lower.SourceSpan(
        file="applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl",
        line=10, column=48,
        end_line=10, end_column=57)
    assert spans["dcsn_to_cntn.retire"].line == 11
    assert list(spans)[: len(expected_addresses(term))] == expected_addresses(term)


# --- (c) an undeclared symbol still has an addressed span -------------------

UNDECLARED = (
    "@stage: probe\n"
    "\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = V[>] + undeclared_symbol\n"
    "}\n"
)


def test_statement_with_an_undeclared_symbol_has_its_address_and_line():
    # `undeclared_symbol` has no declaration; rejecting it is graph
    # construction's task (C06). Parsing records where the statement is: line
    # 4, four spaces of indent, then 28 code points.
    term, spans = lower.parse_with_spans(UNDECLARED)
    assert "cntn_to_dcsn.1" in spans
    span = spans["cntn_to_dcsn.1"]
    assert span.file is None
    assert (span.line, span.column, span.end_line, span.end_column) == (4, 5, 4, 33)
    assert text_at(UNDECLARED, span) == "V = V[>] + undeclared_symbol"
    assert spans["cntn_to_dcsn"] == lower.SourceSpan(
        file=None, line=3, column=1,
        end_line=5, end_column=2)
    assert spans["1"] == lower.SourceSpan(file=None, line=1, column=1, end_line=1, end_column=14)
    assert list(spans) == [
        "1", "cntn_to_dcsn", "cntn_to_dcsn.1",
        # the components of the header, after the items
        "cntn_to_dcsn.in", "cntn_to_dcsn.in.V[>]", "cntn_to_dcsn.in.V[>].domain",
        "cntn_to_dcsn.in.V[>].role",
        "cntn_to_dcsn.out", "cntn_to_dcsn.out.V", "cntn_to_dcsn.out.V.domain",
        "cntn_to_dcsn.out.V.role",
    ]
    assert (spans["cntn_to_dcsn.in.V[>].domain"].column,
            spans["cntn_to_dcsn.in.V[>].domain"].end_column) == (27, 28)


DUPLICATE = (
    "@stage: probe\n"
    "\n"
    "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
    "    V = V[>]        :: [id=value]\n"
    "    V = 2 * V[>]    :: [id=value]\n"
    "}\n"
)


def test_two_items_with_one_address_are_rejected():
    # A table maps each address to one span, so two statements annotated
    # `id=value` in one block cannot both be recorded; the error names the
    # address and both lines.
    with pytest.raises(ValueError) as caught:
        lower.parse_with_spans(DUPLICATE, "probe.bl")
    message = str(caught.value)
    assert "cntn_to_dcsn.value" in message
    assert "probe.bl:4" in message and "probe.bl:5" in message


# --- (d) the encoding is unchanged --------------------------------------------

@pytest.mark.parametrize("name", STAGES)
def test_fixture_encoding_is_unchanged_by_span_collection(name):
    text = (PORTFOLIO / name / f"{name}.bl").read_text(encoding="utf-8")
    saved = recording_path(PORTFOLIO / name / f"{name}.bl", ".ast.json").read_text(encoding="utf-8")
    term, spans = lower.parse_with_spans(
        text, f"applications/portfolio-choice/declaration/stages/{name}/{name}.bl")
    assert term == ToAst().transform(build_parser().parse(text))
    assert unlowered_parse_nodes(term) == []
    assert to_json(term) == json.loads(saved)
    assert json.dumps(to_json(term), indent=2, ensure_ascii=False) + "\n" == saved
    assert_no_positions(term)
    assert len(spans) > 0


# --- (e) the table is immutable ---------------------------------------------

def test_table_is_immutable(text_of):
    cons_text = text_of("cons")
    cons = lower.parse_with_spans(cons_text, CONS_FILE)
    _, spans = cons
    assert isinstance(spans, types.MappingProxyType)
    assert isinstance(spans, collections.abc.Mapping)
    with pytest.raises(TypeError):
        spans["1"] = lower.SourceSpan(file=CONS_FILE, line=1, column=1, end_line=1, end_column=1)
    with pytest.raises(TypeError):
        del spans["1"]
    assert lower.SourceSpans is not None


# --- (f) addresses are computable from the term alone ------------------------

@pytest.mark.parametrize("path", sorted(PORTFOLIO.glob("*/*.bl")) + [
    RETIREMENT / "ret_choice" / "ret_choice.bl"], ids=lambda p: p.stem)
def test_addresses_are_computable_from_the_term_alone(path):
    term, spans = lower.parse_with_spans(path.read_text(encoding="utf-8"), str(path.relative_to(REPO)))
    addresses = expected_addresses(term)
    assert list(spans)[: len(addresses)] == addresses
    # after the items, the components of the block headers, each under a
    # side `in` or `out` of a block (unit T of the model interface
    # specification 0.3)
    assert all({"in", "out"} & set(address.split(".")) for address in list(spans)[len(addresses):])
