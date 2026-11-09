#!/usr/bin/env python3
"""Structural verification of the AST for benhabib_bellman.bl (spec 0.3c, B01).

Each expectation below is derived by hand from the surface text of the
stage file in its colon-and-tilde spelling, and of the methods file beside
it, `declaration/stages/benhabib_bellman/methods.bl`, an addition to the
stage file whose block `policy` holds the lines of the endogenous grid
method and whose block `cntn_to_dcsn` holds the derivative line, read
against the merged ASDL
listing (packages/bellman/bellman/sym/grammars/dynspec_full.asdl) and the
generated term constructors (bellman.sym.terms), not copied from its recording
packages/bellman/tests/snapshot/corpus/benhabib-2019/benhabib_bellman.bl.ast.json.
The file is parsed fresh through the Lark route (stage.lark, then the ToAst
lowering) and each top-level item is compared with its expectation.

Distinctive constructs of this file, all asserted below: the two type sets
are finite sets with named members (`Tau := {q1, …, q10}`, the earnings
deciles; `R_type := {r1, …, r5}`, the return types), lowered to
Space(FiniteSet(members)); the two parameter families are declared with
product sets of a fixed count (`wage_fn : ℝ₊ × … × ℝ₊`, ten factors;
`R_vec : ℝ₊₊ × … × ℝ₊₊`, five), lowered to Domain(Product(factors)); the
instance's types are parameters over those sets (`tau : Tau`,
`r_type : R_type`), bare declarations with no law, since the source model
fixes both types within a life (9 Sep 2026, after the ruling that a family
indexed by a model-content count is written with literal members); the
family selections `wage_fn[tau]` and `R_vec[r_type]` become
Select(Sym(Constant(family)), Key(index)); the policy block's input side
carries the perch word `: !cntn` and its output is `(c : !ctrl) : !dcsn`
(the B01 alignment of 8 Sep 2026); the policy block states the
maximization alone; and the block `policy` of the methods file types the
builder with `!egm`, its grid and its handler and closes with the
endogenous-grid reading `c = c[>]` of the portfolio corpus.

Deliberate conventions asserted here, not incidental output: a bare
declaration line becomes Declare(Declaration(...)); `!vlu` becomes
Role(Value(0)); `!ctrl` becomes Role(Control());
a side's word-type `: !dcsn` becomes that side's Infoset; V[<] / V[>] in
expression position become Sym(Variable(name, At(perch), 0)); the
derivative term `D_{a}V[>]` becomes Operator("D", [Var("a")], [V[>]]); a
coordinate's classifiers keep the order written (`c : !ctrl @ ℝ₊` is role
then domain, `V[>] : ℝ @ !vlu` is domain then role);
":: [id=x, !node]" becomes Annotation entries with !node as
Typer(Marked(Node())); assigning a set expression wraps the value in
Space(...).

Runnable under pytest or directly with the repository interpreter:

    venv/bin/python applications/benhabib-2019/tests/test_benhabib_bellman_ast.py
"""

import pathlib
import sys

_TESTS = pathlib.Path(__file__).resolve().parent
_TOOLS = _TESTS.parents[2] / "packages" / "bellman" / "tests" / "tools"
sys.path.insert(0, str(_TOOLS))

import pytest                         # noqa: E402

import stage_ast                      # noqa: E402
from stage_ast import annotation as _ann, block, parsed, perched as _p, run_checks, sym as _c  # noqa: E402
from stage_types import (             # noqa: E402
    Add, Assignment, At, Cartesian, Constant, Continuation,
    Control, Coordinate, Declaration, Declare, Decision, Div, Domain,
    Equation, FiniteSet, Grid, Handler, Infoset, Interval, Key, KeyValue,
    Law, Marked, Metadata, Method, Mul, Name, Named, Neg, Node, Number,
    Open, Operator, Path, Pow, Product, Range, Role, Segment, Select,
    Signature, Space, Spaced, Statement, Sub, Subject, Sym, Typer, Value,
    Var, Word,
)

