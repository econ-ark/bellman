"""Structural verification of the AST for consumption_choice.bl (spec 0.3c, B01).

The stage file is the Bellman-SYM translation of
applications/pre-dynspec/housing-owner/registry/stages/consumption_choice.yaml
(the owner consumption-choice stage: continuous consumption chosen by
the endogenous grid method, no shock in this stage). Each expectation
below is derived by hand from the surface text of the stage file in its
colon-and-tilde spelling, read against the merged ASDL listing
(packages/bellman/bellman/sym/grammars/dynspec_full.asdl) and the
generated term constructors (bellman.sym.terms). The test parses the
example fresh through the Lark route (stage.lark, then the ToAst
lowering) and compares item by item against hand-built constructor
trees; it does not read the stored .ast.json.

Deliberate conventions asserted here, not incidental output: a bare
declaration line becomes Declare(Declaration(...)), and a declaration's
`::["…"]` description is kept on the Declare item's annotation slot
(AMD-SG-014 §3); `!vlu` becomes
Role(Value(0)); `!ctrl` becomes
Role(Control()); a side's word-type `: !arvl` becomes that side's
Infoset; V[<] / V[>] in expression position become
Sym(Variable(name, At(perch), 0)); the derivative term `D_{x}V` becomes
Operator("D", [Var("x")], [V]); ":: [id=x, !node]" becomes Annotation
entries with !node as Typer(Marked(Node())); assigning a reserved set
glyph wraps the value in Space(Named(...)), while the grid-defining
assignment XH := linspace(H_min, H_max, n_H) stays a bare Call (a
formula, not a set expression, so no Space wrapper).

Two assertions record translation-level facts about this stage: the
source YAML declares an empty exogenous block (income is realized in
the companion housing_choice stage), and accordingly the abstract
tree contains no Shock role and no expectation operator; the Operator
nodes are the argmax of the declarative optimality statement and the
two derivative terms, and the only calls are linspace and the feasible
correspondence Γ.

The derivative line of the decision value builder, and the inverse Euler,
endogenous grid and identification lines of the policy builder, stand in the
methods file beside the stage file,
`declaration/stages/consumption_choice/methods.bl`, an addition to it whose
blocks name the two builders by their ids; the file is parsed and compared
here as the stage file is.

The policy block of this file (revised 9 Sep 2026 on AAS's answer that
the decision states do not belong in the signature, consumption being
decision-measurable) lists the continuation value V[>]
on an input side with the perch word `: !cntn` and produces the control
`c` at the decision perch; its one statement is the declarative
maximisation over the feasible set Γ(w_d), and the lines of the
endogenous grid method stand in the block `policy` of the methods file.

Runnable under pytest or directly with the repository interpreter:

    venv/bin/python applications/housing-owner/tests/test_consumption_choice_ast.py
"""

import pathlib
import sys

from dataclasses import fields, is_dataclass

_TESTS = pathlib.Path(__file__).resolve().parent
_TOOLS = _TESTS.parents[2] / "applications"
sys.path.insert(0, str(_TOOLS))

import pytest                         # noqa: E402

import stage_ast                      # noqa: E402
from stage_ast import (               # noqa: E402
    annotation as _ann, block, one_minus as _one_minus, parsed, perched as _p, run_checks,
    sym as _c)
from bellman.syntax.terms import (             # noqa: E402
    Add, Annotation, Arrival, Assignment, At, Block, Call, Cartesian, Closed,
    Constant, Continuation, Control, Coordinate, CorrDef, Declaration,
    Declare, Decision, Div, Domain, Equation, Grid, In, Infoset, Interval,
    KeyValue, Marked, Metadata, Method, Mul, Name, Named, Neg, Node, Number,
    Open, Operator, Path, Points, Pow, Range, Role, Segment, SetDifference,
    Shock, Signature, Space, Spaced, Statement, Sub, Subject, Tag, Typer,
    Value, Var, Word,
)

_SOURCE = _TESTS.parent / "declaration" / "stages" / "consumption_choice" / "consumption_choice.bl"

