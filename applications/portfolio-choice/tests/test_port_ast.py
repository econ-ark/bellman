"""Hand-derived AST expectations for port.bl (spec 0.3c, S03).

Every expected node below is derived from the surface text of port.bl in
its colon-and-tilde spelling and from the generated term constructors
(bellman.sym.terms, generated from dynspec_full.asdl), not copied from the
saved port.bl.ast.json. The file is parsed fresh through the Lark route
(stage.lark, then the ToAst lowering) and each top-level item is compared
with its expectation. Runnable under pytest or directly:

    venv/bin/python applications/portfolio-choice/tests/test_port_ast.py
"""

import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "applications"))

import pytest

from stage_ast import at_var, check, dom, parsed, run_checks, sym
from bellman.syntax.terms import (
    Add, Annotation, Arrival, At, Block, Call, Closed, Continuation,
    Control, Coordinate, CorrDef, Declaration, Declare, Decision, Domain, Equation,
    In, Infoset, Interval, KeyValue, Law, Metadata, Mul, Neg, Number,
    Operator, Pow, Range, Role, Signature, Statement, Sub, Subject,
    Tag, Tuple, Typer, Value, Var,
)

EXAMPLE = pathlib.Path(__file__).resolve().parents[1] / "declaration" / "stages" / "port" / "port.bl"
ITEMS = parsed(EXAMPLE).items


def test_file_shape():
    # One metadata line, six scalar declarations, the feasible correspondence,
    # the joint shock declaration, its law, and the five standard blocks.
    kinds = [type(i).__name__ for i in ITEMS]
    assert kinds == (["Metadata"] + ["Declare"] * 6 + ["Statement", "Declare", "Statement"]
                     + ["Block"] * 5), kinds


def test_metadata_stage():
    check(ITEMS[0], Metadata("stage", "port"), "items[0]")


def test_parameter_declarations():
    # `R : ℝ₊₊` and its neighbours: the colon types the single coordinate;
    # the Domain sits on the Declaration, the coordinate carries none.
    expected = [("R", "ℝ₊₊"), ("μ_Ψ", "ℝ"), ("σ_Ψ", "ℝ₊"),
                ("μ_θ", "ℝ"), ("σ_θ", "ℝ₊")]
    for i, (stem, space) in enumerate(expected, start=1):
        want = Declare(Declaration(
            Subject([Coordinate(stem, None, [])]), [dom(space)], None))
        check(ITEMS[i], want, f"items[{i}]")


def test_interval_declaration_rho():
    # `ρ_ζ : [-1,1]`: closed ends on both sides, lower bound Neg(Number(1)).
    want = Declare(Declaration(
        Subject([Coordinate("ρ_ζ", None, [])]),
        [Domain(Interval(Range(Closed(), Neg(Number(1)), Number(1),
                               Closed())))],
        None))
    check(ITEMS[6], want, "items[6]")


def test_portfolio_feasible_set():
    # `Γ_ς(k : ℝ₊) := [0,1]`: investable assets may be nought, where the
    # borrowing constraint binds, so the argument is declared on ℝ₊.
    want = Statement(CorrDef(
        "Γ_ς",
        [Coordinate("k", None, [dom("ℝ₊")])],
        Interval(Range(Closed(), Number(0), Number(1), Closed()))),
        None)
    check(ITEMS[7], want, "items[7]")


def test_joint_shock_declaration():
    # `(Ψ : ℝ₊₊, θ : ℝ₊₊)`: each coordinate carries its own Domain and the
    # Declaration itself carries no classifier. No shock word is written;
    # the law on the following line is what makes the pair a shock.
    want = Declare(Declaration(
        Subject([Coordinate("Ψ", None, [dom("ℝ₊₊")]),
                 Coordinate("θ", None, [dom("ℝ₊₊")])]),
        [], None))
    check(ITEMS[8], want, "items[8]")