_SOURCE = _TESTS.parent / "declaration" / "stages" / "benhabib_bellman" / "benhabib_bellman.bl"
_AST = parsed(_SOURCE)
_ITEMS = _AST.items
# the methods file beside the stage file, an addition to it: its block `policy`
# holds the lines of the endogenous grid method and its block `cntn_to_dcsn`
# the derivative line of the decision value
_ADDITION = parsed(_SOURCE.parent / "methods.bl").items
_MARGINAL = block(_ADDITION, "cntn_to_dcsn")
_EGM = block(_ADDITION, "policy")


def _sel(family, index):
    """The family selection family[index]: selection by name key."""
    return Select(Sym(Constant(family)), Key(index))


# R_vec[r_type], the gross return of the instance's return type, appears
# in three equations.
_GROSS_R = _sel("R_vec", "r_type")

_DECILES = ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"]
_RETURN_TYPES = ["r1", "r2", "r3", "r4", "r5"]


def test_item_census():
    # One metadata line, three space assignments, eight parameter
    # declarations (β, σ, μ, A, wage_fn, R_vec, tau, r_type), the feasible
    # set of consumption `Γ_c(x : Xa) := [0, x]`, then three blocks
    # (dcsn_to_cntn, cntn_to_dcsn, policy): the stage has no arrival perch,
    # its decision perch being the perch at which it is entered (decision
    # MB-V25). No law statement: the types are fixed within a life.
    assert len(_ITEMS) == 16
    kinds = [type(it).__name__ for it in _ITEMS]
    assert kinds == (["Metadata"] + ["Statement"] * 3 + ["Declare"] * 8
                     + ["Statement"] + ["Block"] * 3)
    assert stage_ast.unlowered_parse_nodes(_AST) == []


def test_metadata_line():
    # @stage: bellman
    assert _ITEMS[0] == Metadata("stage", "bellman")


def test_space_assignments():
    # Xa := ℝ₊ — a reserved set glyph, wrapped in Space(Named).
    assert _ITEMS[1] == Statement(
        Assignment(Constant("Xa"), Space(Named("ℝ₊"))), None)
    # Tau := {q1, …, q10} and R_type := {r1, …, r5} — finite sets with
    # named members (a finite set's members are names, so the paper's
    # integer labels are spelled q1…q10 and r1…r5), wrapped in
    # Space(FiniteSet).
    assert _ITEMS[2] == Statement(
        Assignment(Constant("Tau"), Space(FiniteSet(_DECILES))), None)
    assert _ITEMS[3] == Statement(
        Assignment(Constant("R_type"), Space(FiniteSet(_RETURN_TYPES))),
        None)


def test_declare_beta_open_interval():
    # `β : (0,1)` — an open interval on both ends; the Domain sits on the
    # Declaration, the coordinate carries none.
    assert _ITEMS[4] == Declare(Declaration(
        Subject([Coordinate("β", None, [])]),
        [Domain(Interval(Range(Open(), Number(0), Number(1), Open())))],
        None))


def test_declares_with_domains():
    # σ, μ, A on ℝ₊; the two families on product sets of a fixed count
    # (ten ℝ₊ factors for the decile wage schedule, five ℝ₊₊ factors for
    # the gross returns), so that the source fixes the count the
    # selections are checked against; the instance's types on their
    # finite sets.
    expected = [
        ("σ", Named("ℝ₊")), ("μ", Named("ℝ₊")), ("A", Named("ℝ₊")),
        ("wage_fn", Product([Named("ℝ₊")] * 10)),
        ("R_vec", Product([Named("ℝ₊₊")] * 5)),
        ("tau", Named("Tau")), ("r_type", Named("R_type")),
    ]
    for offset, (stem, space) in enumerate(expected):
        assert _ITEMS[5 + offset] == Declare(Declaration(
            Subject([Coordinate(stem, None, [])]),
            [Domain(space)],
            None)), stem


def test_types_carry_no_law():
    # tau and r_type are parameters of the instance, not shocks: no
    # statement of the file has a Law core, and the two declarations
    # carry no value or condition tail.
    assert not any(isinstance(it, Statement) and isinstance(it.core, Law)
                   for it in _ITEMS)
    assert _ITEMS[10].declaration.value is None and _ITEMS[11].declaration.value is None