_AST = parsed(_SOURCE)
_ITEMS = _AST.items
# the methods file beside the stage file, an addition to it: a metadata line,
# the three settings of the grid, declared with their sets, and the two blocks
# named by the builders' ids
_ADDITION = parsed(_SOURCE.parent / "methods.bl")
_ADDITION_ITEMS = _ADDITION.items


def _housing_services(stem="H_c"):
    """The housing-services aggregate κ*H + ι: on the continuation
    housing H_c in the inverse Euler line, on the decision housing H_d in
    the backward block, its derivative line and the declarative optimality
    statement."""
    return Add(Mul(_c("κ"), _c(stem)), _c("ι"))


def test_item_census():
    # One metadata line, four space assignments, eight parameter
    # declarations, two blocks, the feasible-correspondence definition
    # Γ, the policy block — and no parse-tree residue. The decision perch
    # is the stage's entry perch: no arrival block stands before it.
    assert len(_ITEMS) == 17
    kinds = [type(it).__name__ for it in _ITEMS]
    assert kinds == (["Metadata"] + ["Statement"] * 4 + ["Declare"] * 8
                     + ["Block"] * 2 + ["Statement"] + ["Block"])
    assert stage_ast.unlowered_parse_nodes(_AST) == []


def test_metadata_line():
    # @stage: consumption_choice
    assert _ITEMS[0] == Metadata("stage", "consumption_choice")


def test_space_assignments():
    # Xa := ℝ₊ and Xw := ℝ₊ — reserved set glyphs, wrapped in Space.
    assert _ITEMS[1] == Statement(
        Assignment(Constant("Xa"), Space(Named("ℝ₊"))), None)
    assert _ITEMS[3] == Statement(
        Assignment(Constant("Xw"), Space(Named("ℝ₊"))), None)
    # Y := ℕ — the source YAML writes Z+; ℕ is the reserved neighbour
    # (no ℤ₊ glyph exists).
    assert _ITEMS[4] == Statement(
        Assignment(Constant("Y"), Space(Named("ℕ"))), None)
    # XH := linspace(H_min, H_max, n_H) — the grid-defining right-hand
    # side is a formula, so it lowers to a Call with three plain
    # symbol arguments and takes no Space wrapper.
    assert _ITEMS[2] == Statement(
        Assignment(Constant("XH"),
                   Call("linspace", [_c("H_min"), _c("H_max"),
                                     _c("n_H")])),
        None)


def test_parameter_declarations():
    # The eight parameters of the source YAML, in order, each a bare
    # declaration line wrapped in the provisional Declare item. β and
    # θ carry open intervals; γ carries the difference ℝ₊ \ {1}, which
    # excludes the value 1, at which the formulas that divide by 1 - γ have
    # no value; ι carries ℝ₊₊; n_H carries ℕ (the source writes Z+). Every
    # parameter but β is written with a description, which stands on the
    # Declare item's annotation slot.
    open_unit = Domain(Interval(Range(Open(), Number(0), Number(1),
                                      Open())))
    expected = [
        ("β", open_unit, None),
        ("γ", Domain(SetDifference(Named("ℝ₊"), Points([Number(1)], None))),
         "curvature of the constant-relative-risk-aversion transform of"
         " the aggregate"),
        ("θ", open_unit,
         "Cobb-Douglas weight on consumption; 1-θ is the weight on housing"
         " services"),
        ("κ", Domain(Named("ℝ₊")),
         "housing services per unit of the housing stock"),
        ("ι", Domain(Named("ℝ₊₊")),
         "constant in housing services, which keeps utility finite at zero"
         " housing"),
        ("n_H", Domain(Named("ℕ")), "Number of housing types"),
        ("H_min", Domain(Named("ℝ₊")), "Minimum housing size"),
        ("H_max", Domain(Named("ℝ₊")), "Maximum housing size"),
    ]
    for offset, (stem, domain, described) in enumerate(expected):
        annot = None if described is None else Annotation([Tag(f'"{described}"')])
        assert _ITEMS[5 + offset] == Declare(Declaration(
            Subject([Coordinate(stem, None, [])]),
            [domain],
            None), annot), stem