def test_joint_law():
    # `(Ψ, θ) ~ LogNormal((μ_Ψ, μ_θ),
    #                     ((σ_Ψ^2, ρ_ζ*σ_Ψ*σ_θ), (ρ_ζ*σ_Ψ*σ_θ, σ_θ^2)))`,
    # spanning three lines inside the parentheses. The risky return and the
    # transitory income are lognormal, both declared on ℝ₊₊. The law is a
    # Statement whose core is Law(subjects, law) with no annotation; the
    # tuple subject lowers to the list of stems; LogNormal is an ordinary
    # Call with two Tuple arguments; ρ_ζ*σ_Ψ*σ_θ associates to the left;
    # σ^2 is Pow with exponent Number(2).
    off_diag = Mul(Mul(sym("ρ_ζ"), sym("σ_Ψ")), sym("σ_θ"))
    mean = Tuple([sym("μ_Ψ"), sym("μ_θ")])
    cov = Tuple([
        Tuple([Pow(sym("σ_Ψ"), Number(2)), off_diag]),
        Tuple([off_diag, Pow(sym("σ_θ"), Number(2))]),
    ])
    want = Statement(Law(["Ψ", "θ"], Call("LogNormal", [mean, cov])), None)
    check(ITEMS[9], want, "items[9]")


def test_block_arvl_to_dcsn():
    # `(k : ℝ₊) : !arvl -> (k_d : ℝ₊) : !dcsn`: each side's word-type is the
    # side's Infoset; the coordinate carries its Domain. Investable assets
    # may be nought, where the borrowing constraint binds.
    want = Block(
        Annotation([
            KeyValue("id", "arvl_to_dcsn"),
            Typer(Signature(
                Subject([Coordinate("k", None, [dom("ℝ₊")])]),
                [Infoset(Arrival())],
                Subject([Coordinate("k_d", None, [dom("ℝ₊")])]),
                [Infoset(Decision())])),
        ]),
        [Statement(Equation(sym("k_d"), sym("k")), None)])
    check(ITEMS[10], want, "items[10]")


def test_block_dcsn_to_cntn_signature():
    # `ς : !ctrl @ [0,1]`: the control role and the closed interval domain
    # attach to the binding coordinate in the order written (word first).
    want = Annotation([
        KeyValue("id", "dcsn_to_cntn"),
        Typer(Signature(
            Subject([
                Coordinate("k_d", None, []),
                Coordinate("ς", None, [
                    Role(Control()),
                    Domain(Interval(Range(Closed(), Number(0), Number(1),
                                          Closed()))),
                ]),
                Coordinate("Ψ", None, []),
                Coordinate("θ", None, []),
            ]),
            [Infoset(Decision())],
            Subject([Coordinate("m_next", None, [dom("ℝ₊₊")])]),
            [Infoset(Continuation())])),
    ])
    check(ITEMS[11].tag, want, "items[11].tag")


def test_block_dcsn_to_cntn_budget():
    # m_next = k_d*(ς*Ψ + (1-ς)*R) + θ: the outer sum adds θ last; the
    # parenthesised sum stays inside the multiplication by k_d.
    rhs = Add(
        Mul(sym("k_d"),
            Add(Mul(sym("ς"), sym("Ψ")),
                Mul(Sub(Number(1), sym("ς")), sym("R")))),
        sym("θ"))
    want = [Statement(Equation(sym("m_next"), rhs), None)]
    check(ITEMS[11].body, want, "items[11].body")


def test_block_cntn_to_dcsn():
    # `V[>] : ℝ @ !vlu` is a Continuation-indexed coordinate with Domain ℝ
    # and the value role of order 0, in the order written, and the share ς
    # is listed with no classifier. The block writes the value and states its
    # derivative in investable assets, `D_{k_d}V`, an operator term on the
    # left side. E_{Ψ,θ}(V[>]) lowers to Operator("E", two Var subscripts,
    # one argument); the derivative line multiplies the derivative of the
    # continuation value in m_next, `D_{m_next}V[>]`, by the gross return on
    # the portfolio. The statement annotations `:: [id=value]` and
    # `:: [id=marginal]` become the Statements' annots.
    ev = Operator("E", [Var("Ψ"), Var("θ")], [at_var("V", Continuation)])
    gross = Add(Mul(sym("ς"), sym("Ψ")),
                Mul(Sub(Number(1), sym("ς")), sym("R")))
    derivative = Operator("D", [Var("m_next")], [at_var("V", Continuation)])
    e_marginal = Operator("E", [Var("Ψ"), Var("θ")], [Mul(derivative, gross)])
    want = Block(
        Annotation([
            KeyValue("id", "cntn_to_dcsn"),
            Typer(Signature(
                Subject([Coordinate("V", At(Continuation()),
                                    [dom("ℝ"), Role(Value(0))]),
                         Coordinate("ς", None, [])]),
                [Infoset(Continuation())],
                Subject([Coordinate("V", None, [dom("ℝ"), Role(Value(0))])]),
                [Infoset(Decision())])),
        ]),
        [Statement(Equation(sym("V"), ev),
                   Annotation([KeyValue("id", "value")])),
         Statement(Equation(Operator("D", [Var("k_d")], [sym("V")]), e_marginal),
                   Annotation([KeyValue("id", "marginal")]))])
    check(ITEMS[12], want, "items[12]")