def test_block_dcsn_to_cntn_header():
    # [id=dcsn_to_cntn, (m : Xa, c : !ctrl @ ℝ₊) : !dcsn -> (a : Xa) : !cntn]
    # — the decision state is typed here, the first header that lists it;
    # the classifiers on c keep their written order, role then domain; the
    # return type is a parameter and so is not a coordinate.
    assert _ITEMS[13].tag == _ann(
        KeyValue("id", "dcsn_to_cntn"),
        Typer(Signature(
            Subject([Coordinate("m", None, [Domain(Named("Xa"))]),
                     Coordinate("c", None, [Role(Control()),
                                            Domain(Named("ℝ₊"))])]),
            [Infoset(Decision())],
            Subject([Coordinate("a", None, [Domain(Named("Xa"))])]),
            [Infoset(Continuation())])))


def test_block_dcsn_to_cntn_body():
    # a = R_vec[r_type] * (m - c) + wage_fn[tau] — the return is applied to
    # the saving and the earnings of the instance's decile are added after
    # it; the product binds before the sum, and the wage schedule selected
    # at the decile is a selection by name key, not a call.
    assert list(_ITEMS[13].body) == [Statement(
        Equation(_c("a"), Add(Mul(_GROSS_R, Sub(_c("m"), _c("c"))),
                              _sel("wage_fn", "tau"))),
        _ann(KeyValue("id", "savings")))]


def test_block_cntn_to_dcsn_header():
    # [id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn
    #        -> (V : ℝ @ !vlu) : !dcsn]
    # The perch mark on V's binding occurrence sits in the coordinate's
    # index slot; !vlu is Role(Value(0)), after its Domain as written.
    assert _ITEMS[14].tag == _ann(
        KeyValue("id", "cntn_to_dcsn"),
        Typer(Signature(
            Subject([Coordinate("V", At(Continuation()),
                                [Domain(Named("ℝ")), Role(Value(0))]),
                     Coordinate("c", None, [])]),
            [Infoset(Continuation())],
            Subject([Coordinate("V", None,
                                [Domain(Named("ℝ")), Role(Value(0))])]),
            [Infoset(Decision())])))


def test_block_cntn_to_dcsn_value_equation():
    # V = c^(1-σ)/(1-σ) + β*V[>] — the power binds before the division,
    # the division before the sum, and V[>] is a continuation-perch
    # occurrence of V. No expectation: the stage has no shock.
    one_minus_sigma = Sub(Number(1), _c("σ"))
    assert _ITEMS[14].body[0] == Statement(
        Equation(_c("V"),
                 Add(Div(Pow(_c("c"), one_minus_sigma), one_minus_sigma),
                     Mul(_c("β"), _p("V", Continuation())))),
        _ann(KeyValue("id", "value")))
    assert len(_ITEMS[14].body) == 1


def test_block_cntn_to_dcsn_marginal_equation():
    # D_{m}V = c^(-σ) — the derivative of the decision value in its state
    # m, an operator term on the left side; the parenthesised exponent is
    # Neg(σ). The line stands in the block `cntn_to_dcsn` of the methods
    # file.
    assert _MARGINAL.body[0] == Statement(
        Equation(Operator("D", [Var("m")], [_c("V")]), Pow(_c("c"), Neg(_c("σ")))),
        _ann(KeyValue("id", "marginal")))


def test_block_policy_header():
    # [id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : !ctrl) : !dcsn]
    # — the B01 alignment (8 Sep 2026) and the removal of the state from
    # the input side (AAS, 18 Sep 2026: a state the policy lines mention is
    # a coordinate of the block, not an input, so the header lists the
    # value function the block reads and no state): the input side carries
    # the continuation perch word, and the
    # output carries the decision perch word and the control role with no
    # set written; V[>] is the value role Value(0), after its Domain. The
    # return type, a parameter, is not a coordinate.
    assert _ITEMS[15].tag == _ann(
        KeyValue("id", "policy"),
        Typer(Signature(
            Subject([Coordinate("V", At(Continuation()),
                                [Domain(Named("ℝ")), Role(Value(0))])]),
            [Infoset(Continuation())],
            Subject([Coordinate("c", None, [Role(Control())])]),
            [Infoset(Decision())])))