def test_block_identities_and_order():
    # The three blocks: the source YAML's arvl_to_dcsn, an empty list
    # meaning the identity, and its dcsn_to_arvl, the identity on the
    # value, are written as no block, the decision perch being the stage's
    # entry perch; dcsn_to_cntn, cntn_to_dcsn and the policy remain.
    ids = [it.tag.entries[0] for it in _ITEMS if isinstance(it, Block)]
    assert ids == [
        KeyValue("id", "dcsn_to_cntn"),
        KeyValue("id", "cntn_to_dcsn"),
        KeyValue("id", "policy"),
    ]


def test_block_dcsn_to_cntn_header():
    # [id=dcsn_to_cntn, (w_d : Xw, H_d : XH, y_d : Y, c : !ctrl @ ℝ₊) : !dcsn
    #        -> (a_nxt : Xa, H_c : XH, y_c : Y) : !cntn]
    # The header types the decision states, the stage having no arrival
    # block whose output would type them; H_d is the housing stock chosen
    # in the companion stage. c is the binding occurrence of the control;
    # its classifiers keep the order written, role before domain.
    assert _ITEMS[13].tag == _ann(
        KeyValue("id", "dcsn_to_cntn"),
        Typer(Signature(
            Subject([Coordinate("w_d", None, [Domain(Named("Xw"))]),
                     Coordinate("H_d", None, [Domain(Named("XH"))]),
                     Coordinate("y_d", None, [Domain(Named("Y"))]),
                     Coordinate("c", None, [Role(Control()),
                                            Domain(Named("ℝ₊"))])]),
            [Infoset(Decision())],
            Subject([Coordinate("a_nxt", None, [Domain(Named("Xa"))]),
                     Coordinate("H_c", None, [Domain(Named("XH"))]),
                     Coordinate("y_c", None, [Domain(Named("Y"))])]),
            [Infoset(Continuation())])))


def test_block_dcsn_to_cntn_body():
    # a_nxt = w_d - c is the source's savings equation; the two carry
    # equations make explicit the housing stock and income index that
    # the source lists as poststates without writing transitions.
    assert _ITEMS[13].body == (
        Statement(Equation(_c("a_nxt"), Sub(_c("w_d"), _c("c"))), None),
        Statement(Equation(_c("H_c"), _c("H_d")), None),
        Statement(Equation(_c("y_c"), _c("y_d")), None),
    )


def test_block_cntn_to_dcsn_header():
    # [id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn
    #        -> (V : ℝ @ !vlu) : !dcsn]
    # The housing stock is read at the decision perch, H_d, a coordinate
    # of the block's output, which the header does not list (the rule of
    # 12 October 2026).
    # V[>] is the binding occurrence of the continuation value: the
    # perch mark sits in the coordinate's index slot, and !vlu lowers to
    # Role(Value(0)) after the Domain, in the order written.
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
    # V = ((c^θ * (κ*H_d + ι)^(1-θ))^(1-γ))/(1-γ) + β*V[>] — the
    # Cobb-Douglas utility over consumption and housing services plus
    # the discounted continuation value, the source's cntn_to_dcsn line
    # with the housing stock read at the decision perch as H_d, and the
    # block's one line: its derivative line stands in the marginal block.
    # No expectation operator appears: the stage is shock-free.
    utility = Div(
        Pow(Mul(Pow(_c("c"), _c("θ")),
                Pow(_housing_services("H_d"), _one_minus("θ"))),
            _one_minus("γ")),
        _one_minus("γ"))
    assert _ITEMS[14].body == (Statement(
        Equation(_c("V"),
                 Add(utility, Mul(_c("β"), _p("V", Continuation())))),
        _ann(KeyValue("id", "value"))),)