def test_block_dcsn_to_arvl():
    # The source side is the parenthesised form `(V) : !dcsn`, which puts
    # Infoset(Decision()) on the side and leaves the coordinate without a
    # classifier. The bare single-coordinate form `V : !dcsn ->` (admitted
    # 30 Aug 2026) attaches the word-type to the coordinate instead and
    # leaves the side's own type list empty; the two forms mean the same
    # thing but encode differently, a difference recorded as an open item in
    # the road-map brief funcdef-law-statement-annotations.md, which this
    # file no longer exercises. The law `k_d = k` is the identity, so the
    # block writes no derivative line.
    want = Block(
        Annotation([
            KeyValue("id", "dcsn_to_arvl"),
            Typer(Signature(
                Subject([Coordinate("V", None, [])]),
                [Infoset(Decision())],
                Subject([Coordinate("V", At(Arrival()),
                                    [dom("ℝ"), Role(Value(0))])]),
                [Infoset(Arrival())])),
        ]),
        [Statement(Equation(at_var("V", Arrival), sym("V")),
                   Annotation([KeyValue("id", "value")]))])
    check(ITEMS[13], want, "items[13]")


def test_block_policy_signature():
    # The header lists the value function the block reads and no state
    # (AAS, 18 September 2026: a state a policy line mentions is a
    # coordinate of the block, not an input), and the input side carries the
    # group tag `: !cntn`, so its type list holds Infoset(Continuation())
    # while the output side is typed with no perch word and its type list is
    # empty.
    want = Annotation([
        KeyValue("id", "policy"),
        Typer(Signature(
            Subject([
                Coordinate("V", At(Continuation()), []),
            ]),
            [Infoset(Continuation())],
            Subject([Coordinate("ς", None, [])]),
            [])),
    ])
    check(ITEMS[14].tag, want, "items[14].tag")


def test_block_policy_objective():
    # argmax_{ς : Γ_ς(k_d)}(E_{Ψ,θ}(V[>])): the binder carries the feasible
    # correspondence and the expectation is the objective.
    ev = Operator("E", [Var("Ψ"), Var("θ")], [at_var("V", Continuation)])
    want = Statement(
        Equation(sym("ς"), Operator("argmax", [
            In("ς", Call("Γ_ς", [sym("k_d")]))
        ], [ev])),
        Annotation([KeyValue("id", "objective"), Tag("!doc")]))
    check(ITEMS[14].body[0], want, "items[14].body[0]")


def test_block_policy_foc():
    # The first-order condition defines ς as a solve occurrence: the binder
    # ς is the unknown and the expectation is the residual (Appendix C R10),
    # which reads the derivative of the continuation value in m_next.
    want = Statement(
        Equation(sym("ς"),
                 Operator("solve", [Var("ς")],
                          [Operator("E", [Var("Ψ"), Var("θ")],
                                    [Mul(Operator("D", [Var("m_next")],
                                                  [at_var("V", Continuation)]),
                                         Sub(sym("Ψ"), sym("R")))])])),
        Annotation([KeyValue("id", "foc")]))
    check(ITEMS[14].body[1], want, "items[14].body[1]")


if __name__ == "__main__":
    sys.exit(run_checks(globals(), f"on {EXAMPLE.name}"))