def test_block_policy_inveuler():
    # c[>] = (β * R_vec[r_type] * D_{a}V[>])^(-1/σ) :: [id=InvEuler, !node]
    # Multiplication associates left, so the base is
    # Mul(Mul(β, R_vec[r_type]), D_{a}V[>]), the derivative of the
    # continuation value in the saving a; unary minus in the grammar takes
    # a whole product, so the exponent is Neg(Div(1, σ)); the !node tag
    # becomes Typer(Marked(Node())). The line stands first in the block
    # `policy` of the methods file.
    assert _EGM.body[0] == Statement(
        Equation(_p("c", Continuation()),
                 Pow(Mul(Mul(_c("β"), _GROSS_R),
                         Operator("D", [Var("a")], [_p("V", Continuation())])),
                     Neg(Div(Number(1), _c("σ"))))),
        _ann(KeyValue("id", "InvEuler"), Typer(Marked(Node()))))


def test_block_policy_inverse_transition():
    # m[>] = c[>] + (a - wage_fn[tau]) / R_vec[r_type]
    #        :: [id=inv_g_dcsn_to_cntn, !node] — the endogenous wealth grid,
    # the inverse of the transition g of dcsn_to_cntn in its state
    # coordinate (id renamed by AAS, 9 September 2026); the earnings are
    # taken off before the return is divided out, since g adds them after
    # it, and the division binds before the sum. The saving `a` is the
    # bound coordinate of the line, not a listed input of the block.
    assert _EGM.body[1] == Statement(
        Equation(_p("m", Continuation()),
                 Add(_p("c", Continuation()),
                     Div(Sub(_c("a"), _sel("wage_fn", "tau")), _GROSS_R))),
        _ann(KeyValue("id", "inv_g_dcsn_to_cntn"), Typer(Marked(Node()))))


def test_block_policy_consumption():
    # c = c[>] :: [id=cons_choice] — the decision-perch consumption is
    # the consumed function read on the endogenous grid, the spelling of
    # the portfolio corpus (cons.bl); no evaluate call appears. It closes
    # the block `policy` of the methods file, third of its three lines; the
    # stage file's policy block holds the maximization alone.
    assert _EGM.body[2] == Statement(
        Equation(_c("c"), _p("c", Continuation())),
        _ann(KeyValue("id", "cons_choice")))
    assert len(_EGM.body) == 3 and len(_ITEMS[15].body) == 1


def test_addition_item_census():
    # The methods file: its metadata line `@methods: bellman`, the three
    # settings the grid reads, declared with their sets, and two blocks, the
    # policy block and the decision value block, each named by the id of the
    # stage block it adds to.
    kinds = [type(it).__name__ for it in _ADDITION]
    assert kinds == ["Metadata"] + ["Declare"] * 3 + ["Block"] * 2
    assert _ADDITION[0] == Metadata("methods", "bellman")
    assert [it.declaration.subject.coordinates[0].stem for it in _ADDITION[1:4]] == [
        "n_a", "a_min", "a_max"]
    assert [it.declaration.classifiers for it in _ADDITION[1:4]] == [
        (Domain(Named("ℕ")),), (Domain(Named("Xa")),), (Domain(Named("Xa")),)]


def test_addition_policy_header():
    # [id=policy, method : !egm | handler : "dolo:egm_backward"
    #     | grid : !Cartesian(a=(a_min, a_max, n_a))]
    # The bracket holds three typing entries, each a Typer: the block's own
    # method component by the relative path `method`, the handler binding as
    # a quoted program, and the grid component, a Cartesian grid with one
    # factor on the continuation state a, its bounds and its count the
    # declared settings by name. The block carries no signature, since it
    # adds no coordinate, and the decision value block carries its id alone.
    assert _EGM.tag == _ann(
        KeyValue("id", "policy"),
        Typer(Declaration(Path([Segment("method")]), [Method(Word("egm"))])),
        Typer(Handler(Path([Segment("handler")]), "dolo:egm_backward")),
        Typer(Declaration(Path([Segment("grid")]), [Grid(Cartesian([
            Spaced("a", Name("a_min"), Name("a_max"), Name("n_a"))]))])))
    assert _MARGINAL.tag == _ann(KeyValue("id", "cntn_to_dcsn"))


if __name__ == "__main__":
    sys.exit(run_checks(globals(), f"for {_SOURCE.name}"))