def test_block_cntn_to_dcsn_marginal_equation():
    # D_{w_d}V = θ * c^(θ*(1-γ)-1) * (κ*H_d + ι)^((1-θ)*(1-γ)) — the
    # marginal utility of consumption, stated as the derivative of the
    # decision value in the cash on hand w_d, the envelope condition.
    # The source YAML states this functional form as the policy-block
    # ShadowBellman line in continuation coordinates; the methods file
    # states it in its block `cntn_to_dcsn`, which appends the line to the
    # decision value builder's block and carries its id alone, since it adds
    # no coordinate.
    assert _ADDITION_ITEMS[0] == Metadata("methods", "consumption_choice")
    marginal = block(_ADDITION_ITEMS, "cntn_to_dcsn")
    assert marginal.tag == _ann(KeyValue("id", "cntn_to_dcsn"))
    assert marginal.body == (Statement(
        Equation(Operator("D", [Var("w_d")], [_c("V")]),
                 Mul(Mul(_c("θ"),
                         Pow(_c("c"),
                             Sub(Mul(_c("θ"), _one_minus("γ")),
                                 Number(1)))),
                     Pow(_housing_services("H_d"),
                         Mul(_one_minus("θ"), _one_minus("γ"))))),
        _ann(KeyValue("id", "marginal"))),)


def test_feasible_correspondence():
    # Γ(x : ℝ₊) := (0, x] :: [id=feasible] — the feasible consumption set
    # as a correspondence definition at file level: one typed parameter
    # and a half-open interval body whose upper bound is the parameter.
    assert _ITEMS[15] == Statement(
        CorrDef("Γ", [Coordinate("x", None, [Domain(Named("ℝ₊"))])],
                Interval(Range(Open(), Number(0), _c("x"), Closed()))),
        _ann(KeyValue("id", "feasible")))


def test_block_policy_header():
    # [id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊ @ !ctrl) : !dcsn]
    # The input side carries the continuation perch word and lists the
    # value function the block reads and no state: a state a policy line
    # mentions is a coordinate of the block, not an input (AAS, 18 Sep
    # 2026), so the continuation states a_nxt and H_c are no longer
    # written, and the decision states w_d and H_d were never listed.
    # V[>] is the binding occurrence of the continuation value, whose
    # derivative the endogenous grid method reads.
    assert _ITEMS[16].tag == _ann(
        KeyValue("id", "policy"),
        Typer(Signature(
            Subject([Coordinate("V", At(Continuation()),
                                [Domain(Named("ℝ")), Role(Value(0))])]),
            [Infoset(Continuation())],
            Subject([Coordinate("c", None,
                                [Domain(Named("ℝ₊")), Role(Control())])]),
            [Infoset(Decision())])))


def test_block_policy_optimality():
    # c = argmax_{cp : Γ(w_d)}(((cp^θ * (κ*H_d + ι)^(1-θ))^(1-γ))/(1-γ)
    #                          + β*V[>])   :: [id=optimality]
    # The declarative maximisation statement (ruling D19), the policy
    # block's one statement: the binder `cp : Γ(w_d)` lowers to In(var,
    # set) with the feasible set a Call to Γ at the decision cash on hand;
    # the objective is the period utility at the candidate cp with the
    # decision housing H_d plus the discounted continuation value. The
    # line carries no !doc, since the method block of the endogenous grid
    # method opens the builder.
    utility = Div(
        Pow(Mul(Pow(_c("cp"), _c("θ")),
                Pow(_housing_services("H_d"), _one_minus("θ"))),
            _one_minus("γ")),
        _one_minus("γ"))
    assert _ITEMS[16].body == (Statement(
        Equation(_c("c"),
                 Operator("argmax", [In("cp", Call("Γ", [_c("w_d")]))],
                          [Add(utility,
                               Mul(_c("β"), _p("V", Continuation())))])),
        _ann(KeyValue("id", "optimality"))),)


def test_addition_policy_block_header():
    # [id=policy, policy.method : !egm | policy.grid : !Cartesian(a_nxt=(a_min, a_max, n_a))]
    # The block of the methods file that adds to the policy builder: its
    # two typing entries, by the absolute path, type the builder's method
    # component with the endogenous grid method and its grid component with
    # one factor on the continuation savings a_nxt, the bounds and the count
    # the declared settings by name; the block carries no signature. The
    # file: its metadata line, the three settings and the two blocks.
    kinds = [type(it).__name__ for it in _ADDITION_ITEMS]
    assert kinds == ["Metadata"] + ["Declare"] * 3 + ["Block"] * 2
    egm = block(_ADDITION_ITEMS, "policy")
    assert egm.tag == _ann(
        KeyValue("id", "policy"),
        Typer(Declaration(Path([Segment("policy"), Segment("method")]),
                          [Method(Word("egm"))])),
        Typer(Declaration(Path([Segment("policy"), Segment("grid")]), [Grid(Cartesian([
            Spaced("a_nxt", Name("a_min"), Name("a_max"), Name("n_a"))]))])))
    assert len(egm.body) == 3


