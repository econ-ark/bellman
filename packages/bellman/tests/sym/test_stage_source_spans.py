"""Public source positions, item addresses and read-only span tables.

The complete corpus guard checks parsed terms and their JSON encodings.
These checks retain the numeric ranges needed by editors and refusals.
"""
from __future__ import annotations

import collections.abc
import pytest

import bellman.syntax.lower as lower
from bellman.syntax import terms as T
from conftest import ROOT, STAGE_FILES

PORTFOLIO = ROOT / "applications/portfolio-choice/declaration/stages"
RETIREMENT = ROOT / "applications/retirement-choice/declaration/stages"
CONS_FILE = "applications/portfolio-choice/declaration/stages/cons/cons.bl"

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


def test_authored_items_keep_exact_source_positions(parsed_source):
    """Metadata, declarations, equations, laws and nested blocks retain their text."""
    sources = {
        "cons": (ROOT / CONS_FILE, {
            "1": ((1, 1, 1, 13), "@stage: cons"),
            "2": ((3, 1, 3, 10), "Xm := ℝ₊₊"),
            "4": ((6, 1, 6, 13), "ρ : [1, inf)"),
            "5": ((8, 1, 8, 49), "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]"),
            "cntn_to_dcsn": ((20, 1, 23, 2), None),
            "cntn_to_dcsn.value": ((21, 5, 21, 50), "V        = 𝑢(c) + V[>]          :: [id=value]"),
            "arvl_to_dcsn.1": ((13, 5, 13, 12), "m_d = m"),
            "policy": ((29, 1, 31, 2), None),
        }),
        "port": (PORTFOLIO / "port/port.bl", {
            "10": ((13, 1, 15, 43), None),
        }),
        "ret_choice": (RETIREMENT / "ret_choice/ret_choice.bl", {
            "dcsn_to_cntn": ((9, 1, 12, 2), None),
            "dcsn_to_cntn.work": ((10, 5, 10, 59), None),
            "dcsn_to_cntn.work.1": ((10, 48, 10, 57), "a_w = a_d"),
        }),
    }
    for name, (path, expected) in sources.items():
        text = path.read_text(encoding="utf-8")
        term, spans = parsed_source(path)
        assert {span.file for span in spans.values()} == {path.relative_to(ROOT).as_posix()}, name
        for address, (position, excerpt) in expected.items():
            span = spans[address]
            assert (span.line, span.column, span.end_line, span.end_column) == position, (name, address)
            if excerpt is not None:
                assert text_at(text, span) == excerpt, (name, address)
        if name == "cons":
            covered = text_at(text, spans["cntn_to_dcsn"])
            assert covered.startswith("[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c)")
            assert covered.endswith("[id=marginal]\n}")
            assert covered == "\n".join(text.splitlines()[19:23])
            assert len(spans) == 7 + 5 + 6 + 39
            assert list(spans)[:18] == [
                "1", "2", "3", "4", "5", "6", "7", "arvl_to_dcsn", "arvl_to_dcsn.1",
                "dcsn_to_cntn", "dcsn_to_cntn.1", "cntn_to_dcsn", "cntn_to_dcsn.value",
                "cntn_to_dcsn.marginal", "dcsn_to_arvl", "dcsn_to_arvl.value", "policy", "policy.optimality",
            ]
        elif name == "port":
            covered = text_at(text, spans["10"])
            assert covered.startswith("(Ψ, θ) ~ LogNormal((μ_Ψ, μ_θ),")
            assert covered.endswith("(ρ_ζ*σ_Ψ*σ_θ, σ_θ^2)))")
            assert covered.count("\n") == 2
        else:
            assert spans["dcsn_to_cntn.retire"].line == 11


def test_addresses_follow_authored_identifiers_and_item_positions(parsed_source):
    """All original portfolio sources and the nested retirement stage retain their addresses."""
    paths = [*(path for path in STAGE_FILES if path.parent.parent == PORTFOLIO),
             RETIREMENT / "ret_choice/ret_choice.bl"]
    for path in paths:
        term, spans = parsed_source(path)
        addresses = expected_addresses(term)
        assert list(spans)[:len(addresses)] == addresses, path.name
        assert all({"in", "out"} & set(address.split("."))
                   for address in list(spans)[len(addresses):]), path.name


def test_source_positions_are_read_only(parsed_source):
    _, spans = parsed_source(ROOT / CONS_FILE)
    assert isinstance(spans, collections.abc.Mapping)
    with pytest.raises(TypeError):
        spans["1"] = spans["2"]
    with pytest.raises(TypeError):
        del spans["1"]


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
