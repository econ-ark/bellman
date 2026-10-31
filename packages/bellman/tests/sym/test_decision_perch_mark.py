"""The optional decision-perch mark `[~]`.

A field at the decision perch is written bare in a stage file; `[<]` and
`[>]` mark the arrival and continuation perches. `x[~]` writes the
decision perch explicitly (the tilde is the ASCII form of the subscript ∼
of the mathematics) and lowers to the same term as the bare name, so the
JSON encoding of a file does not depend on whether the mark is written
(AAS, 6 September 2026). The mark is accepted wherever the grammar admits
a bare name in field position: expressions, signature coordinates,
declaration and law subjects; a mark after a selector is rejected as for
`[<]` and `[>]`. The perch of a bare name is that of the signature side
listing it, and the lowering does not check that a marked name is in fact
at the decision perch (a[~] on a `: !cntn` side is read as that side's
field).
"""

import pathlib

import pytest

from bellman.syntax import terms as T
from bellman.syntax.lower import parse_with_spans

BARE = """@stage: t

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

MARKED = """@stage: t

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

LAW_BARE = "@stage: t\n\ny : ℝ\ny ~ N(0, 1)\n(y, z) ~ N(0, 1)\n"
LAW_MARKED = "@stage: t\n\ny[~] : ℝ\ny[~] ~ N(0, 1)\n(y[~], z) ~ N(0, 1)\n"

APPLICATIONS = pathlib.Path(__file__).resolve().parents[4].joinpath("applications")
CORPUS = sorted(APPLICATIONS.glob("*/declaration/stages/*/*.bl"))


def test_marked_and_bare_decision_fields_lower_to_one_term():
    assert parse_with_spans(MARKED).term == parse_with_spans(BARE).term


def test_marked_and_bare_law_subjects_lower_to_one_term():
    assert parse_with_spans(LAW_MARKED).term == parse_with_spans(LAW_BARE).term


def test_decision_mark_in_expression_is_the_bare_constant():
    term, _ = parse_with_spans("@stage: t\n\n[id=b, (v) : !cntn -> (w) : !dcsn] {\n    w[~] = v\n}\n")
    block = [it for it in term.items if isinstance(it, T.Block)][0]
    lhs = block.body[0].core.lhs
    assert lhs == T.Sym(T.Constant("w"))
    assert not isinstance(lhs.symbol, T.Variable)


def _assert_no_decision_index(term):
    from dataclasses import fields, is_dataclass

    def walk(node):
        if is_dataclass(node):
            if isinstance(node, T.At):
                assert not isinstance(node.side, T.Decision)
            for f in fields(node):
                walk(getattr(node, f.name))
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(term)


def test_no_term_carries_an_explicit_decision_perch():
    """`At(Decision())` never appears in a term: a Variable is at the arrival or
    the continuation perch, and the decision perch is the bare Constant. The
    property holds because `bracketed_name` is the only construction site of `At` and
    builds it with Arrival or Continuation only; the ASDL admits the
    constructor."""
    _assert_no_decision_index(parse_with_spans(MARKED).term)
    _assert_no_decision_index(parse_with_spans(LAW_MARKED).term)


def test_no_corpus_term_carries_an_explicit_decision_perch():
    for src in CORPUS:
        try:
            term, _ = parse_with_spans(src.read_text(encoding="utf-8"), str(src))
        except Exception:
            continue                  # a file that does not parse is recorded in test_corpus.py
        _assert_no_decision_index(term)


def test_arrival_and_continuation_marks_are_unchanged():
    term, _ = parse_with_spans(MARKED)
    block = [it for it in term.items if isinstance(it, T.Block)][1]
    lhs = block.body[0].core.lhs
    assert lhs == T.Sym(T.Variable("V", T.At(T.Arrival()), 0))
    policy = [it for it in term.items if isinstance(it, T.Block)][0]
    rhs = policy.body[1].core.rhs
    assert rhs == T.Sym(T.Variable("c", T.At(T.Continuation()), 0))


def test_decision_mark_before_a_key_selector_is_the_bare_selection():
    marked, _ = parse_with_spans("@stage: t\n\n[id=b, (v) : !cntn -> (w) : !dcsn] {\n    w = v[~][keep]\n}\n")
    bare, _ = parse_with_spans("@stage: t\n\n[id=b, (v) : !cntn -> (w) : !dcsn] {\n    w = v[keep]\n}\n")
    assert marked == bare


def test_decision_mark_after_a_selector_is_rejected_like_the_other_marks():
    # a refusal raised inside the lowering leaves `parse_with_spans` as the
    # lowering wrote it, and not inside the wrapper whose sentence names a
    # rule of Lark (AMD-SG-022 §2). An intentional syntax refusal retains its
    # token position and remedy for the public loader.
    for mark in ("~", ">"):
        with pytest.raises(ValueError) as caught:
            parse_with_spans("@stage: t\n\n[id=b, (v) : !cntn -> (w) : !dcsn] {\n"
                             f"    w = v[keep][{mark}]\n}}\n")
        assert (caught.value.line, caught.value.column) == (4, 17)
        assert f"perch mark `{mark}` follows the first selector" in str(caught.value)
        assert caught.value.advice == f"write one perch mark first, as `v[{mark}][keep]`"
        assert "Error trying to process rule" not in str(caught.value)


def test_spans_of_a_marked_statement_start_at_its_name():
    _, spans = parse_with_spans(MARKED, "marked.bl")
    span = spans["policy.cons_choice"]
    assert (span.line, span.column) == (8, 5)
    assert MARKED.splitlines()[span.line - 1][span.column - 1:].startswith("c[~] = c[>]")