def test_block_policy_inveuler():
    # c[>] = (β*D_{a_nxt}V[>] / (θ*(κ*H_c + ι)^((1-θ)*(1-γ))))
    #            ^(1/(θ*(1-γ) - 1))   :: [id=InvEuler, !node]
    # The inverse-Euler consumed function, expression for expression
    # the source's InvEuler line (c_fn[>] there, c[>] here), written on
    # the continuation housing H_c. The exponent is a bare Div, the
    # reciprocal of θ*(1-γ) - 1, which is the exponent on consumption in
    # the marginal utility less one; the !node tag becomes
    # Typer(Marked(Node())).
    assert block(_ADDITION_ITEMS, "policy").body[0] == Statement(
        Equation(
            _p("c", Continuation()),
            Pow(Div(Mul(_c("β"), Operator("D", [Var("a_nxt")],
                                          [_p("V", Continuation())])),
                    Mul(_c("θ"),
                        Pow(_housing_services(),
                            Mul(_one_minus("θ"), _one_minus("γ"))))),
                Div(Number(1),
                    Sub(Mul(_c("θ"), _one_minus("γ")), Number(1))))),
        _ann(KeyValue("id", "InvEuler"), Typer(Marked(Node()))))


def test_block_policy_regrid():
    # w[>] = a_nxt + c[>] :: [id=regrid, !node] — the endogenous
    # cash-on-hand grid, the source's cntn_to_dcsn_transition line
    # (w_dcsn[>] there, w[>] here).
    assert block(_ADDITION_ITEMS, "policy").body[1] == Statement(
        Equation(_p("w", Continuation()),
                 Add(_c("a_nxt"), _p("c", Continuation()))),
        _ann(KeyValue("id", "regrid"), Typer(Marked(Node()))))


def test_block_policy_consumption():
    # c = c[>] :: [id=cons_choice] — the decision-perch consumption is
    # the consumed function read on the endogenous grid, the spelling of
    # the portfolio corpus (cons.bl); no evaluate call appears.
    assert block(_ADDITION_ITEMS, "policy").body[2] == Statement(
        Equation(_c("c"), _p("c", Continuation())),
        _ann(KeyValue("id", "cons_choice")))


def _walk(node, hit):
    if is_dataclass(node):
        hit(node)
        for f in fields(node):
            _walk(getattr(node, f.name), hit)
    elif isinstance(node, tuple):
        for x in node:
            _walk(x, hit)


def test_shock_free_translation():
    # The source YAML declares exogenous: {} — no shock in this stage.
    # Accordingly the abstract trees contain no Shock role (no law) and
    # no expectation operator; the Operator nodes are the argmax of the
    # declarative optimality statement in the stage file, the derivative
    # term D_{a_nxt}V[>] of the inverse Euler line of the methods file's
    # policy block and the derivative term D_{w_d}V of its derivative line,
    # and the only function calls are the grid constructor and the feasible
    # correspondence Γ.
    operators, shocks, call_heads = [], [], set()

    def hit(n):
        if isinstance(n, Operator):
            operators.append(n)
        elif isinstance(n, Shock):
            shocks.append(n)
        elif isinstance(n, Call):
            call_heads.add(n.fun)

    for tree in (_AST, _ADDITION):
        _walk(tree, hit)
    assert [op.head for op in operators] == ["argmax", "D", "D"]
    assert shocks == []
    assert call_heads == {"linspace", "Γ"}


if __name__ == "__main__":
    sys.exit(run_checks(globals(), f"for {_SOURCE.name}"))
